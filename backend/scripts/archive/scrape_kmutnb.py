"""
Scraper for King Mongkut's University of Technology North Bangkok (KMUTNB)
"""
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

KMUTNB_COURSES = [
    {
        "id": "kmutnb_eng_me",
        "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล",
        "title_en": "Bachelor of Engineering Program in Mechanical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมเครื่องกล)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Mechanical Engineering",
        "department_th": "วิศวกรรมเครื่องกล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "145 หน่วยกิต",
        "tuition_per_semester": "23,000 บาท",
        "tuition_total": "184,000 บาท",
        "description": "มุ่งเน้นการออกแบบเครื่องจักรกล ระบบควบคุม และพลังงาน",
        "curriculum_highlights": ["Thermodynamics", "Robotics", "Mechanical Design"],
        "career_paths": ["Mechanical Engineer", "Production Engineer", "Maintenance Engineer"],
        "tags": ["Engineering", "Mechanical"],
        "website_url": "https://eng.kmutnb.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE: return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    for c in KMUTNB_COURSES:
        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items(): setattr(existing, k, v)
        else:
            session.add(CourseDB(**c))
    session.commit()
    print(f"Seeded {len(KMUTNB_COURSES)} KMUTNB courses.")

if __name__ == "__main__":
    seed_db()
