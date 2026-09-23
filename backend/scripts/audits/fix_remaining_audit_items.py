# -*- coding: utf-8 -*-
"""
Fix Remaining Audit Items & Duplicate Clusters
==============================================
1. KKU: Rakpong Sansri -> วิทยาลัยการปกครองท้องถิ่น
2. Merge Ampika Nanbancha (mu_w57_6608_146 -> mu_sports__018)
3. Merge Alisa Nana (mu_w57_7025_208 -> mu_sports__015)
4. Siwarut Laikram at Walailak (archive stou_law__0125)
5. Merge Paitoon Porntrakoon (assu_reloc_porntrakoon_98bfc8 -> au_vmes__0161)
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine

def main():
    with engine.begin() as conn:
        # 1. KKU: Rakpong Sansri
        conn.execute(text("""
            UPDATE public.faculties
            SET faculty_th = 'วิทยาลัยการปกครองท้องถิ่น',
                faculty = 'College of Local Administration',
                department_th = 'สาขาวิชารัฐประศาสนศาสตร์',
                department = 'Department of Public Administration'
            WHERE id = 'khon_reloc_sansri_026';
        """))
        print("1. Rakpong Sansri updated to COLA KKU")

        # 2. Merge Ampika Nanbancha (mu_w57_6608_146 -> mu_sports__018)
        conn.execute(text("""
            INSERT INTO public.scholars_unassigned
            SELECT * FROM public.faculties WHERE id = 'mu_w57_6608_146'
            ON CONFLICT (id) DO NOTHING;
        """))
        conn.execute(text("DELETE FROM public.faculties WHERE id = 'mu_w57_6608_146';"))
        print("2. Ampika Nanbancha merged/archived")

        # 3. Merge Alisa Nana (mu_w57_7025_208 -> mu_sports__015)
        conn.execute(text("""
            INSERT INTO public.scholars_unassigned
            SELECT * FROM public.faculties WHERE id = 'mu_w57_7025_208'
            ON CONFLICT (id) DO NOTHING;
        """))
        conn.execute(text("DELETE FROM public.faculties WHERE id = 'mu_w57_7025_208';"))
        print("3. Alisa Nana merged/archived")

        # 4. Siwarut Laikram at Walailak (archive stou_law__0125)
        conn.execute(text("""
            UPDATE public.faculties
            SET full_name_th = 'รศ. ศิวรุฒ ลายคราม',
                academic_title_th = 'รศ.',
                first_name = 'Siwarut',
                last_name = 'Laikram'
            WHERE id = 'wu_w51_1489_708';
        """))
        conn.execute(text("""
            INSERT INTO public.scholars_unassigned
            SELECT * FROM public.faculties WHERE id = 'stou_law__0125'
            ON CONFLICT (id) DO NOTHING;
        """))
        conn.execute(text("DELETE FROM public.faculties WHERE id = 'stou_law__0125';"))
        print("4. Siwarut Laikram consolidated")

        # 5. Merge Paitoon Porntrakoon (assu_reloc_porntrakoon_98bfc8 & assu_ground_porntrakoon_98bfc8 -> au_vmes__0161)
        conn.execute(text("""
            UPDATE public.faculties
            SET full_name_th = 'ผศ.ดร. ไพฑูรย์ พรตระกูล',
                academic_title_th = 'ผศ.ดร.'
            WHERE id = 'au_vmes__0161';
        """))
        conn.execute(text("""
            INSERT INTO public.scholars_unassigned
            SELECT * FROM public.faculties WHERE id IN ('assu_reloc_porntrakoon_98bfc8', 'assu_ground_porntrakoon_98bfc8')
            ON CONFLICT (id) DO NOTHING;
        """))
        conn.execute(text("DELETE FROM public.faculties WHERE id IN ('assu_reloc_porntrakoon_98bfc8', 'assu_ground_porntrakoon_98bfc8');"))
        print("5. Paitoon Porntrakoon merged/archived")

        # 6. Archive kase_ground_namwong_59147a in favor of stou_agriculture__0248
        conn.execute(text("""
            INSERT INTO public.scholars_unassigned
            SELECT * FROM public.faculties WHERE id = 'kase_ground_namwong_59147a'
            ON CONFLICT (id) DO NOTHING;
        """))
        conn.execute(text("DELETE FROM public.faculties WHERE id = 'kase_ground_namwong_59147a';"))
        print("6. Sirilak Namwong consolidated at STOU")

        # 7. Update Pisal Yenradee at Thammasat to SIIT
        conn.execute(text("""
            UPDATE public.faculties
            SET faculty_th = 'สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)',
                faculty = 'Sirindhorn International Institute of Technology (SIIT)',
                department_th = 'สาขาวิชาวิศวกรรมอุตสาหการและระบบโลจิสติกส์',
                department = 'Industrial Engineering and Logistics Systems',
                email = 'pisal@siit.tu.ac.th'
            WHERE id = 'tham_reloc_yenradee_ea1e71';
        """))
        print("7. Pisal Yenradee updated to SIIT")

    print("\n✅ All 5 audit and duplicate cluster fixes committed successfully!")

if __name__ == "__main__":
    main()
