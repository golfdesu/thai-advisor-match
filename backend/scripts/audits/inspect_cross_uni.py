# -*- coding: utf-8 -*-
"""
Inspect all cross-university duplicate groups.
"""
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
faculties = db.query(FacultyDB).all()
th_name_all = {}
for f in faculties:
    th = f.full_name_th or ""
    th_clean = re.sub(r"^(ศ|รศ|ผศ|อ|ดร|นพ|พญ|ทพ|ทพญ|สพ|ภก|ภญ|\.|\s)+", "", th).strip()
    th_clean = re.sub(r"\s+", "", th_clean)
    if len(th_clean) >= 6:
        th_name_all.setdefault(th_clean, []).append(f)

cross_uni = {k: v for k, v in th_name_all.items() if len(set(f.university_th for f in v)) > 1}

print(f"Total cross-university groups: {len(cross_uni)}\n")

mover_or_dup = []
for k, flist in cross_uni.items():
    en_names = set(f"{f.first_name or ''} {f.last_name or ''}".strip().lower() for f in flist if f.first_name or f.last_name)
    openalexes = set(f.openalex_id for f in flist if f.openalex_id and f.openalex_id != "not_indexed")
    # check if same person or homonym
    # if English name matches or OpenAlex matches or exact Thai name with rare surname
    print(f"=== {k} (Records: {len(flist)}, EN: {en_names}, OpenAlex: {openalexes}) ===")
    for f in flist:
        print(f"   [{f.university_th}] {f.id} | {f.full_name_th} | {f.first_name} {f.last_name} | {f.faculty_th} | {f.department_th} | {f.email} | OpenAlex: {f.openalex_id}")
    print()

db.close()
