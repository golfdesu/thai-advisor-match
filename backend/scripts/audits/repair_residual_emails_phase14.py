"""Repair residual non-academic emails and normalize university email domain typos.

Phase 14:
1. Purges 11 residual personal freemails (ccTLDs, typo freemails, and private corporate emails) to SQL NULL.
2. Corrects 2 university email domain typos to preserve official institutional emails:
   - 'weeraphol.s@chulalac.th' -> 'weeraphol.s@chula.ac.th'
   - 'pawin@siit.tu' -> 'pawin@siit.tu.ac.th'
3. Rebuilds deterministic embedding_text for every modified faculty record.

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


# 11 residual non-academic / personal freemail / corporate emails to set to NULL
RESIDUAL_PERSONAL_EMAILS_TO_NULL = {
    "wiwat@jowit.com",
    "prasitpandectist@yahoo.co.th",
    "somjitlap@hotmail.co",
    "otani1443@yahoo.co.th",
    "alexander.horstmann@posteo.net",
    "surin_saipanya@hotmail.co.uk",
    "aphiwattee@yahoo.co.uk",
    "thanadol@thanacorp.com",
    "hudakorn_tee@hotmail.co",
    "jjpornpimol@gamil.com",
    "petchpengchai@zoho.com",
}

# 2 university email domain typos to correct and preserve
UNIVERSITY_EMAIL_CORRECTIONS = {
    "weeraphol.s@chulalac.th": "weeraphol.s@chula.ac.th",
    "pawin@siit.tu": "pawin@siit.tu.ac.th",
}


def main(*, apply: bool) -> None:
    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "personal_emails_nulled": [],
        "university_emails_corrected": [],
        "embedding_texts_rebuilt": 0,
    }

    try:
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)
        for f in faculties:
            if not f.email:
                continue

            em_clean = f.email.strip().lower()
            changed = False

            if em_clean in RESIDUAL_PERSONAL_EMAILS_TO_NULL:
                report["personal_emails_nulled"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "old_email": f.email,
                })
                f.email = None
                changed = True
            elif em_clean in UNIVERSITY_EMAIL_CORRECTIONS:
                new_email = UNIVERSITY_EMAIL_CORRECTIONS[em_clean]
                report["university_emails_corrected"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "old_email": f.email,
                    "new_email": new_email,
                })
                f.email = new_email
                changed = True

            if changed:
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1

        out_filename = (
            "residual_emails_phase14_apply.json"
            if apply
            else "residual_emails_phase14_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Personal emails nulled: {len(report['personal_emails_nulled'])}")
        for it in report["personal_emails_nulled"]:
            print(f"  - [{it['id']}] {it['full_name_th']} ({it['university_th']}): {it['old_email']} -> NULL")
        print(f"University emails corrected: {len(report['university_emails_corrected'])}")
        for it in report["university_emails_corrected"]:
            print(f"  - [{it['id']}] {it['full_name_th']} ({it['university_th']}): {it['old_email']} -> {it['new_email']}")
        print(f"Embedding texts rebuilt: {report['embedding_texts_rebuilt']}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed changes to local PostgreSQL.")
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
