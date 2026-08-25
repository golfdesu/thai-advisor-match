"""Scraper for UTK"""
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
    "id": "utk_arts_design",
    "title_th": "ศิลปกรรมศาสตรบัณฑิต สาขาวิชาการออกแบบผลิตภัณฑ์",
    "title_en": "B.F.A. in Product Design",
    "degree_level": "ปริญญาตรี",
    "degree_name": "ศป.บ. (การออกแบบผลิตภัณฑ์)",
    "university": "Rajamangala University of Technology Krungthep",
    "university_th": "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ",
    "faculty": "Faculty of Fine Arts",
    "faculty_th": "คณะศิลปกรรมศาสตร์",
    "department": "Product Design",
    "department_th": "การออกแบบผลิตภัณฑ์",
    "program_type": "ภาคปกติ",
    "duration_years": "4 ปี",
    "total_credits": "130 หน่วยกิต",
    "tuition_per_semester": "15,000 บาท",
    "tuition_total": "120,000 บาท",
    "description": "เน้นการออกแบบผลิตภัณฑ์เชิงสร้างสรรค์ นวัตกรรม 3D",
    "curriculum_highlights": ["Industrial Design", "3D Modeling"],
    "career_paths": ["Product Designer", "Industrial Designer"],
    "tags": ["Design", "Arts", "Product"],
    "website_url": "https://rmutk.ac.th"
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
    print("UTK seeded")
