# -*- coding: utf-8 -*-
"""
Scan for boilerplate strings, spambot notices, web artifacts, and HTML leaks across all fields.
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

BOILERPLATE_PATTERNS = [
    re.compile(r"spambot|protected from spambot|javascript enabled", re.IGNORECASE),
    re.compile(r"click here|read more|contact us|about us|home page", re.IGNORECASE),
    re.compile(r"privacy policy|terms of use|all rights reserved|copyright", re.IGNORECASE),
    re.compile(r"untitled|page not found|404 not found|error 404", re.IGNORECASE),
    re.compile(r"lorem ipsum|sample text|test user|placeholder", re.IGNORECASE),
    re.compile(r"faculty of|department of|university|staff list|personnel", re.IGNORECASE), # when in person names
]

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
print(f"Loaded {len(faculties)} faculty records.")

def check_boilerplate(text):
    if not text: return None
    for p in BOILERPLATE_PATTERNS[:5]:
        if p.search(text):
            return p.pattern
    return None

findings = []
for f in faculties:
    # Check first_name / last_name
    fn_b = check_boilerplate(f.first_name)
    ln_b = check_boilerplate(f.last_name)
    th_b = check_boilerplate(f.full_name_th)
    em_b = check_boilerplate(f.email)

    if fn_b or ln_b or th_b or em_b:
        findings.append({
            "id": f.id,
            "full_name_th": f.full_name_th,
            "first_name": f.first_name,
            "last_name": f.last_name,
            "email": f.email,
            "match": fn_b or ln_b or th_b or em_b
        })

print(f"Found {len(findings)} records with boilerplate artifacts.")
for f in findings[:25]:
    print(f"  - {f['id']} | TH: '{f['full_name_th']}' | EN: '{f['first_name']} {f['last_name']}' | Email: '{f['email']}' | Match: {f['match']}")

db.close()
