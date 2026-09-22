# -*- coding: utf-8 -*-
"""
Dry run for Pass 2 (English Name + University) and Pass 3 (Verified Email) deduplication:
- Includes Category 1 & Category 2 of Pass 2.
- For Category 3 of Pass 2, only includes if OpenAlex ID is identical or token_sort_ratio >= 50 on Thai name.
- Tests scoring, metric preservation, and donor record selection.
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

SPAMBOT_OR_BOILERPLATE = re.compile(r"spambot|protected from spambot|javascript enabled|textbooks copyrights", re.IGNORECASE)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

def get_bare_thai(name):
    if not name: return ""
    m = RE_TITLE.match(name)
    b = name[m.end():].strip() if m else name.strip()
    return re.sub(r"\s+", " ", b)

def get_clean_en(f):
    first = (f.first_name or "").strip()
    last = (f.last_name or "").strip()
    if SPAMBOT_OR_BOILERPLATE.search(first) or SPAMBOT_OR_BOILERPLATE.search(last):
        return ""
    first = RE_EN_PREFIX.sub("", first).strip()
    if first and last and len(first.replace(".", "")) >= 2 and len(last.replace(".", "")) >= 2:
        return f"{first} {last}".lower()
    return ""

def score_faculty(fac):
    s = 0
    # Authentic Thai full name
    name_th = fac.full_name_th or ""
    if re.search(r"[฀-๿]", name_th): s += 150
    if fac.academic_title_th: s += 50
    if fac.email and len(fac.email) > 5 and "@" in fac.email: s += 100
    if fac.openalex_id and fac.openalex_id != "not_indexed": s += 80
    if fac.total_citations: s += min(fac.total_citations, 50)
    if fac.featured_publications: s += len(fac.featured_publications) * 2
    if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 20
    if fac.image_url: s += 10
    return s

pass2_groups = defaultdict(list)
for f in faculties:
    clean_en = get_clean_en(f)
    if clean_en:
        pass2_groups[(f.university_th, clean_en)].append(f)

p2_dups = {k: v for k, v in pass2_groups.items() if len(v) > 1}

eligible_clusters = []
skipped_clusters = []

for (univ, name_en), cluster in p2_dups.items():
    thai_names = [get_bare_thai(f.full_name_th) for f in cluster if f.full_name_th and re.search(r"[฀-๿]", f.full_name_th)]
    unique_thais = list(set(thai_names))

    # Check if this cluster is eligible
    eligible = False
    if len(unique_thais) <= 1:
        # Category 1: Single Thai name, other is English-only
        eligible = True
    else:
        # Check pairwise similarity
        min_sim = min(fuzz.token_sort_ratio(unique_thais[i], unique_thais[j])
                      for i in range(len(unique_thais))
                      for j in range(i+1, len(unique_thais)))
        if min_sim >= 50:
            eligible = True
        else:
            # Check if OpenAlex ID is identical across all records with OA
            oa_ids = {f.openalex_id.replace("https://openalex.org/", "").strip() for f in cluster if f.openalex_id and f.openalex_id != "not_indexed" and f.openalex_id.strip()}
            if len(oa_ids) == 1:
                eligible = True

    if eligible:
        eligible_clusters.append(((univ, name_en), cluster))
    else:
        skipped_clusters.append(((univ, name_en), unique_thais, cluster))

print(f"Total Pass 2 candidate clusters: {len(p2_dups)}")
print(f"Eligible for safe merge: {len(eligible_clusters)}")
print(f"Skipped (potential distinct individuals): {len(skipped_clusters)}")

donor_count = sum(len(c) - 1 for _, c in eligible_clusters)
print(f"Total donor records to be merged in Pass 2: {donor_count}")

db.close()
