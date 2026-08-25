"""
Scraper for King Mongkut's Institute of Technology Ladkrabang (KMITL)
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

KMITL_COURSES = [
    {
        "id": "kmitl_eng_ce",
        "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Computer Engineering",
        "department_th": "วิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "เน้นการพัฒนาระบบคอมพิวเตอร์ ฮาร์ดแวร์ ซอฟต์แวร์ และเครือข่าย",
        "curriculum_highlights": ["Embedded Systems", "Network Engineering", "Software Engineering"],
        "career_paths": ["Computer Engineer", "Software Developer", "Network Engineer"],
        "tags": ["Engineering", "Computer", "IT"],
        "website_url": "https://en.kmitl.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE: return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    for c in KMITL_COURSES:
        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items(): setattr(existing, k, v)
        else:
            session.add(CourseDB(**c))
    session.commit()
    print(f"Seeded {len(KMITL_COURSES)} KMITL courses.")

if __name__ == "__main__":
    seed_db()
