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

    # 1. Investigate email duplicates
    print("=== 1. EMAIL DUPLICATES ===")
    emails = [
        'parinuch.c@psu.ac.th', 'rungnaph@buu.ac.th', 'nattapon@buu.ac.th',
        'piyapong.su@up.ac.th', 'teeraphot.su@up.ac.th', 'purimpat.sa@up.ac.th',
        'adisorn.pr@up.ac.th', 'sitthidet.va@up.ac.th', 'surapol.du@up.ac.th', 'sunanta.ta@up.ac.th'
    ]
    for em in emails:
        facs = db.query(FacultyDB).filter(FacultyDB.email == em).all()
        print(f"\nEmail: {em}")
        for f in facs:
            print(f"  - {f.id} | {f.full_name_th} | {f.first_name} {f.last_name} | {f.university_th} | {f.faculty_th} | {f.department_th}")

    # 2. Investigate English names with prefixes
    print("\n=== 2. ENGLISH NAMES WITH PREFIXES ===")
    ids = [
        'wu_w51_0978_780', 'swu_w44_0101_161', 'mfu_w52_0181_934',
        'ku_agro_wave15_0011', 'ku_agro_wave15_0021', 'tsu_w50_0169_438', 'tsu_w50_1583_132'
    ]
    for fid in ids:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f:
            print(f"{f.id} | fn: '{f.first_name}' | ln: '{f.last_name}' | full_th: '{f.full_name_th}' | email: '{f.email}'")

    db.close()

if __name__ == "__main__":
    main()
