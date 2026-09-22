# -*- coding: utf-8 -*-
"""
Inspect corrupt_pubs_or_interests entries.
"""
import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

db = SessionLocal()
sample_ids = [
    'swu_w44_0231_633', 'swu_w44_0281_183', 'swu_w44_0320_180',
    'buu_w42_0001_451', 'swu_w44_0543_875'
]

for fid in sample_ids:
    f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
    if f:
        print(f"\nID: {f.id} | {f.full_name_th}")
        print(f"featured_publications: {json.dumps(f.featured_publications, ensure_ascii=False, indent=2)}")

db.close()
