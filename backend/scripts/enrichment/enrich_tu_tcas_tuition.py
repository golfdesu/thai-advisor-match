import os
import sys
import re
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB

# Thammasat University (TU) Official Tuition Fees Mapping
# Sources: กองบริหารวิชาการ มหาวิทยาลัยธรรมศาสตร์ & ระเบียบการ TCAS ธรรมศาสตร์
TU_FACULTY_TUITION_MAP = {
    # 1. Health & Medical Sciences (กลุ่มวิทยาศาสตร์สุขภาพ)
    "คณะแพทยศาสตร์": {"per_sem": "30,000 บาท", "years": 6, "semesters": 12},
    "คณะทันตแพทยศาสตร์": {"per_sem": "35,000 บาท", "years": 6, "semesters": 12},
    "คณะเภสัชศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "วิทยาลัยแพทยศาสตร์นานาชาติจฬุาภรณ์": {"per_sem": "150,000 บาท", "years": 6, "semesters": 12},
    "วิทยาลัยแพทยศาสตร์นานาชาติจุฬาภรณ์": {"per_sem": "150,000 บาท", "years": 6, "semesters": 12},
    "CICM": {"per_sem": "150,000 บาท", "years": 6, "semesters": 12},
    "คณะสหเวชศาสตร์": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},
    "คณะพยาบาลศาสตร์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "คณะสาธารณสุขศาสตร์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},

    # 2. Science, Technology & Engineering (กลุ่มวิทยาศาสตร์และเทคโนโลยี)
    "สถาบันเทคโนโลยีนานาชาติสิรินธร": {"per_sem": "85,000 บาท", "years": 4, "semesters": 8},
    "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)": {"per_sem": "85,000 บาท", "years": 4, "semesters": 8},
    "SIIT": {"per_sem": "85,000 บาท", "years": 4, "semesters": 8},
    "คณะวิศวกรรมศาสตร์": {"per_sem": "24,000 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาศาสตร์และเทคโนโลยี": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "คณะสถาปัตยกรรมศาสตร์และการผังเมือง": {"per_sem": "24,000 บาท", "years": 5, "semesters": 10},

    # 3. Social Sciences, Humanities, Management & Law (กลุ่มสังคมศาสตร์ มนุษยศาสตร์ การจัดการ และกฎหมาย)
    "คณะนิติศาสตร์": {"per_sem": "16,500 บาท", "years": 4, "semesters": 8},
    "คณะพาณิชยศาสตร์ และการบัญชี": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะพาณิชยศาสตร์และการบัญชี": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะรัฐศาสตร์": {"per_sem": "16,500 บาท", "years": 4, "semesters": 8},
    "คณะเศรษฐศาสตร์": {"per_sem": "16,500 บาท", "years": 4, "semesters": 8},
    "คณะสังคมสงเคราะห์ศาสตร์": {"per_sem": "16,000 บาท", "years": 4, "semesters": 8},
    "คณะสังคมวิทยาและมานุษยวิทยา": {"per_sem": "16,000 บาท", "years": 4, "semesters": 8},
    "คณะศิลปศาสตร์": {"per_sem": "16,500 บาท", "years": 4, "semesters": 8},
    "คณะวารสารศาสตร์และสื่อสารมวลชน": {"per_sem": "16,500 บาท", "years": 4, "semesters": 8},
    "คณะศิลปกรรมศาสตร์": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},
    "คณะวิทยาการเรียนรู้และศึกษาศาสตร์": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยสหวิทยาการ": {"per_sem": "18,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยนวัตกรรม": {"per_sem": "35,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยนานาชาติ ปรีดี พนมยงค์": {"per_sem": "65,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยโลกคดีศึกษา": {"per_sem": "70,000 บาท", "years": 4, "semesters": 8},
}

