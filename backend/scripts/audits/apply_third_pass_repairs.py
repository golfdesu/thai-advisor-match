"""Third-Pass Database Remediation Script:
1. Merge same-person duplicate pairs (preserving max citations, publications, canonical Thai name, OpenAlex ID).
2. Sanitize cross-contaminated personal emails.
3. Sanitize generic departmental shared inboxes.
4. Normalize parentheses in names and titles.
5. Normalize glued/duplicate titles (e.g. 'ดร. อ. ดร.' -> 'อ.ดร.', 'รศ.ดร. Dr.' -> 'รศ.ดร.').
6. Re-generate embedding_text for all modified records.

Supports --dry-run (default) and --apply.
"""
import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text

# 1. Same-Person Duplicate Pairs: (donor_id, target_id, target_name_override, target_title_override)
DUPLICATE_PAIRS = [
    # Prominent cross-batch & cross-lingual duplicates
    ("cmu_cb0c6016_3425", "cmu_med_nipon_001", "ศ.ดร. นพ. นิพนธ์ ฉัตรทิพากร", "ศ.ดร. นพ."),
    ("cmu_6a741569_7688", "cmu_bmei_siriporn_001", "ศ.ดร. ทพญ. สิริพร ฉัตรทิพากร", "ศ.ดร. ทพญ."),
    ("cmu_3bcc79a3_6324", "cmu_econ_songsak_001", "ศ.ดร. ทรงศักดิ์ ศรีบุญจิตต์", "ศ.ดร."),
    ("tu_bus_tbs_018", "tu_tbs_peter_001", "รศ.ดร. ปีเตอร์ รักธรรม", "รศ.ดร."),
    ("chulalongk_facultyofs_fac_007_007", "chula_sci_002_8742ad", "ศ.ดร. สนอง เอกสิทธิ์", "ศ.ดร."),
    ("chulalongk_facultyofs_fac_017_017", "cu_sci_wave14_b_0031", "ผศ.ดร. นำพล อินสิน", "ผศ.ดร."),
    ("chulalongk_facultyofs_fac_021_021", "cu_sci_wave14_b_0039", "ศ.ดร. พัชณิตา ธรรมยงค์กิจ", "ศ.ดร."),
    ("chulalongk_facultyofs_fac_006_006", "cu_sci_wave14_b_0034", "รศ.ดร. ปกรณ์ วรานุศุภากุล", "รศ.ดร."),
    ("chulalongk_facultyofs_fac_014_014", "cu_sci_wave14_b_0037", "ผศ.ดร. ภาณุวัฒน์ ผดุงรส", "ผศ.ดร."),
    ("mahidoluni_facultyofs_tsakdapipanich_011", "mu_sci_wave14_b_0019", "ศ.ดร. จิตต์ลัดดา ศักดาภิพาณิชย์", "ศ.ดร."),
    ("chulalongk_facultyofv_taw_112", "chulalongk_facultyofv_taweethavonsawa_126", "รศ.ดร. ปิยนันท์ ทวีถาวรสวัสดิ์", "รศ.ดร."),
    ("kku_eng_wave12_0020", "kku_eng_kanchana_001", "ศ.ดร. กาญจนา เศรษฐนันท์", "ศ.ดร."),
    ("kku_1dd5e0f1_2035", "khonkaenun_collegeofc_leelapatra_062", "อ.ดร. วทิศ ลีลาภัทร", "อ.ดร."),
    ("kku_dd282888_5274", "khonkaenun_collegeofc_tientanopajai_051", "อ.ดร. กิตติ์ เธียรธโนปจัย", "อ.ดร."),
    ("kku_5412fb44_5980", "khonkaenun_collegeofc_chaopanon_061", "อ.ดร. วสุ เจ้าพนานนท์", "อ.ดร."),
    ("mfu_it_chucherd_011", "mfu_sirikan_chucherd_1962", "ผศ.ดร. ศิริกานต์ ชูเชิด", "ผศ.ดร."),
    ("mfu_it_teeravisit_001", "mfu_teeravisit_laohapensaeng_4118", "ผศ.ดร. ธีรวิศิฏฐ์ เลาหะเพ็ญแสง", "ผศ.ดร."),
    ("mahidoluni_collegeofm_boonyam_035", "mahidoluni_collegeofm_boonyam_080", "ผศ.ดร. เตรทิพย์ บุญแย้ม", "ผศ.ดร."),
    ("mahidoluni_collegeofm_bowman_036", "mahidoluni_collegeofm_bowman_143", "ผศ.ดร. Joseph Bowman", "ผศ.ดร."),
    ("mahidoluni_collegeofm_szawelski_213", "mahidoluni_collegeofm_szawelski_123", "อ. Marcin Szawelski", "อ."),
    ("mahidoluni_collegeofm_leeswadtrakul_006", "mahidoluni_collegeofm_lee_151", "อ. Shyen Lee", "อ."),
    ("chulalongk_facultyofv_fac_163_163", "chulalongk_facultyofv_chansiriporncha_169", "รศ.ดร. สพ.ญ. ปิยะรัตน์ จันทร์ศิริพรชัย", "รศ.ดร. สพ.ญ."),
    ("chulalongk_facultyofv_fac_164_164", "chulalongk_facultyofv_suwanprparin_172", "ผศ.ดร. สพ.ญ. นิภัทรา สวนไพรินทร์", "ผศ.ดร. สพ.ญ."),
    ("chulalongk_facultyofv_thammacharoen_079", "chulalongk_facultyofv_thamcharoen_068", "รศ. น.สพ. ดร. สัมพันธ์ ธรรมเจริญ", "รศ. น.สพ. ดร."),
    ("kasetsartu_facultyofv_sasadi_009", "ku_wave17_vettech_0011", "รศ.ดร. เมทิตา สัสดี", "รศ.ดร."),
    ("kasetsartu_facultyofv_raksaken_007", "ku_wave17_vettech_0012", "รศ.ดร. รักศักดิ์ รักษาเคน", "รศ.ดร."),
    ("tu_eng_001", "thammasatu_facultyofe_supakwong_029", "รศ.ดร. ศุภวัฒน์ สุภัควงศ์", "รศ.ดร.")
]

