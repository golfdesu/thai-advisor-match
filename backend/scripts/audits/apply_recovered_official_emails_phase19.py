"""Apply Phase 19 recovered authentic emails, deduplication, and name sanitization to local PostgreSQL.

Phase 19:
1. Ingests 65 verified authentic university emails:
   - Chula Faculty of Nursing (29 faculty members via @chula.ac.th)
   - Thammasat University Faculty of Economics (14 faculty members via @econ.tu.ac.th, correcting university affiliation)
   - Chula Department of Computer Engineering (12 faculty members via @chula.ac.th and @cp.eng.chula.ac.th)
   - Chula Faculty of Veterinary Science (5 faculty members via @chula.ac.th)
   - Chula Department of Linguistics, Faculty of Arts (3 faculty members via @chula.ac.th)
   - Chula Faculty of Dentistry (1 faculty member via @chula.ac.th)
   - Kasetsart University Faculty of Science (1 faculty member via @ku.ac.th)
2. Eliminates 5 duplicate records:
   - Merges 1 work from chulalongk_facultyofe_tanasritunyakul_007 into primary record
     chulalongk_facultyofe_thanasomboonyag_040 and removes the duplicate row.
   - Deletes 4 KU committee directory duplicates with glued job titles:
     ku_2354332d_7230, ku_285b9111_9427, ku_43dde539_3137, ku_682d440e_2212.
3. Sanitizes 22 glued positional suffixes from Thai full names:
   - 21 PSU Engineering records stripping ' อาจารย์ประจำแขนง...' / ' อาจารย์ประจำวิศวกรรม...'
   - 1 TU record (tu_58504fd1_7364) stripping 'อาจารย์ประจำ'
4. Rebuilds deterministic embedding_text for all modified faculty records.

Zero external AI API calls, zero egress to Supabase.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB, ResearchLabDB


DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase19.json"

PSU_POSITIONAL_REGEX = re.compile(r"\s+อาจารย์ประจำ(?:แขนง|วิศวกรรม).*$")


def main(*, apply: bool) -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"State file not found: {DATA_FILE}")

    with open(DATA_FILE, encoding="utf-8") as f:
        valid_items = json.load(f)

    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "total_valid_email_items": len(valid_items),
        "updated_emails": [],
        "university_affiliation_fixed": [],
        "deduplicated_records_deleted": [],
        "names_sanitized": [],
        "embedding_texts_rebuilt": 0,
    }

    try:
        updated_emails_count = 0
        rebuilt_count = 0

        # Step 1: Ingest verified official emails and fix affiliations
        for item in valid_items:
            fid = item["id"]
            new_email = item["email"].strip().lower()
            new_source = item.get("source")
            new_univ = item.get("university_th")

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                continue

            changed = False
            if f.email != new_email:
                f.email = new_email
                changed = True

            if new_univ and f.university_th != new_univ:
                f.university_th = new_univ
                changed = True
                report["university_affiliation_fixed"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "new_university_th": new_univ
                })

            if new_source and ("dent.chula.ac.th/teams/" in new_source or "nurs.chula.ac.th" in new_source):
                if f.profile_url != new_source:
                    f.profile_url = new_source
                    changed = True

            if changed:
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    rebuilt_count += 1

                updated_emails_count += 1
                report["updated_emails"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th,
                    "department_th": f.department_th,
                    "new_email": new_email,
                    "profile_url": f.profile_url,
                })

        # Step 2: Deduplicate records
        # 2a. TU Econ duplicate: chulalongk_facultyofe_tanasritunyakul_007 -> chulalongk_facultyofe_thanasomboonyag_040
        dup_tu = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofe_tanasritunyakul_007").options(defer(FacultyDB.embedding)).first()
        primary_tu = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofe_thanasomboonyag_040").options(defer(FacultyDB.embedding)).first()
        if dup_tu and primary_tu:
            # merge publication count
            if (dup_tu.total_publications_count or 0) > 0:
                primary_tu.total_publications_count = max(
                    primary_tu.total_publications_count or 0,
                    dup_tu.total_publications_count or 0
                )
            # check research labs foreign key
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == dup_tu.id).update(
                {ResearchLabDB.lead_advisor_id: primary_tu.id}
            )
            report["deduplicated_records_deleted"].append({
                "deleted_id": dup_tu.id,
                "merged_into_id": primary_tu.id,
                "name": dup_tu.full_name_th
            })
            db.delete(dup_tu)

        # 2b. KU committee duplicates
        ku_dup_ids = [
            "ku_2354332d_7230",
            "ku_285b9111_9427",
            "ku_43dde539_3137",
            "ku_682d440e_2212"
        ]
        for did in ku_dup_ids:
            dup_f = db.query(FacultyDB).filter(FacultyDB.id == did).first()
            if dup_f:
                # verify 0 foreign keys
                labs_count = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == did).count()
                if labs_count == 0:
                    report["deduplicated_records_deleted"].append({
                        "deleted_id": dup_f.id,
                        "name": dup_f.full_name_th
                    })
                    db.delete(dup_f)

        # Step 3: Sanitize 22 glued positional suffixes from Thai full names
        # 3a. tu_58504fd1_7364
        tu_record = db.query(FacultyDB).filter(FacultyDB.id == "tu_58504fd1_7364").options(defer(FacultyDB.embedding)).first()
        if tu_record and "อาจารย์ประจำ" in (tu_record.full_name_th or ""):
            old_name = tu_record.full_name_th
            clean_name = old_name.replace("อาจารย์ประจำ", "").strip()
            tu_record.full_name_th = clean_name
            tu_record.embedding_text = build_faculty_embedding_text(tu_record)
            rebuilt_count += 1
            report["names_sanitized"].append({
                "id": tu_record.id,
                "old_name": old_name,
                "clean_name": clean_name
            })

        # 3b. 21 PSU Engineering records
        psu_records = db.query(FacultyDB).filter(
            FacultyDB.university_th.like("%สงขลานครินทร์%"),
            FacultyDB.full_name_th.like("%อาจารย์ประจำ%")
        ).options(defer(FacultyDB.embedding)).all()

        for pf in psu_records:
            old_name = pf.full_name_th
            clean_name = PSU_POSITIONAL_REGEX.sub("", old_name).strip()
            if clean_name != old_name:
                pf.full_name_th = clean_name
                pf.embedding_text = build_faculty_embedding_text(pf)
                rebuilt_count += 1
                report["names_sanitized"].append({
                    "id": pf.id,
                    "old_name": old_name,
                    "clean_name": clean_name
                })

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase19_apply.json"
            if apply
            else "recovered_official_emails_phase19_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Total candidate email items: {len(valid_items)}")
        print(f"Faculties updated with official email: {updated_emails_count}")
        print(f"University affiliations corrected to TU: {len(report['university_affiliation_fixed'])}")
        print(f"Duplicates deleted: {len(report['deduplicated_records_deleted'])}")
        print(f"Thai full names sanitized: {len(report['names_sanitized'])}")
        print(f"Embedding texts rebuilt: {rebuilt_count}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed all Phase 19 mutations to local PostgreSQL.")
        else:
            db.rollback()
            print("Dry-run complete. No changes were committed.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply mutations to local PostgreSQL")
    args = parser.parse_args()
    main(apply=args.apply)
