# -*- coding: utf-8 -*-
"""
Deep forensic inspection of:
1. Relative image URLs in KMUTT and other universities.
2. Lab lead_advisor_id mismatch across universities.
3. Long academic titles in full_name_th.
4. Junk items in research_interests.
5. Cross-university duplicate faculty analysis.
"""
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

print("=== 1. RELATIVE IMAGE URLS IN FACULTY ===")
rel_imgs = db.query(FacultyDB).filter(FacultyDB.image_url.like("/%")).all()
print(f"Total relative image_url: {len(rel_imgs)}")
for f in rel_imgs[:15]:
    print(f"  {f.id} | {f.full_name_th} | {f.university_th} | {f.faculty_th} | img: {f.image_url}")

print("\n=== 2. LAB LEAD ADVISOR MISMATCH DETAILS ===")
labs = db.query(ResearchLabDB).all()
for l in labs:
    if l.lead_advisor_id:
        adv = db.query(FacultyDB).filter(FacultyDB.id == l.lead_advisor_id).first()
        if adv and adv.university_th != l.university_th:
            print(f"Lab {l.id} ({l.name_th}) at '{l.university_th}'")
            print(f"   -> Advisor {adv.id} ({adv.full_name_th}) at '{adv.university_th}', Fac: {adv.faculty_th}")
            # Can we find a faculty at the lab's university with matching name or interests?
            clean_name = re.sub(r"^(ศ|รศ|ผศ|อ|ดร|\.|\s)+", "", adv.full_name_th or "")
            match = db.query(FacultyDB).filter(FacultyDB.university_th == l.university_th, FacultyDB.full_name_th.contains(clean_name)).all()
            if match:
                print(f"   Found candidate at same university: {[m.id + ': ' + m.full_name_th for m in match]}")

print("\n=== 3. FULL-WORD ACADEMIC TITLES IN full_name_th ===")
long_title_patterns = [
    (re.compile(r"^ศาสตราจารย์\s+ดร\.\s*", re.I), "ศ.ดร. "),
    (re.compile(r"^รองศาสตราจารย์\s+ดร\.\s*", re.I), "รศ.ดร. "),
    (re.compile(r"^ผู้ช่วยศาสตราจารย์\s+ดร\.\s*", re.I), "ผศ.ดร. "),
    (re.compile(r"^ศาสตราจารย์\s+", re.I), "ศ. "),
    (re.compile(r"^รองศาสตราจารย์\s+", re.I), "รศ. "),
    (re.compile(r"^ผู้ช่วยศาสตราจารย์\s+", re.I), "ผศ. "),
    (re.compile(r"^อาจารย์\s+ดร\.\s*", re.I), "อ.ดร. "),
    (re.compile(r"^อาจารย์\s+", re.I), "อ. "),
]
long_title_count = 0
for f in db.query(FacultyDB).all():
    name = f.full_name_th or ""
    for pat, rep in long_title_patterns:
        if pat.search(name):
            long_title_count += 1
            if long_title_count <= 15:
                print(f"  {f.id} | '{name}' -> '{pat.sub(rep, name)}'")
            break
print(f"Total faculties with long full-word titles in full_name_th: {long_title_count}")

print("\n=== 4. JUNK RESEARCH INTERESTS ===")
junk_pat = re.compile(r"^(ไม่มี|none|-|n/a|\.|null|undefined|\?)$", re.I)
junk_int_facs = []
for f in db.query(FacultyDB).all():
    if f.research_interests:
        bad = [x for x in f.research_interests if junk_pat.match(x.strip())]
        if bad:
            junk_int_facs.append((f.id, f.full_name_th, bad, f.research_interests))
print(f"Faculties with pure junk research interests: {len(junk_int_facs)}")
for j in junk_int_facs[:15]:
    print(f"  {j[0]} | {j[1]} | junk: {j[2]} | all: {j[3]}")

db.close()