# 2. Contaminated Emails to Clear (faculty_id, reason)
CONTAMINATED_EMAILS_TO_CLEAR = [
    ("mu-ph-014_db2f3f", "songsak.sri@mahidol.ac.th belongs to Songsak Srianujata"),
    ("mahidoluni_collegeofm_klinsmith_057", "suvich.kli@mahidol.ac.th belongs to Suvich Klinsmith"),
    ("cmu-eng-011_00e66f", "chatchawan.c@cmu.ac.th belongs to Chatchawan Chaichana"),
    ("mfu_integ_sulakkana_001", "sulakkana.noi@mfu.ac.th belongs to Sulakkana Noiprasert"),
    ("cmu-eng-019_080c1b", "somchai.p@cmu.ac.th belongs to Somchai Preechasilpakul"),
    ("camt-cmu-011_fb36c6", "narissara.e@cmu.ac.th belongs to Narissara Eiamkanitchat"),
    ("cu_sci_wave14_b_0025", "nattapong.p@chula.ac.th belongs to Nattapong Puttanapong"),
    ("kmutt_13ee518d_7562", "songsirin.rue@mail.kmutt.ac.th belongs to Songsirin Ruengvisesh"),
    ("mahidoluni_collegeofm_sirilertworakul_011", "siri.sra@mahidol.ac.th belongs to Siri Sranoi"),
    ("thammasatu_thammasatb_fac_051_051", "krit@tbs.tu.ac.th belongs to Krit Pattamaroj"),
    ("ku_wave18_agrips_0045", "fagrkks@ku.ac.th belongs to Kriangkrai Sookhong"),
    ("mahidoluni_collegeofm_jittipichayanan_059", "hyuk.cha@mahidol.edu belongs to Thomas Hyuk Cha"),
    ("su_eng_teacher_090", "sujin@su.ac.th belongs to Sujin Wuttichaiwat"),
    ("su_eng_teacher_125", "patipat@su.ac.th belongs to Patipat Hongsuwan"),
    ("cmu-eng-006_75c670", "korakot.n@cmu.ac.th belongs to Korakot Nganvongpanit"),
    ("mju_7ff309f6_7735", "sanwasan@mju.ac.th belongs to Sanwasan Yodkham"),
    ("ku-sci-math-007_6f2b83", "fsciwcp@ku.ac.th belongs to Wanchai Pluempanupat"),
    ("cmu-nurse-017_4869dd", "natthaphat.s@cmu.ac.th belongs to Natthaphat Siri-angkul"),
    ("chula_sci_014_d03e15", "siriwat.s@chula.ac.th belongs to Siriwat Suatsong"),
    ("mahidoluni_collegeofm_cooper_031", "cooper.wri@mahidol.ac.th belongs to Cooper Wright"),
    ("mahidoluni_facultyofs_laowattanakul_100", "tana.tac@mahidol.ac.th belongs to Tana Taechalertpaisarn"),
    ("cu_cbs_wave11_0147", "anant@acc.chula.ac.th belongs to Anantanat Kunthanyarat"),
    ("nida_as_001", "surapong@as.nida.ac.th belongs to Surapong Auwatanamongkol"),
    ("ku-hum-020_290f0d", "fhumnrk@ku.ac.th belongs to Narong Khienthongkul"),
    ("ku-sci-cs-002_cf7bc3", "fscipph@ku.ac.th belongs to Pimpa Hormnirun"),
    ("cu_sports_siriporn_001", "siriporn.sa@chula.ac.th belongs to Siriporn Sangsuthum"),
    ("sut_apinun_buritatum_6141", "tosaphol@sut.ac.th belongs to Tosaphol Ratniyomchai"),
    ("ku_forest_wave15_0084", "fforpts@ku.ac.th belongs to Phitaktrakul Sriprom"),
    ("sut_eng_chantima_001", "chantima@sut.ac.th belongs to Chantima Deeprasertkul"),
    ("sut_eng_nittaya_001", "nittaya@sut.ac.th belongs to Nittaya Kerdprasop"),
    ("sut_teetut_dolwichai_1031", "prapun@sut.ac.th belongs to Prapun Manyum"),
    ("nu_kumropr__8257", "kumropr@nu.ac.th belongs to Kumrop Raksasate"),
    ("cmu-law-0014_2b5111", "siriporn.c@cmu.ac.th belongs to Siriporn Chattipakorn"),
    # Generic departmental shared inboxes
    ("srinakha_facultyo_06bfc545", "generic departmental surgery inbox surgery.med@g.swu.ac.th"),
    ("srinakha_facultyo_6918d2c3", "generic departmental surgery inbox surgery.med@g.swu.ac.th"),
    ("kmutt_eng_cpe_017", "generic staff email nongyao.jam@mail.kmutt.ac.th"),
    ("kmutt_eng_cpe_026", "generic staff email nongyao.jam@mail.kmutt.ac.th"),
    # Syntax corrupt email
    ("mahidoluni_collegeofm_harimpanich_165", "syntax corrupt email seri'lim@mahidol.ac.th")
]

