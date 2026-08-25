"""
Unified Scraper and Seed Script for Private Universities:
1. Bangkok University (BU)
2. Assumption University (AU / ABAC)
3. Sripatum University (SPU)

Schema:
CourseDB(id, title_th, title_en, degree_level, degree_name, university, university_th,
         faculty, faculty_th, department, department_th, program_type, duration_years,
         total_credits, tuition_per_semester, tuition_total, description,
         curriculum_highlights, career_paths, tags, website_url)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add backend root to sys.path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_ROOT))

from scripts.scrape_bu import BU_COURSES
from scripts.scrape_au import AU_COURSES
from scripts.scrape_spu import SPU_COURSES

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scrape_private_universities")

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

UNIVERSITIES_MAP = {
    "bu": {
        "name": "Bangkok University",
        "courses": BU_COURSES,
        "json_path": DATA_DIR / "bu_courses.json"
    },
    "au": {
        "name": "Assumption University",
        "courses": AU_COURSES,
        "json_path": DATA_DIR / "au_courses.json"
    },
    "spu": {
        "name": "Sripatum University",
        "courses": SPU_COURSES,
        "json_path": DATA_DIR / "spu_courses.json"
    }
}

def seed_courses_to_db(courses: List[Dict[str, Any]], uni_name: str) -> tuple[int, int]:
    if not DB_AVAILABLE:
        logger.error("Database connection unavailable. Skipping database seeding.")
        return 0, 0
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    for c in courses:
        try:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error seeding course {c.get('id')}: {e}")
    session.close()
    logger.info(f"[{uni_name}] Seeded {inserted} new, {updated} updated courses.")
    return inserted, updated

def run_all(seed: bool = False):
    total_courses = 0
    total_inserted = 0
    total_updated = 0
    results_summary = {}

    for key, info in UNIVERSITIES_MAP.items():
        courses = info["courses"]
        total_courses += len(courses)
        
        # Save to JSON
        with open(info["json_path"], "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(courses)} courses for {info['name']} to {info['json_path']}")

        if seed:
            ins, upd = seed_courses_to_db(courses, info["name"])
            total_inserted += ins
            total_updated += upd
            results_summary[info["name"]] = {"courses": len(courses), "inserted": ins, "updated": upd}
        else:
            results_summary[info["name"]] = {"courses": len(courses)}

    logger.info(f"Finished processing all private universities! Total courses: {total_courses}")
    return results_summary

def main():
    import urllib3
    urllib3.disable_warnings()
    parser = argparse.ArgumentParser(description="Private Universities (BU, AU, SPU) Scraper & Catalog Runner")
    parser.add_argument("--seed-db", action="store_true", help="Seed courses directly into DB")
    parser.add_argument("--uni", type=str, choices=["all", "bu", "au", "spu"], default="all", help="Target university")
    args = parser.parse_args()

    if args.uni == "all":
        run_all(seed=args.seed_db)
    else:
        info = UNIVERSITIES_MAP[args.uni]
        with open(info["json_path"], "w", encoding="utf-8") as f:
            json.dump(info["courses"], f, ensure_ascii=False, indent=2)
        if args.seed_db:
            seed_courses_to_db(info["courses"], info["name"])

if __name__ == "__main__":
    main()
