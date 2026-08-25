"""
Scraper for King Mongkut's University of Technology Thonburi (KMUTT)
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

KMUTT_COURSES = [
    {
        "id": "kmutt_sit_cs",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรภาษาอังกฤษ)",
        "title_en": "Bachelor of Science Program in Computer Science (English Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Computer Science",
        "department_th": "วิทยาการคอมพิวเตอร์",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "เน้นวิทยาการคอมพิวเตอร์และการพัฒนาซอฟต์แวร์ระดับนานาชาติ",
        "curriculum_highlights": ["AI", "Data Science", "Software Architecture"],
        "career_paths": ["Software Engineer", "Data Scientist", "System Analyst"],
        "tags": ["Computer Science", "IT", "International"],
        "website_url": "https://www.sit.kmutt.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE: return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    for c in KMUTT_COURSES:
        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items(): setattr(existing, k, v)
        else:
            session.add(CourseDB(**c))
    session.commit()
    print(f"Seeded {len(KMUTT_COURSES)} KMUTT courses.")

if __name__ == "__main__":
    seed_db()
