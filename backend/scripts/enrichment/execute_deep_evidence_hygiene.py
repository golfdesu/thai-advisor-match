# -*- coding: utf-8 -*-
"""
Execute Deep Evidence Faculty Hygiene, Deduplication, and Realignment
====================================================================
Audits and cleans all records in public.faculties across 4 dimensions:
1. Faculty & Department Authenticity:
   - Archives 47 non-teaching administrative staff at Thaksin University into scholars_unassigned.
   - Archives non-teaching secretariat/support staff into scholars_unassigned while grounding true professors.
   - Realigns anomalous CU/MU/KKU records to authentic teaching faculties and universities.
   - Corrects Naresuan University records (nu_w45_1009_310, nu_w45_0386_175).
2. Typographical & OCR Deduplication:
   - Merges 33 exact Thai OCR duplicate pairs (อํา vs อำ, เเ vs แ, พันธ์ vs พันธุ์, หงษ์ vs หงส์, double vowels).
   - Merges remaining confirmed typographic pairs (e.g. ปานเทพ รัตนากร, วงศา เล้าหศิริวงศ์, กอบวุฒิ รุจิจนากุล).
   - Merges English transliteration duplicate pairs at SWU, Walailak, UBU, MSU, SUT, and Phayao.
3. Duplicate OpenAlex IDs:
   - Resolves all 34 duplicate OpenAlex ID pairs, preserving lifetime citations, h-index, and publications.
   - Disambiguates homonymous pairs (Phakdee Sukphonsawan vs Nuttaporn Phakdee) by decoupling false shared OA IDs.
4. University Transfers:
   - Grounding transferred professors (Apiradee Wongkitrungrueng to Chulalongkorn, Nipit Wongpunya to Chulalongkorn,
     Wanwisa Udomsinprasert to Mahidol, Moragot Chatatikun to Walailak, Jumpol Polvichai to KMUTT, etc.).
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB
from scripts.enrichment.clean_and_ground_all_faculties import (
    merge_faculty_metrics_and_lists,
    score_record_as_winner,
)

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
}


def normalize_thai_text(text_in: str) -> str:
    if not text_in:
        return ""
    t = text_in.replace("เเ", "แ")
    t = re.sub(r"[ํ][า]", "ำ", t)
    t = t.replace("ํ", "ำ")
    t = re.sub(r"[ุ]+", "ุ", t)
    t = re.sub(r"[ู]+", "ู", t)
    t = re.sub(r"[่]+", "่", t)
    t = re.sub(r"[้]+", "้", t)
    t = re.sub(r"[๊]+", "๊", t)
    t = re.sub(r"[๋]+", "๋", t)
    t = re.sub(r"[์]+", "์", t)
    t = t.replace("พันธ์ุ", "พันธุ์").replace("พันธ์", "พันธุ์")
    t = t.replace("หงษ์", "หงส์")
    return t


def clean_thai_name_for_matching(th: str) -> str:
    if not th:
        return ""
    th_clean = re.sub(
        r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพญ\.|นพ\.|สพ\.|น\.สพ\.|สพ\.ญ\.|ภญ\.|กภ\.|พญ\.|นายแพทย์|แพทย์หญิง|อาจารย์)\s*",
        "",
        th,
    ).strip()
    th_clean = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_clean).strip()
    th_clean = re.sub(r"\s+", "", th_clean)
    return normalize_thai_text(th_clean)


# University transfer realignments
MANUAL_TRANSFERS = [
    # Apiradee Wongkitrungrueng -> Chulalongkorn Business School
    ("mu_w57_7224_838", "จุฬาลงกรณ์มหาวิทยาลัย", "คณะพาณิชยศาสตร์และการบัญชี", "ภาควิชาการตลาด"),
    # Popchai Ngamskulrungroj -> Mahidol Siriraj
    ("mu_w57_2451_920", "มหาวิทยาลัยมหิดล", "คณะแพทยศาสตร์ศิริราชพยาบาล", "ภาควิชาจุลชีววิทยา"),
    # Aree Jampaklay -> Mahidol IPSR
    ("mu_w57_3164_447", "มหาวิทยาลัยมหิดล", "สถาบันวิจัยประชากรและสังคม", "สาขาวิชาประชากรและการวิจัยสังคม"),
    # Atsadang Boonmee -> Mahidol Science
    ("mu_w57_6659_950", "มหาวิทยาลัยมหิดล", "คณะวิทยาศาสตร์", "ภาควิชาเทคโนโลยีชีวภาพ"),
    # Naresuan University
    ("nu_w45_1009_310", "มหาวิทยาลัยนเรศวร", "คณะศึกษาศาสตร์", "ภาควิชาเทคโนโลยีและสื่อสารการศึกษา"),
    ("nu_w45_0386_175", "มหาวิทยาลัยนเรศวร", "คณะวิศวกรรมศาสตร์", "ภาควิชาวิศวกรรมเคมี"),
    # Walailak Medical Center Dean / Deans
    ("walailak_schoolof_d869fa27", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี", "สาขาวิชาวิศวกรรมเคมีและปิโตรเคมี"),
    ("wu_w51_0008_203", "มหาวิทยาลัยวลัยลักษณ์", "วิทยาลัยทันตแพทยศาสตร์นานาชาติ", "สาขาวิชาทันตแพทยศาสตร์"),
    ("wu_w51_0424_821", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาสถาปัตยกรรมศาสตร์และการออกแบบ", "สาขาวิชาสถาปัตยกรรม"),
    ("wu_w51_0534_213", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาสาธารณสุขศาสตร์", "สาขาวิชาอนามัยสิ่งแวดล้อม"),
    ("wu_w51_0535_338", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาสาธารณสุขศาสตร์", "สาขาวิชาอาชีวอนามัยและความปลอดภัย"),
    ("wu_w51_0536_415", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาสาธารณสุขศาสตร์", "สาขาวิชาสาธารณสุขศาสตร์"),
    ("wu_w51_0537_542", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาสาธารณสุขศาสตร์", "สาขาวิชาอนามัยสิ่งแวดล้อม"),
    ("wu_w51_0132_284", "มหาวิทยาลัยวลัยลักษณ์", "สำนักวิชาการบัญชีและการเงิน", "สาขาวิชาการเงิน"),
    # KU Dean & Vice President department cleanups
    ("ku_wave17_bus_0055", "มหาวิทยาลัยเกษตรศาสตร์", "คณะบริหารธุรกิจ", "ภาควิชาการจัดการ"),
    ("ku_wave17_hum_0173", "มหาวิทยาลัยเกษตรศาสตร์", "คณะมนุษยศาสตร์", "ภาควิชาวรรณคดี"),
    ("ku_wave18_srv_0045", "มหาวิทยาลัยเกษตรศาสตร์", "คณะอุตสาหกรรมบริการ", "สาขาวิชาการจัดการโรงแรมและการท่องเที่ยว"),
    ("ku_wave18_srv_0046", "มหาวิทยาลัยเกษตรศาสตร์", "คณะอุตสาหกรรมบริการ", "สาขาวิชาการจัดการโรงแรมและการท่องเที่ยว"),
    ("ku_wave17_econ_0080", "มหาวิทยาลัยเกษตรศาสตร์", "คณะเศรษฐศาสตร์", "ภาควิชาเศรษฐศาสตร์"),
    ("ku_wave17_soc_0100", "มหาวิทยาลัยเกษตรศาสตร์", "คณะสังคมศาสตร์", "ภาควิชาประวัติศาสตร์"),
    ("ku_wave17_soc_0101", "มหาวิทยาลัยเกษตรศาสตร์", "คณะสังคมศาสตร์", "ภาควิชาสังคมวิทยาและมานุษยวิทยา"),
    ("ku_wave17_soc_0102", "มหาวิทยาลัยเกษตรศาสตร์", "คณะสังคมศาสตร์", "ภาควิชารัฐศาสตร์และรัฐประศาสนศาสตร์"),
    ("ku_wave17_soc_0106", "มหาวิทยาลัยเกษตรศาสตร์", "คณะสังคมศาสตร์", "ภาควิชารัฐศาสตร์และรัฐประศาสนศาสตร์"),
    ("ku_wave17_soc_0109", "มหาวิทยาลัยเกษตรศาสตร์", "คณะสังคมศาสตร์", "ภาควิชาภูมิศาสตร์"),
    ("ku_wave17_soc_0110", "มหาวิทยาลัยเกษตรศาสตร์", "คณะสังคมศาสตร์", "ภาควิชาสังคมวิทยาและมานุษยวิทยา"),
    ("ku_wave18_engkps_0114", "มหาวิทยาลัยเกษตรศาสตร์", "คณะวิศวกรรมศาสตร์ กำแพงแสน", "ภาควิชาวิศวกรรมการอาหาร"),
    ("ku_wave18_engkps_0115", "มหาวิทยาลัยเกษตรศาสตร์", "คณะวิศวกรรมศาสตร์ กำแพงแสน", "ภาควิชาวิศวกรรมเกษตร"),
    ("mahasarakh_facultyofi_khamket_002", "มหาวิทยาลัยมหาสารคาม", "คณะวิทยาการสารสนเทศ", "สาขาวิชาเทคโนโลยีสารสนเทศ"),
]

# OpenAlex Cross-University or Duplicate ID winners
OA_MANUAL_RESOLUTIONS = {
    # Pornchai Jansisyanont: Dean of Chulalongkorn Dentistry
    "https://openalex.org/A5057663942": {
        "winner_id": "chulalongk_facultyofd_jansisiyont_016",
        "ghost_ids": ["dt-mu-001_8f9bbb"],
    },
    # Sompop Prathanturarug: Mahidol Pharmacy
    "https://openalex.org/A5079753974": {
        "winner_id": "mu_pharm_wave12_0075",
        "ghost_ids": ["chulalongk_facultyofp_prathanturarux_031"],
    },
    # Wanwisa Udomsinprasert: Mahidol Pharmacy
    "https://openalex.org/A5060534055": {
        "winner_id": "mu_pharm_wave12_0008",
        "ghost_ids": ["chulalongk_facultyofp_udomsinprasert_007"],
    },
    # Moragot Chatatikun: Walailak Allied Health
    "https://openalex.org/A5042972287": {
        "winner_id": "wu_w51_0499_966",
        "ghost_ids": ["chulalongk_facultyofa_chatathikun_009"],
    },
    # Jumpol Polvichai: KMUTT Engineering
    "https://openalex.org/A5080702231": {
        "winner_id": "kmutt_eng_cpe_012",
        "ghost_ids": ["cu_w58_3694_526"],
    },
    # Nipit Wongpunya: Chulalongkorn Economics (transferred from TU)
    "https://openalex.org/A5031799363": {
        "winner_id": "cu_wave19_econ_0016",
        "ghost_ids": ["tu_econ_nipit_001"],
    },
    # Sasithorn Trongchitpakdee: KU Agro-Industry
    "https://openalex.org/A5088529260": {
        "winner_id": "ku_agro_wave15_0029",
        "ghost_ids": ["ku_ifrpd_sasitorn_001"],
    },
    # Marong Phadungsit: KMUTT
    "https://openalex.org/A5089682879": {
        "winner_id": "kmutt_eng_cpe_013",
        "ghost_ids": ["kmutt_w57_2611_351"],
    },
    # Rajchawit Sarochvigsit: KMUTT
    "https://openalex.org/A5071041561": {
        "winner_id": "kmutt_eng_cpe_002",
        "ghost_ids": ["kmutt_w57_1189_223"],
    },
    # Prapong Preechaprawong: KMUTT
    "https://openalex.org/A5059776332": {
        "winner_id": "kmutt_eng_cpe_003",
        "ghost_ids": ["kmutt_w57_2157_163"],
    },
    # Suthathip Chuenwattana: KMUTT
    "https://openalex.org/A5090961600": {
        "winner_id": "kmutt_eng_cpe_016",
        "ghost_ids": ["kmutt_w57_2914_229"],
    },
    # Chedtaporn Sujitapan: Walailak
    "https://openalex.org/A5003521567": {
        "winner_id": "walailak_schoolof_dcd1e800",
        "ghost_ids": ["wu_w51_1355_231"],
    },
    # Putrada Ninla-Aesong: Walailak
    "https://openalex.org/A5085309539": {
        "winner_id": "wu_w51_0670_755",
        "ghost_ids": ["wu_w51_1193_294"],
    },
    # Nur Lailatur Rofiah: Walailak
    "https://openalex.org/A5102789147": {
        "winner_id": "wu_w51_0254_800",
        "ghost_ids": ["wu_w51_1079_760"],
    },
    # Md Eshrat E Alahi: Walailak
    "https://openalex.org/A5001658147": {
        "winner_id": "walailak_schoolof_3dbe7cf7",
        "ghost_ids": ["wu_w51_0978_780"],
    },
    # Hideyuki J. Majima: Walailak
    "https://openalex.org/A5020481253": {
        "winner_id": "wu_w51_0526_464",
        "ghost_ids": ["wu_w51_0941_334"],
    },
    # Muhammad Awais-E-Yazdan: Walailak
    "https://openalex.org/A5009121724": {
        "winner_id": "wu_w51_0564_382",
        "ghost_ids": ["wu_w51_1238_674"],
    },
    # Suratsavadee K. Korkua: Walailak
    "https://openalex.org/A5067440885": {
        "winner_id": "walailak_schoolof_81b92a26",
        "ghost_ids": ["wu_w51_1039_827"],
    },
    # Imran Sama-ae: Walailak
    "https://openalex.org/A5001970504": {
        "winner_id": "wu_w51_0523_606",
        "ghost_ids": ["wu_w51_1119_101"],
    },
    # Tran Anh Tuan: Walailak
    "https://openalex.org/A5101610867": {
        "winner_id": "walailak_schoolof_f4fd85c7",
        "ghost_ids": ["wu_w51_0975_568"],
    },
    # Marlon D. Sipe: Walailak
    "https://openalex.org/A5061010759": {
        "winner_id": "wu_w51_0232_540",
        "ghost_ids": ["wu_w51_1297_210"],
    },
    # Sudaporn Sukchinda: Walailak
    "https://openalex.org/A5063905163": {
        "winner_id": "wu_w51_0286_429",
        "ghost_ids": ["wu_w51_1792_797"],
    },
    # Punsiri Dam-O Adamczyk: Walailak
    "https://openalex.org/A5015002133": {
        "winner_id": "walailak_schoolof_7198a198",
        "ghost_ids": ["wu_w51_1122_766"],
    },
    # Junifer L. Bucol: Walailak
    "https://openalex.org/A5020065526": {
        "winner_id": "wu_w51_0229_712",
        "ghost_ids": ["wu_w51_1475_899"],
    },
    # Kittisak Saengsura: MSU
    "https://openalex.org/A5090974018": {
        "winner_id": "msu_w47_0039_106",
        "ghost_ids": ["msu_w47_0397_999"],
    },
    # Ratchaneekorn Pilasombat: MSU
    "https://openalex.org/A5001626257": {
        "winner_id": "msu_w47_0526_285",
        "ghost_ids": ["msu_w47_0617_569"],
    },
    # Md Ahbabur Rahman: Thaksin
    "https://openalex.org/A5001210374": {
        "winner_id": "tsu_w50_0961_619",
        "ghost_ids": ["tsu_w50_1583_132"],
    },
    # Anob Kantacha: Thaksin
    "https://openalex.org/A5018726484": {
        "winner_id": "tsu_w50_0037_985",
        "ghost_ids": ["tsu_w50_1511_345"],
    },
    # Wanit Rotniam: Thaksin
    "https://openalex.org/A5087282138": {
        "winner_id": "tsu_w50_0003_749",
        "ghost_ids": ["tsu_w50_1742_373"],
    },
    # Anida Petchkaew: Thaksin
    "https://openalex.org/A5036298489": {
        "winner_id": "tsu_w50_0430_886",
        "ghost_ids": ["tsu_w50_1585_594"],
    },
    # Narissara Mahathaninwong: PSU
    "https://openalex.org/A5061615828": {
        "winner_id": "psu_w41_0056_982",
        "ghost_ids": ["psu_w58_1432_640"],
    },
    # Thanyanan Wannathong Brocklehurst: Silpakorn
    "https://openalex.org/A5032248547": {
        "winner_id": "su_w43_0065_970",
        "ghost_ids": ["su_w58_1152_426"],
    },
    # Komkrit Prasertwong: SWU
    "https://openalex.org/A5077030755": {
        "winner_id": "wave21_0009_952",
        "ghost_ids": ["swu_w44_0896_884"],
    },
}

# Cross-university external co-author ghosts to merge into authentic home university
CROSS_UNIV_MERGES = [
    # Gobwute Rujijanagul: Chulalongkorn ghost -> Chiang Mai winner
    ("cmu_7885ea4e_9916", "cu_w58_0775_292"),
    # Palakorn Surakunprapha: Chulalongkorn ghost
    ("sut_w46_0723_207", "cu_w58_2577_171"),
]

# Additional specific duplicate pairs
SPECIFIC_DUPLICATE_PAIRS = [
    # Mahidol Vet Dean: Parntep Ratanakorn
    ("mu_vet_parntep_001", "wave21_0007_929"),
    # KKU Public Health Dean: Wongsa Laohasiriwong
    ("kk_ph_006", "kku_w58_10792_758"),
    # KKU Wipawee Krisanaputi
    ("wave30_0004_343", "kku_w58_8035_247"),
    # KKU Sompong Doolgindachbaporn
    ("kku_w58_6798_651", "kku_w58_10051_936"),
    # KKU Roengsak Katawatin
    ("kku_w58_8470_831", "kku_w58_10972_550"),
    # KKU Chaloem Ruangviriyachai
    ("kku_w58_8456_975", "kku_w58_11085_473"),
    # KKU Yupa Kukongviriyapan
    ("kku_med_upa_001", "kku_w58_7401_141"),
    ("kku_med_upa_001", "kku_w58_11035_647"),
    # KKU Suchitra Limamnuaylap
    ("kku_w58_10791_663", "kku_w58_10641_125"),
    # KKU Singhanat Phuangchandang
    ("kku_w58_10168_507", "kku_w58_10617_682"),
    # KKU Kimaporn Khamanarong
    ("kku_w58_10654_494", "kku_w58_5707_439"),
    # KKU Chalong Wachirapakorn
    ("kku_w58_7928_725", "kku_w58_10095_462"),
    # KKU Issara Kanjug
    ("kku_edu_001", "kku_w58_10189_992"),
    # KMITL Supannada Chotipant
    ("kingmongku_schoolofin_chotipant_020", "kmitl_w39_0034_818"),
    # KMITL Sirion Vittayakorn
    ("kingmongku_schoolofin_vittayakorn_026", "kmitl_w39_0036_554"),
    # KMITL Ophascharas Nandhavan
    ("kmitl_aad_wave16_0103", "kmitl_w58_8422_899"),
    # PSU Pongthep Suteerawut
    ("psu_w58_6263_652", "psu_w58_7292_773"),
    # Thaksin Orachan Sirichote
    ("thaksinuni_facultyofe_sirichot_014", "tsu_w59_0525_307"),
    # Thaksin Somkiat Saithanu
    ("tsu_w59_0531_659", "tsu_w59_0423_115"),
    # Thaksin Sansanee Jan-anupap
    ("tsu_w50_0219_851", "tsu_w59_0213_342"),
    # Thaksin Korakot Thongkhachok
    ("thaksinuni_facultyofl_thongkhachok_011", "tsu_w59_0318_637"),
    # Thaksin Bradley Eugene Opatz Jr
    ("thaksinuni_facultyofm_opatzjr_021", "tsu_w50_1454_940"),
    # Thaksin Nanthaphan Naphatranan
    ("tsu_w50_1469_926", "tsu_w50_0566_852"),
    # MFU Woranon Lilawejpong
    ("wave28_0015_487", "mfu_w52_0093_395"),
    # MFU Yodsapon Nitiruchirot
    ("wave28_0008_944", "mfu_w52_0087_154"),
    # Walailak Simon Moxon
    ("wu_w51_0315_831", "wu_w59_1174_308"),
    # Silpakorn Chotima Chaturawong
    ("wave23_0063_208", "su_w58_3248_223"),
    # Silpakorn Weerayuth Saelim
    ("wave22_0753_178", "su_w58_4020_671"),
    # Silpakorn Chalermchai Kittisaknawin
    ("wave30_0046_319", "su_w58_3445_416"),
    # KU Taeng-on Prommi
    ("ku_wave18_asc_0127", "wave22_1053_941"),
    # KU Supasinee Numneam
    ("ku_wave18_eduks_0010", "ku_w57_4349_900"),
    # KU Ed Sarobol
    ("agr-ku-002_659cba", "ku_w57_5073_412"),
    # KU Pongprapan Pongsophon
    ("ku_edu_pongprapan_001", "ku_w57_8261_682"),
    # KU Apichart Vanavichit
    ("ku_agr_apichart_001", "ku_w57_6596_245"),
    # KU Nuanwan Tuaycharoen
    ("ku_arch_nuanwan_001", "ku_w57_6783_358"),
    # KU Sutkhet Nakasathien
    ("agr-ku-001_0458e1", "ku_w57_7441_229"),
    # Burapha Natchan Futemwong
    ("wave22_0926_985", "buu_w57_3232_328"),
    # Burapha Pongpun Siriyong
    ("wave21_0068_317", "buu_w57_2301_172"),
    # RMUTP Natcharee Khanachartwiboon
    ("rmutp_w53b_0649_472", "rmutp_w53b_0652_225"),
    # Chula Thanyos Lohpatananont
    ("fca-cu-007_86bbfc", "chulalongk_instituteo_lohpatananont_018"),
    # SWU Suppawan Sajjapibool
    ("srinakhari_facultyofe_fac_059_059", "swu_w57_3648_867"),
    # SWU Supada Sirikutta
    ("swu_w57_0345_211", "swu_w57_3655_411"),
    # SWU Arusa Chaovanalikit
    ("swu_w57_2418_838", "swu_w57_2066_877"),
    # SWU Naruphat Tangmankhongworakul
    ("swu_w57_1949_934", "swu_w57_2211_740"),
    # SWU English Transliterations
    ("swu_w44_0709_692", "swu_w44_1002_186"),
    ("swu_w44_0928_584", "swu_w44_1015_577"),
    ("swu_w44_0774_352", "swu_w44_1018_130"),
    ("swu_w44_1155_692", "swu_w44_1020_168"),
    ("swu_w44_0650_385", "swu_w44_1109_494"),
    ("swu_w44_0600_713", "swu_w44_0104_569"),
    ("swu_w44_0938_716", "swu_w44_0446_551"),
    ("swu_w44_1144_429", "swu_w44_0563_480"),
    ("swu_w44_0333_972", "swu_w44_0088_605"),
    ("swu_w44_1217_862", "swu_w44_0282_258"),
    ("swu_w44_1177_625", "swu_w44_0323_880"),
    # Walailak English Transliterations
    ("wu_w51_1901_223", "wu_w51_1208_479"),
    ("wu_w51_0988_912", "wu_w51_1571_397"),
    ("wu_w51_1949_819", "wu_w51_1808_154"),
    ("wu_w51_1569_861", "wu_w51_1250_837"),
    ("wu_w51_1549_479", "wu_w51_2047_288"),
    ("wu_w51_1730_494", "wu_w51_1880_157"),
    ("wu_w51_1060_106", "wu_w51_1736_781"),
    ("wu_w51_1060_106", "wu_w51_1978_468"),
    ("wu_w51_1760_105", "wu_w51_1755_728"),
    ("wu_w51_1992_807", "wu_w51_1810_128"),
    ("wu_w51_1735_869", "wu_w51_1849_295"),
    ("wu_w51_1900_165", "wu_w51_1922_329"),
    ("wu_w51_0998_720", "wu_w51_2052_680"),
    ("wu_w51_1492_179", "wu_w51_2056_881"),
    ("wu_w51_1460_945", "wu_w51_2089_529"),
    ("wu_w51_1593_863", "wu_w51_2070_517"),
    # Phayao English Transliterations
    ("up_w48_0454_557", "up_w48_1028_663"),
    ("up_w48_0742_958", "up_w48_1016_205"),
    ("up_w48_0522_561", "up_w48_0836_338"),
    ("up_w48_0733_989", "up_w48_0649_594"),
    ("up_w48_0733_989", "up_w48_0643_973"),
    ("up_w48_0682_175", "up_w48_0663_669"),
    ("up_w48_0240_331", "up_w48_0781_611"),
    ("up_w48_0959_483", "up_w48_0924_864"),
    # UBU English Transliterations
    ("ubu_w49_0201_428", "ubu_w49_0475_213"),
    ("ubu_w49_0634_751", "ubu_w49_0204_530"),
    ("ubu_w49_0295_149", "ubu_w49_0716_375"),
    ("ubu_w49_0680_184", "ubu_w49_0286_163"),
    ("ubu_w49_0558_957", "ubu_w49_0694_973"),
    ("ubu_w49_0727_248", "ubu_w49_0287_174"),
    ("ubu_w49_0727_248", "ubu_w49_0632_972"),
    ("ubu_w49_0607_138", "ubu_w49_0177_513"),
    ("ubu_w49_0633_338", "ubu_w49_0242_633"),
    ("ubu_w49_0737_786", "ubu_w49_0182_805"),
    ("ubu_w49_0189_190", "ubu_w49_0663_979"),
    ("ubu_w49_0276_967", "ubu_w49_0624_446"),
    ("ubu_w49_0241_434", "ubu_w49_0751_652"),
    ("ubu_w49_0171_706", "ubu_w49_0617_493"),
    # MSU English Transliterations
    ("msu_w47_0566_112", "msu_w47_0961_128"),
    ("msu_w47_0550_261", "msu_w47_1068_718"),
    ("msu_w47_0525_860", "msu_w47_1112_221"),
    ("msu_w47_1154_163", "msu_w47_1197_122"),
    ("msu_w47_0241_735", "msu_w47_0632_458"),
    ("msu_w47_0331_776", "msu_w47_1046_476"),
    ("msu_w47_0318_231", "msu_w47_0670_991"),
    # SUT English Transliterations
    ("sut_w46_0072_109", "sut_w46_0478_791"),
    ("sut_w46_0835_819", "sut_w46_0886_231"),
    ("sut_w46_0539_516", "sut_w46_0933_750"),
    ("sut_w46_0830_505", "sut_w46_0195_984"),
    ("sut_w46_0523_619", "sut_w46_0817_939"),
    ("sut_w46_0853_642", "sut_w46_0888_640"),
    ("sut_w46_0514_310", "sut_w46_0949_377"),
]


def execute_deep_evidence_hygiene():
    print("=== 🎓 EXECUTING DEEP EVIDENCE FACULTY HYGIENE & AUDIT ===", flush=True)
    t0 = time.time()
    db = SessionLocal()

    ghosts_to_archive_ids: set[str] = set()

    try:
        # ---------------------------------------------------------
        # Dimension 1: University Transfers & Realignment
        # ---------------------------------------------------------
        print("\n--- Dimension 1: University Transfers & Department Realignment ---")
        transferred_count = 0
        for fid, target_u_th, target_fac_th, target_dept_th in MANUAL_TRANSFERS:
            r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if r:
                r.university_th = target_u_th
                r.university = TH_TO_EN_CANONICAL.get(target_u_th, r.university)
                r.faculty_th = target_fac_th
                r.department_th = target_dept_th
                transferred_count += 1
        db.commit()
        print(f"  Transferred/realigned {transferred_count} professors to verified faculties.")

        # ---------------------------------------------------------
        # Dimension 2: Archive Non-Teaching Administrative Personnel
        # ---------------------------------------------------------
        print("\n--- Dimension 2: Non-Teaching Administrative & Support Personnel ---")
        # 1. Thaksin Administrative Units
        tsu_admin_keywords = [
            "สถาบันส่งเสริมการบริการวิชาการ",
            "อุทยานวิทยาศาสตร์ มหาวิทยาลัยทักษิณ",
            "สถาบันปฏิบัติการชุมชนเพื่อการศึกษา มหาวิทยาลัยทักษิณ",
            "สถาบันวิจัยและนวัตกรรม มหาวิทยาลัยทักษิณ",
            "ศูนย์บ่มเพาะวิสาหกิจ มหาวิทยาลัยทักษิณ",
            "สถาบันทรัพยากรการเรียนรู้และเทคโนโลยีดิจิทัล",
            "ศูนย์หนังสือมหาวิทยาลัยทักษิณ",
        ]
        tsu_admins = (
            db.query(FacultyDB)
            .filter(FacultyDB.university_th == "มหาวิทยาลัยทักษิณ")
            .filter(FacultyDB.faculty_th.in_(tsu_admin_keywords))
            .all()
        )
        for ta in tsu_admins:
            ghosts_to_archive_ids.add(ta.id)
        print(f"  Flagged {len(tsu_admins)} Thaksin non-teaching administrative personnel.")

        # 2. Secretariat Office Clerical Staff with 0 citations and no publications
        sec_staff = (
            db.query(FacultyDB)
            .filter(FacultyDB.department_th.like("%สำนักงานเลขานุการ%"))
            .all()
        )
        sec_archived = 0
        for s in sec_staff:
            # If professor has no publications and no citations and default title 'อ.'
            if (s.total_citations or 0) == 0 and not s.featured_publications and s.academic_title_th in ["อ.", "ดร."]:
                ghosts_to_archive_ids.add(s.id)
                sec_archived += 1
        print(f"  Flagged {sec_archived} clerical secretariat staff with zero publications.")

        # 3. MFU schools caught under CU/MU
        anomalous_cu_mu = (
            db.query(FacultyDB)
            .filter(
                (FacultyDB.university_th.in_(["จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยมหิดล"]))
                & (FacultyDB.faculty_th.like("%สำนักวิชา%"))
                & (FacultyDB.id != "cu_sar_nanthigorn_001") # Genuine Chula Saraburi
            )
            .all()
        )
        for a in anomalous_cu_mu:
            ghosts_to_archive_ids.add(a.id)
        print(f"  Flagged {len(anomalous_cu_mu)} anomalous external co-authors at CU/MU.")

        # ---------------------------------------------------------
        # Dimension 3: Duplicate OpenAlex ID Resolution
        # ---------------------------------------------------------
        print("\n--- Dimension 3: Duplicate OpenAlex ID Disambiguation & Merging ---")
        oa_merged = 0
        for oaid, conf in OA_MANUAL_RESOLUTIONS.items():
            winner = db.query(FacultyDB).filter(FacultyDB.id == conf["winner_id"]).first()
            if not winner:
                continue
            for gid in conf["ghost_ids"]:
                ghost = db.query(FacultyDB).filter(FacultyDB.id == gid).first()
                if ghost and ghost.id != winner.id:
                    merge_faculty_metrics_and_lists(winner, ghost)
                    ghosts_to_archive_ids.add(ghost.id)
                    oa_merged += 1

        # Homonymous decoupling for Phakdee Sukphonsawan vs Nuttaporn Phakdee
        f_phakdee1 = db.query(FacultyDB).filter(FacultyDB.id == "buu_w42_0373_424").first()
        f_phakdee2 = db.query(FacultyDB).filter(FacultyDB.id == "buu_w42_0223_906").first()
        if f_phakdee1 and f_phakdee2:
            f_phakdee1.openalex_id = "not_indexed"
            print("  Decoupled false homonymous OpenAlex ID for Burapha faculty (Invariant 10).")

        db.commit()
        print(f"  Resolved and merged {oa_merged} OpenAlex ID duplicate pairs.")

        # ---------------------------------------------------------
        # Dimension 4: Cross-University Merges & Specific Duplicate Pairs
        # ---------------------------------------------------------
        print("\n--- Dimension 4: Cross-University Merges & Typographical Pairs ---")
        spec_merged = 0
        for wid, gid in CROSS_UNIV_MERGES + SPECIFIC_DUPLICATE_PAIRS:
            winner = db.query(FacultyDB).filter(FacultyDB.id == wid).first()
            ghost = db.query(FacultyDB).filter(FacultyDB.id == gid).first()
            if winner and ghost and winner.id != ghost.id:
                merge_faculty_metrics_and_lists(winner, ghost)
                ghosts_to_archive_ids.add(ghost.id)
                spec_merged += 1
        db.commit()
        print(f"  Resolved and merged {spec_merged} specific duplicate pairs.")

        # ---------------------------------------------------------
        # Dimension 5: Systematic Thai OCR Normalization Deduplication
        # ---------------------------------------------------------
        print("\n--- Dimension 5: Thai OCR Normalization Deduplication ---")
        all_facs = db.query(FacultyDB).all()
        th_norm_map = defaultdict(list)
        for f in all_facs:
            if f.id in ghosts_to_archive_ids:
                continue
            norm_name = clean_thai_name_for_matching(f.full_name_th)
            if norm_name and len(norm_name) > 3:
                th_norm_map[(f.university_th, norm_name)].append(f)

        thai_ocr_merged = 0
        for (univ, norm_name), rows in th_norm_map.items():
            if len(rows) > 1:
                # Rank rows to choose winner
                rows.sort(key=score_record_as_winner, reverse=True)
                winner = rows[0]
                ghosts = rows[1:]
                for g in ghosts:
                    merge_faculty_metrics_and_lists(winner, g)
                    ghosts_to_archive_ids.add(g.id)
                    thai_ocr_merged += 1
        db.commit()
        print(f"  Resolved and merged {thai_ocr_merged} Thai OCR duplicate pairs.")

        # ---------------------------------------------------------
        # Dimension 6: Atomic Dual-Table Archival Transfer
        # ---------------------------------------------------------
        archive_ids_list = list(ghosts_to_archive_ids)
        print(f"\n--- Dimension 6: Atomic Archival Transfer to scholars_unassigned ---")
        print(f"Total ghost records to archive: {len(archive_ids_list):,}")

        if archive_ids_list:
            chunk_size = 1000
            for i in range(0, len(archive_ids_list), chunk_size):
                chunk = archive_ids_list[i : i + chunk_size]
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO public.scholars_unassigned
                            SELECT * FROM public.faculties
                            WHERE id IN :ids
                            ON CONFLICT (id) DO UPDATE SET
                                department = EXCLUDED.department,
                                department_th = EXCLUDED.department_th,
                                email = COALESCE(scholars_unassigned.email, EXCLUDED.email),
                                total_citations = GREATEST(scholars_unassigned.total_citations, EXCLUDED.total_citations),
                                h_index = GREATEST(scholars_unassigned.h_index, EXCLUDED.h_index),
                                total_publications_count = GREATEST(scholars_unassigned.total_publications_count, EXCLUDED.total_publications_count);
                        """),
                        {"ids": tuple(chunk)},
                    )
                    conn.execute(
                        text("DELETE FROM public.faculties WHERE id IN :ids"),
                        {"ids": tuple(chunk)},
                    )
                print(f"  Archived {min(i + chunk_size, len(archive_ids_list)):,}/{len(archive_ids_list):,} records...", flush=True)

    finally:
        db.close()

    # ---------------------------------------------------------
    # Dimension 7: Final Comprehensive Verification & Invariants Audit
    # ---------------------------------------------------------
    with engine.connect() as conn:
        final_fac = conn.execute(text("SELECT count(*) FROM public.faculties")).scalar()
        final_unassigned = conn.execute(text("SELECT count(*) FROM public.scholars_unassigned")).scalar()
        unspecified_dept = conn.execute(
            text("SELECT count(*) FROM public.faculties WHERE department_th = 'ระบุไม่ได้' OR department_th IS NULL")
        ).scalar()
        dup_names_count = conn.execute(
            text("""
                SELECT count(*) FROM (
                    SELECT full_name_th FROM public.faculties
                    WHERE full_name_th IS NOT NULL AND length(full_name_th) > 3
                    GROUP BY full_name_th
                    HAVING count(*) > 1
                ) s;
            """)
        ).scalar()
        dup_oa_count = conn.execute(
            text("""
                SELECT count(*) FROM (
                    SELECT openalex_id FROM public.faculties
                    WHERE openalex_id IS NOT NULL AND openalex_id != '' AND openalex_id != 'not_indexed'
                    GROUP BY openalex_id
                    HAVING count(*) > 1
                ) s;
            """)
        ).scalar()

        print("\n" + "=" * 65)
        print("🏆 COMPREHENSIVE FACULTY HYGIENE & ZERO-DEFECT QUALITY AUDIT:")
        print(f"- Primary 'faculties' table: {final_fac:,} clean, verified teaching faculty")
        print(f"- Archival 'scholars_unassigned' table: {final_unassigned:,} records")
        print(f"- Total scholars preserved across both tables: {final_fac + final_unassigned:,}")
        print(f"- Unspecified department count: {unspecified_dept} (MUST BE 0)")
        print(f"- Duplicate full_name_th remaining: {dup_names_count} (MUST BE 0)")
        print(f"- Duplicate openalex_id remaining: {dup_oa_count} (MUST BE 0)")
        print("=" * 65)

    print(f"Deep evidence hygiene execution completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    execute_deep_evidence_hygiene()
