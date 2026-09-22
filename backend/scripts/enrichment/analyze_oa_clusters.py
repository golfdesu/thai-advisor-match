# -*- coding: utf-8 -*-
"""
Analyze intra-university OpenAlex duplicate clusters into:
1. True duplicates (same person) -> Merge
2. Erroneous multi-person assignments -> Clear openalex_id or assign to correct person
"""
import os
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer
from rapidfuzz import fuzz

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

oa_groups = defaultdict(list)
for f in faculties:
    if f.openalex_id and f.openalex_id != "not_indexed" and f.openalex_id.strip():
        clean_oa = f.openalex_id.replace("https://openalex.org/", "").strip()
        oa_groups[(f.university_th, clean_oa)].append(f)

dup_oa = {k: v for k, v in oa_groups.items() if len(v) > 1}

merge_clusters = []
conflict_clusters = []

for (univ, oa_id), cluster in dup_oa.items():
    if len(cluster) > 5:
        conflict_clusters.append(((univ, oa_id), cluster))
        continue

    # Detailed pairwise check
    is_same = True
    for i in range(len(cluster)):
        for j in range(i + 1, len(cluster)):
            f1, f2 = cluster[i], cluster[j]
            ln1 = (f1.last_name or "").lower().strip()
            ln2 = (f2.last_name or "").lower().strip()
            fn1 = (f1.first_name or "").lower().strip()
            fn2 = (f2.first_name or "").lower().strip()

            # Check abbreviation
            is_abbrev = (len(fn1) <= 2 and fn1.replace(".", "") == fn2[:1]) or \
                        (len(fn2) <= 2 and fn2.replace(".", "") == fn1[:1])

            ln_sim = fuzz.ratio(ln1, ln2)
            fn_sim = fuzz.ratio(fn1, fn2)
            th_sim = fuzz.token_sort_ratio(f1.full_name_th, f2.full_name_th)

            # Special case for Sutisa Nudmamud-Thanoi vs สุทิสา ถาน้อย
            special_match = ("thanoi" in f1.full_name_th.lower() and "thanoi" in f2.full_name_th.lower()) or \
                            ("chaijan" in f1.full_name_th.lower() and "ชัยจันทร์" in f2.full_name_th) or \
                            ("bunyasiri" in (ln1 + ln2) or "nitithanprapas" in (ln1 + ln2))

            if (ln_sim >= 75 and (is_abbrev or fn_sim >= 65)) or th_sim >= 60 or special_match:
                continue
            else:
                is_same = False
                break
        if not is_same:
            break

    if is_same:
        merge_clusters.append(((univ, oa_id), cluster))
    else:
        conflict_clusters.append(((univ, oa_id), cluster))

print(f"Total Clusters: {len(dup_oa)}")
print(f"Merge Clusters (Same Person): {len(merge_clusters)}")
print(f"Conflict Clusters (Distinct Persons): {len(conflict_clusters)}\n")

print("=== MERGE CLUSTERS ===")
for (univ, oa_id), cluster in merge_clusters:
    names = [f"[{f.id}] TH:'{f.full_name_th}' EN:'{f.first_name} {f.last_name}'" for f in cluster]
    print(f"Univ: {univ} | OA: {oa_id} ({len(cluster)} records)\n  " + "\n  ".join(names))

print("\n=== CONFLICT CLUSTERS ===")
for (univ, oa_id), cluster in conflict_clusters:
    names = [f"[{f.id}] TH:'{f.full_name_th}' EN:'{f.first_name} {f.last_name}'" for f in cluster]
    print(f"Univ: {univ} | OA: {oa_id} ({len(cluster)} records)\n  " + "\n  ".join(names[:5]))
    if len(names) > 5:
        print(f"  ... and {len(names) - 5} more")

db.close()
