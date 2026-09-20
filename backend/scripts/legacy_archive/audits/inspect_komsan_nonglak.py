# -*- coding: utf-8 -*-
"""
Deep inspection of Komsan Suriya and Nonglak Methakanjanasak.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
print("=== Komsan Suriya ===")
for f in db.query(FacultyDB).filter(FacultyDB.full_name_th.like("%คมสัน สุริยะ%")).all():
    print(f"{f.id} | {f.full_name_th} | {f.first_name} {f.last_name} | {f.university_th} | {f.faculty_th} | {f.department_th} | {f.email} | openalex: {f.openalex_id} | pubs: {f.total_publications_count} | cites: {f.total_citations}")
    if f.featured_publications:
        print("  Pub sample:", [p.get("title", p) if isinstance(p, dict) else str(p) for p in f.featured_publications[:3]])

print("\n=== Nonglak Methakanjanasak ===")
for f in db.query(FacultyDB).filter(FacultyDB.full_name_th.like("%นงลักษณ์ เมธากาญจนศักดิ์%")).all():
    print(f"{f.id} | {f.full_name_th} | {f.first_name} {f.last_name} | {f.university_th} | {f.faculty_th} | {f.department_th} | {f.email} | openalex: {f.openalex_id} | pubs: {f.total_publications_count} | cites: {f.total_citations}")
    if f.featured_publications:
        print("  Pub sample:", [p.get("title", p) if isinstance(p, dict) else str(p) for p in f.featured_publications[:3]])

db.close()
