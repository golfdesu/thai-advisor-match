# -*- coding: utf-8 -*-
import os
import sys
import re
from collections import defaultdict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def parse_en_name(full_name):
    if not full_name:
        return None, None
    # Strip any title
    s = re.sub(r'^(Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s*', '', full_name, flags=re.IGNORECASE).strip()
    parts = s.split()
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    return None, None

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    thai_regex = re.compile(r'[฀-๿]')

    # Count how many would get first_name and last_name
    can_parse = 0
    for f in facs:
        if not f.first_name and f.full_name_th and not thai_regex.search(f.full_name_th):
            fn, ln = parse_en_name(f.full_name_th)
            if fn and ln:
                can_parse += 1
    print(f"Total records that can have first_name and last_name populated from full_name_th: {can_parse}")

    # Now simulate Pass 2 grouping
    pass2_groups = defaultdict(list)
    for f in facs:
        fn = f.first_name
        ln = f.last_name
        if not fn and f.full_name_th and not thai_regex.search(f.full_name_th):
            fn, ln = parse_en_name(f.full_name_th)
        if fn and ln and not thai_regex.search(fn) and not thai_regex.search(ln):
            fn_clean = fn.strip().lower()
            ln_clean = ln.strip().lower()
            if len(fn_clean.replace('.', '')) >= 2 and len(ln_clean.replace('.', '')) >= 2:
                pass2_groups[(f.university_th, f"{fn_clean} {ln_clean}")].append(f)

    dups = {k: v for k, v in pass2_groups.items() if len(v) > 1}
    print(f"Total Pass 2 duplicate clusters found: {len(dups)}")
    total_donors = sum(len(v) - 1 for v in dups.values())
    print(f"Total potential donor records that can be deduplicated: {total_donors}")

    # Inspect some clusters
    sample = 0
    for (univ, name), cluster in dups.items():
        if len(cluster) >= 3:
            sample += 1
            print(f"\nCluster [{sample}] {univ} - {name} ({len(cluster)} records):")
            for f in cluster:
                print(f"   {f.id} | th: {f.full_name_th} | oa: {f.openalex_id} | cites: {f.total_citations} | pubs: {f.total_publications_count}")
            if sample >= 10:
                break

    db.close()

if __name__ == "__main__":
    main()
