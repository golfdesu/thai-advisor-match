# -*- coding: utf-8 -*-
import os
import sys
import re
from collections import defaultdict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def normalize_name(s):
    if not s: return ""
    # replace all unicode hyphens with ASCII hyphen
    s = re.sub(r'[‐-―−]', '-', s)
    # strip trailing degree titles
    s = re.sub(r',\s*(?:Ph\.?D\.?|D\.?V\.?M\.?(?:\s*\(Hons\))?|M\.?D\.?|M\.?Sc\.?|B\.?Sc\.?|Hons).*$', '', s, flags=re.IGNORECASE)
    # strip prefixes
    s = re.sub(r'^(?:Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mrs\.?|Ms\.?|Ph\.?D\.?)\s*', '', s, flags=re.IGNORECASE)
    # clean dots and excess whitespace
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    groups = defaultdict(list)

    for f in facs:
        if not f.university_th: continue
        # Normalized full name
        norm = normalize_name(f.full_name_th)
        if not norm and f.first_name and f.last_name:
            norm = f"{normalize_name(f.first_name)} {normalize_name(f.last_name)}".strip()
        if norm:
            groups[(f.university_th, norm)].append(f)

    dups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Total duplicate clusters found: {len(dups)}")
    total_donors = sum(len(v) - 1 for v in dups.values())
    print(f"Total donor records to merge: {total_donors}")

    # Check J. Kaewkhao
    for (univ, name), cluster in dups.items():
        if 'kaewkhao' in name:
            print(f"Found Kaewkhao cluster: {univ} - {name} ({len(cluster)} records)")

    db.close()

if __name__ == "__main__":
    main()
