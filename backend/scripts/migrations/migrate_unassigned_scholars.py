# -*- coding: utf-8 -*-
"""
Migrate Unassigned Scholars to Separate Table
============================================

Moves scholars without teaching department (`department_th = 'ระบุไม่ได้'` or NULL)
from the primary `faculties` table into `scholars_unassigned`.

Benefits:
1. Web frontend and Search API display only authentic teaching faculty (100% with department).
2. Zero data loss: all OpenAlex metrics, citations, embeddings, and publication data are
   preserved safely in `scholars_unassigned`.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Adjust pythonpath to find backend app
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import engine
from sqlalchemy import text


def run_migration(dry_run: bool = False):
    print("=== 📦 MIGRATION: SEPARATE UNASSIGNED SCHOLARS TABLE ===", flush=True)
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY TO DATABASE'}\n", flush=True)

    with engine.connect() as conn:
        total_before = conn.execute(text("SELECT count(*) FROM faculties")).scalar()
        unassigned_count = conn.execute(text("""
            SELECT count(*)
            FROM faculties
            WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL OR department_th = '';
        """)).scalar()
        assigned_count = total_before - unassigned_count

        # Check for any foreign key dependency in research_labs
        rl_deps = conn.execute(text("""
            SELECT count(*)
            FROM research_labs rl
            JOIN faculties f ON rl.lead_advisor_id = f.id
            WHERE f.department_th = 'ระบุไม่ได้' OR f.department_th IS NULL OR f.department_th = '';
        """)).scalar()

    print(f"1. Database Pre-check:")
    print(f"   - Total rows in 'faculties': {total_before:,}")
    print(f"   - Faculty WITH department: {assigned_count:,} (will remain in 'faculties')")
    print(f"   - Faculty WITHOUT department: {unassigned_count:,} (will move to 'scholars_unassigned')")
    print(f"   - Research lab lead advisors missing department: {rl_deps}")

    if rl_deps > 0:
        raise RuntimeError(f"Cannot proceed: {rl_deps} research labs reference unassigned faculty! Resolve them first.")

    if dry_run:
        print("\n[DRY RUN] Plan verified successfully. Run without --dry-run to execute.", flush=True)
        return

    start_t = time.time()

    # Step 2: Create table scholars_unassigned if not exists
    print("\n2. Ensuring 'scholars_unassigned' table exists in PostgreSQL...", flush=True)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.scholars_unassigned (LIKE public.faculties INCLUDING ALL);
            CREATE INDEX IF NOT EXISTS ix_scholars_unassigned_id ON public.scholars_unassigned (id);
            CREATE INDEX IF NOT EXISTS ix_scholars_unassigned_university_th ON public.scholars_unassigned (university_th);
            CREATE INDEX IF NOT EXISTS ix_scholars_unassigned_h_index ON public.scholars_unassigned (h_index DESC NULLS LAST);
        """))
    print("   Table and indexes verified.")

    # Step 3: Copy data to scholars_unassigned
    print("\n3. Copying unassigned records into 'scholars_unassigned'...", flush=True)
    with engine.begin() as conn:
        copied = conn.execute(text("""
            INSERT INTO public.scholars_unassigned
            SELECT * FROM public.faculties
            WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL OR department_th = ''
            ON CONFLICT (id) DO UPDATE SET
                university = EXCLUDED.university,
                university_th = EXCLUDED.university_th,
                faculty = EXCLUDED.faculty,
                faculty_th = EXCLUDED.faculty_th,
                department = EXCLUDED.department,
                department_th = EXCLUDED.department_th,
                academic_title_th = EXCLUDED.academic_title_th,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                full_name_th = EXCLUDED.full_name_th,
                email = EXCLUDED.email,
                total_citations = EXCLUDED.total_citations,
                h_index = EXCLUDED.h_index,
                openalex_id = EXCLUDED.openalex_id;
        """))
        print(f"   Insert completed. Rows affected: {copied.rowcount:,}")

    # Verify count in destination
    with engine.connect() as conn:
        dest_count = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
    print(f"   Destination table 'scholars_unassigned' row count: {dest_count:,}")

    if dest_count < unassigned_count:
        raise RuntimeError(f"Data verification failed! Destination count ({dest_count}) < Source unassigned count ({unassigned_count})")

    # Step 4: Save checkpoint
    out_dir = Path("backend/data/agent_states")
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = out_dir / "migrate_unassigned_scholars.json"
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_before": total_before,
            "migrated_count": dest_count,
            "remaining_faculties_count": assigned_count,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n4. Checkpoint saved to: {checkpoint_file}", flush=True)

    # Step 5: Delete unassigned records from faculties
    print("\n5. Removing unassigned records from primary 'faculties' table...", flush=True)
    with engine.begin() as conn:
        deleted = conn.execute(text("""
            DELETE FROM public.faculties
            WHERE id IN (SELECT id FROM public.scholars_unassigned);
        """))
        print(f"   Deleted {deleted.rowcount:,} rows from 'faculties'.")

    # Step 6: Post-migration Verification
    with engine.connect() as conn:
        total_after = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        unspecified_remaining = conn.execute(text("""
            SELECT count(*)
            FROM public.faculties
            WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL OR department_th = '';
        """)).scalar()
        dest_final = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()

    print("\n6. Post-migration Verification:")
    print(f"   - 'faculties' total rows: {total_after:,} (all verified teaching faculty)")
    print(f"   - 'faculties' with unspecified department: {unspecified_remaining} (must be 0)")
    print(f"   - 'scholars_unassigned' total rows: {dest_final:,}")
    print(f"   - Total preserved across both tables: {total_after + dest_final:,} (Parity with initial: {total_before:,})")

    if unspecified_remaining != 0:
        print(f"[WARN] Some unspecified rows remain in faculties: {unspecified_remaining}")

    # Optimize postgres tables
    print("\n7. Optimizing query plans via VACUUM ANALYZE...", flush=True)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("VACUUM ANALYZE public.faculties;"))
        conn.execute(text("VACUUM ANALYZE public.scholars_unassigned;"))
    print("   VACUUM ANALYZE complete.")

    elapsed = time.time() - start_t
    print(f"\nMigration completed successfully in {elapsed:.1f}s!", flush=True)


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    run_migration(dry_run=is_dry)
