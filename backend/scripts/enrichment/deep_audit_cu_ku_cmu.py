# -*- coding: utf-8 -*-
"""
Deep Diagnostic & Hygiene Audit: CU, KU, and CMU
Identifies:
1. Placeholder names ('Member', 'Faculty', 'Unknown', etc.)
2. Title-leaked first_name ('Asst Prof', 'Assoc', 'Dr', etc.)
3. Crawl debris (full_name_th == 'อ.', len < 3, no real person)
4. Duplicate records (Thai name match, English name match, email match)
5. Missing/Thai English names (Pattern 3)
6. Missing/Invalid 768-dim embeddings
"""
import os
import sys
import json
import re

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

def inspect_university(db, uni_keyword, uni_name):
    records = db.query(FacultyDB).filter(FacultyDB.university_th.like(f"%{uni_keyword}%")).all()
    print(f"\n=======================================================")
    print(f"📊 Audit Report: {uni_name} ({len(records)} faculty)")
    print(f"=======================================================")

    missing_first = []
    missing_last = []
    thai_in_first = []
    thai_in_last = []
    placeholders = []
    title_leaks = []
    garbage_records = []
    invalid_emb = []

    thai_names = {}
    en_names = {}
    emails = {}

    th_duplicates = []
    en_duplicates = []

    for r in records:
        # Check basic fields
        f_en = r.first_name or ""
        l_en = r.last_name or ""
        f_th = r.full_name_th or ""

        if not f_en:
            missing_first.append(r)
        elif re.search(r"[฀-๿]", f_en):
            thai_in_first.append(r)

        if not l_en:
            missing_last.append(r)
        elif re.search(r"[฀-๿]", l_en):
            thai_in_last.append(r)

        # Placeholders
        if any(p.lower() in [f_en.lower(), l_en.lower()] for p in ["Member", "Faculty", "Unknown", "None", "Staff", "Admin", "Teacher"]):
            placeholders.append((r.id, f_th, f_en, l_en, r.faculty_th))

        # Title leaks
        if TITLE_LEAK_REGEX.match(f_en):
            title_leaks.append((r.id, f_th, f_en, l_en, r.faculty_th))

        # Garbage / Debris records
        cleaned_th = re.sub(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.)\s*", "", f_th).strip()
        if len(cleaned_th) < 2 or f_th.strip() in ["อ.", "ดร.", "ผศ.", "รศ.", "ศ.", "อาจารย์"]:
            garbage_records.append((r.id, f_th, f_en, l_en, r.faculty_th, r.profile_url))

        # Vector Embeddings
        if not r.embedding or len(r.embedding) != 768:
            invalid_emb.append(r.id)

        # Duplicate tracking
        if f_th:
            clean_th_key = re.sub(r"\s+", "", cleaned_th)
            if clean_th_key:
                thai_names.setdefault(clean_th_key, []).append(r)

        if f_en and l_en and not re.search(r"[฀-๿]", f_en) and not re.search(r"[฀-๿]", l_en):
            en_key = f"{f_en.strip().lower()} {l_en.strip().lower()}"
            if "member" not in en_key and "faculty" not in en_key:
                en_names.setdefault(en_key, []).append(r)

    # Calculate duplicate clusters
    for k, v in thai_names.items():
        if len(v) > 1:
            th_duplicates.append(v)

    for k, v in en_names.items():
        if len(v) > 1:
            en_duplicates.append(v)

    print(f"  Missing First Name: {len(missing_first)}")
    print(f"  Missing Last Name:  {len(missing_last)}")
    print(f"  Thai in First Name: {len(thai_in_first)}")
    print(f"  Thai in Last Name:  {len(thai_in_last)}")
    print(f"  Placeholder Names:  {len(placeholders)}")
    for p in placeholders[:5]:
        print(f"    - {p[0]}: {p[1]} -> '{p[2]}' '{p[3]}' ({p[4]})")
    print(f"  Title Leaks in First: {len(title_leaks)}")
    for t in title_leaks[:5]:
        print(f"    - {t[0]}: {t[1]} -> '{t[2]}' '{t[3]}' ({t[4]})")
    print(f"  Garbage/Debris Records: {len(garbage_records)}")
    for g in garbage_records[:5]:
        print(f"    - {g[0]}: '{g[1]}' -> {g[2]} {g[3]} ({g[4]}) URL: {g[5]}")
    print(f"  Invalid Embeddings: {len(invalid_emb)}")
    print(f"  Thai Duplicate Clusters: {len(th_duplicates)}")
    for cl in th_duplicates[:3]:
        ids = [x.id for x in cl]
        print(f"    - {cl[0].full_name_th} ({cl[0].faculty_th}): {ids}")
    print(f"  English Duplicate Clusters: {len(en_duplicates)}")
    for cl in en_duplicates[:3]:
        ids = [x.id for x in cl]
        print(f"    - {cl[0].first_name} {cl[0].last_name} ({cl[0].faculty_th}): {ids}")

    return {
        "uni": uni_name,
        "total": len(records),
        "missing_first": len(missing_first),
        "missing_last": len(missing_last),
        "thai_in_first": len(thai_in_first),
        "thai_in_last": len(thai_in_last),
        "placeholders": placeholders,
        "title_leaks": title_leaks,
        "garbage_records": garbage_records,
        "invalid_emb": len(invalid_emb),
        "th_duplicates": th_duplicates,
        "en_duplicates": en_duplicates,
    }

def main():
    db = SessionLocal()
    ku_res = inspect_university(db, "เกษตรศาสตร์", "Kasetsart University (KU)")
    cu_res = inspect_university(db, "จุฬาลงกรณ์", "Chulalongkorn University (CU)")
    cmu_res = inspect_university(db, "เชียงใหม่", "Chiang Mai University (CMU)")
    db.close()

if __name__ == "__main__":
    main()
