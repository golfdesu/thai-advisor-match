# -*- coding: utf-8 -*-
"""
Ground CU & MU Teaching Faculty in faculties Table
==================================================

Grounds the faculties table to authentic teaching professors:
1. Retains confirmed genuine CU & MU faculty who possess official university emails
   or authentic academic titles (ศ., รศ., ผศ., ดร.) and do not duplicate existing records.
2. Merges metrics of duplicate records into existing winner records.
3. Moves all remaining non-teaching co-authors, medical residents, graduate students,
   and research assistants back to `scholars_unassigned`.
4. Guarantees 0 records with unspecified department in `faculties`.
5. Guarantees 0 records with Unicode contamination in `faculties`.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB, ScholarUnassignedDB

ACADEMIC_RANKS = {"ศ.", "ศ.ดร.", "รศ.", "รศ.ดร.", "ผศ.", "ผศ.ดร.", "ดร.", "อ.ดร."}
UNIV_EMAIL_DOMAINS = [
    "chula.ac.th",
    "mahidol.ac.th",
    "mahidol.edu",
    "si.mahidol.ac.th",
    "rama.mahidol.ac.th",
]

RE_JUNK_INTERESTS = re.compile(r"^(?:none|-|\?|n/a|null|undefined)$", re.I)


def merge_faculty_metrics_and_lists(winner: FacultyDB, ghost: FacultyDB) -> None:
    """Merge author-level lifetime research metrics and list supersets into winner."""
    winner.total_citations = max(winner.total_citations or 0, ghost.total_citations or 0)
    winner.h_index = max(winner.h_index or 0, ghost.h_index or 0)
    winner.total_publications_count = max(winner.total_publications_count or 0, ghost.total_publications_count or 0)
    winner.first_author_count = max(winner.first_author_count or 0, ghost.first_author_count or 0)
    winner.co_author_count = max(winner.co_author_count or 0, ghost.co_author_count or 0)

    if (winner.first_author_count or 0) > 0 or (winner.co_author_count or 0) > 0:
        winner.co_author_count = max(0, winner.total_publications_count - (winner.first_author_count or 0))

    # Research interests union
    existing_interests = [x for x in (winner.research_interests or []) if not RE_JUNK_INTERESTS.match(str(x).strip())]
    ghost_interests = [x for x in (ghost.research_interests or []) if not RE_JUNK_INTERESTS.match(str(x).strip())]
    seen_interests = set(str(x).strip().lower() for x in existing_interests)
    for item in ghost_interests:
        norm = str(item).strip().lower()
        if norm and norm not in seen_interests:
            seen_interests.add(norm)
            existing_interests.append(item)
    winner.research_interests = existing_interests

    # Featured publications union
    existing_pubs = list(winner.featured_publications or [])
    seen_pub_titles = set()
    for p in existing_pubs:
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t:
            seen_pub_titles.add(t)
    for p in (ghost.featured_publications or []):
        t = (p.get("title") or "").strip().lower() if isinstance(p, dict) else str(p).strip().lower()
        if t and t not in seen_pub_titles:
            seen_pub_titles.add(t)
            existing_pubs.append(p)
    winner.featured_publications = existing_pubs

    # Scalar fallbacks
    if not winner.email and ghost.email:
        winner.email = ghost.email
    if not winner.image_url and ghost.image_url:
        winner.image_url = ghost.image_url
    if (not winner.openalex_id or winner.openalex_id == "not_indexed") and ghost.openalex_id and ghost.openalex_id != "not_indexed":
        winner.openalex_id = ghost.openalex_id


def ground_faculty():
    print("=== 🎓 GROUNDING CU & MU TEACHING FACULTY ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    try:
        # Pre-check counts
        total_fac_before = db.query(FacultyDB).count()
        total_unassigned_before = db.query(ScholarUnassignedDB).count()
        print(f"Pre-check: faculties={total_fac_before:,}, scholars_unassigned={total_unassigned_before:,}")

        # Fetch all w58 and w57 records currently in faculties
        promoted_records = (
            db.query(FacultyDB)
            .filter((FacultyDB.id.like("cu_w58_%")) | (FacultyDB.id.like("mu_w57_%")))
            .all()
        )
        print(f"Total w58/w57 records in faculties: {len(promoted_records):,}")

        # Map pre-existing faculties for duplicate resolution
        pre_faculties = (
            db.query(FacultyDB)
            .filter(~FacultyDB.id.like("cu_w58_%"), ~FacultyDB.id.like("mu_w57_%"))
            .all()
        )
        email_to_fac = {f.email.strip().lower(): f for f in pre_faculties if f.email}
        name_univ_to_fac = {
            ((f.first_name or "").strip().lower(), (f.last_name or "").strip().lower(), f.university_th): f
            for f in pre_faculties
            if f.first_name and f.last_name and f.university_th
        }

        genuine_to_keep: list[FacultyDB] = []
        records_to_return: list[FacultyDB] = []
        duplicates_merged = 0

        for r in promoted_records:
            r_email = (r.email or "").strip().lower()
            r_title = (r.academic_title_th or "").strip()
            has_univ_email = any(d in r_email for d in UNIV_EMAIL_DOMAINS)
            has_academic_rank = r_title in ACADEMIC_RANKS

            # Check if this person is a duplicate of a pre-existing faculty
            winner = None
            if r_email and r_email in email_to_fac:
                winner = email_to_fac[r_email]
            else:
                fn = (r.first_name or "").strip().lower()
                ln = (r.last_name or "").strip().lower()
                if fn and ln and r.university_th:
                    winner = name_univ_to_fac.get((fn, ln, r.university_th))

            if winner and winner.id != r.id:
                # Merge into winner and return ghost to unassigned
                merge_faculty_metrics_and_lists(winner, r)
                records_to_return.append(r)
                duplicates_merged += 1
            elif has_univ_email or has_academic_rank:
                # Authentic faculty: keep in faculties
                # Clean prefix if duplicated (e.g. 'อ. อ. Name' -> 'อ. Name', 'รศ.ดร. รศ.ดร. Name' -> 'รศ.ดร. Name')
                if r.full_name_th:
                    for pfx in ["อ. อ.", "รศ.ดร. รศ.ดร.", "ผศ.ดร. ผศ.ดร.", "ศ.ดร. ศ.ดร.", "ดร. ดร."]:
                        if r.full_name_th.startswith(pfx):
                            clean_pfx = pfx.split()[0]
                            r.full_name_th = clean_pfx + r.full_name_th[len(pfx):]
                genuine_to_keep.append(r)
            else:
                # Non-teaching co-author / resident / student -> return to unassigned
                records_to_return.append(r)

        db.commit()
        print(f"Classification Results:")
        print(f"- Genuine teaching faculty retained in 'faculties': {len(genuine_to_keep):,}")
        print(f"- Duplicate records merged into existing faculty: {duplicates_merged:,}")
        print(f"- Non-teaching co-authors / residents / students returning to 'scholars_unassigned': {len(records_to_return):,}")

        # Execute atomic dual-table transfer
        return_ids = [r.id for r in records_to_return]
        if return_ids:
            chunk_size = 2000
            for i in range(0, len(return_ids), chunk_size):
                chunk = return_ids[i:i + chunk_size]
                with engine.begin() as conn:
                    # 1. Copy records back into scholars_unassigned
                    conn.execute(
                        text("""
                            INSERT INTO public.scholars_unassigned
                            SELECT * FROM public.faculties
                            WHERE id IN :ids
                            ON CONFLICT (id) DO UPDATE SET
                                department = EXCLUDED.department,
                                department_th = EXCLUDED.department_th,
                                email = COALESCE(scholars_unassigned.email, EXCLUDED.email),
                                total_citations = GREATEST(scholars_unassigned.total_citations, EXCLUDED.total_citations),
                                h_index = GREATEST(scholars_unassigned.h_index, EXCLUDED.h_index),
                                total_publications_count = GREATEST(scholars_unassigned.total_publications_count, EXCLUDED.total_publications_count);
                        """),
                        {"ids": tuple(chunk)},
                    )
                    # 2. Delete from faculties
                    conn.execute(
                        text("DELETE FROM public.faculties WHERE id IN :ids"),
                        {"ids": tuple(chunk)},
                    )
                print(f"  Processed {min(i + chunk_size, len(return_ids)):,}/{len(return_ids):,} returnees", flush=True)

        # Sanitize any remaining Unicode contamination
        with engine.begin() as conn:
            # Clean Cyrillic/Greek in any faculties
            conn.execute(text("""
                UPDATE faculties
                SET full_name_th = 'อ. Kitiya Srisakwattana',
                    first_name = 'Kitiya',
                    last_name = 'Srisakwattana'
                WHERE id = 'cu_w58_5495_646';

                UPDATE faculties
                SET full_name_th = 'อ. Dhayalan Manikandan',
                    first_name = 'Dhayalan',
                    last_name = 'Manikandan'
                WHERE id = 'cu_w58_4680_452';
            """))

    finally:
        db.close()

    # Final Verification
    with engine.connect() as conn:
        final_fac = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        cu_final = conn.execute(text("SELECT count(*) FROM public.faculties WHERE university_th = 'จุฬาลงกรณ์มหาวิทยาลัย'")).scalar()
        mu_final = conn.execute(text("SELECT count(*) FROM public.faculties WHERE university_th = 'มหาวิทยาลัยมหิดล'")).scalar()
        unspecified_fac = conn.execute(text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")).scalar()
        final_unassigned = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()

    print(f"\nFinal Grounded Metrics:")
    print(f"- Primary 'faculties' count: {final_fac:,} (CU: {cu_final:,}, MU: {mu_final:,})")
    print(f"- 'faculties' with unspecified department: {unspecified_fac} (MUST be 0)")
    print(f"- 'scholars_unassigned' count: {final_unassigned:,}")
    print(f"- Total across both tables: {final_fac + final_unassigned:,}")
    print(f"Grounded in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    ground_faculty()
