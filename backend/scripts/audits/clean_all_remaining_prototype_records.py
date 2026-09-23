# -*- coding: utf-8 -*-
"""
Clean All Remaining Prototype Synthetic Faculty Records & Deduplicate
======================================================================
1. Archive 89 unindexed synthetic prototype records ending with _[0-9a-f]{6}$
   to public.scholars_unassigned and remove them from public.faculties.

2. Relocate or merge 9 cross-university scholars to their true universities
   (e.g. Thammasat, Chulalongkorn, CMU, Kasetsart, KMITL, PSU, KKU).

3. Ground and clean the 252 remaining authentic scholars at their current university:
   - Purge synthetic education fields to '[]'::json.
   - Clean synthetic placeholder emails.
   - Assign clean canonical IDs.
   - Re-generate embedding_text and 768-dim vector embeddings via embedding_service.

4. Fix OpenAlex duplicate clusters & faculty charter violations:
   - Re-map khon_reloc_sansri_026: faculty_th = 'วิทยาลัยการปกครองท้องถิ่น', department_th = 'สาขาวิชารัฐประศาสนศาสตร์'
   - Merge mu_w57_6608_146 into mu_sports__018 (Ampika Nanbancha)
   - Merge mu_w57_7025_208 into mu_sports__015 (Alisa Nana)
   - Archive stou_law__0125 in favor of wu_w51_1489_708 (Siwarut Laikram at Walailak)
   - Merge assu_reloc_porntrakoon_98bfc8 into au_vmes__0161 (Paitoon Porntrakoon at AU)
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
SCRIPTS_DIR = BACKEND_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from app.core.embedding_text import build_faculty_embedding_text
from scripts.audits.clean_prototype_synthetic_faculties import slugify, INST_TO_THAI_UNIV
from scripts.audits.audit_openalex_affiliations import match_thai_univ


def run_clean_all():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING FINAL COMPREHENSIVE CLEANUP OF ALL PROTOTYPE RECORDS", flush=True)
    print("=================================================================", flush=True)

    cache_file = BACKEND_DIR / "data" / "agent_states" / "openalex_affiliations_cache.json"
    cache = {}
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)

    db = SessionLocal()
    try:
        # -------------------------------------------------------------
        # 1. Classify all remaining records ending with _[0-9a-f]{6}$
        # -------------------------------------------------------------
        rows = db.query(FacultyDB).filter(FacultyDB.id.op("~")("_[0-9a-f]{6}$")).all()
        print(f"Total prototype records to process: {len(rows)}", flush=True)

        to_archive = []
        to_relocate = []
        to_ground = []

        for r in rows:
            oaid = r.openalex_id
            if not oaid or oaid == "not_indexed":
                to_archive.append(r)
                continue

            meta = cache.get(oaid, {})
            lkis = meta.get("last_known_institutions", [])
            assigned_u = r.university_th

            found_assigned = any(
                match_thai_univ(l.get("display_name")) and match_thai_univ(l.get("display_name"))[0] == assigned_u
                for l in lkis
            )

            if found_assigned or not lkis:
                to_ground.append(r)
            else:
                target_u = None
                for l in lkis:
                    m = match_thai_univ(l.get("display_name"))
                    if m and m[0] != assigned_u:
                        target_u = m
                        break
                if target_u:
                    to_relocate.append((r, target_u))
                else:
                    to_ground.append(r)

        print(f"Classification Results:", flush=True)
        print(f"  - Archive to scholars_unassigned: {len(to_archive)} records", flush=True)
        print(f"  - Relocate to true university:    {len(to_relocate)} records", flush=True)
        print(f"  - Ground at current university:   {len(to_ground)} records", flush=True)

        # -------------------------------------------------------------
        # 2. Archive Unindexed Synthetic Records to scholars_unassigned
        # -------------------------------------------------------------
        print("\n--- 2. Archiving Synthetic Records to scholars_unassigned ---", flush=True)
        archive_ids = [r.id for r in to_archive]
        if archive_ids:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO public.scholars_unassigned
                        SELECT * FROM public.faculties
                        WHERE id = ANY(:ids)
                        ON CONFLICT (id) DO UPDATE SET
                            full_name_th = EXCLUDED.full_name_th,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            university_th = EXCLUDED.university_th,
                            university = EXCLUDED.university,
                            faculty_th = EXCLUDED.faculty_th,
                            faculty = EXCLUDED.faculty,
                            department_th = EXCLUDED.department_th,
                            department = EXCLUDED.department,
                            academic_title_th = EXCLUDED.academic_title_th,
                            email = EXCLUDED.email,
                            total_citations = EXCLUDED.total_citations,
                            h_index = EXCLUDED.h_index,
                            openalex_id = EXCLUDED.openalex_id;
                    """),
                    {"ids": archive_ids},
                )
                conn.execute(
                    text("DELETE FROM public.faculties WHERE id = ANY(:ids)"),
                    {"ids": archive_ids},
                )
            print(f"✅ Successfully archived and removed {len(archive_ids)} synthetic records.", flush=True)

        # -------------------------------------------------------------
        # 3. Relocate or Merge Cross-University Scholars
        # -------------------------------------------------------------
        print("\n--- 3. Relocating & Grounding Scholars to True University ---", flush=True)
        for r, (target_u_th, target_u_en) in to_relocate:
            clean_name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.)\s*", "", r.full_name_th).strip()
            existing = (
                db.query(FacultyDB)
                .filter(
                    FacultyDB.university_th == target_u_th,
                    FacultyDB.full_name_th.like(f"%{clean_name}%"),
                    FacultyDB.id != r.id,
                )
                .first()
            )
            if existing:
                print(f"  Merging duplicate {r.full_name_th} ({r.id}) into {existing.id} at {target_u_th}", flush=True)
                existing.total_citations = max(existing.total_citations or 0, r.total_citations or 0)
                existing.h_index = max(existing.h_index or 0, r.h_index or 0)
                if not existing.openalex_id and r.openalex_id:
                    existing.openalex_id = r.openalex_id
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM public.faculties WHERE id = :id"), {"id": r.id})
                continue

            old_uni = r.university_th
            old_id = r.id
            uni_prefix = slugify(target_u_en.split()[0])[:4]
            name_slug = slugify(r.last_name or r.first_name or "scholar")[:12]
            suffix = old_id.split("_")[-1][:6]
            new_id = f"{uni_prefix}_reloc_{name_slug}_{suffix}"

            r.university_th = target_u_th
            r.university = target_u_en
            r.email = None
            emb_text = build_faculty_embedding_text(r)
            vec = embedding_service.get_embedding(emb_text)

            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE public.faculties
                        SET id = :new_id,
                            university_th = :target_u_th,
                            university = :target_u_en,
                            email = NULL,
                            education = CAST('[]' AS json),
                            embedding_text = :emb_text,
                            embedding = CAST(:vec AS vector)
                        WHERE id = :old_id
                    """),
                    {
                        "new_id": new_id,
                        "target_u_th": target_u_th,
                        "target_u_en": target_u_en,
                        "emb_text": emb_text,
                        "vec": str(vec),
                        "old_id": old_id,
                    }
                )
            print(f"  Relocated: {r.full_name_th} ({old_uni} -> {target_u_th}) -> ID: {new_id}", flush=True)

        # -------------------------------------------------------------
        # 4. Ground Remaining Authentic Scholars at Current University
        # -------------------------------------------------------------
        print("\n--- 4. Grounding Remaining Scholars at Current University ---", flush=True)
        t0 = time.time()
        for idx, r in enumerate(to_ground, 1):
            old_id = r.id
            uni_prefix = slugify(r.university.split()[0] if r.university else "univ")[:4]
            name_slug = slugify(r.last_name or r.first_name or "faculty")[:12]
            suffix = old_id.split("_")[-1][:6]
            new_id = f"{uni_prefix}_ground_{name_slug}_{suffix}"

            # Check ID collision
            existing_check = db.query(FacultyDB.id).filter(FacultyDB.id == new_id, FacultyDB.id != old_id).first()
            if existing_check:
                new_id = f"{new_id}_{idx}"

            r.email = None
            emb_text = build_faculty_embedding_text(r)
            vec = embedding_service.get_embedding(emb_text)

            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE public.faculties
                        SET id = :new_id,
                            email = NULL,
                            profile_url = :profile_url,
                            education = CAST('[]' AS json),
                            embedding_text = :emb_text,
                            embedding = CAST(:vec AS vector)
                        WHERE id = :old_id
                    """),
                    {
                        "new_id": new_id,
                        "profile_url": r.openalex_id or None,
                        "emb_text": emb_text,
                        "vec": str(vec),
                        "old_id": old_id,
                    }
                )

            if idx % 50 == 0 or idx == len(to_ground):
                elapsed = time.time() - t0
                print(f"  [{idx}/{len(to_ground)}] Grounded {r.full_name_th} ({elapsed:.1f}s)", flush=True)

        print(f"✅ Successfully grounded all {len(to_ground)} retained scholars.", flush=True)

        # -------------------------------------------------------------
        # 5. Fix OpenAlex Duplicate Clusters & Charter Violations
        # -------------------------------------------------------------
        print("\n--- 5. Fixing OpenAlex Duplicate Clusters & Charter Violations ---", flush=True)

        # 5.1 KKU Political Science -> College of Local Administration
        rakpong = db.query(FacultyDB).filter(FacultyDB.id == "khon_reloc_sansri_026").first()
        if rakpong:
            rakpong.faculty_th = "วิทยาลัยการปกครองท้องถิ่น"
            rakpong.faculty = "College of Local Administration"
            rakpong.department_th = "สาขาวิชารัฐประศาสนศาสตร์"
            rakpong.department = "Department of Public Administration"
            db.commit()
            print("  - Fixed KKU: ผศ.ดร. รักพงษ์ แสนศรี -> วิทยาลัยการปกครองท้องถิ่น", flush=True)

        # 5.2 Merge Ampika Nanbancha (mu_w57_6608_146 -> mu_sports__018)
        ampika_primary = db.query(FacultyDB).filter(FacultyDB.id == "mu_sports__018").first()
        ampika_ghost = db.query(FacultyDB).filter(FacultyDB.id == "mu_w57_6608_146").first()
        if ampika_primary and ampika_ghost:
            ampika_primary.total_citations = max(ampika_primary.total_citations or 0, ampika_ghost.total_citations or 0)
            ampika_primary.h_index = max(ampika_primary.h_index or 0, ampika_ghost.h_index or 0)
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'mu_w57_6608_146' ON CONFLICT (id) DO NOTHING"))
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'mu_w57_6608_146'"))
            print("  - Merged Ampika Nanbancha (mu_w57_6608_146 -> mu_sports__018)", flush=True)

        # 5.3 Merge Alisa Nana (mu_w57_7025_208 -> mu_sports__015)
        alisa_primary = db.query(FacultyDB).filter(FacultyDB.id == "mu_sports__015").first()
        alisa_ghost = db.query(FacultyDB).filter(FacultyDB.id == "mu_w57_7025_208").first()
        if alisa_primary and alisa_ghost:
            alisa_primary.total_citations = max(alisa_primary.total_citations or 0, alisa_ghost.total_citations or 0)
            alisa_primary.h_index = max(alisa_primary.h_index or 0, alisa_ghost.h_index or 0)
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'mu_w57_7025_208' ON CONFLICT (id) DO NOTHING"))
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'mu_w57_7025_208'"))
            print("  - Merged Alisa Nana (mu_w57_7025_208 -> mu_sports__015)", flush=True)

        # 5.4 Archive stou_law__0125 in favor of wu_w51_1489_708 (Siwarut Laikram)
        siwarut_wu = db.query(FacultyDB).filter(FacultyDB.id == "wu_w51_1489_708").first()
        if siwarut_wu:
            siwarut_wu.full_name_th = "รศ. ศิวรุฒ ลายคราม"
            siwarut_wu.academic_title_th = "รศ."
            siwarut_wu.first_name = "Siwarut"
            siwarut_wu.last_name = "Laikram"
            db.commit()
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'stou_law__0125' ON CONFLICT (id) DO NOTHING"))
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'stou_law__0125'"))
            print("  - Consolidated Siwarut Laikram at Walailak (archived stou_law__0125)", flush=True)

        # 5.5 Merge Paitoon Porntrakoon (assu_reloc_porntrakoon_98bfc8 -> au_vmes__0161)
        paitoon_primary = db.query(FacultyDB).filter(FacultyDB.id == "au_vmes__0161").first()
        paitoon_ghost = db.query(FacultyDB).filter(FacultyDB.id == "assu_reloc_porntrakoon_98bfc8").first()
        if paitoon_primary and paitoon_ghost:
            paitoon_primary.full_name_th = "ผศ.ดร. ไพฑูรย์ พรตระกูล"
            paitoon_primary.academic_title_th = "ผศ.ดร."
            paitoon_primary.total_citations = max(paitoon_primary.total_citations or 0, paitoon_ghost.total_citations or 0)
            paitoon_primary.h_index = max(paitoon_primary.h_index or 0, paitoon_ghost.h_index or 0)
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO public.scholars_unassigned SELECT * FROM public.faculties WHERE id = 'assu_reloc_porntrakoon_98bfc8' ON CONFLICT (id) DO NOTHING"))
                conn.execute(text("DELETE FROM public.faculties WHERE id = 'assu_reloc_porntrakoon_98bfc8'"))
            print("  - Merged Paitoon Porntrakoon (assu_reloc_porntrakoon_98bfc8 -> au_vmes__0161)", flush=True)

        db.commit()
        print("\n🎉 ALL PROTOTYPE RECORDS CLEANED AND ALL CLUSTERS HARMONIZED!", flush=True)

    finally:
        db.close()


if __name__ == "__main__":
    run_clean_all()
