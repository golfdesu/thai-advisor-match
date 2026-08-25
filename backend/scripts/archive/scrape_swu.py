"""
Scraper for Srinakharinwirot University (SWU)
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

SWU_COURSES = [
    {
        "id": "swu_edu_cni",
        "title_th": "การศึกษาบัณฑิต",
        "title_en": "Bachelor of Education Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "กศ.บ.",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะศึกษาศาสตร์",
        "department": "Education",
        "department_th": "การศึกษา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ผลิตครูวิชาชีพที่มีความเป็นเลิศทางวิชาการและจรรยาบรรณ",
        "curriculum_highlights": ["Pedagogy", "Educational Psychology", "Teaching Practice"],
        "career_paths": ["Teacher", "Educator", "School Administrator"],
        "tags": ["Education", "Teacher"],
        "website_url": "https://edu.swu.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE: return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    for c in SWU_COURSES:
        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items(): setattr(existing, k, v)
        else:
            session.add(CourseDB(**c))
    session.commit()
    print(f"Seeded {len(SWU_COURSES)} SWU courses.")

if __name__ == "__main__":
    seed_db()
