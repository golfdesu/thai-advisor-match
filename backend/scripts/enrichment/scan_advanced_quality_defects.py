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

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    print(f"Total faculty records: {len(facs)}")

    # 1. Check title tokens in first_name or last_name
    title_in_names = []
    for f in facs:
        fn = f.first_name or ""
        ln = f.last_name or ""
        if re.search(r'^(?:Aj\.?|Ajarn|Dr\.?|Prof\.?|Assoc\.?|Asst\.?|Mr\.?|Mrs\.?|Ms\.?)\b', fn, flags=re.IGNORECASE):
            title_in_names.append((f.id, 'fn', fn, ln, f.academic_title_th))
        if re.search(r'^(?:Aj\.?|Ajarn|Dr\.?|Prof\.?|Assoc\.?|Asst\.?|Mr\.?|Mrs\.?|Ms\.?)\b', ln, flags=re.IGNORECASE):
            title_in_names.append((f.id, 'ln', fn, ln, f.academic_title_th))

    print(f"\n1. Title tokens in first/last names: {len(title_in_names)}")
    for item in title_in_names[:15]:
        print(f"   {item}")

    # 2. Check non-ASCII in first_name / last_name (e.g. Chinese, Cyrillic, brackets)
    non_ascii_names = []
    for f in facs:
        fn = f.first_name or ""
        ln = f.last_name or ""
        if re.search(r'[^\x00-\x7F]', fn) or re.search(r'[^\x00-\x7F]', ln):
            non_ascii_names.append((f.id, fn, ln))

    print(f"\n2. Non-ASCII characters in English first/last names: {len(non_ascii_names)}")
    for item in non_ascii_names[:15]:
        print(f"   {item}")

    # 3. Check middle initial matching within same university
    # e.g., (First, Last) vs (First, Middle, Last)
    univ_fl_groups = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn = (f.first_name or "").strip().lower()
        ln = (f.last_name or "").strip().lower()
        if fn and ln:
            # strip middle initials from fn or ln
            fn_clean = re.sub(r'\s+[a-z]\.?$', '', fn)
            fn_clean = re.sub(r'^[a-z]\.?\s+', '', fn_clean)
            ln_clean = re.sub(r'\s+[a-z]\.?$', '', ln)
            ln_clean = re.sub(r'^[a-z]\.?\s+', '', ln_clean)
            # if fn has multiple tokens, take first
            fn_tokens = fn_clean.split()
            ln_tokens = ln_clean.split()
            if fn_tokens and ln_tokens:
                key = (f.university_th, fn_tokens[0], ln_tokens[-1])
                univ_fl_groups[key].append(f)

    fl_dups = {k: v for k, v in univ_fl_groups.items() if len(v) > 1}
    print(f"\n3. Same-university first token + last token clusters: {len(fl_dups)}")

    # Sample clusters where full strings differed
    distinct_fl_dups = []
    for k, cluster in fl_dups.items():
        distinct_names = set(f"{(f.first_name or '').lower()} {(f.last_name or '').lower()}" for f in cluster)
        if len(distinct_names) > 1:
            distinct_fl_dups.append((k, cluster))

    print(f"   Of which distinct name strings: {len(distinct_fl_dups)}")
    for (univ, fn, ln), cluster in distinct_fl_dups[:15]:
        print(f"\n   {univ} - {fn} ... {ln}:")
        for f in cluster:
            print(f"      {f.id} | fn: '{f.first_name}' | ln: '{f.last_name}' | th: '{f.full_name_th}' | oa: {f.openalex_id} | cites: {f.total_citations}")

    db.close()

if __name__ == "__main__":
    main()
