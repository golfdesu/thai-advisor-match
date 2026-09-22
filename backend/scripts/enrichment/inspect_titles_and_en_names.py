# -*- coding: utf-8 -*-
import sys, os, re
sys.path.insert(0, os.path.abspath('backend'))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_TITLE = re.compile(
    r"^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|"
    r"นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.|"
    r"ศ\.คลินิก|รศ\.คลินิก|ผศ\.คลินิก|ศ\.\(พิเศษ\)|รศ\.\(พิเศษ\)|ผศ\.\(พิเศษ\))\s*"
)

RE_EN_PREFIX = re.compile(
    r"^(Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Lecturer|Mr\.|Mrs\.|Ms\.)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

mismatches = []
for f in faculties:
    name = (f.full_name_th or "").strip()
    title = (f.academic_title_th or "").strip()
    m = RE_TITLE.match(name)
    if m:
        extracted = m.group(1)
        if title != extracted:
            mismatches.append((f.id, f.university_th, name, title, extracted))

en_leaks = []
for f in faculties:
    first_name = (f.first_name or "").strip()
    last_name = (f.last_name or "").strip()
    m = RE_EN_PREFIX.match(first_name)
    if m:
        en_leaks.append((f.id, f.university_th, first_name, last_name))

print(f"Total title mismatches: {len(mismatches)}")
for m in mismatches[:20]:
    print(f"  {m[0]} | {m[1]} | name: '{m[2]}' | curr_title: '{m[3]}' -> should_be: '{m[4]}'")

print(f"\nTotal English name leaks: {len(en_leaks)}")
for e in en_leaks[:20]:
    print(f"  {e[0]} | {e[1]} | first: '{e[2]}' | last: '{e[3]}'")

db.close()
