# -*- coding: utf-8 -*-
"""
Scan full_name_th for Thai navigation words, breadcrumbs, UI labels, and organizational markers.
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

THAI_NAV_PATTERNS = [
    re.compile(r"(ติดต่อเรา|เกี่ยวกับเรา|หน้าแรก|ดาวน์โหลด|เมนูหลัก|แผนผัง|ข่าวสาร|ประชาสัมพันธ์)"),
    re.compile(r"(คณะวิชา|ภาควิชา|สาขาวิชา|สำนักวิชา|วิทยาลัย|หน่วยงาน|สถาบัน|มหาวิทยาลัย)"),
    re.compile(r"(หลักสูตร|ปริญญาตรี|ปริญญาโท|ปริญญาเอก|แผนการเรียน|ตารางสอน)"),
    re.compile(r"(เบอร์โทร|โทรศัพท์|โทรสาร|อีเมล|สถานที่ติดต่อ|ห้องทำงาน)"),
]

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

findings = []
for f in faculties:
    name_th = (f.full_name_th or "").strip()
    for p in THAI_NAV_PATTERNS:
        m = p.search(name_th)
        if m:
            findings.append((f, m.group(0)))
            break

print(f"Total Thai navigation/label matches in full_name_th: {len(findings)}")
for f, m in findings:
    print(f"  - {f.id} | TH: '{f.full_name_th}' | EN: '{f.first_name} {f.last_name}' | dept: '{f.department_th}' | match: '{m}'")

db.close()
