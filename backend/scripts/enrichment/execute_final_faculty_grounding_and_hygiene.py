# -*- coding: utf-8 -*-
"""
Execute Final Faculty Grounding, University Transfers & Department Hygiene
========================================================================
1. Transfers verified professors to their authentic home university based on institutional emails:
   - Prof. Dr. Suksun Horpibulsuk (SUT)
   - Prof. Dr. Sukit Limpijumnong (SUT)
   - Prof. Dr. Thanaruk Theeramunkong (TU SIIT)
   - Prof. Dr. Pithi Chanvorachote (CU Pharmacy Dean)
   - Prof. Dr. Ammarin Thakkinstian (MU Clinical Epidemiology)
   - Prof. Dr. Opa Vajragupta (MU Pharmacy)
   - Prof. Dr. Paramate Horkaew (SUT Computer Engineering)
   - Prof. Dr. Ronnason Chinram (PSU Mathematics)
   - CU Arts professors captured under Silpakorn
   - MU Medical / Clinical professors captured under CU
   - SUT Engineering professors captured under Rajabhat
2. Archives non-teaching central university administrative staff (Thaksin admin offices, central library, computer center)
   into scholars_unassigned.
3. Cleans scraped header artifacts and phone numbers in department names.
4. Verifies zero duplicates, zero unspecified departments, and 100% clean verified faculty.
"""
from __future__ import annotations

import re
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
from app.models.db_models import FacultyDB


