# -*- coding: utf-8 -*-
"""
Master Nationwide Faculty Ingestion & Gemini Vector Embedding Pipeline (v2 - Extended)
Integrates:
1. Massive Batch 1: CU, MU, KU (Core Top 3)
2. Massive Batch 2: CMU, MFU, NU (Northern Regional)
3. Massive Batch 3: KMITL, KMUTT, KMUTNB (3 Phra Jom Klao)
4. Massive Batch 4: KKU, SUT (Isan Regional)
5. Massive Batch 5: PSU, TU, SWU, SU, BUU, NIDA (Southern & Central)
6. Deep CU Expansion: Chemical Engineering Catalysis, Smart Grid, BME, Cardiology, Precision Oncology, FinTech
7. Deep MU Expansion: Siriraj Laparoscopic Surgery, Stem Cells, Tropical Medicine Malaria, Cryo-EM Structural Biology, Genomics
8. Deep KU Expansion: Aerospace Additive Manufacturing, Nanocatalysis, Aquaculture Genetics, Biological Control, Agribusiness Supply Chain
9. All Pre-existing Verified Curated Batches

Generates 768-dim vector embeddings and writes to master JSON backup.
"""

import sys
import json
import logging
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service

# Import all massive faculty datasets
from scripts.data_sources.massive_faculties_batch1_cu_mu_ku import CU_MU_KU_MASSIVE_FACULTIES
from scripts.data_sources.massive_faculties_batch2_cmu_mfu_nu import CMU_MFU_NU_MASSIVE_FACULTIES
from scripts.data_sources.massive_faculties_batch3_phrajomklao import PHRA_JOM_KLAO_MASSIVE_FACULTIES
from scripts.data_sources.massive_faculties_batch4_isan_kku_sut import ISAN_REGIONAL_MASSIVE_FACULTIES
from scripts.data_sources.massive_faculties_batch5_psu_tu_swu_su_buu_nida import SOUTHERN_CENTRAL_MASSIVE_FACULTIES

# Import new Deep Expansion datasets for CU, MU, KU
from scripts.data_sources.deep_cu_faculties import CU_DEEP_EXPANSION_FACULTIES
from scripts.data_sources.deep_mu_faculties import MU_DEEP_EXPANSION_FACULTIES
from scripts.data_sources.deep_ku_faculties import KU_DEEP_EXPANSION_FACULTIES

# Import core previous datasets for complete nationwide coverage
from scripts.data_sources.tu_kku_faculties import TU_KKU_FACULTIES
from scripts.data_sources.psu_kmitl_kmutt_faculties import PSU_KMITL_KMUTT_FACULTIES
from scripts.data_sources.sut_swu_su_buu_faculties import SUT_SWU_SU_BUU_FACULTIES
from scripts.data_sources.batch2_faculties_expansion import BATCH2_FACULTIES
from scripts.expand_national_universities_complete import NATIONAL_UNIS_FACULTY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ALL_EXPANSION_BATCHES = [
    ("Deep CU Expansion (Chula Catalysis, Power, BME, Cardio, Oncology, CBS)", CU_DEEP_EXPANSION_FACULTIES),
    ("Deep MU Expansion (Siriraj Surgery, Stem Cells, Tropical Med, Cryo-EM, Genomics)", MU_DEEP_EXPANSION_FACULTIES),
    ("Deep KU Expansion (Aerospace Superalloys, CCU, Aquaculture Genetics, Agribusiness)", KU_DEEP_EXPANSION_FACULTIES),
    ("Massive Batch 1: CU, MU, KU (Core Top 3)", CU_MU_KU_MASSIVE_FACULTIES),
    ("Massive Batch 2: CMU, MFU, NU (Northern Regional)", CMU_MFU_NU_MASSIVE_FACULTIES),
    ("Massive Batch 3: KMITL, KMUTT, KMUTNB (3 Phra Jom Klao)", PHRA_JOM_KLAO_MASSIVE_FACULTIES),
    ("Massive Batch 4: KKU, SUT (Northeastern Regional)", ISAN_REGIONAL_MASSIVE_FACULTIES),
    ("Massive Batch 5: PSU, TU, SWU, SU, BUU, NIDA (Southern & Central)", SOUTHERN_CENTRAL_MASSIVE_FACULTIES),
    ("Core TU & KKU Dataset", TU_KKU_FACULTIES),
    ("Core PSU, KMITL & KMUTT Dataset", PSU_KMITL_KMUTT_FACULTIES),
    ("Core SUT, SWU, SU & BUU Dataset", SUT_SWU_SU_BUU_FACULTIES),
    ("National Outstanding Professors Batch 2", BATCH2_FACULTIES),
    ("National Universities Core Dataset", NATIONAL_UNIS_FACULTY)
]

