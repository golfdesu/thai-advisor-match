"""Scraper for MJU"""
import sys, os, json
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))
try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
COURSES = [{
    "id": "mju_agri_animal",
    "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาสัตวศาสตร์",
    "title_en": "B.Sc. in Animal Science",
    "degree_level": "ปริญญาตรี",
    "degree_name": "วท.บ. (สัตวศาสตร์)",
    "university": "Maejo University",
    "university_th": "มหาวิทยาลัยแม่โจ้",
    "faculty": "Faculty of Animal Science and Technology",
    "faculty_th": "คณะสัตวศาสตร์และเทคโนโลยี",
    "department": "Animal Science",
    "department_th": "สัตวศาสตร์",
    "program_type": "ภาคปกติ",
    "duration_years": "4 ปี",
    "total_credits": "130 หน่วยกิต",
    "tuition_per_semester": "15,000 บาท",
    "tuition_total": "120,000 บาท",
    "description": "เน้นการจัดการปศุสัตว์ เทคโนโลยีการผลิตสัตว์ และอาหารสัตว์",
    "curriculum_highlights": ["Animal Nutrition", "Livestock Management"],
    "career_paths": ["Animal Scientist", "Farm Manager"],
    "tags": ["Agriculture", "Animal Science"],
    "website_url": "https://mju.ac.th"
}]
def seed_db():
    if not DB_AVAILABLE: return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    for c in COURSES:
        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items(): setattr(existing, k, v)
        else:
            session.add(CourseDB(**c))
    session.commit()
if __name__ == "__main__":
    seed_db()
    print("MJU seeded")
