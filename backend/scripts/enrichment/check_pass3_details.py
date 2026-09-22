# -*- coding: utf-8 -*-
"""
Inspect Pass 3 email clusters to check if any are cross-university or generic.
"""
import os
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

GENERIC_USERS = {
    "info", "admin", "contact", "office", "dean", "sci", "dent", "med", "eng",
    "academic", "graduate", "service", "pr", "help", "hr", "reg", "library",
    "support", "webmaster", "postmaster", "director", "rector", "secretary"
}

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

email_groups = defaultdict(list)
for f in faculties:
    if f.email and "@" in f.email:
        em = f.email.strip().lower()
        u = em.split("@")[0]
        if u not in GENERIC_USERS and len(u) >= 3:
            email_groups[em].append(f)

dup_emails = {k: v for k, v in email_groups.items() if len(v) > 1}
print(f"Total duplicate email clusters: {len(dup_emails)}")

cross_univ_count = 0
same_univ_count = 0

for em, cluster in dup_emails.items():
    univs = {f.university_th for f in cluster}
    if len(univs) > 1:
        cross_univ_count += 1
        print(f"\n[CROSS-UNIV] Email: {em} across: {univs}")
        for f in cluster:
            print(f"   {f.id} | {f.university_th} | TH: {f.full_name_th} | EN: {f.first_name} {f.last_name}")
    else:
        same_univ_count += 1

print(f"\nSummary: {same_univ_count} same-university email clusters, {cross_univ_count} cross-university clusters.")
db.close()
