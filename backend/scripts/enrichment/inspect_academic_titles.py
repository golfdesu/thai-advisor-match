# -*- coding: utf-8 -*-
"""
Inspect all distinct academic_title_th across the database
"""
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def main():
    db = SessionLocal()
    titles = [r.academic_title_th for r in db.query(FacultyDB.academic_title_th).all()]
    counter = Counter(titles)
    print(f"Total records: {len(titles)}")
    print(f"Distinct academic_title_th values: {len(counter)}")
    for t, cnt in counter.most_common(35):
        print(f"  '{t}': {cnt}")

    # Check for emeritus, senior, special
    emeritus_records = db.query(FacultyDB).filter(
        (FacultyDB.academic_title_th.like("%เกียรติคุณ%")) |
        (FacultyDB.academic_title_th.like("%อาวุโส%")) |
        (FacultyDB.academic_title_th.like("%พิเศษ%")) |
        (FacultyDB.full_name_th.like("%เกียรติคุณ%")) |
        (FacultyDB.full_name_th.like("%อาวุโส%"))
    ).all()
    print(f"\nEmeritus / Senior / Special title records: {len(emeritus_records)}")
    for r in emeritus_records[:15]:
        print(f"  [{r.id}] {r.university_th} | {r.faculty_th} | title='{r.academic_title_th}' | name='{r.full_name_th}' | email='{r.email}'")

    db.close()

if __name__ == "__main__":
    main()
