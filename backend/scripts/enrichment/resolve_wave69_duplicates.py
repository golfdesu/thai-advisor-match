# -*- coding: utf-8 -*-
"""
Resolve Wave 69 Duplicates & Grounding Merge
============================================
Merges duplicates and consolidates profiles following Wave 69 acquisition:
1. Intra-university duplicate listings (CU CPS, KKU Education, NU Nursing, CU Sasin).
2. Harmonizing course-to-faculty parentheticals in courses (Sasin School of Management).
3. Merging new graduate-level records while preserving highest citations, images, and official emails.
4. Consolidating duplicate OpenAlex ID clusters.
5. Standardizing publication shape to {"title", "year", "venue", "url", "citation_count"}.
6. Splitting unparsed slashes (' / ') in research interests.
7. Synchronizing English university name (university) from TH_TO_EN_CANONICAL.
8. Sanitizing empty strings to None across all URL/email/name fields.
9. Cross-university email domain alignment using get_email_univ_safe.
10. Archiving merged secondary records to public.scholars_unassigned.
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
        primary.h_index or 0
    )

    # Authorship breakdown preservation
    if (secondary.first_author_count or 0) > 0 or (secondary.co_author_count or 0) > 0:
        primary.first_author_count = max(primary.first_author_count or 0, secondary.first_author_count or 0)
        primary.co_author_count = max(primary.co_author_count or 0, secondary.co_author_count or 0)
        primary.total_publications_count = max(
            primary.total_publications_count or 0,
            (primary.first_author_count or 0) + (primary.co_author_count or 0)
        )

    # OpenAlex ID: preserve authentic ID
    if (not primary.openalex_id or primary.openalex_id == "not_indexed") and secondary.openalex_id and secondary.openalex_id != "not_indexed":
        primary.openalex_id = secondary.openalex_id

    # Union publications
    pubs_map = {}
    for p in (primary.featured_publications or []):
        t = (p.get("title") or "").strip().lower()
        if t:
            pubs_map[t] = p
    for p in (secondary.featured_publications or []):
        t = (p.get("title") or "").strip().lower()
        if t and t not in pubs_map:
            pubs_map[t] = p
    primary.featured_publications = list(pubs_map.values())[:10]

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
            {"sid": sec_id}
        )
        conn.execute(text("DELETE FROM public.faculties WHERE id = :sid"), {"sid": sec_id})

    return sec_id


def resolve_wave69_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 69 DUPLICATES & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 0: Harmonize Course-to-Faculty Parentheticals in courses
        print("\n--- Harmonizing Course Parentheticals & Historical Names ---", flush=True)
        course_mappings = [
            ("จุฬาลงกรณ์มหาวิทยาลัย", "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์แห่งจุฬาลงกรณ์มหาวิทยาลัย", "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์"),
        ]

        harmonized_courses = 0
        for univ, old_fac, new_fac in course_mappings:
            courses = db.query(CourseDB).filter(CourseDB.university_th == univ, CourseDB.faculty_th == old_fac).all()
            for c in courses:
                c.faculty_th = new_fac
                harmonized_courses += 1
            if courses:
                print(f"  [Course Harmonization] [{univ}] \"{old_fac}\" -> \"{new_fac}\" ({len(courses)} courses)")
        print(f"✅ Total harmonized course entries: {harmonized_courses}")
        db.commit()

        # Step 0b: Standardize Sasin School of Management faculty name in faculties table
        print("\n--- Standardizing Sasin Faculty Names ---", flush=True)
        sasin_facs = db.query(FacultyDB).filter(FacultyDB.id.like("%sasin%")).all()
        for sf in sasin_facs:
            sf.faculty_th = "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์"
            sf.faculty = "Sasin School of Management"
        print(f"✅ Standardized {len(sasin_facs)} Sasin faculty records to 'สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์'")
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

        db.commit()

        # Step 2: Clean anomalous entries, fix slashes in interests, and publication shape for Wave 69
        wave69_prefixes = ["cu_cps%", "kku_ed%", "nu_nurse%", "cu_sasin%"]
        conditions = [FacultyDB.id.like(p) for p in wave69_prefixes]
        from sqlalchemy import or_
        all_wave_records = db.query(FacultyDB).filter(or_(*conditions)).all()

        for f in all_wave_records:
            # Fix double title prefixes
            for prefix in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "อ.", "ดร."]:
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

            # Deduplicate research interests and split " / "
            if f.research_interests:
                seen_int = set()
                c_int = []
                for item in f.research_interests:
                    parts = str(item).split(" / ")
                    for p in parts:
                        k = p.strip()
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

        # Step 2b: Archive administrative non-teaching support personnel from faculties
        print("\n--- Archiving Administrative Support Personnel ---", flush=True)
        staff_ids = ["nu_nurse__001", "nu_nurse__060"]
        for sid in staff_ids:
            s_rec = db.query(FacultyDB).filter(FacultyDB.id == sid).first()
            if s_rec:
                print(f"  [Archive Staff] Archiving non-teaching staff {s_rec.id} ({s_rec.full_name_th}) to scholars_unassigned")
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = :sid ON CONFLICT (id) DO NOTHING;"),
                        {"sid": sid}
                    )
                    conn.execute(text("DELETE FROM public.faculties WHERE id = :sid"), {"sid": sid})

        # Step 2c: Cross-University Institutional Transfer Merges
        print("\n--- Cross-University Institutional Transfer Merges ---", flush=True)
        # Chanita Praditsathaporn transferred from NU to UP (University of Phayao)
        nu_chanita = db.query(FacultyDB).filter(FacultyDB.id == "nu_nurse__044").first()
        up_chanita = db.query(FacultyDB).filter(FacultyDB.id == "up_w48_0061_846").first()
        if nu_chanita and up_chanita:
            print(f"  [Transfer Merge] Merging NU record ({nu_chanita.id}) into active UP faculty ({up_chanita.id})")
            merge_faculty_pair(up_chanita, nu_chanita, db)

        # Step 2d: Sasin School of Management Intra-Faculty Deduplication Merges
        print("\n--- Sasin Intra-Faculty Deduplication Merges ---", flush=True)
        sasin_pairs = [
            ("cu_sasin_professor_018", "cu_sasin_fenwick_001"),  # Ian Fenwick
            ("cu_sasin__003", "cu_sasin_038"),                  # Philip C. Zerrillo
            ("cu_sasin_professor_047", "cu_sasin_047"),          # Sirimon Treepongkaruna
            ("cu_sasin_professor_033", "cu_sasin_033"),          # Nophea Sasaki
            ("cu_sasin_professor_032", "cu_sasin_034"),          # Pattanaporn Chatjuthamard
            ("cu_sasin_sorapop_048", "cu_sasin_048"),            # Sorapop Kiatpongsan
            ("cu_sasin_professor_050", "cu_sasin_050"),          # Takamasa Fujioka
            ("cu_sasin__004", "cu_sasin_053"),                  # Wantanee Poonvoralak
        ]
        for p_id, s_id in sasin_pairs:
            p_rec = db.query(FacultyDB).filter(FacultyDB.id == p_id).first()
            s_rec = db.query(FacultyDB).filter(FacultyDB.id == s_id).first()
            if p_rec and s_rec:
                print(f"  [Sasin Merge] Merging secondary {s_rec.id} ({s_rec.full_name_th}) into primary {p_rec.id} ({p_rec.full_name_th})")
                merge_faculty_pair(p_rec, s_rec, db)

        # PDPA freemail purge (only institutional emails retained)
        for dom in ["@yahoo.", "@gmail.", "@hotmail.", "@outlook.", "@live.", "@icloud."]:
            for f in db.query(FacultyDB).filter(FacultyDB.email.like(f"%{dom}%")).all():
                f.email = None

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
            FacultyDB.total_publications_count < FacultyDB.h_index
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
                    1 if not r.id.startswith("univ_") else 0
                ),
                reverse=True
            )
            primary = records[0]
            for secondary in records[1:]:
                print(f"  - Merging OA {oaid}: ({secondary.id}) {secondary.full_name_th} -> ({primary.id}) {primary.full_name_th}")
                merge_faculty_pair(primary, secondary, db)

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
                        1 if r.image_url else 0
                    ),
                    reverse=True
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

    print("\n🎉 Wave 69 duplicate resolution completed successfully!")


if __name__ == "__main__":
    resolve_wave69_duplicates()
