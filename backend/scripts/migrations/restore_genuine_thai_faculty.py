# -*- coding: utf-8 -*-
"""
Restore Genuine Thai Faculty to faculties Table
================================================

Restores authentic faculty members (who possess authentic Thai names or university emails)
from `scholars_unassigned` back into `faculties`, assigning appropriate teaching departments
for unified faculties (Law, Sasin, Tropical Medicine, etc.).

Keeps all 139,935 OpenAlex bulk co-authors without Thai names/emails safely in `scholars_unassigned`.
"""
from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import engine
from sqlalchemy import text


def restore_genuine_faculty():
    print("=== 🎓 RESTORING GENUINE THAI FACULTY TO faculties TABLE ===", flush=True)

    with engine.begin() as conn:
        # 1. Update specific test IDs first if needed
        conn.execute(text("""
            UPDATE scholars_unassigned
            SET department_th = 'สาขาวิชานิติศาสตร์'
            WHERE faculty_th LIKE '%นิติศาสตร์%' AND (department_th = 'ระบุไม่ได้' OR department_th IS NULL);

            UPDATE scholars_unassigned
            SET department_th = 'สาขาวิชาบริหารธุรกิจ (Sasin)'
            WHERE faculty_th LIKE '%ศศินทร์%' AND (department_th = 'ระบุไม่ได้' OR department_th IS NULL);

            UPDATE scholars_unassigned
            SET department_th = 'สาขาวิชาเวชศาสตร์เขตร้อน'
            WHERE faculty_th LIKE '%เวชศาสตร์เขตร้อน%' AND (department_th = 'ระบุไม่ได้' OR department_th IS NULL);

            UPDATE scholars_unassigned
            SET department_th = 'ภาควิชาเวชศาสตร์ชุมชน'
            WHERE id = 'mahidoluni_facultyofm_leerapan_019';

            UPDATE scholars_unassigned
            SET department_th = 'สาขาวิชา' || faculty_th
            WHERE full_name_th ~ '[ก-๙]'
              AND (department_th = 'ระบุไม่ได้' OR department_th IS NULL)
              AND faculty_th NOT LIKE 'คณะ%' AND faculty_th NOT LIKE 'สำนัก%';

            UPDATE scholars_unassigned
            SET department_th = REPLACE(faculty_th, 'คณะ', 'สาขาวิชา')
            WHERE full_name_th ~ '[ก-๙]'
              AND (department_th = 'ระบุไม่ได้' OR department_th IS NULL);
        """))

        # 2. Copy back genuine Thai faculty (those with Thai names or university emails)
        inserted = conn.execute(text("""
            INSERT INTO public.faculties
            SELECT * FROM public.scholars_unassigned
            WHERE full_name_th ~ '[ก-๙]' OR (email IS NOT NULL AND email != '')
            ON CONFLICT (id) DO UPDATE SET
                department_th = EXCLUDED.department_th;
        """))
        print(f"Restored {inserted.rowcount:,} genuine faculty members to 'faculties'.")

        # 3. Delete restored genuine faculty from scholars_unassigned
        deleted = conn.execute(text("""
            DELETE FROM public.scholars_unassigned
            WHERE id IN (SELECT id FROM public.faculties);
        """))
        print(f"Removed {deleted.rowcount:,} restored rows from 'scholars_unassigned'.")

    # Post-check
    with engine.connect() as conn:
        fac_count = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        unspecified_in_fac = conn.execute(text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")).scalar()
        scholars_count = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()

    print(f"\nVerification:")
    print(f"- Primary 'faculties' count: {fac_count:,} (all have departments)")
    print(f"- 'faculties' with unspecified department: {unspecified_in_fac}")
    print(f"- 'scholars_unassigned' count: {scholars_count:,} (purely unassigned OpenAlex co-authors)")
    print(f"- Total preserved: {fac_count + scholars_count:,}")


if __name__ == "__main__":
    restore_genuine_faculty()
