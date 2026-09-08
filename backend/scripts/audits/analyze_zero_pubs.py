# -*- coding: utf-8 -*-
import sys
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import Counter

db = SessionLocal()
all_facs = db.query(FacultyDB).all()

zero_facs = [f for f in all_facs if not f.featured_publications or len(f.featured_publications) == 0]
print(f"Total in DB with 0 publications: {len(zero_facs)}")

univ_counts = Counter([f.university_th for f in zero_facs])
print("\nTop Universities for 0-pub faculties:")
for u, cnt in univ_counts.most_common(12):
    print(f"  {u}: {cnt}")

fac_counts = Counter([f.faculty_th for f in zero_facs])
print("\nTop Faculties for 0-pub faculties:")
for fc, cnt in fac_counts.most_common(15):
    print(f"  {fc}: {cnt}")

db.close()
