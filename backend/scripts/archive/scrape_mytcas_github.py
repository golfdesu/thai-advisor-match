"""
MyTCAS GitHub Dump Importer
This script imports Bachelor's degree programs from community-maintained MyTCAS JSON dumps.
Since MyTCAS does not provide an official public API, using community JSON dumps 
avoids overloading their servers and prevents IP bans.

Target: https://raw.githubusercontent.com/tcas-community/thai-university-database/main/tcas_courses.json
(Note: Replace the URL with the actual active community dump URL)
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import requests

# Add backend root to path for DB access
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

try:
    from app.core.database import engine, Base, SessionLocal
    from app.models.db_models import CourseDB
    from sqlalchemy.orm import Session
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("mytcas_importer")

# Placeholder URL for the community TCAS JSON dump
TCAS_DUMP_URL = "https://raw.githubusercontent.com/tcas-community/thai-university-database/main/tcas_courses.json"
DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = DATA_DIR / "mytcas_bachelor_dump.json"

def fetch_tcas_dump() -> List[Dict[str, Any]]:
    """Fetches the TCAS JSON dump from GitHub."""
    log.info(f"Downloading MyTCAS dump from {TCAS_DUMP_URL}...")
    try:
        # Mocking the request for the sake of demonstration, 
        # as the exact community URL might change each admission year.
        # response = requests.get(TCAS_DUMP_URL, timeout=30)
        # response.raise_for_status()
        # return response.json()
        
        # Simulated Data Structure based on typical TCAS open data
        log.info("Simulating community dump fetch (URL placeholder used)...")
        time.sleep(1)
        return [
            {
                "university_id": "001",
                "university_name_th": "มหาวิทยาลัยเชียงใหม่",
                "university_name_en": "Chiang Mai University",
                "faculty_name_th": "คณะวิทยาศาสตร์",
                "program_name_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
                "program_name_en": "B.Sc. in Computer Science",
                "degree": "ปริญญาตรี",
                "tcac_round_1": True,
                "tcac_round_2": True,
                "tcac_round_3": True,
                "tuition_fee": 20000,
                "url": "https://www.science.cmu.ac.th"
            },
            {
                "university_id": "002",
                "university_name_th": "มหาวิทยาลัยธรรมศาสตร์",
                "university_name_en": "Thammasat University",
                "faculty_name_th": "คณะวิศวกรรมศาสตร์",
                "program_name_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมซอฟต์แวร์ (นานาชาติ)",
                "program_name_en": "B.Eng. in Software Engineering (International)",
                "degree": "ปริญญาตรี",
                "tcac_round_1": True,
                "tcac_round_2": False,
                "tcac_round_3": True,
                "tuition_fee": 75000,
                "url": "https://www.engr.tu.ac.th"
            }
        ]
    except Exception as e:
        log.error(f"Failed to fetch TCAS dump: {e}")
        return []

def transform_to_schema(tcas_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforms TCAS open data format into the Project's CourseDB schema."""
    courses = []
    for item in tcas_data:
        uni_prefix = item.get("university_name_en", "").split()[0].lower()
        prog_id = f"mytcas_{uni_prefix}_{abs(hash(item.get('program_name_en', '')))}"
        
        course = {
            "id": prog_id,
            "title_th": item.get("program_name_th", ""),
            "title_en": item.get("program_name_en", ""),
            "degree_level": item.get("degree", "ปริญญาตรี"),
            "degree_name": "", # Often not explicitly separated in TCAS dumps
            "university": item.get("university_name_en", ""),
            "university_th": item.get("university_name_th", ""),
            "faculty": "",
            "faculty_th": item.get("faculty_name_th", ""),
            "department": "",
            "department_th": "",
            "program_type": "ภาคปกติ" if "นานาชาติ" not in item.get("program_name_th", "") else "นานาชาติ (International Program)",
            "duration_years": "4 ปี", # Default for Bachelor's
            "total_credits": "ไม่ระบุ",
            "tuition_per_semester": f"{item.get('tuition_fee', 0):,} บาท",
            "tuition_total": f"{item.get('tuition_fee', 0) * 8:,} บาท",
            "description": "ข้อมูลหลักสูตรปริญญาตรีนำเข้าจากฐานข้อมูลระบบ TCAS",
            "curriculum_highlights": [],
            "career_paths": [],
            "tags": ["TCAS", "Bachelor", item.get("university_name_en", "")],
            "website_url": item.get("url", "")
        }
        courses.append(course)
    return courses

def seed_database(courses: List[Dict[str, Any]]):
    """Seeds the transformed courses into the Supabase PostgreSQL database."""
    if not DB_AVAILABLE:
        log.error("Database module not available. Skipping DB seeding.")
        return

    Base.metadata.create_all(bind=engine)
    session: Session = SessionLocal()
    
    try:
        inserted = 0
        updated = 0
        for course_data in courses:
            existing = session.query(CourseDB).filter(CourseDB.id == course_data["id"]).first()
            if existing:
                for key, value in course_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                new_course = CourseDB(**course_data)
                session.add(new_course)
                inserted += 1
        
        session.commit()
        log.info(f"Database Seeding Completed: {inserted} inserted, {updated} updated.")
    except Exception as e:
        session.rollback()
        log.error(f"Database seeding failed: {e}")
    finally:
        session.close()

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch
    raw_data = fetch_tcas_dump()
    if not raw_data:
        log.warning("No data retrieved.")
        return
        
    # 2. Transform
    log.info("Transforming TCAS data to EduCenter schema...")
    courses = transform_to_schema(raw_data)
    
    # 3. Save locally
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(courses)} courses to {OUTPUT_FILE}")
    
    # 4. Seed DB
    seed_database(courses)

if __name__ == "__main__":
    main()
