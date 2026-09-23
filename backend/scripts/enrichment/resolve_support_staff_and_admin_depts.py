# -*- coding: utf-8 -*-
"""
Resolve Support Staff & Administrative Departments
===================================================
1. Archive Non-Teaching Personnel into public.scholars_unassigned:
   - Walailak University Hospital / Medical Center clinical staff (234 records)
   - Walailak Graduate School Dean's Office staff (1 record)
   - Maejo University Science Dean's Office staff (4 records)
   - Kasetsart University Sakon Nakhon clerical staff (7 records)
   - Kasetsart University Sriracha educational service staff (1 record)
   - Kasetsart University Sriracha engineering secretariat staff (1 record)
   - Silpakorn University lab scientists & production staff (3 records)
   - Ubon Ratchathani University drugstore & lab testing staff (12 records)
   - KU IFRPD production and sales non-research staff (3 records)

2. Remap Authentic Teaching Faculty to Official Academic Departments:
   - Walailak School of Management: Dr. Neeranat Kaewprasertrakangtong -> สาขาวิชาบริหารธุรกิจ
   - MSU Faculty of Informatics (5 professors) -> Computer Science / Information Technology / Media Technology
   - CMU Data Science Consortium (46 professors) -> authentic engineering, science, economics, medicine, business departments
   - Chulalongkorn University Veterinary Science units -> ภาควิชาพยาธิวิทยา / ภาควิชาสรีรวิทยา / ภาควิชาปรสิตวิทยา
   - KMUTNB College of Industrial Technology testing labs -> ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล / ภาควิชาเทคโนโลยีวิศวกรรมอุตสาหการ
   - KU Kamphaeng Saen Agricultural Machinery Center -> ภาควิชาวิศวกรรมเกษตร
   - KMITL Agricultural Technology -> ภาควิชาเทคโนโลยีการผลิตพืช

3. Merge Verified Duplicate Records:
   - Jantima Polpinij: mahasarakh_facultyofi_phonphinit_001 + msu_w47_0522_214
   - Preecha Noiumkar: mahasarakh_facultyofi_noiamka_009 + msu_w47_1060_777
"""
from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB


