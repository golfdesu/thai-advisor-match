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
from rapidfuzz import fuzz
from sqlalchemy.orm import defer

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

# Check profile URL duplicates
url_map = defaultdict(list)
for f in faculties:
    if f.profile_url and len(f.profile_url) > 10:
        url_map[f.profile_url.strip().lower()].append(f)

dup_urls = {k: v for k, v in url_map.items() if len(v) > 1}
print(f"Total Duplicate Profile URLs: {len(dup_urls)}\n")

for url, grp in dup_urls.items():
    print(f"=== URL: {url} ===")
    for f in grp:
        print(f"  - ID: {f.id} | {f.academic_title_th} {f.full_name_th} | EN: {f.first_name} {f.last_name} | {f.university_th} - {f.faculty_th} | Email: {f.email}")
    print()

db.close()
