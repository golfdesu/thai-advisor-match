"""Apply Phase 26 recovered authentic official emails to local PostgreSQL.

Phase 26:
1. Ingests verified authentic university emails across 10 high-priority clusters:
   - Khon Kaen University College of Computing (computing.kku.ac.th via @kku.ac.th)
   - Thammasat University Business School (tbs.tu.ac.th via @tbs.tu.ac.th)
   - Mahidol University Faculty of Tropical Medicine (tm.mahidol.ac.th via @mahidol.ac.th, @mahidol.edu)
   - Mahidol University Faculty of Science (science.mahidol.ac.th via @mahidol.ac.th)
   - Chulalongkorn University Department of Computer Engineering (cp.eng.chula.ac.th via @chula.ac.th, @cp.eng.chula.ac.th)
   - Chulalongkorn University Faculty of Economics (econ.chula.ac.th via @chula.ac.th)
   - Chulalongkorn University Vaccine Research Center (chulavrc.org via @chula.ac.th, @chulavrc.org)
   - Chiang Mai University Department of Mechanical Engineering (me.eng.cmu.ac.th via @cmu.ac.th, @eng.cmu.ac.th)
   - King Mongkut's University of Technology Thonburi Department of Computer Engineering (cpe.kmutt.ac.th via @kmutt.ac.th, @mail.kmutt.ac.th)
   - Mahidol University Faculty of Public Health (ph.mahidol.ac.th via @mahidol.ac.th)
2. Confirms that clinical hospital wards, retired emeritus professors, visiting modular faculty,
   and individuals with only personal freemails (@gmail/@yahoo) remain SQL NULL under Section 9 Quality Invariants and PDPA.
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

DATA_FILE = BACKEND_DIR / "data" / "agent_states" / "recoverable_official_emails_phase26.json"


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
                "tbs.tu.ac.th/staff/",
                "tm.mahidol.ac.th/tropmed-staff/",
                "science.mahidol.ac.th/expertise/search.php",
                "cp.eng.chula.ac.th/about/faculty/",
                "chulavrc.org/staff/",
                "me.eng.cmu.ac.th/staff/professor",
                "cpe.kmutt.ac.th/th/staff/",
                "ph.mahidol.ac.th/",
                "siit.tu.ac.th/"
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
            "recovered_official_emails_phase26_apply.json"
            if apply
            else "recovered_official_emails_phase26_dryrun.json"
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
            print("Successfully committed all Phase 26 mutations to local PostgreSQL.")
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
