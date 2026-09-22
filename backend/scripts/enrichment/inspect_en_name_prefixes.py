# -*- coding: utf-8 -*-
"""
Inspect the 762 records flagged under en_name_prefixes.
"""
import os
import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b|อ\.|ผศ\.|รศ\.|ศ\.)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

thai_prefix_in_en = []
en_prefix_in_en = []

for f in faculties:
    first = (f.first_name or "").strip()
    if first:
        if re.search(r"[฀-๿]", first):
            thai_prefix_in_en.append((f.id, f.first_name, f.last_name, f.academic_title_th, f.full_name_th))
        elif RE_EN_PREFIX.match(first):
            en_prefix_in_en.append((f.id, f.first_name, f.last_name, f.academic_title_th, f.full_name_th))

print(f"Thai strings in first_name: {len(thai_prefix_in_en)}")
print(f"English title prefixes in first_name: {len(en_prefix_in_en)}")

print("\n--- Sample Thai strings in first_name (first 10) ---")
for item in thai_prefix_in_en[:10]:
    print(f"  {item[0]} | first: '{item[1]}' | last: '{item[2]}' | title: '{item[3]}' | full_th: '{item[4]}'")

print("\n--- Sample English prefixes in first_name (first 10) ---")
for item in en_prefix_in_en[:10]:
    print(f"  {item[0]} | first: '{item[1]}' | last: '{item[2]}' | title: '{item[3]}' | full_th: '{item[4]}'")

db.close()
