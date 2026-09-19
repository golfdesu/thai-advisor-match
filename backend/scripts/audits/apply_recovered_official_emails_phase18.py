"""Apply recovered authentic university emails to faculties table in local PostgreSQL.

Phase 18:
- Ingests 125 verified authentic university emails recovered from official faculty directories:
  * Thammasat University (Faculty of Architecture & Planning - TDS: 46 faculty members via @ap.tu.ac.th, @tu.ac.th)
  * Chiang Mai University (Faculty of Associated Medical Sciences - OT: 24 faculty members via @cmu.ac.th)
  * King Mongkut's University of Technology North Bangkok (Faculty of Applied Science - Applied Statistics: 20 faculty members via @sci.kmutnb.ac.th)
  * Chulalongkorn University (Faculty of Science - Food Tech & Chem: 20 faculty members via @chula.ac.th)
  * Chiang Mai University (Faculty of Science - Biology: 10 faculty members via @cmu.ac.th)
  * Chulalongkorn University (Faculty of Dentistry: 5 faculty members via @chula.ac.th)
- Updates 1-to-1 profile URLs where applicable.
- Strictly excludes all departmental shared inboxes and freemail addresses.
- Rebuilds deterministic embedding_text for all modified faculty records.

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


DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase18.json"


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
            new_source = item.get("source")

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                continue

            changed = False
            if f.email != new_email:
                f.email = new_email
                changed = True

            # If new_source is a 1-to-1 profile URL (e.g. chem.sc.chula.ac.th or dent.chula.ac.th/teams/)
            if new_source and ("chem.sc.chula.ac.th/" in new_source or "dent.chula.ac.th/teams/" in new_source):
                if f.profile_url != new_source:
                    f.profile_url = new_source
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
                    "profile_url": f.profile_url,
                })

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase18_apply.json"
            if apply
            else "recovered_official_emails_phase18_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Total candidate items: {len(valid_items)}")
        print(f"Faculties updated with official email: {updated_count}")
        print(f"Embedding texts rebuilt: {rebuilt_count}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed all Phase 18 recovered emails to local PostgreSQL.")
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