# Special & International Programs at Thammasat
TU_SPECIAL_PROGRAMS = [
    {"keyword": "SIIT", "title_match": "สิรินธร", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "BBA", "title_match": "บริหารธุรกิจบัณฑิต (หลักสูตรนานาชาติ)", "fee": "95,000 บาท", "semesters": 8},
    {"keyword": "BE", "title_match": "เศรษฐศาสตรบัณฑิต (หลักสูตรนานาชาติ)", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "BIR", "title_match": "การเมืองและการระหว่างประเทศ", "fee": "75,000 บาท", "semesters": 8},
    {"keyword": "BMIR", "title_match": "การเมืองและการระหว่างประเทศ (ปริญญาโท)", "fee": "65,000 บาท", "semesters": 4},
    {"keyword": "TEP", "title_match": "TEP", "fee": "120,000 บาท", "semesters": 8},
    {"keyword": "TEPE", "title_match": "TEPE", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "AUTO", "title_match": "ยานยนต์", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "CPE Inter", "title_match": "วิศวกรรมคอมพิวเตอร์ (นานาชาติ)", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "PBIC", "title_match": "ปรีดี พนมยงค์", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "GSSE", "title_match": "โลกคดีศึกษา", "fee": "70,000 บาท", "semesters": 8},
    {"keyword": "SPD", "title_match": "การพัฒนานโยบายสาธารณะ", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "BJM", "title_match": "วารสารศาสตร์ (นานาชาติ)", "fee": "70,000 บาท", "semesters": 8},
    {"keyword": "DBTM", "title_match": "การจัดการการออกแบบ ธุรกิจ และเทคโนโลยี", "fee": "85,000 บาท", "semesters": 8},
    {"keyword": "UDDI", "title_match": "การออกแบบและการพัฒนาเมือง", "fee": "85,000 บาท", "semesters": 8},
]

def enrich_tu():
    db = SessionLocal()
    tu_courses = db.query(CourseDB).filter(CourseDB.university.ilike("%Thammasat%")).all()
    print(f"Total Thammasat courses in database to process: {len(tu_courses)}")

    enriched_count = 0

    for c in tu_courses:
        is_inter = "นานาชาติ" in (c.title_th or "") or "International" in (c.title_en or "") or c.program_type == "นานาชาติ" or "SIIT" in (c.title_en or "") or "SIIT" in (c.faculty_th or "")
        matched_fee = None
        matched_semesters = 8

        # 1. Check special / international rules
        if is_inter:
            for sp in TU_SPECIAL_PROGRAMS:
                if sp["keyword"].lower() in (c.title_en or "").lower() or sp["title_match"] in (c.title_th or ""):
                    matched_fee = sp["fee"]
                    matched_semesters = sp["semesters"]
                    break
            if not matched_fee:
                if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                    matched_fee = "55,000 บาท"
                    matched_semesters = 4
                elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                    matched_fee = "70,000 บาท"
                    matched_semesters = 6
                else:
                    matched_fee = "75,000 บาท"
                    matched_semesters = 8
        else:
            # 2. Check Faculty standard rate
            for fac_name, fee_info in TU_FACULTY_TUITION_MAP.items():
                if c.faculty_th and (fac_name in c.faculty_th or c.faculty_th in fac_name):
                    matched_fee = fee_info["per_sem"]
                    if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                        matched_semesters = 4
                        if "30,000" not in matched_fee and "35,000" not in matched_fee:
                            matched_fee = "25,000 บาท"
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
                matched_fee = "25,000 บาท"
                matched_semesters = 4
            elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                matched_fee = "35,000 บาท"
                matched_semesters = 6
            elif "ประกาศนียบัตร" in (c.degree_level or ""):
                matched_fee = "20,000 บาท"
                matched_semesters = 2
            else:
                matched_fee = "17,000 บาท"
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
    print(f"\nSuccessfully enriched {enriched_count} Thammasat University courses with official tuition fees!")
    db.close()

if __name__ == "__main__":
    enrich_tu()
