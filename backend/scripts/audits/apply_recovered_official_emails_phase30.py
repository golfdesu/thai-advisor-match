"""Apply Phase 30 multi-agent recovered authentic official emails to local PostgreSQL.

Phase 30 Target High-Yield Clusters:
- Chula Water Resources Engineering (water.eng.chula.ac.th)
- Kasetsart Computer Engineering (cpe.ku.ac.th)
- Chula Allied Health Sciences (ahs.chula.ac.th)
- Chula Science - Mathematics & Computer Science (math.sc.chula.ac.th)

Strict Section 9 Invariant Compliance:
- Rejects personal freemails (@gmail, @hotmail, @yahoo, etc.)
- Rejects generic inboxes (info@, contact@, saraban@, etc.)
- Validates institutional domains (.ac.th, .edu, .or.th, etc.)
- Rebuilds deterministic embedding_text for every updated faculty
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
from app.models.db_models import FacultyDB

DATA_DIR = BACKEND_DIR / "data" / "agent_states"
DEFAULT_INPUT_FILE = DATA_DIR / "recoverable_official_emails_phase30.json"

REJECT_FREEMAILS = {
    "@gmail.com", "@hotmail.com", "@yahoo.com", "@yahoo.co.th",
    "@outlook.com", "@live.com", "@icloud.com"
}
REJECT_GENERIC = {
    "info@", "contact@", "saraban@", "admin@", "support@", "office@",
    "dean@", "webmaster@", "pr@", "academic@", "admissions@", "admission@",
    "fibo@", "fin@", "help@", "service@", "press@"
}
VALID_SUFFIXES = (
    ".ac.th", ".edu", ".or.th", ".go.th", "ku.th", ".ac.kr", ".dk",
    "tggs-bangkok.org", "chulavrc.org", "cern.ch", "chula.md"
)


def load_recovered_items(input_path: Path) -> list[dict[str, str]]:
    if not input_path.exists():
        print(f"Error: {input_path} does not exist.")
        return []
    data = json.loads(input_path.read_text(encoding="utf-8"))
    return data


def validate_email(email: str) -> bool:
    email_clean = email.strip().lower().replace("%20", "")
    if any(email_clean.endswith(f) for f in REJECT_FREEMAILS):
        return False
    if any(email_clean.startswith(g) for g in REJECT_GENERIC):
        return False
    if not any(email_clean.endswith(s) or f"@{s}" in email_clean for s in VALID_SUFFIXES):
        return False
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_clean):
        return False
    user = email_clean.split("@")[0]
    if user.startswith("_") or user.startswith(".") or len(user) < 2:
        return False
    return True


def main(apply: bool = False, input_file: str | None = None) -> None:
    in_path = Path(input_file) if input_file else DEFAULT_INPUT_FILE
    raw_items = load_recovered_items(in_path)
    print(f"Loaded {len(raw_items)} recovered records from {in_path}")

    # Validate emails
    valid_items: list[dict[str, str]] = []
    rejected_items: list[dict[str, str]] = []

    for item in raw_items:
        em = item.get("email", "").strip().lower().replace("%20", "")
        if validate_email(em):
            item["email"] = em
            valid_items.append(item)
        else:
            rejected_items.append(item)

    if rejected_items:
        print(f"Rejected {len(rejected_items)} items due to Section 9 email hygiene:")
        for r in rejected_items:
            print(f"  - {r.get('id')}: {r.get('email')}")

    db = SessionLocal()
    try:
        report = {
            "mode": "APPLY" if apply else "DRY-RUN",
            "total_candidates": len(raw_items),
            "valid_candidates": len(valid_items),
            "rejected_candidates": len(rejected_items),
            "updated_emails": [],
            "skipped_already_populated": [],
            "not_found_in_db": []
        }

        updated_emails_count = 0
        rebuilt_count = 0

        for item in valid_items:
            fid = item["id"]
            new_email = item["email"].strip().lower()
            new_source = item.get("source")

            f = db.query(FacultyDB).filter(FacultyDB.id == fid).options(defer(FacultyDB.embedding)).first()
            if not f:
                report["not_found_in_db"].append(fid)
                continue

            changed = False
            if f.email != new_email:
                f.email = new_email
                changed = True

            # Update profile URL if authentic and specific
            if new_source and ("http://" in new_source or "https://" in new_source):
                if not f.profile_url or any(gen in f.profile_url for gen in ["google.com", "facebook.com", "search"]):
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
                    "cluster": item.get("cluster") or item.get("source")
                })
            else:
                report["skipped_already_populated"].append(fid)

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase30_apply.json"
            if apply
            else "recovered_official_emails_phase30_dryrun.json"
        )
        out_path = DATA_DIR / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("----------------------------------------------------------")
        print(f"Execution Mode: {'APPLY (Committed)' if apply else 'DRY-RUN (Simulated)'}")
        print(f"Total Valid Records: {len(valid_items)}")
        print(f"Updated Emails: {updated_emails_count}")
        print(f"Rebuilt Embedding Texts: {rebuilt_count}")
        print(f"Skipped (Already Populated): {len(report['skipped_already_populated'])}")
        print(f"Report saved to: {out_path}")
        print("----------------------------------------------------------")

        if apply:
            db.commit()
            print("✅ Database changes successfully committed.")
        else:
            db.rollback()
            print("🔍 Dry-run completed. No changes made to database.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply Phase 30 recovered official emails to PostgreSQL.")
    parser.add_argument("--apply", action="store_true", help="Commit changes to database (default: dry-run)")
    parser.add_argument("--input", type=str, help="Path to input JSON file", default=None)
    args = parser.parse_args()
    main(apply=args.apply, input_file=args.input)
