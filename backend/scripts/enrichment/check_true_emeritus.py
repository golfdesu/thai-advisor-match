# -*- coding: utf-8 -*-
"""
Deep inspection of Emeritus, Retired, and Former faculty across the entire DB
"""
import os
import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def main():
    db = SessionLocal()
    faculties = db.query(FacultyDB).all()

    true_emeritus = []

    for r in faculties:
        th = r.full_name_th or ""
        title = r.academic_title_th or ""

        # Check if title has เกียรติคุณ as title, not surname or firstname
        is_emeritus = False
        if "ศ.เกียรติคุณ" in th or "ศ. เกียรติคุณ" in th or "ศาสตราจารย์เกียรติคุณ" in th:
            is_emeritus = True
        elif title in ["ศ.เกียรติคุณ", "ศาสตราจารย์เกียรติคุณ"]:
            is_emeritus = True
        elif "professor emeritus" in (r.last_name or "").lower() or "professor emeritus" in (r.first_name or "").lower():
            is_emeritus = True

        if is_emeritus:
            true_emeritus.append(r)

    print(f"Total verified Emeritus (ศาสตราจารย์เกียรติคุณ) in database: {len(true_emeritus)}")
    for r in true_emeritus:
        print(f"  [{r.id}] {r.university_th} | {r.faculty_th} | {r.academic_title_th} | th='{r.full_name_th}' | en='{r.first_name} {r.last_name}' | email='{r.email}'")

    db.close()

if __name__ == "__main__":
    main()
