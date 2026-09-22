# -*- coding: utf-8 -*-
"""
Inspect Pass 2 clusters in detail to check if they are identical persons or distinct.
"""
import os
import sys
import re
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

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
print(f"Total Pass 2 clusters: {len(p2_dups)}")

# Let's categorize clusters:
# 1. Clusters where openalex_id matches (or one has it and other is None/not_indexed)
# 2. Clusters where Thai names are essentially the same person (or one has no Thai name / English transliteration)
# 3. Clusters where Thai names are clearly DIFFERENT individuals!

suspicious_diff_thai = []
confirmed_same = []

for (univ, name_en), cluster in p2_dups.items():
    thai_names = {f.full_name_th for f in cluster if f.full_name_th and re.search(r"[฀-๿]", f.full_name_th)}
    # If more than 1 distinct Thai name exists:
    if len(thai_names) > 1:
        # Check if they are just spelling variants (e.g. มณทินี vs มนทิณี) or different people
        suspicious_diff_thai.append(((univ, name_en), list(thai_names), cluster))
    else:
        confirmed_same.append(((univ, name_en), list(thai_names), cluster))

print(f"Confirmed same / 1 Thai name clusters: {len(confirmed_same)}")
print(f"Clusters with multiple distinct Thai names: {len(suspicious_diff_thai)}")

print("\n--- Inspecting clusters with multiple distinct Thai names (first 20) ---")
for (univ, name_en), t_names, cluster in suspicious_diff_thai[:20]:
    print(f"\nUniv: {univ} | EN: '{name_en}'")
    print(f"  Thai names: {t_names}")
    for f in cluster:
        print(f"    id: {f.id} | TH: '{f.full_name_th}' | email: {f.email} | openalex: {f.openalex_id} | cites: {f.total_citations}")

db.close()