def execute_resolutions():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING SUPPORT STAFF SEPARATION & DEPARTMENT GROUNDING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # -------------------------------------------------------------
        # 1. Identify Non-Teaching Personnel to Archive to scholars_unassigned
        # -------------------------------------------------------------
        archive_ids = set()

        # 1.1 Walailak Medical Center clinical staff
        wu_med = db.query(FacultyDB.id).filter(
            FacultyDB.university_th == "มหาวิทยาลัยวลัยลักษณ์",
            FacultyDB.faculty_th == "ศูนย์การแพทย์มหาวิทยาลัยวลัยลักษณ์",
        ).all()
        for (fid,) in wu_med:
            archive_ids.add(fid)

        # 1.2 Walailak Graduate School Dean's Office staff
        archive_ids.add("wu_w51_0005_916")

        # 1.3 Maejo Science Dean's Office staff
        mju_staff = ["wave22_1155_677", "wave22_1156_993", "wave22_1157_288", "wave22_1158_424"]
        for fid in mju_staff:
            archive_ids.add(fid)

        # 1.4 KU Sakon Nakhon clerical staff
        ku_lams = [
            "ku_wave18_lams_0001", "ku_wave18_lams_0002", "ku_wave18_lams_0003",
            "ku_wave18_lams_0004", "ku_wave18_lams_0005", "ku_wave18_lams_0006",
            "ku_wave18_lams_0007"
        ]
        for fid in ku_lams:
            archive_ids.add(fid)

        # 1.5 KU Sriracha Educational Services staff
        archive_ids.add("ku_wave18_msc_0001")

        # 1.6 KU Sriracha Engineering Secretariat staff
        archive_ids.add("ku_wave18_engsrc_0086")

        # 1.7 Silpakorn Lab Scientists & Production workers
        su_staff = ["su_w58_0950_331", "su_w58_1097_736", "su_w58_1127_263"]
        for fid in su_staff:
            archive_ids.add(fid)

        # 1.8 Ubon Pharmacy Drugstore & Lab Testing staff
        ubu_staff = [
            "ubu_w49_0070_321", "ubu_w49_0069_682", "ubu_w49_0072_402", "ubu_w49_0075_394",
            "ubu_w49_0076_555", "ubu_w49_0077_202", "ubu_w49_0078_317", "ubu_w49_0071_478",
            "ubu_w49_0079_233", "ubu_w49_0074_765", "ubu_w49_0039_137", "ubu_w49_0041_687"
        ]
        for fid in ubu_staff:
            archive_ids.add(fid)

        # 1.9 KU IFRPD non-research sales staff
        ifrpd_sales = ["ku_wave18_ifrpd_0040", "ku_wave18_ifrpd_0041", "ku_wave18_ifrpd_0043"]
        for fid in ifrpd_sales:
            archive_ids.add(fid)

        # Filter to only IDs that exist in faculties
        existing_archive_ids = [
            fid for (fid,) in db.query(FacultyDB.id).filter(FacultyDB.id.in_(list(archive_ids))).all()
        ]
        print(f"Total non-teaching support personnel to archive: {len(existing_archive_ids)}")

        # Perform atomic archival transfer
        if existing_archive_ids:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO public.scholars_unassigned
                        SELECT * FROM public.faculties
                        WHERE id = ANY(:ids)
                        ON CONFLICT (id) DO UPDATE SET
                            full_name_th = EXCLUDED.full_name_th,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            university_th = EXCLUDED.university_th,
                            university = EXCLUDED.university,
                            faculty_th = EXCLUDED.faculty_th,
                            faculty = EXCLUDED.faculty,
                            department_th = EXCLUDED.department_th,
                            department = EXCLUDED.department,
                            academic_title_th = EXCLUDED.academic_title_th,
                            email = EXCLUDED.email,
                            total_citations = EXCLUDED.total_citations,
                            h_index = EXCLUDED.h_index,
                            openalex_id = EXCLUDED.openalex_id;
                    """),
                    {"ids": existing_archive_ids},
                )
                conn.execute(
                    text("DELETE FROM public.faculties WHERE id = ANY(:ids)"),
                    {"ids": existing_archive_ids},
                )
            print(f"✅ Successfully archived {len(existing_archive_ids)} non-teaching records into scholars_unassigned.")

        # -------------------------------------------------------------
        # 2. Merge Duplicate Records
        # -------------------------------------------------------------
        print("\n--- Merging Verified Duplicate Records ---")
        # 2.1 Jantima Polpinij: mahasarakh_facultyofi_phonphinit_001 + msu_w47_0522_214
        jantima_primary = db.query(FacultyDB).filter(FacultyDB.id == "mahasarakh_facultyofi_phonphinit_001").first()
        jantima_ghost = db.query(FacultyDB).filter(FacultyDB.id == "msu_w47_0522_214").first()
        if jantima_primary and jantima_ghost:
            jantima_primary.openalex_id = jantima_ghost.openalex_id
            jantima_primary.total_citations = max(jantima_primary.total_citations or 0, jantima_ghost.total_citations or 0)
            jantima_primary.h_index = max(jantima_primary.h_index or 0, jantima_ghost.h_index or 0)
            jantima_primary.department_th = "ภาควิชาวิทยาการคอมพิวเตอร์"
            jantima_primary.department = "Department of Computer Science"
            if jantima_ghost.featured_publications:
                jantima_primary.featured_publications = jantima_ghost.featured_publications
            db.commit()

            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'msu_w47_0522_214' ON CONFLICT (id) DO NOTHING")
                )
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'msu_w47_0522_214'"))
            print("✅ Merged Jantima Polpinij (mahasarakh_facultyofi_phonphinit_001 + msu_w47_0522_214)")

        # 2.2 Preecha Noiumkar: mahasarakh_facultyofi_noiamka_009 + msu_w47_1060_777
        preecha_primary = db.query(FacultyDB).filter(FacultyDB.id == "mahasarakh_facultyofi_noiamka_009").first()
        preecha_ghost = db.query(FacultyDB).filter(FacultyDB.id == "msu_w47_1060_777").first()
        if preecha_primary and preecha_ghost:
            preecha_primary.openalex_id = preecha_ghost.openalex_id
            preecha_primary.total_citations = max(preecha_primary.total_citations or 0, preecha_ghost.total_citations or 0)
            preecha_primary.h_index = max(preecha_primary.h_index or 0, preecha_ghost.h_index or 0)
            preecha_primary.department_th = "ภาควิชาเทคโนโลยีสารสนเทศ"
            preecha_primary.department = "Department of Information Technology"
            if preecha_ghost.featured_publications:
                preecha_primary.featured_publications = preecha_ghost.featured_publications
            db.commit()

            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'msu_w47_1060_777' ON CONFLICT (id) DO NOTHING")
                )
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'msu_w47_1060_777'"))
            print("✅ Merged Preecha Noiumkar (mahasarakh_facultyofi_noiamka_009 + msu_w47_1060_777)")

        # -------------------------------------------------------------
        # 3. Remap Departments of Authentic Faculty Members
        # -------------------------------------------------------------
        print("\n--- Remapping Authentic Faculty Departments ---")

        # 3.1 Walailak School of Management
        neeranat = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_kaewprasertrakk_042").first()
        if neeranat:
            neeranat.department_th = "สาขาวิชาบริหารธุรกิจ"
            neeranat.department = "School of Management"
            print("  - Walailak: Dr. Neeranat Kaewprasertrakangtong -> สาขาวิชาบริหารธุรกิจ")

        # 3.2 MSU Faculty of Informatics (5 professors)
        msu_remaps = {
            "mahasarakh_facultyofi_uttha_003": ("ภาควิชาวิทยาการคอมพิวเตอร์", "Department of Computer Science"),
            "mahasarakh_facultyofi_sibunruang_004": ("ภาควิชาวิทยาการคอมพิวเตอร์", "Department of Computer Science"),
            "mahasarakh_facultyofi_saithong_005": ("ภาควิชาสื่อนฤมิต", "Department of Media Technology"),
            "mahasarakh_facultyofi_juanchaiyaphum_006": ("ภาควิชาวิทยาการคอมพิวเตอร์", "Department of Computer Science"),
            "mahasarakh_facultyofi_wichianchai_008": ("ภาควิชาเทคโนโลยีสารสนเทศ", "Department of Information Technology"),
        }
        for fid, (d_th, d_en) in msu_remaps.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.department_th = d_th
                f.department = d_en
                print(f"  - MSU: {f.full_name_th} -> {d_th}")

        # 3.3 Chulalongkorn Vet Med units
        cu_vet_units = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "จุฬาลงกรณ์มหาวิทยาลัย",
                FacultyDB.faculty_th == "คณะสัตวแพทยศาสตร์",
            )
            .all()
        )
        for f in cu_vet_units:
            d = f.department_th or ""
            if "พยาธิวิทยา" in d:
                f.department_th = "ภาควิชาพยาธิวิทยา"
                f.department = "Department of Pathology"
            elif "ชีวเคมี" in d or "สรีรวิทยา" in d:
                f.department_th = "ภาควิชาสรีรวิทยา"
                f.department = "Department of Physiology"
            elif "ปรสิตวิทยา" in d:
                f.department_th = "ภาควิชาปรสิตวิทยา"
                f.department = "Department of Parasitology"
            elif "สัตวแพทยสาธารณสุข" in d:
                f.department_th = "ภาควิชาสัตวแพทยสาธารณสุข"
                f.department = "Department of Veterinary Public Health"

        # 3.4 KMUTNB College of Industrial Technology testing labs
        kmutnb_lab_remaps = {
            "wave30_0047_796": "ภาควิชาเทคโนโลยีวิศวกรรมอุตสาหการ",
            "wave30_0048_621": "ภาควิชาเทคโนโลยีวิศวกรรมอุตสาหการ",
            "wave30_0050_647": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0049_944": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0051_280": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0052_583": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0053_466": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0054_248": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0055_989": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
            "wave30_0056_728": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล",
        }
        for fid, d_th in kmutnb_lab_remaps.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.department_th = d_th
                f.department = "College of Industrial Technology"

        # 3.5 KU Kamphaeng Saen Agricultural Machinery Center
        ku_engkps = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยเกษตรศาสตร์",
                FacultyDB.faculty_th == "คณะวิศวกรรมศาสตร์ กำแพงแสน",
                FacultyDB.department_th == "ศูนย์เครื่องจักรกลการเกษตรแห่งชาติ",
            )
            .all()
        )
        for f in ku_engkps:
            f.department_th = "ภาควิชาวิศวกรรมเกษตร"
            f.department = "Department of Agricultural Engineering"

        # 3.6 KMITL Agricultural Technology research center
        jarongsak = db.query(FacultyDB).filter(FacultyDB.id == "wave22_1251_426").first()
        if jarongsak:
            jarongsak.department_th = "ภาควิชาเทคโนโลยีการผลิตพืช"
            jarongsak.department = "Department of Plant Production Technology"

        # 3.7 CMU Data Science Consortium (46 professors)
        cmu_ds = (
            db.query(FacultyDB)
            .filter(FacultyDB.department_th == "ศูนย์วิทยาการข้อมูล (Data Science Consortium)")
            .all()
        )
        for f in cmu_ds:
            fac = f.faculty_th
            if fac == "คณะวิศวกรรมศาสตร์":
                # Check specific engineering department verified from official department portals (cpe.eng.cmu.ac.th, me.eng.cmu.ac.th, ie.eng.cmu.ac.th)
                if f.id in [
                    "cmu_eng_cpe_sakgasit_025", "chiangmaiu_facultyofe_sipitakiat_008",
                    "cmu_eng_sansanee_001", "cmu_eng_department_sanpawat_106",
                    "cmu_eng_department_kampol_111", "cmu_eng_department_narissara_104",
                    "cmu_eng_department_natthanan_110", "cmu_eng_department_nasi_116"
                ]:
                    f.department_th = "ภาควิชาวิศวกรรมคอมพิวเตอร์"
                    f.department = "Department of Computer Engineering"
                elif f.id in ["cmu_eng_department_yottana_75"]:
                    f.department_th = "ภาควิชาวิศวกรรมเครื่องกล"
                    f.department = "Department of Mechanical Engineering"
                else:
                    # Verified industrial engineering professors
                    f.department_th = "ภาควิชาวิศวกรรมอุตสาหการ"
                    f.department = "Department of Industrial Engineering"
            elif fac == "คณะวิทยาศาสตร์":
                if f.id in ["cmu_19b9cfbb_1507", "cmu_5dfc8308_9921", "cmu_7c17bf38_6130"]:
                    f.department_th = "ภาควิชาคณิตศาสตร์"
                    f.department = "Department of Mathematics"
                else:
                    f.department_th = "ภาควิชาสถิติ"
                    f.department = "Department of Statistics"
            elif fac == "คณะเศรษฐศาสตร์":
                f.department_th = "สาขาวิชาเศรษฐศาสตร์"
                f.department = "Faculty of Economics"
            elif fac == "คณะบริหารธุรกิจ":
                f.department_th = "ภาควิชาการเงินและการธนาคาร"
                f.department = "Department of Finance and Banking"
            elif fac == "คณะแพทยศาสตร์":
                if f.id == "cmu_ds_wave11_0025":
                    f.department_th = "ภาควิชานิติเวชศาสตร์"
                    f.department = "Department of Forensic Medicine"
                elif f.id == "cmu_ds_wave11_0010":
                    f.department_th = "ภาควิชาจักษุวิทยา"
                    f.department = "Department of Ophthalmology"
                elif f.id == "cmu_ds_wave11_0006":
                    f.department_th = "ภาควิชาอายุรศาสตร์"
                    f.department = "Department of Internal Medicine"
                elif f.id == "cmu_ds_wave11_0011":
                    f.department_th = "ภาควิชาศัลยศาสตร์"
                    f.department = "Department of Surgery"
                elif f.id == "cmu_ds_wave11_0027":
                    f.department_th = "ภาควิชาชีวเคมี"
                    f.department = "Department of Biochemistry"
                else:
                    f.department_th = "ภาควิชาอายุรศาสตร์"
                    f.department = "Department of Medicine"
            elif fac == "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี":
                if f.id in ["cmu_ds_wave11_0004", "cmu_ds_wave11_0016", "cmu_ds_wave11_0015"]:
                    f.department_th = "วิศวกรรมซอฟต์แวร์"
                    f.department = "Software Engineering"
                elif f.id == "cmu_ds_wave11_0009":
                    f.department_th = "การจัดการความรู้และนวัตกรรมดิจิทัล"
                    f.department = "Knowledge and Digital Innovation Management"
                else:
                    f.department_th = "สาขาวิชาวิศวกรรมความรู้และซอฟต์แวร์"
                    f.department = "Knowledge and Software Engineering"

        db.commit()
        print("✅ Department remappings committed successfully.")

    finally:
        db.close()

    print("\n🎉 Support staff separation and department grounding completed!")


if __name__ == "__main__":
    execute_resolutions()
