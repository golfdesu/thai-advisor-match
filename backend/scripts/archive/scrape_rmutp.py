"""Scraper for RMUTP"""
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
    "id": "rmutp_hm_tourism",
    "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาการจัดการการท่องเที่ยว",
    "title_en": "B.A. in Tourism Management",
    "degree_level": "ปริญญาตรี",
    "degree_name": "ศศ.บ. (การจัดการการท่องเที่ยว)",
    "university": "Rajamangala University of Technology Phra Nakhon",
    "university_th": "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
    "faculty": "Faculty of Liberal Arts",
    "faculty_th": "คณะศิลปศาสตร์",
    "department": "Tourism",
    "department_th": "การท่องเที่ยว",
    "program_type": "ภาคปกติ",
    "duration_years": "4 ปี",
    "total_credits": "130 หน่วยกิต",
    "tuition_per_semester": "16,000 บาท",
    "tuition_total": "128,000 บาท",
    "description": "เน้นการจัดการธุรกิจท่องเที่ยว มัคคุเทศก์ และอุตสาหกรรมบริการ",
    "curriculum_highlights": ["Tourism Planning", "Hospitality Management"],
    "career_paths": ["Tour Guide", "Tourism Planner", "Hotel Manager"],
    "tags": ["Tourism", "Hospitality"],
    "website_url": "https://rmutp.ac.th"
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
    print("RMUTP seeded")
