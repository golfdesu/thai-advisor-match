# -*- coding: utf-8 -*-
"""
Resolve Wave 82 Duplicates & Flagship Faculty Harmonization
===========================================================
Harmonizes and consolidates flagship faculty profiles across Top 5 Thai universities:
1. Chulalongkorn University (Faculty of Architecture)
2. Thammasat University (Faculty of Economics, Political Science, Journalism)
3. Mahidol University (Faculty of Engineering - EGCO)

Cleaning Steps:
1. Synchronizing English university name from TH_TO_EN_CANONICAL.
2. Sanitizing empty strings to None across all URL/email/name fields.
3. Enforcing Bibliometric Monotonicity Invariant (total_publications_count >= h_index).
4. Deduplicating identical OpenAlex IDs within and across universities.
5. Exact & normalized Thai name deduplication within university.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB, CourseDB, ScholarUnassignedDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL


def merge_faculty_pair(primary: FacultyDB, secondary: FacultyDB, db) -> str:
    """Merges secondary into primary, retaining max metrics and authentic contact info."""
    if secondary.academic_title_th and (not primary.academic_title_th or primary.academic_title_th in ["อาจารย์", "อ."]):
        primary.academic_title_th = secondary.academic_title_th
    if secondary.email and not primary.email:
        primary.email = secondary.email
    if secondary.image_url and not primary.image_url:
        primary.image_url = secondary.image_url
    if secondary.department_th and (not primary.department_th or primary.department_th == "ระบุไม่ได้"):
        primary.department_th = secondary.department_th
    if secondary.department and not primary.department:
        primary.department = secondary.department
    if secondary.profile_url and not primary.profile_url:
        primary.profile_url = secondary.profile_url

    # Bibliometrics: preserve max
    primary.total_citations = max(primary.total_citations or 0, secondary.total_citations or 0)
    primary.h_index = max(primary.h_index or 0, secondary.h_index or 0)
    primary.total_publications_count = max(
        primary.total_publications_count or 0,
        secondary.total_publications_count or 0,
        primary.h_index or 0,
    )

    # Authorship breakdown preservation
    if (secondary.first_author_count or 0) > 0 or (secondary.co_author_count or 0) > 0:
        primary.first_author_count = max(primary.first_author_count or 0, secondary.first_author_count or 0)
        primary.co_author_count = max(primary.co_author_count or 0, secondary.co_author_count or 0)
        primary.total_publications_count = max(
            primary.total_publications_count or 0,
            (primary.first_author_count or 0) + (primary.co_author_count or 0),
        )

    # OpenAlex ID: preserve authentic ID
    if (not primary.openalex_id or primary.openalex_id == "not_indexed") and secondary.openalex_id and secondary.openalex_id != "not_indexed":
        primary.openalex_id = secondary.openalex_id

    # Union publications
    pubs_map = {}
    for p in primary.featured_publications or []:
        t = (p.get("title") or "").strip().lower()
        if t:
            pubs_map[t] = p
    for p in secondary.featured_publications or []:
        t = (p.get("title") or "").strip().lower()
        if t and t not in pubs_map:
            pubs_map[t] = p
    primary.featured_publications = list(pubs_map.values())[:10]

    # Union research interests
    nav_boilerplate = ["วิจัย/บริการวิชาการ", "งานวิจัย และงานวิชาการ", "โทรศัพท์", "ติดต่อ", "กยศ.", "ทุนการศึกษา", "Office:", "Email:"]
    seen_interests = set()
    cleaned_interests = []
    for item in (primary.research_interests or []) + (secondary.research_interests or []):
        parts = str(item).split(" / ")
        for p in parts:
            k = p.strip().rstrip(",;.:")
            if k.startswith(('"', "'")) and k.endswith(('"', "'")):
                k = k[1:-1].strip()
            if any(b in k for b in nav_boilerplate):
                continue
            if re.match(r"^\d+$", k):
                continue
            if "|" in k:
                k = k.replace("|", "").strip()
            if k and k.lower() not in seen_interests and len(k) > 1:
                seen_interests.add(k.lower())
                cleaned_interests.append(k)
    primary.research_interests = cleaned_interests

    sec_id = secondary.id
    db.commit()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = :sid
                ON CONFLICT (id) DO UPDATE SET
                    total_citations = EXCLUDED.total_citations,
                    h_index = EXCLUDED.h_index,
                    openalex_id = EXCLUDED.openalex_id;
            """),
            {"sid": sec_id},
        )
        conn.execute(text("DELETE FROM public.faculties WHERE id = :sid"), {"sid": sec_id})

    return sec_id


