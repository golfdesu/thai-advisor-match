# -*- coding: utf-8 -*-
"""
Advanced Autonomous Zero-Defect Optimization & Unified Deduplication Loop:
1. Clean English name columns:
   - Strips 'Aj.' / 'Ajarn' prefixes from first_name and sets academic_title_th = 'อ.' where missing.
   - Cleans non-Latin scripts (e.g. Chinese characters in brackets like 'Peng (彭坚)' -> 'Peng').
2. Clean empty string columns to NULL:
   - FacultyDB.openalex_id: '' -> NULL (273 records in MFU).
   - CourseDB.website_url: '' -> NULL.
   - CourseDB.department_th: '' -> NULL.
3. Consolidate Kevin D. Hyde records at Mae Fah Luang into a single authoritative record.
4. Execute unified token-set & initial-aware same-university deduplication across 216 clusters:
   - Merges donor metrics: max(total_citations), max(h_index), max(total_publications_count).
   - Unions featured_publications and research_interests.
   - Re-points research_labs.lead_advisor_id.
   - Rebuilds primary embedding_text.
5. Saves snapshot checkpoint to backend/data/agent_states/advanced_zero_defect_loop_snapshot.json.
"""
import os
import sys
import re
import json
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text

THAI_REGEX = re.compile(r'[฀-๿]')
COMMON_SHORT_GIVEN = {'li', 'wei', 'jian', 'hong', 'min', 'yan', 'jun', 'hui', 'lei', 'bin', 'bo', 'chao', 'xin', 'tao', 'jie'}

def get_name_tokens(f):
    fn = (f.first_name or "").lower().strip()
    ln = (f.last_name or "").lower().strip()
    if fn.startswith('aj.') or fn.startswith('ajarn'):
        full = f"{fn} {ln}".strip()
        full_clean = re.sub(r'^(?:Aj\.?|Ajarn)\s*', '', full, flags=re.IGNORECASE).strip()
        parts = full_clean.split()
        if len(parts) >= 2:
            fn, ln = parts[0], " ".join(parts[1:])
    if not fn and not ln and f.full_name_th:
        name_th = f.full_name_th.strip()
        clean = re.sub(r'^(?:ศ\.(?:\(พิเศษ\)|\(เชี่ยวชาญพิเศษ\))?|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.)\s*', '', name_th)
        parts = clean.split()
        if len(parts) >= 2 and not THAI_REGEX.search(clean):
            fn, ln = parts[0].lower(), " ".join(parts[1:]).lower()
    tokens = tuple(re.findall(r'[a-z]+', f"{fn} {ln}"))
    return fn, ln, tokens

def are_same_person(tok1, tok2):
    if len(tok1) < 2 or len(tok2) < 2:
        return False
    # Condition A: exact token set match (e.g. inverted name order)
    if frozenset(tok1) == frozenset(tok2):
        return True

    # Condition B: middle initial / abbreviation match
    if tok1[0] == tok2[0] and tok1[-1] == tok2[-1]:
        first, last = tok1[0], tok1[-1]
        if first in COMMON_SHORT_GIVEN or len(first) <= 2 or len(last) <= 2:
            return False
        mid1, mid2 = tok1[1:-1], tok2[1:-1]
        if len(mid1) == 0 and len(mid2) == 1:
            return True
        if len(mid2) == 0 and len(mid1) == 1:
            return True
        if len(mid1) == 1 and len(mid2) == 1:
            m1, m2 = mid1[0], mid2[0]
            if m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2)):
                return True
        if len(mid1) == len(mid2) and len(mid1) > 1:
            if all(m1 == m2 or (len(m1) == 1 and m2.startswith(m1)) or (len(m2) == 1 and m1.startswith(m2)) for m1, m2 in zip(mid1, mid2)):
                return True

    return False

def score_faculty(fac):
    s = 0
    name_th = fac.full_name_th or ""
    if THAI_REGEX.search(name_th): s += 150
    if fac.academic_title_th: s += 50
    if fac.email and len(fac.email) > 5 and "@" in fac.email: s += 100
    if fac.openalex_id and fac.openalex_id != "not_indexed": s += 80
    if fac.total_citations: s += min(fac.total_citations, 100)
    if fac.featured_publications: s += len(fac.featured_publications) * 2
    if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 20
    if fac.image_url: s += 10
    return s

