import sys
import os
import re
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import defaultdict
from sqlalchemy.orm import defer

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

# Find all EN name duplicate pairs
en_name_groups = defaultdict(list)
for f in faculties:
    if f.first_name and f.last_name:
        en_key = f"{f.first_name.strip().lower()} {f.last_name.strip().lower()}"
        en_name_groups[en_key].append(f)

dup_en = {k: v for k, v in en_name_groups.items() if len(v) > 1}

print(f"Total Duplicate Pairs found: {len(dup_en)}\n")

for k, grp in dup_en.items():
    print(f"=== Name: {k} ===")
    for f in grp:
        print(f"  ID: {f.id}")
        print(f"  Full Name TH: {f.full_name_th}")
        print(f"  Title: {f.academic_title_th} | Name: {f.first_name} {f.last_name}")
        print(f"  University: {f.university_th} ({f.university})")
        print(f"  Faculty: {f.faculty_th} | Department: {f.department_th}")
        print(f"  Email: {f.email}")
        print(f"  Profile URL: {f.profile_url}")
        print(f"  Interests: {f.research_interests[:2] if f.research_interests else []}")
        print()

db.close()
