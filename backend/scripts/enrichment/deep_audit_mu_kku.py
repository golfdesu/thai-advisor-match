# -*- coding: utf-8 -*-
"""
SKILL.state Audit: Comprehensive 10-Dimensional Quality Audit for MU & KKU
Audits:
1. Missing English first name
2. Missing English last name
3. Thai characters in English first name
4. Thai characters in English last name
5. Placeholders (REDACTED, Member, Faculty, etc.)
6. Leaked academic titles in first_name (Prof, Assoc Prof, Asst Prof, Dr, Miss, etc.)
7. Garbage / Debris crawl records (solitary titles, empty names)
8. Invalid or missing 768-dim vector embeddings
9. Thai duplicate clusters
10. English duplicate clusters
"""
import os
import sys
import re
import json
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

TITLE_LEAK_REGEX = re.compile(
    r"^(?:Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Dr\.?|Lect\.?|Mr\.?|Ms\.?|Mrs\.?|Assoc|Asst|Prof)\s+",
    re.IGNORECASE
)

PLACEHOLDER_NAMES = {"redacted", "member", "faculty", "unknown", "staff", "none", "null", "undefined", "n/a"}

def audit_university(db, univ_name):
    print(f"\n=======================================================")
    print(f"📊 Auditing {univ_name}")
    print(f"=======================================================")

    faculties = db.query(FacultyDB).filter(FacultyDB.university_th == univ_name).all()
    total = len(faculties)
    print(f"Total faculty members: {total}")

    if total == 0:
        print("No records found!")
        return {}

    missing_first = []
    missing_last = []
    thai_in_first = []
    thai_in_last = []
    placeholders = []
    title_leaks = []
    garbage_records = []
    invalid_emb = []

    th_clusters = defaultdict(list)
    en_clusters = defaultdict(list)
    email_clusters = defaultdict(list)

    for f in faculties:
        fid = f.id
        fn = (f.first_name or "").strip()
        ln = (f.last_name or "").strip()
        th = (f.full_name_th or "").strip()
        em = (f.email or "").strip().lower()

        # 1. Missing first
        if not fn:
            missing_first.append(f)
        # 2. Missing last
        if not ln:
            missing_last.append(f)
        # 3. Thai in first
        if fn and re.search(r"[฀-๿]", fn):
            thai_in_first.append(f)
        # 4. Thai in last
        if ln and re.search(r"[฀-๿]", ln):
            thai_in_last.append(f)
        # 5. Placeholders
        if fn.lower() in PLACEHOLDER_NAMES or ln.lower() in PLACEHOLDER_NAMES:
            placeholders.append(f)
        # 6. Title leaks
        if fn and TITLE_LEAK_REGEX.match(fn):
            title_leaks.append(f)
        # 7. Garbage / Debris
        if len(th) <= 2 or (th in ['อ.', 'ดร.', 'ผศ.', 'รศ.', 'ศ.'] and not fn):
            garbage_records.append(f)
        # 8. Embedding
        if f.embedding is None:
            invalid_emb.append(f)
        else:
            try:
                emb_len = len(f.embedding)
                if emb_len != 768:
                    invalid_emb.append(f)
            except Exception:
                invalid_emb.append(f)

        # Duplicates
        clean_th = re.sub(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|สพ\.ญ\.|สพ\.บ\.)\s*", "", th).strip()
        if len(clean_th) > 3:
            th_clusters[clean_th].append(f)

        if fn and ln and len(fn) > 1 and len(ln) > 1 and not re.search(r"[฀-๿]", fn) and not re.search(r"[฀-๿]", ln):
            clean_en = f"{fn.lower()} {ln.lower()}"
            en_clusters[clean_en].append(f)

        if em and "@" in em and not any(em.startswith(p) for p in ["info@", "contact@", "admin@", "sci@", "dent@", "med@", "eng@"]):
            email_clusters[em].append(f)

    th_dups = {k: v for k, v in th_clusters.items() if len(v) > 1}
    en_dups = {k: v for k, v in en_clusters.items() if len(v) > 1}
    em_dups = {k: v for k, v in email_clusters.items() if len(v) > 1}

    print(f"1. Missing English First Name: {len(missing_first)}")
    print(f"2. Missing English Last Name: {len(missing_last)}")
    print(f"3. Thai in English First Name: {len(thai_in_first)}")
    print(f"4. Thai in English Last Name: {len(thai_in_last)}")
    print(f"5. Placeholder Names: {len(placeholders)}")
    print(f"6. Leaked Academic Titles in First Name: {len(title_leaks)}")
    print(f"7. Garbage / Debris Records: {len(garbage_records)}")
    print(f"8. Invalid / Missing 768-dim Embeddings: {len(invalid_emb)}")
    print(f"9. Thai Duplicate Clusters: {len(th_dups)}")
    print(f"10. English Duplicate Clusters: {len(en_dups)}")
    print(f"11. Email Duplicate Clusters: {len(em_dups)}")

    return {
        "total": total,
        "missing_first": missing_first,
        "missing_last": missing_last,
        "thai_in_first": thai_in_first,
        "thai_in_last": thai_in_last,
        "placeholders": placeholders,
        "title_leaks": title_leaks,
        "garbage_records": garbage_records,
        "invalid_emb": invalid_emb,
        "th_dups": th_dups,
        "en_dups": en_dups,
        "em_dups": em_dups,
    }

def main():
    db = SessionLocal()
    audit_university(db, "มหาวิทยาลัยมหิดล")
    audit_university(db, "มหาวิทยาลัยขอนแก่น")
    db.close()

if __name__ == "__main__":
    main()
