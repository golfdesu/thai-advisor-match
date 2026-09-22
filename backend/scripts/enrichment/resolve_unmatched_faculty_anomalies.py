# -*- coding: utf-8 -*-
"""
Resolve Unmatched Faculty Anomalies
==================================
1. Restores Prof. Dr. Supareak Prasertdam (cu_oa_disc_a5036226683) to CU Engineering and archives Walailak ghost.
2. Resolves KKU: archives 6 non-teaching co-authors in 'คณะรัฐศาสตร์' and 3 in 'คณะอุตสาหกรรมเกษตร'.
3. Resolves KU: remaps Assoc. Prof. Dr. Kumut Sangkhasila to Faculty of Agriculture, archives 2 co-authors in Political Science / Medicine, remaps 2 faculty from Computer Center to Eng/Econ, archives 21 IT staff.
4. Resolves CMU: remaps Prof. Dr. Attachak Sattayanurak from 'คณะรัฐศาสตร์' to 'คณะมนุษยศาสตร์' (ภาควิชาประวัติศาสตร์).
5. Resolves TSU: archives 31 foreign international co-authors under 'คณะแพทยศาสตร์', remaps 12 Thai medical doctors to 'คณะวิทยาการสุขภาพและการกีฬา' (สาขาวิชาแพทยศาสตร์), normalizes 'คณะสหวิทยาการ' -> 'คณะสหวิทยาการและการประกอบการ'.
6. Resolves Songkhla Rajabhat: remaps Asst. Prof. Dr. Suwit Khongphakdi from 'คณะศึกษาศาสตร์' to 'คณะครุศาสตร์'.
7. Resolves RMUTSB: remaps Assoc. Prof. Dr. Poonpong Suksawang to Burapha University Faculty of Education (ภาควิชาวิจัยและจิตวิทยาประยุกต์).
8. Resolves UP: remaps 3 faculty from 'คณะเกษตรศาสตร์' to 'คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ'.
9. Resolves KMUTNB: remaps Assoc. Prof. Dr. Chatcharn Thongchab from 'คณะเทคโนโลยีอุตสาหกรรม' to 'วิทยาลัยเทคโนโลยีอุตสาหกรรม'.
10. Resolves KMUTT: remaps Dr. Eric A. Ambele to 'คณะศิลปศาสตร์' and normalizes 'คณะพลังงานสิ่งแวดล้อมและวัสดุ'.
11. Resolves CU: normalizes MMRI and remaps Vaccine Center staff to Medicine/Science/Pharmacy.
12. Resolves PSU: strips campus suffixes from Pattani, Phuket, and Surat Thani faculties.
13. Resolves CMRU: archives 1 ghost and remaps industrial tech staff to Science & Technology.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB, ScholarUnassignedDB


def execute_resolutions():
    print("=== 🛠️ EXECUTING COMPREHENSIVE FACULTY ANOMALY RESOLUTIONS ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    ghosts_to_archive: set[str] = set()

    try:
        # 1. Walailak & Chulalongkorn: Prof. Dr. Supareak Prasertdam
        wu_supareak = db.query(FacultyDB).filter(FacultyDB.id == "wu_w59_0054_947").first()
        cu_supareak = db.query(ScholarUnassignedDB).filter(ScholarUnassignedDB.id == "cu_oa_disc_a5036226683").first()

        # Restore CU Supareak to faculties
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO public.faculties
                    SELECT * FROM public.scholars_unassigned
                    WHERE id = 'cu_oa_disc_a5036226683'
                    ON CONFLICT (id) DO UPDATE SET
                        university_th = 'จุฬาลงกรณ์มหาวิทยาลัย',
                        university = 'Chulalongkorn University',
                        faculty_th = 'คณะวิศวกรรมศาสตร์',
                        faculty = 'Faculty of Engineering',
                        department_th = 'ภาควิชาวิศวกรรมเคมี',
                        department = 'Department of Chemical Engineering',
                        total_citations = 2817,
                        total_publications_count = 150,
                        email = 'supareak.p@chula.ac.th';
                """)
            )
            conn.execute(text("DELETE FROM public.scholars_unassigned WHERE id = 'cu_oa_disc_a5036226683'"))

        # Verify restored CU record
        cu_restored = db.query(FacultyDB).filter(FacultyDB.id == "cu_oa_disc_a5036226683").first()
        if cu_restored:
            cu_restored.full_name_th = "ศ.ดร. ศุภฤกษ์ ประเสริฐธรรม"
            cu_restored.academic_title_th = "ศ.ดร."
            cu_restored.university_th = "จุฬาลงกรณ์มหาวิทยาลัย"
            cu_restored.university = "Chulalongkorn University"
            cu_restored.faculty_th = "คณะวิศวกรรมศาสตร์"
            cu_restored.faculty = "Faculty of Engineering"
            cu_restored.department_th = "ภาควิชาวิศวกรรมเคมี"
            cu_restored.department = "Department of Chemical Engineering"
            cu_restored.total_citations = 2817
            cu_restored.total_publications_count = 150
            cu_restored.email = "supareak.p@chula.ac.th"
            print("  [1] Restored Prof. Dr. Supareak Prasertdam to Chulalongkorn Engineering.")

        if wu_supareak:
            ghosts_to_archive.add("wu_w59_0054_947")
            print("  [1] Flagged Walailak Engineering ghost (wu_w59_0054_947) for archival.")

        # 2. Khon Kaen University
        kku_pol_ghosts = [
            "kku_w58_10637_189", "kku_w58_5057_423", "kku_w58_7026_250",
            "kku_w58_9284_676", "kku_w58_9285_974", "kku_w58_10019_865"
        ]
        for gid in kku_pol_ghosts:
            ghosts_to_archive.add(gid)
        print(f"  [2] Flagged {len(kku_pol_ghosts)} KKU Political Science co-authors for archival.")

        kku_agro_ghosts = ["kku_w58_5038_555", "kku_w58_10622_380", "kku_w58_5672_146"]
        for gid in kku_agro_ghosts:
            ghosts_to_archive.add(gid)
        print(f"  [2] Flagged {len(kku_agro_ghosts)} KKU Agro-Industry co-authors for archival.")

        # 3. Kasetsart University
        ku_kumut = db.query(FacultyDB).filter(FacultyDB.id == "ku_w57_5911_377").first()
        if ku_kumut:
            ku_kumut.academic_title_th = "รศ.ดร."
            ku_kumut.full_name_th = "รศ.ดร. กุมุท สังขศิลา"
            ku_kumut.faculty_th = "คณะเกษตร"
            ku_kumut.faculty = "Faculty of Agriculture"
            ku_kumut.department_th = "ภาควิชาปฐพีวิทยา"
            ku_kumut.department = "Department of Soil Science"
            print("  [3] Remapped Assoc. Prof. Dr. Kumut Sangkhasila to KU Faculty of Agriculture (ภาควิชาปฐพีวิทยา).")

        ghosts_to_archive.add("ku_w57_5195_440")  # Sakorn Chinwong
        ghosts_to_archive.add("ku_w57_3090_357")  # Pensri Sawaengcharoen
        print("  [3] Flagged KU Political Science & Medicine co-authors for archival.")

        # KU Computer Service Center
        ku_pw = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_cc_0001").first()
        if ku_pw:
            ku_pw.faculty_th = "คณะวิศวกรรมศาสตร์"
            ku_pw.faculty = "Faculty of Engineering"
            ku_pw.department_th = "ภาควิชาวิศวกรรมคอมพิวเตอร์"
            ku_pw.department = "Department of Computer Engineering"
            print("  [3] Remapped Asst. Prof. Dr. Peerawat Wattanapongs to KU Computer Engineering.")

        ku_ad = db.query(FacultyDB).filter(FacultyDB.id == "ku_wave18_cc_0012").first()
        if ku_ad:
            ku_ad.faculty_th = "คณะเศรษฐศาสตร์"
            ku_ad.faculty = "Faculty of Economics"
            ku_ad.department_th = "ภาควิชาเศรษฐศาสตร์การเกษตรและทรัพยากร"
            ku_ad.department = "Department of Agricultural and Resource Economics"
            print("  [3] Remapped Asst. Prof. Dr. Apichart Daloonpate to KU Faculty of Economics.")

        ku_cc_staff = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยเกษตรศาสตร์",
                FacultyDB.faculty_th == "สำนักบริการคอมพิวเตอร์",
                FacultyDB.id.notin_(["ku_wave18_cc_0001", "ku_wave18_cc_0012"])
            )
            .all()
        )
        for s in ku_cc_staff:
            ghosts_to_archive.add(s.id)
        print(f"  [3] Flagged {len(ku_cc_staff)} KU non-teaching Computer Service staff for archival.")

        # 4. Chiang Mai University
        cmu_att = db.query(FacultyDB).filter(FacultyDB.id == "cmu_w57_5657_944").first()
        if cmu_att:
            cmu_att.academic_title_th = "ศ.ดร."
            cmu_att.full_name_th = "ศ.ดร. อรรถจักร์ สัตยานุรักษ์"
            cmu_att.faculty_th = "คณะมนุษยศาสตร์"
            cmu_att.faculty = "Faculty of Humanities"
            cmu_att.department_th = "ภาควิชาประวัติศาสตร์"
            cmu_att.department = "Department of History"
            print("  [4] Remapped Prof. Dr. Attachak Sattayanurak to CMU Faculty of Humanities (ภาควิชาประวัติศาสตร์).")

        # 5. Thaksin University
        tsu_med_doctors = [
            "tsu_w50_0991_516", "tsu_w50_1475_264", "tsu_w50_1478_810", "tsu_w50_1471_359",
            "tsu_w50_1474_778", "tsu_w50_1477_942", "tsu_w50_1472_930", "tsu_w50_1473_660",
            "tsu_w50_1476_344", "tsu_w50_1470_193", "tsu_w50_1479_855", "tsu_w50_0243_892"
        ]
        for mid in tsu_med_doctors:
            mr = db.query(FacultyDB).filter(FacultyDB.id == mid).first()
            if mr:
                mr.faculty_th = "คณะวิทยาการสุขภาพและการกีฬา"
                mr.faculty = "Faculty of Health and Sports Science"
                mr.department_th = "สาขาวิชาแพทยศาสตร์ (โครงการจัดตั้ง)"
                mr.department = "Division of Medicine"
        print(f"  [5] Remapped {len(tsu_med_doctors)} Thaksin medical doctors to Faculty of Health and Sports Science.")

        tsu_foreign_med = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยทักษิณ",
                FacultyDB.faculty_th == "คณะแพทยศาสตร์",
                FacultyDB.id.notin_(tsu_med_doctors)
            )
            .all()
        )
        for fm in tsu_foreign_med:
            ghosts_to_archive.add(fm.id)
        print(f"  [5] Flagged {len(tsu_foreign_med)} Thaksin foreign co-authors for archival.")

        # TSU Normalize คณะสหวิทยาการ -> คณะสหวิทยาการและการประกอบการ
        tsu_inter = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยทักษิณ",
                FacultyDB.faculty_th == "คณะสหวิทยาการ"
            )
            .all()
        )
        for ti in tsu_inter:
            ti.faculty_th = "คณะสหวิทยาการและการประกอบการ"
            ti.faculty = "Faculty of Interdisciplinary Studies and Entrepreneurship"
        print(f"  [5] Normalized {len(tsu_inter)} TSU faculty to คณะสหวิทยาการและการประกอบการ.")

        # 6. Songkhla Rajabhat University
        skru_fac = db.query(FacultyDB).filter(FacultyDB.id == "skru_w56_0201_122").first()
        if skru_fac:
            skru_fac.faculty_th = "คณะครุศาสตร์"
            skru_fac.faculty = "Faculty of Education"
            print("  [6] Remapped Asst. Prof. Dr. Suwit Khongphakdi to Songkhla Rajabhat Faculty of Education (คณะครุศาสตร์).")

        # 7. RMUT Suvarnabhumi -> Burapha University
        rmuts_fac = db.query(FacultyDB).filter(FacultyDB.id == "rmuts_w53b_0321_844").first()
        if rmuts_fac:
            rmuts_fac.university_th = "มหาวิทยาลัยบูรพา"
            rmuts_fac.university = "Burapha University"
            rmuts_fac.faculty_th = "คณะศึกษาศาสตร์"
            rmuts_fac.faculty = "Faculty of Education"
            rmuts_fac.department_th = "ภาควิชาวิจัยและจิตวิทยาประยุกต์"
            rmuts_fac.department = "Department of Research and Applied Psychology"
            rmuts_fac.academic_title_th = "รศ.ดร."
            rmuts_fac.full_name_th = "รศ.ดร. พูลพงศ์ สุขสว่าง"
            print("  [7] Remapped Assoc. Prof. Dr. Poonpong Suksawang to Burapha University Faculty of Education.")

        # 8. University of Phayao
        up_agri = ["wave24_0430_104", "wave24_0429_250", "wave24_0428_217"]
        for uid in up_agri:
            ur = db.query(FacultyDB).filter(FacultyDB.id == uid).first()
            if ur:
                ur.faculty_th = "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ"
                ur.faculty = "School of Agriculture and Natural Resources"
        print(f"  [8] Remapped {len(up_agri)} Phayao faculty to คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ.")

        # 9. KMUTNB
        kmutnb_ind = db.query(FacultyDB).filter(FacultyDB.id == "wave25_0007_430").first()
        if kmutnb_ind:
            kmutnb_ind.faculty_th = "วิทยาลัยเทคโนโลยีอุตสาหกรรม"
            kmutnb_ind.faculty = "College of Industrial Technology"
            print("  [9] Remapped Assoc. Prof. Dr. Chatcharn Thongchab to KMUTNB College of Industrial Technology.")

        # 10. KMUTT
        kmutt_eric = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_w57_0830_647").first()
        if kmutt_eric:
            kmutt_eric.faculty_th = "คณะศิลปศาสตร์"
            kmutt_eric.faculty = "School of Liberal Arts"
            kmutt_eric.department_th = "สายวิชาภาษา"
            kmutt_eric.department = "Department of Language Studies"
            print("  [10] Remapped Dr. Eric A. Ambele to KMUTT School of Liberal Arts.")

        kmutt_somchart = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_energy_somchart_001").first()
        if kmutt_somchart:
            kmutt_somchart.faculty_th = "คณะพลังงานสิ่งแวดล้อมและวัสดุ"
            kmutt_somchart.faculty = "School of Energy, Environment and Materials"
            print("  [10] Normalized Prof. Dr. Somchart Soponronnarit to คณะพลังงานสิ่งแวดล้อมและวัสดุ.")

        # 11. Chulalongkorn Normalizations
        cu_mmri = db.query(FacultyDB).filter(FacultyDB.id == "cu_oa_disc_a5057708985").first()
        if cu_mmri:
            cu_mmri.faculty_th = "สถาบันวิจัยโลหะและวัสดุ"
            cu_mmri.faculty = "Metallurgy and Materials Science Research Institute"
            print("  [11] Normalized MMRI faculty string.")

        cu_vrc_palaga = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_centerofex_palaga_003").first()
        if cu_vrc_palaga:
            cu_vrc_palaga.faculty_th = "คณะวิทยาศาสตร์"
            cu_vrc_palaga.faculty = "Faculty of Science"
            cu_vrc_palaga.department_th = "ภาควิชาจุลชีววิทยา"

        cu_vrc_prom = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_centerofex_prompetchara_006").first()
        if cu_vrc_prom:
            cu_vrc_prom.faculty_th = "คณะเภสัชศาสตร์"
            cu_vrc_prom.faculty = "Faculty of Pharmaceutical Sciences"
            cu_vrc_prom.department_th = "ภาควิชาชีวเคมีและจุลชีววิทยา"

        cu_vrc_rest = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "จุฬาลงกรณ์มหาวิทยาลัย",
                FacultyDB.faculty_th == "ศูนย์วิจัยวัคซีน คณะแพทยศาสตร์"
            )
            .all()
        )
        for vr in cu_vrc_rest:
            vr.faculty_th = "คณะแพทยศาสตร์"
            vr.faculty = "Faculty of Medicine"
        print(f"  [11] Remapped Chulalongkorn Vaccine Research Center faculty to authentic teaching faculties.")

        # 12. PSU Campus Suffix Normalization
        psu_normalizations = [
            ("คณะรัฐศาสตร์ (วิทยาเขตปัตตานี)", "คณะรัฐศาสตร์"),
            ("คณะการบริการและการท่องเที่ยว (วิทยาเขตภูเก็ต)", "คณะการบริการและการท่องเที่ยว"),
            ("คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม (วิทยาเขตสุราษฎร์ธานี)", "คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม"),
            ("คณะศึกษาศาสตร์ (วิทยาเขตปัตตานี)", "คณะศึกษาศาสตร์"),
            ("คณะเทคโนโลยีและสิ่งแวดล้อม วิทยาเขตภูเก็ต", "คณะเทคโนโลยีและสิ่งแวดล้อม"),
            ("วิทยาลัยการคอมพิวเตอร์ (วิทยาเขตภูเก็ต)", "วิทยาลัยการคอมพิวเตอร์"),
        ]
        for old_f, new_f in psu_normalizations:
            psu_rows = (
                db.query(FacultyDB)
                .filter(FacultyDB.university_th == "มหาวิทยาลัยสงขลานครินทร์", FacultyDB.faculty_th == old_f)
                .all()
            )
            for pr in psu_rows:
                pr.faculty_th = new_f
            if psu_rows:
                print(f"  [12] Normalized PSU '{old_f}' -> '{new_f}' ({len(psu_rows)} records).")

        # 13. CMRU Normalization
        ghosts_to_archive.add("cmru_w56_0643_101")
        cmru_ind = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยราชภัฏเชียงใหม่",
                FacultyDB.faculty_th == "คณะเทคโนโลยีอุตสาหกรรม"
            )
            .all()
        )
        for cr in cmru_ind:
            cr.faculty_th = "คณะวิทยาศาสตร์และเทคโนโลยี"
            cr.faculty = "Faculty of Science and Technology"
        print(f"  [13] Remapped {len(cmru_ind)} CMRU Industrial Tech staff to Faculty of Science and Technology.")

        db.commit()

        # Archive ghost records atomically
        archive_list = list(ghosts_to_archive)
        if archive_list:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO public.scholars_unassigned
                        SELECT * FROM public.faculties
                        WHERE id IN :ids
                        ON CONFLICT (id) DO UPDATE SET
                            department = EXCLUDED.department,
                            department_th = EXCLUDED.department_th,
                            email = COALESCE(scholars_unassigned.email, EXCLUDED.email);
                    """),
                    {"ids": tuple(archive_list)},
                )
                conn.execute(
                    text("DELETE FROM public.faculties WHERE id IN :ids"),
                    {"ids": tuple(archive_list)},
                )
            print(f"  Successfully archived {len(archive_list)} ghost records to scholars_unassigned.")

    finally:
        db.close()

    print(f"Anomaly resolutions completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    execute_resolutions()
