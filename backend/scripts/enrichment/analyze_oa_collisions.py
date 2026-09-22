# -*- coding: utf-8 -*-
import os
import sys
import re
from collections import defaultdict
from rapidfuzz import fuzz

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def clean_name(name):
    if not name: return ""
    # strip titles
    s = re.sub(r'^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|สพ\.|น.สพ\.|สพ.ญ\.|ภก\.|ภญ\.|นายแพทย์|แพทย์หญิง|อาจารย์|ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์)\s*', '', name).strip()
    s = re.sub(r'^(ดร\.|ผศ\.|รศ\.|ศ\.|อ\.)\s*', '', s).strip()
    s = re.sub(r'^(Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s*', '', s, flags=re.IGNORECASE).strip()
    return s.strip().lower()

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).filter(FacultyDB.openalex_id.isnot(None)).filter(FacultyDB.openalex_id != 'not_indexed').all()

    by_oa = defaultdict(list)
    for f in facs:
        oa = f.openalex_id.replace("https://openalex.org/", "").strip()
        if oa:
            by_oa[oa].append(f)

    shared_oa = {k: v for k, v in by_oa.items() if len(v) > 1}
    print(f"Total shared OpenAlex IDs: {len(shared_oa)}")

    same_person_clusters = []
    different_person_clusters = []

    for oa, cluster in shared_oa.items():
        names = [clean_name(f.full_name_th) or f"{f.first_name or ''} {f.last_name or ''}".strip().lower() for f in cluster]
        names = [n for n in names if n]

        # Check pairwise similarity
        is_same = True
        if len(names) >= 2:
            min_sim = min(fuzz.token_sort_ratio(names[i], names[j]) for i in range(len(names)) for j in range(i+1, len(names)))
            if min_sim < 60:
                is_same = False

        if is_same:
            same_person_clusters.append((oa, cluster))
        else:
            different_person_clusters.append((oa, cluster))

    print(f"Same person clusters (shared OpenAlex ID across duplicate records): {len(same_person_clusters)}")
    print(f"Different person clusters (erroneous OpenAlex collision): {len(different_person_clusters)}")

    print("\n--- SAMPLE DIFFERENT PERSON CLUSTERS (ERRONEOUS OPENALEX COLLISION) ---")
    for oa, cluster in different_person_clusters[:10]:
        print(f"\nOpenAlex ID: {oa}")
        for f in cluster:
            print(f"   {f.id} | {f.full_name_th} | en: '{f.first_name}' '{f.last_name}' | {f.university_th} | {f.faculty_th} | cites: {f.total_citations}")

    db.close()

if __name__ == "__main__":
    main()
