"""
Unified Course Scraper & Seeder for Thaksin University, Ramkhamhaeng University, and Sukhothai Thammathirat Open University
Conforms to Schema:
CourseDB(id, title_th, title_en, degree_level, degree_name, university, university_th, faculty, faculty_th, department, department_th, program_type, duration_years, total_credits, tuition_per_semester, tuition_total, description, curriculum_highlights, career_paths, tags, website_url)
"""
import os
import sys
import json
import logging
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ScraperUniversalTSU_RU_STOU")

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from backend.scripts.scrape_tsu import TSU_COURSES
from backend.scripts.scrape_ru import RU_COURSES
from backend.scripts.scrape_stou import STOU_COURSES

ALL_UNIVERSITIES_DATA = {
    "Thaksin University": TSU_COURSES,
    "Ramkhamhaeng University": RU_COURSES,
    "Sukhothai Thammathirat Open University": STOU_COURSES
}

def seed_all_courses():
    if not DB_AVAILABLE:
        logger.error("Database connection not available.")
        return {}

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    results = {}

    try:
        for uni_name, courses in ALL_UNIVERSITIES_DATA.items():
            inserted = 0
            updated = 0
            for c in courses:
                existing = session.query(CourseDB).filter_by(id=c["id"]).first()
                if existing:
                    for k, v in c.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    session.add(CourseDB(**c))
                    inserted += 1
            session.commit()
            results[uni_name] = {"inserted": inserted, "updated": updated, "total": len(courses)}
            logger.info(f"[{uni_name}] Processed {len(courses)} courses (New: {inserted}, Updated: {updated})")
        return results
    except Exception as e:
        session.rollback()
        logger.error(f"Error during universal seeding: {e}")
        return results
    finally:
        session.close()

if __name__ == "__main__":
    res = seed_all_courses()
    print("Seeding Summary:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
