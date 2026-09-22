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

same_univ_thai_dups = defaultdict(list)
for f in faculties:
    name_clean = (f.full_name_th or "").strip()
    # Check only Thai names (has Thai chars)
    if re.search(r"[฀-๿]", name_clean):
        m = RE_TITLE.match(name_clean)
        clean_bare = name_clean[m.end():].strip() if m else name_clean
        clean_bare = re.sub(r"\s+", " ", clean_bare)
        # Require at least 2 Thai words (first and last name)
        words = clean_bare.split()
        if len(words) >= 2:
            same_univ_thai_dups[(f.university_th, clean_bare)].append(f)

real_thai_dups = {k: v for k, v in same_univ_thai_dups.items() if len(v) > 1}
print(f"Total same-university Thai name duplicate sets: {len(real_thai_dups)}")

# Inspect sample
for k, group in list(real_thai_dups.items())[:15]:
    print(f"\n--- {k[0]} | '{k[1]}' (count: {len(group)}) ---")
    for f in group:
        print(f"  [{f.id}] {f.full_name_th} | fac: {f.faculty_th} | dept: {f.department_th} | email: {f.email} | pubs: {len(f.featured_publications or [])} | cites: {f.total_citations} | openalex: {f.openalex_id}")

db.close()
