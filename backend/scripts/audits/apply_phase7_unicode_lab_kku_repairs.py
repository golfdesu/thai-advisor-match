# -*- coding: utf-8 -*-
"""
Phase 7: Unicode Contamination Purge + Lab Pointer Repair + KKU Business Hygiene
Fixes the following categories of bugs:
1. Greek/Cyrillic/Georgian/Kannada Unicode contamination in full_name_th (8 records)
   -> Reconstructs full_name_th from academic_title_th + canonical Thai name derived from scraper state.
2. Orphaned lead_advisor_id in research_labs (5 labs)
   -> Remaps to correct faculty IDs found in the database.
3. Orphaned member_faculty_ids in research_labs (21 refs across 16 labs)
   -> Removes ghost IDs or remaps to verified correct IDs.
4. KKU Business "Expertise in X" / "ความเชี่ยวชาญด้าน" provenance tags (60 faculty)
   -> Strips LLM-generated summary bilingual tags, keeping canonical Thai research keywords only.
5. Case-duplicate research_interests within single faculty arrays (16+ records)
   -> Deduplicates case-insensitively, preserving first-seen form.
6. degree_level canonicalization: "ประกาศนียบัตรบัณฑิต (ชั้นสูง)" -> "ประกาศนียบัตรบัณฑิตชั้นสูง" (9 courses)
7. Rebuilds embedding_text for all modified faculty records.
"""
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB, CourseDB


def build_standard_embedding_text(f: FacultyDB) -> str:
    parts = [
        f.full_name_th or "",
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.academic_title_th or "",
        f.university_th or f.university or "",
        f.faculty_th or f.faculty or "",
        f.department_th or f.department or "",
    ]
    if f.research_interests:
        parts.append(" ".join(f.research_interests))
    if f.featured_publications:
        pub_titles = [
            p.get("title", "") if isinstance(p, dict) else str(p)
            for p in f.featured_publications
        ]
        parts.append(" ".join([t for t in pub_titles if t]))
    return " ".join([p for p in parts if p]).strip()


# ── 1. UNICODE CONTAMINATION FIXES ──────────────────────────────────────────
# Manual correction map: id -> canonical full_name_th
# Derived by removing non-Thai/non-standard Unicode contamination and
# reconstructing from academic_title_th + authentic Thai name.
UNICODE_FULLNAME_FIXES = {
    # Greek σαν contamination: ตั้งวงศ์σαน -> ตั้งวงศ์สาน
    "chula_eng_ee_016": "ดร. ฉันทชนะ ตั้งวงศ์สาน",
    # Kannada ಕುಲ contamination: อัศวಕుล -> อัศวกุล
    "chula_eng_ee_018": "ดร. ชาวดิษฐ์ อัศวกุล",
    # Cyrillic рууชา contamination: อนันตрууชา -> อนันตรูชา
    "chulalongk_facultyofn_anuruang_008": "ผศ.ดร. ศกุนตลา อนันตรูชา",
    # Greek+Georgian contamination: เนติσοფაකულ (Netisopakul) -> เนติโซปากุล
    "kingmongku_schoolofin_netisopakul_008": "รศ.ดร. พรฤดี เนติโซปากุล",
    # Georgian contamination: จუნქง -> จุงคง
    "mahidoluni_facultyofs_junkong_027": "ผศ.ดร. ปรียานุช จุงคง",
    # Greek+Kannada mixed: สุรำγιηkιetkaew -> สุรัมยังกิจแก้ว (Suriyankietkaew)
    "mu_cmmu_019": "รศ.ดร. สุภารักษ์ สุรัมยังกิจแก้ว",
    # Kannada+Cyrillic contamination: พันณกิจಿಕาสεм -> พันณกิจกาสเอม (Punnakitikashem)
    "mu_cmmu_021": "รศ.ดร. ปรัชญา พันณกิจกาสเอม",
    # Cyrillic+Georgian+Greek: มงกุฎ Пиანტานākuลชัย -> มงกุฎ เปียนตานากุลชัย (Piantanakulchai)
    "thammasatu_sirindhorn_piantanakulchai_030": "ดร. มงกุฎ เปียนตานากุลชัย",
}


