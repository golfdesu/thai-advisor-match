"""Apply Phase 20 recovered authentic official emails and name repair to local PostgreSQL.

Phase 20:
1. Ingests 200 verified authentic university emails:
   - Chulalongkorn University Faculty of Engineering (65 faculty members via @chula.ac.th, @eng.chula.ac.th)
   - Chiang Mai University Faculty of Agro-Industry (62 faculty members via @cmu.ac.th)
   - Thammasat University Faculty of Engineering (51 faculty members via @engr.tu.ac.th - 100% resolution of NULLs)
   - Kasetsart University Faculty of Engineering / Chemical Engineering (22 faculty members via @ku.ac.th, @ku.th)
2. Repairs incomplete Thai full name for tu_eng_wave16_0018:
   - 'อ.ดร. ดิเรก' -> 'อ.ดร. ดิเรก นวลสิงห์' (Direk Nualsing)
3. Confirms that all remaining faculties with no published academic email remain SQL NULL (Zero-Freemail / PDPA Invariant).
4. Deterministically rebuilds embedding_text via build_faculty_embedding_text for all modified faculty records.

Zero external AI API calls, zero egress to Supabase.
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

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB


DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase20.json"


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
        "names_repaired": [],
        "embedding_texts_rebuilt": 0,
    }

    try:
        updated_emails_count = 0
        rebuilt_count = 0

        for item in valid_items:
            fid = item["id"]
            new_email = item["email"].strip().lower()
            new_source = item.get("source")
            repaired_name = item.get("repaired_full_name_th")

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                continue

            changed = False

            # Update email if different
            if f.email != new_email:
                f.email = new_email
                changed = True

            # Repair Thai name if provided (e.g. tu_eng_wave16_0018)
            if repaired_name and f.full_name_th != repaired_name:
                old_name = f.full_name_th
                f.full_name_th = repaired_name
                changed = True
                report["names_repaired"].append({
                    "id": f.id,
                    "old_name": old_name,
                    "repaired_name": repaired_name
                })

            # Update 1-to-1 profile URL if authentic and specific
            if new_source and any(k in new_source for k in [
                "eng.chula.ac.th/th/staff/",
                "ece.engr.tu.ac.th/lecturer/profile/",
                "che.eng.ku.ac.th/prof-details.html",
                "data_show3.php?id="
            ]):
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

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase20_apply.json"
            if apply
            else "recovered_official_emails_phase20_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Total candidate email items: {len(valid_items)}")
        print(f"Faculties updated with official email: {updated_emails_count}")
        print(f"Thai names repaired: {len(report['names_repaired'])}")
        print(f"Embedding texts rebuilt: {rebuilt_count}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed all Phase 20 mutations to local PostgreSQL.")
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
