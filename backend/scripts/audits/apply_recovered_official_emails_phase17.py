# Apply recovered authentic university emails to faculties table in local PostgreSQL.
# Phase 17:
# - Ingests 173 verified authentic university emails recovered from 1-to-1 official faculty profiles across Kasetsart University Faculty of Science:
#   * Physics, Maths, Zoology, Genetics, Earth Science, Statistics, Applied Radiation, Botany, and Biochemistry
#   * Email domains: @ku.ac.th (145), @ku.th (28)
# - Updates 1-to-1 official profile URLs (e.g. /ku-personnel/<slug>/)
# - Strictly excludes all departmental shared inboxes (sci@ku.ac.th, fish@ku.ac.th, etc.)
# - Rebuilds deterministic embedding_text for all modified faculty records.
#
# Zero external AI API calls, zero egress to Supabase.
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

DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase17.json"


def main(*, apply: bool) -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"State file not found: {DATA_FILE}")

    with open(DATA_FILE, encoding="utf-8") as f:
        valid_items = json.load(f)

    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
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
            new_profile_url = item.get("profile_url")

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                continue

            changed = False
            if f.email != new_email:
                f.email = new_email
                changed = True

            if new_profile_url and f.profile_url != new_profile_url:
                f.profile_url = new_profile_url
                changed = True

            if changed:
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
                    "department_th": f.department_th,
                    "new_email": new_email,
                    "new_profile_url": new_profile_url,
                })

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase17_apply.json"
            if apply
            else "recovered_official_emails_phase17_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Total valid candidate items: {len(valid_items)}")
        print(f"Faculties updated with official email & 1-to-1 profile: {updated_count}")
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
