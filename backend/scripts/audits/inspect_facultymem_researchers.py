# -*- coding: utf-8 -*-
"""
Inspect regionalun_facultymem_* where faculty_th == 'คณาจารย์และนักวิจัย'
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
facs = db.query(FacultyDB).filter(FacultyDB.faculty_th == "คณาจารย์และนักวิจัย").all()
print(f"Total faculties with faculty_th == 'คณาจารย์และนักวิจัย': {len(facs)}")
for f in facs:
    print(f"{f.id} | {f.full_name_th} | Uni: {f.university_th} | Dept: {f.department_th} | URL: {f.profile_url}")
db.close()
