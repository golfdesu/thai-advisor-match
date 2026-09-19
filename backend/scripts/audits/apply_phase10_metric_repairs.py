# -*- coding: utf-8 -*-
"""Phase 10: clear stale author sub-counts after identity disambiguation.

The two target records were already disambiguated in earlier approved repairs:
Jennit Manyaem had a false OpenAlex homonym and Komsan Suriya had metrics from
another Komsan Suriya record. Their first/co-author counters were not cleared
at that time, leaving counts that contradicted the retained record metrics.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

TARGETS = {
    "chulalongk_facultyofp_fac_036_036": {
        "reason": "False CERN/Peter Jenni homonym was cleared; source record has no verified publications.",
        "expected": {
            "total_publications_count": 0,
            "first_author_count": 0,
            "co_author_count": 0,
            "total_citations": 0,
            "h_index": 0,
        },
    },
    "mfu_med_komsan_001": {
        "reason": "Cross-person OpenAlex metrics were cleared in Phase 5; stale authorship sub-counts remained.",
        "expected": {
            "first_author_count": 0,
            "co_author_count": 0,
            "total_citations": 0,
            "h_index": 0,
            "openalex_id": "not_indexed",
        },
    },
}


def run_phase10_repairs() -> None:
    db = SessionLocal()
    report = {
        "phase": 10,
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "changes": [],
    }
    try:
        for faculty_id, spec in TARGETS.items():
            faculty = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            if faculty is None:
                raise RuntimeError(f"Expected faculty record not found: {faculty_id}")

            before = {
                field: getattr(faculty, field)
                for field in spec["expected"]
            }
            changed = False
            for field, value in spec["expected"].items():
                if getattr(faculty, field) != value:
                    setattr(faculty, field, value)
                    changed = True

            report["changes"].append({
                "id": faculty_id,
                "reason": spec["reason"],
                "before": before,
                "after": spec["expected"],
                "changed": changed,
            })

        db.commit()
        checkpoint = BACKEND_DIR / "data" / "agent_states" / "phase10_metric_repairs.json"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Phase 10 committed successfully:")
        for change in report["changes"]:
            print(f"  - {change['id']}: changed={change['changed']}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_phase10_repairs()