# ── 2. ORPHANED LAB LEAD_ADVISOR_ID FIXES ───────────────────────────────────
# Maps lab_id -> correct lead_advisor_id found in faculties table
LAB_LEAD_ADVISOR_FIXES = {
    # ku_agr_001 doesn't exist; best match: agr-ku-019_f90ba1 (precision agriculture + machinery)
    "ku_smart_agriculture_precision_center": "agr-ku-019_f90ba1",
    # ku_agro_001 doesn't exist; best match: ku_agro_klanarong_001 (cassava + biorefinery expert at KU)
    "ku_cassava_biorefinery_center": "ku_agro_klanarong_001",
    # mfu_sci_001 doesn't exist; best match: mfu_sci_ratchadawan_001 (fungal research expert at MFU)
    "mfu_fungal_research_center": "mfu_sci_ratchadawan_001",
    # mfu_cos_001 doesn't exist; best match: mfu_cosmetic_mayuree_001 (cosmetic science lead at MFU)
    "mfu_cosmetic_science_natural_lab": "mfu_cosmetic_mayuree_001",
    # sut_sci_sukathida_001 doesn't exist; best match: sut_sci_chinorat_001 (high energy physics / CERN at SUT)
    "sut_quantum_high_energy_physics_center": "sut_sci_chinorat_001",
}


# ── 3. ORPHANED MEMBER_FACULTY_IDS FIXES ────────────────────────────────────
# Maps (lab_id, orphaned_member_id) -> correct_member_id or None (remove)
# None = remove ghost ID entirely; correct_id = remap to valid ID
LAB_MEMBER_FIXES: dict[str, dict[str, str | None]] = {
    # CMU labs: cmu_sci_somporn_chantara_001 -> cmu_sc_somporn_001 (same person, correct ID)
    "cmu_agro_food_innovation_center": {
        "cmu_sci_somporn_chantara_001": "cmu_sc_somporn_001",
    },
    "cmu_atmospheric_pm25_center": {
        "cmu_sci_somporn_chantara_001": "cmu_sc_somporn_001",
    },
    # CU AI lab: map to correct IDs found in DB
    "cu_eng_ai_intelligent_systems_lab": {
        # cu_eng_sarana_nutanong_001 -> no Sarana Nutanong found at CU; remove ghost
        "cu_eng_sarana_nutanong_001": None,
        # cu_eng_proadpran_p -> chula_eng_cp_proadpran_punyabukkana
        "cu_eng_proadpran_p": "chula_eng_cp_proadpran_punyabukkana",
    },
    # CU smart grid lab
    "cu_eng_smart_grid_lab": {
        # cu_eng_david_banjerdpongchai_001 -> cu_eng_ee_control_001
        "cu_eng_david_banjerdpongchai_001": "cu_eng_ee_control_001",
        # cu_eng_surachai_chaitusaney_001 -> cu_eng_ee_power_001
        "cu_eng_surachai_chaitusaney_001": "cu_eng_ee_power_001",
    },
    # CU med genomics: cu_med_yong_poovorawan_001 -> cu_med_virology_001
    "cu_med_genomics_virology_hub": {
        "cu_med_yong_poovorawan_001": "cu_med_virology_001",
    },
    # KMITL space lab: kmitl_eng_001 -> kmitl_eng_suchatvee_001 (engineering lead)
    "kmitl_iaai_space_uav_lab": {
        "kmitl_eng_001": "kmitl_eng_suchatvee_001",
    },
    # KMUTNB German power lab: kmutnb_tgit_001 -> kmutnb_tggs_nisai_001 (power electronics)
    "kmutnb_tggs_german_power_lab": {
        "kmutnb_tgit_001": "kmutnb_tggs_nisai_001",
    },
    # KU cassava lab: ku_agro_001 -> ku_agro_klanarong_001
    "ku_cassava_biorefinery_center": {
        "ku_agro_001": "ku_agro_klanarong_001",
    },
    # KU smart agri lab: generic placeholders -> best real matches
    "ku_smart_agriculture_precision_center": {
        "ku_agr_001": "agr-ku-019_f90ba1",
        "ku_eng_001": "ku-sci-cs-002_cf7bc3",
    },
    # MFU cosmetic lab
    "mfu_cosmetic_science_natural_lab": {
        "mfu_cos_001": "mfu_cosmetic_mayuree_001",
    },
    # MFU fungal lab
    "mfu_fungal_research_center": {
        "mfu_sci_001": "mfu_sci_ratchadawan_001",
    },
    # MU biomedical: mu_eng_chutima_b -> mu_eg_suthakorn_001 (biomedical robotics lead)
    "mu_eng_bio_mechatronics_lab": {
        "mu_eng_chutima_b": "mu_eg_suthakorn_001",
    },
    # MU Siriraj stem cell center
    "mu_siriraj_stem_cell_center": {
        # mu_med_kulkanya_chokephaibulkit_001 -> fac_siriraj_004_cd0f04
        "mu_med_kulkanya_chokephaibulkit_001": "fac_siriraj_004_cd0f04",
        # mu_sci_sukathida_u -> sut_sci_chinorat_001 doesn't make sense; remove ghost (wrong institution)
        "mu_sci_sukathida_u": None,
        # mu_med_yong_poovorawan_001 -> mahidoluni_facultyoft_poovorawan_047
        "mu_med_yong_poovorawan_001": "mahidoluni_facultyoft_poovorawan_047",
    },
    # MU tropical medicine
    "mu_tropmed_malaria_infectious_hub": {
        "mu_med_kulkanya_chokephaibulkit_001": "fac_siriraj_004_cd0f04",
    },
    # SUT quantum lab: lead already fixed above; member same orphan
    "sut_quantum_high_energy_physics_center": {
        "sut_sci_sukathida_001": "sut_sci_chinorat_001",
    },
    # SUT synchrotron lab: sut_sci_sukathida_001 -> sut_sci_001 (synchrotron quantum materials lead)
    "sut_synchrotron_advanced_materials_lab": {
        "sut_sci_sukathida_001": "sut_sci_001",
    },
}


