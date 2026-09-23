# -*- coding: utf-8 -*-
"""
Resolve Wave 62 Duplicates & Grounding Merge
============================================
Merges duplicates and consolidates profiles following Wave 62 acquisition:
1. Intra-university duplicate listings (e.g. Sasin historical IDs vs newly harvested records).
2. Merging new graduate-level records while preserving highest citations, images, and official emails.
3. Consolidating duplicate OpenAlex ID clusters.
4. Archiving merged secondary records to public.scholars_unassigned.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
import re

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB, ScholarUnassignedDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching


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


def resolve_wave62_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 62 DUPLICATES & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 1: Deduplicate identical OpenAlex IDs
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
            # Prioritize official email, higher academic rank, full credentials, and citations
            records.sort(
                key=lambda r: (
                    1 if r.email and "@" in r.email else 0,
                    1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                    1 if r.image_url else 0,
                    r.total_citations or 0,
                    r.h_index or 0,
                    1 if not r.id.startswith("cu_sasin_0") else 0  # prefer new structured ID or vice versa
                ),
                reverse=True
            )
            primary = records[0]
            for secondary in records[1:]:
                print(f"  - Merging OA {oaid}: ({secondary.id}) {secondary.full_name_th} -> ({primary.id}) {primary.full_name_th}")
                merge_faculty_pair(primary, secondary, db)

        # Step 2: Exact & normalized name duplicates within university
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
                # Sort records: prioritize official email, title rank, citations, and image
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

    print("\n🎉 Wave 62 duplicate resolution completed successfully!")


if __name__ == "__main__":
    resolve_wave62_duplicates()
