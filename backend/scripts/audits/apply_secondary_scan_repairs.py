"""Apply database repairs identified in the second-pass exhaustive forensic scan:
1. Fix 62 English university desynchronizations to match canonical English names.
2. Sanitize cross-university profile URLs (3) and image URLs (4).
3. Clean up Thaksin University MUSE:
   - Merge 5 duplicate pairs (thaksinuni_facultyofm_001..005 -> regionalun_facultymem_fac_088..092)
     preserving email, publications, citations, and h-index.
   - Realign remaining 17 faculty to คณะสหวิทยาการและการประกอบการ (Faculty of Multidisciplinary Studies and Entrepreneurship).
   - Strip 'คณะดุริยางคศาสตร์' from research_interests.
4. Clean up compound and misplaced faculties:
   - Mahidol University Siriraj vs Ramathibodi:
     - Purge incomplete entry: mahidoluni_facultyofm_fac_015_015 ("ผศ. นพ. ธีรวุฒิ")
     - Re-affiliate 2 Chulalongkorn Medicine faculty (Dr. Trairak Pisitkun & Dr. Surasak Wannakrairot)
     - Split Siriraj (17) and Ramathibodi (5) faculty cleanly
     - Repair truncated Thai names (ปีติ ธุวะเศรษฐกุล, บวรศม ลีระพันธ์)
   - Kasetsart University:
     - Split Agro-Industry (2) and Veterinary Medicine (1)
   - Burapha University:
     - Set Faculty of Science for 2 Marine Science records
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB

TH_TO_EN_CANONICAL = {
    "จุฬาลงกรณ์มหาวิทยาลัย": "Chulalongkorn University",
    "มหาวิทยาลัยเกษตรศาสตร์": "Kasetsart University",
    "มหาวิทยาลัยเชียงใหม่": "Chiang Mai University",
    "มหาวิทยาลัยมหิดล": "Mahidol University",
    "มหาวิทยาลัยธรรมศาสตร์": "Thammasat University",
    "มหาวิทยาลัยขอนแก่น": "Khon Kaen University",
    "มหาวิทยาลัยสงขลานครินทร์": "Prince of Songkla University",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": "King Mongkut's Institute of Technology Ladkrabang",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": "King Mongkut's University of Technology Thonburi",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": "King Mongkut's University of Technology North Bangkok",
    "มหาวิทยาลัยศิลปากร": "Silpakorn University",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": "Srinakharinwirot University",
    "มหาวิทยาลัยอุบลราชธานี": "Ubon Ratchathani University",
    "มหาวิทยาลัยนเรศวร": "Naresuan University",
    "มหาวิทยาลัยบูรพา": "Burapha University",
    "มหาวิทยาลัยแม่ฟ้าหลวง": "Mae Fah Luang University",
    "มหาวิทยาลัยแม่โจ้": "Maejo University",
    "มหาวิทยาลัยวลัยลักษณ์": "Walailak University",
    "มหาวิทยาลัยพะเยา": "University of Phayao",
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": "Suranaree University of Technology",
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": "National Institute of Development Administration",
    "มหาวิทยาลัยทักษิณ": "Thaksin University",
    "มหาวิทยาลัยรามคำแหง": "Ramkhamhaeng University",
    "มหาวิทยาลัยมหาสารคาม": "Mahasarakham University",
    "มหาวิทยาลัยราชภัฏสวนสุนันทา": "Suan Sunandha Rajabhat University",
    "ราชวิทยาลัยจุฬาภรณ์": "Chulabhorn Royal Academy",
    "มหาวิทยาลัยกรุงเทพ": "Bangkok University",
    "มหาวิทยาลัยสุโขทัยธรรมาธิราช": "Sukhothai Thammathirat Open University",
    "มหาวิทยาลัยอัสสัมชัญ": "Assumption University",
    "มหาวิทยาลัยศรีปทุม": "Sripatum University",
    "มหาวิทยาลัยศรีปทุม วิทยาเขตขอนแก่น": "Sripatum University Khon Kaen Campus",
    "มหาวิทยาลัยศรีปทุม วิทยาเขตชลบุรี": "Sripatum University Chonburi Campus",
}

# 3 Thaksin MUSE duplicate pairs (donor -> target to keep)
TSU_MUSE_DUPLICATES = [
    {
        "donor_id": "thaksinuni_facultyofm_jitpakdee_001",
        "target_id": "regionalun_facultymem_fac_088_088",
    },
    {
        "donor_id": "thaksinuni_facultyofm_wongsawat_002",
        "target_id": "regionalun_facultymem_fac_089_089",
    },
    {
        "donor_id": "thaksinuni_facultyofm_diawkee_003",
        "target_id": "regionalun_facultymem_fac_090_090",
    },
    {
        "donor_id": "thaksinuni_facultyofm_seubsakulajinda_004",
        "target_id": "regionalun_facultymem_fac_091_091",
    },
    {
        "donor_id": "thaksinuni_facultyofm_watcharakorn_005",
        "target_id": "regionalun_facultymem_fac_092_092",
    },
]

# Mahidol Medicine Ramathibodi IDs
RAMA_IDS = [
    "mahidoluni_facultyofm_pookriyakamee_009",  # Department of Psychiatry
    "mahidoluni_facultyofm_kitiyakara_013",      # Department of Medicine (Nephrology)
    "mahidoluni_facultyofm_leerapan_019",       # Department of Community Medicine
    "mahidoluni_facultyofm_sukhato_023",        # Department of Family Medicine
    "mahidoluni_facultyofm_homsanit_026",       # Department of Community Medicine
]

# Mahidol Medicine Siriraj IDs
SIRIRAJ_IDS = [
    "mahidoluni_facultyofm_songsivilai_001",
    "mahidoluni_facultyofm_luangwechakan_002",
    "mahidoluni_facultyofm_thuvasethakul_003",
    "mahidoluni_facultyofm_kamtorntip_004",
    "mahidoluni_facultyofm_jiarakul_005",
    "mahidoluni_facultyofm_chotireungnapa_006",
    "mahidoluni_facultyofm_ruangtrakool_008",
    "mahidoluni_facultyofm_prateepavanich_010",
    "mahidoluni_facultyofm_vasuvattakul_011",
    "mahidoluni_facultyofm_pajareya_012",
    "mahidoluni_facultyofm_dankulchai_014",
    "mahidoluni_facultyofm_duangthongpol_016",
    "mahidoluni_facultyofm_sampattavanich_017",
    "mahidoluni_facultyofm_sungkaworn_021",
    "mahidoluni_facultyofm_dangprapai_022",
    "mahidoluni_facultyofm_sutharatanapong_024",
    "mahidoluni_facultyofm_nainetr_025",
]


def run_repairs(apply_changes: bool = False):
    db = SessionLocal()
    report = {
        "apply": apply_changes,
        "en_university_synced": [],
        "cross_urls_sanitized": [],
        "tsu_muse_duplicates_merged": [],
        "tsu_muse_faculty_realigned": [],
        "mahidol_medicine_de_compounded": [],
        "chula_medicine_reaffiliated": [],
        "ku_and_buu_de_compounded": [],
    }

    try:
        # =========================================================================
        # 1. BILINGUAL UNIVERSITY DESYNCHRONIZATION (62 RECORDS)
        # =========================================================================
        print("\n=== 1. SYNCHRONIZE BILINGUAL UNIVERSITY NAMES ===")
        all_faculties = db.query(FacultyDB).all()
        for f in all_faculties:
            expected_en = TH_TO_EN_CANONICAL.get(f.university_th)
            if expected_en and f.university != expected_en:
                old_en = f.university
                print(f"  [SYNC EN] {f.id} | {f.full_name_th} | {f.university_th} | Old: '{old_en}' -> New: '{expected_en}'")
                report["en_university_synced"].append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "th": f.university_th,
                    "old_en": old_en,
                    "new_en": expected_en
                })
                if apply_changes:
                    f.university = expected_en
                    f.embedding_text = build_faculty_embedding_text(f)

        print(f"Total English university names synced: {len(report['en_university_synced'])}")

        # =========================================================================
        # 2. CROSS-UNIVERSITY PROFILE & IMAGE URLS
        # =========================================================================
        print("\n=== 2. SANITIZE CROSS-UNIVERSITY PROFILE & IMAGE URLS ===")

        # 2a. Supachai Vorapojpisut (TU ME)
        tu_me = db.query(FacultyDB).filter(FacultyDB.id == "thammasatu_facultyofe_vorapojpisut_001").first()
        if tu_me:
            old_p = tu_me.profile_url
            new_p = "https://me.engr.tu.ac.th/th/department_me/personel_detail/3"
            print(f"  [PROFILE URL] {tu_me.id} | Old: {old_p} -> New: {new_p}")
            report["cross_urls_sanitized"].append({"id": tu_me.id, "field": "profile_url", "old": old_p, "new": new_p})
            if apply_changes:
                tu_me.profile_url = new_p

        # 2b. Chaiyong Ragkhitwetsagul (Mahidol ICT)
        mu_ict = db.query(FacultyDB).filter(FacultyDB.id == "mu_398425a6_1356").first()
        if mu_ict:
            old_img = mu_ict.image_url
            new_img = "https://www.ict.mahidol.ac.th/wp-content/uploads/2021/05/Chaiyong-1.jpg"
            print(f"  [IMAGE URL] {mu_ict.id} | Old: {old_img} -> New: {new_img}")
            report["cross_urls_sanitized"].append({"id": mu_ict.id, "field": "image_url", "old": old_img, "new": new_img})
            if apply_changes:
                mu_ict.image_url = new_img

        # 2c. Surapol Naowarat (Walailak Science)
        wu_surapol = db.query(FacultyDB).filter(FacultyDB.id == "walailak_schoolof_e7211fe0").first()
        if wu_surapol:
            old_p = wu_surapol.profile_url
            old_img = wu_surapol.image_url
            print(f"  [PROFILE/IMAGE URL] {wu_surapol.id} | Clear CMU profile & image")
            report["cross_urls_sanitized"].append({"id": wu_surapol.id, "field": "profile_url", "old": old_p, "new": "https://science.wu.ac.th/"})
            report["cross_urls_sanitized"].append({"id": wu_surapol.id, "field": "image_url", "old": old_img, "new": None})
            if apply_changes:
                wu_surapol.profile_url = "https://science.wu.ac.th/"
                wu_surapol.image_url = None

        # 2d. Supathinee Kongkaew (Walailak Science)
        wu_supathinee = db.query(FacultyDB).filter(FacultyDB.id == "walailak_schoolof_ebb717ab").first()
        if wu_supathinee:
            old_p = wu_supathinee.profile_url
            old_img = wu_supathinee.image_url
            print(f"  [PROFILE/IMAGE URL] {wu_supathinee.id} | Clear PSU profile & image")
            report["cross_urls_sanitized"].append({"id": wu_supathinee.id, "field": "profile_url", "old": old_p, "new": "https://science.wu.ac.th/"})
            report["cross_urls_sanitized"].append({"id": wu_supathinee.id, "field": "image_url", "old": old_img, "new": None})
            if apply_changes:
                wu_supathinee.profile_url = "https://science.wu.ac.th/"
                wu_supathinee.image_url = None

        # 2e. Kiattawee Choowongkomon (KU Science)
        ku_kiat = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0003").first()
        if ku_kiat:
            old_img = ku_kiat.image_url
            print(f"  [IMAGE URL] {ku_kiat.id} | Clear Mahidol image -> None")
            report["cross_urls_sanitized"].append({"id": ku_kiat.id, "field": "image_url", "old": old_img, "new": None})
            if apply_changes:
                ku_kiat.image_url = None

        # =========================================================================
        # 3. THAKSIN UNIVERSITY MUSE DUPLICATES AND REALIGNMENT
        # =========================================================================
        print("\n=== 3. THAKSIN UNIVERSITY MUSE CLEANUP ===")

        # 3a. Merge 5 duplicate pairs
        for pair in TSU_MUSE_DUPLICATES:
            donor = db.query(FacultyDB).filter(FacultyDB.id == pair["donor_id"]).first()
            target = db.query(FacultyDB).filter(FacultyDB.id == pair["target_id"]).first()
            if donor and target:
                print(f"  [MERGE DUPLICATE] Donor {donor.id} -> Target {target.id} ({target.full_name_th})")
                print(f"    Email: {target.email} -> {donor.email}")
                print(f"    Citations: {target.total_citations} -> max({target.total_citations}, {donor.total_citations})")
                print(f"    H-index: {target.h_index} -> max({target.h_index}, {donor.h_index})")

                report["tsu_muse_duplicates_merged"].append({
                    "donor_id": donor.id,
                    "target_id": target.id,
                    "name": target.full_name_th,
                    "email": donor.email,
                })

                if apply_changes:
                    # Update target with donor's email and metrics
                    if donor.email and not target.email:
                        target.email = donor.email
                    target.total_citations = max(target.total_citations or 0, donor.total_citations or 0)
                    target.h_index = max(target.h_index or 0, donor.h_index or 0)
                    target.total_publications_count = max(target.total_publications_count or 0, donor.total_publications_count or 0)
                    if donor.openalex_id and not target.openalex_id:
                        target.openalex_id = donor.openalex_id
                    if donor.scholar_url and not target.scholar_url:
                        target.scholar_url = donor.scholar_url

                    # Merge publications & education
                    donor_pubs = donor.featured_publications or []
                    target_pubs = target.featured_publications or []
                    seen_titles = set(p.get("title", "") for p in target_pubs if isinstance(p, dict))
                    for p in donor_pubs:
                        if isinstance(p, dict) and p.get("title") and p.get("title") not in seen_titles:
                            target_pubs.append(p)
                            seen_titles.add(p.get("title"))
                    target.featured_publications = target_pubs

                    # Ensure target canonical naming
                    target.faculty_th = "คณะสหวิทยาการและการประกอบการ"
                    target.faculty = "Faculty of Multidisciplinary Studies and Entrepreneurship"
                    target.department_th = "คณะสหวิทยาการและการประกอบการ"
                    target.department = "Faculty of Multidisciplinary Studies and Entrepreneurship"
                    target.embedding_text = build_faculty_embedding_text(target)

                    # Delete donor record
                    db.delete(donor)

        # 3b. Realign remaining Thaksin faculty labeled "คณะดุริยางคศาสตร์"
        tsu_remaining = db.query(FacultyDB).filter(
            FacultyDB.university_th == "มหาวิทยาลัยทักษิณ",
            FacultyDB.faculty_th == "คณะดุริยางคศาสตร์"
        ).all()
        for f in tsu_remaining:
            # Skip if it was one of the donors deleted above
            if any(f.id == p["donor_id"] for p in TSU_MUSE_DUPLICATES):
                continue

            print(f"  [REALIGN FACULTY] {f.id} | {f.full_name_th} | คณะดุริยางคศาสตร์ -> คณะสหวิทยาการและการประกอบการ")
            cleaned_interests = [i for i in (f.research_interests or []) if i != "คณะดุริยางคศาสตร์"]
            report["tsu_muse_faculty_realigned"].append({
                "id": f.id,
                "name": f.full_name_th,
                "cleaned_interests": cleaned_interests,
            })
            if apply_changes:
                f.faculty_th = "คณะสหวิทยาการและการประกอบการ"
                f.faculty = "Faculty of Multidisciplinary Studies and Entrepreneurship"
                f.department_th = "คณะสหวิทยาการและการประกอบการ"
                f.department = "Faculty of Multidisciplinary Studies and Entrepreneurship"
                f.research_interests = cleaned_interests
                f.embedding_text = build_faculty_embedding_text(f)

        # =========================================================================
        # 4. COMPOUND / MISPLACED FACULTY REPAIRS
        # =========================================================================
        print("\n=== 4. COMPOUND & MISPLACED FACULTY REPAIRS ===")

        # 4a. Purge corrupted incomplete record mahidoluni_facultyofm_fac_015_015
        f_corrupt = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_fac_015_015").first()
        if f_corrupt:
            print(f"  [PURGE CORRUPT] {f_corrupt.id} | '{f_corrupt.full_name_th}' (No last name, no department, no email)")
            if apply_changes:
                db.delete(f_corrupt)

        # 4b. Re-affiliate 2 Chulalongkorn Medicine faculty
        # Trairak Pisitkun
        f_trairak = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_pisitkun_018").first()
        if f_trairak:
            print(f"  [RE-AFFILIATE CU] {f_trairak.id} | {f_trairak.full_name_th} -> Chula Medicine Systems Biology")
            report["chula_medicine_reaffiliated"].append({
                "id": f_trairak.id,
                "name": f_trairak.full_name_th,
                "to_uni": "จุฬาลงกรณ์มหาวิทยาลัย",
                "to_fac": "คณะแพทยศาสตร์"
            })
            if apply_changes:
                f_trairak.university = "Chulalongkorn University"
                f_trairak.university_th = "จุฬาลงกรณ์มหาวิทยาลัย"
                f_trairak.faculty = "Faculty of Medicine"
                f_trairak.faculty_th = "คณะแพทยศาสตร์"
                f_trairak.department = "Center of Excellence in Systems Biology"
                f_trairak.department_th = "ศูนย์เชี่ยวชาญเฉพาะทางด้านชีววิทยาระบบ"
                f_trairak.academic_title_th = "รศ.ดร. นพ."
                f_trairak.academic_title = "Assoc. Prof. Dr."
                f_trairak.profile_url = "https://www.med.chula.ac.th/"
                f_trairak.research_interests = ["Systems Biology", "Proteomics", "Bioinformatics", "Kidney Disease Mechanisms"]
                f_trairak.embedding_text = build_faculty_embedding_text(f_trairak)

        # Surasak Wannakrairot
        f_surasak = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_wannakrairot_020").first()
        if f_surasak:
            print(f"  [RE-AFFILIATE CU] {f_surasak.id} | {f_surasak.full_name_th} -> Chula Medicine Pathology")
            report["chula_medicine_reaffiliated"].append({
                "id": f_surasak.id,
                "name": f_surasak.full_name_th,
                "to_uni": "จุฬาลงกรณ์มหาวิทยาลัย",
                "to_fac": "คณะแพทยศาสตร์"
            })
            if apply_changes:
                f_surasak.university = "Chulalongkorn University"
                f_surasak.university_th = "จุฬาลงกรณ์มหาวิทยาลัย"
                f_surasak.faculty = "Faculty of Medicine"
                f_surasak.faculty_th = "คณะแพทยศาสตร์"
                f_surasak.department = "Department of Pathology"
                f_surasak.department_th = "ภาควิชาพยาธิวิทยา"
                f_surasak.academic_title_th = "ผศ. นพ."
                f_surasak.academic_title = "Asst. Prof."
                f_surasak.profile_url = "https://www.med.chula.ac.th/"
                f_surasak.research_interests = ["Anatomical Pathology", "Surgical Pathology", "Cytopathology"]
                f_surasak.embedding_text = build_faculty_embedding_text(f_surasak)

        # 4c. Name repairs for Mahidol Medicine
        f_piti = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_thuvasethakul_003").first()
        if f_piti:
            print(f"  [NAME REPAIR] {f_piti.id} | '{f_piti.full_name_th}' -> 'รศ.ดร. นพ.ปีติ ธุวะเศรษฐกุล'")
            if apply_changes:
                f_piti.full_name_th = "รศ.ดร. นพ.ปีติ ธุวะเศรษฐกุล"
                f_piti.last_name = "Thuvasethakul"

        f_bovornsom = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_facultyofm_leerapan_019").first()
        if f_bovornsom:
            print(f"  [NAME REPAIR] {f_bovornsom.id} | '{f_bovornsom.full_name_th}' -> 'อ.ดร. นพ.บวรศม ลีระพันธ์'")
            if apply_changes:
                f_bovornsom.full_name_th = "อ.ดร. นพ.บวรศม ลีระพันธ์"
                f_bovornsom.first_name = "Bovornsom"
                f_bovornsom.last_name = "Leerapan"
                f_bovornsom.academic_title_th = "อ.ดร. นพ."
                f_bovornsom.academic_title = "Dr."

        # 4d. Separate Mahidol Ramathibodi vs Siriraj
        for rid in RAMA_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == rid).first()
            if f:
                print(f"  [MAHIDOL RAMA] {f.id} | {f.full_name_th} -> คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี")
                report["mahidol_medicine_de_compounded"].append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี"
                })
                if apply_changes:
                    f.faculty_th = "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี"
                    f.faculty = "Faculty of Medicine Ramathibodi Hospital"
                    f.embedding_text = build_faculty_embedding_text(f)

        for sid in SIRIRAJ_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == sid).first()
            if f:
                print(f"  [MAHIDOL SIRIRAJ] {f.id} | {f.full_name_th} -> คณะแพทยศาสตร์ศิริราชพยาบาล")
                report["mahidol_medicine_de_compounded"].append({
                    "id": f.id,
                    "name": f.full_name_th,
                    "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล"
                })
                if apply_changes:
                    f.faculty_th = "คณะแพทยศาสตร์ศิริราชพยาบาล"
                    f.faculty = "Faculty of Medicine Siriraj Hospital"
                    f.embedding_text = build_faculty_embedding_text(f)

        # 4e. Kasetsart University Agro vs Vet
        ku_agro_ids = ["kasetsartu_facultyofa_vityakiat_009", "kasetsartu_facultyofa_tansakul_008"]
        for kid in ku_agro_ids:
            f = db.query(FacultyDB).filter(FacultyDB.id == kid).first()
            if f:
                print(f"  [KU AGRO] {f.id} | {f.full_name_th} -> คณะอุตสาหกรรมเกษตร")
                report["ku_and_buu_de_compounded"].append({"id": f.id, "faculty_th": "คณะอุตสาหกรรมเกษตร"})
                if apply_changes:
                    f.faculty_th = "คณะอุตสาหกรรมเกษตร"
                    f.faculty = "Faculty of Agro-Industry"
                    f.embedding_text = build_faculty_embedding_text(f)

        f_vet = db.query(FacultyDB).filter(FacultyDB.id == "kasetsartu_facultyofa_pichai_022").first()
        if f_vet:
            print(f"  [KU VET] {f_vet.id} | {f_vet.full_name_th} -> คณะสัตวแพทยศาสตร์")
            report["ku_and_buu_de_compounded"].append({"id": f_vet.id, "faculty_th": "คณะสัตวแพทยศาสตร์"})
            if apply_changes:
                f_vet.faculty_th = "คณะสัตวแพทยศาสตร์"
                f_vet.faculty = "Faculty of Veterinary Medicine"
                f_vet.embedding_text = build_faculty_embedding_text(f_vet)

        # 4f. Burapha University Science
        buu_ids = ["buu_sci_sarawut_001", "buu_marine_voranop_001"]
        for bid in buu_ids:
            f = db.query(FacultyDB).filter(FacultyDB.id == bid).first()
            if f:
                print(f"  [BUU SCI] {f.id} | {f.full_name_th} -> คณะวิทยาศาสตร์")
                report["ku_and_buu_de_compounded"].append({"id": f.id, "faculty_th": "คณะวิทยาศาสตร์"})
                if apply_changes:
                    f.faculty_th = "คณะวิทยาศาสตร์"
                    f.faculty = "Faculty of Science"
                    f.embedding_text = build_faculty_embedding_text(f)

        # Commit or Rollback
        if apply_changes:
            db.commit()
            print("\n>>> All secondary scan repairs committed successfully to PostgreSQL.")
        else:
            db.rollback()
            print("\n>>> DRY RUN complete. No database changes were committed.")

    finally:
        db.close()

    out_file = (
        BACKEND_DIR / "data" / "agent_states" / "secondary_scan_repairs_apply.json"
        if apply_changes
        else BACKEND_DIR / "data" / "agent_states" / "secondary_scan_repairs_dryrun.json"
    )
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Audit state saved to: {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply secondary scan repairs.")
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    args = parser.parse_args()

    run_repairs(apply_changes=args.apply)
