# -*- coding: utf-8 -*-
import sys, os, re
sys.path.insert(0, os.path.abspath('backend'))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

# A: academic_title_th has civic title
civic_in_title = []
for f in faculties:
    t = (f.academic_title_th or "").strip()
    if t in ["นาย", "นาง", "นางสาว"] or any(c in t for c in ["นาย", "นาง", "นางสาว"]):
        civic_in_title.append((f.id, f.university_th, f.full_name_th, t))

print(f"Total with civic title in academic_title_th: {len(civic_in_title)}")
for c in civic_in_title[:15]:
    print(f"  {c[0]} | {c[1]} | name: '{c[2]}' | title: '{c[3]}'")

# B: English name title leaks
en_title_fixes = []
RE_EN = re.compile(r"^(?:Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mrs\.?|Ms\.?)\s*", re.IGNORECASE)

for f in faculties:
    first = (f.first_name or "").strip()
    last = (f.last_name or "").strip()

    if first.lower() in ["dr.", "dr", "prof.", "prof", "assoc. prof.", "asst. prof.", "mr.", "mr", "mrs.", "mrs", "ms.", "ms"]:
        # Case 1: first_name is just the title, last_name has full name
        parts = last.split(maxsplit=1)
        if len(parts) == 2:
            en_title_fixes.append((f.id, "split_last", first, last, parts[0], parts[1]))
        else:
            en_title_fixes.append((f.id, "single_last", first, last, last, ""))
    elif RE_EN.match(first):
        # Case 2: first_name starts with title, e.g. "DR.KITTIRAT" or "Dr. Kittirat"
        cleaned_first = RE_EN.sub("", first).strip()
        en_title_fixes.append((f.id, "strip_prefix", first, last, cleaned_first, last))

print(f"\nTotal English name title fixes: {len(en_title_fixes)}")
for e in en_title_fixes[:15]:
    print(f"  [{e[1]}] {e[0]} | '{e[2]}' '{e[3]}' -> '{e[4]}' '{e[5]}'")

# C: Repeated compound titles in full_name_th
repeated_titles = []
for f in faculties:
    name = (f.full_name_th or "").strip()
    # Check repeated title patterns like "ศ.น.สพ. ดร. น.สพ. ดร." or "ดร. ดร."
    if re.search(r"(น\.สพ\.|สพ\.ญ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|ดร\.).*?\b\1", name):
        repeated_titles.append((f.id, f.university_th, name))

print(f"\nTotal with repeated title tokens: {len(repeated_titles)}")
for r in repeated_titles[:20]:
    print(f"  {r[0]} | {r[1]} | '{r[2]}'")

db.close()
