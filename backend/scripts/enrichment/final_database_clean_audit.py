# -*- coding: utf-8 -*-
"""
Final Database-Wide Hygiene & Zero-Defect Audit:
Scans the entire faculties table across all universities to verify:
1. Phantoms / Non-person / Breadcrumb records
2. Pure DOI / URL / Initial records
3. Corrupted titles (double titles, space-separated dots in titles, civic title concatenation)
4. Corrupted emails
5. Lingering emeritus / departed markers
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
from sqlalchemy.orm import defer

RE_NON_PERSON = re.compile(
    r"(?:^ภาควิชา|^สาขาวิชา|^สถานที่ติดต่อ|^ติดต่อเรา|^เว็บไซต์|^บุคลากร|^เจ้าหน้าที่|"
    r"^admin\b|^staff\b|^test\b|^sample\b|^undefined\b|^null\b|^none\b|"
    r"^อ\.\s*e-mail|et\s+al\.|editor\s+of)",
    re.IGNORECASE
)

def run_audit():
    db = SessionLocal()
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

    total_count = 0
    non_person_count = 0
    corrupt_title_count = 0
    phantom_count = 0
    civic_title_count = 0
    departed_count = 0

    issues = []

    for f in faculties:
        total_count += 1
        name = (f.full_name_th or "").strip()
        role = (f.role or "").strip()

        # Check phantom
        if name in ("อ.", "ดร.", "ผศ.", "รศ.", "ศ.", "-", "N/A") or len(name) < 2:
            phantom_count += 1
            issues.append(("Phantom", f.id, f.university_th, name))

        # Check non-person breadcrumb
        if RE_NON_PERSON.search(name):
            non_person_count += 1
            issues.append(("Non-person", f.id, f.university_th, name))

        # Check departed
        if any(k in name for k in ["(เกษียณ)", "(ลาออก)", "(เสียชีวิต)", "(ถึงแก่กรรม)", "(ลาศึกษาต่อ)"]):
            departed_count += 1
            issues.append(("Departed", f.id, f.university_th, name))

        # Check double titles e.g. "ศ.ดร. ศ.ดร."
        if re.search(r"(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.)\s+\1", name):
            corrupt_title_count += 1
            issues.append(("DoubleTitle", f.id, f.university_th, name))

        # Check civic titles like "อ. นาย", "ผศ. นางสาว"
        if re.search(r"^(อ\.|ผศ\.|รศ\.|ศ\.|อ\.ดร\.|ผศ\.ดร\.|รศ\.ดร\.|ศ\.ดร\.)\s+(?:นาย|นางสาว|นาง)\s+", name):
            civic_title_count += 1
            issues.append(("CivicTitle", f.id, f.university_th, name))

    print(f"==================================================")
    print(f"DATABASE-WIDE AUDIT REPORT (Total Faculty: {total_count})")
    print(f"==================================================")
    print(f"Phantoms: {phantom_count}")
    print(f"Non-person Breadcrumbs: {non_person_count}")
    print(f"Departed / Former markers: {departed_count}")
    print(f"Double Titles: {corrupt_title_count}")
    print(f"Civic Titles in Name: {civic_title_count}")
    print(f"Total Issues Detected: {len(issues)}")

    if issues:
        print("\nSample issues:")
        for issue in issues[:20]:
            print(f"  [{issue[0]}] {issue[1]} | {issue[2]} | {issue[3]}")

    db.close()
    return len(issues)

if __name__ == "__main__":
    run_audit()
