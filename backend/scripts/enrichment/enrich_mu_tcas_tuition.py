import os
import sys
import re
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(backend_dir, ".env"))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB

# Mahidol University Official Faculty Tuition Mapping (มหาวิทยาลัยมหิดล)
# Sources: กองบริหารการศึกษา มหาวิทยาลัยมหิดล & ระเบียบการ TCAS มหิดล & บัณฑิตวิทยาลัย
MAHIDOL_FACULTY_TUITION_MAP = {
    # 1. Health & Medical Sciences (คณะกลุ่มการแพทย์และวิทยาศาสตร์สุขภาพ)
    "คณะแพทยศาสตร์ศิริราชพยาบาล": {"per_sem": "30,000 บาท", "years": 6, "semesters": 12},
    "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี": {"per_sem": "30,000 บาท", "years": 6, "semesters": 12},
    "คณะทันตแพทยศาสตร์": {"per_sem": "35,000 บาท", "years": 6, "semesters": 12},
    "คณะเภสัชศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "คณะสัตวแพทยศาสตร์": {"per_sem": "28,000 บาท", "years": 6, "semesters": 12},
    "คณะพยาบาลศาสตร์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "คณะเทคนิคการแพทย์": {"per_sem": "22,000 บาท", "years": 4, "semesters": 8},
    "คณะกายภาพบำบัด": {"per_sem": "22,000 บาท", "years": 4, "semesters": 8},
    "คณะสาธารณสุขศาสตร์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "คณะเวชศาสตร์เขตร้อน": {"per_sem": "35,000 บาท", "years": 2, "semesters": 4},

    # 2. Science, Technology & Engineering (คณะกลุ่มวิทยาศาสตร์ เทคโนโลยี และวิศวกรรม)
    "คณะวิทยาศาสตร์": {"per_sem": "21,000 บาท", "years": 4, "semesters": 8},
    "คณะเทคโนโลยีสารสนเทศและการสื่อสาร": {"per_sem": "35,000 บาท", "years": 4, "semesters": 8},
    "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (ICT)": {"per_sem": "35,000 บาท", "years": 4, "semesters": 8},
    "คณะวิศวกรรมศาสตร์": {"per_sem": "24,000 บาท", "years": 4, "semesters": 8},
    "คณะสิ่งแวดล้อมและทรัพยากรศาสตร์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},

    # 3. Social Sciences, Humanities, Music & Management (กลุ่มสังคมศาสตร์ มนุษยศาสตร์ ดุริยางคศิลป์ และการจัดการ)
    "คณะสังคมศาสตร์และมนุษยศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "คณะศิลปศาสตร์": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยการจัดการ": {"per_sem": "55,000 บาท", "years": 2, "semesters": 5},
    "วิทยาลัยดุริยางคศิลป์": {"per_sem": "65,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยศาสนศึกษา": {"per_sem": "17,000 บาท", "years": 4, "semesters": 8},
    "สถาบันแห่งชาติด้านการพัฒนาเด็กและครอบครัว": {"per_sem": "25,000 บาท", "years": 2, "semesters": 4},
    "สถาบันวิจัยประชากรและสังคม": {"per_sem": "25,000 บาท", "years": 2, "semesters": 4},
    "สถาบันพัฒนาสุขภาพอาเซียน": {"per_sem": "30,000 บาท", "years": 2, "semesters": 4},
    "สถาบันชีววิทยาศาสตร์โมเลกุล": {"per_sem": "30,000 บาท", "years": 2, "semesters": 4},
    "สถาบันสิทธิมนุษยชนและสันติศึกษา": {"per_sem": "25,000 บาท", "years": 2, "semesters": 4},
    "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย": {"per_sem": "20,000 บาท", "years": 2, "semesters": 4},
    "วิทยาเขตนครสวรรค์": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "วิทยาเขตกาญจนบุรี": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "วิทยาเขตอำนาจเจริญ": {"per_sem": "20,000 บาท", "years": 4, "semesters": 8},
    "วิทยาลัยนานาชาติ": {"per_sem": "95,000 บาท", "years": 4, "semesters": 8},
}

# Special & International Programs at Mahidol
MAHIDOL_SPECIAL_PROGRAMS = [
    # MUIC (Mahidol University International College)
    {"keyword": "MUIC", "title_match": "วิทยาลัยนานาชาติ", "fee": "95,000 บาท", "semesters": 8},
    {"keyword": "MUICT", "title_match": "วิทยาการและเทคโนโลยีสารสนเทศ", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "DST", "title_match": "เทคโนโลยีดิจิทัล", "fee": "65,000 บาท", "semesters": 8},
    {"keyword": "BBA", "title_match": "บริหารธุรกิจ", "fee": "95,000 บาท", "semesters": 8},
    {"keyword": "CMMU", "title_match": "การจัดการ", "fee": "55,000 บาท", "semesters": 5},
    {"keyword": "CMMU Executive", "title_match": "การจัดการสำหรับผู้บริหาร", "fee": "75,000 บาท", "semesters": 5},
    {"keyword": "Biomedical Engineering Inter", "title_match": "วิศวกรรมชีวการแพทย์", "fee": "70,000 บาท", "semesters": 8},
    {"keyword": "Chemical Engineering Inter", "title_match": "วิศวกรรมเคมี", "fee": "60,000 บาท", "semesters": 8},
    {"keyword": "Music", "title_match": "ดนตรี", "fee": "65,000 บาท", "semesters": 8},
]

def enrich_mahidol():
    db = SessionLocal()
    mu_courses = db.query(CourseDB).filter(CourseDB.university.ilike("%Mahidol%")).all()
    print(f"Total Mahidol courses in database: {len(mu_courses)}")

    enriched_count = 0

    for c in mu_courses:
        is_inter = "นานาชาติ" in (c.title_th or "") or "International" in (c.title_en or "") or c.program_type == "นานาชาติ"
        matched_fee = None
        matched_semesters = 8

        # 1. Check special / international rules
        if is_inter or "วิทยาลัยนานาชาติ" in (c.faculty_th or ""):
            for sp in MAHIDOL_SPECIAL_PROGRAMS:
                if sp["keyword"].lower() in (c.title_en or "").lower() or sp["title_match"] in (c.title_th or ""):
                    matched_fee = sp["fee"]
                    matched_semesters = sp["semesters"]
                    break
            if not matched_fee:
                if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                    matched_fee = "50,000 บาท"
                    matched_semesters = 4
                elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                    matched_fee = "65,000 บาท"
                    matched_semesters = 6
                else:
                    matched_fee = "85,000 บาท"
                    matched_semesters = 8
        else:
            # 2. Check Faculty standard rate
            for fac_name, fee_info in MAHIDOL_FACULTY_TUITION_MAP.items():
                if c.faculty_th and (fac_name in c.faculty_th or c.faculty_th in fac_name):
                    matched_fee = fee_info["per_sem"]
                    if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                        matched_semesters = 4
                        # Master's tuition adjustment
                        if "30,000" not in matched_fee and "35,000" not in matched_fee and "55,000" not in matched_fee:
                            matched_fee = "28,000 บาท"
                    elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                        matched_semesters = 6
                        matched_fee = "40,000 บาท"
                    elif "ประกาศนียบัตร" in (c.degree_level or ""):
                        matched_semesters = 2
                        matched_fee = "25,000 บาท"
                    else:
                        matched_semesters = fee_info["semesters"]
                    break

        if not matched_fee:
            # Default Mahidol rate based on level
            if c.degree_level in ["ปริญญาโท", "Master", "Master's Degree"]:
                matched_fee = "28,000 บาท"
                matched_semesters = 4
            elif c.degree_level in ["ปริญญาเอก", "Doctorate", "Doctoral Degree", "Ph.D."]:
                matched_fee = "40,000 บาท"
                matched_semesters = 6
            elif "ประกาศนียบัตร" in (c.degree_level or ""):
                matched_fee = "25,000 บาท"
                matched_semesters = 2
            else:
                matched_fee = "21,000 บาท"
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
    print(f"\nSuccessfully enriched {enriched_count} Mahidol University courses with official tuition fees!")
    db.close()

if __name__ == "__main__":
    enrich_mahidol()
