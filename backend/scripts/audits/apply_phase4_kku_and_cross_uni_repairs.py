# -*- coding: utf-8 -*-
"""
Phase 4 Deep Database Hygiene Repairs.
Resolves:
1. KKU Medicine ethics committee scraper artifacts (khonkaenun_facultyofm_*):
   - Deduplicate Siriraj Dean (mu_si_apichat_001), PSU Science Dean (princeofso_facultyofs_prateep_105),
     SUT Science (sut_sci_kritsana_001), PSU Science (princeofso_facultyofs_panichyakul_143).
   - Re-attribute SUT professors (tantanuch_018, siritanont_019) to Suranaree University of Technology.
   - Re-attribute PSU professors (fac_010_010, sothhiphan_021, fac_035_035, fac_036_036, wongwatcharanan_022).
   - Re-attribute CMU Medicine professors (chatkul_013, fac_012_012, j_016, kunlayawutipong_014).
   - Re-attribute KKU Science professors (fac_033_033, guayjarernpanis_025, luangchaisri_026, fac_031_031,
     ngeontae_027, ruangchai_030, tummuangpak_029, fac_034_034, burakham_028) to คณะวิทยาศาสตร์.
   - Re-attribute KKU Engineering professors (phongraktham_039, wanchantuk_038, sureephat_041, tangjaijit_040).
   - Clean duplicate titles (fac_004_004, fac_005_005, fac_006_006) and restore missing surname (nithichanon_007).
2. Mahidol Public Health crawler duplicates (mahidoluni_facultyofp_*):
   - Merge 5 CMU Public Health duplicate records (naksen_012, boonchieng_024, chaowatakul_028, thongprachum_029, singweratham_011).
   - Re-attribute external institutions (narin_027 to CMU Nursing, mahikul_014 to Chulabhorn Royal Academy, kongsawat_030 to CMU AMS).
3. Chulalongkorn Communication Arts naming (chulalongk_facultyofc_*):
   - Rename faculty_th from 'คณะวารสารศาสตร์และสื่อสารมวลชน' to 'คณะนิเทศศาสตร์' across 24 records.
   - Fix Dean Preeda Akrachantachote (akrachantachote_016) from 'คณะจิตวิทยา' to 'คณะนิเทศศาสตร์'.
   - Fix external faculty re-attributions (chongvilaikasem_017 to TU, phongphiw_021 & suwannarat_029 to CMU Humanities).
4. Regional universities crawler sweep repairs (regionalun_facultymem_*):
   - Merge duplicates (damrongkiatsak_078 to Maejo, srithep_034 to MSU, lailert_064 to CMU Med).
   - Re-attribute 14 Maejo records (mju.ac.th) and 4 UBU records (ubu.ac.th) from Naresuan.
   - Re-attribute Thaksin (klaivitphat_086) and Phayao (tulawattanakul_061).
5. Silpakorn Architecture committee sweep repairs (silpakornu_facultyofa_*):
   - Merge 3 Chula Architecture duplicates (sangsayan_003, sapsuk_002, wongphayat_004).
   - Merge 2 CMU Fine Arts duplicates (likhitmanon_009, suwanhem_007).
   - Re-attribute standalone CMU Fine Arts (chainakut_015, janthakhaisorn_010, gasorngatsara_016).
   - Re-attribute standalone KMUTNB Architecture (anantacha_017, chintanawat_020, kunawan_018, piriyasurawong_019).
   - Re-attribute standalone Chula Architecture (panhiphak_001, sirithanawat_005).
   - Re-attribute authentic Silpakorn Painting (kasornsawan_006, charoenwong_007, pongdam_008).
6. Cross-University Visiting / External Committee Pairs:
   - Merge Bin Zhao, Anchana Prathep, Ekwipoo Kalkornsurapranee, Anek Phuthong, Somkit Lertpaithoon,
     Pranee Kullavanijaya, Chalat Santivarangkna, Chutamanee Suthisisang, Sriwan Theeramankong,
     Rungrawee Temsiririrkkul, Kanokwan Chancharoenchai, Rossarin Osathanunkul, Olarn Rojanapornpun,
     Bundit Manaskasemsak, Jiraphol Chiyachantana, Pornchai Wisuttisak, Tuantong Jutagate.
7. Institutional Faculty Naming Standardization:
   - NIDA Business School: nida_biz_001, 002, 003 -> คณะบริหารธุรกิจ
   - KU Agriculture: ku_agri_001, ku_agri_entomology_001 -> คณะเกษตร
8. Text-Vector Symmetry:
   - Regenerate embedding_text for all mutated and merged records.
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


def merge_faculty_records(db, donor_id: str, keeper_id: str, updates: dict = None) -> bool:
    """Merges donor faculty record into keeper faculty record and deletes donor."""
    donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()
    keeper = db.query(FacultyDB).filter(FacultyDB.id == keeper_id).first()

    if not donor or not keeper:
        print(f"Skipping merge {donor_id} -> {keeper_id} (one or both records not found)")
        return False

    # Apply any specific attribute overrides to keeper
    if updates:
        for k, v in updates.items():
            setattr(keeper, k, v)

    # Preserve highest bibliometric metrics
    keeper.total_citations = max(keeper.total_citations or 0, donor.total_citations or 0)
    keeper.h_index = max(keeper.h_index or 0, donor.h_index or 0)
    keeper.total_publications_count = max(keeper.total_publications_count or 0, donor.total_publications_count or 0)

    # Preserve OpenAlex ID
    if (not keeper.openalex_id or keeper.openalex_id == "not_indexed") and donor.openalex_id and donor.openalex_id != "not_indexed":
        keeper.openalex_id = donor.openalex_id

    # Preserve email if keeper lacks one
    if not keeper.email and donor.email:
        keeper.email = donor.email

    # Union research interests
    k_ints = set(keeper.research_interests or [])
    d_ints = set(donor.research_interests or [])
    clean_ints = sorted(list((k_ints | d_ints) - {"-", "?", "null", "ไม่มี", "none", "n/a"}))
    if clean_ints:
        keeper.research_interests = clean_ints
        flag_modified(keeper, "research_interests")

    # Union education
    k_edu = set(keeper.education or [])
    d_edu = set(donor.education or [])
    clean_edu = sorted(list(k_edu | d_edu))
    if clean_edu:
        keeper.education = clean_edu
        flag_modified(keeper, "education")

    # Re-generate embedding text
    keeper.embedding_text = build_standard_embedding_text(keeper)

    # Re-point any research lab foreign keys
    db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_id).update(
        {ResearchLabDB.lead_advisor_id: keeper_id}
    )

    db.delete(donor)
    print(f"Merged & Deleted donor '{donor_id}' -> Keeper '{keeper_id}' ({keeper.full_name_th}, {keeper.university_th})")
    return True


def apply_phase4_repairs():
    db = SessionLocal()
    print("=" * 80)
    print("🚀 EXECUTING PHASE 4 DEEP DATABASE REPAIRS")
    print("=" * 80)

    try:
        # -------------------------------------------------------------
        # 1. KHON KAEN MEDICINE SCRAPER ARTIFACTS (khonkaenun_facultyofm_*)
        # -------------------------------------------------------------
        print("\n--- 1. RESOLVING KKU MEDICINE SCRAPER ARTIFACTS ---")

        # 1.1 Deduplication Merges
        kku_deans_merges = [
            ("khonkaenun_facultyofm_fac_009_009", "mu_si_apichat_001", {}),
            ("khonkaenun_facultyofm_prateep_024", "princeofso_facultyofs_prateep_105", {}),
            ("khonkaenun_facultyofm_sagarik_017", "sut_sci_kritsana_001", {}),
            ("khonkaenun_facultyofm_panichayakul_023", "princeofso_facultyofs_panichyakul_143", {}),
        ]
        for donor_id, keeper_id, upds in kku_deans_merges:
            merge_faculty_records(db, donor_id, keeper_id, upds)

        # 1.2 Re-attribute SUT professors
        sut_updates = [
            ("khonkaenun_facultyofm_tantanuch_018", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิทยาศาสตร์", "สาขาวิชาคณิตศาสตร์"),
            ("khonkaenun_facultyofm_siritanont_019", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "สำนักวิชาวิทยาศาสตร์", "สาขาวิชาเคมี"),
        ]
        for fid, uni, fac, dept in sut_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed SUT: {fid} ({f.full_name_th}) -> {uni}, {fac}, {dept}")

        # 1.3 Re-attribute PSU professors
        psu_updates = [
            ("khonkaenun_facultyofm_fac_010_010", "มหาวิทยาลัยสงขลานครินทร์", "คณะแพทยศาสตร์", "ภาควิชาอายุรศาสตร์"),
            ("khonkaenun_facultyofm_sothhiphan_021", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิทยาศาสตร์", "ภาควิชาชีววิทยา"),
            ("khonkaenun_facultyofm_fac_035_035", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิศวกรรมศาสตร์", "ภาควิชาวิศวกรรมเครื่องกลและเมคาทรอนิกส์"),
            ("khonkaenun_facultyofm_fac_036_036", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิศวกรรมศาสตร์", "ภาควิชาวิศวกรรมคอมพิวเตอร์"),
            ("khonkaenun_facultyofm_wongwatcharanan_022", "มหาวิทยาลัยสงขลานครินทร์", "คณะวิทยาศาสตร์", "ภาควิชากายวิภาคศาสตร์"),
        ]
        for fid, uni, fac, dept in psu_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed PSU: {fid} ({f.full_name_th}) -> {uni}, {fac}, {dept}")

        # 1.4 Re-attribute CMU Medicine professors
        cmu_med_updates = [
            ("khonkaenun_facultyofm_chatkul_013", "มหาวิทยาลัยเชียงใหม่", "คณะแพทยศาสตร์", "ภาควิชาอายุรศาสตร์"),
            ("khonkaenun_facultyofm_fac_012_012", "มหาวิทยาลัยเชียงใหม่", "คณะแพทยศาสตร์", "ภาควิชาเภสัชวิทยา"),
            ("khonkaenun_facultyofm_j_016", "มหาวิทยาลัยเชียงใหม่", "คณะแพทยศาสตร์", "ภาควิชาเวชศาสตร์ครอบครัว"),
            ("khonkaenun_facultyofm_kunlayawutipong_014", "มหาวิทยาลัยเชียงใหม่", "คณะแพทยศาสตร์", "ภาควิชาอายุรศาสตร์"),
        ]
        for fid, uni, fac, dept in cmu_med_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                # Clean full_name_th formatting if needed
                f.full_name_th = re.sub(r"^(รศ\.ดร\.)\s*(นายแพทย์)\s*", r"\1นพ. ", f.full_name_th)
                f.full_name_th = re.sub(r"^(รศ\.)\s*(พญ\.)\s*", r"\1\2 ", f.full_name_th)
                f.full_name_th = re.sub(r"^(อ\.)\s*(นพ\.)\s*", r"\1\2 ", f.full_name_th)
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed CMU Med: {fid} ({f.full_name_th}) -> {uni}, {fac}, {dept}")

        # 1.5 Re-attribute KKU Science faculty members
        kku_sci_updates = [
            ("khonkaenun_facultyofm_fac_033_033", "คณะวิทยาศาสตร์", "สาขาวิชาคณิตศาสตร์"),
            ("khonkaenun_facultyofm_guayjarernpanis_025", "คณะวิทยาศาสตร์", "สาขาวิชาคณิตศาสตร์"),
            ("khonkaenun_facultyofm_luangchaisri_026", "คณะวิทยาศาสตร์", "สาขาวิชาคณิตศาสตร์"),
            ("khonkaenun_facultyofm_fac_031_031", "คณะวิทยาศาสตร์", "สาขาวิชาฟิสิกส์"),
            ("khonkaenun_facultyofm_ngeontae_027", "คณะวิทยาศาสตร์", "สาขาวิชาเคมี"),
            ("khonkaenun_facultyofm_ruangchai_030", "คณะวิทยาศาสตร์", "สาขาวิชาฟิสิกส์"),
            ("khonkaenun_facultyofm_tummuangpak_029", "คณะวิทยาศาสตร์", "สาขาวิชาฟิสิกส์"),
            ("khonkaenun_facultyofm_fac_034_034", "คณะวิทยาศาสตร์", "สาขาวิชาเคมี"),
            ("khonkaenun_facultyofm_burakham_028", "คณะวิทยาศาสตร์", "สาขาวิชาเคมี"),
        ]
        for fid, fac, dept in kku_sci_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed KKU Science: {fid} ({f.full_name_th}) -> {fac}, {dept}")

        # 1.6 Re-attribute KKU Engineering faculty members
        kku_eng_updates = [
            ("khonkaenun_facultyofm_phongraktham_039", "คณะวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมเครื่องกล"),
            ("khonkaenun_facultyofm_wanchantuk_038", "คณะวิศวกรรมศาสตร์", "ภาควิชาวิศวกรรมคอมพิวเตอร์"),
            ("khonkaenun_facultyofm_sureephat_041", "คณะวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมอุตสาหการ"),
            ("khonkaenun_facultyofm_tangjaijit_040", "คณะวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมเครื่องกล"),
        ]
        for fid, fac, dept in kku_eng_updates:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed KKU Engineering: {fid} ({f.full_name_th}) -> {fac}, {dept}")

        # 1.7 Clean Double Titles & Missing Surname
        title_fixes = [
            ("khonkaenun_facultyofm_fac_004_004", "นพ. ยุทธพงศ์ วงศ์สวัสดิวัฒน์", "Yutthaphong", "Wongsawatdiwat"),
            ("khonkaenun_facultyofm_fac_005_005", "นพ. รัฐพล อุปลา", "Ratthaphon", "Upala"),
            ("khonkaenun_facultyofm_fac_006_006", "นพ. สิรภูมิ เนียมสนิท", "Siraphum", "Niamsanit"),
        ]
        for fid, fn_th, first, last in title_fixes:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.full_name_th = fn_th
                f.first_name = first
                f.last_name = last
                f.academic_title_th = "นพ."
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Fixed double title: {fid} -> {fn_th}")

        # Missing surname for Arnon Nithichanon
        f_arnon = db.query(FacultyDB).filter(FacultyDB.id == "khonkaenun_facultyofm_nithichanon_007").first()
        if f_arnon:
            f_arnon.full_name_th = "ผศ.ดร. อานันต์ นิธิชานนท์"
            f_arnon.first_name = "Arnon"
            f_arnon.last_name = "Nithichanon"
            f_arnon.department_th = "ภาควิชาจุลชีววิทยา"
            f_arnon.embedding_text = build_standard_embedding_text(f_arnon)
            print(f"Restored surname: {f_arnon.id} -> {f_arnon.full_name_th}")

        # -------------------------------------------------------------
        # 2. MAHIDOL PUBLIC HEALTH SCRAPER ARTIFACTS (mahidoluni_facultyofp_*)
        # -------------------------------------------------------------
        print("\n--- 2. RESOLVING MAHIDOL PUBLIC HEALTH SCRAPER ARTIFACTS ---")
        mu_p_merges = [
            ("mahidoluni_facultyofp_naksen_012", "chiangmaiu_facultyofp_naksen_003", {}),
            ("mahidoluni_facultyofp_boonchieng_024", "chiangmaiu_facultyofp_boonchieng_002", {}),
            ("mahidoluni_facultyofp_chaowatakul_028", "chiangmaiu_facultyofp_chautrakarn_006", {}),
            ("mahidoluni_facultyofp_thongprachum_029", "chiangmaiu_facultyofp_thongprachum_004", {}),
            ("mahidoluni_facultyofp_singweratham_011", "chiangmaiu_facultyofp_singweratham_008", {}),
        ]
        for donor_id, keeper_id, upds in mu_p_merges:
            merge_faculty_records(db, donor_id, keeper_id, upds)

        mu_p_reattributes = [
            ("mahidoluni_facultyofp_narin_027", "มหาวิทยาลัยเชียงใหม่", "คณะพยาบาลศาสตร์", "กลุ่มวิชาการพยาบาลสาธารณสุขศาสตร์"),
            ("mahidoluni_facultyofp_mahikul_014", "ราชวิทยาลัยจุฬาภรณ์", "วิทยาลัยแพทยศาสตร์ศรีสวางควัฒน", "กลุ่มวิชาการแพทย์และสาธารณสุข"),
            ("mahidoluni_facultyofp_kongsawat_030", "มหาวิทยาลัยเชียงใหม่", "คณะเทคนิคการแพทย์", "ภาควิชากายภาพบำบัด"),
        ]
        for fid, uni, fac, dept in mu_p_reattributes:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed Mahidol PH record: {fid} ({f.full_name_th}) -> {uni}, {fac}, {dept}")

        # -------------------------------------------------------------
        # 3. CHULALONGKORN COMMUNICATION ARTS FACULTY NAME BUG
        # -------------------------------------------------------------
        print("\n--- 3. FIXING CHULALONGKORN COMMUNICATION ARTS FACULTY NAMES ---")
        chula_comm_records = db.query(FacultyDB).filter(
            FacultyDB.university_th == "จุฬาลงกรณ์มหาวิทยาลัย",
            FacultyDB.faculty_th == "คณะวารสารศาสตร์และสื่อสารมวลชน"
        ).all()
        for f in chula_comm_records:
            f.faculty_th = "คณะนิเทศศาสตร์"
            f.embedding_text = build_standard_embedding_text(f)
        print(f"Updated faculty_th to 'คณะนิเทศศาสตร์' for {len(chula_comm_records)} Chulalongkorn professors.")

        # Specific Chula Comm Arts Dean & External Faculty fixes
        f_preeda = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofc_akrachantachote_016").first()
        if f_preeda:
            f_preeda.faculty_th = "คณะนิเทศศาสตร์"
            f_preeda.department_th = "ภาควิชาการสื่อสารมวลชน"
            f_preeda.embedding_text = build_standard_embedding_text(f_preeda)
            print(f"Fixed Chula Dean: {f_preeda.id} ({f_preeda.full_name_th}) -> คณะนิเทศศาสตร์")

        chula_c_external = [
            ("chulalongk_facultyofc_chongvilaikasem_017", "มหาวิทยาลัยธรรมศาสตร์", "คณะวารสารศาสตร์และสื่อสารมวลชน", "กลุ่มวิชาการสื่อสารมวลชน"),
            ("chulalongk_facultyofc_phongphiw_021", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาจิตวิทยา"),
            ("chulalongk_facultyofc_suwannarat_029", "มหาวิทยาลัยเชียงใหม่", "คณะมนุษยศาสตร์", "ภาควิชาจิตวิทยา"),
        ]
        for fid, uni, fac, dept in chula_c_external:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed Chula-C external: {fid} ({f.full_name_th}) -> {uni}, {fac}, {dept}")

        # -------------------------------------------------------------
        # 4. REGIONAL UNIVERSITIES SWEEP REPAIRS (regionalun_facultymem_*)
        # -------------------------------------------------------------
        print("\n--- 4. RESOLVING REGIONAL UNIVERSITIES SWEEPS ---")
        # 4.1 Merge duplicates
        reg_merges = [
            ("regionalun_facultymem_damrongkiatsak_078", "mju_6bd50b84_4764", {}),
            ("regionalun_facultymem_srithep_034", "msu_yottha_s_3427", {}),
            ("regionalun_facultymem_lailert_064", "cmu_4f0f3518_0705", {}),
        ]
        for donor_id, keeper_id, upds in reg_merges:
            merge_faculty_records(db, donor_id, keeper_id, upds)

        # 4.2 Re-attribute Maejo University records
        mju_facs = db.query(FacultyDB).filter(
            FacultyDB.id.like("regionalun_facultymem_%"),
            FacultyDB.university_th == "มหาวิทยาลัยนเรศวร",
            FacultyDB.profile_url.like("%mju.ac.th%")
        ).all()
        for f in mju_facs:
            f.university_th = "มหาวิทยาลัยแม่โจ้"
            f.embedding_text = build_standard_embedding_text(f)
            print(f"Re-attributed to Maejo: {f.id} ({f.full_name_th}) -> มหาวิทยาลัยแม่โจ้")

        # 4.3 Re-attribute Ubon Ratchathani University records
        ubu_facs = db.query(FacultyDB).filter(
            FacultyDB.id.like("regionalun_facultymem_%"),
            FacultyDB.university_th == "มหาวิทยาลัยนเรศวร",
            FacultyDB.profile_url.like("%ubu.ac.th%")
        ).all()
        for f in ubu_facs:
            f.university_th = "มหาวิทยาลัยอุบลราชธานี"
            f.faculty_th = "คณะศึกษาศาสตร์"
            f.embedding_text = build_standard_embedding_text(f)
            print(f"Re-attributed to UBU: {f.id} ({f.full_name_th}) -> มหาวิทยาลัยอุบลราชธานี, คณะศึกษาศาสตร์")

        # 4.4 Re-attribute Thaksin & Phayao
        f_klaivit = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_klaivitphat_086").first()
        if f_klaivit:
            f_klaivit.university_th = "มหาวิทยาลัยทักษิณ"
            f_klaivit.faculty_th = "คณะศึกษาศาสตร์"
            f_klaivit.embedding_text = build_standard_embedding_text(f_klaivit)
            print(f"Re-attributed Thaksin: {f_klaivit.id} -> มหาวิทยาลัยทักษิณ")

        f_tula = db.query(FacultyDB).filter(FacultyDB.id == "regionalun_facultymem_tulawattanakul_061").first()
        if f_tula:
            f_tula.university_th = "มหาวิทยาลัยพะเยา"
            f_tula.faculty_th = "คณะสาธารณสุขศาสตร์"
            f_tula.embedding_text = build_standard_embedding_text(f_tula)
            print(f"Re-attributed Phayao: {f_tula.id} -> มหาวิทยาลัยพะเยา, คณะสาธารณสุขศาสตร์")

        # -------------------------------------------------------------
        # 5. SILPAKORN ARCHITECTURE COMMITTEE SWEEPS (silpakornu_facultyofa_*)
        # -------------------------------------------------------------
        print("\n--- 5. RESOLVING SILPAKORN ARCHITECTURE COMMITTEE SWEEPS ---")
        su_a_merges = [
            ("silpakornu_facultyofa_sangsayan_003", "cu_ds_wave11_0023", {}),
            ("silpakornu_facultyofa_sapsuk_002", "cu_ds_wave11_0021", {}),
            ("silpakornu_facultyofa_wongphayat_004", "cu_ds_wave11_0017", {}),
            ("silpakornu_facultyofa_likhitmanon_009", "chiangmaiu_facultyoff_likhitmanont_001", {}),
            ("silpakornu_facultyoff_suwanhem_007", "silpakornu_facultyofa_suwanhem_011", {"faculty_th": "คณะวิจิตรศิลป์", "department_th": "ภาควิชาทัศนศิลป์"}),
        ]
        for donor_id, keeper_id, upds in su_a_merges:
            merge_faculty_records(db, donor_id, keeper_id, upds)

        # Standalone re-attributions from silpakornu_facultyofa_*
        su_a_reattributes = [
            ("silpakornu_facultyofa_chainakut_015", "มหาวิทยาลัยเชียงใหม่", "คณะวิจิตรศิลป์", "ภาควิชาภาพพิมพ์ จิตรกรรม และประติมากรรม"),
            ("silpakornu_facultyofa_janthakhaisorn_010", "มหาวิทยาลัยเชียงใหม่", "คณะวิจิตรศิลป์", "ภาควิชาทัศนศิลป์"),
            ("silpakornu_facultyofa_gasorngatsara_016", "มหาวิทยาลัยเชียงใหม่", "คณะวิจิตรศิลป์", "ภาควิชาทัศนศิลป์"),
            ("silpakornu_facultyofa_anantacha_017", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "คณะสถาปัตยกรรมและการออกแบบ", "ภาควิชาสถาปัตยกรรม"),
            ("silpakornu_facultyofa_chintanawat_020", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "คณะสถาปัตยกรรมและการออกแบบ", "ภาควิชาสถาปัตยกรรม"),
            ("silpakornu_facultyofa_kunawan_018", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "คณะสถาปัตยกรรมและการออกแบบ", "สาขาวิชาสถาปัตยกรรม"),
            ("silpakornu_facultyofa_piriyasurawong_019", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "คณะสถาปัตยกรรมและการออกแบบ", "ภาควิชาการจัดการงานออกแบบ"),
            ("silpakornu_facultyofa_panhiphak_001", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะสถาปัตยกรรมศาสตร์", "ภาควิชาการวางแผนภาคและเมือง"),
            ("silpakornu_facultyofa_sirithanawat_005", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะสถาปัตยกรรมศาสตร์", "ภาควิชาสถาปัตยกรรมศาสตร์"),
            ("silpakornu_facultyofa_kasornsawan_006", "มหาวิทยาลัยศิลปากร", "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "ภาควิชาภาพพิมพ์"),
            ("silpakornu_facultyofa_charoenwong_007", "มหาวิทยาลัยศิลปากร", "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "ภาควิชาประติมากรรม"),
            ("silpakornu_facultyofa_pongdam_008", "มหาวิทยาลัยศิลปากร", "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "ภาควิชาภาพพิมพ์"),
        ]
        for fid, uni, fac, dept in su_a_reattributes:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.university_th = uni
                f.faculty_th = fac
                f.department_th = dept
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Re-attributed Silpakorn-A: {fid} ({f.full_name_th}) -> {uni}, {fac}, {dept}")

        # -------------------------------------------------------------
        # 6. DEDUPLICATE CROSS-UNIVERSITY VISITING / EXTERNAL COMMITTEE PAIRS
        # -------------------------------------------------------------
        print("\n--- 6. DEDUPLICATING CROSS-UNIVERSITY VISITING PAIRS ---")
        cross_pairs_to_merge = [
            # Bin Zhao: Chula Econ -> Thammasat Business School
            ("chulalongk_facultyofe_zhao_021", "thammasatu_thammasatb_fac_072_072", {}),
            # Anchana Prathep: KU -> PSU Science Dean
            ("ku-sci-zoo-010_648b2c", "princeofso_facultyofs_prateep_105", {}),
            # Ekwipoo Kalkornsurapranee: Chula Vet -> PSU Science Polymer Chemistry
            ("chulalongk_facultyofv_kankornsurapane_025", "princeofso_facultyofs_kalkornsuraphan_067", {}),
            # Anek Phuthong: Chula Allied Health -> Thammasat Allied Health
            ("chulalongk_facultyofa_phuthong_025", "tu_78332273_2711", {}),
            # Somkit Lertpaithoon: Thaksin Law -> Thammasat Law
            ("thaksinuni_facultyofl_lertpaithoon_009", "tu_law_064", {}),
            # Pranee Kullavanijaya: Chula Arts -> KU Humanities
            ("chulalongk_facultyofa_kulavanich_021", "ku-hum-003_7906a2", {}),
            # Chalat Santivarangkna: Chula Pharmacy -> Mahidol Institute of Nutrition Director
            ("chulalongk_facultyofp_santivarangkna_030", "mahidoluni_instituteo_santivarangkna_001", {}),
            # Chutamanee Suthisisang: Chula Pharmacy -> Mahidol Pharmacy
            ("chulalongk_facultyofp_suthisisang_033", "mu-pharm-020_8318c0", {}),
            # Sriwan Theeramankong: Chula Pharmacy -> Thammasat Pharmacy
            ("chulalongk_facultyofp_theeramankong_018", "thammasatu_facultyofp_theramunkong_032", {}),
            # Rungrawee Temsiririrkkul: Chula Pharmacy -> Thammasat Pharmacy
            ("chulalongk_facultyofp_temsiririrkkul_005", "thammasatu_facultyofp_temsiririrkkul_030", {}),
            # Kanokwan Chancharoenchai: Chula Econ -> KU Economics
            ("chulalongk_facultyofe_chancharoenchai_022", "ku_wave17_econ_0009", {}),
            # Rossarin Osathanunkul: Chula Econ -> CMU Economics
            ("chulalongk_facultyofe_osathanunkul_036", "cmu_46875b4a_0671", {}),
            # Olarn Rojanapornpun: KMUTT SIT -> KMITL IT
            ("kmutt_sit_oran_rojanapornpan", "kmitl_it_olarn_001", {}),
            # Bundit Manaskasemsak: KU CPE -> KMITL IT
            ("ku_eng_cpe_011", "kmitl_it_bundit_001", {}),
            # Jiraphol Chiyachantana: Chula CBS -> CMU Business Administration
            ("cu_cbs_wave11_0172", "cmu-ba-017_e1fbb3", {}),
            # Pornchai Wisuttisak: KU Econ -> CMU Law
            ("ku-econ-006_3d8c76", "chiangmaiu_facultyofl_wisuttisak_016", {}),
            # Tuantong Jutagate: KU Fish -> Ubon Ratchathani University Agriculture (Dean/Professor)
            ("ku_fish_tuantong_001", "ubonratcha_facultyofa_jutagate_001", {"email": "ffisttj@ku.ac.th"}),
        ]
        for donor_id, keeper_id, upds in cross_pairs_to_merge:
            merge_faculty_records(db, donor_id, keeper_id, upds)

        # -------------------------------------------------------------
        # 7. INSTITUTIONAL FACULTY NAMING STANDARDIZATION
        # -------------------------------------------------------------
        print("\n--- 7. INSTITUTIONAL FACULTY NAMING STANDARDIZATION ---")
        # NIDA Business School
        nida_biz_ids = ["nida_biz_001", "nida_biz_002", "nida_biz_003"]
        for fid in nida_biz_ids:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.faculty_th = "คณะบริหารธุรกิจ"
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Standardized NIDA: {fid} -> คณะบริหารธุรกิจ")

        # KU Faculty of Agriculture (คณะเกษตร)
        ku_agri_ids = ["ku_agri_001", "ku_agri_entomology_001"]
        for fid in ku_agri_ids:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.faculty_th = "คณะเกษตร"
                f.embedding_text = build_standard_embedding_text(f)
                print(f"Standardized KU: {fid} -> คณะเกษตร")

        # Commit all transaction changes atomically
        db.commit()
        print("\n" + "=" * 80)
        print("✅ ALL PHASE 4 REPAIRS COMMITTED SUCCESSFULLY!")
        print("=" * 80)

        final_count = db.query(FacultyDB).count()
        print(f"Final Active Faculty Records Count: {final_count}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error applying Phase 4 repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_phase4_repairs()
