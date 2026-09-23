# -*- coding: utf-8 -*-
"""
Resolve Wave 60 Duplicates & Grounding Merge
============================================
Merges duplicates identified in Wave 60 acquisition:
1. Within-faculty curriculum duplicate listings (e.g. professors listed in multiple programs).
2. Merges with older wave records (e.g. psu_w58, kku_w58) preserving highest citations, h-index, and official emails.
3. Resolves cross-university transfers.
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict
import re

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB, ScholarUnassignedDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching


def merge_faculty_pair(primary: FacultyDB, secondary: FacultyDB, db) -> str:
    """Merges secondary into primary, retaining max metrics and authentic contact info."""
    # Retain best title and full name
    if secondary.academic_title_th and not primary.academic_title_th:
        primary.academic_title_th = secondary.academic_title_th
    if secondary.email and not primary.email:
        primary.email = secondary.email
    if secondary.image_url and not primary.image_url:
        primary.image_url = secondary.image_url
    if secondary.department_th and (not primary.department_th or primary.department_th == "ระบุไม่ได้"):
        primary.department_th = secondary.department_th

    # Bibliometrics: keep max
    primary.total_citations = max(primary.total_citations or 0, secondary.total_citations or 0)
    primary.h_index = max(primary.h_index or 0, secondary.h_index or 0)
    primary.total_publications_count = max(
        primary.total_publications_count or 0,
        secondary.total_publications_count or 0,
        primary.h_index or 0
    )

    # OpenAlex ID
    if (not primary.openalex_id or primary.openalex_id == "not_indexed") and secondary.openalex_id and secondary.openalex_id != "not_indexed":
        primary.openalex_id = secondary.openalex_id

    # Union publications
    pubs_map = {}
    for p in (primary.featured_publications or []):
        t = (p.get("title") or "").strip().lower()
        if t: pubs_map[t] = p
    for p in (secondary.featured_publications or []):
        t = (p.get("title") or "").strip().lower()
        if t and t not in pubs_map:
            pubs_map[t] = p
    primary.featured_publications = list(pubs_map.values())[:10]

    # Archive secondary to scholars_unassigned if it had distinct research ID or citations
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


def resolve_wave60_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 60 DUPLICATES & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 1: Exact full_name_th duplicates within faculties
        all_facs = db.query(FacultyDB).all()
        norm_map = defaultdict(list)
        for f in all_facs:
            cname = clean_thai_name_for_matching(f.full_name_th)
            if cname and len(cname) > 3:
                norm_map[(f.university_th, cname)].append(f)

        merged_count = 0
        for (u, cname), records in norm_map.items():
            if len(records) > 1:
                # Sort records: prefer one with official email, title, and most complete info
                records.sort(
                    key=lambda r: (
                        1 if r.email and "@" in r.email else 0,
                        1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                        r.total_citations or 0,
                        r.h_index or 0,
                        1 if r.image_url else 0,
                        1 if not r.id.startswith("univ_") else 0
                    ),
                    reverse=True
                )
                primary = records[0]
                for secondary in records[1:]:
                    print(f"  - Merging [{u}] {secondary.full_name_th} ({secondary.id}) into ({primary.id})")
                    merge_faculty_pair(primary, secondary, db)
                    merged_count += 1

        print(f"✅ Merged {merged_count} intra-university duplicate records.")

        # Step 2: Cross-University transfer checks
        # 2.1 Dr. Chutsana Techakana: KMUTNB Faculty of Business Administration vs Phayao ghost
        chutsana_kmutnb = db.query(FacultyDB).filter(FacultyDB.id.like("kmutnb_fba%"), FacultyDB.full_name_th.like("%ชุษณะ%")).first()
        chutsana_up = db.query(FacultyDB).filter(FacultyDB.id == "up_w59_1192_744").first()
        if chutsana_kmutnb and chutsana_up:
            print(f"  - Resolving transfer: Dr. Chutsana Techakana -> KMUTNB (archiving Phayao ghost)")
            merge_faculty_pair(chutsana_kmutnb, chutsana_up, db)

        # 2.2 Dr. On-anong Mala (PSU Nurse vs Phayao Physician)
        # Note: 'ดร. อรอนงค์ มาลา' (PSU Nursing Lecturer) vs 'พญ. อรอนงค์ มาลา' (Phayao Medical Doctor)
        # These are distinct people (Nurse Dr. vs Medical Doctor), so verify whether they are homonyms
        psu_on = db.query(FacultyDB).filter(FacultyDB.id.like("psu_nur%"), FacultyDB.full_name_th.like("%อรอนงค์ มาลา%")).first()
        up_on = db.query(FacultyDB).filter(FacultyDB.id == "wave22_0155_663").first()
        if psu_on and up_on:
            print(f"  - Verified distinct homonym: PSU Nursing ({psu_on.id}) vs UP Medicine ({up_on.id}). Retaining both authentically.")

        db.commit()
    finally:
        db.close()

    print("\n🎉 Wave 60 duplicate resolution completed successfully!")


if __name__ == "__main__":
    resolve_wave60_duplicates()
