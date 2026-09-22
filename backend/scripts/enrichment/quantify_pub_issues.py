# -*- coding: utf-8 -*-
"""
Inspect all 1,094 records with non-dict featured_publications.
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

summary_placeholder_count = 0
plain_string_list_count = 0
other_count = 0

for f in faculties:
    pubs = f.featured_publications
    if pubs:
        has_summary = False
        has_plain_string = False
        has_other = False
        for p in pubs:
            if isinstance(p, str):
                if p.startswith("OpenAlex h-index:"):
                    has_summary = True
                else:
                    has_plain_string = True
            elif isinstance(p, dict):
                pass
            else:
                has_other = True

        if has_summary: summary_placeholder_count += 1
        if has_plain_string: plain_string_list_count += 1
        if has_other: other_count += 1

print(f"Summary placeholder strings ('OpenAlex h-index:...'): {summary_placeholder_count}")
print(f"Plain string titles (need normalization to dict): {plain_string_list_count}")
print(f"Other non-dict entries: {other_count}")

db.close()
