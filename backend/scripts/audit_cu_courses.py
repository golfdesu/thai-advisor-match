import os
import sys
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB

def audit_cu():
    db = SessionLocal()
    cu_courses = db.query(CourseDB).filter(CourseDB.university.ilike("%Chulalongkorn%")).all()
    print(f"Total CU courses in DB: {len(cu_courses)}")

    levels = {}
    valid_tuition = 0
    unspecified_titles = 0
    sample_empty_tuition = []

    for c in cu_courses:
        lvl = c.degree_level or "Unknown"
        levels[lvl] = levels.get(lvl, 0) + 1
        if c.tuition_per_semester and c.tuition_per_semester not in ["ไม่ระบุ", "None", ""]:
            valid_tuition += 1
        else:
            if len(sample_empty_tuition) < 10:
                sample_empty_tuition.append(c)
        if c.title_th in ["ไม่ระบุ", "None", ""] or not c.title_th:
            unspecified_titles += 1

    print("Degree Levels Breakdown:")
    for lvl, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {lvl}: {count}")

    print(f"\nValid tuition: {valid_tuition}/{len(cu_courses)}")
    print(f"Unspecified title_th: {unspecified_titles}/{len(cu_courses)}")

    print("\nSample CU Courses needing tuition enrichment:")
    for c in sample_empty_tuition:
        print(f"  [{c.id}] ({c.degree_level}) {c.faculty_th} | {c.title_th} ({c.title_en})")

    db.close()

if __name__ == "__main__":
    audit_cu()
