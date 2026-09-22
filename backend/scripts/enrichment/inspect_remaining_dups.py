# -*- coding: utf-8 -*-
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    by_univ_name = defaultdict(list)
    for f in facs:
        name = (f.full_name_th or "").strip().lower()
        if name and f.university_th:
            by_univ_name[(f.university_th, name)].append(f)

    dups = {k: v for k, v in by_univ_name.items() if len(v) > 1}
    print(f"Total remaining duplicate name clusters within same university: {len(dups)}")
    for (univ, name), cluster in dups.items():
        print(f"\n{univ} - {name} ({len(cluster)} records):")
        for f in cluster:
            print(f"   {f.id} | th: '{f.full_name_th}' | fn: '{f.first_name}' | ln: '{f.last_name}' | fac: '{f.faculty_th}' | email: '{f.email}' | oa: '{f.openalex_id}' | cites: {f.total_citations}")

    db.close()

if __name__ == "__main__":
    main()
