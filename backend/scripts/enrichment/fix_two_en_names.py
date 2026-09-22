# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.abspath('backend'))
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text

db = SessionLocal()
fixes = {
    "mju_w54_1549_753": "Doungporn",
    "mju_w54_1551_449": "Jongkon"
}
for fid, new_first in fixes.items():
    f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
    if f:
        f.first_name = new_first
        f.embedding_text = build_faculty_embedding_text(f)

db.commit()
print("Fixed remaining 2 English names.")
db.close()