def main():
    db = SessionLocal()
    print("======================================================================")
    print("🚀 EXECUTING ADVANCED ZERO-DEFECT OPTIMIZATION & UNIFIED DEDUPLICATION")
    print("======================================================================")

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "description": "Advanced Zero-Defect Optimization & Unified Deduplication",
        "empty_strings_cleaned": {},
        "name_cleanups": [],
        "merges": []
    }

    # 1. Clean English name columns
    print("\n--- 1. Cleaning Name Columns ---")
    all_facs = db.query(FacultyDB).all()
    cleaned_names_count = 0
    for f in all_facs:
        changed = False
        fn = f.first_name or ""
        ln = f.last_name or ""
        # Clean 'Aj.' prefix
        if fn.lower().startswith("aj.") or fn.lower().startswith("ajarn"):
            full = f"{fn} {ln}".strip()
            full_clean = re.sub(r'^(?:Aj\.?|Ajarn)\s*', '', full, flags=re.IGNORECASE).strip()
            parts = full_clean.split()
            if len(parts) >= 2:
                f.first_name = parts[0]
                f.last_name = " ".join(parts[1:])
                if not f.academic_title_th:
                    f.academic_title_th = "อ."
                changed = True
        # Clean Chinese characters in brackets (e.g. 'Peng (彭坚)' -> 'Peng')
        if f.last_name and re.search(r'\([^\x00-\x7F]+\)', f.last_name):
            cleaned_ln = re.sub(r'\s*\([^\x00-\x7F]+\)', '', f.last_name).strip()
            f.last_name = cleaned_ln
            changed = True
        if f.first_name and re.search(r'\([^\x00-\x7F]+\)', f.first_name):
            cleaned_fn = re.sub(r'\s*\([^\x00-\x7F]+\)', '', f.first_name).strip()
            f.first_name = cleaned_fn
            changed = True
        if changed:
            f.embedding_text = build_faculty_embedding_text(f)
            cleaned_names_count += 1
            snapshot["name_cleanups"].append({"id": f.id, "fn": f.first_name, "ln": f.last_name, "title": f.academic_title_th})
    print(f"  Cleaned {cleaned_names_count} name fields.")

    # 2. Clean empty strings across database tables
    print("\n--- 2. Cleaning Empty String Columns to NULL ---")
    # FacultyDB.openalex_id
    empty_oa = db.query(FacultyDB).filter(FacultyDB.openalex_id == '').all()
    for f in empty_oa:
        f.openalex_id = None
    snapshot["empty_strings_cleaned"]["faculty_openalex_id"] = len(empty_oa)
    print(f"  Set openalex_id = NULL on {len(empty_oa)} faculty records.")

    # CourseDB empty strings
    empty_course_urls = db.query(CourseDB).filter(CourseDB.website_url == '').all()
    for c in empty_course_urls:
        c.website_url = None
    empty_course_depts = db.query(CourseDB).filter(CourseDB.department_th == '').all()
    for c in empty_course_depts:
        c.department_th = None
    snapshot["empty_strings_cleaned"]["course_website_url"] = len(empty_course_urls)
    snapshot["empty_strings_cleaned"]["course_department_th"] = len(empty_course_depts)
    print(f"  Set website_url = NULL on {len(empty_course_urls)} courses.")
    print(f"  Set department_th = NULL on {len(empty_course_depts)} courses.")

    # 3. Consolidate Kevin D. Hyde at Mae Fah Luang University
    print("\n--- 3. Consolidating Kevin D. Hyde at Mae Fah Luang ---")
    mfu_hyde_records = db.query(FacultyDB).filter(
        FacultyDB.university_th == "มหาวิทยาลัยแม่ฟ้าหลวง",
        FacultyDB.full_name_th.ilike("%hyde%")
    ).all()
    if len(mfu_hyde_records) > 1:
        # Choose primary with highest citations
        primary_hyde = max(mfu_hyde_records, key=lambda f: f.total_citations or 0)
        donor_hydes = [f for f in mfu_hyde_records if f.id != primary_hyde.id]

        primary_hyde.academic_title_th = "ศ.(พิเศษ) ดร."
        primary_hyde.first_name = "Kevin"
        primary_hyde.last_name = "Hyde"
        primary_hyde.full_name_th = "ศ.(พิเศษ) ดร. Kevin D. Hyde"
        primary_hyde.faculty_th = "สำนักวิชาวิทยาศาสตร์"
        primary_hyde.department_th = "Center of Excellence in Fungal Research"

        for d in donor_hydes:
            primary_hyde.total_citations = max(primary_hyde.total_citations or 0, d.total_citations or 0)
            primary_hyde.h_index = max(primary_hyde.h_index or 0, d.h_index or 0)
            primary_hyde.total_publications_count = max(primary_hyde.total_publications_count or 0, d.total_publications_count or 0)
            if not primary_hyde.openalex_id and d.openalex_id:
                primary_hyde.openalex_id = d.openalex_id
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == d.id).update(
                {ResearchLabDB.lead_advisor_id: primary_hyde.id}, synchronize_session=False
            )
            db.delete(d)
        primary_hyde.embedding_text = build_faculty_embedding_text(primary_hyde)
        print(f"  Merged {len(donor_hydes)} Kevin Hyde records into {primary_hyde.id} (citations: {primary_hyde.total_citations}, h-index: {primary_hyde.h_index}).")
        snapshot["merges"].append({
            "cluster_type": "kevin_hyde_consolidation",
            "primary_id": primary_hyde.id,
            "donor_ids": [d.id for d in donor_hydes]
        })

    # 4. Unified Deduplication across 216 clusters
    print("\n--- 4. Executing Unified Token & Initial-Aware Deduplication ---")
    facs = db.query(FacultyDB).all()
    by_univ = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn, ln, tokens = get_name_tokens(f)
        if len(tokens) >= 2:
            by_univ[f.university_th].append((f, tokens))

    clusters = []
    seen = set()

    for univ, members in by_univ.items():
        n = len(members)
        for i in range(n):
            f1, tok1 = members[i]
            if f1.id in seen:
                continue
            cluster = [f1]
            for j in range(i + 1, n):
                f2, tok2 = members[j]
                if f2.id in seen:
                    continue
                if are_same_person(tok1, tok2):
                    cluster.append(f2)
            if len(cluster) > 1:
                clusters.append((univ, cluster))
                for m in cluster:
                    seen.add(m.id)

    print(f"  Identified {len(clusters)} clusters to merge.")
    total_donors_deleted = 0

    for univ, cluster in clusters:
        sorted_cluster = sorted(cluster, key=score_faculty, reverse=True)
        primary = sorted_cluster[0]
        donors = sorted_cluster[1:]

        merge_entry = {
            "university_th": univ,
            "primary_id": primary.id,
            "donor_ids": [d.id for d in donors],
            "primary_before_cites": primary.total_citations,
            "donors_count": len(donors)
        }

        # Union publications
        all_pubs = []
        seen_pub_titles = set()
        for p in (primary.featured_publications or []):
            if isinstance(p, dict) and p.get("title"):
                t = p["title"].strip().lower()
                if t not in seen_pub_titles:
                    seen_pub_titles.add(t)
                    all_pubs.append(p)

        all_interests = list(primary.research_interests or [])
        seen_interests = set(all_interests)

        for donor in donors:
            primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
            primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
            primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
            primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
            primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

            # Metadata fallback
            if not primary.email and donor.email:
                primary.email = donor.email
            if (not primary.openalex_id or primary.openalex_id == "not_indexed") and (donor.openalex_id and donor.openalex_id != "not_indexed"):
                primary.openalex_id = donor.openalex_id
            if not primary.academic_title_th and donor.academic_title_th:
                primary.academic_title_th = donor.academic_title_th

            prim_has_thai = bool(THAI_REGEX.search(primary.full_name_th or ""))
            donor_has_thai = bool(THAI_REGEX.search(donor.full_name_th or ""))
            if not prim_has_thai and donor_has_thai:
                primary.full_name_th = donor.full_name_th

            if not primary.faculty_th and donor.faculty_th:
                primary.faculty_th = donor.faculty_th
            if not primary.department_th and donor.department_th:
                primary.department_th = donor.department_th
            if not primary.image_url and donor.image_url:
                primary.image_url = donor.image_url
            if not primary.profile_url and donor.profile_url:
                primary.profile_url = donor.profile_url

            for p in (donor.featured_publications or []):
                if isinstance(p, dict) and p.get("title"):
                    t = p["title"].strip().lower()
                    if t not in seen_pub_titles:
                        seen_pub_titles.add(t)
                        all_pubs.append(p)

            for item in (donor.research_interests or []):
                if item not in seen_interests:
                    seen_interests.add(item)
                    all_interests.append(item)

            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).update(
                {ResearchLabDB.lead_advisor_id: primary.id}, synchronize_session=False
            )

            db.delete(donor)
            total_donors_deleted += 1

        primary.featured_publications = all_pubs[:20]
        primary.research_interests = all_interests[:20]
        primary.embedding_text = build_faculty_embedding_text(primary)
        snapshot["merges"].append(merge_entry)

    print(f"  Successfully merged and deleted {total_donors_deleted} donor records across {len(clusters)} clusters.")

    # Save snapshot
    snap_path = os.path.join(BACKEND_DIR, "data", "agent_states", "advanced_zero_defect_loop_snapshot.json")
    with open(snap_path, "w", encoding="utf-8") as out:
        json.dump(snapshot, out, ensure_ascii=False, indent=2)
    print(f"  Saved snapshot checkpoint to {snap_path}")

    db.commit()
    db.close()
    print("\n======================================================================")
    print("✅ ADVANCED ZERO-DEFECT OPTIMIZATION COMPLETED AND COMMITTED")
    print("======================================================================")

if __name__ == "__main__":
    main()