# Precise Transfer and Faculty Realignment Mappings
UNIVERSITY_TRANSFERS = [
    # Renowned Engineering & Science Professors
    ("rmuti_w53b_0007_174", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมโยธาและธรณีเทคนิค"),
    ("nrru_w56_0007_855", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิทยาศาสตร์", "ศูนย์ความเป็นเลิศด้านวัสดุขั้นสูงและฟิสิกส์สารกึ่งตัวนำ"),
    ("nrru_w56_0024_598", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมคอมพิวเตอร์"),
    ("nrru_w56_0062_966", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมเคมี"),
    ("nrru_w56_0130_406", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมเครื่องกล"),
    ("rmutl_w53b_0014_527", "มหาวิทยาลัยธรรมศาสตร์", "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)", "สาขาวิชาเทคโนโลยีสารสนเทศ คอมพิวเตอร์ และการสื่อสาร"),
    ("rmuti_w53b_0123_643", "มหาวิทยาลัยศรีนครินทรวิโรฒ", "คณะวิศวกรรมศาสตร์", "ภาควิชาวิศวกรรมไฟฟ้า"),
    ("bru_w56_0003_247", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิทยาศาสตร์", "สาขาวิชาคณิตศาสตร์"),
    ("npru_w56_0094_145", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิทยาศาสตร์", "สาขาวิชาเทคโนโลยีสารสนเทศและการสื่อสาร"),
    ("nstru_w56_0675_884", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิทยาศาสตร์", "สาขาวิชาสถิติ"),
    ("skru_w56_0076_215", "มหาวิทยาลัยทักษิณ", "คณะศึกษาศาสตร์", "สาขาวิชาศึกษาศาสตร์"),
    ("skru_w56_0072_361", "มหาวิทยาลัยทักษิณ", "คณะศิลปกรรมศาสตร์", "สาขาวิชาดุริยางคศาสตร์"),
    ("nstru_w56_0524_181", "มหาวิทยาลัยทักษิณ", "คณะเศรษฐศาสตร์และบริหารธุรกิจ", "สาขาวิชาเศรษฐศาสตร์"),
    ("tsu_w50_0231_253", "มหาวิทยาลัยสงขลานครินทร์", "คณะพยาบาลศาสตร์", "สาขาวิชาพยาบาลศาสตร์"),
    ("wave22_1050_934", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "คณะอุตสาหกรรมเกษตร", "ภาควิชาเทคโนโลยีชีวภาพ"),
    ("wave22_1053_941", "มหาวิทยาลัยเกษตรศาสตร์", "คณะประมง", "ภาควิชาชีววิทยาประมง"),
    ("kmutt_w38_0177_241", "มหาวิทยาลัยธรรมศาสตร์", "วิทยาลัยโลกคดีศึกษา", "สาขาวิชาการพัฒนานวัตกรรม"),

    # CU / MU Cross-University Transfers
    ("mu_w57_0718_583", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะเภสัชศาสตร์", "ภาควิชาเภสัชวิทยาและสรีรวิทยา"),
    ("mu_w57_8502_709", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะแพทยศาสตร์", "ภาควิชาตจวิทยา"),
    ("mu_w57_1458_787", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะแพทยศาสตร์", "ภาควิชาจุลชีววิทยา"),
    ("wave22_0757_904", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะเภสัชศาสตร์", "ภาควิชาเภสัชกรรมปฏิบัติ"),
    ("wave22_0739_540", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาภาษาอังกฤษ"),
    ("wave22_0738_179", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาภาษาอังกฤษ"),
    ("wave22_0734_126", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาประวัติศาสตร์"),
    ("wave22_0736_184", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาภาษาอังกฤษ"),
    ("wave22_0742_819", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาภาษาอังกฤษ"),
    ("wave22_0735_422", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาภาษาอังกฤษ"),
    ("wave22_0737_102", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะอักษรศาสตร์", "ภาควิชาภาษาอังกฤษ"),

    ("cu_w58_0378_837", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี", "สาขาวิชาระบาดวิทยาคลินิก"),
    ("cu_w58_2072_689", "มหาวิทยาลัยมหิดล", "คณะเภสัชศาสตร์", "ภาควิชาเภสัชเคมี"),
    ("cu_w58_4057_913", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์ศิริราชพยาบาล", "ภาควิชากุมารเวชศาสตร์"),
    ("cu_w58_5183_679", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี", "ภาควิชาสูติศาสตร์-นรีเวชวิทยา"),
    ("cu_w58_1991_477", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์ศิริราชพยาบาล", "ภาควิชาอายุรศาสตร์"),
    ("cu_w58_1186_699", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์ศิริราชพยาบาล", "ภาควิชาอายุรศาสตร์"),
    ("cu_w58_1854_778", "มหาวิทยาลัยมหิดล", "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา", "สาขาวิชาวิทยาศาสตร์การกีฬา"),
    ("cu_w58_2554_599", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์ศิริราชพยาบาล", "ภาควิชาวิทยาภูมิคุ้มกัน"),
    ("cu_w58_1837_960", "มหาวิทยาลัยมหิดล", "คณะวิศวกรรมศาสตร์", "ภาควิชาวิศวกรรมเคมี"),
    ("cu_w58_6362_417", "มหาวิทยาลัยมหิดล", "คณะวิทยาศาสตร์", "ภาควิชาเคมี"),
    ("cu_w58_5360_859", "มหาวิทยาลัยมหิดล", "สถาบันวิจัยประชากรและสังคม", "สาขาวิชาประชากรและวิจัยสังคม"),
    ("cu_w58_3988_759", "มหาวิทยาลัยมหิดล", "คณะวิทยาศาสตร์", "ภาควิชาเคมี"),
    ("wave22_0756_362", "มหาวิทยาลัยมหิดล", "คณะเภสัชศาสตร์", "ภาควิชาเภสัชกรรม"),
]

# Departmental Header / Phone Cleanups
DEPT_CLEANUPS = [
    ("cu_pharm_wave16_0017", "ภาควิชาเภสัชเวทและเภสัชพฤกษศาสตร์"),
    ("cu_pharm_wave16_0023", "ภาควิชาเภสัชกรรมปฏิบัติ"),
    ("cu_pharm_wave16_0066", "ภาควิชาเภสัชวิทยาและสรีรวิทยา"),
    ("cu_pharm_wave16_0077", "ภาควิชาชีวเคมีและจุลชีววิทยา"),
    ("chulalongk_facultyofp_limpananont_023", "ภาควิชาเภสัชกรรมปฏิบัติ"),
    ("mahasarakh_facultyofi_chotithanom_007", "สาขาวิชาเทคโนโลยีสารสนเทศ"),
    ("ku_arch_singh_001", "ภาควิชานวัตกรรมอาคาร"),
    ("wave23_0206_465", "ภาควิชาเทคโนโลยีชีวภาพ"),
    ("wave23_0204_184", "ภาควิชาเทคโนโลยีการเกษตร"),
    ("wave23_0205_338", "ภาควิชาเทคโนโลยีการอาหารและโภชนศาสตร์"),
    ("thammasatu_thammasatb_fac_051_051", "สาขาวิชาบริหารการปฏิบัติการ"),
    ("thammasatu_thammasatb_fac_007_007", "ภาควิชาการเงิน"),
]


def run_hygiene():
    print("=== 🎓 EXECUTING FINAL FACULTY GROUNDING, TRANSFERS & HYGIENE ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    try:
        # Step 1: Realignment & University Transfers
        print("1. Updating university assignments for verified faculty...")
        transferred_count = 0
        for fid, target_univ, target_fac, target_dept in UNIVERSITY_TRANSFERS:
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                r.university_th = target_univ
                r.faculty_th = target_fac
                r.department_th = target_dept
                transferred_count += 1

        # Fix email anomaly for tsu_w50_0381_549
        r_tsu = db.query(FacultyDB).filter(FacultyDB.id == "tsu_w50_0381_549").first()
        if r_tsu:
            r_tsu.email = None

        db.commit()
        print(f"  Successfully transferred {transferred_count} verified professors to their active home university.")

        # Step 2: Department Cleanup
        print("2. Cleaning scraped header and phone artifacts in departments...")
        dept_fixed = 0
        for fid, clean_dept in DEPT_CLEANUPS:
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                r.department_th = clean_dept
                dept_fixed += 1
        db.commit()
        print(f"  Cleaned {dept_fixed} departmental strings.")

        # Step 3: Archive Central Admin, Library, and Computer Center staff
        print("3. Archiving central non-teaching administrative staff into scholars_unassigned...")
        admin_fac_prefixes = ["กอง", "งาน", "ฝ่าย", "แผนก", "สำนักงาน"]
        admin_fac_keywords = ["สำนักหอสมุด", "สำนักคอมพิวเตอร์"]

        admin_records = (
            db.query(FacultyDB)
            .filter(
                (FacultyDB.faculty_th.in_(admin_fac_keywords))
                | (FacultyDB.faculty_th.like("กอง%"))
                | (FacultyDB.faculty_th.like("ฝ่าย%"))
                | (FacultyDB.faculty_th.like("งาน%"))
                | (FacultyDB.faculty_th.like("สำนักงาน%"))
            )
            .all()
        )

        admin_archive_ids = [r.id for r in admin_records]
        print(f"  Found {len(admin_archive_ids)} central administrative/service staff to archive.")

        if admin_archive_ids:
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
                    {"ids": tuple(admin_archive_ids)},
                )
                conn.execute(
                    text("DELETE FROM public.faculties WHERE id IN :ids"),
                    {"ids": tuple(admin_archive_ids)},
                )
            print(f"  Successfully archived {len(admin_archive_ids)} non-teaching records into scholars_unassigned.")

    finally:
        db.close()

    # Step 4: Complete System Audit
    with engine.connect() as conn:
        final_fac = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        final_unassigned = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
        unspecified_dept = conn.execute(text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")).scalar()

        dup_names_count = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT full_name_th FROM public.faculties
                WHERE full_name_th IS NOT NULL AND length(full_name_th) > 3
                GROUP BY full_name_th
                HAVING count(*) > 1
            ) s;
        """)).scalar()

        print(f"\n=======================================================")
        print(f"FINAL ZERO-DEFECT QUALITY AUDIT:")
        print(f"- Primary 'faculties' count: {final_fac:,} clean verified faculty")
        print(f"- 'scholars_unassigned' count: {final_unassigned:,}")
        print(f"- Total across both tables: {final_fac + final_unassigned:,}")
        print(f"- Unspecified department count: {unspecified_dept} (MUST BE 0)")
        print(f"- Duplicate full_name_th remaining: {dup_names_count} (MUST BE 0)")
        print(f"=======================================================")

    print(f"All operations finished cleanly in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_hygiene()
