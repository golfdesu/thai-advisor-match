# -*- coding: utf-8 -*-
"""
Simulation script for Phase 3:
1. Clean 'Aj.' / titles from first_name and last_name on MFU and other records.
2. Clean empty strings in openalex_id, courses, and labs.
3. Simulate token-set same-university deduplication.
4. Simulate middle-name/middle-initial same-university deduplication.
5. Simulate Kevin D. Hyde consolidation at MFU.
"""
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

def normalize_token(t):
    return re.sub(r'[^a-z]', '', t.lower())

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    print(f"Loaded {len(facs)} faculty records.")

    # 1. Clean 'Aj.' and titles from first_name
    cleaned_names = 0
    for f in facs:
        fn = f.first_name or ""
        ln = f.last_name or ""
        if fn.lower().startswith("aj.") or fn.lower().startswith("ajarn"):
            # e.g. fn="Aj.", ln="Alan Michael Gallion"
            full = f"{fn} {ln}".strip()
            # strip Aj./Ajarn
            full_clean = re.sub(r'^(?:Aj\.?|Ajarn)\s*', '', full, flags=re.IGNORECASE).strip()
            parts = full_clean.split()
            if len(parts) >= 2:
                f.first_name = parts[0]
                f.last_name = " ".join(parts[1:])
                cleaned_names += 1
                if not f.academic_title_th:
                    f.academic_title_th = "อ."
    print(f"Cleaned 'Aj.' from {cleaned_names} faculty records.")

    # 2. Token-set deduplication simulation
    univ_token_groups = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn = (f.first_name or "").lower().strip()
        ln = (f.last_name or "").lower().strip()
        if fn and ln and len(fn) > 1 and len(ln) > 1:
            tokens = frozenset(re.findall(r'[a-z]+', f"{fn} {ln}"))
            if len(tokens) >= 2:
                univ_token_groups[(f.university_th, tokens)].append(f)

    token_dups = {k: v for k, v in univ_token_groups.items() if len(v) > 1}
    print(f"Token-set same-university clusters: {len(token_dups)}")
    token_donors = sum(len(v) - 1 for v in token_dups.values())
    print(f"Token-set donor records to merge: {token_donors}")

    # 3. Middle-name / middle-initial deduplication simulation
    # Match: same university, same first name, same last name (where one has middle initial/name)
    # e.g. "Ruvishika Jayawardena" vs "Ruvishika S. Jayawardena"
    # "Kenneth Butcher" vs "Kenneth John Butcher"
    univ_fn_ln = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn = (f.first_name or "").strip()
        ln = (f.last_name or "").strip()
        if fn and ln:
            # normalized first token
            fn_tokens = re.findall(r'[a-zA-Z]+', fn)
            ln_tokens = re.findall(r'[a-zA-Z]+', ln)
            if fn_tokens and ln_tokens:
                first = fn_tokens[0].lower()
                last = ln_tokens[-1].lower()
                # ignore single-letter first names
                if len(first) > 2 and len(last) > 2:
                    univ_fn_ln[(f.university_th, first, last)].append(f)

    middle_dups = {k: v for k, v in univ_fn_ln.items() if len(v) > 1}
    print(f"First-token + Last-token same-university clusters: {len(middle_dups)}")

    # Check which clusters are NOT in token_dups (pure middle-name/initial differences)
    pure_middle_clusters = []
    for k, cluster in middle_dups.items():
        # check if this cluster has multiple records that don't share the exact same token set
        token_sets = set(frozenset(re.findall(r'[a-z]+', f"{(f.first_name or '').lower()} {(f.last_name or '').lower()}")) for f in cluster)
        if len(token_sets) > 1:
            pure_middle_clusters.append((k, cluster))

    print(f"Pure middle-name/initial clusters: {len(pure_middle_clusters)}")
    for (univ, first, last), cluster in pure_middle_clusters[:20]:
        print(f"\n{univ} - {first} ... {last}:")
        for f in cluster:
            print(f"   {f.id} | fn: '{f.first_name}' | ln: '{f.last_name}' | th: '{f.full_name_th}' | oa: {f.openalex_id} | cites: {f.total_citations}")

    db.close()

if __name__ == "__main__":
    main()