# 3. Parentheses in Names Normalization: (id, new_full_name, new_title, new_first, new_last)
PARENTHESES_NORMALIZATIONS = [
    ("cmu_58ee6d12_3751", "ศ.เชี่ยวชาญพิเศษ ดร. นพ. กิตติพันธุ์ ฤกษ์เกษม", "ศ.เชี่ยวชาญพิเศษ ดร. นพ.", "กิตติพันธุ์", "ฤกษ์เกษม"),
    ("chulalongk_facultyofv_fac_158_158", "รศ.ดร. สพ.ญ. วรา พานิชเกรียงไกร", "รศ.ดร. สพ.ญ.", "วรา", "พานิชเกรียงไกร"),
    ("chulalongk_facultyofv_fac_159_159", "รศ.ดร. ภญ. สุพัตรา ศรีไชยรัตน์", "รศ.ดร. ภญ.", "สุพัตรา", "ศรีไชยรัตน์"),
    ("cmu_103fe821_4247", "ศ.เชี่ยวชาญพิเศษ ดร. ทพ. อะนัฆ เอี่ยมอรุณ", "ศ.เชี่ยวชาญพิเศษ ดร. ทพ.", "อะนัฆ", "เอี่ยมอรุณ"),
    ("ku_agro_wave15_0038", "รศ.ดร. สงวนศรี เจริญเหรียญ", "รศ.ดร.", "สงวนศรี", "เจริญเหรียญ"),
    ("ku_agro_wave15_0039", "รศ.ดร. สิรี ชัยเสรี", "รศ.ดร.", "สิรี", "ชัยเสรี"),
    ("ku_agro_wave15_0040", "ศ.ดร. อรอนงค์ นัยวิกุล", "ศ.ดร.", "อรอนงค์", "นัยวิกุล"),
    ("ku_agro_wave15_0041", "ผศ.ดร. ธนะบูลย์ สัจจาอนันตกุล", "ผศ.ดร.", "ธนะบูลย์", "สัจจาอนันตกุล"),
    ("ku_agro_wave15_0042", "รศ.ดร. ปริศนา สุวรรณาภรณ์", "รศ.ดร.", "ปริศนา", "สุวรรณาภรณ์"),
    ("ku_agro_wave15_0043", "รศ.ดร. ปาริฉัตร หงสประภาส", "รศ.ดร.", "ปาริฉัตร", "หงสประภาส"),
    ("ku_agro_wave15_0044", "รศ.ดร. วราภา มหากาญจนกุล", "รศ.ดร.", "วราภา", "มหากาญจนกุล"),
    ("chulalongk_facultyofv_fac_153_153", "อ. สุพิศ จินดาวณิค", "อ.", "สุพิศ", "จินดาวณิค"),
    ("chiangmaiu_facultyofv_suriyasathaporn_082", "ศ.คลินิก ดร. สพ.ญ. วรรณนา สุริยาสถาพร", "ศ.คลินิก ดร. สพ.ญ.", "วรรณนา", "สุริยาสถาพร"),
    ("cu_7baa4e89_2397", "ผศ.พิเศษ พญ. สาริน เล็กชื่นสกุล", "ผศ.พิเศษ พญ.", "สาริน", "เล็กชื่นสกุล"),
    ("cu_eddd86df_1649", "ผศ.พิเศษ พญ. อังควิภา ทรัพย์รุ่งเรือง", "ผศ.พิเศษ พญ.", "อังควิภา", "ทรัพย์รุ่งเรือง"),
    ("chulalongk_facultyofv_fac_160_160", "รศ.ดร. สพ.ญ. อนงค์ บิณฑวิหค", "รศ.ดร. สพ.ญ.", "อนงค์", "บิณฑวิหค"),
    ("silpakornu_facultyofa_chainakut_015", "ศ.เกียรติคุณ พงศ์เดช ไชยคุตร", "ศ.เกียรติคุณ", "พงศ์เดช", "ไชยคุตร"),
    ("cu_cbs_wave11_0096", "รศ.ดร. Savanid Vatanasakdakul", "รศ.ดร.", "Savanid", "Vatanasakdakul"),
    ("cu_eng_chem_biorefinery_001", "ศ.ดร. อัญชลีพร วาริทสวัสดิ์", "ศ.ดร.", "อัญชลีพร", "วาริทสวัสดิ์"),
]

