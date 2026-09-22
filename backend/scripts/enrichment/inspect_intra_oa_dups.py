# -*- coding: utf-8 -*-
"""
Inspect all 71 intra-university OpenAlex duplicate clusters.
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

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

oa_groups = defaultdict(list)
for f in faculties:
    if f.openalex_id and f.openalex_id != "not_indexed" and f.openalex_id.strip():
        clean_oa = f.openalex_id.replace("https://openalex.org/", "").strip()
        oa_groups[(f.university_th, clean_oa)].append(f)

dup_oa = {k: v for k, v in oa_groups.items() if len(v) > 1}
print(f"Total intra-university OpenAlex duplicate clusters: {len(dup_oa)}")

donor_count = 0
for (univ, oa_id), cluster in dup_oa.items():
    donor_count += len(cluster) - 1
    print(f"\nUniv: {univ} | OpenAlex: {oa_id} ({len(cluster)} records)")
    for f in cluster:
        print(f"  {f.id} | TH: '{f.full_name_th}' | EN: '{f.first_name} {f.last_name}' | dept: '{f.department_th}' | cites: {f.total_citations} | email: {f.email}")

print(f"\nTotal donor records in intra-university OpenAlex clusters: {donor_count}")
db.close()
