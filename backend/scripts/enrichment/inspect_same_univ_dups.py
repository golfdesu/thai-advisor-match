# -*- coding: utf-8 -*-
import sys, os, re
from collections import defaultdict
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

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

same_univ_dups = defaultdict(list)
for f in faculties:
    name_clean = (f.full_name_th or "").strip()
    if name_clean and len(name_clean) > 4:
        m = RE_TITLE.match(name_clean)
        clean_bare = name_clean[m.end():].strip() if m else name_clean
        # Normalize spaces
        clean_bare = re.sub(r"\s+", " ", clean_bare)
        same_univ_dups[(f.university_th, clean_bare)].append(f)

real_same_dups = {k: v for k, v in same_univ_dups.items() if len(v) > 1}
print(f"Total same-university duplicate sets: {len(real_same_dups)}")

# Let's inspect 10 sets
for k, group in list(real_same_dups.items())[:10]:
    print(f"\n--- {k[0]} | '{k[1]}' (count: {len(group)}) ---")
    for f in group:
        print(f"  [{f.id}] {f.full_name_th} | EN: {f.first_name} {f.last_name} | email: {f.email} | fac: {f.faculty_th} | dept: {f.department_th} | openalex: {f.openalex_id} | cites: {f.total_citations}")

db.close()