def run_repairs(apply_changes: bool = False):
    db = SessionLocal()
    try:
        print(f"=== THIRD-PASS DATABASE REMEDIATION ({'APPLY' if apply_changes else 'DRY-RUN'}) ===")
        report = {
            "apply": apply_changes,
            "duplicate_merges": [],
            "email_sanitizations": [],
            "parentheses_normalizations": [],
            "glued_title_normalizations": [],
            "embeddings_updated": 0
        }

        # 1. Merge Duplicate Pairs
        print(f"\n1. Merging {len(DUPLICATE_PAIRS)} duplicate pairs...")
        for donor_id, target_id, target_name_override, target_title_override in DUPLICATE_PAIRS:
            donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()
            target = db.query(FacultyDB).filter(FacultyDB.id == target_id).first()

            if not donor or not target:
                print(f"   [SKIP] Missing donor ({donor_id}: {bool(donor)}) or target ({target_id}: {bool(target)})")
                continue

            # Preservation logic
            prev_target_cites = target.total_citations or 0
            prev_target_name = target.full_name_th

            # Preserve maximum research metrics
            target.total_citations = max(donor.total_citations or 0, target.total_citations or 0)
            target.h_index = max(donor.h_index or 0, target.h_index or 0)
            target.total_publications_count = max(donor.total_publications_count or 0, target.total_publications_count or 0)

            # Preserve valid OpenAlex ID
            if (not target.openalex_id or target.openalex_id in ["not_indexed", "none", "null"]) and donor.openalex_id and donor.openalex_id not in ["not_indexed", "none", "null"]:
                target.openalex_id = donor.openalex_id

            # Preserve valid email
            if not target.email and donor.email:
                target.email = donor.email

            # Union research interests
            t_interests = [str(x) for x in (target.research_interests or [])]
            d_interests = [str(x) for x in (donor.research_interests or [])]
            target.research_interests = list(dict.fromkeys(t_interests + d_interests))

            # Union featured publications safely (dicts or strings)
            seen_pub_keys = set()
            merged_pubs = []
            for p in (target.featured_publications or []) + (donor.featured_publications or []):
                if isinstance(p, dict):
                    pkey = p.get("doi") or p.get("title") or json.dumps(p, sort_keys=True)
                else:
                    pkey = str(p)
                if pkey not in seen_pub_keys:
                    seen_pub_keys.add(pkey)
                    merged_pubs.append(p)
            target.featured_publications = merged_pubs

            # Apply name and title overrides
            if target_name_override:
                target.full_name_th = target_name_override
            if target_title_override:
                target.academic_title_th = target_title_override

            # Re-point foreign keys (Research Labs lead advisor & member faculty)
            labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).all()
            for lab in labs:
                lab.lead_advisor_id = target.id

            all_labs = db.query(ResearchLabDB).all()
            for lab in all_labs:
                if lab.member_faculty_ids and donor.id in lab.member_faculty_ids:
                    lab.member_faculty_ids = [target.id if m == donor.id else m for m in lab.member_faculty_ids]

            # Update embedding text
            target.embedding_text = build_faculty_embedding_text(target)

            merge_info = {
                "donor_id": donor.id,
                "donor_name": donor.full_name_th,
                "target_id": target.id,
                "target_name": target.full_name_th,
                "citations_preserved": target.total_citations,
                "labs_repointed": len(labs)
            }
            report["duplicate_merges"].append(merge_info)
            print(f"   [MERGE] {donor.id} ({donor.full_name_th}) -> {target.id} ({target.full_name_th}) | cites: {prev_target_cites} -> {target.total_citations}")

            # Delete donor
            db.delete(donor)

        # 2. Sanitize Contaminated Emails
        print(f"\n2. Sanitizing {len(CONTAMINATED_EMAILS_TO_CLEAR)} contaminated emails...")
        for fac_id, reason in CONTAMINATED_EMAILS_TO_CLEAR:
            fac = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if not fac:
                continue
            prev_email = fac.email
            fac.email = None
            fac.embedding_text = build_faculty_embedding_text(fac)
            san_info = {
                "id": fac.id,
                "name": fac.full_name_th,
                "cleared_email": prev_email,
                "reason": reason
            }
            report["email_sanitizations"].append(san_info)
            print(f"   [CLEAR] {fac.id} ({fac.full_name_th}) cleared email '{prev_email}' ({reason})")

        # 3. Normalize Parentheses Records
        print(f"\n3. Normalizing {len(PARENTHESES_NORMALIZATIONS)} parentheses records...")
        for fac_id, new_full_name, new_title, new_first, new_last in PARENTHESES_NORMALIZATIONS:
            fac = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if not fac:
                continue
            prev_name = fac.full_name_th
            fac.full_name_th = new_full_name
            fac.academic_title_th = new_title
            fac.first_name = new_first
            fac.last_name = new_last
            fac.embedding_text = build_faculty_embedding_text(fac)
            norm_info = {
                "id": fac.id,
                "old_name": prev_name,
                "new_name": new_full_name,
                "new_title": new_title
            }
            report["parentheses_normalizations"].append(norm_info)
            print(f"   [NORM PAREN] {fac.id}: '{prev_name}' -> '{new_full_name}'")

        # 4. Normalize Glued / Duplicate Titles (e.g. 'ดร. อ. ดร.')
        print("\n4. Normalizing glued/duplicate titles across remaining records...")
        faculties = db.query(FacultyDB).all()
        for fac in faculties:
            if not fac.full_name_th:
                continue
            old_name = fac.full_name_th
            new_name = old_name

            # Fix 'ดร. อ. ดร. ...'
            if re.match(r"^ดร\.\s*อ\.\s*ดร\.\s*", new_name):
                new_name = re.sub(r"^ดร\.\s*อ\.\s*ดร\.\s*", "อ.ดร. ", new_name)
                fac.academic_title_th = "อ.ดร."

            # Fix 'รศ.ดร. Dr. ...'
            if re.match(r"^รศ\.ดร\.\s*Dr\.\s*", new_name):
                new_name = re.sub(r"^รศ\.ดร\.\s*Dr\.\s*", "รศ.ดร. ", new_name)
                fac.academic_title_th = "รศ.ดร."

            # Fix 'ดร. Dr. ...'
            if re.match(r"^ดร\.\s*Dr\.\s*", new_name):
                new_name = re.sub(r"^ดร\.\s*Dr\.\s*", "ดร. ", new_name)
                fac.academic_title_th = "ดร."

            # Fix English titles glued to Thai title prefixes: 'ศ.ดร. Prof. Dr. ...'
            if re.match(r"^ศ\.ดร\.\s*Prof\.\s*(Dr\.)?\s*", new_name):
                new_name = re.sub(r"^ศ\.ดร\.\s*Prof\.\s*(Dr\.)?\s*", "ศ.ดร. ", new_name)
                fac.academic_title_th = "ศ.ดร."

            # Fix 'รศ.ดร. Assoc. Prof. (Dr.)? ...'
            if re.match(r"^รศ\.ดร\.\s*Assoc\.\s*Prof\.\s*(Dr\.)?\s*", new_name):
                new_name = re.sub(r"^รศ\.ดร\.\s*Assoc\.\s*Prof\.\s*(Dr\.)?\s*", "รศ.ดร. ", new_name)
                fac.academic_title_th = "รศ.ดร."

            # Fix 'ผศ.ดร. Asst. Prof. (Dr.)? ...'
            if re.match(r"^ผศ\.ดร\.\s*Asst\.\s*Prof\.\s*(Dr\.)?\s*", new_name):
                new_name = re.sub(r"^ผศ\.ดร\.\s*Asst\.\s*Prof\.\s*(Dr\.)?\s*", "ผศ.ดร. ", new_name)
                fac.academic_title_th = "ผศ.ดร."

            if new_name != old_name:
                fac.full_name_th = new_name
                fac.embedding_text = build_faculty_embedding_text(fac)
                report["glued_title_normalizations"].append({
                    "id": fac.id,
                    "old_name": old_name,
                    "new_name": new_name,
                    "title": fac.academic_title_th
                })
                print(f"   [NORM TITLE] {fac.id}: '{old_name}' -> '{new_name}'")

        report["embeddings_updated"] = (
            len(report["duplicate_merges"]) +
            len(report["email_sanitizations"]) +
            len(report["parentheses_normalizations"]) +
            len(report["glued_title_normalizations"])
        )

        out_name = "third_pass_repairs_apply.json" if apply_changes else "third_pass_repairs_dryrun.json"
        out_path = BACKEND_DIR / "data" / "agent_states" / out_name
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReport saved to: {out_path}")

        if apply_changes:
            db.commit()
            print("Database transaction COMMITTED successfully.")
        else:
            db.rollback()
            print("Dry run completed. Database rolled back cleanly.")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply changes to database")
    args = parser.parse_args()
    run_repairs(apply_changes=args.apply)
