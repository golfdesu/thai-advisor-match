"""Scraper for SUT"""
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
    "id": "sut_eng_civil",
    "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา",
    "title_en": "B.Eng. in Civil Engineering",
    "degree_level": "ปริญญาตรี",
    "degree_name": "วศ.บ. (วิศวกรรมโยธา)",
    "university": "Suranaree University of Technology",
    "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
    "faculty": "Institute of Engineering",
    "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
    "department": "Civil Engineering",
    "department_th": "วิศวกรรมโยธา",
    "program_type": "สหกิจศึกษา",
    "duration_years": "4 ปี",
    "total_credits": "140 หน่วยกิต",
    "tuition_per_semester": "20,000 บาท",
    "tuition_total": "160,000 บาท",
    "description": "เน้นวิศวกรรมโยธา โครงสร้าง ทรัพยากรน้ำ และสหกิจศึกษา",
    "curriculum_highlights": ["Structural Design", "Surveying"],
    "career_paths": ["Civil Engineer"],
    "tags": ["Engineering", "Civil"],
    "website_url": "https://sut.ac.th"
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
    print("SUT seeded")
