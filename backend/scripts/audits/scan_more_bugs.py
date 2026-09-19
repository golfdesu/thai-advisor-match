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
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB

db = SessionLocal()

print("--- SCANNING FOR THAI NAMES WITH ENGLISH GLUED CHARACTERS ---")
for f in db.query(FacultyDB).all():
    name = f.full_name_th or ""
    th_letters = re.findall(r"[ก-ฮะ-์]", name)
    en_letters = re.findall(r"[a-zA-Z]", name)
    if len(th_letters) >= 8 and len(en_letters) >= 1:
        en_str = "".join(en_letters)
        print(f"{f.id} | {f.university_th} | {f.faculty_th} | {repr(name)} | EN: {en_str}")

print("\n--- SCANNING FOR FIRST_NAME / LAST_NAME CORRUPTIONS ---")
for f in db.query(FacultyDB).all():
    fn = f.first_name or ""
    ln = f.last_name or ""
    # check for weird punctuation, html tags, single chars, or titles in first_name/last_name
    if re.search(r"^(Assoc|Asst|Prof|Dr|Mr|Mrs|Ms|Lecturer)\b", fn, re.I):
        print(f"Prefix title in first_name: {f.id} | fn={repr(fn)} | ln={repr(ln)}")
    if re.search(r"(?:^|[ ,;()])(?:Ph\.D\.?|M\.D\.?|M\.Sc\.?)\s*$", ln, re.I):
        print(f"Degree in last_name: {f.id} | fn={repr(fn)} | ln={repr(ln)}")
    if re.search(r"[<>{}\[\]\\]", fn) or re.search(r"[<>{}\[\]\\]", ln):
        print(f"Punctuation in name: {f.id} | fn={repr(fn)} | ln={repr(ln)}")
    if fn and len(fn) == 1 and fn.isalpha():
        print(f"Single char first_name: {f.id} | fn={repr(fn)} | ln={repr(ln)}")
    if ln and len(ln) == 1 and ln.isalpha():
        print(f"Single char last_name: {f.id} | fn={repr(fn)} | ln={repr(ln)}")

print("\n--- SCANNING FOR UNRESOLVED / IMPOSSIBLE METRICS ---")
# Faculty with publications > 0 but citations == 0 and h_index > publications
impossible_h = db.query(FacultyDB).filter(FacultyDB.h_index > FacultyDB.total_publications_count).all()
for f in impossible_h:
    print(f"Impossible h-index: {f.id} | pubs={f.total_publications_count} | cits={f.total_citations} | h={f.h_index}")

db.close()
