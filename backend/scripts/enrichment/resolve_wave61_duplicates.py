# -*- coding: utf-8 -*-
"""
Resolve Wave 61 Duplicates & Grounding Merge
============================================
Merges duplicates and consolidates profiles following Wave 61 acquisition:
1. Intra-university duplicate listings (e.g. cross-program appointments, duplicate titles).
2. Merging new graduate-level records with historical waves (e.g. wave58, wave59) while preserving highest citations and official emails.
3. Cross-university transfers based on verified institutional emails (.ac.th).
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
    if secondary.academic_title_th and not primary.academic_title_th:
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


def resolve_wave61_duplicates():
    print("=================================================================", flush=True)
    print("🔄 RESOLVING WAVE 61 DUPLICATES & PROFILE MERGING", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 1: Clean any truly empty anomalous entries
        anomalous = db.query(FacultyDB).filter(
            ((FacultyDB.full_name_th == "") | (FacultyDB.full_name_th.is_(None))) &
            ((FacultyDB.first_name == "") | (FacultyDB.first_name.is_(None)))
        ).all()
        for a in anomalous:
            print(f"  ❌ Purging anomalous entry with empty name: {a.id}")
            db.delete(a)
        db.commit()

        # Step 2: Resolve specific verified transfers & cross-university duplicates
        # 2.1 รศ. ฉวีวรรณ บุญสุยา -> Thammasat University (FPH)
        f_chaweewan = db.query(FacultyDB).filter(FacultyDB.id == "wave30_0090_125").first()
        if f_chaweewan and "fph.tu.ac.th" in (f_chaweewan.email or ""):
            print("  🔄 Re-affiliating Assoc. Prof. Chaweewan Boonsuya to Thammasat University (Faculty of Public Health)")
            f_chaweewan.university_th = "มหาวิทยาลัยธรรมศาสตร์"
            f_chaweewan.faculty_th = "คณะสาธารณสุขศาสตร์"
            f_chaweewan.department_th = "สาขาวิชาอนามัยชุมชน"
            db.commit()

        # 2.2 Assoc. Prof. Dr. Aunnitha Disthanont: CBS Chula (cbs-012_661aca) -> CITU Thammasat (tu_grad__062)
        f_tu_aun = db.query(FacultyDB).filter(FacultyDB.id == "tu_grad__062").first()
        f_cu_aun = db.query(FacultyDB).filter(FacultyDB.id == "cbs-012_661aca").first()
        if f_tu_aun and f_cu_aun:
            print("  🔄 Consolidating Assoc. Prof. Dr. Aunnitha Disthanont into Thammasat CITU")
            merge_faculty_pair(f_tu_aun, f_cu_aun, db)

        # Step 3: Deduplicate identical OpenAlex IDs (e.g. Mahidol CMMU bilingual duplicates)
        dup_oa = (
            db.query(FacultyDB.openalex_id, text("count(*) as cnt"))
            .filter(FacultyDB.openalex_id.isnot(None), FacultyDB.openalex_id != "", FacultyDB.openalex_id != "not_indexed")
            .group_by(FacultyDB.openalex_id)
            .having(text("count(*) > 1"))
            .all()
        )
        print(f"\n--- Resolving {len(dup_oa)} Duplicate OpenAlex ID Clusters ---")
        for oaid, cnt in dup_oa:
            records = db.query(FacultyDB).filter(FacultyDB.openalex_id == oaid).all()
            # Prioritize official email, Thai name, specific department, and citations
            records.sort(
                key=lambda r: (
                    1 if r.email and "@" in r.email else 0,
                    1 if r.department_th and r.department_th not in ["วิทยาลัยการจัดการ", "ระบุไม่ได้"] else 0,
                    1 if any(ord(c) > 3000 for c in (r.full_name_th or "")) else 0,
                    1 if r.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."] else 0,
                    r.total_citations or 0,
                    r.h_index or 0
                ),
                reverse=True
            )
            primary = records[0]
            for secondary in records[1:]:
                print(f"  - Merging OA {oaid}: ({secondary.id}) {secondary.full_name_th} -> ({primary.id}) {primary.full_name_th}")
                merge_faculty_pair(primary, secondary, db)

        # Step 4: Exact full_name_th duplicates within faculties
        all_facs = db.query(FacultyDB).all()
        norm_map = defaultdict(list)
        for f in all_facs:
            cname = clean_thai_name_for_matching(f.full_name_th)
            if cname and len(cname) > 3:
                norm_map[(f.university_th, cname)].append(f)

        merged_count = 0
        for (u, cname), records in norm_map.items():
            if len(records) > 1:
                # Sort records: prioritize official email, title, citation count, and graduate departmental record
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
        db.commit()
    finally:
        db.close()

    print("\n🎉 Wave 61 duplicate resolution completed successfully!")


if __name__ == "__main__":
    resolve_wave61_duplicates()
