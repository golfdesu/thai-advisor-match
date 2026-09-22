# -*- coding: utf-8 -*-
import os
import sys
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()

    # 1. Thai characters in first_name or last_name
    print("=== 1. THAI IN FIRST/LAST NAME ===")
    thai_pattern = re.compile(r'[฀-๿]')
    thai_name_facs = []
    all_facs = db.query(FacultyDB).yield_per(1000)
    for f in all_facs:
        fn_thai = bool(f.first_name and thai_pattern.search(f.first_name))
        ln_thai = bool(f.last_name and thai_pattern.search(f.last_name))
        if fn_thai or ln_thai:
            thai_name_facs.append((f.id, f.first_name, f.last_name, f.full_name_th))
    print(f"Total faculties with Thai characters in first_name/last_name: {len(thai_name_facs)}")
    for x in thai_name_facs[:10]:
        print(f"  {x}")

    # 2. Potential same-university duplicate faculty
    print("\n=== 2. SAME-UNIVERSITY DUPLICATES (PASS 1 & 2) ===")
    by_univ_name = defaultdict(list)
    all_facs = db.query(FacultyDB).yield_per(1000)
    for f in all_facs:
        # Check normalized full_name_th
        if f.full_name_th and f.university_th:
            clean_th = re.sub(r'^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|สพ\.|น.สพ\.|สพ.ญ\.|ภก\.|ภญ\.|อ\.\s*ดร\.|ผศ\.\s*ดร\.|รศ\.\s*ดร\.|ศ\.\s*ดร\.|นายแพทย์|แพทย์หญิง|อาจารย์|ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์)\s*', '', f.full_name_th).strip()
            # Also strip titles with dots/spaces
            clean_th = re.sub(r'^(ดร\.|ผศ\.|รศ\.|ศ\.|อ\.)\s*', '', clean_th).strip()
            if len(clean_th) >= 4 and ' ' in clean_th:
                key = (f.university_th, clean_th)
                by_univ_name[key].append(f)

    dups = {k: v for k, v in by_univ_name.items() if len(v) > 1}
    print(f"Total Thai name duplicate clusters within same university: {len(dups)}")
    sample_count = 0
    for (univ, name), group in list(dups.items())[:15]:
        sample_count += 1
        print(f"\n[{sample_count}] {univ} - {name} ({len(group)} records):")
        for f in group:
            print(f"    - {f.id} | title: {f.academic_title_th} | fac: {f.faculty_th} | dept: {f.department_th} | email: {f.email} | oa: {f.openalex_id} | cites: {f.total_citations}")

    # 3. Same university English name duplicates
    print("\n=== 3. SAME-UNIVERSITY ENGLISH NAME DUPLICATES ===")
    by_univ_en = defaultdict(list)
    all_facs = db.query(FacultyDB).yield_per(1000)
    for f in all_facs:
        if f.first_name and f.last_name and f.university_th:
            fn = f.first_name.strip().lower()
            ln = f.last_name.strip().lower()
            if len(fn) > 1 and len(ln) > 1 and not thai_pattern.search(fn) and not thai_pattern.search(ln):
                key = (f.university_th, fn, ln)
                by_univ_en[key].append(f)

    en_dups = {k: v for k, v in by_univ_en.items() if len(v) > 1}
    print(f"Total English name duplicate clusters within same university: {len(en_dups)}")
    for (univ, fn, ln), group in list(en_dups.items())[:15]:
        print(f"\n{univ} - {fn} {ln} ({len(group)} records):")
        for f in group:
            print(f"    - {f.id} | th: {f.full_name_th} | fac: {f.faculty_th} | email: {f.email} | oa: {f.openalex_id} | cites: {f.total_citations}")

    db.close()

if __name__ == "__main__":
    main()
