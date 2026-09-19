# -*- coding: utf-8 -*-
"""
Apply Comprehensive Database Hygiene Repairs.

Covers 7 Audit Categories:
1. Merge CMU duplicate profiles:
   - cmu_21646dd5_9077 -> cmu_398c4c40_5859 (อ.พญ. ภาศิริ สิงหศิริ)
   - cmu_6add0253_6499 -> cmu-med-021_9d90dd (รศ.นพ. สยาม ทองประเสริฐ - corrected title to รศ.นพ.)
2. Administrative decree text cleanup in full_name_th:
   - mu_pharm_wave12_0064 -> ศ.ดร. ลีณา สุนทรสุข (Leena Suntornsuk)
   - mu_pharm_wave12_0096 -> ศ.ดร. ณัฏฐสนันท์ สินชัยพานิช (Nuttanan Sinchaipanid)
3. KKU Agriculture trailing glued titles cleanup (10 faculty records).
4. Hidden control characters & BOM cleanup (\\ufeff, \\u200b, \\t, \\r, \\n, \\xa0).
   - sut_thanasak_phittayakorn_8728 -> อ.ดร. ธนศักดิ์ พิทยากร (Thanasak Phittayakorn)
5. English title & name parsing normalization:
   - mu_pharm_wave12_* (34 records): Assist. Prof. -> ผศ. with clean first_name & last_name.
   - Foreign faculty in full_name_th: Kenneth Cosh, Tri Indrarini Wirjantoro, James Michael Brimson,
     Isaac Adam Jamieson, Nang Hsu Mon Pyae, Shanmugam Nandagopalan, Natthakan Rungraeng.
   - Strip trailing ', Ph.D.' from KKU Science faculty last_name (31 records).
   - Strip trailing comma from CMU last_name ('Siroros,').
6. Impossible OpenAlex metrics normalization:
   - Zero out h_index for faculty with total_citations == 0 and total_publications_count == 0.
   - Normalize Dr. Mikhail Kovachev pubs count to match h-index.
7. Course formatting standardization:
   - Append 'ปี' to numeric duration ranges ('1-2', '3-4', '3 - 4', '0.5', '1.5').
   - Standardize multi-string / English course program_type values (258 courses).
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
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB
from sqlalchemy.orm.attributes import flag_modified


def build_standard_embedding_text(f: FacultyDB) -> str:
    parts = [
        f.full_name_th or "",
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.academic_title_th or "",
        f.university_th or f.university or "",
        f.faculty_th or f.faculty or "",
        f.department_th or f.department or "",
    ]
    if f.research_interests:
        parts.append(" ".join(f.research_interests))
    if f.featured_publications:
        pub_titles = [
            p.get("title", "") if isinstance(p, dict) else str(p)
            for p in f.featured_publications
        ]
        parts.append(" ".join([t for t in pub_titles if t]))
    return " ".join([p for p in parts if p]).strip()


def apply_comprehensive_database_hygiene():
    db = SessionLocal()
    print("=" * 70)
    print("🚀 EXECUTING COMPREHENSIVE DATABASE HYGIENE REPAIRS")
    print("=" * 70)

    try:
        # -------------------------------------------------------------
        # 1. MERGE CMU DUPLICATE PROFILES
        # -------------------------------------------------------------
        # 1.1 Pasiri Singhasiri
        donor_pasiri = db.query(FacultyDB).filter(FacultyDB.id == "cmu_21646dd5_9077").first()
        target_pasiri = db.query(FacultyDB).filter(FacultyDB.id == "cmu_398c4c40_5859").first()
        if donor_pasiri and target_pasiri:
            print(f"🔗 Merging CMU Pasiri donor {donor_pasiri.id} into target {target_pasiri.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_pasiri.id).update(
                {ResearchLabDB.lead_advisor_id: target_pasiri.id}
            )
            # Combine featured publications if target is missing any
            if not target_pasiri.featured_publications and donor_pasiri.featured_publications:
                target_pasiri.featured_publications = donor_pasiri.featured_publications
                flag_modified(target_pasiri, "featured_publications")
            db.delete(donor_pasiri)

        # 1.2 Siam Tongprasert
        donor_siam = db.query(FacultyDB).filter(FacultyDB.id == "cmu_6add0253_6499").first()
        target_siam = db.query(FacultyDB).filter(FacultyDB.id == "cmu-med-021_9d90dd").first()
        if donor_siam and target_siam:
            print(f"🔗 Merging CMU Siam donor {donor_siam.id} into target {target_siam.id}")
            target_siam.full_name_th = "รศ.นพ. สยาม ทองประเสริฐ"
            target_siam.academic_title_th = "รศ.นพ."
            target_siam.first_name = "Siam"
            target_siam.last_name = "Tongprasert"
            target_siam.embedding_text = build_standard_embedding_text(target_siam)
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_siam.id).update(
                {ResearchLabDB.lead_advisor_id: target_siam.id}
            )
            db.delete(donor_siam)

        # -------------------------------------------------------------
        # 2. ADMINISTRATIVE DECREE TEXT CLEANUP
        # -------------------------------------------------------------
        leena = db.query(FacultyDB).filter(FacultyDB.id == "mu_pharm_wave12_0064").first()
        if leena:
            print(f"🏛️ Restoring authentic name for Leena Suntornsuk: {leena.id}")
            leena.full_name_th = "ศ.ดร. ลีณา สุนทรสุข"
            leena.academic_title_th = "ศ.ดร."
            leena.first_name = "Leena"
            leena.last_name = "Suntornsuk"
            leena.embedding_text = build_standard_embedding_text(leena)

        nuttanan = db.query(FacultyDB).filter(FacultyDB.id == "mu_pharm_wave12_0096").first()
        if nuttanan:
            print(f"🏛️ Restoring authentic name for Nuttanan Sinchaipanid: {nuttanan.id}")
            nuttanan.full_name_th = "ศ.ดร. ณัฏฐสนันท์ สินชัยพานิช"
            nuttanan.academic_title_th = "ศ.ดร."
            nuttanan.first_name = "Nuttanan"
            nuttanan.last_name = "Sinchaipanid"
            nuttanan.embedding_text = build_standard_embedding_text(nuttanan)

        # -------------------------------------------------------------
        # 3. KKU AGRICULTURE TRAILING GLUED TITLES
        # -------------------------------------------------------------
        kku_glued = {
            "kku_agri_wave14_b_0079": "รศ.ดร. ประกายจันทร์ นิ่มกิ่งรัตน์",
            "kku_agri_wave14_b_0080": "รศ.ดร. อุบล ตังควานิช",
            "kku_agri_wave14_b_0081": "ผศ.ดร. ดวงรัตน์ ธงภักดิ์",
            "kku_agri_wave14_b_0082": "ผศ.ดร. ยุวธิดา ศรีพลแท่น",
            "kku_agri_wave14_b_0083": "ผศ.ดร. นรินทร์ ชมภูพวง",
            "kku_agri_wave14_b_0084": "อ.ดร. ปพิชญา เตียวกุล",
            "kku_agri_wave14_b_0086": "ผศ.ดร. สุวิตา แสไพศาล",
            "kku_agri_wave14_b_0087": "รศ.ดร. เพชรรัตน์ ธรรมเบญจพล",
            "kku_agri_wave14_b_0088": "ผศ.ดร. กานต์สิรี จินดาปัณณาพัฒน์",
            "kku_agri_wave14_b_0089": "อ.ดร. ชเนรินทร์ ฟ้าแลบ",
        }
        for fid, clean_name in kku_glued.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                print(f"🌾 Cleaning KKU Agriculture glued title: {fid} -> {clean_name}")
                f.full_name_th = clean_name
                f.embedding_text = build_standard_embedding_text(f)

        # -------------------------------------------------------------
        # 4. HIDDEN CONTROL CHARACTERS & BOM CLEANUP
        # -------------------------------------------------------------
        # SUT Thanasak Phittayakorn
        thanasak = db.query(FacultyDB).filter(FacultyDB.id == "sut_thanasak_phittayakorn_8728").first()
        if thanasak:
            print(f"🔬 Restoring Thai name for Thanasak Phittayakorn: {thanasak.id}")
            thanasak.full_name_th = "อ.ดร. ธนศักดิ์ พิทยากร"
            thanasak.academic_title_th = "อ.ดร."
            thanasak.first_name = "Thanasak"
            thanasak.last_name = "Phittayakorn"
            thanasak.embedding_text = build_standard_embedding_text(thanasak)

        # Strip zero-width spaces across all faculties
        zw_pat = re.compile(r"[﻿​‌‍\xa0\t\r\n]+")
        fac_all = db.query(FacultyDB).all()
        clean_fac_zw_count = 0
        for f in fac_all:
            changed = False
            for col in ["full_name_th", "academic_title_th", "first_name", "last_name", "email"]:
                val = getattr(f, col)
                if val and zw_pat.search(val):
                    setattr(f, col, zw_pat.sub(" ", val).strip())
                    changed = True
            if changed:
                # normalize any multi-spaces created
                if f.full_name_th:
                    f.full_name_th = re.sub(r"\s+", " ", f.full_name_th).strip()
                f.embedding_text = build_standard_embedding_text(f)
                clean_fac_zw_count += 1
        print(f"🧹 Cleaned zero-width and control characters in {clean_fac_zw_count} faculty records")

        # Strip newlines and non-breaking spaces in courses
        course_all = db.query(CourseDB).all()
        clean_course_zw_count = 0
        for c in course_all:
            changed = False
            for col in ["title_th", "title_en", "degree_level", "program_type", "duration_years"]:
                val = getattr(c, col)
                if val and zw_pat.search(val):
                    cleaned_val = zw_pat.sub(" ", val).strip()
                    cleaned_val = re.sub(r"\s+", " ", cleaned_val)
                    setattr(c, col, cleaned_val)
                    changed = True
            if changed:
                clean_course_zw_count += 1
        print(f"🧹 Cleaned control characters in {clean_course_zw_count} course records")

        # -------------------------------------------------------------
        # 5. ENGLISH TITLE & NAME PARSING NORMALIZATION
        # -------------------------------------------------------------
        # 5.1 Mahidol Pharmacy mu_pharm_wave12_* Assist. Prof. records (34 records)
        mu_pharm_assist = (
            db.query(FacultyDB)
            .filter(FacultyDB.id.like("mu_pharm_wave12%"), FacultyDB.first_name == "Assist.")
            .all()
        )
        for m in mu_pharm_assist:
            # m.last_name is like 'Prof. Supatat Chumnumwat'
            ln_raw = (m.last_name or "").strip()
            ln_clean = re.sub(r"^Prof\.\s*", "", ln_raw).strip()
            # Split into first and last
            parts = ln_clean.split(maxsplit=1)
            fn = parts[0] if parts else ""
            ln = parts[1] if len(parts) > 1 else ""
            m.academic_title_th = "ผศ."
            m.first_name = fn
            m.last_name = ln
            m.full_name_th = f"ผศ. {fn} {ln}".strip()
            m.embedding_text = build_standard_embedding_text(m)
        print(f"💊 Normalized {len(mu_pharm_assist)} Mahidol Pharmacy 'Assist. Prof.' records to 'ผศ.'")

        # 5.2 Specific foreign faculty records with glued English titles
        specific_foreign_fixes = {
            "cmu_eng_department_kenneth_103": {
                "full_name_th": "รศ.ดร. Kenneth Cosh",
                "academic_title_th": "รศ.ดร.",
                "first_name": "Kenneth",
                "last_name": "Cosh",
            },
            "cmu_d542da29_8423": {
                "full_name_th": "รศ.ดร. Tri Indrarini Wirjantoro",
                "academic_title_th": "รศ.ดร.",
                "first_name": "Tri Indrarini",
                "last_name": "Wirjantoro",
            },
            "cu_ahs_wave15_0008": {
                "full_name_th": "ดร. James Michael Brimson",
                "academic_title_th": "ดร.",
                "first_name": "James Michael",
                "last_name": "Brimson",
            },
            "tu_77228bb7_6146": {
                "full_name_th": "ผศ.ดร. Isaac Adam Jamieson",
                "academic_title_th": "ผศ.ดร.",
                "first_name": "Isaac Adam",
                "last_name": "Jamieson",
            },
            "mfu_nanghsumonpyaemfu__9408": {
                "full_name_th": "อ.ดร. Nang Hsu Mon Pyae",
                "academic_title_th": "อ.ดร.",
                "first_name": "Nang Hsu Mon",
                "last_name": "Pyae",
            },
            "mfu_shanmugamnandagopalanmfu__6638": {
                "full_name_th": "ศ.ดร. Shanmugam Nandagopalan",
                "academic_title_th": "ศ.ดร.",
                "first_name": "Shanmugam",
                "last_name": "Nandagopalan",
            },
            "mfu_agro_natthakan_run": {
                "full_name_th": "รศ.ดร. ณัฐกานต์ รุ่งเรือง",
                "academic_title_th": "รศ.ดร.",
                "first_name": "Natthakan",
                "last_name": "Rungraeng",
            },
            "chula_eng_ee_033": {
                "full_name_th": "ดร. วัชรพงษ์ โควิดรุ่งโรจน์",
                "academic_title_th": "ดร.",
                "first_name": "Watcharapong",
                "last_name": "Khovidhungij",
            },
        }
        for fid, attrs in specific_foreign_fixes.items():
            rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if rec:
                print(f"🌍 Correcting foreign title/name concatenation: {fid} -> {attrs['full_name_th']}")
                for k, v in attrs.items():
                    setattr(rec, k, v)
                rec.embedding_text = build_standard_embedding_text(rec)

        # 5.3 Strip trailing ', Ph.D.' from KKU Science faculty last_name
        kku_phd_facs = db.query(FacultyDB).filter(FacultyDB.last_name.like("%Ph.D%")).all()
        for f in kku_phd_facs:
            cleaned_ln = re.sub(r",?\s*Ph\.?D\.?", "", f.last_name or "").strip()
            f.last_name = cleaned_ln
            f.embedding_text = build_standard_embedding_text(f)
        print(f"🎓 Stripped ', Ph.D.' from last_name of {len(kku_phd_facs)} faculty records")

        # 5.4 Strip trailing comma from CMU last_name
        nad = db.query(FacultyDB).filter(FacultyDB.id == "cmu_eng_department_nad_64").first()
        if nad and nad.last_name:
            nad.last_name = nad.last_name.rstrip(",")
            nad.embedding_text = build_standard_embedding_text(nad)
            print(f"🧹 Cleaned trailing comma from {nad.id} last_name: '{nad.last_name}'")

        # -------------------------------------------------------------
        # 6. IMPOSSIBLE METRICS NORMALIZATION
        # -------------------------------------------------------------
        # Faculty with h_index > 0 but total_citations == 0 and total_publications_count == 0
        zero_work_h = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.h_index > 0,
                FacultyDB.total_citations == 0,
                FacultyDB.total_publications_count == 0,
            )
            .all()
        )
        for f in zero_work_h:
            f.h_index = 0
        print(f"📊 Normalized h_index = 0 for {len(zero_work_h)} faculty with 0 publications and 0 citations")

        # Pimonpan Apichonbancha (cmu_bus_013): cits=0, h=1 -> h=0
        pimon = db.query(FacultyDB).filter(FacultyDB.id == "cmu_bus_013").first()
        if pimon and pimon.total_citations == 0:
            pimon.h_index = 0

        # Mikhail Kovachev (mu_sci_wave14_b_0135): h=22, cits=2135, pubs=0 -> pubs=22
        mikhail = db.query(FacultyDB).filter(FacultyDB.id == "mu_sci_wave14_b_0135").first()
        if mikhail and (mikhail.total_publications_count or 0) < (mikhail.h_index or 0):
            mikhail.total_publications_count = mikhail.h_index
            print(f"📊 Aligned total_publications_count for Mikhail Kovachev: {mikhail.total_publications_count}")

        # -------------------------------------------------------------
        # 7. COURSE DURATION & PROGRAM_TYPE STANDARDIZATION
        # -------------------------------------------------------------
        # 7.1 Course duration ranges
        dur_map = {
            "1-2": "1-2 ปี",
            "3-4": "3-4 ปี",
            "3 - 4": "3-4 ปี",
            "0.5": "0.5 ปี",
            "1.5": "1.5 ปี",
        }
        dur_count = 0
        for c in course_all:
            d = (c.duration_years or "").strip()
            if d in dur_map:
                c.duration_years = dur_map[d]
                dur_count += 1
        print(f"⏱️ Standardized duration_years for {dur_count} courses")

        # 7.2 Course program_type
        pt_map = {
            "นานาชาติ (International Program)": "นานาชาติ",
            "หลักสูตรนานาชาติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์)": "นานาชาติ",
            "หลักสูตรนานาชาติ / หลักสูตรสหสาขาวิชา / ภาคปกติ (วันจันทร์-ศุกร์)": "นานาชาติ",
            "หลักสูตรนานาชาติ / หลักสูตรเดี่ยว / ภาคพิเศษ (วันเสาร์-อาทิตย์ ) / ภาคปกติ (วันจันทร์-ศุกร์)": "นานาชาติ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์)": "ภาคปกติ",
            "หลักสูตรปกติ / หลักสูตรสหสาขาวิชา / ภาคปกติ (วันจันทร์-ศุกร์)": "ภาคปกติ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันเสาร์-อาทิตย์ )": "ภาคปกติ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคปกติ (วันเสาร์-อาทิตย์)": "ภาคปกติ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ ) / ภาคปกติ (วันจันทร์-ศุกร์)": "ภาคปกติ / ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
            "หลักสูตรสองภาษา / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "สองภาษา / ภาคพิเศษ",
            "หลักสูตรสองภาษา / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์)": "สองภาษา",
            "หลักสูตรไทย (ภาคพิเศษ)": "ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรสหสาขาวิชา / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคพิเศษ (วันจันทร์-ศุกร์ (ช่วงเย็น)) และ ภาคพิเศษ (วันเสาร์-อาทิตย์)": "ภาคพิเศษ",
            "หลักสูตรปกติ / หลักสูตรสหสาขาวิชา / หลักสูตรเดี่ยว / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคพิเศษ",
            "โครงการพิเศษ (เสาร์-อาทิตย์)": "ภาคพิเศษ",
            "ภาคปกติ / โครงการพิเศษ": "ภาคปกติ / ภาคพิเศษ",
            "ภาคปกติ (23,000 บาท/เทอม) | โครงการพิเศษ/นานาชาติ (50,000 บาท/เทอม)": "ภาคปกติ / โครงการพิเศษ",
            "วิจัยเต็มเวลา (Full Research)": "วิจัยเต็มเวลา",
        }
        pt_count = 0
        for c in course_all:
            pt = (c.program_type or "").strip()
            if pt in pt_map:
                c.program_type = pt_map[pt]
                pt_count += 1
        print(f"🎓 Standardized program_type for {pt_count} courses")

        db.commit()
        print("\n" + "=" * 70)
        print("✅ ALL COMPREHENSIVE DATABASE HYGIENE REPAIRS COMMITTED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during comprehensive repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_comprehensive_database_hygiene()
