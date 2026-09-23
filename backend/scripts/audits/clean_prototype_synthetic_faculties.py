# -*- coding: utf-8 -*-
"""
Clean Prototype Synthetic Faculty Records
=========================================
1. Re-point research labs referencing prototype IDs:
   - ku_genomics_bioeconomy_center -> ku_agr_sutkhet_nakasathien_001
   - cmu_atmospheric_pm25_center -> cmu_sci_somporn_chantara_001
   - ku_smart_agriculture_precision_center -> ku_wave18_engkps_0017 (ศ.ดร. อนุพันธ์ เทอดวงศ์วรกุล)

2. Archive ~299 unindexed / fabricated records to public.scholars_unassigned
   and remove them from public.faculties.

3. Relocate ~35 scholars whose OpenAlex affiliation demonstrates they belong to another university.
   - Ground their university_th, university, faculty_th to their true institution.
   - Clean synthetic placeholder emails, profiles, and education.
   - Assign clean canonical IDs.

4. Retain ~150 authentic scholars at their current university.
   - Clean synthetic placeholder emails, profiles, and education.
   - Assign clean canonical IDs.

5. Synchronize embedding_text and vector embeddings for all modified records.
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
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_service import embedding_service
from fetch_openalex_publication_metrics import fetch_with_retry

INST_TO_THAI_UNIV = {
    "Chulalongkorn University": ("จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University"),
    "Chiang Mai University": ("มหาวิทยาลัยเชียงใหม่", "Chiang Mai University"),
    "Kasetsart University": ("มหาวิทยาลัยเกษตรศาสตร์", "Kasetsart University"),
    "Mahidol University": ("มหาวิทยาลัยมหิดล", "Mahidol University"),
    "Thammasat University": ("มหาวิทยาลัยธรรมศาสตร์", "Thammasat University"),
    "Khon Kaen University": ("มหาวิทยาลัยขอนแก่น", "Khon Kaen University"),
    "Prince of Songkla University": ("มหาวิทยาลัยสงขลานครินทร์", "Prince of Songkla University"),
    "King Mongkut's Institute of Technology Ladkrabang": ("สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "King Mongkut's Institute of Technology Ladkrabang"),
    "King Mongkut's University of Technology Thonburi": ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี", "King Mongkut's University of Technology Thonburi"),
    "King Mongkut's University of Technology North Bangkok": ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "King Mongkut's University of Technology North Bangkok"),
    "Suranaree University of Technology": ("มหาวิทยาลัยเทคโนโลยีสุรนารี", "Suranaree University of Technology"),
    "Mae Fah Luang University": ("มหาวิทยาลัยแม่ฟ้าหลวง", "Mae Fah Luang University"),
    "National Institute of Development Administration": ("สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)", "National Institute of Development Administration"),
    "Srinakharinwirot University": ("มหาวิทยาลัยศรีนครินทรวิโรฒ", "Srinakharinwirot University"),
    "Silpakorn University": ("มหาวิทยาลัยศิลปากร", "Silpakorn University"),
    "Burapha University": ("มหาวิทยาลัยบูรพา", "Burapha University"),
    "Ubon Ratchathani University": ("มหาวิทยาลัยอุบลราชธานี", "Ubon Ratchathani University"),
    "University of Phayao": ("มหาวิทยาลัยพะเยา", "University of Phayao"),
    "Maejo University": ("มหาวิทยาลัยแม่โจ้", "Maejo University"),
    "Walailak University": ("มหาวิทยาลัยวลัยลักษณ์", "Walailak University"),
    "Assumption University": ("มหาวิทยาลัยอัสสัมชัญ", "Assumption University"),
    "Sukhothai Thammathirat Open University": ("มหาวิทยาลัยสุโขทัยธรรมาธิราช", "Sukhothai Thammathirat Open University"),
}


def slugify(text_in: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", (text_in or "").strip().lower()).strip("_")
    return s[:30]


def run_clean_prototype_synthetic():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING COMPLETE PROTOTYPE SYNTHETIC FACULTY CLEANUP", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # -------------------------------------------------------------
        # 1. Re-point Research Labs
        # -------------------------------------------------------------
        print("\n--- 1. Re-pointing Research Labs ---", flush=True)
        lab_updates = [
            ("ku_genomics_bioeconomy_center", "ku_agr_sutkhet_nakasathien_001"),
            ("cmu_atmospheric_pm25_center", "cmu_sci_somporn_chantara_001"),
            ("ku_smart_agriculture_precision_center", "ku_wave18_engkps_0017"),
        ]
        for lab_id, target_adv_id in lab_updates:
            lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == lab_id).first()
            if lab:
                old_adv = lab.lead_advisor_id
                lab.lead_advisor_id = target_adv_id
                print(f"  Lab {lab_id}: {old_adv} -> {target_adv_id}", flush=True)
        db.commit()

        # -------------------------------------------------------------
        # 2. Identify and Classify all 484 Prototype Records
        # -------------------------------------------------------------
        print("\n--- 2. Classifying 484 Prototype Records via OpenAlex ---", flush=True)
        rows = db.query(FacultyDB).filter(
            FacultyDB.id.op("~")("^[a-z]+-[a-z]+-[0-9]+_[0-9a-f]{6}$")
        ).all()
        print(f"Total prototype records found in database: {len(rows)}", flush=True)

        to_archive = []
        to_relocate = []
        to_keep = []

        for f in rows:
            oaid = f.openalex_id
            if not oaid or oaid == "not_indexed":
                to_archive.append((f, "unindexed_synthetic"))
                continue

            oaid_short = oaid.split("/")[-1]
            data = fetch_with_retry(f"https://api.openalex.org/authors/{oaid_short}")
            if not data:
                to_archive.append((f, "fetch_failed"))
                continue

            last_insts = [inst.get("display_name") for inst in (data.get("last_known_institutions") or [])]
            matched_univ_th = None
            matched_univ_en = None
            for inst_name in last_insts:
                if not inst_name:
                    continue
                for eng_name, (th_u, en_u) in INST_TO_THAI_UNIV.items():
                    if eng_name.lower() in inst_name.lower():
                        matched_univ_th = th_u
                        matched_univ_en = en_u
                        break
                if matched_univ_th:
                    break

            if matched_univ_th == f.university_th:
                to_keep.append((f, data))
            elif matched_univ_th:
                to_relocate.append((f, matched_univ_th, matched_univ_en, data))
            else:
                # If foreign or unlisted institution, check citation credibility
                if (f.total_citations or 0) > 10:
                    to_keep.append((f, data))
                else:
                    to_archive.append((f, f"unknown_institution_{last_insts}"))

        print(f"Classification Results:", flush=True)
        print(f"  - Archive to scholars_unassigned: {len(to_archive)} records", flush=True)
        print(f"  - Keep at current university:     {len(to_keep)} records", flush=True)
        print(f"  - Relocate to true university:    {len(to_relocate)} records", flush=True)

        # -------------------------------------------------------------
        # 3. Archive Unindexed / Fabricated Records to scholars_unassigned
        # -------------------------------------------------------------
        print("\n--- 3. Archiving Synthetic Records to scholars_unassigned ---", flush=True)
        archive_ids = [f.id for f, _ in to_archive]
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
        # 4. Relocate Authentic Scholars to True University & Clean
        # -------------------------------------------------------------
        print("\n--- 4. Relocating & Grounding Scholars to True University ---", flush=True)
        for f, new_u_th, new_u_en, oa_data in to_relocate:
            clean_name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", f.full_name_th).strip()
            existing = (
                db.query(FacultyDB)
                .filter(
                    FacultyDB.university_th == new_u_th,
                    FacultyDB.full_name_th.like(f"%{clean_name}%"),
                    FacultyDB.id != f.id,
                )
                .first()
            )
            if existing:
                print(f"  Merging duplicate {f.full_name_th} ({f.id}) into existing {existing.id} at {new_u_th}", flush=True)
                existing.total_citations = max(existing.total_citations or 0, f.total_citations or 0)
                existing.h_index = max(existing.h_index or 0, f.h_index or 0)
                if not existing.openalex_id and f.openalex_id:
                    existing.openalex_id = f.openalex_id
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM public.faculties WHERE id = :id"), {"id": f.id})
                continue

            old_uni = f.university_th
            old_id = f.id

            # Generate new clean ID
            uni_prefix = slugify(new_u_en.split()[0])[:4]
            name_slug = slugify(f.last_name or f.first_name or "scholar")[:12]
            new_id = f"{uni_prefix}_reloc_{name_slug}_{old_id.split('_')[-1]}"

            # Update embedding text
            emb_text = f"{f.full_name_th} {f.first_name or ''} {f.last_name or ''} {new_u_th} {new_u_en} {f.faculty_th or ''} {f.department_th or ''} {' '.join(f.research_interests or [])}"
            vec = embedding_service.get_embedding(emb_text)

            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE public.faculties
                        SET id = :new_id,
                            university_th = :new_u_th,
                            university = :new_u_en,
                            email = NULL,
                            profile_url = :profile_url,
                            education = CAST('[]' AS json),
                            embedding_text = :emb_text,
                            embedding = CAST(:vec AS vector)
                        WHERE id = :old_id
                    """),
                    {
                        "new_id": new_id,
                        "new_u_th": new_u_th,
                        "new_u_en": new_u_en,
                        "profile_url": f.openalex_id or None,
                        "emb_text": emb_text,
                        "vec": str(vec),
                        "old_id": old_id,
                    },
                )
            print(f"  Relocated: {f.full_name_th} ({old_uni} -> {new_u_th}) ID: {new_id}", flush=True)

        # -------------------------------------------------------------
        # 5. Ground Remaining Authentic Scholars at Current University
        # -------------------------------------------------------------
        print("\n--- 5. Grounding Remaining Scholars at Current University ---", flush=True)
        for f, oa_data in to_keep:
            old_id = f.id
            edu_json = "[]"

            # Special canonical IDs for lab heads
            if old_id == "agr-ku-001_0458e1":
                new_id = "ku_agr_sutkhet_nakasathien_001"
                edu_json = json.dumps([
                    "Ph.D. (Crop Physiology), North Carolina State University (NCSU), USA",
                    "M.S. (Agronomy), North Carolina State University (NCSU), USA",
                    "B.Sc. (Agronomy), Kasetsart University"
                ], ensure_ascii=False)
            elif old_id == "cmu-sci-021_f78748":
                new_id = "cmu_sci_somporn_chantara_001"
                edu_json = json.dumps([
                    "Ph.D. in Environmental Science, University of East Anglia, UK",
                    "M.Sc. in Chemistry, Chiang Mai University",
                    "B.Sc. in Chemistry, Chiang Mai University"
                ], ensure_ascii=False)
            else:
                uni_prefix = slugify(f.university.split()[0] if f.university else "univ")[:4]
                name_slug = slugify(f.last_name or f.first_name or "faculty")[:12]
                new_id = f"{uni_prefix}_ground_{name_slug}_{old_id.split('_')[-1]}"

            # Update embedding text
            emb_text = f"{f.full_name_th} {f.first_name or ''} {f.last_name or ''} {f.university_th} {f.university} {f.faculty_th or ''} {f.department_th or ''} {' '.join(f.research_interests or [])}"
            vec = embedding_service.get_embedding(emb_text)

            with engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE public.faculties
                        SET id = :new_id,
                            email = NULL,
                            profile_url = :profile_url,
                            education = CAST(:edu_json AS json),
                            embedding_text = :emb_text,
                            embedding = CAST(:vec AS vector)
                        WHERE id = :old_id
                    """),
                    {
                        "new_id": new_id,
                        "profile_url": f.openalex_id or None,
                        "edu_json": edu_json,
                        "emb_text": emb_text,
                        "vec": str(vec),
                        "old_id": old_id,
                    },
                )

        print("✅ Grounded and updated all retained scholars.", flush=True)

    finally:
        db.close()

    print("\n🎉 Complete cleanup of prototype synthetic records finished successfully!", flush=True)


if __name__ == "__main__":
    run_clean_prototype_synthetic()