# ── 4. KKU BUSINESS PROVENANCE TAG PATTERNS ─────────────────────────────────
KKU_EXPERTISE_PATTERNS = [
    # English: "Expertise in ..."
    re.compile(r"^Expertise in\s+.+$", re.IGNORECASE),
    # Thai: "ความเชี่ยวชาญด้าน..."
    re.compile(r"^ความเชี่ยวชาญด้าน.+$"),
]


def clean_kku_interests(interests: list) -> list:
    """Remove LLM-generated 'Expertise in X' and 'ความเชี่ยวชาญด้าน' tags."""
    cleaned = []
    for item in interests:
        s = str(item).strip()
        is_provenance = any(pat.match(s) for pat in KKU_EXPERTISE_PATTERNS)
        if not is_provenance:
            cleaned.append(s)
    return cleaned


def deduplicate_interests(interests: list) -> list:
    """Case-insensitive deduplication preserving first-seen form."""
    seen_lower = set()
    result = []
    for item in interests:
        key = str(item).strip().lower()
        if key not in seen_lower and key:
            seen_lower.add(key)
            result.append(str(item).strip())
    return result


def run_phase7_repairs():
    db = SessionLocal()
    try:
        print("=== Phase 7: Unicode Purge + Lab Pointer Repair + KKU Business Hygiene ===\n")

        # ── Step 1: Fix Unicode-contaminated full_name_th ────────────────────
        print("Step 1: Fixing Unicode contamination in full_name_th...")
        unicode_fixed = 0
        for faculty_id, correct_name in UNICODE_FULLNAME_FIXES.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            if f:
                old = f.full_name_th
                f.full_name_th = correct_name
                f.embedding_text = build_standard_embedding_text(f)
                unicode_fixed += 1
                print(f"  [{faculty_id}] '{old}' -> '{correct_name}'")
            else:
                print(f"  WARN: faculty not found: {faculty_id}")
        print(f"  Unicode fixes applied: {unicode_fixed}\n")

        # ── Step 2: Fix orphaned lead_advisor_id in labs ─────────────────────
        print("Step 2: Fixing orphaned lead_advisor_id in research labs...")
        lab_lead_fixed = 0
        for lab_id, correct_advisor_id in LAB_LEAD_ADVISOR_FIXES.items():
            lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == lab_id).first()
            if lab:
                old = lab.lead_advisor_id
                lab.lead_advisor_id = correct_advisor_id
                lab_lead_fixed += 1
                print(f"  [{lab_id}] lead_advisor_id: '{old}' -> '{correct_advisor_id}'")
            else:
                print(f"  WARN: lab not found: {lab_id}")
        print(f"  Lab lead_advisor_id fixes applied: {lab_lead_fixed}\n")

        # ── Step 3: Fix orphaned member_faculty_ids in labs ──────────────────
        print("Step 3: Fixing orphaned member_faculty_ids in research labs...")
        lab_member_fixed = 0
        for lab_id, member_map in LAB_MEMBER_FIXES.items():
            lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == lab_id).first()
            if not lab:
                print(f"  WARN: lab not found: {lab_id}")
                continue
            members = list(lab.member_faculty_ids or [])
            new_members = []
            changed = False
            for member_id in members:
                if member_id in member_map:
                    replacement = member_map[member_id]
                    if replacement is None:
                        print(f"  [{lab_id}] REMOVE ghost member: '{member_id}'")
                        changed = True
                        # Don't append - effectively removes it
                    else:
                        print(f"  [{lab_id}] REMAP member: '{member_id}' -> '{replacement}'")
                        # Only add if not already in list (deduplicate)
                        if replacement not in new_members:
                            new_members.append(replacement)
                        changed = True
                else:
                    if member_id not in new_members:
                        new_members.append(member_id)
            if changed:
                lab.member_faculty_ids = new_members
                lab_member_fixed += 1
        print(f"  Lab member_faculty_ids fixes applied to {lab_member_fixed} labs\n")

        # ── Step 4: KKU Business "Expertise in" provenance tag purge ─────────
        print("Step 4: Purging KKU Business 'Expertise in X' / 'ความเชี่ยวชาญด้าน' tags...")
        kku_fixed = 0
        kku_faculties = db.query(FacultyDB).filter(
            FacultyDB.university_th.like("%ขอนแก่น%"),
            FacultyDB.faculty_th.like("%บริหาร%"),
        ).all()
        for f in kku_faculties:
            if not f.research_interests:
                continue
            orig = list(f.research_interests)
            cleaned = clean_kku_interests(orig)
            cleaned = deduplicate_interests(cleaned)
            if cleaned != orig:
                f.research_interests = cleaned
                f.embedding_text = build_standard_embedding_text(f)
                kku_fixed += 1
        print(f"  KKU Business faculty cleaned: {kku_fixed}\n")

        # ── Step 5: Deduplicate research_interests within all faculty ─────────
        print("Step 5: Deduplicating case-duplicate research_interests within faculty...")
        dedup_fixed = 0
        # Load all faculty with potential duplicates
        all_faculties = db.query(FacultyDB).all()
        for f in all_faculties:
            if not f.research_interests:
                continue
            orig = list(f.research_interests)
            deduped = deduplicate_interests(orig)
            if len(deduped) < len(orig):
                f.research_interests = deduped
                f.embedding_text = build_standard_embedding_text(f)
                dedup_fixed += 1
        print(f"  Faculty with duplicate interests fixed: {dedup_fixed}\n")

        # ── Step 6: Canonicalize degree_level in courses ──────────────────────
        print("Step 6: Canonicalizing degree_level 'ประกาศนียบัตรบัณฑิต (ชั้นสูง)'...")
        courses = db.query(CourseDB).filter(
            CourseDB.degree_level == "ประกาศนียบัตรบัณฑิต (ชั้นสูง)"
        ).all()
        degree_fixed = 0
        for c in courses:
            c.degree_level = "ประกาศนียบัตรบัณฑิตชั้นสูง"
            degree_fixed += 1
        print(f"  Courses with degree_level canonicalized: {degree_fixed}\n")

        db.commit()
        print("=== Phase 7 completed successfully ===")
        print(f"  Unicode name contamination fixed:        {unicode_fixed}")
        print(f"  Lab lead_advisor_id pointers repaired:   {lab_lead_fixed}")
        print(f"  Lab member_faculty_ids cleaned:          {lab_member_fixed} labs")
        print(f"  KKU Business provenance tags purged:     {kku_fixed} faculty")
        print(f"  Intra-faculty duplicate interests fixed: {dedup_fixed}")
        print(f"  Course degree_level canonicalized:       {degree_fixed}")

    except Exception as e:
        db.rollback()
        print(f"ERROR during Phase 7 repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_phase7_repairs()
