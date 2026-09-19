# -*- coding: utf-8 -*-
"""
Apply Phase 2 Deep Database Hygiene Repairs.

Covers 8 Categories:
1. Merge duplicate faculty profiles (3 pairs):
   - chiangmaiu_facultyofa_wirjantoro_002 -> cmu_d542da29_8423 (Tri Indrarini Wirjantoro)
   - mahidoluni_collegeofm_jung_208 -> mahidoluni_collegeofm_jung_155 (Yu-Jin Jung)
   - chula_eng_cp_chentanez -> cu_eng_wave13_0004 (Nuttapong Chentanez)
2. Purge crawler address footer record (1 record):
   - kku_eng_wave12_0046 (ต.ในเมือง อ.เมือง จ.ขอนแก่น parsed into faculty)
3. Restore noble & compound Thai surnames ('ณ' and 'ต.') (5 records):
   - cmu_ds_wave11_0016 (ภัทรหทัย ณ ลำพูน)
   - cu_eng_wave13_0068 (ดาลัด ณ นคร)
   - ku_sci_wave13_0048 (สุริยา ณ หนองคาย)
   - ku_sci_wave13_0003 (จิรโรจน์ ต.เทียนประเสริฐ)
   - ku_sci_wave13_b_0008 (ณัฐนันท์ ต.เทียนประเสริฐ)
4. Fix corrupted foreign-script / font-encoding glyphs & glued English in names (38 records).
5. Strip title prefixes and degree suffixes from English names (20 records).
6. Restore missing surnames & expand initial-only last names (MSU / KKU / PSU) (46 records).
7. Align bibliometric monotonicity for Mahidol Science (5 records).
8. Course credit bug & program_type standardization:
   - cmu_tqf_25490041110551 credits 368797 -> 36 หน่วยกิต
   - Standardize Mahidol 'Graduate' program types & variant labels.
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
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB
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


def apply_phase2_deep_repairs():
    db = SessionLocal()
    print("=" * 70)
    print("🚀 EXECUTING PHASE 2 DEEP DATABASE HYGIENE REPAIRS")
    print("=" * 70)

    try:
        # -------------------------------------------------------------
        # 1. MERGE DUPLICATE FACULTY PROFILES (3 pairs)
        # -------------------------------------------------------------
        # 1.1 Tri Indrarini Wirjantoro
        donor_tri = db.query(FacultyDB).filter(FacultyDB.id == "chiangmaiu_facultyofa_wirjantoro_002").first()
        target_tri = db.query(FacultyDB).filter(FacultyDB.id == "cmu_d542da29_8423").first()
        if donor_tri and target_tri:
            print(f"🔗 [1.1] Merging Tri Indrarini donor {donor_tri.id} into target {target_tri.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_tri.id).update(
                {ResearchLabDB.lead_advisor_id: target_tri.id}
            )
            if not target_tri.featured_publications and donor_tri.featured_publications:
                target_tri.featured_publications = donor_tri.featured_publications
                flag_modified(target_tri, "featured_publications")
            db.delete(donor_tri)

        # 1.2 Yu-Jin Jung
        donor_jung = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_collegeofm_jung_208").first()
        target_jung = db.query(FacultyDB).filter(FacultyDB.id == "mahidoluni_collegeofm_jung_155").first()
        if donor_jung and target_jung:
            print(f"🔗 [1.2] Merging Yu-Jin Jung donor {donor_jung.id} into target {target_jung.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_jung.id).update(
                {ResearchLabDB.lead_advisor_id: target_jung.id}
            )
            target_jung.first_name = "Yu-Jin"
            target_jung.last_name = "Jung"
            target_jung.full_name_th = "อ. Yu-Jin Jung"
            target_jung.embedding_text = build_standard_embedding_text(target_jung)
            db.delete(donor_jung)

        # 1.3 Nuttapong Chentanez
        donor_chen = db.query(FacultyDB).filter(FacultyDB.id == "chula_eng_cp_chentanez").first()
        target_chen = db.query(FacultyDB).filter(FacultyDB.id == "cu_eng_wave13_0004").first()
        if donor_chen and target_chen:
            print(f"🔗 [1.3] Merging Nuttapong Chentanez donor {donor_chen.id} into target {target_chen.id}")
            target_chen.full_name_th = "รศ.ดร. ณัฐพงศ์ ชินธเนศ"
            target_chen.academic_title_th = "รศ.ดร."
            target_chen.first_name = "Nuttapong"
            target_chen.last_name = "Chentanez"
            target_chen.total_citations = max(donor_chen.total_citations or 0, target_chen.total_citations or 0)
            target_chen.total_publications_count = max(donor_chen.total_publications_count or 0, target_chen.total_publications_count or 0)
            target_chen.h_index = max(donor_chen.h_index or 0, target_chen.h_index or 0)
            if not target_chen.featured_publications and donor_chen.featured_publications:
                target_chen.featured_publications = donor_chen.featured_publications
                flag_modified(target_chen, "featured_publications")
            target_chen.embedding_text = build_standard_embedding_text(target_chen)
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_chen.id).update(
                {ResearchLabDB.lead_advisor_id: target_chen.id}
            )
            db.delete(donor_chen)

        # 1.4 Jiraroj T-Thienprasert (KU Science)
        donor_jiraroj = db.query(FacultyDB).filter(FacultyDB.id == "ku_d0d43a11_6582").first()
        target_jiraroj = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_0003").first()
        if donor_jiraroj and target_jiraroj:
            print(f"🔗 [1.4] Merging Jiraroj donor {donor_jiraroj.id} into target {target_jiraroj.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_jiraroj.id).update(
                {ResearchLabDB.lead_advisor_id: target_jiraroj.id}
            )
            db.delete(donor_jiraroj)

        # 1.5 Nuttanan T-Thienprasert (KU Science)
        donor_nuttanan = db.query(FacultyDB).filter(FacultyDB.id == "ku_7566e1bc_6378").first()
        target_nuttanan = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0008").first()
        if donor_nuttanan and target_nuttanan:
            print(f"🔗 [1.5] Merging Nuttanan donor {donor_nuttanan.id} into target {target_nuttanan.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_nuttanan.id).update(
                {ResearchLabDB.lead_advisor_id: target_nuttanan.id}
            )
            db.delete(donor_nuttanan)

        # 1.6 Supawadee Daodee (KKU Pharmacy)
        donor_supawadee = db.query(FacultyDB).filter(FacultyDB.id == "kku_pharm_wave16_0029").first()
        target_supawadee = db.query(FacultyDB).filter(FacultyDB.id == "kku_pharm_supawadee_001").first()
        if donor_supawadee and target_supawadee:
            print(f"🔗 [1.6] Merging Supawadee donor {donor_supawadee.id} into target {target_supawadee.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_supawadee.id).update(
                {ResearchLabDB.lead_advisor_id: target_supawadee.id}
            )
            db.delete(donor_supawadee)

        # 1.7 Issaratt Assoratkul (Chula Dentistry)
        donor_issaratt = db.query(FacultyDB).filter(FacultyDB.id == "chulalongk_facultyofd_assoratkul_004").first()
        target_issaratt = db.query(FacultyDB).filter(FacultyDB.id == "cu_dent_wave15_0137").first()
        if donor_issaratt and target_issaratt:
            print(f"🔗 [1.7] Merging Issaratt donor {donor_issaratt.id} into target {target_issaratt.id}")
            target_issaratt.academic_title_th = "อ.ทพ.ดร."
            target_issaratt.full_name_th = "อ.ทพ.ดร. อิษฏ์ อัสโสรัตน์กุล"
            target_issaratt.first_name = "Issaratt"
            target_issaratt.last_name = "Assoratkul"
            target_issaratt.embedding_text = build_standard_embedding_text(target_issaratt)
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_issaratt.id).update(
                {ResearchLabDB.lead_advisor_id: target_issaratt.id}
            )
            db.delete(donor_issaratt)

        # 1.8 Chonlameth Arpnikanondt (KMUTT SIT)
        donor_chonlameth = db.query(FacultyDB).filter(FacultyDB.id == "kingmong_schoolof_1dc3129f").first()
        target_chonlameth = db.query(FacultyDB).filter(FacultyDB.id == "kmutt_sit_chonlameth_arpnikanondt").first()
        if donor_chonlameth and target_chonlameth:
            print(f"🔗 [1.8] Merging Chonlameth donor {donor_chonlameth.id} into target {target_chonlameth.id}")
            if not target_chonlameth.email and donor_chonlameth.email:
                target_chonlameth.email = donor_chonlameth.email
            if (not target_chonlameth.department_th or target_chonlameth.department_th == "คณะเทคโนโลยีสารสนเทศ") and donor_chonlameth.department_th:
                target_chonlameth.department_th = donor_chonlameth.department_th
            target_chonlameth.embedding_text = build_standard_embedding_text(target_chonlameth)
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_chonlameth.id).update(
                {ResearchLabDB.lead_advisor_id: target_chonlameth.id}
            )
            db.delete(donor_chonlameth)

        # -------------------------------------------------------------
        # 2. PURGE CRAWLER ADDRESS FOOTER RECORD (1 record)
        # -------------------------------------------------------------
        footer_fac = db.query(FacultyDB).filter(FacultyDB.id == "kku_eng_wave12_0046").first()
        if footer_fac:
            print(f"🗑️ [2] Purging crawler address footer faculty record: {footer_fac.id} ('{footer_fac.full_name_th}')")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == footer_fac.id).update(
                {ResearchLabDB.lead_advisor_id: None}
            )
            db.delete(footer_fac)

        # -------------------------------------------------------------
        # 3. RESTORE NOBLE & COMPOUND THAI SURNAMES ('ณ' and 'ต.') (5 records)
        # -------------------------------------------------------------
        noble_fixes = {
            "cmu_ds_wave11_0016": {
                "academic_title_th": "ผศ.ดร.",
                "full_name_th": "ผศ.ดร. ภัทรหทัย ณ ลำพูน",
                "first_name": "Pattarahathai",
                "last_name": "Na Lamphun",
            },
            "cu_eng_wave13_0068": {
                "academic_title_th": "อ.ดร.",
                "full_name_th": "อ.ดร. ดาลัด ณ นคร",
                "first_name": "Dalad",
                "last_name": "Na Nakorn",
            },
            "ku_sci_wave13_0048": {
                "academic_title_th": "ผศ.ดร.",
                "full_name_th": "ผศ.ดร. สุริยา ณ หนองคาย",
                "first_name": "Suriya",
                "last_name": "Na Nongkhai",
            },
            "ku_sci_wave13_0003": {
                "academic_title_th": "รศ.ดร.",
                "full_name_th": "รศ.ดร. จิรโรจน์ ต.เทียนประเสริฐ",
                "first_name": "Jiraroj",
                "last_name": "T-Thienprasert",
            },
            "ku_sci_wave13_b_0008": {
                "academic_title_th": "รศ.ดร.",
                "full_name_th": "รศ.ดร. ณัฐนันท์ ต.เทียนประเสริฐ",
                "first_name": "Nuttanan",
                "last_name": "T-Thienprasert",
            },
        }
        for fid, attrs in noble_fixes.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                print(f"👑 [3] Restoring noble/compound surname: {fid} -> {attrs['full_name_th']}")
                for k, v in attrs.items():
                    setattr(f, k, v)
                f.embedding_text = build_standard_embedding_text(f)

        # -------------------------------------------------------------
        # 4. FIX CORRUPTED FOREIGN-SCRIPT / FONT-ENCODING GLYPHS & GLUED ENGLISH (38 records)
        # -------------------------------------------------------------
        corrupted_name_fixes = {
            "cmu_1c5854e7_6808": {
                "full_name_th": "รศ.นพ. ชุมพล เจตจำนงค์",
                "academic_title_th": "รศ.นพ.",
                "first_name": "Chumpol",
                "last_name": "Chetjamnong",
            },
            "tu_siripen_tor_7224": {
                "full_name_th": "รศ. ศิริเพ็ญ ต่ออุดม",
                "academic_title_th": "รศ.",
                "first_name": "Siripen",
                "last_name": "Tor-udom",
            },
            "cu_cbs_wave11_0326": {
                "full_name_th": "อ. ฉัททวุฒิ พีชผล",
                "academic_title_th": "อ.",
                "first_name": "Chattavut",
                "last_name": "Peechapol",
            },
            "chulalongk_facultyofe_jantori_019": {
                "full_name_th": "ดร. ปาริฉัตร จันทรา",
                "academic_title_th": "ดร.",
                "first_name": "Parichat",
                "last_name": "Jantori",
            },
            "cmu_35d07752_0597": {
                "full_name_th": "อ.พญ. ณัชชา อรุณไพรโรจนกุล",
                "academic_title_th": "อ.พญ.",
                "first_name": "Natcha",
                "last_name": "Arunphairojanakul",
            },
            "kingmongku_schoolofen_chotiprayanakul_016": {
                "full_name_th": "ดร. พลชัย โชติประยานุกุล",
                "academic_title_th": "ดร.",
            },
            "kingmongku_schoolofen_hamontree_002": {
                "full_name_th": "ผศ.ดร. เชาวลิต หะมนตรี",
                "academic_title_th": "ผศ.ดร.",
            },
            "kingmongku_schoolofen_koiwanit_004": {
                "full_name_th": "รศ.ดร. จารุวรรณ กอยวานิช",
                "academic_title_th": "รศ.ดร.",
            },
            "mahidoluni_facultyoft_moonsom_080": {
                "full_name_th": "รศ.ดร. แสงเดือน มูลสม",
                "academic_title_th": "รศ.ดร.",
            },
            "mahidoluni_facultyoft_petmitr_002": {
                "full_name_th": "ศ.ดร. ทรงศักดิ์ เพชรมิตร",
                "academic_title_th": "ศ.ดร.",
            },
            "chulalongk_facultyofn_prachusilpa_016": {
                "full_name_th": "รศ.ดร. กันยดา ประจุศิลป์",
                "academic_title_th": "รศ.ดร.",
            },
            "chulalongk_facultyofn_treenai_029": {
                "full_name_th": "ผศ.ดร. สุรศักดิ์ ตรีไนย",
                "academic_title_th": "ผศ.ดร.",
            },
            "chulalongk_facultyofn_upasen_025": {
                "full_name_th": "รศ.ดร. รัชนีกร อุบเสน",
                "academic_title_th": "รศ.ดร.",
            },
            "chulalongk_facultyofn_waraphok_014": {
                "full_name_th": "อ. สินีนาถ วาราพุก",
                "academic_title_th": "อ.",
            },
            "mu_cmmu_001": {
                "full_name_th": "รศ.ดร. กิตติชัย ราชจำเริญ",
                "academic_title_th": "รศ.ดร.",
            },
            "chulalongk_facultyofn_kamonratananun_020": {
                "full_name_th": "ผศ.ดร. เนตรชนก กมลรัตนานันท์",
                "academic_title_th": "ผศ.ดร.",
            },
            "chulalongk_facultyofn_anuruang_008": {
                "full_name_th": "ผศ.ดร. ศกุนตลา อนุเรือง",
                "academic_title_th": "ผศ.ดร.",
            },
            "khonkaenun_facultyofn_payjapoh_050": {
                "full_name_th": "อ. จุฑามาศ ปัจจะพงษ์",
                "academic_title_th": "อ.",
            },
            "kingmongku_facultyofe_usadornsak_015": {
                "full_name_th": "ผศ.ดร. ฉัตรชัย อัษฎาศักดิ์",
                "academic_title_th": "ผศ.ดร.",
            },
            "mahidoluni_facultyoft_tajasuwan_140": {
                "full_name_th": "อ.ดร. ลลีวรรณ ตะจะสุวรรณ",
                "academic_title_th": "อ.ดร.",
            },
            "chulalongk_centerofex_pitakpolrat_009": {
                "full_name_th": "อ. ภัทรวดี พิทักษ์พลรัตน์",
                "academic_title_th": "อ.",
            },
            "kingmongku_schoolofen_suampun_065": {
                "full_name_th": "ดร. วรุตม์ สุอำพันธน์",
                "academic_title_th": "ดร.",
            },
            "kingmongku_schoolofin_nootyaskool_022": {
                "full_name_th": "ผศ.ดร. ศุภกิจ นุตยาสกุล",
                "academic_title_th": "ผศ.ดร.",
            },
            "mahidoluni_facultyoft_pitaksajjakul_126": {
                "full_name_th": "รศ.ดร. พรรณอำทิพย์ พิทักษ์สัจจากุล",
                "academic_title_th": "รศ.ดร.",
            },
            "kingmongku_facultyofe_canyook_078": {
                "full_name_th": "ผศ.ดร. รุ่งสินีย์ ฉันยุคต์",
                "academic_title_th": "ผศ.ดร.",
            },
            "thammasatu_sirindhorn_piantanakulchai_030": {
                "full_name_th": "ดร. มงกุฎ เพียรธนากุลชัย",
                "academic_title_th": "ดร.",
            },
            "mahidoluni_facultyoft_kosoltanapiwat_019": {
                "full_name_th": "รศ.ดร. ณฐมน โกศลธนาพิวัฒน์",
                "academic_title_th": "รศ.ดร.",
            },
            "khonkaenun_facultyofn_haungthaisong_051": {
                "full_name_th": "ดร. อุไรวรรณ หอห่างไทยสงฆ์",
                "academic_title_th": "ดร.",
            },
            "kingmongku_schoolofin_pradittasnee_019": {
                "full_name_th": "ผศ.ดร. ลาภัส ประดิษฐ์ทัศนีย์",
                "academic_title_th": "ผศ.ดร.",
            },
            "kingmongku_schoolofin_titijaroonroj_029": {
                "full_name_th": "ผศ.ดร. ธาราวิชญ์ ติติจารุณโรจน์",
                "academic_title_th": "ผศ.ดร.",
            },
            "mahidoluni_facultyoft_arunsodsai_066": {
                "full_name_th": "ผศ.ดร. วัชรี อรุณสดใส",
                "academic_title_th": "ผศ.ดร.",
            },
            "mahidoluni_facultyoft_limkittikul_068": {
                "full_name_th": "รศ.ดร. เกรียงศักดิ์ ลิ้มกิตติกุล",
                "academic_title_th": "รศ.ดร.",
            },
            "mahidoluni_facultyoft_pongpaew_133": {
                "full_name_th": "ศ.เกียรติคุณ ดร. ปราณีต ปองผ่องผิว",
                "academic_title_th": "ศ.เกียรติคุณ ดร.",
            },
            "chula_eng_ee_018": {
                "full_name_th": "ศ.ดร. ชาวดิษฐ์ อัศวกุล",
                "academic_title_th": "ศ.ดร.",
            },
            "chula_eng_ee_026": {
                "full_name_th": "รศ.ดร. สุปตนา เอื้อทวีกุล",
                "academic_title_th": "รศ.ดร.",
            },
            "chula_eng_ee_025": {
                "full_name_th": "รศ.ดร. สุชิน อรุณสวัสดิ์วงศ์",
                "academic_title_th": "รศ.ดร.",
            },
            "chula_eng_ee_016": {
                "full_name_th": "รศ.ดร. ฉันทชนะ ตั้งวงศ์ศานต์",
                "academic_title_th": "รศ.ดร.",
            },
            "kingmongku_schoolofin_netisopakul_008": {
                "full_name_th": "รศ.ดร. พรฤดี เนติโสภากุล",
                "academic_title_th": "รศ.ดร.",
            },
        }
        for fid, attrs in corrupted_name_fixes.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                print(f"🔤 [4] Repairing font-encoding / corrupted name: {fid} -> {attrs['full_name_th']}")
                for k, v in attrs.items():
                    setattr(f, k, v)
                f.embedding_text = build_standard_embedding_text(f)

        # -------------------------------------------------------------
        # 5. STRIP TITLE PREFIXES AND DEGREE SUFFIXES FROM ENGLISH NAMES (20 records)
        # -------------------------------------------------------------
        title_prefix_fixes = {
            "cmu_eng_department_drpeerapong_43": {"first_name": "Peerapong"},
            "srinakhari_facultyofe_wattana_009": {"first_name": "Pawanrat"},
            "srinakhari_facultyofe_srisawat_001": {"first_name": "Patcharaporn"},
            "cu_cbs_wave11_0089": {
                "academic_title_th": "รศ.ดร.",
                "first_name": "Porpan",
                "last_name": "Vachajitpan",
            },
            "cu_cbs_wave11_0133": {
                "academic_title_th": "รศ.",
                "first_name": "Choosak",
                "last_name": "Udomsri",
            },
            "cu_cbs_wave11_0139": {
                "academic_title_th": "รศ.",
                "first_name": "Manop",
                "last_name": "Varapak",
            },
            "cu_cbs_wave11_0177": {
                "academic_title_th": "ผศ.ดร.",
                "first_name": "June",
                "last_name": "Charoenseang",
            },
            "kingmong_schoolof_1dc3129f": {"first_name": "Chonlameth"},
            "kingmong_schoolof_65dc5783": {"first_name": "Chakarida"},
            "kingmong_schoolof_09b152b2": {"first_name": "Kriengkrai"},
            "kingmong_schoolof_39d6bb17": {"first_name": "Prasert"},
            "kingmong_schoolof_57e2b988": {"first_name": "Pornchai"},
            "kingmong_schoolof_646df1f1": {"first_name": "Suree"},
            "mfu_cos_panitita_wat": {"first_name": "Panitita"},
            "mfu_cos_patcharee_pon": {"first_name": "Patcharee"},
            "kku_sci_wave14_b_0114": {
                "academic_title_th": "รศ.ดร.",
                "first_name": "Siriboon",
                "last_name": "Mukdasai",
            },
            "kku_sci_wave14_b_0127": {
                "academic_title_th": "รศ.ดร.",
                "first_name": "Kingkaew",
                "last_name": "Chayakul Chanapattharapol",
            },
            "kku_sci_wave14_b_0141": {
                "academic_title_th": "ผศ.ดร.",
                "first_name": "Wijittra",
                "last_name": "Wichiansee",
            },
            "kku_sci_wave14_b_0051": {
                "academic_title_th": "รศ.ดร.",
                "full_name_th": "รศ.ดร. บัณฑิต ภิบาลจอมมี",
                "first_name": "Bundit",
                "last_name": "Pibaljommee",
            },
            "kku_sci_wave14_b_0055": {
                "academic_title_th": "รศ.ดร.",
                "full_name_th": "รศ.ดร. สมนึก วรวิเศษ",
                "first_name": "Somnuek",
                "last_name": "Worawiset",
            },
        }
        for fid, attrs in title_prefix_fixes.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                print(f"🎓 [5] Stripping title/degree from English name: {fid}")
                for k, v in attrs.items():
                    setattr(f, k, v)
                f.embedding_text = build_standard_embedding_text(f)

        # -------------------------------------------------------------
        # 6. RESTORE MISSING SURNAMES & EXPAND INITIAL-ONLY LAST NAMES (46 records)
        # -------------------------------------------------------------
        single_char_surnames = {
            # MSU Noppadol missing surname
            "msu_noppadol_s_2683": {
                "full_name_th": "ผศ.ดร. นพปฎล เสงี่ยมศักดิ์",
                "academic_title_th": "ผศ.ดร.",
                "first_name": "Noppadol",
                "last_name": "Sangiamsak",
            },
            # KKU Science Chakrit
            "kku_sci_wave14_b_0104": {"last_name": "Pongkitivanichkul"},
            # PSU Science
            "psu_supatinee_k_0146": {"last_name": "Kongkaew"},
            "psu_suparat_c_0400": {"last_name": "Khotchim"},
            "psu_thanawit_k_8357": {"last_name": "Kueamitr"},
            "psu_rawiporn_p_3998": {"last_name": "Promsoong"},
            "psu_kasrin_s_9930": {"last_name": "Saisahas"},
            # MSU Engineering
            "msu_piyanat_j_4588": {"last_name": "Janthosut"},
            "msu_raungrut_c_8434": {"last_name": "Cheerarot"},
            "msu_sahalaph_h_0461": {"last_name": "Homwuttiwong"},
            "msu_chaicharn_c_5614": {"last_name": "Chotithanorm"},
            "msu_siwa_k_5790": {"last_name": "Kaewplang"},
            "msu_rattana_h_7637": {"last_name": "Homwichian"},
            "msu_napanom_k_2355": {"last_name": "Kaewhanam"},
            "msu_bopit_b_0099": {"last_name": "Bubphachot"},
            "msu_nutnicha_i_5206": {"last_name": "Imnamkhao"},
            "msu_sudsakorn_i_1740": {"last_name": "Inthidech"},
            "msu_yottha_s_3427": {"last_name": "Srithep"},
            "msu_chanat_v_9242": {"last_name": "Wiphatthanaporn"},
            "msu_juckamas_l_4507": {"last_name": "Laohavanich"},
            "msu_suphan_y_8562": {"last_name": "Yangyuen"},
            "msu_teerapat_c_3786": {"last_name": "Chomphukham"},
            "msu_sopa_c_4740": {"last_name": "Cansee"},
            "msu_tawatchai_k_6914": {"last_name": "Kunakote"},
            "msu_narin_s_7129": {"last_name": "Siriwan"},
            "msu_kiattisin_k_3747": {"last_name": "Kanjanavapibul"},
            "msu_theerayuth_c_0672": {"last_name": "Chatchanayunyong"},
            "msu_wasan_d_9549": {"last_name": "Duangkhamchan"},
            "msu_siriluk_w_7692": {"last_name": "Wongkhasem"},
            "msu_banri_k_5720": {"last_name": "Khemkladmook"},
            "msu_chonlatee_p_6174": {"last_name": "Photong"},
            "msu_niwat_a_7429": {"last_name": "Angkawisittpan"},
            "msu_supannika_w_0693": {"last_name": "Wattana"},
            "msu_nawarat_p_0611": {"last_name": "Piladaeng"},
            "msu_nattawoot_s_8088": {"last_name": "Suwannatha"},
            "msu_nuttapon_c_2074": {"last_name": "Chaiduangsri"},
            "msu_chaiyong_s_0283": {"last_name": "Sermphol"},
            "msu_krit_l_4881": {"last_name": "Lertlum"},
            "msu_nattapol_p_5635": {"last_name": "Poomsa-ad"},
            "msu_songchai_w_4502": {"last_name": "Wiriyaumpaiwong"},
            "msu_anongrit_k_0212": {"last_name": "Kangrang"},
            "msu_wajussakorn_k_6227": {"last_name": "Kanjana"},
            "msu_sattawat_t_6447": {"last_name": "Thuangchon"},
            "msu_surachai_w_2113": {"last_name": "Wongcharee"},
            "msu_grit_n_8347": {"last_name": "Ngowtanasuwan"},
            "msu_surapong_l_6760": {"last_name": "Liwthaisong"},
            "msu_tanayut_c_9888": {"last_name": "Chaithongrat"},
        }
        for fid, attrs in single_char_surnames.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                print(f"👤 [6] Expanding single-letter/missing surname: {fid} -> {attrs}")
                for k, v in attrs.items():
                    setattr(f, k, v)
                f.embedding_text = build_standard_embedding_text(f)

        # -------------------------------------------------------------
        # 7. ALIGN BIBLIOMETRIC MONOTONICITY (5 Mahidol Science records)
        # -------------------------------------------------------------
        mono_records = [
            ("mu_sci_wave14_b_0169", 2),
            ("mu_sci_wave14_b_0062", 17),
            ("mu_sci_wave14_b_0006", 4),
            ("mu_sci_wave14_b_0205", 6),
            ("mu_sci_wave14_b_0227", 3),
        ]
        for fid, target_pubs in mono_records:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f and (f.total_publications_count or 0) < target_pubs:
                print(f"📊 [7] Aligning bibliometric monotonicity for {fid} ({f.full_name_th}): pubs 0 -> {target_pubs}")
                f.total_publications_count = target_pubs

        # -------------------------------------------------------------
        # 8. COURSE CREDIT BUG & PROGRAM_TYPE STANDARDIZATION
        # -------------------------------------------------------------
        # 8.1 CMU credit bug 368797 -> 36 หน่วยกิต
        cmu_course = db.query(CourseDB).filter(CourseDB.id == "cmu_tqf_25490041110551").first()
        if cmu_course:
            print(f"📚 [8.1] Correcting corrupted credits in course {cmu_course.id}: '368797 หน่วยกิต' -> '36 หน่วยกิต'")
            cmu_course.total_credits = "36 หน่วยกิต"
            if cmu_course.description and "368797" in cmu_course.description:
                cmu_course.description = cmu_course.description.replace("368797", "36")

        # 8.2 Standardize Mahidol 'Graduate' and other program types
        all_courses = db.query(CourseDB).all()
        pt_updated = 0
        for c in all_courses:
            pt = (c.program_type or "").strip()
            if pt == "Graduate":
                t_th = c.title_th or ""
                t_en = c.title_en or ""
                is_inter = "นานาชาติ" in t_th or "International" in t_en
                is_special = "ภาคพิเศษ" in t_th or "โครงการพิเศษ" in t_th
                if is_inter and is_special:
                    c.program_type = "ภาคพิเศษ / นานาชาติ"
                elif is_inter:
                    c.program_type = "นานาชาติ"
                elif is_special:
                    c.program_type = "ภาคพิเศษ"
                else:
                    c.program_type = "ภาคปกติ"
                pt_updated += 1
            else:
                mapping = {
                    "นานาชาติ (International)": "นานาชาติ",
                    "นานาชาติ (International / Weekend)": "ภาคพิเศษ / นานาชาติ",
                    "นานาชาติ (ภาคพิเศษ)": "ภาคพิเศษ / นานาชาติ",
                    "หลักสูตรนานาชาติ (ภาคพิเศษ)": "ภาคพิเศษ / นานาชาติ",
                    "หลักสูตรนานาชาติ ภาคพิเศษ": "ภาคพิเศษ / นานาชาติ",
                    "ภาคพิเศษ (นานาชาติ)": "ภาคพิเศษ / นานาชาติ",
                    "Special / International": "ภาคพิเศษ / นานาชาติ",
                    "Special": "ภาคพิเศษ",
                    "ภาคปกติ (Thai Program)": "ภาคปกติ",
                    "ภาคปกติ (ภาษาไทย)": "ภาคปกติ",
                    "ภาคปกติ (Thai/Inter)": "ภาคปกติ / นานาชาติ",
                    "ภาคปกติและนานาชาติ": "ภาคปกติ / นานาชาติ",
                    "ภาคปกติและภาคพิเศษ": "ภาคปกติ / ภาคพิเศษ",
                    "ภาคปกติ/ภาคพิเศษ": "ภาคปกติ / ภาคพิเศษ",
                    "ภาคปกติ / ภาคพิเศษ (วันเสาร์-อาทิตย์)": "ภาคปกติ / ภาคพิเศษ",
                    "ภาคปกติ / ภาคพิเศษ เสาร์-อาทิตย์": "ภาคปกติ / ภาคพิเศษ",
                    "ภาคปกติ / เสาร์-อาทิตย์": "ภาคปกติ / ภาคพิเศษ",
                    "ภาคพิเศษ (วันเสาร์-อาทิตย์)": "ภาคพิเศษ",
                    "ภาคพิเศษ (เสาร์-อาทิตย์)": "ภาคพิเศษ",
                    "ภาคพิเศษ เสาร์-อาทิตย์": "ภาคพิเศษ",
                    "ภาคพิเศษ / เสาร์-อาทิตย์": "ภาคพิเศษ",
                    "ภาคพิเศษ (วันหยุด เสาร์-อาทิตย์)": "ภาคพิเศษ",
                    "ภาคพิเศษ (Special Program)": "ภาคพิเศษ",
                    "ภาคพิเศษ (Weekend)": "ภาคพิเศษ",
                    "ภาคพิเศษ (Weekend / Professional)": "ภาคพิเศษ",
                    "โครงการพิเศษ": "ภาคพิเศษ",
                    "หลักสูตรปกติ / โครงการพิเศษ": "ภาคปกติ / ภาคพิเศษ",
                    "หลักสูตรไทย (ภาคพิเศษ)": "ภาคพิเศษ",
                    "สองภาษา (Bilingual)": "สองภาษา",
                    "ภาคพิเศษ (สองภาษา)": "สองภาษา / ภาคพิเศษ",
                    "หลักสูตรภาษาอังกฤษ": "ภาคภาษาอังกฤษ",
                    "ภาคปกติ / ภาษาอังกฤษ": "ภาคปกติ / ภาคภาษาอังกฤษ",
                    "ระบบการศึกษาทางไกล (Online / Distance Learning)": "ระบบการศึกษาทางไกล",
                    "ระบบการศึกษาทางไกล / บัณฑิตศึกษา": "ระบบการศึกษาทางไกล",
                    "ระบบทางไกล / บัณฑิตศึกษา": "ระบบการศึกษาทางไกล",
                    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคปกติ (วันเสาร์-อาทิตย์)": "ภาคปกติ",
                    "หลักสูตรปกติ / หลักสูตรเดี่ยว / ภาคปกติ (วันจันทร์-ศุกร์) และ ภาคพิเศษ (วันเสาร์-อาทิตย์ ) / ภาคพิเศษ (วันเสาร์-อาทิตย์ )": "ภาคปกติ / ภาคพิเศษ",
                }
                if pt in mapping:
                    c.program_type = mapping[pt]
                    pt_updated += 1

        print(f"🎓 [8.2] Standardized program_type for {pt_updated} courses")

        db.commit()
        print("\n" + "=" * 70)
        print("✅ ALL PHASE 2 DEEP REPAIRS COMMITTED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during Phase 2 repairs: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_phase2_deep_repairs()
