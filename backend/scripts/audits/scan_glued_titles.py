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

print("--- SCANNING FOR TITLES GLUED AT THE END OF FULL_NAME_TH ---")
trailing_title_keywords = [
    "ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์",
    "Assoc", "Asst", "Prof", "Lecturer", "Ph.D", "M.D", "MD"
]

glued_facs = []
for f in db.query(FacultyDB).all():
    name = (f.full_name_th or "").strip()
    # check if name ends with or contains trailing title keywords after at least 10 chars
    for kw in trailing_title_keywords:
        if kw in name[5:]: # not the prefix
            glued_facs.append((f.id, f.university_th, f.faculty_th, name, kw))

print(f"Faculties with trailing/glued titles in full_name_th: {len(glued_facs)}")
for gf in glued_facs:
    print(f"  {gf[0]} | {gf[1]} | {gf[2]} | {repr(gf[3])} | kw: {gf[4]}")

db.close()
