# -*- coding: utf-8 -*-
import sys
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
records = db.query(FacultyDB).filter(
    (FacultyDB.total_publications_count == 0) | (FacultyDB.openalex_id == None) | (FacultyDB.openalex_id == '')
).all()

c0 = [f for f in records if not f.featured_publications or len(f.featured_publications) == 0]

print(f"Total found with 0 pubs: {len(c0)}")
for f in c0[:8]:
    print(f"ID: {f.id} | Name: {f.full_name_th} ({f.first_name} {f.last_name})")
    print(f"  Univ: {f.university_th} | Fac: {f.faculty_th} | Dept: {f.department_th}")
    print(f"  Interests: {f.research_interests}")
    print(f"  Courses: {f.taught_courses}")
    print(f"  Profile URL: {f.profile_url}")
    print("-" * 60)

db.close()