def resolve_wave82_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 82 FLAGSHIP FACULTY DUPLICATES & HARMONIZATION", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 1: English university name synchronization & empty string sanitization
        all_faculties = db.query(FacultyDB).all()
        print(f"Checking {len(all_faculties)} faculty records...", flush=True)
        for f in all_faculties:
            if f.university_th in TH_TO_EN_CANONICAL:
                expected_en = TH_TO_EN_CANONICAL[f.university_th]
                if f.university != expected_en:
                    f.university = expected_en

            # Sanitize empty strings to None
            if f.image_url == "":
                f.image_url = None
            if f.profile_url == "":
                f.profile_url = None
            if f.email == "":
                f.email = None
            if f.scholar_url == "":
                f.scholar_url = None
            if f.role == "":
                f.role = None
            if f.department == "":
                f.department = None
            if f.department_th == "":
                f.department_th = None

            # Bibliometric monotonicity
            if f.h_index is not None and (f.total_publications_count or 0) < f.h_index:
                f.total_publications_count = f.h_index

        db.commit()
        print("✅ Field sanitization and English university canonicalization completed.", flush=True)

        # Step 2: Deduplicate identical OpenAlex IDs
        dup_oa = (
            db.query(FacultyDB.openalex_id, text("count(*) as cnt"))
            .filter(FacultyDB.openalex_id.isnot(None), FacultyDB.openalex_id != "", FacultyDB.openalex_id != "not_indexed")
            .group_by(FacultyDB.openalex_id)
            .having(text("count(*) > 1"))
            .all()
        )
        print(f"\n--- Resolving {len(dup_oa)} Duplicate OpenAlex ID Clusters ---", flush=True)
        for oaid, cnt in dup_oa:
            records = db.query(FacultyDB).filter(FacultyDB.openalex_id == oaid).all()
            records.sort(
                key=lambda r: (
                    1 if r.email and "@" in r.email else 0,
                    1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                    1 if r.image_url else 0,
                    r.total_citations or 0,
                    r.h_index or 0,
                    1 if not r.id.startswith("univ_") else 0,
                ),
                reverse=True,
            )
            primary = records[0]
            p_cname = clean_thai_name_for_matching(primary.full_name_th)
            for secondary in records[1:]:
                s_cname = clean_thai_name_for_matching(secondary.full_name_th)
                same_person = (
                    (p_cname and s_cname and (p_cname in s_cname or s_cname in p_cname))
                    or (primary.first_name and secondary.first_name and primary.first_name.lower() == secondary.first_name.lower())
                )
                if same_person:
                    print(f"  - Merging OA {oaid}: ({secondary.id}) {secondary.full_name_th} -> ({primary.id}) {primary.full_name_th}")
                    merge_faculty_pair(primary, secondary, db)
                else:
                    print(f"  - Disambiguating OA collision for {oaid}: Disconnecting secondary ({secondary.id}) {secondary.full_name_th} from ({primary.id}) {primary.full_name_th}")
                    secondary.openalex_id = None
                    db.commit()

        # Step 3: Exact & normalized name duplicates within university
        all_facs = db.query(FacultyDB).all()
        norm_map = defaultdict(list)
        for f in all_facs:
            cname = clean_thai_name_for_matching(f.full_name_th)
            if cname and len(cname) > 3:
                norm_map[(f.university_th, cname)].append(f)

        print(f"\n--- Checking Normalized Name Clusters ---", flush=True)
        merged_count = 0
        for (u, cname), records in norm_map.items():
            if len(records) > 1:
                records.sort(
                    key=lambda r: (
                        1 if r.email and "@" in r.email else 0,
                        1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                        r.total_citations or 0,
                        r.h_index or 0,
                        1 if r.image_url else 0,
                    ),
                    reverse=True,
                )
                primary = records[0]
                for secondary in records[1:]:
                    print(f"  - Merging [{u}] {secondary.full_name_th} ({secondary.id}) into ({primary.id})")
                    merge_faculty_pair(primary, secondary, db)
                    merged_count += 1

        print(f"✅ Merged {merged_count} intra-university duplicate records.")
        db.commit()
    finally:
        db.close()

    print("\n🎉 Wave 82 duplicate resolution completed successfully!")


if __name__ == "__main__":
    resolve_wave82_duplicates()
