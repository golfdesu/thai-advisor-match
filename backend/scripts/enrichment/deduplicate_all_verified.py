# -*- coding: utf-8 -*-
"""
Phase 3: High-Fidelity Deduplication & Foreign Key Consolidation
Merges duplicate faculty in KU, CMU, and CU adhering to Section 9 Invariant 10:
- Retains max(total_citations), max(h_index), max(works_count)
- Unions list supersets (research_interests, featured_publications, education)
- Dynamically re-points research_labs.lead_advisor_id
- Deletes donor records
- Checkpoints state to disk
"""
import os
import sys
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService

STATE_CHECKPOINT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "skill_state_dedup_resolved.json")

# Verified (survivor_id, donor_id, reason)
MERGE_PAIRS = [
    # KU (1 pair)
    ("ku-vet-010_a2a88b", "kasetsartu_facultyofa_fac_019_019", "KU Vet Natthasit Tansakul"),

    # CMU (5 pairs)
    ("cmu-med-011_ba4c79", "cmu_44bea860_4246", "CMU Med Surapan Khunamornpong"),
    ("cmu-sci-012_aa3b4c", "cmu_4610e0bb_2017", "CMU Sci Prasit Wangpakapattanawong"),
    ("cmu_560364fa_6439", "cmu_215d93ff_5129", "CMU Med Penpitcha Rojpibulsathit"),
    ("cmu_d542da29_8423", "wave21_0004_860", "CMU Agro Tri Indrarini Wirjantoro"),
    ("cmu_dent_anak_001", "cmu_103fe821_4247", "CMU Dent Anak Iamaroon"),

    # CU (18 pairs)
    ("md-chula-009_4672bf", "mahidoluni_facultyofm_pisitkun_018", "CU Med Trairak Pisitkun"),
    ("chulalongk_facultyofs_fac_005_005", "cu_cbs_wave11_0324", "CU Sci Chatchawan Chaisuekul"),
    ("cu_sci_wave14_b_0060", "chulalongk_facultyofs_fac_015_015", "CU Sci Supawan Tantayanon"),
    ("cu_ppc_pramoch_001", "wave30_0079_843", "CU PPC Pramoch Rangsunvigit"),
    ("chulalongk_facultyofv_bintvihok_170", "chulalongk_facultyofv_fac_160_160", "CU Vet Anong Bintvihok"),
    ("fca-cu-005_ad2cae", "cu_22cda09a_8885", "CU CommArts Jessada Salathong"),
    ("chulalongk_facultyofv_nuntaphaitoon_092", "wave30_0084_952", "CU Vet Morakot Nuntaphaitoon"),

    # CU Public Health wave30 intra-faculty duplicates
    ("wave30_0054_565", "wave30_0073_153", "CU Public Health Montakarn Chuemchit"),
    ("wave30_0056_614", "wave30_0074_550", "CU Public Health Nutta Taneepanichskul"),
    ("wave30_0059_226", "wave30_0075_792", "CU Public Health Pokkate Wongsasuluk"),
    ("wave30_0060_848", "wave30_0076_969", "CU Public Health Pramon Viwattanakulvanid"),
    ("wave30_0063_450", "wave30_0079_634", "CU Public Health Anuchit Phanumartwiwath"),
    ("wave30_0065_670", "wave30_0077_267", "CU Public Health Nuchanad Hounnaklang"),
    ("wave30_0066_534", "wave30_0081_112", "CU Public Health Narumol Bhummaphan"),
    ("wave30_0067_643", "wave30_0082_828", "CU Public Health May Chan Oo"),
    ("wave30_0069_680", "wave30_0088_818", "CU Public Health Ratana Somrongthong"),
    ("wave30_0070_930", "wave30_0094_739", "CU Public Health Usaneya Perngparn"),
    ("wave30_0071_680", "wave30_0095_921", "CU Public Health Khemika Yamarat"),
]

def merge_faculty(db, embedder, survivor_id, donor_id, reason):
    survivor = db.query(FacultyDB).filter(FacultyDB.id == survivor_id).first()
    donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()

    if not survivor or not donor:
        print(f"  [Skip] Missing record for {reason}: survivor={bool(survivor)}, donor={bool(donor)}")
        return False

    # 1. Authoritative metrics: retain max
    survivor.total_citations = max(survivor.total_citations or 0, donor.total_citations or 0)
    survivor.h_index = max(survivor.h_index or 0, donor.h_index or 0)
    if hasattr(survivor, "i10_index") and hasattr(donor, "i10_index"):
        survivor.i10_index = max(survivor.i10_index or 0, donor.i10_index or 0)
    if hasattr(survivor, "works_count") and hasattr(donor, "works_count"):
        survivor.works_count = max(survivor.works_count or 0, donor.works_count or 0)

    # 2. Lists: union supersets
    def union_lists(l1, l2):
        res = []
        for x in (l1 or []) + (l2 or []):
            if x and x not in res:
                res.append(x)
        return res

    survivor.research_interests = union_lists(survivor.research_interests, donor.research_interests)
    survivor.featured_publications = union_lists(survivor.featured_publications, donor.featured_publications)
    survivor.education = union_lists(survivor.education, donor.education)

    # 3. Scalar fields: fallback to richer values
    if (not survivor.email or "@" not in survivor.email) and (donor.email and "@" in donor.email):
        survivor.email = donor.email
    if (not survivor.department_th or survivor.department_th in ["None", "ภาควิชาของคณะฯ", survivor.faculty_th]) and donor.department_th:
        survivor.department_th = donor.department_th
    if (not survivor.academic_title_th or survivor.academic_title_th in ["None", "อ."]) and donor.academic_title_th:
        survivor.academic_title_th = donor.academic_title_th
    if not survivor.image_url and donor.image_url:
        survivor.image_url = donor.image_url
    if not survivor.profile_url and donor.profile_url:
        survivor.profile_url = donor.profile_url

    # 4. Re-point research labs
    labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).all()
    for lab in labs:
        lab.lead_advisor_id = survivor.id
        print(f"    Re-pointed lab {lab.id} to survivor {survivor.id}")

    # 5. Recompute canonical embedding
    survivor.embedding_text = build_faculty_embedding_text(survivor)
    survivor.embedding = embedder.get_embedding(survivor.embedding_text)

    # 6. Delete donor
    db.delete(donor)
    print(f"  ✓ Merged {reason}: {donor_id} -> {survivor_id} (Citations: {survivor.total_citations}, h-index: {survivor.h_index})")
    return True

def main():
    print("=================================================================")
    print("🚀 PHASE 3: HIGH-FIDELITY FACULTY DEDUPLICATION & RE-INDEXING")
    print("=================================================================")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db = SessionLocal()
    embedder = EmbeddingService()

    success_count = 0
    merged_records = []

    for s_id, d_id, reason in MERGE_PAIRS:
        ok = merge_faculty(db, embedder, s_id, d_id, reason)
        if ok:
            success_count += 1
            merged_records.append({"survivor_id": s_id, "donor_id": d_id, "reason": reason})

    db.commit()
    print(f"\n✅ Successfully merged {success_count} / {len(MERGE_PAIRS)} duplicate pairs across KU, CMU, and CU!")

    # Checkpoint state to disk
    os.makedirs(os.path.dirname(STATE_CHECKPOINT_PATH), exist_ok=True)
    with open(STATE_CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "merged_count": success_count,
            "pairs": merged_records
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved to: {STATE_CHECKPOINT_PATH}")

    db.close()

if __name__ == "__main__":
    main()
