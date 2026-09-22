# -*- coding: utf-8 -*-
"""
Detailed inspection of Pass 3 (Verified Academic Email) deduplication.
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

def score_faculty(fac, email_domain):
    s = 0
    # Prefer record where university matches email domain
    # e.g. email has tu.ac.th and university is Thammasat
    univ = (fac.university_th or "").lower()
    if "tu.ac.th" in email_domain and "ธรรมศาสตร์" in univ: s += 500
    elif "cmu.ac.th" in email_domain and "เชียงใหม่" in univ: s += 500
    elif "kmitl.ac.th" in email_domain and "ลาดกระบัง" in univ: s += 500
    elif "mfu.ac.th" in email_domain and "แม่ฟ้าหลวง" in univ: s += 500
    elif "ku.ac.th" in email_domain and "เกษตรศาสตร์" in univ: s += 500
    elif "chula.ac.th" in email_domain and "จุฬา" in univ: s += 500
    elif "mahidol.ac.th" in email_domain and "มหิดล" in univ: s += 500
    elif "nu.ac.th" in email_domain and "นเรศวร" in univ: s += 500
    elif "psu.ac.th" in email_domain and "สงขลา" in univ: s += 500

    # Authentic Thai full name
    name_th = fac.full_name_th or ""
    if re.search(r"[฀-๿]", name_th): s += 100

    # Academic title
    if fac.academic_title_th: s += 50

    # Citations and publications
    if fac.total_citations: s += min(fac.total_citations, 50)
    if fac.featured_publications: s += len(fac.featured_publications) * 2
    if fac.openalex_id and fac.openalex_id != "not_indexed": s += 50
    if fac.image_url: s += 20
    if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 10
    return s

donor_count = 0
for em, cluster in dup_emails.items():
    domain = em.split("@")[-1]
    sorted_cluster = sorted(cluster, key=lambda f: score_faculty(f, domain), reverse=True)
    primary = sorted_cluster[0]
    donors = sorted_cluster[1:]
    donor_count += len(donors)

print(f"Total donor records to merge via Pass 3: {donor_count}")
db.close()
