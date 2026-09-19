"""Audit and correct Chula Sasin visiting faculty affiliations in PostgreSQL.

1. Re-affiliate Dr. Dolchai La-ornual (cu_sasin_011) to his true home institution:
   - University: มหาวิทยาลัยมหิดล (Mahidol University)
   - Faculty: วิทยาลัยนานาชาติ (Mahidol University International College - MUIC)
   - Department: สาขาวิชาบริหารธุรกิจ (Business Administration Division)
   - ID: mu_muic_dolchai_001
   - Name: อ. ดร. ดลชัย ลาภอรุณลักษณ์ (Dolchai La-ornual, Ph.D.)
   - Email: dolchai.lar@mahidol.ac.th

2. Purge foreign visiting professors from Sasin (cu_sasin_*) who reside and work
   permanently abroad (Northwestern, Yale, UIC, WHU, Baruch CUNY):
   - cu_sasin_014 (Eliane Karsaklian - Univ of Illinois Chicago)
   - cu_sasin_028 (Mark W. Finn - Northwestern Univ)
   - cu_sasin_030 (Michael Frenkel - WHU Germany)
   - cu_sasin_045 (Sankar Sen - Baruch College CUNY)
   - cu_sasin_052 (Tauhid R. Zaman - Yale Univ)

3. Update embedding_text deterministically for newly affiliated faculty.
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

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB

DATA_DIR = BACKEND_DIR / "data" / "agent_states"
FOREIGN_VISITING_IDS = [
    "cu_sasin_014",  # Eliane Karsaklian (UIC)
    "cu_sasin_028",  # Mark W. Finn (Northwestern)
    "cu_sasin_030",  # Michael Frenkel (WHU)
    "cu_sasin_045",  # Sankar Sen (Baruch CUNY)
    "cu_sasin_052",  # Tauhid R. Zaman (Yale)
]


def main(apply: bool = False) -> None:
    db = SessionLocal()
    report = {
        "mode": "APPLY" if apply else "DRY-RUN",
        "re_affiliated": [],
        "purged_foreign_visiting": []
    }

    try:
        # 1. Re-affiliate Dr. Dolchai La-ornual
        dolchai = db.query(FacultyDB).filter(FacultyDB.id == "cu_sasin_011").first()
        if dolchai:
            # Create new MUIC record
            new_dolchai = FacultyDB(
                id="mu_muic_dolchai_001",
                full_name_th="อ. ดร. ดลชัย ลาภอรุณลักษณ์",
                first_name="Dolchai",
                last_name="La-ornual",
                academic_title_th="อ. ดร.",
                university="Mahidol University",
                university_th="มหาวิทยาลัยมหิดล",
                faculty="Mahidol University International College (MUIC)",
                faculty_th="วิทยาลัยนานาชาติ",
                department="Business Administration Division",
                department_th="สาขาวิชาบริหารธุรกิจ",
                role="Faculty",
                email="dolchai.lar@mahidol.ac.th",
                image_url=dolchai.image_url,
                profile_url="https://muic.mahidol.ac.th/eng/faculty/business-administration-division/",
                research_interests=dolchai.research_interests,
                taught_courses=dolchai.taught_courses,
                featured_publications=dolchai.featured_publications,
                education=dolchai.education,
                total_publications_count=dolchai.total_publications_count,
                first_author_count=dolchai.first_author_count,
                co_author_count=dolchai.co_author_count,
                total_citations=dolchai.total_citations,
                h_index=dolchai.h_index,
                openalex_id=dolchai.openalex_id,
                scholar_url=dolchai.scholar_url,
                embedding=dolchai.embedding
            )
            new_dolchai.embedding_text = build_faculty_embedding_text(new_dolchai)

            report["re_affiliated"].append({
                "old_id": dolchai.id,
                "new_id": new_dolchai.id,
                "name": new_dolchai.full_name_th,
                "old_uni": dolchai.university_th,
                "new_uni": new_dolchai.university_th,
                "old_faculty": dolchai.faculty_th,
                "new_faculty": new_dolchai.faculty_th,
                "department": new_dolchai.department_th,
                "email": new_dolchai.email
            })

            if apply:
                db.delete(dolchai)
                db.flush()
                db.add(new_dolchai)
        else:
            print("  [WARN] cu_sasin_011 not found or already migrated.")

        # 2. Purge foreign visiting faculty
        for fid in FOREIGN_VISITING_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                report["purged_foreign_visiting"].append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "email": f.email,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th
                })
                if apply:
                    db.delete(f)

        out_name = "sasin_visiting_corrections_apply.json" if apply else "sasin_visiting_corrections_dryrun.json"
        out_path = DATA_DIR / out_name
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 60)
        print(f"Mode: {'APPLY (Committed)' if apply else 'DRY-RUN (Simulated)'}")
        print("=" * 60)
        print(f"Re-affiliated to Mahidol MUIC: {len(report['re_affiliated'])}")
        for r in report["re_affiliated"]:
            print(f"  - {r['old_id']} -> {r['new_id']}: {r['name']} ({r['new_uni']} - {r['new_faculty']})")
        print(f"Purged Foreign Visiting Faculty: {len(report['purged_foreign_visiting'])}")
        for p in report["purged_foreign_visiting"]:
            print(f"  - {p['id']}: {p['name']} ({p['email']})")
        print(f"Report saved to: {out_path}")

        if apply:
            db.commit()
            print("\nDatabase changes successfully committed.")
        else:
            db.rollback()
            print("\nDry-run complete. No changes made to database.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    args = parser.parse_args()
    main(apply=args.apply)
