# -*- coding: utf-8 -*-
"""
Inspect Pass 2 (English Name + University) and Pass 3 (Email) duplicate candidates
after Pass 1 deduplication has been completed.
"""
import os
import sys
import re
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b)\s*",
    re.IGNORECASE
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
print(f"Total faculty records in DB: {len(faculties)}")

# Pass 2: Clean English Name + Univ
pass2_groups = defaultdict(list)
for f in faculties:
    first_en = RE_EN_PREFIX.sub("", (f.first_name or "").strip()).strip()
    last_en = (f.last_name or "").strip()
    if first_en and last_en and len(first_en) > 1 and len(last_en) > 1:
        # Ignore initials like 'J.' or single letters
        if len(first_en.replace(".", "")) >= 2 and len(last_en.replace(".", "")) >= 2:
            clean_en = f"{first_en} {last_en}".lower()
            clean_en = re.sub(r"\s+", " ", clean_en)
            pass2_groups[(f.university_th, clean_en)].append(f)

p2_dups = {k: v for k, v in pass2_groups.items() if len(v) > 1}
print(f"Pass 2 (Clean English Name + Univ) clusters: {len(p2_dups)} (total records: {sum(len(v) for v in p2_dups.values())})")

# Pass 3: Verified Non-Shared Personal Academic Email
pass3_groups = defaultdict(list)
for f in faculties:
    if f.email and "@" in f.email:
        clean_email = f.email.strip().lower()
        user = clean_email.split("@")[0]
        # Exclude common departmental or shared inboxes
        if user not in {"info", "admin", "contact", "office", "dean", "sci", "dent", "med", "eng", "academic", "graduate", "service"}:
            pass3_groups[clean_email].append(f)

p3_dups = {k: v for k, v in pass3_groups.items() if len(v) > 1}
print(f"Pass 3 (Verified Academic Email) clusters: {len(p3_dups)} (total records: {sum(len(v) for v in p3_dups.values())})")

# Sample Pass 2 clusters
print("\n--- Sample Pass 2 (English Name + Univ) Clusters ---")
for (univ, name_en), cluster in list(p2_dups.items())[:10]:
    print(f"\nUniv: {univ} | EN: '{name_en}' ({len(cluster)} records)")
    for f in cluster:
        print(f"  - {f.id} | {f.academic_title_th} | TH: '{f.full_name_th}' | email: {f.email} | openalex: {f.openalex_id} | cites: {f.total_citations}")

# Sample Pass 3 clusters
print("\n--- Sample Pass 3 (Verified Academic Email) Clusters ---")
for email, cluster in list(p3_dups.items())[:10]:
    print(f"\nEmail: {email} ({len(cluster)} records)")
    for f in cluster:
        print(f"  - {f.id} | {f.university_th} | TH: '{f.full_name_th}' | EN: '{f.first_name} {f.last_name}' | openalex: {f.openalex_id} | cites: {f.total_citations}")

db.close()
