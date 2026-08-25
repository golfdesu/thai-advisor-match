"""Scraper for PSU"""
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
    "id": "psu_sci_bio",
    "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาชีววิทยา",
    "title_en": "B.Sc. in Biology",
    "degree_level": "ปริญญาตรี",
    "degree_name": "วท.บ. (ชีววิทยา)",
    "university": "Prince of Songkla University",
    "university_th": "มหาวิทยาลัยสงขลานครินทร์",
    "faculty": "Faculty of Science",
    "faculty_th": "คณะวิทยาศาสตร์",
    "department": "Biology",
    "department_th": "ชีววิทยา",
    "program_type": "ภาคปกติ",
    "duration_years": "4 ปี",
    "total_credits": "130 หน่วยกิต",
    "tuition_per_semester": "18,000 บาท",
    "tuition_total": "144,000 บาท",
    "description": "ศึกษาด้านชีววิทยา พฤกษศาสตร์ สัตววิทยา",
    "curriculum_highlights": ["Ecology", "Genetics"],
    "career_paths": ["Biologist", "Researcher"],
    "tags": ["Biology", "Science"],
    "website_url": "https://sci.psu.ac.th"
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
    print("PSU seeded")
