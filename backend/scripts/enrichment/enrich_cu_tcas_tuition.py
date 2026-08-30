import os
import sys
import re
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from rapidfuzz import fuzz

# Official CU Tuition Rate Mapping
CU_FACULTY_TUITION_MAP = {
    # Health Sciences
    "คณะแพทยศาสตร์": {"per_sem": "34,000 บาท", "years": 6, "semesters": 12},
    "คณะทันตแพทยศาสตร์": {"per_sem": "34,000 บาท", "years": 6, "semesters": 12},
    "คณะเภสัชศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "คณะสัตวแพทยศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "คณะสหเวชศาสตร์": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},
    "คณะพยาบาลศาสตร์": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},
    "คณะจิตวิทยา": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},

    # Science & Technology
    "คณะวิศวกรรมศาสตร์": {"per_sem": "25,500 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาศาสตร์": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},
    "คณะสถาปัตยกรรมศาสตร์": {"per_sem": "23,500 บาท", "years": 5, "semesters": 10},
    "คณะวิทยาศาสตร์การกีฬา": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},
    "สำนักวิชาทรัพยากรการเกษตร": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},

    # Humanities & Social Sciences
    "คณะพาณิชยศาสตร์และการบัญชี": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะนิติศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะนิเทศศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะรัฐศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะเศรษฐศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะอักษรศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะครุศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะศิลปกรรมศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
}

# Special & International Programs
SPECIAL_PROGRAMS = [
    {"keyword": "CEDT", "title_match": "คอมพิวเตอร์และเทคโนโลยีดิจิทัล", "fee": "25,500 บาท", "semesters": 7},
    {"keyword": "ISE", "title_match": "วิศวกรรม", "fee": "84,000 บาท", "semesters": 8},
    {"keyword": "BBA", "title_match": "บริหารธุรกิจ", "fee": "105,000 บาท", "semesters": 8},
    {"keyword": "EBA", "title_match": "เศรษฐศาสตร์", "fee": "95,000 บาท", "semesters": 8},
    {"keyword": "INDA", "title_match": "สถาปัตยกรรม", "fee": "115,000 บาท", "semesters": 10},
    {"keyword": "CommDe", "title_match": "การออกแบบนิเทศศิลป์", "fee": "95,000 บาท", "semesters": 8},
    {"keyword": "BALAC", "title_match": "ภาษาและวัฒนธรรม", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "BSAC", "title_match": "เคมีประยุกต์", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "BBTech", "title_match": "เทคโนโลยีชีวภาพ", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "PGS", "title_match": "การเมืองและโลกสัมพันธ์", "fee": "90,000 บาท", "semesters": 8},
    {"keyword": "JIPP", "title_match": "จิตวิทยา", "fee": "120,000 บาท", "semesters": 8},
    {"keyword": "Sasin", "title_match": "บริหารธุรกิจ", "fee": "265,000 บาท", "semesters": 6},
]

def enrich_cu():
    db = SessionLocal()
    cu_courses = db.query(CourseDB).filter(CourseDB.university.ilike("%Chulalongkorn%")).all()
    print(f"Total CU courses in database to process: {len(cu_courses)}")

    enriched_count = 0
    re_embedded_count = 0

    for c in cu_courses:
        is_inter = "นานาชาติ" in (c.title_th or "") or "International" in (c.title_en or "") or c.program_type == "นานาชาติ"
        matched_fee = None
        matched_semesters = 8

        # 1. Check special/international rules
        if is_inter:
            for sp in SPECIAL_PROGRAMS:
                if sp["keyword"].lower() in (c.title_en or "").lower() or sp["title_match"] in (c.title_th or ""):
                    matched_fee = sp["fee"]
                    matched_semesters = sp["semesters"]
                    break
            if not matched_fee:
                # Default international rate
                matched_fee = "85,000 บาท"
                matched_semesters = 8
        else:
            # 2. Check Faculty standard rate
            for fac_name, fee_info in CU_FACULTY_TUITION_MAP.items():
                if c.faculty_th and (fac_name in c.faculty_th or c.faculty_th in fac_name):
                    matched_fee = fee_info["per_sem"]
                    matched_semesters = fee_info["semesters"]
                    break

        if matched_fee:
            c.tuition_per_semester = matched_fee
            fee_num = int(matched_fee.replace(" บาท", "").replace(",", ""))
            c.tuition_total = f"{fee_num * matched_semesters:,} บาท"
            enriched_count += 1

            # Update embedding text
            tags_str = " ".join(c.tags) if c.tags else ""
            career_str = " ".join(c.career_paths) if c.career_paths else ""
            t_en = c.title_en or ""
            f_th = c.faculty_th or ""
            f_en = c.faculty or ""
            desc = c.description or ""
            emb_text = f"{c.title_th} {t_en} {f_th} {f_en} {desc} {career_str} {tags_str}"
            c.embedding_text = emb_text

    db.commit()
    print(f"\nSuccessfully enriched {enriched_count} CU courses with standard tuition fees!")
    db.close()

if __name__ == "__main__":
    enrich_cu()
