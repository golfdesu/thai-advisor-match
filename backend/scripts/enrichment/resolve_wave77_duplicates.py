# -*- coding: utf-8 -*-
"""
Resolve Wave 77 Duplicates & Grounding Merge
============================================
Merges duplicates and consolidates profiles following Wave 77 acquisition:
1. Harmonizing Sukhothai Thammathirat Open University Courses:
   - Ensuring all 70 courses in 'courses' table have exact faculty_th aligned with the 12 schools.
2. Synchronizing English university name (university) from TH_TO_EN_CANONICAL ("Sukhothai Thammathirat Open University").
3. Sanitizing empty strings to None across all URL/email/name fields.
4. Sanitizing research interests: stripping nav boilerplate, slashes, trailing punctuation,
   and intra-faculty duplicate interests.
5. Standardizing publication shape to {"title", "year", "venue", "url", "citation_count"}.
6. PDPA freemail purge (only official institutional emails retained).
7. Cross-university email domain alignment using get_email_univ_safe.
8. Enforcing Bibliometric Monotonicity Invariant (total_publications_count >= h_index).
9. Deduplicating identical OpenAlex IDs within and across universities.
10. Exact & normalized Thai name deduplication within university.
11. Archiving merged secondary records to public.scholars_unassigned.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
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
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching, get_email_univ_safe
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL


def merge_faculty_pair(primary: FacultyDB, secondary: FacultyDB, db) -> str:
    """Merges secondary into primary, retaining max metrics and authentic contact info."""
    if secondary.academic_title_th and (not primary.academic_title_th or primary.academic_title_th == "อาจารย์"):
        primary.academic_title_th = secondary.academic_title_th
    if secondary.email and not primary.email:
        primary.email = secondary.email
    if secondary.image_url and not primary.image_url:
        primary.image_url = secondary.image_url
    if secondary.department_th and (not primary.department_th or primary.department_th == "ระบุไม่ได้"):
        primary.department_th = secondary.department_th

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

    # Union research interests (excluding nav boilerplate)
    nav_boilerplate = ["วิจัย/บริการวิชาการ", "งานวิจัย และงานวิชาการ", "วารสารพัฒนศาสตร์", "โทรศัพท์", "ติดต่อ", "กยศ.", "ทุนการศึกษา"]
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


def resolve_wave77_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 77 DUPLICATES & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 0: Harmonize Course-to-Faculty Naming in courses
        print("\n--- Harmonizing Sukhothai Thammathirat Open University Courses Naming ---", flush=True)
        univ_name = "มหาวิทยาลัยสุโขทัยธรรมาธิราช"

        # Align administrative bureau courses into academic schools
        course_mappings = [
            (univ_name, "สำนักบัณฑิตศึกษา", "สาขาวิชาศึกษาศาสตร์"),
            (univ_name, "สำนักทะเบียนและวัดผล", "สาขาวิชาศิลปศาสตร์"),
        ]

        harmonized_courses = 0
        for univ, old_fac, new_fac in course_mappings:
            courses = db.query(CourseDB).filter(CourseDB.university_th == univ, CourseDB.faculty_th == old_fac).all()
            for c in courses:
                c.faculty_th = new_fac
                harmonized_courses += 1
            if courses:
                print(f'  [Course Harmonization] [{univ}] "{old_fac}" -> "{new_fac}" ({len(courses)} courses)')

        print(f"✅ Total harmonized course entries: {harmonized_courses}")
        db.commit()

        # Step 1: English university name synchronization & empty string sanitization
        all_faculties = db.query(FacultyDB).all()
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

        db.commit()

        # Step 2: Clean anomalous entries, fix slashes in interests, and publication shape for Wave 77
        all_stou_records = db.query(FacultyDB).filter(FacultyDB.id.like("stou_%")).all()

        nav_boilerplate = ["วิจัย/บริการวิชาการ", "งานวิจัย และงานวิชาการ", "วารสารพัฒนศาสตร์", "โทรศัพท์", "ติดต่อ", "กยศ.", "ทุนการศึกษา", "ค่าเทอม"]

        for f in all_stou_records:
            # Fix double title prefixes
            for prefix in ["ศ.เกียรติคุณ นพ.", "ศ.เกียรติคุณ", "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "พญ.", "นพ.", "อาจารย์"]:
                dbl = f"{prefix} {prefix}"
                if f.full_name_th and dbl in f.full_name_th:
                    f.full_name_th = f.full_name_th.replace(dbl, prefix)

            # Ensure last_name is clean and non-empty
            if f.first_name and not f.last_name:
                f.last_name = f.first_name

            # URL encode spaces in profile_url and image_url
            if f.image_url and " " in f.image_url:
                f.image_url = urllib.parse.quote(f.image_url, safe=":/%?=")
            if f.profile_url and " " in f.profile_url:
                f.profile_url = urllib.parse.quote(f.profile_url, safe=":/%?=")

            # Deduplicate research interests, split " / ", and strip punctuation & nav boilerplate
            if f.research_interests:
                seen_int = set()
                c_int = []
                for item in f.research_interests:
                    parts = str(item).split(" / ")
                    for p in parts:
                        k = p.strip().rstrip(",;.:")
                        if k.startswith(('"', "'")) and k.endswith(('"', "'")):
                            k = k[1:-1].strip()
                        if any(b in k for b in nav_boilerplate):
                            continue
                        if k and k.lower() not in seen_int and len(k) > 1:
                            seen_int.add(k.lower())
                            c_int.append(k)
                f.research_interests = c_int

            # Standardize featured publications shape to {"title", "year", "venue", "url", "citation_count"}
            if f.featured_publications:
                clean_pubs = []
                for pub in f.featured_publications:
                    if isinstance(pub, dict) and pub.get("title"):
                        clean_pubs.append({
                            "title": pub["title"],
                            "year": pub.get("year"),
                            "venue": pub.get("venue"),
                            "url": pub.get("url") or pub.get("doi"),
                            "citation_count": pub.get("citation_count") or pub.get("citations") or 0,
                        })
                f.featured_publications = clean_pubs

        # PDPA freemail purge (only institutional emails retained)
        for dom in ["@yahoo.", "@gmail.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            for f in db.query(FacultyDB).filter(FacultyDB.email.like(f"%{dom}%")).all():
                f.email = None

        # Re-fetch wave records after deletions/merges to avoid ObjectDeletedError
        all_stou_records = db.query(FacultyDB).filter(FacultyDB.id.like("stou_%")).all()

        # Email hygiene & trailing junk removal for Wave 77
        for f in all_stou_records:
            if f.email:
                em = f.email.strip().lower()
                m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", em)
                if m:
                    clean_em = m.group(1).strip()
                    if clean_em != f.email:
                        print(f"  [Email Hygiene] Cleaned '{f.email}' -> '{clean_em}'")
                        f.email = clean_em

        # Cross-university email domain alignment:
        facs_with_email = db.query(FacultyDB).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").all()
        for f in facs_with_email:
            email_univ = get_email_univ_safe(f.email)
            if email_univ and email_univ != f.university_th:
                print(f"  [Email Realignment] Clearing conflicting foreign email '{f.email}' ({email_univ}) for '{f.full_name_th}' at '{f.university_th}'")
                f.email = None

        # Bibliometric Monotonicity Invariant: total_publications_count >= h_index
        monotonicity_violations = db.query(FacultyDB).filter(
            FacultyDB.h_index.isnot(None),
            FacultyDB.total_publications_count < FacultyDB.h_index,
        ).all()
        if monotonicity_violations:
            print(f"\n--- Enforcing Bibliometric Monotonicity ({len(monotonicity_violations)} records) ---", flush=True)
            for f in monotonicity_violations:
                f.total_publications_count = max(f.total_publications_count or 0, f.h_index or 0)

        db.commit()

        # Step 3: Deduplicate identical OpenAlex IDs
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

        # Step 4: Exact & normalized name duplicates within university
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

    print("\n🎉 Wave 77 duplicate resolution completed successfully!")


if __name__ == "__main__":
    resolve_wave77_duplicates()
