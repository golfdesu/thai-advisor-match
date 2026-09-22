# -*- coding: utf-8 -*-
"""
Deep inspection of Pass 2 (Clean English Name + University):
Determine how many clusters are guaranteed same-person vs distinct people.
"""
import os
import sys
import re
from collections import defaultdict
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_TITLE = re.compile(
    r"^(ศ\.เชี่ยวชาญพิเศษ\s+ดร\.\s+นพ\.|ศ\.คลินิก\s+ดร\.\s+สพ\.ญ\.|ศ\.คลินิก\s+ทพญ\.|"
    r"ศ\.ดร\.นพ\.|ศ\.ดร\.พญ\.|ศ\.ดร\.ภก\.|ศ\.ดร\.ภญ\.|ศ\.ดร\.น\.สพ\.|ศ\.ดร\.สพ\.ญ\.|"
    r"รศ\.ดร\.นพ\.|รศ\.ดร\.พญ\.|รศ\.ดร\.ภก\.|รศ\.ดร\.ภญ\.|รศ\.ดร\.น\.สพ\.|รศ\.ดร\.สพ\.ญ\.|รศ\.ดร\.ทพ\.|รศ\.ดร\.ทพญ\.|"
    r"ผศ\.ดร\.นพ\.|ผศ\.ดร\.พญ\.|ผศ\.ดร\.ภก\.|ผศ\.ดร\.ภญ\.|ผศ\.ดร\.น\.สพ\.|ผศ\.ดร\.สพ\.ญ\.|ผศ\.ดร\.ทพ\.|ผศ\.ดร\.ทพญ\.|"
    r"ศ\.นพ\.|ศ\.พญ\.|ศ\.ภก\.|ศ\.ภญ\.|ศ\.น\.สพ\.|ศ\.สพ\.ญ\.|ศ\.ทพ\.|ศ\.ทพญ\.|"
    r"รศ\.นพ\.|รศ\.พญ\.|รศ\.ภก\.|รศ\.ภญ\.|รศ\.น\.สพ\.|รศ\.สพ\.ญ\.|รศ\.ทพ\.|รศ\.ทพญ\.|"
    r"ผศ\.นพ\.|ผศ\.พญ\.|ผศ\.ภก\.|ผศ\.ภญ\.|ผศ\.น\.สพ\.|ผศ\.สพ\.ญ\.|ผศ\.ทพ\.|ผศ\.ทพญ\.|"
    r"อ\.นพ\.|อ\.พญ\.|อ\.ภก\.|อ\.ภญ\.|อ\.น\.สพ\.|อ\.สพ\.ญ\.|อ\.ทพ\.|อ\.ทพญ\.|"
    r"ศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+นพ\.|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|"
    r"ศ\.คลินิก|รศ\.คลินิก|ผศ\.คลินิก|ศ\.\(พิเศษ\)|รศ\.\(พิเศษ\)|ผศ\.\(พิเศษ\)|"
    r"ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.)\s*"
)

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

def get_bare_thai(name):
    if not name: return ""
    m = RE_TITLE.match(name)
    b = name[m.end():].strip() if m else name.strip()
    return re.sub(r"\s+", " ", b)

pass2_groups = defaultdict(list)
for f in faculties:
    first_en = RE_EN_PREFIX.sub("", (f.first_name or "").strip()).strip()
    last_en = (f.last_name or "").strip()
    if first_en and last_en and len(first_en) > 1 and len(last_en) > 1:
        if len(first_en.replace(".", "")) >= 2 and len(last_en.replace(".", "")) >= 2:
            clean_en = f"{first_en} {last_en}".lower()
            clean_en = re.sub(r"\s+", " ", clean_en)
            pass2_groups[(f.university_th, clean_en)].append(f)

p2_dups = {k: v for k, v in pass2_groups.items() if len(v) > 1}

# Categorize
category_1_single_thai = [] # Only one distinct Thai name in cluster, or others are English-only
category_2_matching_thai = [] # Multiple Thai names, but token similarity >= 75 (spelling variants)
category_3_different_thai = [] # Multiple Thai names with low similarity

for (univ, name_en), cluster in p2_dups.items():
    thai_names = [get_bare_thai(f.full_name_th) for f in cluster if f.full_name_th and re.search(r"[฀-๿]", f.full_name_th)]
    unique_thais = list(set(thai_names))

    if len(unique_thais) <= 1:
        category_1_single_thai.append(((univ, name_en), unique_thais, cluster))
    else:
        # Check pairwise similarity between all unique Thai names
        min_sim = min(fuzz.token_sort_ratio(unique_thais[i], unique_thais[j])
                      for i in range(len(unique_thais))
                      for j in range(i+1, len(unique_thais)))
        if min_sim >= 60:
            category_2_matching_thai.append(((univ, name_en), unique_thais, cluster, min_sim))
        else:
            category_3_different_thai.append(((univ, name_en), unique_thais, cluster, min_sim))

print(f"Total Pass 2 clusters: {len(p2_dups)}")
print(f"Category 1 (Single Thai name / other is English-only): {len(category_1_single_thai)}")
print(f"Category 2 (Multiple Thai names with phonetic/spelling similarity >= 60): {len(category_2_matching_thai)}")
print(f"Category 3 (Distinct Thai names with similarity < 60): {len(category_3_different_thai)}")

print("\n--- Inspecting Category 3 (Potential Distinct People) ---")
for (univ, name_en), th_names, cluster, sim in category_3_different_thai:
    print(f"\nUniv: {univ} | EN: '{name_en}' | sim: {sim}")
    print(f"  Thai names: {th_names}")
    for f in cluster:
        print(f"    id: {f.id} | TH: '{f.full_name_th}' | fac: '{f.faculty_th}' | cites: {f.total_citations} | OA: {f.openalex_id}")

db.close()
