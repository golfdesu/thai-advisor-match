# -*- coding: utf-8 -*-
"""
Scan first_name and last_name for common boilerplate, navigation labels, and UI headers.
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

LEAK_PATTERNS = [
    re.compile(r"\b(redacted|phone|email|telephone|tel|fax|mobile)\b", re.IGNORECASE),
    re.compile(r"\b(grant|grants|award|awards|patent|patents|publication|publications)\b", re.IGNORECASE),
    re.compile(r"\b(textbook|textbooks|copyright|copyrights|all rights reserved)\b", re.IGNORECASE),
    re.compile(r"\b(education|biography|curriculum|vitae|resume|profile|contact)\b", re.IGNORECASE),
    re.compile(r"\b(academic|service|research|project|laboratory|course|courses)\b", re.IGNORECASE),
    re.compile(r"\b(department|faculty|university|school|institute|center|college)\b", re.IGNORECASE),
    re.compile(r"\b(room|building|floor|campus|address|website|homepage)\b", re.IGNORECASE),
    re.compile(r"\b(select|option|dropdown|search|submit|button|click)\b", re.IGNORECASE),
]

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

leaks = []
for f in faculties:
    first = (f.first_name or "").strip()
    last = (f.last_name or "").strip()
    full_en = f"{first} {last}".strip()

    # Check if first or last matches leak patterns
    matched_pattern = None
    for p in LEAK_PATTERNS:
        if p.search(first) or p.search(last):
            matched_pattern = p.pattern
            break

    if matched_pattern:
        leaks.append((f, matched_pattern, full_en))

print(f"Total records with potential English header/sidebar leaks: {len(leaks)}")
for f, pat, full_en in leaks[:35]:
    print(f"  - {f.id} | TH: '{f.full_name_th}' | EN: '{full_en}' | dept: '{f.department_th}' | match: '{pat}'")

db.close()
