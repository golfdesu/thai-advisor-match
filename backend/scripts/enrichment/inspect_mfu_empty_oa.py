# -*- coding: utf-8 -*-
import os
import sys
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

THAI_REGEX = re.compile(r'[฀-๿]')

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).filter(FacultyDB.openalex_id == '').all()
    print(f"Total MFU records with openalex_id == '': {len(facs)}")

    has_thai_full_name = 0
    en_full_name = 0
    already_in_db = 0

    for f in facs:
        name = f.full_name_th or ""
        if THAI_REGEX.search(name):
            has_thai_full_name += 1
        else:
            en_full_name += 1
            print(f"  English full_name_th: {f.id} | title: '{f.academic_title_th}' | name: '{f.full_name_th}' | fn: '{f.first_name}' | ln: '{f.last_name}'")

    print(f"Has Thai full_name_th: {has_thai_full_name}")
    print(f"Has English full_name_th: {en_full_name}")

    db.close()

if __name__ == "__main__":
    main()
