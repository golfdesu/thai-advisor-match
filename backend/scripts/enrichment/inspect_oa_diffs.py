# -*- coding: utf-8 -*-
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).filter(FacultyDB.id.like('ssru_w56_%')).filter(FacultyDB.first_name == 'Somdech').all()
    print(f"Somdech Rungsrisawat records ({len(facs)}):")
    for f in facs:
        print(f"ID: {f.id}")
        print(f"  full_name_th: {f.full_name_th}")
        print(f"  first_name: {f.first_name}, last_name: {f.last_name}")
        print(f"  oa: {f.openalex_id}, cites: {f.total_citations}, pubs: {f.total_publications_count}")
        print(f"  interests: {f.research_interests}")
        print(f"  pubs: {f.featured_publications}")

    # Check Kalawong Sa
    ks = db.query(FacultyDB).filter(FacultyDB.id.like('bsru_w56_%')).filter(FacultyDB.last_name == 'Sa').all()
    print(f"\nKalawong Sa records ({len(ks)}):")
    for f in ks:
        print(f"ID: {f.id} | fn: {f.first_name} | ln: {f.last_name} | oa: {f.openalex_id} | cites: {f.total_citations} | pubs: {f.total_publications_count} | pubs: {f.featured_publications}")

    db.close()

if __name__ == "__main__":
    main()
