"""
Seeds CMU curricula (Bachelor -> Ph.D.) into the Supabase `courses` table
from backend/scripts/data/cmu_courses.json.

Usage:
    python seed_cmu_courses.py            # upsert all records
    python seed_cmu_courses.py --dry-run  # validate only, no DB writes
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base
from app.models.db_models import CourseDB
from sqlalchemy.orm import Session

DATA_FILE = Path(__file__).resolve().parent / "data" / "cmu_courses.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("seed")


def seed(dry_run: bool = False):
    if not DATA_FILE.exists():
        log.error("Data file not found: %s (run build_cmu_courses_json.py first)", DATA_FILE)
        sys.exit(1)

    with DATA_FILE.open(encoding="utf-8") as f:
        courses = json.load(f)

    log.info("Loaded %d course records", len(courses))
    ids = [c["id"] for c in courses]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        log.error("Duplicate IDs found: %s", sorted(dupes)[:10])
        sys.exit(1)

    required = ["id", "title_th", "degree_level", "university", "university_th", "faculty", "faculty_th"]
    bad = [c["id"] for c in courses if any(not c.get(k) for k in required)]
    if bad:
        log.error("%d records missing required fields, e.g. %s", len(bad), bad[:5])
        sys.exit(1)

    if dry_run:
        levels = {}
        for c in courses:
            levels[c["degree_level"]] = levels.get(c["degree_level"], 0) + 1
        log.info("DRY RUN OK — %d records valid. Levels: %s", len(courses), levels)
        return

    Base.metadata.create_all(bind=engine)
    inserted = updated = 0
    with Session(engine) as session:
        for c in courses:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for key, value in c.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                session.add(CourseDB(
                    id=c["id"],
                    title_th=c["title_th"],
                    title_en=c.get("title_en"),
                    degree_level=c["degree_level"],
                    degree_name=c.get("degree_name"),
                    university=c["university"],
                    university_th=c["university_th"],
                    faculty=c["faculty"],
                    faculty_th=c["faculty_th"],
                    department=c.get("department"),
                    department_th=c.get("department_th"),
                    program_type=c.get("program_type"),
                    duration_years=c.get("duration_years"),
                    total_credits=c.get("total_credits"),
                    tuition_per_semester=c.get("tuition_per_semester"),
                    tuition_total=c.get("tuition_total"),
                    description=c.get("description"),
                    curriculum_highlights=c.get("curriculum_highlights", []),
                    career_paths=c.get("career_paths", []),
                    tags=c.get("tags", []),
                    website_url=c.get("website_url"),
                ))
                inserted += 1
        session.commit()

    log.info("Seed complete — inserted=%d updated=%d total=%d", inserted, updated, len(courses))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed CMU TQF2 courses")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
