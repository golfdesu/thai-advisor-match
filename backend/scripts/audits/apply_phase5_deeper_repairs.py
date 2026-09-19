# -*- coding: utf-8 -*-
"""
Phase 5 Deep Database Hygiene Repairs:
1. Resolve 74 generic breadcrumb faculty_th == 'คณาจารย์และนักวิจัย' in regionalun_facultymem_*
   with authentic faculties and departments.
2. Merge 17 cross-university duplicate pairs with lifetime research metric preservation.
3. Fix Thai surname on psu_agro_nonglak_001 (Meethaokhanchit -> รศ.ดร. นงลักษณ์ มีเถ้าขันจิตร).
4. Disambiguate and clean research metrics for mfu_med_komsan_001.
5. Sanitize unescaped HTML entities and HTML tags in featured_publications.
6. Strip trailing commas/semicolons and unescaped quotes in research_interests.
7. Standardize Thaksin University Faculty of Economics and Business Administration (40 records)
   and clean Thammasat Law departmental breadcrumbs.
8. Recompute embedding_text for all modified faculty profiles.
"""
import sys
import re
import html
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB


def build_standard_embedding_text(f: FacultyDB) -> str:
    """Build unified embedding text consistent with backend vector generation."""
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


MAPPINGS_74 = {
    # Naresuan University (NU)
    "regionalun_facultymem_swangmek_002": ("คณะศึกษาศาสตร์", "ภาควิชาการศึกษา"),
    "regionalun_facultymem_chapu_003": ("คณะศึกษาศาสตร์", "ภาควิชาการศึกษา"),
    "regionalun_facultymem_khunmathuros_004": ("คณะศึกษาศาสตร์", "ภาควิชาการศึกษา"),
    "regionalun_facultymem_wongtheerathon_022": ("คณะศึกษาศาสตร์", "ภาควิชาวิจัยและจิตวิทยาประยุกต์"),
    "regionalun_facultymem_woraurai_060": ("คณะศึกษาศาสตร์", "ภาควิชาการศึกษา"),
    "regionalun_facultymem_wongupparaj_014": ("คณะศึกษาศาสตร์", "ภาควิชาวิจัยและจิตวิทยาประยุกต์"),
    "regionalun_facultymem_khammanee_012": ("คณะศึกษาศาสตร์", "ภาควิชาวิจัยและจิตวิทยาประยุกต์"),
    "regionalun_facultymem_naksiang_013": ("คณะศึกษาศาสตร์", "ภาควิชาวิจัยและจิตวิทยาประยุกต์"),
    "regionalun_facultymem_laoorattapong_016": ("คณะศึกษาศาสตร์", "ภาควิชาการศึกษา"),
    "regionalun_facultymem_soithong_015": ("คณะศึกษาศาสตร์", "ภาควิชาการศึกษา"),

    "regionalun_facultymem_eakapont_007": ("คณะมนุษยศาสตร์", "ภาควิชาภาษาไทย"),
    "regionalun_facultymem_mahamontri_008": ("คณะมนุษยศาสตร์", "ภาควิชาภาษาไทย"),
    "regionalun_facultymem_cailliau_006": ("คณะมนุษยศาสตร์", "ภาควิชาภาษาตะวันตก"),
    "regionalun_facultymem_longue_005": ("คณะมนุษยศาสตร์", "ภาควิชาภาษาตะวันตก"),
    "regionalun_facultymem_chaison_033": ("คณะมนุษยศาสตร์", "ภาควิชาดุริยางคศาสตร์"),

    "regionalun_facultymem_phudphandan_009": ("คณะวิทยาศาสตร์การแพทย์", "ภาควิชากายวิภาคศาสตร์"),
    "regionalun_facultymem_attapanyawanich_010": ("คณะวิทยาศาสตร์การแพทย์", "ภาควิชากายวิภาคศาสตร์"),

    "regionalun_facultymem_onpong_027": ("คณะวิทยาศาสตร์", "ภาควิชาคอมพิวเตอร์"),
    "regionalun_facultymem_kanawong_028": ("คณะวิทยาศาสตร์", "ภาควิชาคอมพิวเตอร์"),
    "regionalun_facultymem_soonklang_026": ("คณะวิทยาศาสตร์", "ภาควิชาคอมพิวเตอร์"),
    "regionalun_facultymem_kaewwangchai_032": ("คณะวิทยาศาสตร์", "ภาควิชาเคมี"),
    "regionalun_facultymem_charitkuan_017": ("คณะวิทยาศาสตร์", "ภาควิชาวิทยาศาสตร์การเดินเรือและประมง"),

    "regionalun_facultymem_nilmoj_030": ("คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "ภาควิชาบริหารธุรกิจ"),
    "regionalun_facultymem_ampawat_029": ("คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "ภาควิชาบริหารธุรกิจ"),
    "regionalun_facultymem_thammavinyu_035": ("คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "ภาควิชาการบัญชี"),
    "regionalun_facultymem_suwandacha_018": ("คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "ภาควิชาบริหารธุรกิจ"),
    "regionalun_facultymem_boonchairoj_020": ("คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "ภาควิชาบริหารธุรกิจ"),
    "regionalun_facultymem_naktang_019": ("คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "ภาควิชาบริหารธุรกิจ"),

    "regionalun_facultymem_srisilapanan_057": ("คณะทันตแพทยศาสตร์", "ภาควิชาทันตกรรมชุมชน"),

    "regionalun_facultymem_makkaew_044": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยสิ่งแวดล้อม"),
    "regionalun_facultymem_preecha_046": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยชุมชน"),
    "regionalun_facultymem_wongrit_055": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยชุมชน"),
    "regionalun_facultymem_somporn_053": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยสิ่งแวดล้อม"),
    "regionalun_facultymem_kongpran_043": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยสิ่งแวดล้อม"),
    "regionalun_facultymem_theerawattanasu_052": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยสิ่งแวดล้อม"),
    "regionalun_facultymem_chutipattana_054": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยชุมชน"),
    "regionalun_facultymem_srimok_047": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยชุมชน"),
    "regionalun_facultymem_wongkhongdech_038": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยสิ่งแวดล้อม"),
    "regionalun_facultymem_thongkhao_045": ("คณะสาธารณสุขศาสตร์", "ภาควิชาอนามัยชุมชน"),

    # Maejo University (MJU)
    "regionalun_facultymem_uphoyo_080": ("คณะสัตวแพทยศาสตร์", "กลุ่มวิชาคลินิกสัตว์เลี้ยง"),
    "regionalun_facultymem_srivorakul_065": ("คณะสัตวแพทยศาสตร์", "กลุ่มวิชาปรีคลินิกทางสัตวแพทย์"),
    "regionalun_facultymem_pokkaew_073": ("คณะวิศวกรรมและอุตสาหกรรมเกษตร", "สาขาวิชาวิศวกรรมเกษตร"),
    "regionalun_facultymem_suksamran_067": ("คณะศิลปศาสตร์", "สาขาวิชาการท่องเที่ยวและบริการ"),
    "regionalun_facultymem_khammoon_076": ("คณะศิลปศาสตร์", "สาขาวิชาภาษาอังกฤษ"),
    "regionalun_facultymem_lianghiranthawo_075": ("คณะศิลปศาสตร์", "สาขาวิชาภาษาจีน"),
    "regionalun_facultymem_maneechookate_077": ("คณะศิลปศาสตร์", "สาขาวิชาภาษาไทย"),
    "regionalun_facultymem_sreenorchan_068": ("คณะศิลปศาสตร์", "สาขาวิชาการท่องเที่ยวและบริการ"),
    "regionalun_facultymem_dechaphatumwan_066": ("คณะศิลปศาสตร์", "สาขาวิชาภาษาอังกฤษ"),
    "regionalun_facultymem_phansaensri_074": ("คณะวิทยาศาสตร์", "สาขาวิชาเคมี"),
    "regionalun_facultymem_pisitsakul_079": ("คณะวิทยาศาสตร์", "สาขาวิชาชีววิทยาประยุกต์"),
    "regionalun_facultymem_lertkanjanaporn_071": ("คณะวิทยาศาสตร์", "สาขาวิชาวิทยาการคอมพิวเตอร์"),
    "regionalun_facultymem_phositthiphan_081": ("คณะศิลปศาสตร์", "สาขาวิชาการท่องเที่ยวและบริการ"),
    "regionalun_facultymem_rakprayoon_072": ("คณะสารสนเทศและการสื่อสาร", "สาขาวิชาการสื่อสารดิจิทัล"),
    "regionalun_facultymem_tirawong_070": ("คณะบริหารธุรกิจ", "สาขาวิชาการจัดการ"),
    "regionalun_facultymem_boontham_069": ("คณะบริหารธุรกิจ", "สาขาวิชาการเงิน"),
    "regionalun_facultymem_maneewan_063": ("คณะสัตวศาสตร์และเทคโนโลยี", "สาขาวิชาสัตวศาสตร์"),

    # University of Phayao (UP)
    "regionalun_facultymem_sunanta_058": ("คณะแพทยศาสตร์", "หลักสูตรการแพทย์แผนจีนบัณฑิต"),
    "regionalun_facultymem_inkam_059": ("คณะศิลปศาสตร์", "สาขาวิชาภาษาไทย"),
    "regionalun_facultymem_nuengmek_056": ("คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ", "สาขาวิชาเกษตรศาสตร์"),
    "regionalun_facultymem_sirilak_062": ("คณะวิศวกรรมศาสตร์", "สาขาวิชาวิศวกรรมโยธา"),

    # Walailak University (WU)
    "regionalun_facultymem_klamsangsai_048": ("สำนักวิชาการจัดการ", "หลักสูตรบริหารธุรกิจ"),
    "regionalun_facultymem_klinmanee_049": ("สำนักวิชาศิลปศาสตร์", "หลักสูตรภาษาอังกฤษ"),
    "regionalun_facultymem_thamrongrat_041": ("สำนักวิชาวิทยาศาสตร์", "หลักสูตรวิทยาศาสตร์การแพทย์"),
    "regionalun_facultymem_kaewprasertrakk_042": ("สำนักวิชาการจัดการ", "หลักสูตรบริหารธุรกิจ"),
    "regionalun_facultymem_maneechot_051": ("สำนักวิชานิติศาสตร์", "หลักสูตรนิติศาสตรบัณฑิต"),

    # Mahasarakham University (MSU)
    "regionalun_facultymem_ketuwong_040": ("คณะศิลปกรรมศาสตร์และวัฒนธรรมศาสตร์", "สาขาวิชาทัศนศิลป์"),
    "regionalun_facultymem_pramual_036": ("คณะวิทยาศาสตร์", "ภาควิชาชีววิทยา"),
    "regionalun_facultymem_sanghamanee_037": ("คณะสาธารณสุขศาสตร์", "กลุ่มวิชาอนามัยสิ่งแวดล้อม"),
    "regionalun_facultymem_praphan_039": ("คณะมนุษยศาสตร์และสังคมศาสตร์", "สาขาวิชาภาษาอังกฤษและภาษาตะวันออก"),

    # Burapha University (BUU)
    "regionalun_facultymem_amornratanaphan_011": ("คณะศึกษาศาสตร์", "ภาควิชาการบริหารการศึกษา"),
    "regionalun_facultymem_chantanavaranon_023": ("คณะศึกษาศาสตร์", "ภาควิชาการบริหารการศึกษา"),
    "regionalun_facultymem_inthamaso_024": ("คณะสหเวชศาสตร์", "สายวิชาเทคนิคการแพทย์"),
    "regionalun_facultymem_anusasananan_021": ("คณะศึกษาศาสตร์", "ภาควิชาวิจัยและจิตวิทยาประยุกต์"),

    # Silpakorn University (SU)
    "regionalun_facultymem_patanathabutr_031": ("คณะวิทยาการจัดการ", "สาขาวิชาการจัดการธุรกิจและภาษา"),
}

CROSS_UNI_MERGES_17 = [
    ("camt-cmu-015_01d96c", "mu_398425a6_1356"),
    ("walailak_schoolof_437c2bf2", "psu_eng_002"),
    ("srinakha_facultyo_e57b3746", "mu_sci_wave14_b_0227"),
    ("psu_supatinee_k_0146", "walailak_schoolof_ebb717ab"),
    ("cmu-sci-017_a8bf1a", "walailak_schoolof_e7211fe0"),
    ("sut_chatchai_jothiyangkoon_1332", "kku_eng_chatchai_j_001"),
    ("mu_sc_kiattawee_001", "ku_sci_wave13_b_0003"),
    ("sut_eng_pitiwat_001", "cmu_eng_department_prof_41"),
    ("srinakhari_facultyofe_fac_072_072", "ku_wave18_edu_0002"),
    ("kingmongku_facultyofe_srisungsitthisu_066", "kmitl_eng_pornsak_001"),
    ("kmitl_eng_supachai_vor_001", "thammasatu_facultyofe_vorapojpisut_001"),
    ("kmitl_sci_wilailak_001", "kku_sci_wave14_b_0044"),
    ("sut_eng_kwanchai_001", "nu_kwanchai_kraitong_4512"),
    ("sut_eng_thaweesak_001", "nu_taweeksak_taekratok_1609"),
    ("kku_eng_wave12_0030", "sut_eng_apichart_001"),
    ("cu_cbs_wave11_0165", "ku_agro_wave15_0092"),
    ("cu_cbs_wave11_0304", "ku_agro_wave15_0100"),
]


def apply_phase5_repairs():
    db = SessionLocal()
    print("=" * 80)
    print("🚀 APPLYING PHASE 5 DEEP DATABASE HYGIENE REPAIRS")
    print("=" * 80)

    try:
        # -------------------------------------------------------------
        # 1. Resolve 74 generic breadcrumb faculty_th == 'คณาจารย์และนักวิจัย'
        # -------------------------------------------------------------
        print("\n--- 1. Resolving 74 Generic Faculty Breadcrumbs ---")
        repaired_74_count = 0
        for fid, (fac_th, dept_th) in MAPPINGS_74.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.faculty_th = fac_th
                f.department_th = dept_th
                if f.research_interests:
                    # Clean out generic placeholder
                    f.research_interests = [
                        i for i in f.research_interests
                        if str(i).strip() not in ["คณาจารย์และนักวิจัย", "นวัตกรรมและเทคโนโลยีประยุกต์"]
                    ]
                    if not f.research_interests:
                        f.research_interests = None
                f.embedding_text = build_standard_embedding_text(f)
                repaired_74_count += 1
        print(f"Repaired {repaired_74_count} / {len(MAPPINGS_74)} generic breadcrumb profiles.")

        # -------------------------------------------------------------
        # 2. Merge 17 Cross-University Duplicate Pairs
        # -------------------------------------------------------------
        print("\n--- 2. Merging 17 Cross-University Duplicate Pairs ---")
        merged_count = 0
        for donor_id, canon_id in CROSS_UNI_MERGES_17:
            donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()
            canon = db.query(FacultyDB).filter(FacultyDB.id == canon_id).first()
            if not donor:
                print(f"  Donor {donor_id} already absent, skipping.")
                continue
            if not canon:
                print(f"  Canon {canon_id} not found, skipping merge of {donor_id}.")
                continue

            # Lifetime research metrics preservation
            canon.total_citations = max(canon.total_citations or 0, donor.total_citations or 0)
            canon.total_publications_count = max(canon.total_publications_count or 0, donor.total_publications_count or 0)
            canon.h_index = max(canon.h_index or 0, donor.h_index or 0)

            # Metadata fallback preservation
            if not canon.openalex_id and donor.openalex_id:
                canon.openalex_id = donor.openalex_id
            if not canon.scholar_url and donor.scholar_url:
                canon.scholar_url = donor.scholar_url
            if not canon.email and donor.email:
                canon.email = donor.email
            if not canon.profile_url and donor.profile_url:
                canon.profile_url = donor.profile_url
            if not canon.image_url and donor.image_url:
                canon.image_url = donor.image_url

            # Research interests union
            canon_interests = list(canon.research_interests or [])
            donor_interests = list(donor.research_interests or [])
            seen_interests = set(i.lower().strip() for i in canon_interests)
            for di in donor_interests:
                if di.lower().strip() not in seen_interests:
                    canon_interests.append(di)
                    seen_interests.add(di.lower().strip())
            canon.research_interests = canon_interests if canon_interests else None

            # Featured publications union
            canon_pubs = list(canon.featured_publications or [])
            donor_pubs = list(donor.featured_publications or [])
            seen_titles = set()
            for cp in canon_pubs:
                t = cp.get("title", "") if isinstance(cp, dict) else str(cp)
                seen_titles.add(t.strip().lower())
            for dp in donor_pubs:
                t = dp.get("title", "") if isinstance(dp, dict) else str(dp)
                if t.strip().lower() not in seen_titles:
                    canon_pubs.append(dp)
                    seen_titles.add(t.strip().lower())
            canon.featured_publications = canon_pubs if canon_pubs else None

            # Re-point research labs references
            labs_led = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_id).all()
            for lab in labs_led:
                lab.lead_advisor_id = canon_id
                print(f"  Re-pointed lab {lab.id} lead_advisor_id: {donor_id} -> {canon_id}")

            all_labs = db.query(ResearchLabDB).all()
            for lab in all_labs:
                if lab.member_faculty_ids and donor_id in lab.member_faculty_ids:
                    lab.member_faculty_ids = [
                        canon_id if mid == donor_id else mid
                        for mid in lab.member_faculty_ids
                    ]
                    print(f"  Re-pointed lab {lab.id} member_id: {donor_id} -> {canon_id}")

            canon.embedding_text = build_standard_embedding_text(canon)
            db.delete(donor)
            merged_count += 1
            print(f"  Merged {donor_id} ({donor.full_name_th}) -> {canon_id} ({canon.full_name_th})")

        print(f"Successfully merged {merged_count} cross-university duplicate pairs.")

        # -------------------------------------------------------------
        # 3. Fix Thai surname on psu_agro_nonglak_001
        # -------------------------------------------------------------
        print("\n--- 3. Fixing Thai Surname on psu_agro_nonglak_001 ---")
        psu_nonglak = db.query(FacultyDB).filter(FacultyDB.id == "psu_agro_nonglak_001").first()
        if psu_nonglak:
            psu_nonglak.full_name_th = "รศ.ดร. นงลักษณ์ มีเถ้าขันจิตร"
            psu_nonglak.academic_title_th = "รศ.ดร."
            psu_nonglak.first_name = "Nonglak"
            psu_nonglak.last_name = "Meethaokhanchit"
            psu_nonglak.embedding_text = build_standard_embedding_text(psu_nonglak)
            print(f"  Updated psu_agro_nonglak_001 to: {psu_nonglak.full_name_th}")

        # -------------------------------------------------------------
        # 4. Disambiguate and clean research metrics for mfu_med_komsan_001
        # -------------------------------------------------------------
        print("\n--- 4. Cleaning Metrics for mfu_med_komsan_001 ---")
        mfu_komsan = db.query(FacultyDB).filter(FacultyDB.id == "mfu_med_komsan_001").first()
        if mfu_komsan:
            mfu_komsan.total_publications_count = len(mfu_komsan.featured_publications or [])
            mfu_komsan.total_citations = 0
            mfu_komsan.h_index = 0
            mfu_komsan.openalex_id = "not_indexed"
            mfu_komsan.embedding_text = build_standard_embedding_text(mfu_komsan)
            print(f"  Cleaned mfu_med_komsan_001: pubs={mfu_komsan.total_publications_count}, cites={mfu_komsan.total_citations}")

        # -------------------------------------------------------------
        # 5. Sanitize HTML entities and HTML tags in featured_publications
        # -------------------------------------------------------------
        print("\n--- 5. Sanitizing Publication Titles ---")
        pub_clean_count = 0
        all_facs = db.query(FacultyDB).all()
        for f in all_facs:
            if f.featured_publications:
                changed = False
                cleaned_pubs = []
                for p in f.featured_publications:
                    if isinstance(p, dict):
                        orig_title = p.get("title", "")
                        if orig_title:
                            # 1. unescape HTML entities
                            clean_t = html.unescape(orig_title)
                            # 2. strip HTML tags (<p ...>, <i>, </strong>, etc.)
                            clean_t = re.sub(r"</?[a-zA-Z][^>]*>", "", clean_t)
                            # 3. normalize whitespace
                            clean_t = re.sub(r"\s+", " ", clean_t).strip()
                            if clean_t != orig_title:
                                p_copy = dict(p)
                                p_copy["title"] = clean_t
                                cleaned_pubs.append(p_copy)
                                changed = True
                            else:
                                cleaned_pubs.append(p)
                        else:
                            cleaned_pubs.append(p)
                    else:
                        orig_str = str(p)
                        clean_t = html.unescape(orig_str)
                        clean_t = re.sub(r"</?[a-zA-Z][^>]*>", "", clean_t)
                        clean_t = re.sub(r"\s+", " ", clean_t).strip()
                        if clean_t != orig_str:
                            cleaned_pubs.append(clean_t)
                            changed = True
                        else:
                            cleaned_pubs.append(p)
                if changed:
                    f.featured_publications = cleaned_pubs
                    f.embedding_text = build_standard_embedding_text(f)
                    pub_clean_count += 1
        print(f"Sanitized featured publications across {pub_clean_count} faculty profiles.")

        # -------------------------------------------------------------
        # 6. Sanitize research_interests trailing punctuation & quotes
        # -------------------------------------------------------------
        print("\n--- 6. Sanitizing Research Interests ---")
        interests_clean_count = 0
        for f in all_facs:
            if f.research_interests:
                new_interests = []
                changed = False
                for it in f.research_interests:
                    s = html.unescape(str(it)).strip()
                    # Strip wrapping quotes
                    s = re.sub(r'^["\'\s]+|["\'\s]+$', "", s).strip()
                    # Strip trailing commas and semicolons
                    s = re.sub(r"[,;\s]+$", "", s).strip()
                    # Strip leading question marks/bullets from scraper artifacts
                    s = re.sub(r"^[?\s\-\*]+", "", s).strip()
                    if s and s not in ["-", "?", "null", "none", "ไม่มี", "n/a", "คณาจารย์และนักวิจัย"]:
                        if s != it:
                            changed = True
                        new_interests.append(s)
                    else:
                        changed = True
                if changed:
                    f.research_interests = new_interests if new_interests else None
                    f.embedding_text = build_standard_embedding_text(f)
                    interests_clean_count += 1
        print(f"Sanitized research interests across {interests_clean_count} faculty profiles.")

        # -------------------------------------------------------------
        # 7. Institutional Standardizations
        # -------------------------------------------------------------
        print("\n--- 7. Standardizing Institutional Faculty & Department Names ---")
        # 7.1 Thaksin University Faculty of Economics and Business Administration
        tsu_updated = 0
        tsu_facs = db.query(FacultyDB).filter(
            FacultyDB.university_th.like("%ทักษิณ%"),
            FacultyDB.faculty_th == "คณะเศรษฐศาสตร์และการบริหาร"
        ).all()
        for tf in tsu_facs:
            tf.faculty_th = "คณะเศรษฐศาสตร์และบริหารธุรกิจ"
            tf.department_th = "คณะเศรษฐศาสตร์และบริหารธุรกิจ"
            tf.embedding_text = build_standard_embedding_text(tf)
            tsu_updated += 1
        print(f"  Standardized {tsu_updated} Thaksin University economics faculty records.")

        # 7.2 Thammasat Law department breadcrumbs
        tu_law_updated = 0
        tu_law_facs = db.query(FacultyDB).filter(
            FacultyDB.university_th.like("%ธรรมศาสตร์%"),
            FacultyDB.faculty_th == "คณะนิติศาสตร์",
            FacultyDB.department_th.like("%คณะนิติศาสตร์ มหาวิทยาลัยธรรมศาสตร์%")
        ).all()
        for tlf in tu_law_facs:
            if "ศูนย์ลำปาง" in tlf.department_th:
                tlf.department_th = "คณะนิติศาสตร์ ศูนย์ลำปาง"
            else:
                tlf.department_th = "คณะนิติศาสตร์"
            tlf.embedding_text = build_standard_embedding_text(tlf)
            tu_law_updated += 1
        print(f"  Cleaned {tu_law_updated} Thammasat Law department breadcrumb records.")

        # 7.3 Chula Allied Health visiting scholar Philaiwan Siriphrukphong
        siriprik = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofa_siriprikphong_026").first()
        if siriprik:
            siriprik.university_th = "มหาวิทยาลัยธรรมศาสตร์"
            siriprik.faculty_th = "คณะสหเวชศาสตร์"
            siriprik.department_th = "คณะสหเวชศาสตร์"
            siriprik.embedding_text = build_standard_embedding_text(siriprik)
            print("  Re-attributed chulalongk_facultyofa_siriprikphong_026 to Thammasat University.")

        # 7.4 Clean duplicate uni in department for Mahidol Public Health & Tech Med
        utrarachkij = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofp_utrarachkij_013").first()
        if utrarachkij and "มหาวิทยาลัยมหิดล" in (utrarachkij.department_th or ""):
            utrarachkij.department_th = "คณะสาธารณสุขศาสตร์"
            utrarachkij.embedding_text = build_standard_embedding_text(utrarachkij)
            print("  Cleaned department_th on mahidoluni_facultyofp_utrarachkij_013.")

        asipat = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofa_asipat_030").first()
        if asipat and "มหาวิทยาลัยมหิดล" in (asipat.department_th or ""):
            asipat.department_th = "คณะเทคนิคการแพทย์"
            asipat.embedding_text = build_standard_embedding_text(asipat)
            print("  Cleaned department_th on chulalongk_facultyofa_asipat_030.")

        # Commit all repairs in a single atomic transaction
        db.commit()
        print("\n Transaction successfully committed to PostgreSQL database!")

        remaining_fac_count = db.query(FacultyDB).count()
        print(f"Final Active Faculty Count: {remaining_fac_count}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during Phase 5 repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_phase5_repairs()
