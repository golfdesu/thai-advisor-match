"""Scraper for WU"""
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
    "id": "wu_allied_med",
    "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเทคนิคการแพทย์",
    "title_en": "B.Sc. in Medical Technology",
    "degree_level": "ปริญญาตรี",
    "degree_name": "วท.บ. (เทคนิคการแพทย์)",
    "university": "Walailak University",
    "university_th": "มหาวิทยาลัยวลัยลักษณ์",
    "faculty": "School of Allied Health Sciences",
    "faculty_th": "สำนักวิชาสหเวชศาสตร์",
    "department": "Medical Technology",
    "department_th": "เทคนิคการแพทย์",
    "program_type": "ภาคปกติ",
    "duration_years": "4 ปี",
    "total_credits": "135 หน่วยกิต",
    "tuition_per_semester": "25,000 บาท",
    "tuition_total": "200,000 บาท",
    "description": "วิเคราะห์ทางห้องปฏิบัติการทางการแพทย์เพื่อการวินิจฉัยโรค",
    "curriculum_highlights": ["Clinical Pathology", "Microbiology"],
    "career_paths": ["Medical Technologist", "Lab Scientist"],
    "tags": ["Medical", "Health"],
    "website_url": "https://wu.ac.th"
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
    print("WU seeded")
