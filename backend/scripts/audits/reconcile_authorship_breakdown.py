"""
Reconcile authorship breakdown metrics across the database.
Ensures total_publications_count == first_author_count + co_author_count
for all faculty records with authorship position breakdown.
"""

import json
import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

# Faculty records that were disambiguated in Phase 12 (unindexed / false profile detachment)
DISAMBIGUATED_RESET_IDS = {
    "chulalongk_facultyofa_fac_001_001",
    "chulalongk_facultyofa_fac_008_008",
    "chulalongk_facultyofd_fac_020_020",
    "chulalongk_facultyofd_fac_028_028",
    "chulalongk_facultyofp_fac_010_010",
    "khonkaenun_facultyofm_fac_035_035",
    "khonkaenun_facultyofm_fac_036_036",
}


def reconcile_authorship_breakdown():
    db = SessionLocal()
    try:
        # 1. Reset disambiguated records where OpenAlex was detached
        for fid in DISAMBIGUATED_RESET_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.total_publications_count = 0
                f.first_author_count = 0
                f.co_author_count = 0
                f.total_citations = 0
                f.h_index = 0
        db.commit()

        # 2. Find all faculty with active authorship breakdowns
        facs = (
            db.query(FacultyDB)
            .filter((FacultyDB.first_author_count > 0) | (FacultyDB.co_author_count > 0))
            .all()
        )

        mismatches = [
            f
            for f in facs
            if (f.total_publications_count or 0)
            != ((f.first_author_count or 0) + (f.co_author_count or 0))
        ]

        print(f"Total faculty with active breakdown: {len(facs)}")
        print(f"Total mismatched records to reconcile: {len(mismatches)}")

        snapshot_records = []
        updated_count = 0

        for f in mismatches:
            tot = f.total_publications_count or 0
            first = f.first_author_count or 0
            co = f.co_author_count or 0

            before_state = {
                "id": f.id,
                "full_name_th": f.full_name_th,
                "total_publications_count": tot,
                "first_author_count": first,
                "co_author_count": co,
            }

            # Case: total is less than sum of components -> update total to match reality
            if tot < (first + co):
                new_tot = first + co
                f.total_publications_count = new_tot
                reason = "set_total_to_first_plus_co"
            # Case: total > first + co -> update co_author_count to balance total
            else:
                new_co = tot - first
                f.co_author_count = new_co
                reason = "set_co_to_balance_total"

            after_state = {
                "total_publications_count": f.total_publications_count,
                "first_author_count": f.first_author_count,
                "co_author_count": f.co_author_count,
                "reason": reason,
            }

            snapshot_records.append(
                {
                    "id": f.id,
                    "name": f.full_name_th,
                    "before": before_state,
                    "after": after_state,
                }
            )
            updated_count += 1

        db.commit()
        print(f"Successfully reconciled and committed {updated_count} records.")

        # Save snapshot
        snapshot_dir = backend_dir / "data" / "agent_states"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = snapshot_dir / "reconcile_authorship_breakdown_snapshot.json"

        with open(snapshot_file, "w", encoding="utf-8") as fp:
            json.dump(
                {
                    "total_reconciled": updated_count,
                    "records": snapshot_records,
                },
                fp,
                ensure_ascii=False,
                indent=2,
            )
        print(f"Snapshot checkpoint saved to {snapshot_file}")

        # Verification query
        recheck = (
            db.query(FacultyDB)
            .filter((FacultyDB.first_author_count > 0) | (FacultyDB.co_author_count > 0))
            .all()
        )
        remaining_mismatches = [
            f
            for f in recheck
            if (f.total_publications_count or 0)
            != ((f.first_author_count or 0) + (f.co_author_count or 0))
        ]
        print(f"Post-reconciliation remaining mismatches: {len(remaining_mismatches)}")
        assert len(remaining_mismatches) == 0, f"Expected 0 mismatches, found {len(remaining_mismatches)}"

    finally:
        db.close()


if __name__ == "__main__":
    reconcile_authorship_breakdown()
