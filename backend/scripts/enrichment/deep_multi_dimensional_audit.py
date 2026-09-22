# -*- coding: utf-8 -*-
"""
Deep Multi-Dimensional Quality Audit across 9 Dimensions:
1. English Name Hygiene (first_name, last_name)
2. Academic Title Hygiene (academic_title_th vs full_name_th)
3. Email Syntax & Validity
4. Institutional Integrity (university_th, university)
5. Faculty & Department Hygiene
6. Bibliometric Consistency (total_citations, h_index, total_publications_count)
7. Publication & Interest Quality (PDPA phone leaks, invalid structures)
8. OpenAlex Integrity (intra-university duplicates of valid OpenAlex IDs)
9. Referential Integrity (research_labs foreign keys)
"""
import os
import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from sqlalchemy.orm import defer

RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{3,4}\b")
RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b|อ\.|ผศ\.|รศ\.|ศ\.)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

issues = {
    "en_name_prefixes": [],
    "title_anomalies": [],
    "invalid_emails": [],
    "phone_leaks": [],
    "missing_university": [],
    "placeholder_departments": [],
    "negative_metrics": [],
    "corrupt_pubs_or_interests": [],
    "intra_univ_oa_dups": [],
}

oa_seen = {} # (univ, oa_id) -> fac_id

total = 0
for f in faculties:
    total += 1

    # 1. EN name prefixes
    first = (f.first_name or "").strip()
    if first and RE_EN_PREFIX.match(first):
        issues["en_name_prefixes"].append((f.id, f.first_name, f.last_name))

    # 2. Title anomalies
    title = (f.academic_title_th or "").strip()
    if title:
        if any(c.isdigit() for c in title) or title in ["นาย", "นาง", "นางสาว"] or "None" in title:
            issues["title_anomalies"].append((f.id, title, f.full_name_th))

    # 3. Email syntax
    if f.email:
        em = f.email.strip()
        if not RE_EMAIL.match(em):
            issues["invalid_emails"].append((f.id, em))

    # 4. Phone leaks in interests, bio, or name (PDPA compliance)
    all_text = f"{f.full_name_th} {' '.join(f.research_interests or [])} {' '.join(f.education or [])}"
    if RE_PHONE.search(all_text):
        issues["phone_leaks"].append((f.id, RE_PHONE.search(all_text).group(0)))

    # 5. Missing university
    if not f.university_th or not f.university_th.strip():
        issues["missing_university"].append(f.id)

    # 6. Placeholder departments like "None", "undefined"
    if f.department_th in ["None", "undefined", "null"]:
        issues["placeholder_departments"].append((f.id, f.department_th))

    # 7. Negative metrics
    if (f.total_citations or 0) < 0 or (f.h_index or 0) < 0 or (f.total_publications_count or 0) < 0:
        issues["negative_metrics"].append((f.id, f.total_citations, f.h_index, f.total_publications_count))

    # 8. Corrupt publications/interests
    if f.featured_publications:
        for p in f.featured_publications:
            if not isinstance(p, dict) or not p.get("title"):
                issues["corrupt_pubs_or_interests"].append((f.id, "invalid_pub_entry"))
                break

    # 9. Intra-university duplicate OpenAlex IDs
    if f.openalex_id and f.openalex_id != "not_indexed" and f.openalex_id.strip():
        clean_oa = f.openalex_id.replace("https://openalex.org/", "").strip()
        key = (f.university_th, clean_oa)
        if key in oa_seen:
            issues["intra_univ_oa_dups"].append((f.id, oa_seen[key], f.university_th, clean_oa, f.full_name_th))
        else:
            oa_seen[key] = f.id

# 10. Referential integrity for research labs
lab_orphans = db.query(ResearchLabDB).filter(
    ResearchLabDB.lead_advisor_id.isnot(None)
).all()
valid_fac_ids = {f.id for f in db.query(FacultyDB.id).all()}
orphaned_labs = [l.id for l in lab_orphans if l.lead_advisor_id not in valid_fac_ids]

print(f"==================================================")
print(f"DEEP MULTI-DIMENSIONAL AUDIT REPORT (Total: {total})")
print(f"==================================================")
for k, v in issues.items():
    print(f"{k}: {len(v)}")
print(f"orphaned_labs: {len(orphaned_labs)}")

for k, v in issues.items():
    if v:
        print(f"\n--- Sample {k} (first 10) ---")
        for item in v[:10]:
            print(f"  {item}")

if orphaned_labs:
    print(f"\nOrphaned labs: {orphaned_labs}")

db.close()
