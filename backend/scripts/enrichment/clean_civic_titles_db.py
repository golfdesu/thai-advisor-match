# -*- coding: utf-8 -*-
"""
Database-Wide Civic Title Normalization:
Removes redundant civic titles (นาย, นาง, นางสาว) that appear immediately after
an academic title (อ., ผศ., รศ., ศ., อ.ดร., ผศ.ดร., รศ.ดร., ศ.ดร.)
e.g. 'อ. นาย วิเชษฐ์ จันทร์คงหอม' -> 'อ. วิเชษฐ์ จันทร์คงหอม'
"""
import os
import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from sqlalchemy.orm import defer

RE_CIVIC = re.compile(
    r"^(อ\.|ผศ\.|รศ\.|ศ\.|อ\.ดร\.|ผศ\.ดร\.|รศ\.ดร\.|ศ\.ดร\.|ดร\.)\s+(?:นาย|นางสาว|นาง)\s+(.*)"
)

def clean_civic_titles():
    db = SessionLocal()
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

    updated = 0
    batch_size = 500

    for f in faculties:
        name = (f.full_name_th or "").strip()
        m = RE_CIVIC.match(name)
        if m:
            academic_title = m.group(1)
            rest_name = m.group(2).strip()
            f.full_name_th = f"{academic_title} {rest_name}"
            if not f.academic_title_th:
                f.academic_title_th = academic_title
            f.embedding_text = build_faculty_embedding_text(f)
            updated += 1

    db.commit()
    print(f"Normalized {updated} records with redundant civic titles.")
    db.close()

if __name__ == "__main__":
    clean_civic_titles()
