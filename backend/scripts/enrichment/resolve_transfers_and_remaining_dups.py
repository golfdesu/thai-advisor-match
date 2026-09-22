# -*- coding: utf-8 -*-
"""
Resolve University Transfers & Remaining Duplicate Faculty
=========================================================
Resolves:
1. 148 duplicate Thai name clusters where one record has verified email/rank and other rows are ghosts.
2. 6 cross-university transfers (e.g. Grienggrai Rajchakit SUT vs MJU, Sutthiphan Suriya TU vs SU, Pakkawat Detcheewa BUU vs MJU).
3. Preserves 100% of author lifetime citations, h-index, and publication supersets.
4. Archives obsolete / ghost rows into scholars_unassigned.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
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
from scripts.enrichment.clean_and_ground_all_faculties import (
    merge_faculty_metrics_and_lists,
    get_email_univ,
    score_record_as_winner,
)


def resolve_remaining():
    print("=== 🎓 RESOLVING UNIVERSITY TRANSFERS & REMAINING DUPLICATES ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    try:
        facs_all = db.query(FacultyDB).all()
        print(f"Total current faculties: {len(facs_all):,}")

        thai_groups = defaultdict(list)
        for f in facs_all:
            th = (f.full_name_th or "").strip()
            th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.)\s*", "", th).strip()
            th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
            th_clean = re.sub(r"\s+", "", th_clean)
            if th_clean and len(th_clean) > 3 and not re.match(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)$", th_clean):
                thai_groups[th_clean].append(f)

        remaining_dups = {k: v for k, v in thai_groups.items() if len(v) > 1}
        print(f"Discovered {len(remaining_dups)} duplicate Thai name groups.")

        ghosts_to_archive: list[FacultyDB] = []
        merges_count = 0

        # Special manual transfer overrides where known
        TRANSFER_WINNERS = {
            "เกรียงไกรราชกิจ": "sut_sci_grienggrai_001",           # Grienggrai Rajchakit -> SUT
            "ภก.สุทธิพันธ์สุริยะ": "thammasatu_facultyofp_suriya_023", # Sutthiphan Suriya -> Thammasat
            "ภัควัฒน์เดชชีวะ": "buu_w42_0194_134",                 # Pakkawat Detcheewa -> Burapha
            "ชัยพัฒน์หล่อศิริรัตน์": "wave24_0016_910",              # Chaipat Lorsirirat -> Chulalongkorn
            "พงษ์ศักดิ์กีรติวินทกร": "kmitl_w39_0011_606",          # Phongsak Keeratiwintakorn -> KMITL
            "นันทภัทร์เฉลียวศักดิ์": "wu_w51_0192_137",              # Nanthaphat Chaleawsak -> Walailak
        }

        for k, rows in remaining_dups.items():
            if k in TRANSFER_WINNERS:
                target_id = TRANSFER_WINNERS[k]
                winner = next((r for r in rows if r.id == target_id), rows[0])
                ghosts = [r for r in rows if r.id != winner.id]
            else:
                # Score to find winner
                rows.sort(key=score_record_as_winner, reverse=True)
                winner = rows[0]
                ghosts = rows[1:]

            for g in ghosts:
                merge_faculty_metrics_and_lists(winner, g)
                ghosts_to_archive.append(g)
                merges_count += 1

        db.commit()
        print(f"Resolved {merges_count} duplicate and transfer ghost rows.")

        archive_ids = list({g.id for g in ghosts_to_archive})
        print(f"Archiving {len(archive_ids)} ghost records into scholars_unassigned...")

        if archive_ids:
            chunk_size = 2000
            for i in range(0, len(archive_ids), chunk_size):
                chunk = archive_ids[i:i + chunk_size]
                with engine.begin() as conn:
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
                    conn.execute(
                        text("DELETE FROM public.faculties WHERE id IN :ids"),
                        {"ids": tuple(chunk)},
                    )
                print(f"  Processed {min(i + chunk_size, len(archive_ids)):,}/{len(archive_ids):,} returnees", flush=True)

    finally:
        db.close()

    # Final Verification
    with engine.connect() as conn:
        final_fac = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        final_unassigned = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
        unspecified_dept = conn.execute(text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")).scalar()

        dup_names_count = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT full_name_th FROM public.faculties
                WHERE full_name_th IS NOT NULL AND length(full_name_th) > 3
                GROUP BY full_name_th
                HAVING count(*) > 1
            ) s;
        """)).scalar()

        print(f"\n=======================================================")
        print(f"FINAL GROUNDING METRICS:")
        print(f"- Primary 'faculties' count: {final_fac:,} clean verified faculty")
        print(f"- 'scholars_unassigned' count: {final_unassigned:,}")
        print(f"- Total across both tables: {final_fac + final_unassigned:,}")
        print(f"- Unspecified department count: {unspecified_dept} (MUST BE 0)")
        print(f"- Duplicate full_name_th remaining: {dup_names_count}")
        print(f"=======================================================")

    print(f"Execution completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    resolve_remaining()
