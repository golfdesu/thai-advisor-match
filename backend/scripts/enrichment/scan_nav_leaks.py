# -*- coding: utf-8 -*-
"""
Scan full_name_th for English navigation words, UI labels, and website breadcrumbs.
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

NAV_PATTERNS = [
    re.compile(r"\b(home|menu|contact|about|search|login|logout|register|sitemap|feedback)\b", re.IGNORECASE),
    re.compile(r"\b(download|upload|gallery|news|event|calendar|faq|privacy|terms)\b", re.IGNORECASE),
    re.compile(r"\b(faculty|department|division|office|center|institute|campus|building|room)\b", re.IGNORECASE),
    re.compile(r"\b(curriculum|course|syllabus|program|degree|bachelor|master|doctorate)\b", re.IGNORECASE),
    re.compile(r"\b(staff|personnel|officer|admin|administrator|webmaster|advisor)\b", re.IGNORECASE),
    re.compile(r"\b(publication|research|laboratory|project|thesis|dissertation)\b", re.IGNORECASE),
]

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

nav_findings = []
for f in faculties:
    name_th = (f.full_name_th or "").strip()
    for p in NAV_PATTERNS:
        m = p.search(name_th)
        if m:
            nav_findings.append((f, m.group(0)))
            break

print(f"Total potential navigation/label leaks in full_name_th: {len(nav_findings)}")
for f, match in nav_findings:
    print(f"  - {f.id} | TH: '{f.full_name_th}' | EN: '{f.first_name} {f.last_name}' | email: '{f.email}' | cites: {f.total_citations} | Match: '{match}'")

db.close()
