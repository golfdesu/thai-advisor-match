# -*- coding: utf-8 -*-
"""
Inspect Pass 2 clusters where both records have different OpenAlex IDs.
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

diff_openalex_clusters = []
for (univ, name_en), cluster in p2_dups.items():
    oa_ids = {f.openalex_id.replace("https://openalex.org/", "").strip() for f in cluster if f.openalex_id and f.openalex_id != "not_indexed" and f.openalex_id.strip()}
    if len(oa_ids) > 1:
        diff_openalex_clusters.append(((univ, name_en), oa_ids, cluster))

print(f"Pass 2 clusters with multiple different OpenAlex IDs: {len(diff_openalex_clusters)}")

for (univ, name_en), oa_ids, cluster in diff_openalex_clusters:
    print(f"\nUniv: {univ} | EN: '{name_en}' | OpenAlex IDs: {oa_ids}")
    for f in cluster:
        print(f"  id: {f.id} | TH: '{f.full_name_th}' | fac: '{f.faculty_th}' | dept: '{f.department_th}' | cites: {f.total_citations} | OA: {f.openalex_id}")

db.close()
