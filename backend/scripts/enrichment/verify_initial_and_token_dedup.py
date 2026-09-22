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

COMMON_SHORT_GIVEN = {'li', 'wei', 'jian', 'hong', 'min', 'yan', 'jun', 'hui', 'lei', 'bin', 'bo', 'chao', 'xin', 'tao', 'jie'}

def get_name_tokens(f):
    fn = (f.first_name or "").lower().strip()
    ln = (f.last_name or "").lower().strip()
    # clean 'aj.' prefix
    if fn.startswith('aj.') or fn.startswith('ajarn'):
        full = f"{fn} {ln}".strip()
        full_clean = re.sub(r'^(?:Aj\.?|Ajarn)\s*', '', full, flags=re.IGNORECASE).strip()
        parts = full_clean.split()
        if len(parts) >= 2:
            fn, ln = parts[0], " ".join(parts[1:])
    # tokenize
    tokens = re.findall(r'[a-z]+', f"{fn} {ln}")
    return fn, ln, tokens

def is_initial_match(tokens1, tokens2):
    """
    Check if tokens1 and tokens2 represent the same person with initial expansion.
    e.g. ['adam', 'm', 'cotton'] vs ['adam', 'miles', 'cotton']
    e.g. ['curt', 'barnes'] vs ['curt', 'h', 'barnes']
    """
    if len(tokens1) == 0 or len(tokens2) == 0:
        return False
    # Exact permutation (Condition A)
    if frozenset(tokens1) == frozenset(tokens2):
        return True

    # Must share first token and last token
    if tokens1[0] != tokens2[0] or tokens1[-1] != tokens2[-1]:
        return False

    first = tokens1[0]
    last = tokens1[-1]

    # Reject common short Chinese given names with omitted middle tokens
    if first in COMMON_SHORT_GIVEN or len(first) <= 2 or len(last) <= 2:
        return False

    mid1 = tokens1[1:-1]
    mid2 = tokens2[1:-1]

    # Case 1: One has no middle token, one has 1 middle token
    if len(mid1) == 0 and len(mid2) == 1:
        # e.g. ['ruvishika', 'jayawardena'] vs ['ruvishika', 's', 'jayawardena']
        return True
    if len(mid2) == 0 and len(mid1) == 1:
        return True

    # Case 2: Both have 1 middle token, one is abbreviation of other
    if len(mid1) == 1 and len(mid2) == 1:
        m1, m2 = mid1[0], mid2[0]
        if m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2)):
            return True

    # Case 3: Initial abbreviation with multiple middle tokens
    # e.g. ['maria', 'evangeline', 'l', 'wiangsamut'] vs ['maria', 'evangeline', 'loyola', 'wiangsamut']
    if len(mid1) == len(mid2):
        all_match = True
        for m1, m2 in zip(mid1, mid2):
            if not (m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2))):
                all_match = False
                break
        if all_match:
            return True

    return False

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    print(f"Loaded {len(facs)} faculty records.")

    # Group by (university_th, first_initial, last_token)
    univ_groups = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn, ln, tokens = get_name_tokens(f)
        if len(tokens) >= 2:
            key = (f.university_th, tokens[-1])
            univ_groups[key].append((f, tokens))

    matched_clusters = []
    seen_ids = set()

    for (univ, last), members in univ_groups.items():
        if len(members) < 2:
            continue
        n = len(members)
        for i in range(n):
            f1, tok1 = members[i]
            cluster = [f1]
            for j in range(i + 1, n):
                f2, tok2 = members[j]
                if f2.id in seen_ids or f1.id in seen_ids:
                    continue
                if is_initial_match(tok1, tok2):
                    cluster.append(f2)
            if len(cluster) > 1:
                matched_clusters.append((univ, cluster))
                for m in cluster:
                    seen_ids.add(m.id)

    print(f"\nTotal verified clusters to merge: {len(matched_clusters)}")
    total_donors = sum(len(c) - 1 for _, c in matched_clusters)
    print(f"Total donor records: {total_donors}")

    for idx, (univ, cluster) in enumerate(matched_clusters[:30], 1):
        print(f"\n[{idx}] {univ} ({len(cluster)} records):")
        for f in cluster:
            print(f"    {f.id} | th: '{f.full_name_th}' | fn: '{f.first_name}' | ln: '{f.last_name}' | oa: {f.openalex_id} | cites: {f.total_citations}")

    db.close()

if __name__ == "__main__":
    main()
