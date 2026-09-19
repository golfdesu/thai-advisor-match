# -*- coding: utf-8 -*-
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB

db = SessionLocal()

zw_chars = ["﻿", "​", "‌", "‍", "\xa0", "\t", "\r", "\n"]

print("--- SCANNING FOR ZERO-WIDTH SPACES, BOM, TABS, NEWLINES IN TEXT COLUMNS ---")

fac_zw = []
for f in db.query(FacultyDB).all():
    found = []
    for col in ["full_name_th", "first_name", "last_name", "email", "academic_title_th"]:
        val = getattr(f, col)
        if val and any(c in val for c in zw_chars):
            bad = [repr(c) for c in zw_chars if c in val]
            found.append((col, val, bad))
    if found:
        fac_zw.append((f.id, found))

print(f"Faculties with hidden control/zero-width chars: {len(fac_zw)}")
for fid, cols in fac_zw:
    print(f"  {fid}:")
    for col, val, bad in cols:
        print(f"    - {col} = {repr(val)} (bad: {bad})")

course_zw = []
for c in db.query(CourseDB).all():
    found = []
    for col in ["title_th", "title_en", "degree_level", "program_type", "duration_years"]:
        val = getattr(c, col)
        if val and any(c in val for c in zw_chars):
            bad = [repr(c) for c in zw_chars if c in val]
            found.append((col, val, bad))
    if found:
        course_zw.append((c.id, found))

print(f"\nCourses with hidden control/zero-width chars: {len(course_zw)}")
for cid, cols in course_zw[:15]:
    print(f"  {cid}:")
    for col, val, bad in cols:
        print(f"    - {col} = {repr(val)} (bad: {bad})")

db.close()
