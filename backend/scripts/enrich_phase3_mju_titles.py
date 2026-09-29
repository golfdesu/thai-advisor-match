# -*- coding: utf-8 -*-
"""
Enrich English titles (title_en), clean typos, and re-embed Phase 3 graduate courses for:
  - Maejo University (MJU)
"""
import os
import sys
import re
import logging
from collections import Counter

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("enrich_phase3_titles")

MJU_TITLE_EN_MAP = {
    # Master's
    "mju_grad_001": "Master of Business Administration Program in Tourism Management",
    "mju_grad_002": "Master of Business Administration Program in Organic Agriculture Management",
    "mju_grad_003": "Master of Economics Program in Digital Economics and Innovation",
    "mju_grad_004": "Master of Business Administration Program in Business Administration",
    "mju_grad_005": "Master of Economics Program in Applied Economics",
    "mju_grad_006": "Master of Business Administration Program in Accounting",
    "mju_grad_007": "Master of Science Program in Tourism Development",
    "mju_grad_008": "Master of Science Program in Interdisciplinary Agriculture",
    "mju_grad_009": "Master of Science Program in Technological Innovation",
    "mju_grad_010": "Master of Public Administration Program in Public Administration",
    "mju_grad_011": "Master of Engineering Program in Renewable Energy Engineering",
    "mju_grad_012": "Master of Science Program in Community Health Development",
    "mju_grad_013": "Master of Science Program in Agronomy",
    "mju_grad_014": "Master of Science Program in Fisheries Technology and Aquatic Resources",
    "mju_grad_015": "Master of Science Program in Soil Science",
    "mju_grad_016": "Master of Science Program in Urban and Environmental Planning",
    "mju_grad_017": "Master of Engineering Program in Agricultural Engineering",
    "mju_grad_018": "Master of Science Program in Food Science and Technology Innovation",
    "mju_grad_019": "Master of Science Program in Agricultural Extension and Rural Development",
    "mju_grad_020": "Master of Science Program in Resource Management and Development",
    "mju_grad_021": "Master of Science Program in Forest Management",
    "mju_grad_022": "Master of Science Program in Animal Science",
    "mju_grad_023": "Master of Science Program in Environmental Technology",

    # Doctoral
    "mju_doc_001": "Doctor of Philosophy Program in Business Administration",
    "mju_doc_002": "Doctor of Philosophy Program in Applied Economics",
    "mju_doc_003": "Doctor of Philosophy Program in Tourism Development",
    "mju_doc_004": "Doctor of Philosophy Program in Interdisciplinary Agriculture",
    "mju_doc_005": "Doctor of Philosophy Program in Food Engineering",
    "mju_doc_006": "Doctor of Philosophy Program in Administrative Sciences",
    "mju_doc_007": "Doctor of Philosophy Program in Renewable Energy Engineering",
    "mju_doc_008": "Doctor of Philosophy Program in Tourism Management",
    "mju_doc_009": "Doctor of Philosophy Program in Organic Agriculture Management",
    "mju_doc_010": "Doctor of Philosophy Program in Digital Economics and Innovation",
    "mju_doc_011": "Doctor of Philosophy Program in Agronomy",
    "mju_doc_012": "Doctor of Philosophy Program in Animal Science",
    "mju_doc_013": "Doctor of Philosophy Program in Fisheries Technology and Aquatic Resources",
    "mju_doc_014": "Doctor of Philosophy Program in Sustainable Design Innovation",
    "mju_doc_015": "Doctor of Philosophy Program in Agricultural Extension and Rural Development",
    "mju_doc_016": "Doctor of Philosophy Program in Applied Chemistry",
    "mju_doc_017": "Doctor of Philosophy Program in Genetics",
    "mju_doc_018": "Doctor of Philosophy Program in Biotechnology",
}

def build_embedding_text(c: CourseDB) -> str:
    hl = ", ".join(c.curriculum_highlights or [])
    cp = ", ".join(c.career_paths or [])
    tg = ", ".join(c.tags or [])
    return (
        f"{c.title_th} {c.title_en or ''}. "
        f"University: {c.university or ''} {c.university_th or ''}. "
        f"Faculty: {c.faculty or ''} {c.faculty_th or ''}. "
        f"Department: {c.department or ''} {c.department_th or ''}. "
        f"Degree: {c.degree_level} {c.degree_name or ''}. "
        f"Description: {c.description or ''}. "
        f"Highlights: {hl}. Careers: {cp}. Tags: {tg}."
    )

def main():
    logger.info("=== Starting MJU English Title & Typo Repair ===")
    session = SessionLocal()
    try:
        updated_count = 0
        for cid, en_title in MJU_TITLE_EN_MAP.items():
            course = session.query(CourseDB).filter(CourseDB.id == cid).first()
            if not course:
                logger.warning(f"Course not found: {cid}")
                continue

            # Fix typos in Thai title if any
            clean_th = course.title_th
            clean_th = clean_th.replace("ท่องเที่ยว่ยว", "ท่องเที่ยว")
            clean_th = clean_th.replace("ท่องเที", "ท่องเที่ยว")
            clean_th = re.sub(r"\s+", " ", clean_th).strip()

            course.title_th = clean_th
            course.title_en = en_title
            course.description = f"{clean_th} ({en_title}) {course.faculty_th} มหาวิทยาลัยแม่โจ้"

            # Re-generate embedding with updated title_en
            emb_text = build_embedding_text(course)
            vec = embedding_service.get_embedding(emb_text)
            if isinstance(vec, list) and len(vec) == 768:
                course.embedding_text = emb_text
                course.embedding = vec
                updated_count += 1
            else:
                logger.error(f"Failed to generate embedding for {cid}")

        session.commit()
        logger.info(f"SUCCESS: Enriched and re-embedded {updated_count} MJU graduate courses.")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to enrich courses: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
