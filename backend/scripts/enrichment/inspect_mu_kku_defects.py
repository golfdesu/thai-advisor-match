# -*- coding: utf-8 -*-
"""
Inspect specific defect records in MU & KKU
"""
import os
import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def inspect_mu(db):
    print("=== MU DEFECT DETAILS ===")
    faculties = db.query(FacultyDB).filter(FacultyDB.university_th == "มหาวิทยาลัยมหิดล").all()
    for f in faculties:
        fn = (f.first_name or "").strip()
        ln = (f.last_name or "").strip()
        th = (f.full_name_th or "").strip()

        reasons = []
        if not fn or not ln:
            reasons.append(f"Missing Name (fn='{fn}', ln='{ln}')")
        if (fn and re.search(r"[฀-๿]", fn)) or (ln and re.search(r"[฀-๿]", ln)):
            reasons.append(f"Thai in English (fn='{fn}', ln='{ln}')")
        if len(th) <= 2 or th in ['อ.', 'ดร.', 'ผศ.', 'รศ.', 'ศ.']:
            reasons.append(f"Garbage th='{th}'")

        if reasons:
            print(f"[{f.id}] {f.faculty_th} | th='{th}' | en='{fn} {ln}' | email='{f.email}' | {reasons}")

    # Check duplicates in MU
    from collections import defaultdict
    en_map = defaultdict(list)
    for f in faculties:
        fn = (f.first_name or "").strip()
        ln = (f.last_name or "").strip()
        if fn and ln:
            en_map[f"{fn.lower()} {ln.lower()}"].append(f)
    for k, v in en_map.items():
        if len(v) > 1:
            print(f"\nMU Duplicate Cluster '{k}':")
            for f in v:
                print(f"  [{f.id}] {f.faculty_th} | {f.full_name_th} | cites={f.total_citations} | h={f.h_index} | email={f.email}")

def inspect_kku(db):
    print("\n=== KKU DEFECT DETAILS ===")
    faculties = db.query(FacultyDB).filter(FacultyDB.university_th == "มหาวิทยาลัยขอนแก่น").all()
    missing_cnt = 0
    thai_cnt = 0
    by_faculty = {}
    for f in faculties:
        fn = (f.first_name or "").strip()
        ln = (f.last_name or "").strip()
        th = (f.full_name_th or "").strip()

        is_missing = not fn or not ln
        is_thai = (fn and re.search(r"[฀-๿]", fn)) or (ln and re.search(r"[฀-๿]", ln))

        if is_missing or is_thai:
            by_faculty.setdefault(f.faculty_th, []).append(f)
            if is_missing:
                missing_cnt += 1
            if is_thai:
                thai_cnt += 1

    print(f"KKU Defect Summary: {missing_cnt} missing names, {thai_cnt} thai in english")
    print("Breakdown by Faculty:")
    for fac, recs in by_faculty.items():
        print(f"  {fac}: {len(recs)} records")
        for r in recs[:3]:
            print(f"    [{r.id}] th='{r.full_name_th}' | en='{r.first_name} {r.last_name}' | email='{r.email}'")

    # Check duplicates in KKU
    from collections import defaultdict
    en_map = defaultdict(list)
    for f in faculties:
        fn = (f.first_name or "").strip()
        ln = (f.last_name or "").strip()
        if fn and ln and not re.search(r"[฀-๿]", fn) and not re.search(r"[฀-๿]", ln):
            en_map[f"{fn.lower()} {ln.lower()}"].append(f)
    for k, v in en_map.items():
        if len(v) > 1:
            print(f"\nKKU Duplicate Cluster '{k}':")
            for f in v:
                print(f"  [{f.id}] {f.faculty_th} | {f.full_name_th} | cites={f.total_citations} | h={f.h_index} | email={f.email}")

def main():
    db = SessionLocal()
    inspect_mu(db)
    inspect_kku(db)
    db.close()

if __name__ == "__main__":
    main()
