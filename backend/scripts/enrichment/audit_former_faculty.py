# -*- coding: utf-8 -*-
"""
Diagnostic: Audit for Former, Retired, Deceased, and Resigned Faculty in Database
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

KEYWORDS_TH = [
    "เกษียณ", "อดีต", "ถึงแก่กรรม", "เสียชีวิต", "ลาออก", "บำนาญ", "มรณภาพ",
    "พ้นสภาพ", "หมดวาระ", "ลาศึกษาต่อ"
]

KEYWORDS_EN = [
    "retired", "emeritus", "former", "deceased", "resigned", "passed away", "ex-faculty"
]

def audit_former_faculty():
    db = SessionLocal()
    faculties = db.query(FacultyDB).all()
    print(f"Total faculty in database: {len(faculties)}")

    hits = []

    for r in faculties:
        fields = {
            "full_name_th": r.full_name_th or "",
            "academic_title_th": r.academic_title_th or "",
            "faculty_th": r.faculty_th or "",
            "department_th": r.department_th or "",
            "first_name": r.first_name or "",
            "last_name": r.last_name or "",
        }

        # Check research interests and education if available
        interests = " ".join(r.research_interests or [])
        education = " ".join(r.education or [])

        matched = []
        for kw in KEYWORDS_TH:
            for fname, val in fields.items():
                if kw in val:
                    matched.append((kw, fname, val))
            if kw in interests:
                matched.append((kw, "research_interests", interests[:50]))
            if kw in education:
                matched.append((kw, "education", education[:50]))

        for kw in KEYWORDS_EN:
            for fname, val in fields.items():
                if kw.lower() in val.lower():
                    matched.append((kw, fname, val))
            if kw.lower() in interests.lower():
                matched.append((kw, "research_interests", interests[:50]))

        if matched:
            hits.append((r.id, r.university_th, r.faculty_th, r.full_name_th, r.first_name, r.last_name, matched))

    print(f"Total records with potential former/retired/deceased markers: {len(hits)}")
    by_kw = {}
    for h in hits:
        kws = set(m[0] for m in h[6])
        for k in kws:
            by_kw.setdefault(k, []).append(h)

    for k, recs in by_kw.items():
        print(f"\nKeyword '{k}' ({len(recs)} records):")
        for h in recs[:8]:
            matches_str = "; ".join([f"{m[1]}='{m[2]}'" for m in h[6]])
            print(f"  [{h[0]}] {h[1]} | {h[2]} | {h[3]} ({h[4]} {h[5]}) -> {matches_str}")

    db.close()

if __name__ == "__main__":
    audit_former_faculty()
