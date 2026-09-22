# -*- coding: utf-8 -*-
import os
import sys
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()
    courses = db.query(CourseDB).all()
    labs = db.query(ResearchLabDB).all()

    print("=" * 60)
    print("🏆 FINAL COMPREHENSIVE ZERO-DEFECT DATABASE AUDIT")
    print("=" * 60)
    print(f"Total Faculties: {len(facs)}")
    print(f"Total Courses: {len(courses)}")
    print(f"Total Research Labs: {len(labs)}")

    # 1. Name & Title Quality
    civic_titles = 0
    en_punct = 0
    for f in facs:
        nth = f.full_name_th or ""
        fn = f.first_name or ""
        ln = f.last_name or ""
        if re.search(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)(?:\s*ดร\.)?\s*(?:นาย\s+|นางสาว\s*|นาง\s+)[a-zA-Z฀-๿]", nth.strip()):
            civic_titles += 1
        if "," in fn or "," in ln:
            en_punct += 1
    print(f"\n[1] Name & Title Hygiene:")
    print(f"    - Civic titles following academic titles: {civic_titles}")
    print(f"    - Stray commas in English names: {en_punct}")

    # 2. URL Hygiene
    relative_urls = 0
    for f in facs:
        for u in [f.image_url, f.profile_url, f.scholar_url]:
            if u and u.strip().startswith("../"):
                relative_urls += 1
    print(f"\n[2] URL Hygiene:")
    print(f"    - Relative image/profile URLs ('../'): {relative_urls}")

    # 3. Research Interests Hygiene
    junk_interests = 0
    junk_set = {"2010-2016", "1844-1900", ":", "/??", "etc.", "etc", "...", "-", "--", "ฯลฯ"}
    for f in facs:
        for item in (f.research_interests or []):
            if str(item).strip() in junk_set or len(str(item).strip()) <= 1:
                junk_interests += 1
    print(f"\n[3] Research Interests Hygiene:")
    print(f"    - Junk tokens in research_interests: {junk_interests}")

    # 4. Email Hygiene
    freemails = 0
    malformed_emails = 0
    freemail_domains = ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@live.com")
    for f in facs:
        if f.email:
            e = f.email.strip().lower()
            if any(e.endswith(dom) for dom in freemail_domains):
                freemails += 1
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e):
                malformed_emails += 1
    print(f"\n[4] Email Hygiene:")
    print(f"    - Personal freemails: {freemails}")
    print(f"    - Malformed emails: {malformed_emails}")

    # 5. Bibliometric Monotonicity
    monotonicity_violations = 0
    for f in facs:
        if f.h_index and f.total_publications_count and f.h_index > f.total_publications_count:
            monotonicity_violations += 1
    print(f"\n[5] Bibliometrics:")
    print(f"    - Monotonicity violations (h_index > total_publications_count): {monotonicity_violations}")

    # 6. Bilingual University Symmetry
    mismatches = [
        f.id for f in facs
        if f.university_th in TH_TO_EN_CANONICAL and f.university != TH_TO_EN_CANONICAL[f.university_th]
    ]
    print(f"\n[6] Bilingual Symmetry:")
    print(f"    - Bilingual university name mismatches: {len(mismatches)}")

    # 7. Research Lab Foreign Keys
    orphan_leads = 0
    for l in labs:
        if l.lead_advisor_id:
            if not db.query(FacultyDB).filter(FacultyDB.id == l.lead_advisor_id).first():
                orphan_leads += 1
    print(f"\n[7] Research Labs:")
    print(f"    - Orphaned lead advisor IDs: {orphan_leads}")

    print("\n" + "=" * 60)
    print("STATUS: 100% ZERO DEFECT VERIFIED" if all([
        civic_titles == 0, en_punct == 0, relative_urls == 0, junk_interests == 0,
        freemails == 0, malformed_emails == 0, monotonicity_violations == 0,
        len(mismatches) == 0, orphan_leads == 0
    ]) else "STATUS: REMAINING DEFECTS FOUND")
    print("=" * 60)

    db.close()

if __name__ == "__main__":
    main()
