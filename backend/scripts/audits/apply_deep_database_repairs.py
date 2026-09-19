# -*- coding: utf-8 -*-
"""
Apply Deep Database Repairs for Residual Anomalies.

Applies:
1. Purge non-person structural records (3):
   - cu_cbs_wave11_0441 ('อ. นอกคณะ')
   - tu_14e72924_5384 ('อ. กรรมการประจำคณะ')
   - khonkaenun_facultyofm_fac_011_011 ('รศ. พญ.')
2. Clean false CERN Peter Jenni OpenAlex match & restore authentic Chula Pharmacy professor:
   - chulalongk_facultyofp_fac_036_036 -> ผศ.ภญ.ดร. เจนนิษฐ์ มั่นแย้ม (Jennit Manyaem)
3. Clean job position grade from person name:
   - cu_pharm_wave16_0078 -> ดร. สมภพ ถมโพธิ์ (Sompop Thompho)
4. Synchronize authoritative OpenAlex metrics:
   - ku_wave17_econ_0044 -> h_index=1, total_citations=9, total_publications_count=1
   - mahidoluni_facultyofs_pattarakijwanic_096 -> h_index=8, total_citations=678, total_publications_count=22
5. Fix university affiliation and restore full names for Thaksin University faculty (5):
   - regionalun_facultymem_fac_088_088 .. fac_092_092 -> Thaksin University (มหาวิทยาลัยทักษิณ)
6. Data hygiene standardization:
   - Clean research_interests = ['-'] to []
   - Normalize academic title spacing ('ผศ. ดร.' -> 'ผศ.ดร.', 'รศ. ดร.' -> 'รศ.ดร.', 'อ. ดร.' -> 'อ.ดร.')
   - Normalize course degree_level ('ประกาศนียบัตรบัณฑิต (ชั้นสูง)' -> 'ประกาศนียบัตรบัณฑิตชั้นสูง')
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB


def apply_deep_repairs():
    db = SessionLocal()
    print("=" * 65)
    print("🚀 APPLYING DEEP DATABASE REPAIRS")
    print("=" * 65)

    try:
        # 1. Purge non-person structural records (3)
        to_purge = [
            "cu_cbs_wave11_0441",
            "tu_14e72924_5384",
            "khonkaenun_facultyofm_fac_011_011",
        ]
        for fid in to_purge:
            rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if rec:
                print(f"🗑️ Purging non-person record: {rec.id} ({rec.full_name_th})")
                db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == rec.id).update(
                    {ResearchLabDB.lead_advisor_id: None}
                )
                db.delete(rec)

        # 2. Fix Chula Pharmacy Jennit Manyaem & clear false CERN Peter Jenni match
        jennit = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofp_fac_036_036").first()
        if jennit:
            print(f"✅ Restoring Chula Pharmacy faculty & clearing CERN Peter Jenni match: {jennit.id}")
            jennit.full_name_th = "ผศ.ภญ.ดร. เจนนิษฐ์ มั่นแย้ม"
            jennit.academic_title_th = "ผศ.ดร."
            jennit.first_name = "Jennit"
            jennit.last_name = "Manyaem"
            jennit.openalex_id = None
            jennit.h_index = 0
            jennit.total_citations = 0
            jennit.total_publications_count = 0
            jennit.featured_publications = []

        # 3. Clean job position grade from person name
        sompop = db.query(FacultyDB).filter(FacultyDB.id == "cu_pharm_wave16_0078").first()
        if sompop:
            print(f"✅ Cleaning AR-5 job position grade from name: {sompop.id}")
            sompop.full_name_th = "ดร. สมภพ ถมโพธิ์"
            sompop.academic_title_th = "ดร."
            sompop.first_name = "Sompop"
            sompop.last_name = "Thompho"

        # 4. Sync authoritative OpenAlex metrics
        orachos = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave17_econ_0044").first()
        if orachos:
            print(f"📊 Syncing authoritative OpenAlex metrics for Orachos Napasintuwong: {orachos.id}")
            orachos.h_index = 1
            orachos.total_citations = 9
            orachos.total_publications_count = 1

        petchara = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofs_pattarakijwanic_096").first()
        if petchara:
            print(f"📊 Syncing authoritative OpenAlex metrics for Petchara Pattarakijwanich: {petchara.id}")
            petchara.h_index = 8
            petchara.total_citations = 678
            petchara.total_publications_count = 22

        # 5. Fix university affiliation and restore full names for Thaksin University faculty
        tsu_map = {
            "regionalun_facultymem_fac_088_088": {
                "full_name_th": "รศ.ดร. รุ่งรวี สุวรรณจินดา",
                "academic_title_th": "รศ.ดร.",
                "first_name": "Rungrawee",
                "last_name": "Suwanjinda",
            },
            "regionalun_facultymem_fac_089_089": {
                "full_name_th": "อ.ดร. ศันสนีย์ สุรเนตร",
                "academic_title_th": "อ.ดร.",
                "first_name": "Sansanee",
                "last_name": "Suranetr",
            },
            "regionalun_facultymem_fac_090_090": {
                "full_name_th": "อ. เทียนทิพย์ ธนชิตกุล",
                "academic_title_th": "อ.",
                "first_name": "Thiantip",
                "last_name": "Thanachitkul",
            },
            "regionalun_facultymem_fac_091_091": {
                "full_name_th": "อ. วันพระ อ่อนน้อม",
                "academic_title_th": "อ.",
                "first_name": "Wanpra",
                "last_name": "Onnom",
            },
            "regionalun_facultymem_fac_092_092": {
                "full_name_th": "อ. วันวิสา มูฮำหมัด",
                "academic_title_th": "อ.",
                "first_name": "Wanwisa",
                "last_name": "Muhamad",
            },
        }
        for fid, attrs in tsu_map.items():
            tf = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if tf:
                print(f"🏛️ Re-assigning to Thaksin University: {fid} -> {attrs['full_name_th']}")
                tf.university = "Thaksin University"
                tf.university_th = "มหาวิทยาลัยทักษิณ"
                tf.faculty = "Faculty of Music and Performing Arts"
                tf.faculty_th = "คณะดุริยางคศาสตร์และศิลปะการแสดง"
                for k, v in attrs.items():
                    setattr(tf, k, v)

        # 6. Data hygiene standardization
        # Clean dash-only research interests
        dash_facs = db.query(FacultyDB).filter(FacultyDB.research_interests.isnot(None)).all()
        dash_count = 0
        for f in dash_facs:
            if f.research_interests == ["-"] or f.research_interests == [""]:
                f.research_interests = []
                dash_count += 1
        print(f"🧹 Cleaned dash-only research_interests: {dash_count} faculties")

        # Normalize academic title spacing in faculties
        title_space_map = {
            "ผศ. ดร.": "ผศ.ดร.",
            "รศ. ดร.": "รศ.ดร.",
            "อ. ดร.": "อ.ดร.",
            "ศ. ดร.": "ศ.ดร.",
        }
        title_fix_count = 0
        for old_t, new_t in title_space_map.items():
            matches = db.query(FacultyDB).filter(FacultyDB.academic_title_th == old_t).all()
            for m in matches:
                m.academic_title_th = new_t
                title_fix_count += 1
        print(f"✨ Standardized academic title spacing: {title_fix_count} faculties")

        # Normalize course degree_level
        course_fixes = (
            db.query(CourseDB)
            .filter(CourseDB.degree_level == "ประกาศนียบัตรบัณฑิต (ชั้นสูง)")
            .all()
        )
        for c in course_fixes:
            c.degree_level = "ประกาศนียบัตรบัณฑิตชั้นสูง"
        print(f"🎓 Standardized degree_level for courses: {len(course_fixes)} courses")

        db.commit()
        print("\n" + "=" * 65)
        print("✅ ALL DEEP DATABASE REPAIRS COMMITTED SUCCESSFULLY")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during repair execution: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_deep_repairs()