def build_advisor_embedding_text(f: dict) -> str:
    interests = ", ".join(f.get("research_interests", []))
    education = ", ".join(f.get("education", []))
    pubs = ", ".join(f.get("featured_publications", []))
    taught = ", ".join(f.get("taught_courses", []))
    return (
        f"{f['full_name_th']} ({f.get('full_name', '')}). "
        f"Title: {f.get('academic_title_th', '')} {f.get('academic_title', '')}. "
        f"University: {f['university']} ({f['university_th']}). "
        f"Faculty: {f['faculty']} ({f['faculty_th']}). "
        f"Department: {f.get('department', '')} ({f.get('department_th', '')}). "
        f"Role: {f.get('role', '')}. "
        f"Research Interests: {interests}. "
        f"Featured Publications: {pubs}. "
        f"Education: {education}. "
        f"Taught Courses: {taught}."
    )[:6000]

def run_master_faculty_ingestion_v2():
    logger.info("==========================================================================")
    logger.info("🚀 STARTING EXTENDED NATIONWIDE FACULTY EXPANSION & EMBEDDING PIPELINE (V2)")
    logger.info("==========================================================================")

    session = SessionLocal()
    master_dict = {}

    try:
        total_batches_processed = 0
        total_upserted = 0
        total_embedded = 0

        for batch_name, batch_records in ALL_EXPANSION_BATCHES:
            logger.info(f"\n📂 Processing {batch_name} ({len(batch_records)} advisors)...")

            for item in batch_records:
                adv_id = item["id"]
                master_dict[adv_id] = item

                emb_text = build_advisor_embedding_text(item)
                existing = session.query(FacultyDB).filter_by(id=adv_id).first()

                if not existing:
                    logger.info(f"➕ [INSERT] {adv_id}: {item['full_name_th']} ({item['university_th']})")
                    emb_vec = embedding_service.get_embedding(emb_text)
                    new_adv = FacultyDB(
                        id=adv_id,
                        university=item.get("university"),
                        university_th=item.get("university_th"),
                        faculty=item.get("faculty"),
                        faculty_th=item.get("faculty_th"),
                        department=item.get("department"),
                        department_th=item.get("department_th"),
                        academic_title_th=item.get("academic_title_th"),
                        first_name=item.get("first_name"),
                        last_name=item.get("last_name"),
                        full_name_th=item.get("full_name_th"),
                        role=item.get("role"),
                        email=item.get("email"),
                        image_url=item.get("image_url"),
                        profile_url=item.get("profile_url"),
                        education=item.get("education", []),
                        research_interests=item.get("research_interests", []),
                        taught_courses=item.get("taught_courses", []),
                        featured_publications=item.get("featured_publications", []),
                        scholar_url=item.get("scholar_url"),
                        embedding_text=emb_text,
                        embedding=emb_vec if (emb_vec and len(emb_vec) == 768) else None
                    )
                    session.add(new_adv)
                    total_upserted += 1
                    if emb_vec:
                        total_embedded += 1
                else:
                    # Update fields
                    for k, v in item.items():
                        if hasattr(existing, k) and k not in ["id", "embedding"]:
                            setattr(existing, k, v)
                    existing.embedding_text = emb_text

                    if existing.embedding is None or len(existing.embedding) != 768:
                        emb_vec = embedding_service.get_embedding(emb_text)
                        if emb_vec and len(emb_vec) == 768:
                            existing.embedding = emb_vec
                            total_embedded += 1

                    logger.info(f"🔄 [UPDATE/SYNC] {adv_id}: {item['full_name_th']}")
                    total_upserted += 1

            session.commit()
            total_batches_processed += 1

        # Save JSON master archive
        output_dir = backend_dir / "data" / "courses_new"
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = output_dir / "all_faculty_advisors_nationwide.json"

        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(list(master_dict.values()), f, ensure_ascii=False, indent=2)

        logger.info("\n==========================================================================")
        logger.info("🎉 NATIONWIDE FACULTY INGESTION COMPLETE & VERIFIED (V2)")
        logger.info("==========================================================================")
        logger.info(f"Total Unique Curated Advisors : {len(master_dict)}")
        logger.info(f"Total Database Operations     : {total_upserted}")
        logger.info(f"Vectors Generated / Verified  : {total_embedded}")
        logger.info(f"💾 Master JSON Archive Saved  : {archive_path}")
        logger.info("==========================================================================")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error during master faculty ingestion: {e}", exc_info=True)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_master_faculty_ingestion_v2()
