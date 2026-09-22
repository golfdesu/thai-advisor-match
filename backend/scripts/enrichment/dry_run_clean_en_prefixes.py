# -*- coding: utf-8 -*-
"""
Dry run for cleaning the 762 records in en_name_prefixes.
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

RE_STRIP_TITLE = re.compile(
    r"^(?:Mr\.?|Mrs\.?|Ms\.?|Miss\.?|Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

to_fix_en = []
to_clear_thai = []

for f in faculties:
    first = (f.first_name or "").strip()
    if first and RE_EN_PREFIX.match(first):
        ln = (f.last_name or "").strip()
        has_thai = bool(re.search(r"[฀-๿]", ln))
        has_en = bool(re.search(r"[a-zA-Z]", ln))

        if has_en and not has_thai:
            to_fix_en.append((f, ln))
        else:
            to_clear_thai.append(f)

print(f"Total prefix records: {len(to_fix_en) + len(to_clear_thai)}")
print(f"Records to extract English names: {len(to_fix_en)}")
print(f"Records to clear Thai from first/last: {len(to_clear_thai)}")

print("\n--- Dry Run English Name Extractions ---")
for f, raw_ln in to_fix_en:
    # Strip any leading title in raw_ln
    clean_ln = RE_STRIP_TITLE.sub("", raw_ln).strip()
    parts = clean_ln.split()
    if len(parts) == 1:
        new_fn = parts[0].capitalize()
        new_ln = ""
    elif len(parts) == 2:
        new_fn = parts[0].capitalize()
        new_ln = parts[1].capitalize()
    else:
        # e.g. Richard Anthony O Donnell
        # Or Seppo Juhani Karrila
        new_fn = " ".join(p.capitalize() for p in parts[:-1])
        new_ln = parts[-1].capitalize()

    print(f"ID: {f.id} | raw: '{raw_ln}' -> fn: '{new_fn}', ln: '{new_ln}'")

db.close()
