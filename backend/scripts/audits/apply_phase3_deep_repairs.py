# -*- coding: utf-8 -*-
"""
Phase 3 Deep Database Hygiene Repairs.
Applies:
1. Resolution of 41 KMUTT relative image URLs with authentic base domains (mic.kmutt.ac.th, chem.kmutt.ac.th).
2. ResearchLab lead_advisor_id and member_faculty_ids foreign key repairs for Silpakorn & NIDA labs.
3. Standardization of 501 long full-word academic titles in full_name_th to canonical contracted titles.
4. Removal of junk tokens ('-', '?', 'null', 'ไม่มี') from research_interests across 59 faculty records.
5. Re-attribution of misattributed symposium/committee scraper faculties (CMU and Thammasat faculty).
6. Deduplication merge of 7 cross-institution duplicate pairs between Chula and Silpakorn scraper artifacts.
7. Restoration of missing surname for Walailak Law lecturer (ผศ.ดร. วชิราภรณ์ พลวัต).
8. Regeneration of embedding_text for all mutated faculties (Text-Vector Symmetry Invariant).
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
from app.models.db_models import FacultyDB, ResearchLabDB
from sqlalchemy.orm.attributes import flag_modified


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


def apply_phase3_deep_repairs():
    db = SessionLocal()
    print("=" * 70)
    print("🚀 EXECUTING PHASE 3 DEEP DATABASE REPAIRS")
    print("=" * 70)

    try:
        # -------------------------------------------------------------
        # 1. RESOLVE KMUTT RELATIVE IMAGE URLS (41 records)
        # -------------------------------------------------------------
        print("\n--- 1. RESOLVING KMUTT RELATIVE IMAGE URLS ---")
        rel_facs = db.query(FacultyDB).filter(FacultyDB.image_url.like("/%")).all()
        fixed_urls = 0
        for f in rel_facs:
            old_url = f.image_url
            if f.department_th == "ภาควิชาจุลชีววิทยา":
                f.image_url = f"https://mic.kmutt.ac.th{old_url}"
                fixed_urls += 1
            elif f.department_th == "ภาควิชาเคมี":
                f.image_url = f"https://chem.kmutt.ac.th{old_url}"
                fixed_urls += 1
            else:
                # Fallback to general KMUTT domain if another dept
                f.image_url = f"https://www.kmutt.ac.th{old_url}"
                fixed_urls += 1
        print(f"Fixed {fixed_urls} relative image URLs to absolute HTTPS origins.")

        # -------------------------------------------------------------
        # 2. RESEARCH LAB LEAD ADVISOR RE-POINTING (3 Labs)
        # -------------------------------------------------------------
        print("\n--- 2. RE-POINTING RESEARCH LAB LEAD ADVISORS ---")
        lab_repairs = [
            ("su_pharm_drug_delivery_lab", "su_pharm_praneet_001"),
            ("su_eng_biopolymer_advanced_materials", "su_eng_teacher_074"),
            ("nida_bigdata_social_innovation", "nida_as_analytics_002"),
        ]
        for lab_id, target_lead_id in lab_repairs:
            lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == lab_id).first()
            if lab:
                old_lead = lab.lead_advisor_id
                lab.lead_advisor_id = target_lead_id
                lab.member_faculty_ids = [target_lead_id]
                flag_modified(lab, "member_faculty_ids")
                print(f"Lab '{lab.id}' ({lab.name_th}): re-pointed lead_advisor_id '{old_lead}' -> '{target_lead_id}'")

        # -------------------------------------------------------------
        # 3. STANDARDIZE FULL-WORD ACADEMIC TITLES IN full_name_th (501 records)
        # -------------------------------------------------------------
        print("\n--- 3. STANDARDIZING ACADEMIC TITLES IN full_name_th ---")
        long_title_patterns = [
            (re.compile(r"^ศาสตราจารย์\s+ดร\.\s*", re.I), "ศ.ดร. "),
            (re.compile(r"^รองศาสตราจารย์\s+ดร\.\s*", re.I), "รศ.ดร. "),
            (re.compile(r"^ผู้ช่วยศาสตราจารย์\s+ดร\.\s*", re.I), "ผศ.ดร. "),
            (re.compile(r"^ศาสตราจารย์\s+", re.I), "ศ. "),
            (re.compile(r"^รองศาสตราจารย์\s+", re.I), "รศ. "),
            (re.compile(r"^ผู้ช่วยศาสตราจารย์\s+", re.I), "ผศ. "),
            (re.compile(r"^อาจารย์\s+ดร\.\s*", re.I), "อ.ดร. "),
            (re.compile(r"^อาจารย์\s+", re.I), "อ. "),
        ]
        all_facs = db.query(FacultyDB).all()
        contracted_count = 0
        for f in all_facs:
            orig_name = f.full_name_th or ""
            new_name = orig_name
            for pat, rep in long_title_patterns:
                if pat.search(new_name):
                    new_name = pat.sub(rep, new_name)
                    break
            if new_name != orig_name:
                f.full_name_th = new_name
                f.embedding_text = build_standard_embedding_text(f)
                contracted_count += 1
        print(f"Contracted full-word academic titles to canonical abbreviations in {contracted_count} records.")

        # -------------------------------------------------------------
        # 4. STRIP JUNK RESEARCH INTERESTS (59 records)
        # -------------------------------------------------------------
        print("\n--- 4. STRIPPING JUNK RESEARCH INTERESTS ---")
        junk_pat = re.compile(r"^(ไม่มี|none|-|n/a|\.|null|undefined|\?)$", re.I)
        cleaned_int_count = 0
        for f in all_facs:
            if f.research_interests:
                clean_ints = [x.strip() for x in f.research_interests if not junk_pat.match(x.strip())]
                if len(clean_ints) != len(f.research_interests):
                    f.research_interests = clean_ints
                    flag_modified(f, "research_interests")
                    f.embedding_text = build_standard_embedding_text(f)
                    cleaned_int_count += 1
        print(f"Stripped junk tokens from research_interests in {cleaned_int_count} records.")

        # -------------------------------------------------------------
        # 5. RESTORE WALAILAK LAW LECTURER SURNAME (1 record)
        # -------------------------------------------------------------
        print("\n--- 5. RESTORING WALAILAK LAW LECTURER SURNAME ---")
        wu_law = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_fac_050_050").first()
        if wu_law:
            wu_law.full_name_th = "ผศ.ดร. วชิราภรณ์ พลวัต"
            wu_law.first_name = "Wachiraporn"
            wu_law.last_name = "Ponlawat"
            wu_law.faculty_th = "สำนักวิชานิติศาสตร์"
            wu_law.academic_title_th = "ผศ.ดร."
            wu_law.embedding_text = build_standard_embedding_text(wu_law)
            print("Restored: regionalun_facultymem_fac_050_050 -> ผศ.ดร. วชิราภรณ์ พลวัต (สำนักวิชานิติศาสตร์ ม.วลัยลักษณ์)")

        # -------------------------------------------------------------
        # 6. FIX SCRAPER COMMITTEE MISATTRIBUTIONS (Thammasat & Standalone CMU)
        # -------------------------------------------------------------
        print("\n--- 6. FIXING SCRAPER COMMITTEE MISATTRIBUTIONS ---")
        # 6.1 Thammasat Journalism
        tu_updates = [
            ("chulalongk_facultyofc_hinwiman_018", "มหาวิทยาลัยธรรมศาสตร์", "คณะวารสารศาสตร์และสื่อสารมวลชน", "กลุ่มวิชาการสื่อสารมวลชน"),
            ("chulalongk_facultyofc_saengsingkeo_003", "มหาวิทยาลัยธรรมศาสตร์", "คณะวารสารศาสตร์และสื่อสารมวลชน", "กลุ่มวิชาการสื่อสารมวลชน"),
            ("chulalongk_facultyofc_ronawech_005", "มหาวิทยาลัยธรรมศาสตร์", "คณะวารสารศาสตร์และสื่อสารมวลชน", "กลุ่มวิชาการสื่อสารมวลชน"),
        ]
        for fid, uni, fac, dept in tu_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed TU: {fid} ({f.full_name_th}) -> {uni}, {fac}")

        # 6.2 Standalone CMU faculty misattributed to Chula or Silpakorn
        cmu_updates = [
            ("chulalongk_facultyofc_promyiam_026", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาภาษาไทย"),
            ("chulalongk_facultyofc_nanthasri_025", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาภาษาตะวันตกและภาษาศาสตร์"),
            ("silpakornu_facultyoff_rattakanok_028", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาภาษาไทย"),
            ("silpakornu_facultyoff_channgam_030", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาปรัชญาและศาสนา"),
            ("silpakornu_facultyoff_pattiya_029", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาประวัติศาสตร์"),
        ]
        for fid, uni, fac, dept in cmu_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed CMU: {fid} ({f.full_name_th}) -> {uni}, {fac}")

        # -------------------------------------------------------------
        # 7. MERGE 7 CHULA-SILPAKORN DUPLICATE PAIRS TO CANONICAL CMU
        # -------------------------------------------------------------
        print("\n--- 7. MERGING 7 CHULA-SILPAKORN DUPLICATE PAIRS TO CMU ---")
        # (donor_chula_id, keeper_su_id, uni, fac, dept)
        cmu_duplicate_pairs = [
            (
                "chulalongk_facultyofc_santasombat_009",
                "silpakornu_facultyoff_santasombat_031",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะสังคมศาสตร์",
                "ภาควิชาสังคมวิทยาและมานุษยวิทยา",
            ),
            (
                "chulalongk_facultyofc_chansong_027",
                "silpakornu_facultyoff_chansong_026",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะมนุษยศาสตร์",
                "ภาควิชาปรัชญาและศาสนา",
            ),
            (
                "chulalongk_facultyofc_kongthweesak_011",
                "silpakornu_facultyoff_kongthweesak_032",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะสังคมศาสตร์",
                "ภาควิชาสังคมวิทยาและมานุษยวิทยา",
            ),
            (
                "chulalongk_facultyofc_rattanawong_022",
                "silpakornu_facultyoff_rattanawong_023",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะมนุษยศาสตร์",
                "ภาควิชาภาษาไทย",
            ),
            (
                "chulalongk_facultyofc_thainta_024",
                "silpakornu_facultyoff_tainta_024",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะมนุษยศาสตร์",
                "ภาควิชาภาษาตะวันออก สาขาวิชาภาษาญี่ปุ่น",
            ),
            (
                "chulalongk_facultyofc_chumsai_028",
                "silpakornu_facultyoff_chumsai_027",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะมนุษยศาสตร์",
                "ภาควิชาจิตวิทยา",
            ),
            (
                "chulalongk_facultyofc_ketmanee_013",
                "silpakornu_facultyoff_katumanee_034",
                "มหาวิทยาลัยเชียงใหม่",
                "คณะสังคมศาสตร์",
                "ภาควิชาสังคมวิทยาและมานุษยวิทยา",
            ),
        ]

        merged_count = 0
        for donor_id, keeper_id, uni, fac, dept in cmu_duplicate_pairs:
            donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()
            keeper = db.query(FacultyDB).filter(FacultyDB.id == keeper_id).first()

            if not keeper or not donor:
                print(f"Skipping pair {donor_id} / {keeper_id} (one or both not found)")
                continue

            # Update keeper to Chiang Mai University with authentic department
            keeper.university_th = uni
            keeper.faculty_th = fac
            keeper.department_th = dept

            # Preserve maximum bibliometric metrics
            keeper.total_citations = max(keeper.total_citations or 0, donor.total_citations or 0)
            keeper.h_index = max(keeper.h_index or 0, donor.h_index or 0)
            keeper.total_publications_count = max(keeper.total_publications_count or 0, donor.total_publications_count or 0)

            # Preserve OpenAlex ID if donor has a valid one
            if (not keeper.openalex_id or keeper.openalex_id == "not_indexed") and donor.openalex_id and donor.openalex_id != "not_indexed":
                keeper.openalex_id = donor.openalex_id

            # Union research interests and education
            k_ints = set(keeper.research_interests or [])
            d_ints = set(donor.research_interests or [])
            merged_ints = sorted(list((k_ints | d_ints) - {"-", "?", "null", "ไม่มี", "none", "n/a"}))
            keeper.research_interests = merged_ints
            flag_modified(keeper, "research_interests")

            k_edu = set(keeper.education or [])
            d_edu = set(donor.education or [])
            merged_edu = sorted(list(k_edu | d_edu))
            keeper.education = merged_edu
            flag_modified(keeper, "education")

            # Contract academic title on keeper if needed
            for pat, rep in long_title_patterns:
                if pat.search(keeper.full_name_th or ""):
                    keeper.full_name_th = pat.sub(rep, keeper.full_name_th)
                    break

            # Re-generate embedding text
            keeper.embedding_text = build_standard_embedding_text(keeper)

            # Safely delete donor record
            db.delete(donor)
            merged_count += 1
            print(f"Merged & Deleted donor '{donor_id}' -> Keeper '{keeper_id}' ({keeper.full_name_th}, {uni}, {fac})")

        # Commit all atomic changes
        db.commit()
        print(f"\nSuccessfully committed all Phase 3 repairs (7 duplicate pairs merged, total deleted: {merged_count}).")

        # Verify final faculty count
        final_count = db.query(FacultyDB).count()
        print(f"Final active faculty records count: {final_count}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during Phase 3 repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_phase3_deep_repairs()
