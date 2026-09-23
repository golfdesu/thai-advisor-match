# -*- coding: utf-8 -*-
"""
Execute Clean Faculty Transfers & Cross-University Duplicate Deduplication
========================================================================
1. Realigns Asst. Prof. Dr. Nutthapat Kaewrattanapat to Suan Sunandha Rajabhat
   University (Faculty of Education) with email nutthapat.ke@ssru.ac.th and archives RMUTSB ghost.
2. Realigns Dr. Saran Cheenacharoen from Maejo to Chiang Mai Rajabhat University (Faculty of Science & Tech) with email saran_che@cmru.ac.th.
3. Realigns Asst. Prof. Dr. Sasithorn Sanporkha from Maejo to RMUTTO (Faculty of Science & Tech) with email sasithorn_su@rmutto.ac.th.
4. Realigns Assoc. Prof. Dr. Nipon Poapongsakorn at NIDA from 'คณะเศรษฐศาสตร์' to 'คณะพัฒนาการเศรษฐกิจ' (School of Development Economics).
5. Deduplicates Prof. Dr. Sombat Thamrongthanyawong: archives Walailak ghost wu_w51_1906_444, retains primary NIDA record nida_wu_sombat_001.
6. Deduplicates Assoc. Prof. Dr. Manad Khamkong: updates CMU cmu_ds_wave11_0018 with OpenAlex ID, archives KKU co-author ghost kku_w58_10501_684.
7. Deduplicates Asst. Prof. Dr. Butsara Yongkamcha: archives RMU ghost rmu_w56_0598_786, retains MSU record wave22_1012_141.
8. Deduplicates Assoc. Prof. Dr. Choomporn Moorapun: archives TU ghost wave24_0342_418, retains KMITL record kmitl_aad_wave16_0001.
9. Ingests 47 authentic RMUTP curriculum programs crawled directly from official portal https://www.rmutp.ac.th/หลักสูตร/.
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
from app.models.db_models import FacultyDB, CourseDB, ScholarUnassignedDB
from scripts.data_sources.rmutp_courses_extracted import EXTRACTED_COURSES


def execute_transfers_and_dedup():
    print("=================================================================", flush=True)
    print("🛠️ EXECUTING FACULTY TRANSFERS & CROSS-UNIVERSITY DEDUPLICATION", flush=True)
    print("=================================================================", flush=True)
    t0 = time.time()
    db = SessionLocal()

    ghosts_to_archive: set[str] = set()

    try:
        # 1. Nutthapat Kaewrattanapat: SSRU vs RMUTSB
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO public.faculties
                    SELECT * FROM public.scholars_unassigned
                    WHERE id = 'suansunand_facultyofe_kaewrattanapat_036'
                    ON CONFLICT (id) DO UPDATE SET
                        university_th = 'มหาวิทยาลัยราชภัฏสวนสุนันทา',
                        university = 'Suan Sunandha Rajabhat University',
                        faculty_th = 'คณะครุศาสตร์',
                        faculty = 'Faculty of Education',
                        department_th = 'สาขาวิชานวัตกรรมและเทคโนโลยีการศึกษา',
                        department = 'Department of Innovation and Educational Technology',
                        total_citations = 81,
                        email = 'nutthapat.ke@ssru.ac.th';
                """)
            )
            conn.execute(text("DELETE FROM public.scholars_unassigned WHERE id = 'suansunand_facultyofe_kaewrattanapat_036'"))

        ssru_rec = db.query(FacultyDB).filter(FacultyDB.id == "suansunand_facultyofe_kaewrattanapat_036").first()
        if ssru_rec:
            ssru_rec.full_name_th = "ผศ.ดร. ณัฐภัทร แก้วรัตนภัทร์"
            ssru_rec.academic_title_th = "ผศ.ดร."
            ssru_rec.university_th = "มหาวิทยาลัยราชภัฏสวนสุนันทา"
            ssru_rec.university = "Suan Sunandha Rajabhat University"
            ssru_rec.faculty_th = "คณะครุศาสตร์"
            ssru_rec.faculty = "Faculty of Education"
            ssru_rec.department_th = "สาขาวิชานวัตกรรมและเทคโนโลยีการศึกษา"
            ssru_rec.department = "Department of Innovation and Educational Technology"
            ssru_rec.total_citations = 81
            ssru_rec.email = "nutthapat.ke@ssru.ac.th"
            print("  [1] Restored Asst. Prof. Dr. Nutthapat Kaewrattanapat to SSRU Faculty of Education.")

        ghosts_to_archive.add("rmuts_w53b_0075_995")
        print("  [1] Flagged RMUTSB ghost rmuts_w53b_0075_995 for archival.")

        # 2. Saran Cheenacharoen: Maejo -> CMRU
        saran = db.query(FacultyDB).filter(FacultyDB.id == "wave22_1048_591").first()
        if saran:
            saran.university_th = "มหาวิทยาลัยราชภัฏเชียงใหม่"
            saran.university = "Chiang Mai Rajabhat University"
            saran.faculty_th = "คณะวิทยาศาสตร์และเทคโนโลยี"
            saran.faculty = "Faculty of Science and Technology"
            saran.department_th = "ภาควิชาฟิสิกส์และวิทยาศาสตร์ทั่วไป"
            saran.department = "Department of Physics and General Science"
            saran.email = "saran_che@cmru.ac.th"
            print("  [2] Realigned Dr. Saran Cheenacharoen to Chiang Mai Rajabhat University.")

        # 3. Sasithorn Sanporkha: Maejo -> RMUTTO
        sasithorn = db.query(FacultyDB).filter(FacultyDB.id == "wave22_1049_741").first()
        if sasithorn:
            sasithorn.university_th = "มหาวิทยาลัยเทคโนโลยีราชมงคลตะวันออก"
            sasithorn.university = "Rajamangala University of Technology Tawan-ok"
            sasithorn.faculty_th = "คณะวิทยาศาสตร์และเทคโนโลยี"
            sasithorn.faculty = "Faculty of Science and Technology"
            sasithorn.department_th = "สาขาวิชาวิทยาศาสตร์และคณิตศาสตร์"
            sasithorn.department = "Department of Science and Mathematics"
            sasithorn.email = "sasithorn_su@rmutto.ac.th"
            print("  [3] Realigned Asst. Prof. Dr. Sasithorn Sanporkha to RMUTTO.")

        # 4. Nipon Poapongsakorn: NIDA School of Development Economics
        nipon = db.query(FacultyDB).filter(FacultyDB.id == "nida_w55_0108_644").first()
        if nipon:
            nipon.faculty_th = "คณะพัฒนาการเศรษฐกิจ"
            nipon.faculty = "School of Development Economics"
            nipon.department_th = "สาขาวิชาเศรษฐศาสตร์การพัฒนา"
            nipon.department = "Department of Development Economics"
            print("  [4] Realigned Assoc. Prof. Dr. Nipon Poapongsakorn to NIDA คณะพัฒนาการเศรษฐกิจ.")

        # 5. Sombat Thamrongthanyawong: Archive Walailak ghost
        ghosts_to_archive.add("wu_w51_1906_444")
        print("  [5] Flagged Walailak duplicate wu_w51_1906_444 for archival (NIDA record retained).")

        # 6. Manad Khamkong: Update CMU record & archive KKU ghost
        cmu_manad = db.query(FacultyDB).filter(FacultyDB.id == "cmu_ds_wave11_0018").first()
        if cmu_manad:
            cmu_manad.openalex_id = "https://openalex.org/A5014785093"
            cmu_manad.total_publications_count = max(cmu_manad.total_publications_count or 0, 1)
            print("  [6] Enhanced CMU Assoc. Prof. Dr. Manad Khamkong with OpenAlex ID.")
        ghosts_to_archive.add("kku_w58_10501_684")
        print("  [6] Flagged KKU co-author ghost kku_w58_10501_684 for archival.")

        # 7. Butsara Yongkamcha: Archive RMU ghost
        ghosts_to_archive.add("rmu_w56_0598_786")
        print("  [7] Flagged RMU duplicate rmu_w56_0598_786 for archival (MSU record retained).")

        # 8. Choomporn Moorapun: Archive TU ghost
        ghosts_to_archive.add("wave24_0342_418")
        print("  [8] Flagged TU duplicate wave24_0342_418 for archival (KMITL record retained).")

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
            print(f"  Successfully archived {len(archive_list)} ghost/duplicate records to scholars_unassigned.")

        # 9. Ingest 47 Authentic RMUTP Courses
        print("\n--- Ingesting Authentic RMUTP Degree Programs from Official Web Portal ---")
        inserted_courses = 0
        updated_courses = 0

        # Faculty English Name Map for RMUTP
        rmutp_fac_en_map = {
            "คณะครุศาสตร์อุตสาหกรรม": "Faculty of Industrial Education",
            "คณะเทคโนโลยีคหกรรมศาสตร์": "Faculty of Home Economics Technology",
            "คณะเทคโนโลยีสื่อสารมวลชน": "Faculty of Mass Communication Technology",
            "คณะบริหารธุรกิจ": "Faculty of Business Administration",
            "คณะวิทยาศาสตร์และเทคโนโลยี": "Faculty of Science and Technology",
            "คณะวิศวกรรมศาสตร์": "Faculty of Engineering",
            "คณะศิลปศาสตร์": "Faculty of Liberal Arts",
            "คณะอุตสาหกรรมสิ่งทอและออกแบบแฟชั่น": "Faculty of Textile Industry and Fashion Design",
            "คณะสถาปัตยกรรมศาสตร์และการออกแบบ": "Faculty of Architecture and Design"
        }

        for c_data in EXTRACTED_COURSES:
            cid = c_data["id"]
            fac_th = c_data.get("faculty_th") or c_data.get("department_th") or ""
            fac_en = rmutp_fac_en_map.get(fac_th, "Faculty of " + fac_th.replace("คณะ", "").strip())

            existing_c = db.query(CourseDB).filter(CourseDB.id == cid).first()
            if existing_c:
                existing_c.title_th = c_data["title_th"]
                existing_c.title_en = c_data["title_en"]
                existing_c.degree_level = c_data["degree_level"]
                existing_c.degree_name = c_data["degree_name"]
                existing_c.university = c_data["university"]
                existing_c.university_th = c_data["university_th"]
                existing_c.faculty = fac_en
                existing_c.faculty_th = fac_th
                existing_c.duration_years = c_data.get("duration_years") or "4 ปี"
                existing_c.website_url = c_data.get("website_url") or "https://www.rmutp.ac.th/หลักสูตร/"
                existing_c.description = c_data.get("description") or f"หลักสูตร {c_data['title_th']} มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร"
                existing_c.tags = c_data.get("tags") or [fac_th, c_data["degree_level"]]
                updated_courses += 1
            else:
                new_c = CourseDB(
                    id=cid,
                    title_th=c_data["title_th"],
                    title_en=c_data["title_en"],
                    degree_level=c_data["degree_level"],
                    degree_name=c_data["degree_name"],
                    university=c_data["university"],
                    university_th=c_data["university_th"],
                    faculty=fac_en,
                    faculty_th=fac_th,
                    department="",
                    department_th="",
                    program_type=c_data.get("program_type") or "ภาคปกติ",
                    duration_years=c_data.get("duration_years") or "4 ปี",
                    total_credits=c_data.get("total_credits") or "",
                    tuition_per_semester=c_data.get("tuition_per_semester") or "",
                    tuition_total=c_data.get("tuition_total") or "",
                    description=c_data.get("description") or f"หลักสูตร {c_data['title_th']} มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
                    curriculum_highlights=c_data.get("curriculum_highlights") or [],
                    career_paths=c_data.get("career_paths") or [],
                    tags=c_data.get("tags") or [fac_th, c_data["degree_level"]],
                    website_url=c_data.get("website_url") or "https://www.rmutp.ac.th/หลักสูตร/",
                    embedding_text=f"{c_data['title_th']} {fac_th} มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
                    embedding=[0.0] * 768,
                )
                db.add(new_c)
                inserted_courses += 1

        db.commit()
        print(f"  RMUTP authentic courses ingested: {inserted_courses} new, {updated_courses} updated.")

    finally:
        db.close()

    print(f"\nExecution completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    execute_transfers_and_dedup()
