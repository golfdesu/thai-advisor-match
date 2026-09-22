# -*- coding: utf-8 -*-
"""
Analyze the 762 records in en_name_prefixes.
"""
import os
import sys
import re
from collections import Counter

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

prefix_records = []
for f in faculties:
    first = (f.first_name or "").strip()
    if first and RE_EN_PREFIX.match(first):
        prefix_records.append(f)

print(f"Total records with prefix in first_name: {len(prefix_records)}")

# Group by pattern of first_name and last_name
first_names = Counter((f.first_name or "").strip() for f in prefix_records)
print(f"\nTop 15 first_name values:")
for fn, count in first_names.most_common(15):
    print(f"  '{fn}': {count}")

# Check how many have English in last_name vs Thai in last_name
en_in_last = 0
thai_in_last = 0
other_last = 0

samples_en_last = []
samples_thai_last = []

for f in prefix_records:
    ln = (f.last_name or "").strip()
    has_thai = bool(re.search(r"[฀-๿]", ln))
    has_en = bool(re.search(r"[a-zA-Z]", ln))

    if has_en and not has_thai:
        en_in_last += 1
        if len(samples_en_last) < 5: samples_en_last.append(f)
    elif has_thai and not has_en:
        thai_in_last += 1
        if len(samples_thai_last) < 5: samples_thai_last.append(f)
    else:
        other_last += 1

print(f"\nLast name classification:")
print(f"  Only English in last_name: {en_in_last}")
print(f"  Only Thai in last_name: {thai_in_last}")
print(f"  Mixed / other: {other_last}")

print("\n--- Sample with English in last_name ---")
for f in samples_en_last:
    print(f"  {f.id} | title: '{f.academic_title_th}' | first: '{f.first_name}' | last: '{f.last_name}' | full_th: '{f.full_name_th}'")

print("\n--- Sample with Thai in last_name ---")
for f in samples_thai_last:
    print(f"  {f.id} | title: '{f.academic_title_th}' | first: '{f.first_name}' | last: '{f.last_name}' | full_th: '{f.full_name_th}'")

db.close()
