# -*- coding: utf-8 -*-
"""
Ground and Clean Remaining Anomalous Faculty Assignments
======================================================
1. Grounds Prof. Dr. Bancha Chernchujit to Faculty of Medicine, Thammasat University.
2. Archives 58 non-faculty student co-authors with 0 citations under 'คณะสังคมศาสตร์' at TU into scholars_unassigned.
3. Archives 5 non-teaching science park staff at Thaksin University into scholars_unassigned.
4. Realigns Mahidol faculty (Adisorn Ratanayotha to Faculty of Science, Phongthana Pasookhush to Institute of Nutrition).
5. Realigns Chulalongkorn faculty (Prof. Dr. Jiaqian Qin to Metallurgy and Materials Science Research Institute).
6. Realigns Khon Kaen faculty (Sompong, Prapas, Leklai to Faculty of Agriculture, Buapan & Wiyut to Faculty of Humanities and Social Sciences).
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
from app.models.db_models import FacultyDB


def run_cleanup():
    print("=== 🎓 GROUNDING REMAINING ANOMALOUS FACULTY ASSIGNMENTS ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    ghosts_to_archive: set[str] = set()

    try:
        # 1. Ground Prof. Dr. Bancha Chernchujit
        bancha = db.query(FacultyDB).filter(FacultyDB.id == "tu_w58_0356_921").first()
        if bancha:
            bancha.full_name_th = "ศ.นพ. บัญชา ชื่นชูจิตต์"
            bancha.academic_title_th = "ศ.นพ."
            bancha.faculty_th = "คณะแพทยศาสตร์"
            bancha.faculty = "Faculty of Medicine"
            bancha.department_th = "ภาควิชาออร์โธปิดิกส์"
            bancha.department = "Department of Orthopaedics"
            print("  Grounded Prof. Dr. Bancha Chernchujit to Faculty of Medicine, TU.")

        # 2. Archive 58 TU non-teaching co-authors under คณะสังคมศาสตร์
        tu_soc = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยธรรมศาสตร์",
                FacultyDB.faculty_th == "คณะสังคมศาสตร์",
                FacultyDB.id != "tu_w58_0356_921",
            )
            .all()
        )
        for r in tu_soc:
            ghosts_to_archive.add(r.id)
        print(f"  Flagged {len(tu_soc)} non-teaching co-authors at TU คณะสังคมศาสตร์ for archival.")

        # 3. Archive 5 Thaksin Science Park staff
        tsu_park = (
            db.query(FacultyDB)
            .filter(
                FacultyDB.university_th == "มหาวิทยาลัยทักษิณ",
                FacultyDB.faculty_th == "อุทยานวิทยาศาสตร์และนวัตกรรมสังคม",
            )
            .all()
        )
        for r in tsu_park:
            ghosts_to_archive.add(r.id)
        print(f"  Flagged {len(tsu_park)} non-teaching Thaksin Science Park staff for archival.")

        # 4. Mahidol faculty realignments
        m1 = db.query(FacultyDB).filter(FacultyDB.id == "mu_w57_9676_672").first()
        if m1:
            m1.faculty_th = "คณะวิทยาศาสตร์"
            m1.faculty = "Faculty of Science"
            m1.department_th = "ภาควิชาสรีรวิทยา"
            m1.department = "Department of Physiology"

        m2 = db.query(FacultyDB).filter(FacultyDB.id == "mu_w57_5963_881").first()
        if m2:
            m2.faculty_th = "สถาบันโภชนาการ"
            m2.faculty = "Institute of Nutrition"
            m2.department_th = "ฝ่ายความปลอดภัยและโภชนาการ"
            m2.department = "Department of Food and Nutrition"
        print("  Realigned Mahidol faculty.")

        # 5. Chulalongkorn faculty realignment
        cq = db.query(FacultyDB).filter(FacultyDB.id == "cu_oa_disc_a5057708985").first()
        if cq:
            cq.faculty_th = "สถาบันวิจัยโลหะและวัสดุ"
            cq.faculty = "Metallurgy and Materials Science Research Institute"
            cq.department_th = "ศูนย์ความเป็นเลิศด้านวัสดุสวมใส่ตอบสนอง"
        print("  Realigned Chulalongkorn Metallurgy and Materials Science Research Institute faculty.")

        # 6. Khon Kaen faculty realignments
        kku_realign = [
            ("kku_w58_6798_651", "คณะเกษตรศาสตร์", "Faculty of Agriculture", "สาขาวิชาประมง", "Department of Fisheries"),
            ("kku_w58_6637_193", "คณะเกษตรศาสตร์", "Faculty of Agriculture", "สาขาวิชาประมง", "Department of Fisheries"),
            ("kku_w58_10124_215", "คณะเกษตรศาสตร์", "Faculty of Agriculture", "สาขาวิชาประมง", "Department of Fisheries"),
            ("kku_w58_8310_442", "คณะมนุษยศาสตร์และสังคมศาสตร์", "Faculty of Humanities and Social Sciences", "สาขาวิชาสังคมศาสตร์", "Department of Social Sciences"),
            ("kku_w58_5552_233", "คณะมนุษยศาสตร์และสังคมศาสตร์", "Faculty of Humanities and Social Sciences", "สาขาวิชาสังคมศาสตร์", "Department of Social Sciences"),
        ]
        for kid, fth, fen, dth, den in kku_realign:
            kr = db.query(FacultyDB).filter(FacultyDB.id == kid).first()
            if kr:
                kr.faculty_th = fth
                kr.faculty = fen
                kr.department_th = dth
                kr.department = den
        print("  Realigned Khon Kaen faculty to authentic academic faculties.")

        db.commit()

        # Archive ghost records
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

    print(f"Cleanup completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_cleanup()
