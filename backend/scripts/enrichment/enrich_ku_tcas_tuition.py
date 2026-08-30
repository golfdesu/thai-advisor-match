import os
import sys
import re
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB

# Kasetsart University (KU) Official Tuition Rate Mapping
# Sources: กองบริหารการศึกษา มหาวิทยาลัยเกษตรศาสตร์ & ระเบียบการ TCAS มก. (ทุกวิทยาเขต)
KU_FACULTY_TUITION_MAP = {
    # 1. Health & Medical Sciences
    "คณะแพทยศาสตร์": {"per_sem": "35,000 บาท", "years": 6, "semesters": 12},
    "คณะสัตวแพทยศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "คณะเทคโนโลยีการสัตวแพทย์": {"per_sem": "22,000 บาท", "years": 4, "semesters": 8},
    "คณะเทคนิคการสัตวแพทย์": {"per_sem": "22,000 บาท", "years": 4, "semesters": 8},
    "คณะพยาบาลศาสตร์": {"per_sem": "22,000 บาท", "years": 4, "semesters": 8},
    "คณะเภสัชศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "คณะสาธารณสุขศาสตร์": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},

    # 2. Engineering, Science & Tech
    "คณะวิศวกรรมศาสตร์": {"per_sem": "17,300 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาศาสตร์": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "คณะสถาปัตยกรรมศาสตร์": {"per_sem": "21,300 บาท", "years": 5, "semesters": 10},
    "คณะวิทยาศาสตร์และวิศวกรรมศาสตร์": {"per_sem": "17,300 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาการจัดการ": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะพาณิชยนาวีนานาชาติ": {"per_sem": "24,000 บาท", "years": 4, "semesters": 8},

    # 3. Agriculture, Forestry, Fisheries & Agro-Industry
    "คณะเกษตร": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "คณะวนศาสตร์": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "คณะประมง": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "คณะอุตสาหกรรมเกษตร": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "คณะสิ่งแวดล้อม": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "คณะทรัพยากรธรรมชาติและอุตสาหกรรมเกษตร": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},

    # 4. Business, Economics, Humanities, Social & Education
    "คณะบริหารธุรกิจ": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะเศรษฐศาสตร์": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะมนุษยศาสตร์": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะสังคมศาสตร์": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะศึกษาศาสตร์": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะศึกษาศาสตร์และพัฒนศาสตร์": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะศิลปศาสตร์และวิทยาการจัดการ": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะศิลปศาสตร์และวิทยาศาสตร์": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
    "คณะอุตสาหกรรมบริการ": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยบูรณาการศาสตร์": {"per_sem": "16,300 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยการชลประทาน": {"per_sem": "17,300 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาศาสตร์การกีฬา": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาศาสตร์การกีฬาและสุขภาพ": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},
    "คณะสหวิทยาการจัดการและเทคโนโลยี (สุพรรณบุรี)": {"per_sem": "15,300 บาท", "years": 4, "semesters": 8},
}

# Special & International Programs at KU
KU_SPECIAL_PROGRAMS = [
    {"keyword": "IUP", "title_match": "IUP", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "IDD", "title_match": "นานาชาติ", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "KUBIM", "title_match": "การจัดการธุรกิจระหว่างประเทศ (นานาชาติ)", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "KUBUS", "title_match": "บริหารธุรกิจ (นานาชาติ)", "fee": "60,000 บาท", "semesters": 8},
    {"keyword": "EEBA", "title_match": "เศรษฐศาสตร์ผู้ประกอบการ (นานาชาติ)", "fee": "55,000 บาท", "semesters": 8},
    {"keyword": "BEcon Inter", "title_match": "เศรษฐศาสตร์ (นานาชาติ)", "fee": "55,000 บาท", "semesters": 8},
    {"keyword": "Aerospace", "title_match": "วิศวกรรมการบินและอวกาศ", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "Software & Knowledge", "title_match": "วิศวกรรมซอฟต์แวร์และความรู้", "fee": "60,000 บาท", "semesters": 8},
    {"keyword": "ภาคพิเศษ", "title_match": "ภาคพิเศษ", "fee": "35,000 บาท", "semesters": 8},
]

def enrich_ku():
    db = SessionLocal()
    ku_courses = db.query(CourseDB).filter(CourseDB.university.ilike("%Kasetsart%")).all()
    print(f"Total Kasetsart courses in database to process: {len(ku_courses)}")

    enriched_count = 0

    for c in ku_courses:
        is_inter = "นานาชาติ" in (c.title_th or "") or "International" in (c.title_en or "") or c.program_type == "นานาชาติ"
        is_special = "ภาคพิเศษ" in (c.title_th or "") or "ภาคพิเศษ" in (c.program_type or "") or "Special" in (c.title_en or "")
        matched_fee = None
        matched_semesters = 8

        # 1. Check special / international rules
        if is_inter or is_special:
            for sp in KU_SPECIAL_PROGRAMS:
                if sp["keyword"].lower() in (c.title_en or "").lower() or sp["title_match"] in (c.title_th or ""):
                    matched_fee = sp["fee"]
                    matched_semesters = sp["semesters"]
                    break
            if not matched_fee:
                if is_inter:
                    if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                        matched_fee = "50,000 บาท"
                        matched_semesters = 4
                    elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                        matched_fee = "65,000 บาท"
                        matched_semesters = 6
                    else:
                        matched_fee = "60,000 บาท"
                        matched_semesters = 8
                elif is_special:
                    if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                        matched_fee = "35,000 บาท"
                        matched_semesters = 4
                    else:
                        matched_fee = "32,000 บาท"
                        matched_semesters = 8
        else:
            # 2. Check Faculty standard rate
            for fac_name, fee_info in KU_FACULTY_TUITION_MAP.items():
                clean_fac = fac_name.replace(" (วิทยาเขตบางเขน)", "").replace(" (วิทยาเขตกำแพงแสน)", "").replace(" (วิทยาเขตศรีราชา)", "")
                if c.faculty_th and (clean_fac in c.faculty_th or c.faculty_th in clean_fac):
                    matched_fee = fee_info["per_sem"]
                    if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                        matched_semesters = 4
                        if "35,000" not in matched_fee:
                            matched_fee = "24,000 บาท"
                    elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                        matched_semesters = 6
                        matched_fee = "35,000 บาท"
                    elif "ประกาศนียบัตร" in (c.degree_level or ""):
                        matched_semesters = 2
                        matched_fee = "20,000 บาท"
                    else:
                        matched_semesters = fee_info["semesters"]
                    break

        if not matched_fee:
            if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                matched_fee = "24,000 บาท"
                matched_semesters = 4
            elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                matched_fee = "35,000 บาท"
                matched_semesters = 6
            elif "ประกาศนียบัตร" in (c.degree_level or ""):
                matched_fee = "20,000 บาท"
                matched_semesters = 2
            else:
                matched_fee = "16,300 บาท"
                matched_semesters = 8

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
    print(f"\nSuccessfully enriched {enriched_count} Kasetsart University courses with official tuition fees!")
    db.close()

if __name__ == "__main__":
    enrich_ku()
