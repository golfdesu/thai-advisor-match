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

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    print(f"Total faculties: {len(facs)}")

    # 1. Name issues
    print("\n=== 1. Name Issues ===")
    for f in facs:
        fn = f.first_name or ""
        ln = f.last_name or ""
        nth = f.full_name_th or ""
        if re.search(r'[\d<>{}\[\]\(\)_+=*&^%$#@!~`|]', fn) or re.search(r'[\d<>{}\[\]\(\)_+=*&^%$#@!~`|]', ln):
            print(f"EN_PUNCT: {f.id} | fn: '{fn}' | ln: '{ln}' | nth: '{nth}'")
        elif '&nbsp;' in nth or '&amp;' in nth or '<' in nth:
            print(f"HTML: {f.id} | nth: '{nth}'")
        elif re.search(r'\d', nth):
            print(f"DIGIT: {f.id} | nth: '{nth}'")

    # 2. Faculty/Dept anomalies
    print("\n=== 2. Faculty/Dept Anomalies ===")
    fac_dept_count = 0
    for f in facs:
        fac_th = f.faculty_th or ""
        dept_th = f.department_th or ""
        matched = False
        for val in [fac_th, dept_th]:
            if val and any(term in val.lower() for term in ['null', 'none', 'undefined', 'http', 'www.', '.ac.th', 'โทร']):
                print(f"{f.id} ({f.university_th}): fac_th='{fac_th}', dept_th='{dept_th}'")
                fac_dept_count += 1
                matched = True
                break
    print(f"Total faculty/dept issues: {fac_dept_count}")

    # 3. Research interest anomalies
    print("\n=== 3. Research Interest Anomalies ===")
    ri_count = 0
    for f in facs:
        interests = f.research_interests or []
        for item in interests:
            if not isinstance(item, str):
                print(f"{f.id}: not_string -> {item}")
                ri_count += 1
                break
            elif any(term in item.lower() for term in ['http://', 'https://', 'www.', 'tel.', 'โทร.', '0-2', '02-']):
                print(f"{f.id}: url_or_phone -> {item}")
                ri_count += 1
                break
            elif len(item.strip()) <= 1 or item.strip() in ['-', '--', '...', 'ฯลฯ', 'etc', 'etc.']:
                print(f"{f.id}: junk_token -> '{item}'")
                ri_count += 1
                break
    print(f"Total research interest issues: {ri_count}")

    db.close()

if __name__ == "__main__":
    main()
