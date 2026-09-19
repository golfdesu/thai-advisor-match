"""Apply forensic repairs for cross-university email mismatches and foreign visiting faculty.

Operations:
1. Purge 2 foreign visiting professors residing abroad:
   - cu_cbs_wave11_0035 (Prof. Dr. Woon Oh Jung - Seoul National University)
   - cu_cbs_wave11_0032 (Prof. Dr. Thomas Josef Otto Kirchmaier - Copenhagen Business School)
2. Re-affiliate 2 misplaced faculty records to their authentic institutions:
   - thaksinuni_facultyofm_sitthitikul_008 -> tu_litu_sitthitikul_001 (Thammasat LITU)
   - thammasatu_sirindhorn_chucherd_011 -> mfu_it_chucherd_011 (Mae Fah Luang IT)
3. Sanitize cross-university contaminated emails to None:
   - thammasatu_facultyofp_sakulpanich_026 (Orapha Sakulpanich -> None)
   - thammasatu_facultyofe_vorapojpisut_001 (Supachai Vorapojpisut -> None)
   - ubonratcha_facultyofa_jutagate_001 (Tuantong Jutagate -> None)
   - thammasatu_facultyofp_suksriwong_002 (Cha-oncin Suksriwong -> None)
   - thammasatu_facultyofp_sarisut_027 (Narong Sarisuta -> None)
   - thammasatu_facultyofp_suwankoot_003 (Uthai Suwankoot -> None)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB

FOREIGN_VISITING_IDS = [
    "cu_cbs_wave11_0035",  # Prof. Dr. Woon Oh Jung (Seoul National University)
    "cu_cbs_wave11_0032",  # Prof. Dr. Thomas Josef Otto Kirchmaier (Copenhagen Business School)
]

CLEAR_EMAIL_IDS = [
    "thammasatu_facultyofp_sakulpanich_026",  # Mahidol email -> None (Real web email is personal freemail yahoo.com)
    "thammasatu_facultyofp_suksriwong_002",    # Mahidol email -> None
    "thammasatu_facultyofp_sarisut_027",       # Mahidol email -> None
    "thammasatu_facultyofp_suwankoot_003",     # Chula email -> None
]

RECOVER_OFFICIAL_EMAILS = {
    "thammasatu_facultyofe_vorapojpisut_001": "vsupacha@engr.tu.ac.th",  # KMITL email replaced with authentic TU email
    "ubonratcha_facultyofa_jutagate_001": "tuantong.j@ubu.ac.th",        # KU email replaced with authentic UBU email
}


def run_repairs(apply_changes: bool = False):
    db = SessionLocal()
    audit_report = {
        "apply": apply_changes,
        "purged_foreign_visiting": [],
        "reaffiliated_faculty": [],
        "cleared_cross_emails": [],
    }

    try:
        # 1. Purge foreign visiting professors
        print("\n=== 1. PURGE FOREIGN VISITING PROFESSORS ===")
        for fid in FOREIGN_VISITING_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                print(f"  [PURGE] {f.id} | {f.full_name_th} | {f.university_th} | {f.email}")
                audit_report["purged_foreign_visiting"].append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "university": f.university_th,
                    "email": f.email
                })
                if apply_changes:
                    db.delete(f)
            else:
                print(f"  [NOT FOUND] {fid}")

        # 2. Re-affiliate misplaced faculty
        print("\n=== 2. RE-AFFILIATE MISPLACED FACULTY ===")

        # 2a. Pragasit Sitthitikul (Thaksin -> Thammasat LITU)
        p_old = db.query(FacultyDB).filter(FacultyDB.id == "thaksinuni_facultyofm_sitthitikul_008").first()
        if p_old:
            print(f"  [RE-AFFILIATE] {p_old.id} -> tu_litu_sitthitikul_001")
            print("    From: Thaksin University, Faculty of Music")
            print("    To:   Thammasat University, Language Institute (LITU)")
            p_new = FacultyDB(
                id="tu_litu_sitthitikul_001",
                full_name_th=p_old.full_name_th,
                first_name=p_old.first_name,
                last_name=p_old.last_name,
                academic_title_th=p_old.academic_title_th,
                university="Thammasat University",
                university_th="มหาวิทยาลัยธรรมศาสตร์",
                faculty="Language Institute",
                faculty_th="สถาบันภาษา",
                department="Language Institute",
                department_th="สถาบันภาษา",
                role="อาจารย์ประจำ",
                email="pragasit.s@litu.tu.ac.th",
                profile_url="https://litu.tu.ac.th/",
                education=p_old.education,
                research_interests=["Applied Linguistics", "Second Language Acquisition", "Reading Comprehension", "English Language Teaching (ELT)"],
                taught_courses=p_old.taught_courses,
                featured_publications=p_old.featured_publications,
                total_publications_count=p_old.total_publications_count,
                first_author_count=p_old.first_author_count,
                co_author_count=p_old.co_author_count,
                total_citations=p_old.total_citations,
                h_index=p_old.h_index,
                openalex_id=p_old.openalex_id,
                scholar_url=p_old.scholar_url,
                embedding=p_old.embedding,
            )
            p_new.embedding_text = build_faculty_embedding_text(p_new)

            audit_report["reaffiliated_faculty"].append({
                "old_id": p_old.id,
                "new_id": p_new.id,
                "name": p_new.full_name_th,
                "old_uni": p_old.university_th,
                "new_uni": p_new.university_th,
                "new_faculty": p_new.faculty_th,
                "email": p_new.email,
            })

            if apply_changes:
                db.delete(p_old)
                db.flush()
                db.add(p_new)

        # 2b. Sirikan Chucherd (TU SIIT -> Mae Fah Luang IT)
        s_old = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_sirindhorn_chucherd_011").first()
        if s_old:
            print(f"  [RE-AFFILIATE] {s_old.id} -> mfu_it_chucherd_011")
            print("    From: Thammasat University, Sirindhorn International Institute of Technology")
            print("    To:   Mae Fah Luang University, School of Information Technology")
            s_new = FacultyDB(
                id="mfu_it_chucherd_011",
                full_name_th=s_old.full_name_th,
                first_name=s_old.first_name,
                last_name=s_old.last_name,
                academic_title_th=s_old.academic_title_th,
                university="Mae Fah Luang University",
                university_th="มหาวิทยาลัยแม่ฟ้าหลวง",
                faculty="School of Information Technology",
                faculty_th="สำนักวิชาเทคโนโลยีสารสนเทศ",
                department="Department of Computer Science and Innovation",
                department_th="สาขาวิชาวิทยาการคอมพิวเตอร์และนวัตกรรมดิจิทัล",
                role="อาจารย์ประจำ",
                email="sirikan@mfu.ac.th",
                profile_url="https://itschool.mfu.ac.th/it-lecturer/",
                education=s_old.education,
                research_interests=["Computer Science", "Medical Image Processing", "Deep Learning", "Pattern Recognition"],
                taught_courses=s_old.taught_courses,
                featured_publications=s_old.featured_publications,
                total_publications_count=s_old.total_publications_count,
                first_author_count=s_old.first_author_count,
                co_author_count=s_old.co_author_count,
                total_citations=s_old.total_citations,
                h_index=s_old.h_index,
                openalex_id=s_old.openalex_id,
                scholar_url=s_old.scholar_url,
                embedding=s_old.embedding,
            )
            s_new.embedding_text = build_faculty_embedding_text(s_new)

            audit_report["reaffiliated_faculty"].append({
                "old_id": s_old.id,
                "new_id": s_new.id,
                "name": s_new.full_name_th,
                "old_uni": s_old.university_th,
                "new_uni": s_new.university_th,
                "new_faculty": s_new.faculty_th,
                "email": s_new.email,
            })

            if apply_changes:
                db.delete(s_old)
                db.flush()
                db.add(s_new)

        # 3. Sanitize cross-university contaminated emails
        print("\n=== 3. SANITIZE CROSS-UNIVERSITY CONTAMINATED EMAILS ===")
        for fid in CLEAR_EMAIL_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                old_email = f.email
                print(f"  [CLEAR EMAIL] {f.id} | {f.full_name_th} | {f.university_th} | Old: {old_email} -> New: None")
                audit_report["cleared_cross_emails"].append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "university": f.university_th,
                    "cleared_email": old_email
                })
                if apply_changes:
                    f.email = None
            else:
                print(f"  [NOT FOUND] {fid}")

        # 4. Recover authentic university emails for cross-mismatches
        print("\n=== 4. RECOVER AUTHENTIC OFFICIAL EMAILS FOR CROSS-MISMATCHES ===")
        for fid, new_email in RECOVER_OFFICIAL_EMAILS.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                old_email = f.email
                print(f"  [RECOVER EMAIL] {f.id} | {f.full_name_th} | {f.university_th} | Old: {old_email} -> New: {new_email}")
                if apply_changes:
                    f.email = new_email
            else:
                print(f"  [NOT FOUND] {fid}")

        if apply_changes:
            db.commit()
            print("\n>>> All changes committed successfully to PostgreSQL.")
        else:
            db.rollback()
            print("\n>>> DRY RUN complete. No changes were committed.")

    finally:
        db.close()

    out_file = (
        BACKEND_DIR / "data" / "agent_states" / "cross_uni_and_visiting_repairs_apply.json"
        if apply_changes
        else BACKEND_DIR / "data" / "agent_states" / "cross_uni_and_visiting_repairs_dryrun.json"
    )
    out_file.write_text(json.dumps(audit_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Audit state saved to: {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repair cross-university and visiting anomalies.")
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    args = parser.parse_args()

    run_repairs(apply_changes=args.apply)
