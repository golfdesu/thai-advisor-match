# -*- coding: utf-8 -*-
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()

print("--- SCANNING FOR ENGLISH ACADEMIC TITLES INSIDE full_name_th ---")
en_title_patterns = [
    r"Assoc\.?\s*Prof",
    r"Asst\.?\s*Prof",
    r"Assist\.?\s*Prof",
    r"Prof\.?\s*Dr",
    r"Lecturer",
    r",\s*Ph\.?D",
    r",\s*M\.?D",
]

found = []
for f in db.query(FacultyDB).all():
    name = f.full_name_th or ""
    for pat in en_title_patterns:
        if re.search(pat, name, flags=re.IGNORECASE):
            found.append((f.id, f.university_th, f.faculty_th, name, pat))
            break

print(f"Faculties found: {len(found)}")
for fid, uni, fac, name, pat in found:
    print(f"  {fid} | {uni} | {fac} | {repr(name)} | pat: {pat}")

db.close()
