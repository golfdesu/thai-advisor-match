# -*- coding: utf-8 -*-
"""
Inspect psu_agro_nonglak_001
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
f = db.query(FacultyDB).filter(FacultyDB.id == "psu_agro_nonglak_001").first()
if f:
    print(f"ID: {f.id}")
    print(f"full_name_th: {f.full_name_th}")
    print(f"first_name: {f.first_name}")
    print(f"last_name: {f.last_name}")
    print(f"email: {f.email}")
    print(f"profile_url: {f.profile_url}")
    print(f"education: {f.education}")
    print(f"research_interests: {f.research_interests}")
db.close()
