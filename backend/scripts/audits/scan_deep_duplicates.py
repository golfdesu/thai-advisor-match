# -*- coding: utf-8 -*-
import sys
import re
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB

db = SessionLocal()

faculties = db.query(FacultyDB).all()
print(f"Total faculty records: {len(faculties)}")

# 1. Duplicate clean English name within same university
name_uni_map = defaultdict(list)
for f in faculties:
    en_fn = (f.first_name or "").strip().lower()
    en_ln = (f.last_name or "").strip().lower()
    clean_fn = re.sub(r"[^a-z]", "", en_fn)
    clean_ln = re.sub(r"[^a-z]", "", en_ln)
    full_en = f"{clean_fn}_{clean_ln}"
    if len(clean_fn) >= 2 and len(clean_ln) >= 2:
        name_uni_map[(f.university_th, full_en)].append(f)

print("\n--- DUPLICATE CLEAN ENGLISH NAMES WITHIN SAME UNIVERSITY ---")
dup_en_count = 0
for (uni, name), flist in name_uni_map.items():
    if len(flist) > 1:
        dup_en_count += 1
        print(f"[{uni}] {name}:")
        for f in flist:
            print(f"   ID: {f.id} | Name: {f.full_name_th} | Email: {f.email} | Fac: {f.faculty_th} | Dept: {f.department_th}")

print(f"Total: {dup_en_count}")

# 2. Duplicate clean Thai names within same university
th_uni_map = defaultdict(list)
for f in faculties:
    th = f.full_name_th or ""
    # strip titles
    th_clean = re.sub(r"^(ศ|รศ|ผศ|อ|ดร|นพ|พญ|ทพ|ทพญ|สพ|ภก|ภญ|\.|\s)+", "", th).strip()
    th_clean = re.sub(r"\s+", "", th_clean)
    if len(th_clean) >= 6:
        th_uni_map[(f.university_th, th_clean)].append(f)

print("\n--- DUPLICATE CLEAN THAI NAMES WITHIN SAME UNIVERSITY ---")
dup_th_count = 0
for (uni, name), flist in th_uni_map.items():
    if len(flist) > 1:
        dup_th_count += 1
        print(f"[{uni}] {name}:")
        for f in flist:
            print(f"   ID: {f.id} | Name: {f.full_name_th} | Email: {f.email} | Fac: {f.faculty_th} | Dept: {f.department_th}")

print(f"Total: {dup_th_count}")

# 3. Duplicate Personal Emails
email_map = defaultdict(list)
generic_emails = {"agro@cmu.ac.th", "sci@ku.ac.th", "dent@cmu.ac.th", "info@chula.ac.th", "grad@ku.ac.th", "admin@tu.ac.th"}
for f in faculties:
    em = (f.email or "").strip().lower()
    if em and em not in generic_emails and "@" in em:
        email_map[em].append(f)

print("\n--- DUPLICATE PERSONAL EMAILS ---")
dup_em_count = 0
for em, flist in email_map.items():
    if len(flist) > 1:
        dup_em_count += 1
        print(f"Email: {em}:")
        for f in flist:
            print(f"   ID: {f.id} | Name: {f.full_name_th} | Uni: {f.university_th} | Fac: {f.faculty_th}")

print(f"Total: {dup_em_count}")

# 4. Check ResearchLabDB lead_advisor_id integrity
print("\n--- RESEARCH LAB LEAD ADVISOR INTEGRITY ---")
labs = db.query(ResearchLabDB).all()
fac_ids = {f.id for f in faculties}
dangling_labs = [l for l in labs if l.lead_advisor_id and l.lead_advisor_id not in fac_ids]
print(f"Dangling lead_advisor_ids in research_labs: {len(dangling_labs)}")
for l in dangling_labs:
    print(f"   Lab ID: {l.id} | Name: {l.name_th} | lead_advisor_id: {l.lead_advisor_id}")

db.close()
