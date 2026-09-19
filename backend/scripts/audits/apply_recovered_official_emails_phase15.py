"""Apply recovered authentic university emails to faculties table in local PostgreSQL.

Phase 15:
- Ingests 352 verified authentic university emails recovered from 1-to-1 official faculty profiles:
  * Kasetsart University (237 faculty members via KU Forest: @src.ku.ac.th, @csc.ku.ac.th, @nontri.ku.ac.th)
  * Chulalongkorn University (115 faculty members via SC CU Chem, Bio, Math: @chula.ac.th)
- Excludes all departmental shared inboxes (chemistry@chula.ac.th).
- Rebuilds deterministic embedding_text for all 352 modified faculty records.

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


DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase15.json"


def main(*, apply: bool) -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"State file not found: {DATA_FILE}")

    with open(DATA_FILE, encoding="utf-8") as f:
        raw_data = json.load(f)

    # Exclude departmental inboxes
    valid_items = [
        item for item in raw_data
        if "chemistry" not in item["email"].lower()
    ]

    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "total_candidates": len(raw_data),
        "total_valid_items": len(valid_items),
        "updated_faculties": [],
        "embedding_texts_rebuilt": 0,
    }

    try:
        updated_count = 0
        rebuilt_count = 0

        for item in valid_items:
            fid = item["id"]
            new_email = item["email"].strip().lower()

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                continue

            if f.email != new_email:
                f.email = new_email
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    rebuilt_count += 1

                updated_count += 1
                report["updated_faculties"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th,
                    "new_email": new_email,
                })

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase15_apply.json"
            if apply
            else "recovered_official_emails_phase15_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Total valid candidate items: {len(valid_items)}")
        print(f"Faculties updated with official email: {updated_count}")
        print(f"Embedding texts rebuilt: {rebuilt_count}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed all recovered emails to local PostgreSQL.")
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
