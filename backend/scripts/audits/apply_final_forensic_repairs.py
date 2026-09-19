# -*- coding: utf-8 -*-
"""
Apply Final Forensic Repairs for Full Database Standardization.

Applies:
1. Fix name & contact glitches:
   - cmu_398c4c40_5859: อ.พญ. ภาศิริ สิงหศิริ (Pasiri Singhasiri, pasiri.s@cmu.ac.th)
   - chula_eng_cp_chentanez: อ.ดร. ณัฐพงศ์ เจนตระกูล (Nuttapong Chentanez, nuttapong.ch@chula.ac.th)
2. Fix single-character English first names (4 records at KMITL and MSU).
3. Clean parenthetical artifacts from full_name_th (5 records at UP, CMU, NU).
4. Standardize uncontracted academic titles (57 records across medical/dental faculties).
5. Standardize course duration_years format (append 'ปี' to raw numeric strings).
"""

import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB


def apply_forensic_repairs():
    db = SessionLocal()
    print("=" * 65)
    print("🚀 APPLYING FINAL FORENSIC REPAIRS")
    print("=" * 65)

    try:
        # 1. Name & contact glitches
        pasiri = db.query(FacultyDB).filter(FacultyDB.id == "cmu_398c4c40_5859").first()
        if pasiri:
            print(f"✅ Correcting Pasiri Singhasiri profile & email: {pasiri.id}")
            pasiri.full_name_th = "อ.พญ. ภาศิริ สิงหศิริ"
            pasiri.academic_title_th = "อ.พญ."
            pasiri.first_name = "Pasiri"
            pasiri.last_name = "Singhasiri"
            pasiri.email = "pasiri.s@cmu.ac.th"

        chentanez = db.query(FacultyDB).filter(FacultyDB.id == "chula_eng_cp_chentanez").first()
        if chentanez:
            print(f"✅ Correcting Nuttapong Chentanez profile: {chentanez.id}")
            chentanez.full_name_th = "อ.ดร. ณัฐพงศ์ เจนตระกูล"
            chentanez.academic_title_th = "อ.ดร."
            chentanez.first_name = "Nuttapong"
            chentanez.last_name = "Chentanez"
            chentanez.email = "nuttapong.ch@chula.ac.th"

        # 2. Single-character English first names
        en_fixes = {
            "kmitl_s_tipawan_4803": ("Tipawan", "Klaiboonmee"),
            "msu_k_chaimoon_2142": ("Krisn", "Chaimoon"),
            "msu_n_meeso_6596": ("Nares", "Meeso"),
            "msu_n_seelsaen_4159": ("Nida", "Chaimoon"),
        }
        for fid, (fn, ln) in en_fixes.items():
            rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if rec:
                print(f"✅ Fixing English name: {fid} -> {fn} {ln}")
                rec.first_name = fn
                rec.last_name = ln

        # 3. Clean parenthetical artifacts from full_name_th
        paren_fixes = {
            "universi_schoolof_b7555d98": {
                "full_name_th": "ผศ. จิรวัฒน์ สุขแก้ว",
                "academic_title_th": "ผศ.",
                "first_name": "Jirawat",
                "last_name": "Sukkaew",
            },
            "universi_schoolof_fde34f16": {
                "full_name_th": "อ. ศักดิ์พันธุ์ แดงมณี",
                "academic_title_th": "อ.",
                "first_name": "Sakphan",
                "last_name": "Daengmanee",
            },
            "universi_schoolof_560b2cd6": {
                "full_name_th": "อ. อดิศยา เจริญผล",
                "academic_title_th": "อ.",
                "first_name": "Adisaya",
                "last_name": "Charoenphon",
            },
            "cmu_eng_department_nakorn_96": {
                "full_name_th": "ศ.ดร. นคร ทิพยาวงศ์",
            },
            "nu_suchada_ukaew_3240": {
                "full_name_th": "ผศ.ดร. สุชาดา อยู่แก้ว",
            },
        }
        for fid, attrs in paren_fixes.items():
            rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if rec:
                print(f"🧹 Cleaning parenthetical artifact: {fid} -> {attrs['full_name_th']}")
                for k, v in attrs.items():
                    setattr(rec, k, v)

        # 4. Standardize uncontracted academic titles (57 records)
        title_contractions = {
            "ศาสตราจารย์ นพ.": "ศ.นพ.",
            "รองศาสตราจารย์ พญ.": "รศ.พญ.",
            "รองศาสตราจารย์ นพ.": "รศ.นพ.",
            "ศาสตราจารย์ พญ.": "ศ.พญ.",
            "รองศาสตราจารย์ ดร.นพ.": "รศ.ดร.นพ.",
            "ศาสตราจารย์ ดร. นพ.": "ศ.ดร.นพ.",
            "ศาสตราจารย์ ดร.นพ.": "ศ.ดร.นพ.",
            "รองศาสตราจารย์ ดร.ทันตแพทย์หญิง": "รศ.ดร.ทญ.",
            "ผู้ช่วยศาสตราจารย์ ดร.ทันตแพทย์หญิง": "ผศ.ดร.ทญ.",
            "ศาสตราจารย์ ดร.ทันตแพทย์หญิง": "ศ.ดร.ทญ.",
            "ผู้ช่วยศาสตราจารย์ นพ.": "ผศ.นพ.",
            "ผู้ช่วยศาสตราจารย์ พญ. ดร.": "ผศ.ดร.พญ.",
            "ผู้ช่วยศาสตราจารย์ ดร. นพ.": "ผศ.ดร.นพ.",
            "ศาสตราจารย์กิตติคุณ": "ศ.เกียรติคุณ",
            "ศ. กิตติคุณ": "ศ.เกียรติคุณ",
            "ศ.เกียรติคุณ ดร.": "ศ.ดร.",
        }
        uncontracted_count = 0
        for old_t, new_t in title_contractions.items():
            matches = db.query(FacultyDB).filter(FacultyDB.academic_title_th == old_t).all()
            for m in matches:
                m.academic_title_th = new_t
                # Also ensure full_name_th reflects the contracted title
                if m.full_name_th and m.full_name_th.startswith(old_t):
                    m.full_name_th = new_t + m.full_name_th[len(old_t):]
                uncontracted_count += 1
        print(f"✨ Contracted academic titles: {uncontracted_count} faculties")

        # 5. Standardize course duration_years format
        course_dur_count = 0
        courses = db.query(CourseDB).filter(CourseDB.duration_years.isnot(None)).all()
        for c in courses:
            dur = c.duration_years.strip()
            if dur.isdigit():
                c.duration_years = f"{dur} ปี"
                course_dur_count += 1
            elif dur == "ไม่ระบุ":
                pass
        print(f"🎓 Standardized duration_years format: {course_dur_count} courses")

        db.commit()
        print("\n" + "=" * 65)
        print("✅ ALL FINAL FORENSIC REPAIRS COMMITTED SUCCESSFULLY")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during forensic repair execution: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_forensic_repairs()
