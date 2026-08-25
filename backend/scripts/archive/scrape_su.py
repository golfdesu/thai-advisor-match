"""
Scraper for Silpakorn University (SU)
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

SU_COURSES = [
    {
        "id": "su_arts_th",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาภาษาไทย",
        "title_en": "Bachelor of Arts Program in Thai",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาไทย)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Arts",
        "faculty_th": "คณะอักษรศาสตร์",
        "department": "Department of Thai",
        "department_th": "ภาควิชาภาษาไทย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการศึกษาภาษาและวรรณคดีไทย วัฒนธรรมไทย และการสื่อสาร",
        "curriculum_highlights": ["Thai Literature", "Linguistics", "Creative Writing"],
        "career_paths": ["Writer", "Editor", "Teacher", "Content Creator"],
        "tags": ["Thai", "Arts", "Literature"],
        "website_url": "https://arts.su.ac.th"
    },
    {
        "id": "su_arch_barch",
        "title_th": "สถาปัตยกรรมศาสตรบัณฑิต",
        "title_en": "Bachelor of Architecture Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรม)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Architecture",
        "department_th": "สถาปัตยกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "165 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "มุ่งเน้นการออกแบบสถาปัตยกรรมที่สอดคล้องกับสภาพแวดล้อมและศิลปวัฒนธรรม",
        "curriculum_highlights": ["Architectural Design", "Building Technology", "Urban Design"],
        "career_paths": ["Architect", "Urban Designer", "Project Manager"],
        "tags": ["Architecture", "Design"],
        "website_url": "https://arch.su.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE: return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    for c in SU_COURSES:
        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items(): setattr(existing, k, v)
        else:
            session.add(CourseDB(**c))
    session.commit()
    print(f"Seeded {len(SU_COURSES)} SU courses.")

if __name__ == "__main__":
    seed_db()
