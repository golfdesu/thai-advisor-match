"""Apply Phase 25 recovered authentic official emails to local PostgreSQL.

Phase 25:
1. Ingests 351 verified authentic university emails:
   - Kasetsart University Faculty of Agriculture (139 faculty members via @ku.ac.th, @ku.th)
   - Khon Kaen University Faculty of Nursing (70 faculty members via @kku.ac.th)
   - Kasetsart University Faculty of Engineering (37 faculty members via @ku.ac.th, @ku.th)
   - King Mongkut's University of Technology Thonburi Faculty of Science (25 faculty members via @kmutt.ac.th, @mail.kmutt.ac.th)
   - Ubon Ratchathani University Faculty of Pharmacy (25 faculty members via @ubu.ac.th)
   - KMITL Faculty of Architecture, Art & Design (18 faculty members via @kmitl.ac.th)
   - Chulalongkorn University Institute of Asian Studies (17 faculty members via @chula.ac.th)
   - Kasetsart University Faculty of Science (8 faculty members via @ku.ac.th, @ku.th)
   - Chulalongkorn University Faculty of Veterinary Science (7 faculty members via @chula.ac.th)
   - Chulalongkorn University Faculty of Political Science (3 faculty members via @chula.ac.th)
   - Chulalongkorn University Faculty of Pharmacy (1 faculty member via @chula.ac.th)
   - Chiang Mai University Faculty of Engineering (1 faculty member via @cmu.ac.th)
2. Confirms that unresolvable entries in clinical hospital departments (CMU Medicine Surgery/Rehab,
   PSU Medicine Internal Med/Pathology, SWU Medicine, TU Medicine, Chula Medicine), retired emeritus
   professors (Chula CP founding faculty, Chula Vet emeritus), international visiting modular faculty (Sasin MBA),
   and faculty with personal freemails (@gmail/@yahoo/@hotmail) remain SQL NULL under Section 9 Quality Invariants and PDPA.
3. Deterministically rebuilds embedding_text via build_faculty_embedding_text for all modified faculty records.

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

DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase25.json"


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

            # Update email if different
            if f.email != new_email:
                f.email = new_email
                changed = True

            # Update 1-to-1 profile URL if authentic and specific
            if new_source and any(k in new_source for k in [
                "research.ku.ac.th/forest/Person.aspx?id=",
                "hr.eng.ku.ac.th/directory.php?id=",
                "mic.kmutt.ac.th/",
                "chem.kmutt.ac.th/",
                "sci.ku.ac.th/ku-personnel/",
                "aad.kmitl.ac.th/our_team/",
                "polsci.chula.ac.th/content/view",
                "ie.eng.cmu.ac.th/people/faculty/",
                "ias.chula.ac.th/personnel/",
                "vet.chula.ac.th/researcher_info/",
                "phar.ubu.ac.th/main/profile/"
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
                    "cluster": item.get("cluster")
                })

        report["embedding_texts_rebuilt"] = rebuilt_count

        out_filename = (
            "recovered_official_emails_phase25_apply.json"
            if apply
            else "recovered_official_emails_phase25_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
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
            print("Successfully committed all Phase 25 mutations to local PostgreSQL.")
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
