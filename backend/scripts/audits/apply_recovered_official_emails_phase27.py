"""Apply Phase 27 multi-agent recovered authentic official emails to local PostgreSQL.

Phase 27:
Aggregates findings from autonomous subagents across:
- KMITL (aad.kmitl.ac.th, arch.kmitl.ac.th) and KMUTNB (sci.kmutnb.ac.th)
- Chulalongkorn University (Pharmacy, Engineering, Political Science, Vet, Sasin, AHS)
- Thammasat, Mahidol, and Silpakorn (SU Engineering, Mahidol Music, TU Law, TU Pharmacy)
- Regional Universities (CMU Engineering, KU Science, RU Political Science, UBU)

Strictly validates against Section 9 Quality Invariants:
- Rejects personal freemails (@gmail, @hotmail, @yahoo, etc.)
- Rejects generic inboxes (info@, contact@, saraban@)
- Validates institutional domains (.ac.th, .edu, .or.th, ku.th, etc.)
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
OUTPUT_FILE = DATA_DIR / "recoverable_official_emails_phase27.json"

REJECT_FREEMAILS = {
    "@gmail.com", "@hotmail.com", "@yahoo.com", "@outlook.com", "@live.com"
}
REJECT_GENERIC = {
    "info@", "contact@", "saraban@", "admin@", "support@", "office@",
    "dean@", "webmaster@", "pr@", "academic@"
}
VALID_SUFFIXES = (
    ".ac.th", ".edu", ".or.th", ".go.th", "ku.th", ".ac.kr", ".dk", "tggs-bangkok.org", "chulavrc.org", "cern.ch", "chula.md"
)


def load_all_recovered_items(input_path: Path | None = None) -> list[dict[str, str]]:
    """Aggregate items from specific file or all recovered_emails_*.json files."""
    items: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    files_to_read: list[Path] = []
    if input_path and input_path.exists():
        files_to_read = [input_path]
    elif OUTPUT_FILE.exists():
        files_to_read = [OUTPUT_FILE]
    else:
        files_to_read = sorted(list(DATA_DIR.glob("recovered_emails_*.json")))

    for fpath in files_to_read:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        fid = entry.get("id")
                        em = (entry.get("email") or "").strip().lower()
                        if not fid or not em or fid in seen_ids:
                            continue
                        # Validation against freemails & generic
                        if any(em.endswith(fm) for fm in REJECT_FREEMAILS):
                            continue
                        if any(em.startswith(gen) for gen in REJECT_GENERIC):
                            continue
                        dom = em.split("@")[-1] if "@" in em else ""
                        if not any(dom == s or dom.endswith(s) for s in VALID_SUFFIXES):
                            continue
                        seen_ids.add(fid)
                        items.append(entry)
        except Exception as e:
            print(f"Warning reading {fpath}: {e}", file=sys.stderr)

    return items


def main(*, apply: bool, input_file: str | None = None) -> None:
    target_input = Path(input_file) if input_file else None
    valid_items = load_all_recovered_items(target_input)

    # Save aggregated master file if reading from individual agent files
    if not OUTPUT_FILE.exists() or len(valid_items) > 0:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(valid_items, f, ensure_ascii=False, indent=2)

    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "total_valid_email_items": len(valid_items),
        "updated_emails": [],
        "embedding_texts_rebuilt": 0,
    }

    try:
        updated_emails_count = 0
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

            # Update profile URL if authentic and specific
            if new_source and ("http://" in new_source or "https://" in new_source):
                if f.profile_url != new_source and not any(gen in new_source for gen in ["google.com", "facebook.com", "search"]):
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

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase27_apply.json"
            if apply
            else "recovered_official_emails_phase27_dryrun.json"
        )
        out_path = DATA_DIR / out_filename
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Total candidate email items: {len(valid_items)}")
        print(f"Faculties updated with official email: {updated_emails_count}")
        print(f"Embedding texts rebuilt: {rebuilt_count}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed all Phase 27 mutations to local PostgreSQL.")
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
    parser.add_argument("--input", type=str, default=None, help="Optional specific input JSON path")
    args = parser.parse_args()
    main(apply=args.apply, input_file=args.input)
