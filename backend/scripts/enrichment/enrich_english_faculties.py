# -*- coding: utf-8 -*-
"""
Enrich missing English faculty names in database
Maps authentic English faculty names from faculty_th for any records where faculty is NULL or empty string.
"""

import sys
import time
from pathlib import Path
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from scripts.enrichment.enrich_phase_d_faculties import FACULTY_EN_MAP

ADDITIONAL_MAP = {
    "คณะการจัดการและการท่องเที่ยว": "Faculty of Management and Tourism",
    "คณะเทคโนโลยี": "Faculty of Technology",
    "คณะบริหารธุรกิจเพื่อสังคม": "Faculty of Social Business Administration",
    "คณะบริหารธุรกิจและการบัญชี": "Faculty of Business Administration and Accountancy",
    "คณะประมง": "Faculty of Fisheries",
    "คณะแพทยศาสตร์ศิริราชพยาบาล": "Faculty of Medicine Siriraj Hospital",
    "คณะรัฐศาสตร์และรัฐประศาสนศาสตร์": "Faculty of Political Science and Public Administration",
    "คณะวนศาสตร์": "Faculty of Forestry",
    "คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม (วิทยาเขตสุราษฎร์ธานี)": "Faculty of Science and Industrial Technology (Surat Thani Campus)",
    "คณะวิศวกรรมศาสตร์ ภาควิชาวิศวกรรมชีวการแพทย์ (BART LAB)": "Department of Biomedical Engineering, Faculty of Engineering (BART LAB)",
    "คณะเวชศาสตร์เขตร้อน": "Faculty of Tropical Medicine",
    "คณะเศรษฐศาสตร์และการบริหาร": "Faculty of Economics and Business Administration",
    "คณะสังคมสงเคราะห์ศาสตร์": "Faculty of Social Administration",
    "บัณฑิตวิทยาลัยพลังงาน สิ่งแวดล้อมและวัสดุ": "School of Energy, Environment and Materials",
    "บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม (JGSEE)": "The Joint Graduate School of Energy and Environment (JGSEE)",
    "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)",
    "วิทยาลัยการจัดการ (CMMU)": "College of Management Mahidol University (CMMU)",
    "วิทยาลัยนวัตกรรมสื่อสารสังคม": "College of Social Communication Innovation",
    "วิทยาลัยปิโตรเลียมและปิโตรเคมี": "Petroleum and Petrochemical College",
    "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี (SGtech)": "School of Renewable Energy and Smart Grid Technology (SGtech)",
    "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา": "College of Sports Science and Technology",
    "ศูนย์วิจัยวัคซีน คณะแพทยศาสตร์": "Vaccine Research Center, Faculty of Medicine",
    "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ฯ": "Sasin School of Management",
    "สถาบันภาษา": "Language Institute",
    "สถาบันโภชนาการ": "Institute of Nutrition",
    "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย (RILCA)": "Research Institute for Languages and Cultures of Asia (RILCA)",
    "สำนักวิจัยวิศวกรรมและเทคโนโลยี": "Engineering and Technology Research Center",
    "สำนักวิชาเทคโนโลยีดิจิทัลประยุกต์": "School of Applied Digital Technology",
    "สำนักวิชานิติศาสตร์": "School of Law",
    "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง": "School of Cosmetic Science",
    "สำนักวิชาวิทยาศาสตร์สุขภาพ": "School of Health Science",
    "สำนักวิชาอุตสาหกรรมเกษตร": "School of Agro-Industry",
}

FULL_MAP = {**FACULTY_EN_MAP, **ADDITIONAL_MAP}


def run_enrich_english():
    start = time.time()
    db = SessionLocal()
    try:
        updated_total = 0
        for fth, fen in FULL_MAP.items():
            res = db.execute(text("""
                UPDATE faculties
                SET faculty = :fen
                WHERE faculty_th = :fth
                  AND (faculty IS NULL OR trim(faculty) = :empty)
            """), {"fen": fen, "fth": fth, "empty": ""})
            updated_total += res.rowcount

        db.commit()
        elapsed = time.time() - start
        print(f"✅ Enriched English faculty names for {updated_total:,} records in {elapsed:.2f}s")
    finally:
        db.close()


if __name__ == "__main__":
    run_enrich_english()
