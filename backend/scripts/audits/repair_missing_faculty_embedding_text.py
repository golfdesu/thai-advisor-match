"""Restore missing faculty embedding text without regenerating vectors."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB


def repair_missing_embedding_text(*, dry_run: bool = False) -> tuple[int, int]:
    """Fill only NULL/blank text fields and preserve every existing vector."""
    db = SessionLocal()
    updated = 0
    skipped = 0
    try:
        rows = (
            db.query(FacultyDB)
            .options(defer(FacultyDB.embedding))
            .filter(FacultyDB.embedding_text.is_(None))
            .order_by(FacultyDB.id)
            .yield_per(500)
        )
        for faculty in rows:
            text = build_faculty_embedding_text(faculty)
            if not text:
                skipped += 1
                continue
            faculty.embedding_text = text
            updated += 1

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Count changes without committing")
    args = parser.parse_args()

    updated, skipped = repair_missing_embedding_text(dry_run=args.dry_run)
    mode = "would update" if args.dry_run else "updated"
    print(f"{mode}: {updated} faculty embedding_text rows")
    print(f"skipped (no source text): {skipped}")


if __name__ == "__main__":
    main()
