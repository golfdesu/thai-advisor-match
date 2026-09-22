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
    # check full_name_th if fn/ln empty
    if not fn and not ln and f.full_name_th:
        name_th = f.full_name_th.strip()
        # strip title
        clean = re.sub(r'^(?:ศ\.(?:\(พิเศษ\)|\(เชี่ยวชาญพิเศษ\))?|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.)\s*', '', name_th)
        parts = clean.split()
        if len(parts) >= 2 and not re.search(r'[฀-๿]', clean):
            fn, ln = parts[0].lower(), " ".join(parts[1:]).lower()
    tokens = tuple(re.findall(r'[a-z]+', f"{fn} {ln}"))
    return fn, ln, tokens

def are_same_person(tok1, tok2):
    if len(tok1) < 2 or len(tok2) < 2:
        return False
    # Condition A: exact token set match (e.g. inverted name order)
    if frozenset(tok1) == frozenset(tok2):
        return True

    # Condition B: middle initial / abbreviation match
    if tok1[0] == tok2[0] and tok1[-1] == tok2[-1]:
        first, last = tok1[0], tok1[-1]
        if first in COMMON_SHORT_GIVEN or len(first) <= 2 or len(last) <= 2:
            return False
        mid1, mid2 = tok1[1:-1], tok2[1:-1]
        if len(mid1) == 0 and len(mid2) == 1:
            return True
        if len(mid2) == 0 and len(mid1) == 1:
            return True
        if len(mid1) == 1 and len(mid2) == 1:
            m1, m2 = mid1[0], mid2[0]
            if m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2)):
                return True
        if len(mid1) == len(mid2) and len(mid1) > 1:
            if all(m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2)) for m1, m2 in zip(mid1, mid2)):
                return True

    return False

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    print(f"Total faculty: {len(facs)}")

    # Special check for Kevin Hyde at MFU
    mfu_hyde = [f for f in facs if f.university_th == "มหาวิทยาลัยแม่ฟ้าหลวง" and "hyde" in f.full_name_th.lower()]
    print(f"MFU Hyde records: {len(mfu_hyde)}")

    by_univ = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn, ln, tokens = get_name_tokens(f)
        if len(tokens) >= 2:
            by_univ[f.university_th].append((f, tokens))

    clusters = []
    seen = set()

    for univ, members in by_univ.items():
        n = len(members)
        for i in range(n):
            f1, tok1 = members[i]
            if f1.id in seen:
                continue
            cluster = [f1]
            for j in range(i + 1, n):
                f2, tok2 = members[j]
                if f2.id in seen:
                    continue
                if are_same_person(tok1, tok2):
                    cluster.append(f2)
            if len(cluster) > 1:
                clusters.append((univ, cluster))
                for m in cluster:
                    seen.add(m.id)

    print(f"Total unified clusters: {len(clusters)}")
    total_donors = sum(len(c) - 1 for _, c in clusters)
    print(f"Total donor records to merge: {total_donors}")

    db.close()

if __name__ == "__main__":
    main()
