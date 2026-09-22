# -*- coding: utf-8 -*-
import sys, os
from collections import defaultdict
sys.path.insert(0, os.path.abspath('backend'))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

openalex_groups = defaultdict(list)
for f in faculties:
    if f.openalex_id:
        openalex_groups[f.openalex_id].append(f)

dups = {k: v for k, v in openalex_groups.items() if len(v) > 1}
print(f"Total duplicate OpenAlex ID sets: {len(dups)}")

for k, group in list(dups.items())[:10]:
    print(f"\n--- OpenAlex ID: {k} (count: {len(group)}) ---")
    for f in group:
        print(f"  [{f.id}] {f.university_th} | {f.full_name_th} | EN: {f.first_name} {f.last_name} | email: {f.email} | pubs: {len(f.featured_publications or [])} | cites: {f.total_citations}")

db.close()
