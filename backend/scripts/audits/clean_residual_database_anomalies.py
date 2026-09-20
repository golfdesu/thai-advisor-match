"""Clean Residual Database Anomalies and Deduplicate (2026-09-13).

Autonomous, transactional script addressing residual database anomalies:
1. Bare title strings in `full_name_th` (18 records).
2. Title prefixes contaminating `first_name` (254 records).
3. Mahidol ICT "Computer Science Group" placeholder names (40 records).
4. Truncated emails, scraped sidebar boilerplate, and English academic titles.
5. Erroneous OpenAlex ID collisions and multi-faculty duplicate assignments.
6. Multi-pass deduplication of newly surfaced same-university duplicate groups.

Usage:
  python backend/scripts/audits/clean_residual_database_anomalies_2026_09_13.py [--apply]
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.university_canonicalizer import get_university_dedup_key
from app.models.schema import _strip_leading_title_tokens

UNIFIED_TITLE_RE = re.compile(
    r"^(?:(?:Assoc\.?|Asst\.?|Assist\.?|Prof\.?)\s*(?:Prof\.?\s*)?(?:Dr\.?\s*)?|Dr\.?|Mrs\.?|Mr\.?|Ms\.?|s\.)\s*",
    re.IGNORECASE,
)

CMU_CIVIL_FIRST_NAMES = {
    "cmu_eng_department_prof_34": "Chayanon",
    "cmu_eng_department_prof_37": "Teewara",
    "cmu_eng_department_prof_41": "Pitiwat",
    "cmu_eng_department_prof_51": "Songyot",
    "cmu_eng_department_prof_54": "Puttipol",
    "cmu_eng_department_prof_55": "Thanaporn",
    "cmu_eng_department_prof_57": "Pheerawat",
    "cmu_eng_department_prof_58": "Poon",
    "cmu_eng_department_prof_60": "Damrongsak",
}

SHARED_EMAIL_BLACKLIST = {
    "sci@ku.ac.th", "dent@cmu.ac.th", "civil@eng.chula.ac.th", "surgery@cmu.ac.th",
    "contact@cmu.ac.th", "info@ku.ac.th", "admin@chula.ac.th", "dean@eng.chula.ac.th",
    "water@eng.chula.ac.th", "microbiology.med@g.swu.ac.th", "medicine.med@g.swu.ac.th",
    "commarts@chula.ac.th", "cpe@eng.cmu.ac.th"
}


def is_shared_email(email: str | None) -> bool:
    if not email:
        return False
    em = email.strip().lower()
    if em in SHARED_EMAIL_BLACKLIST:
        return True
    user = em.split("@")[0]
    dept_keywords = [
        "sci", "dent", "civil", "surgery", "contact", "info", "admin", "dean", "dept", "head", "office",
        "water", "microbiology", "chem", "math", "phys", "bio", "eng", "grad", "academic", "pr", "center",
        "secretary", "med", "fvet", "vet", "agro", "econ", "pharm", "nurse", "law", "art", "ed"
    ]
    return any(user == k or user.startswith(k + ".") or user.startswith(k + "_") for k in dept_keywords)


def parse_clean_english_name(fn: str | None, ln: str | None, fid: str | None = None) -> tuple[str, str]:
    fn_clean = (fn or "").strip()
    ln_clean = (ln or "").strip()
    if not fn_clean:
        return fn_clean, ln_clean

    first_token = fn_clean.lower().split()[0]
    if first_token in (
        "prof.", "prof", "assoc.", "asst.", "dr.", "dr", "mr.", "mr", "ms.", "ms", "mrs.", "mrs", "s.",
        "assoc.prof.", "asst.prof.", "prof.dr.", "assoc.prof.dr.", "asst.prof.dr."
    ):
        full = f"{fn_clean} {ln_clean}".strip()
        cleaned = UNIFIED_TITLE_RE.sub("", full).strip()
        cleaned = re.sub(r"\s*\([^\)]+\)$", "", cleaned).strip()
        parts = cleaned.split()
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        elif len(parts) == 1:
            if fid and fid in CMU_CIVIL_FIRST_NAMES:
                return CMU_CIVIL_FIRST_NAMES[fid], parts[0]
            return fn_clean, parts[0]
    return fn_clean, ln_clean


def parse_mahidol_cs_slug(profile_url: str | None, email: str | None) -> tuple[str | None, str | None]:
    if profile_url:
        m = re.search(r"/([^/]+)/?$", profile_url.strip())
        if m:
            slug = m.group(1).replace("-", "_")
            parts = slug.split("_")
            if len(parts) >= 2:
                fn = parts[0].capitalize()
                ln = "-".join(p.capitalize() for p in parts[1:])
                return fn, ln
    if email and "@" in email:
        prefix = email.split("@")[0]
        parts = prefix.split(".")
        if len(parts) >= 2:
            fn = parts[0].capitalize()
            ln = "-".join(p.capitalize() for p in parts[1:])
            return fn, ln
    return None, None


def deduplicate_list(items: list | None) -> list:
    if not items:
        return []
    seen = set()
    result = []
    for item in items:
        if isinstance(item, dict):
            key = item.get("title") or item.get("name") or json.dumps(item, sort_keys=True)
        else:
            key = str(item).strip()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def is_pure_thai(s: str | None) -> bool:
    if not s:
        return False
    has_th = bool(re.search(r"[ก-๙]{3,}", s))
    has_foreign = bool(re.search(r"[a-zA-Z؀-ۿͰ-Ͽ]", s))
    return has_th and not has_foreign


def score_faculty(f: FacultyDB) -> tuple:
    th_score = 1000 if is_pure_thai(f.full_name_th) else 0
    has_img = 500 if f.image_url else 0
    em = (f.email or "").strip().lower()
    has_em = 300 if (em and "@" in em and not is_shared_email(em)) else 0
    has_en = 100 if (f.first_name and f.first_name.lower() not in ("none", "computer", "")) else 0
    cites = f.total_citations or 0
    pubs = len(f.featured_publications or [])
    interests = len(f.research_interests or [])
    has_oa = 50 if (f.openalex_id and f.openalex_id != "not_indexed") else 0
    return (th_score, has_img, has_em, has_en, cites, pubs, interests, has_oa)


def merge_donor(primary: FacultyDB, donor: FacultyDB, db, donor_map: dict, apply: bool):
    # Absorb pure Thai name if primary does not have it
    if not is_pure_thai(primary.full_name_th) and is_pure_thai(donor.full_name_th):
        primary.full_name_th = donor.full_name_th
    # Absorb personal email if primary lacks one or has shared
    if (not primary.email or is_shared_email(primary.email)) and (donor.email and not is_shared_email(donor.email)):
        primary.email = donor.email
    elif not primary.email and donor.email:
        primary.email = donor.email
    # Absorb URLs
    if not primary.image_url and donor.image_url:
        primary.image_url = donor.image_url
    if not primary.profile_url and donor.profile_url:
        primary.profile_url = donor.profile_url
    if not primary.scholar_url and donor.scholar_url:
        primary.scholar_url = donor.scholar_url
    if not primary.department_th and donor.department_th:
        primary.department_th = donor.department_th
    # Absorb English names
    if (not primary.first_name or primary.first_name.lower() in ("none", "computer", "")) and donor.first_name and donor.first_name.lower() not in ("none", "computer", ""):
        primary.first_name = donor.first_name
        primary.last_name = donor.last_name
    # Merge lists
    primary.featured_publications = deduplicate_list((primary.featured_publications or []) + (donor.featured_publications or []))
    primary.research_interests = deduplicate_list((primary.research_interests or []) + (donor.research_interests or []))
    primary.education = deduplicate_list((primary.education or []) + (donor.education or []))
    primary.taught_courses = deduplicate_list((primary.taught_courses or []) + (donor.taught_courses or []))
    # Max lifetime metrics
    primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
    primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
    primary.total_publications_count = max(
        primary.total_publications_count or 0,
        donor.total_publications_count or 0,
        len(primary.featured_publications)
    )
    # OpenAlex ID
    if (not primary.openalex_id or primary.openalex_id == "not_indexed") and donor.openalex_id and donor.openalex_id != "not_indexed":
        primary.openalex_id = donor.openalex_id

    donor_map[donor.id] = primary.id
    if apply:
        db.delete(donor)


def main():
    parser = argparse.ArgumentParser(description="Clean residual database anomalies and deduplicate")
    parser.add_argument("--apply", action="store_true", help="Commit changes to local database")
    args = parser.parse_args()
    apply = args.apply

    db = SessionLocal()
    audit_report = {
        "apply": apply,
        "phase1_bare_titles_cleaned": 0,
        "phase2_title_prefix_cleaned": 0,
        "phase3_mahidol_cs_cleaned": 0,
        "phase4_emails_and_boilerplate_cleaned": 0,
        "phase5_openalex_dedup_cleared": 0,
        "phase6_duplicate_donors_merged": 0,
        "merged_donor_ids": [],
    }

    print(f"=== Running Residual Database Hygiene Audit (apply={apply}) ===")

    try:
        # -------------------------------------------------------------
        # PHASE 1: Bare Title Records in full_name_th (18 records)
        # -------------------------------------------------------------
        print("\n--- Phase 1: Bare Title Records in full_name_th ---")
        bare_facs = db.query(FacultyDB).filter(FacultyDB.full_name_th.in_(["อ.", "ผศ.", "ดร.", "รศ.", "ศ."])).all()
        for f in bare_facs:
            if f.id == "kmutt_eng_wave12_0023":
                # Will be merged into kmutt_eng_cpe_025 in Phase 6
                continue
            elif f.id == "ku_agro_wave15_0045":
                f.full_name_th = "รศ.ดร. ศิริชัย ส่งเสริมพงษ์"
                f.academic_title_th = "รศ.ดร."
                audit_report["phase1_bare_titles_cleaned"] += 1
            elif f.id == "suansunand_facultyofe_fac_010_010":
                f.full_name_th = "ผศ. ช่วง อุทิศสาร"
                f.first_name = "Chouang"
                f.last_name = "Utitsarn"
                f.academic_title_th = "ผศ."
                audit_report["phase1_bare_titles_cleaned"] += 1
            else:
                # Foreign faculty
                fn = (f.first_name or "").strip()
                ln = (f.last_name or "").strip()
                title = f.full_name_th.strip()
                f.full_name_th = f"{title} {fn} {ln}".strip()
                audit_report["phase1_bare_titles_cleaned"] += 1

        print(f"Phase 1 cleaned: {audit_report['phase1_bare_titles_cleaned']} bare title records")

        # -------------------------------------------------------------
        # PHASE 2: Title Prefixes Contaminating first_name (254 records)
        # -------------------------------------------------------------
        print("\n--- Phase 2: Title Prefixes Contaminating first_name ---")
        all_facs = db.query(FacultyDB).all()
        for f in all_facs:
            fn, ln = parse_clean_english_name(f.first_name, f.last_name, f.id)
            if fn != (f.first_name or "") or ln != (f.last_name or ""):
                f.first_name = fn
                f.last_name = ln
                audit_report["phase2_title_prefix_cleaned"] += 1

        print(f"Phase 2 cleaned: {audit_report['phase2_title_prefix_cleaned']} English names")

        # -------------------------------------------------------------
        # PHASE 3: Mahidol ICT "Computer Science Group" Placeholders (40 records)
        # -------------------------------------------------------------
        print("\n--- Phase 3: Mahidol ICT 'Computer Science Group' Placeholders ---")
        mu_cs = db.query(FacultyDB).filter(
            FacultyDB.first_name == "Computer",
            FacultyDB.last_name == "Science Group"
        ).all()
        for f in mu_cs:
            fn, ln = parse_mahidol_cs_slug(f.profile_url, f.email)
            if fn and ln:
                f.first_name = fn
                f.last_name = ln
                audit_report["phase3_mahidol_cs_cleaned"] += 1
            # Check for concatenated Thai name
            if f.full_name_th == "รศ.ดร. ชมทิพพรพนมชัย":
                f.full_name_th = "รศ.ดร. ชมทิพ พรพนมชัย"

        print(f"Phase 3 cleaned: {audit_report['phase3_mahidol_cs_cleaned']} Mahidol ICT faculty")

        # -------------------------------------------------------------
        # PHASE 4: Truncated Emails, Scraped Boilerplate, & Titles
        # -------------------------------------------------------------
        print("\n--- Phase 4: Truncated Emails & Scraped Boilerplate ---")
        truncated_email_map = {
            "su_eng_teacher_020": "ssonwai@su.ac.th",
            "su_eng_teacher_110": "nitipongsopon@hotmail.com",
            "su_eng_teacher_051": "wanida@su.ac.th",
            "cmu_6e46b7bf_1635": "nabhat.noparat@cmu.ac.th",
        }
        for fid, clean_em in truncated_email_map.items():
            fac = db.query(FacultyDB).filter_by(id=fid).first()
            if fac:
                fac.email = clean_em
                audit_report["phase4_emails_and_boilerplate_cleaned"] += 1

        # Chula Worasinchai
        chula_wora = db.query(FacultyDB).filter_by(id="chulalongk_facultyofa_worasinchai_013").first()
        if chula_wora:
            chula_wora.email = "worasilchai.navaporn1@gmail.com"
            chula_wora.department_th = "ภาควิชาเวชศาสตร์การธนาคารเลือดและจุลชีววิทยาคลินิก"
            chula_wora.education = []
            audit_report["phase4_emails_and_boilerplate_cleaned"] += 1

        # KU Econ degree suffix
        ku_econ_72 = db.query(FacultyDB).filter_by(id="ku_wave17_econ_0072").first()
        if ku_econ_72 and ku_econ_72.education:
            clean_edu = []
            for item in ku_econ_72.education:
                clean_edu.append(item.replace(". Email, 2013", ", 2013"))
            ku_econ_72.education = clean_edu
            audit_report["phase4_emails_and_boilerplate_cleaned"] += 1

        # Standardize English academic titles in academic_title_th
        title_map = {
            "Assoc. Prof. Dr.": "รศ.ดร.",
            "Dr.": "ดร.",
            "Prof. Dr.": "ศ.ดร.",
            "Mr.": "อ.",
            "รองศาสตราจารย์ ดร.": "รศ.ดร.",
            "ผู้ช่วยศาสตราจารย์ ดร.": "ผศ.ดร.",
            "ศาสตราจารย์ ดร.": "ศ.ดร.",
            "รองศาสตราจารย์": "รศ.",
            "ผู้ช่วยศาสตราจารย์": "ผศ.",
            "อาจารย์ ดร.": "อ.ดร.",
            "อาจารย์": "อ.",
            "ศาสตราจารย์": "ศ.",
        }
        for old_t, new_t in title_map.items():
            matching = db.query(FacultyDB).filter_by(academic_title_th=old_t).all()
            for m in matching:
                m.academic_title_th = new_t
                audit_report["phase4_emails_and_boilerplate_cleaned"] += 1

        print(f"Phase 4 cleaned: {audit_report['phase4_emails_and_boilerplate_cleaned']} items")

        # -------------------------------------------------------------
        # PHASE 5: OpenAlex ID Collisions and Multi-Faculty Assignments
        # -------------------------------------------------------------
        print("\n--- Phase 5: OpenAlex Disambiguation & Deduplication ---")
        # 1. Reset false positive collision between distinct KU faculty
        for fid in ["ku_wave17_bus_0018", "ku_wave17_bus_0006"]:
            f = db.query(FacultyDB).filter_by(id=fid).first()
            if f and f.openalex_id:
                f.openalex_id = "not_indexed"
                audit_report["phase5_openalex_dedup_cleared"] += 1

        # 2. For any remaining duplicate OpenAlex IDs across faculty rows,
        # retain the ID on the primary winner and clear on others
        from sqlalchemy import func
        dup_oa_ids = db.query(FacultyDB.openalex_id, func.count(FacultyDB.id)).filter(
            FacultyDB.openalex_id.isnot(None),
            FacultyDB.openalex_id != "not_indexed",
            FacultyDB.openalex_id != ""
        ).group_by(FacultyDB.openalex_id).having(func.count(FacultyDB.id) > 1).all()

        for oa_id, _ in dup_oa_ids:
            candidates = db.query(FacultyDB).filter_by(openalex_id=oa_id).all()
            if len(candidates) > 1:
                # Rank candidates: highest score wins
                candidates.sort(key=score_faculty, reverse=True)
                winner = candidates[0]
                for loser in candidates[1:]:
                    loser.openalex_id = "not_indexed"
                    audit_report["phase5_openalex_dedup_cleared"] += 1

        print(f"Phase 5 cleared: {audit_report['phase5_openalex_dedup_cleared']} conflicting OpenAlex assignments")

        # -------------------------------------------------------------
        # PHASE 6: Multi-Pass Faculty Deduplication
        # -------------------------------------------------------------
        print("\n--- Phase 6: Multi-Pass Faculty Deduplication ---")
        donor_to_primary_map = {}

        # List of confirmed duplicate pairs to merge: (primary_candidate, donor_candidate)
        duplicate_pairs = [
            # Newly surfaced from English Title / Mahidol CS group cleaning
            ("chula_eng_ee_012", "cu_cbs_wave11_0067"),
            ("cu_eng_wave13_b_0031", "cu_cbs_wave11_0187"),
            ("ict-mu-001_0465c9", "mu_7a75b2ac_6924"),
            ("ict-mu-006_a63bc5", "mu_1dab4358_2501"),
            ("ict-mu-020_81a17c", "mu_5a63549c_1772"),
            ("eg-cpe-002_1bffad", "mu_1ddd658b_5810"),
            ("ict-mu-015_1b7624", "mu_1e4815bc_7992"),
            ("mu_ict_haddawy_001", "mu_26ff7e8e_6388"),
            ("mu_ict_vasaka_001", "mu_419eaa18_1626"),
            ("kmutt_eng_cpe_025", "kmutt_eng_wave12_0023"),

            # Confirmed same-university personal email pairs
            ("kmutt_eng_cpe_027", "kmutt_eng_wave12_0024"),
            ("kmutt_eng_cpe_012", "kmutt_eng_wave12_0012"),
            ("kmutt_eng_cpe_018", "kmutt_eng_wave12_0018"),
            ("kmutt_eng_cpe_020", "kmutt_eng_wave12_0020"),
            ("kmutt_eng_cpe_004", "kmutt_eng_wave12_0003"),
            ("kmutt_eng_cpe_003", "kmutt_eng_wave12_0004"),
            ("kmutt_eng_cpe_014", "kmutt_eng_wave12_0014"),
            ("kmutt_eng_cpe_007", "kmutt_eng_wave12_0007"),
            ("kmutt_eng_cpe_016", "kmutt_eng_wave12_0016"),
            ("kmutt_eng_cpe_002", "kmutt_eng_wave12_0002"),
            ("kmutt_eng_cpe_019", "kmutt_eng_wave12_0019"),
            ("kmutt_eng_cpe_008", "kmutt_eng_wave12_0008"),
            ("kmutt_eng_cpe_013", "kmutt_eng_wave12_0013"),
            ("kmutt_eng_cpe_021", "kmutt_eng_wave12_0021"),
            ("kmutt_eng_cpe_022", "kmutt_eng_wave12_0022"),
            ("chula_eng_cp_proadpran_punyabukkana", "chula_eng_cp_073"),
            ("chulalongk_facultyofc_srisarakham_003", "cu_1000de72_8342"),
            ("econ-cu-004_938ed4", "cu_wave19_econ_0012"),
            ("cu_ahs_wanida_001", "cu_ahs_wave15_0034"),
            ("chula_eng_ee_053", "cu_eng_wave13_0056"),
            ("chula_eng_ee_054", "cu_eng_wave13_0055"),
            ("psu_eng_001", "psu_eng_wave11_0037"),
            ("psu_eng_nattha_001", "psu_eng_wave11_0041"),
            ("kku_sci_sakda_001", "kku_pharm_wave16_0059"),
            ("mu_pt_jarugool_001", "mahidoluni_facultyofp_trisiriluck_035"),
            ("ku-vet-010_a2a88b", "ku_forest_wave15_0016"),
            ("regionalun_facultymem_phuttawong_001", "nu_panu_puttawong_5884"),
            ("cmu_7b85461a_4378", "khonkaenun_facultyofm_fac_015_015"),

            # Confirmed Thai transliteration & variant pairs
            ("cmu_pharm_jiradech_001", "cmu_pharm_jiradej_001"),
            ("chulalongk_facultyofv_kaewamatawong_119", "chulalongk_facultyofv_kaewamatawong_106"),
            ("chulalongk_facultyofv_sawangmek_173", "chulalongk_facultyofv_fac_165_165"),
            ("chulalongk_facultyofv_asvasanti_100", "chulalongk_facultyofv_asvakajorn_075"),
            ("chulalongk_facultyofv_klanthararaktho_077", "chulalongk_facultyofv_kladkarnontthon_067"),
            ("cu_vet_achariya_001", "chulalongk_facultyofv_alaisoot_104"),
            ("chulalongk_facultyofv_yibchokanun_168", "chulalongk_facultyofv_fac_162_162"),
            ("chulalongk_facultyofv_thitwatcharapor_102", "chulalongk_facultyofv_thitiwat_072"),
            ("fca-cu-003_8bdcee", "cu_11c43117_9754"),
            ("chulalongk_facultyofp_thitaphiwatnaku_020", "cu_pharm_wave16_0067"),
            ("srinakhari_facultyofe_ltkittikoonrung_006", "srinakhari_facultyofe_fac_075_075"),
            ("kku_eng_sirapat_001", "kku_comp_siripat_001"),
            ("kku_sci_lamyai_001", "khonkaenun_facultyofs_neeratpanphun_014"),
            ("tu_bus_tbs_035", "thammasatu_thammasatb_fac_058_058"),
            ("cmu-sci-003_c7c75f", "cmu_5a5a78f1_1778"),
            ("cmu-eng-009_045df0", "cmu_eng_department_sakgasit_105"),
            ("cu_3708922f_5923", "cu_5308f228_0188"),
            ("ict-mu-016_c09b72", "mu_7ebe2db5_5857"),
        ]

        for id1, id2 in duplicate_pairs:
            f1 = db.query(FacultyDB).filter_by(id=id1).first()
            f2 = db.query(FacultyDB).filter_by(id=id2).first()
            if not f1 or not f2:
                continue

            # Determine primary vs donor
            s1 = score_faculty(f1)
            s2 = score_faculty(f2)
            primary = f1 if s1 >= s2 else f2
            donor = f2 if s1 >= s2 else f1

            merge_donor(primary, donor, db, donor_to_primary_map, apply)
            audit_report["phase6_duplicate_donors_merged"] += 1
            audit_report["merged_donor_ids"].append({"primary": primary.id, "donor": donor.id})

        print(f"Phase 6 merged: {audit_report['phase6_duplicate_donors_merged']} donor faculty")

        # -------------------------------------------------------------
        # Re-point any Research Lab lead_advisor_ids
        # -------------------------------------------------------------
        if donor_to_primary_map:
            labs = db.query(ResearchLabDB).all()
            repointed_labs = 0
            for lab in labs:
                if lab.lead_advisor_id in donor_to_primary_map:
                    lab.lead_advisor_id = donor_to_primary_map[lab.lead_advisor_id]
                    repointed_labs += 1
            if repointed_labs:
                print(f"Re-pointed {repointed_labs} research lab lead_advisor_id references")

        if apply:
            db.commit()
            print("\n>>> All changes successfully COMMITTED to local database! <<<")
        else:
            db.rollback()
            print("\n>>> Dry-run complete. No changes were committed. Use --apply to execute. <<<")

        # Save checkpoint audit state
        state_path = backend_dir / "data" / "agent_states" / "db_residual_hygiene_2026_09_13.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(audit_report, f, ensure_ascii=False, indent=2)
        print(f"Saved audit state to: {state_path}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: Transaction aborted due to exception: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
