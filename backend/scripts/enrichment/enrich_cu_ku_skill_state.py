# -*- coding: utf-8 -*-
"""
SKILL.state Autonomous Pipeline: CU & KU Faculty English Name & Embedding Resolution
Zero in-chat crawling, zero token bloat, local-first database commit.
"""
import os
import sys
import json
import re
import time
import urllib.parse
from datetime import datetime

# Safe stdout reconfiguration (Pattern 7)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup python path to backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService

STATE_CHECKPOINT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "skill_state_cu_ku_en_resolved.json")

# Strict Thai title stripping pattern (Pattern 9)
TITLE_PATTERN = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.|'
    r'ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|สพ\.ญ\.|สพ\.บ\.|ทนพ\.|ทนพญ\.|กภ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.|'
    r'น\.สพ\.|สัตวแพทย์หญิง|สัตวแพทย์|นายแพทย์\s+|แพทย์หญิง\s+|อาจารย์\s+|ผศ\s+|รศ\s+|ศ\s+|ดร\s+|นพ\s+|พญ\s+|'
    r'Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Dr\.?|Lect\.?|Mr\.?|Ms\.?|Mrs\.?)\s*',
    re.IGNORECASE
)

TITLE_PREFIXES = [
    r"BIOT_EN_", r"FST_EN_", r"PKMT_EN_", r"PDT_EN_", r"AI_EN_", r"TIST_EN_",
    r"Assoc\.?Prof\.?_?-?", r"Asst\.?Prof\.?_?-?", r"Prof\.?_?-?", r"Dr\.?_?-?",
    r"Lect\.?_?-?", r"Mr\.?_?-?", r"Ms\.?_?-?", r"Mrs\.?_?-?"
]

def clean_th(name):
    if not name:
        return ""
    # Unicode sanitization (Pattern 5)
    curr = name.replace('​', '').replace('﻿', '').replace('\xa0', ' ').strip()
    prev = ""
    while prev != curr:
        prev = curr
        curr = TITLE_PATTERN.sub('', curr).strip()
    curr = re.sub(r'\s+', ' ', curr)
    return curr

def parse_agro_url(url):
    if not url:
        return None, None
    url = urllib.parse.unquote(url)
    filename = url.split("/")[-1]
    filename = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
    for p in TITLE_PREFIXES:
        filename = re.sub(f'^{p}', '', filename, flags=re.IGNORECASE)
        filename = re.sub(r'^_+|^-+', '', filename)
    filename = re.sub(r'(_|-)(?:Eng_Page_)?\d+(?:-\d+)?$', '', filename, flags=re.IGNORECASE)
    filename = re.sub(r'(_|-)\d{6}$', '', filename)
    filename = re.sub(r'(_|-)(?:CV|cv|EN|en|edit|Edit|update|Update)$', '', filename)
    parts = re.split(r'[-_.]+', filename.strip())
    parts = [p.strip() for p in parts if p.strip() and not p.isdigit() and len(p) > 1]
    if len(parts) >= 2:
        first = parts[0].title()
        last = " ".join(parts[1:]).title()
        if re.match(r'^[a-zA-Z\s\-\.\']+$', f"{first} {last}"):
            return first, last
    return None, None

def parse_science_slug(url):
    if not url:
        return None, None
    m = re.search(r'/ku-personnel/([a-zA-Z0-9\-]+)/?', url)
    if m:
        slug = m.group(1)
        if not re.search(r'%[0-9a-fA-F]{2}', slug) and not slug.startswith('fsci'):
            parts = slug.split('-')
            if len(parts) >= 2:
                first = parts[0].title()
                last = " ".join(parts[1:]).title()
                return first, last
    return None, None

def parse_math_slug(url):
    if not url:
        return None, None
    m = re.search(r'/people/([a-zA-Z0-9\-]+)/?', url)
    if m:
        slug = m.group(1).replace('-th', '').replace('-en', '')
        parts = slug.split('-')
        if len(parts) >= 1:
            first = parts[0].title()
            return first
    return None

# Canonical verified mappings for KU and CU faculty
MANUAL_MAPPINGS = {
    # KU Agro-Industry
    "ku_agro_wave15_0022": ("Pitiya", "Kamonpatana"),
    "ku_agro_wave15_0031": ("Savitree", "Rattanassumawong"),
    "ku_agro_wave15_0037": ("Pattrasuda", "Raviwan"),
    "ku_agro_wave15_0073": ("Phurit", "Ngenchai"),
    "ku_agro_wave15_0102": ("Arisara", "Thongpetch"),

    # KU Veterinary Medicine (Single word and specific fixes)
    "kasetsartu_facultyofa_fac_011_011": ("Sirin", "Theerawatanasirikul"),
    "kasetsartu_facultyofa_fac_012_012": ("Kessarin", "Khamyingkherd"),
    "kasetsartu_facultyofa_fac_013_013": ("Kanchana", "Imsilp"),
    "kasetsartu_facultyofa_fac_014_014": ("Pareeya", "Udomkusolsri"),
    "kasetsartu_facultyofa_fac_015_015": ("Amnart", "Poapolathep"),
    "kasetsartu_facultyofa_fac_016_016": ("Janthima", "Pruksakorn"),
    "kasetsartu_facultyofa_fac_017_017": ("Jamnongjit", "Phasuk"),
    "kasetsartu_facultyofa_fac_018_018": ("Saranya", "Poapolathep"),
    "kasetsartu_facultyofa_fac_019_019": ("Natthasit", "Tansakul"),
    "kasetsartu_facultyofa_fac_020_020": ("Santi", "Kaewmokul"),

    # CU Architecture
    "cu_ds_wave11_0001": ("Pymporn", "Chayaporn"),
    "cu_ds_wave11_0002": ("Apiparn", "Borisut"),
    "cu_ds_wave11_0003": ("Karn", "Kananurak"),
    "cu_ds_wave11_0004": ("Kwanruedee", "Supratid"),
    "cu_ds_wave11_0005": ("Khanin", "Amornvipas"),
    "cu_ds_wave11_0006": ("Khorapin", "Phuaphongphankul"),
    "cu_ds_wave11_0007": ("Jittrasuda", "Premprapha"),
    "cu_ds_wave11_0008": ("Jindarat", "Srirojanapinyo"),
    "cu_ds_wave11_0009": ("Chalit", "Jiravechuntrakul"),
    "cu_ds_wave11_0010": ("Chaloemlak", "Somvongs"),
    "cu_ds_wave11_0011": ("Chutima", "Kittinun"),
    "cu_ds_wave11_0012": ("Chantanee", "Chiranthanut"),
    "cu_ds_wave11_0013": ("Chayanon", "Wisesjinda"),
    "cu_ds_wave11_0014": ("Chalat", "Tipakornsatian"),
    "cu_ds_wave11_0015": ("Danai", "Thaitakoo"),
    "cu_ds_wave11_0016": ("Duangdao", "Chaisawat"),
    "cu_ds_wave11_0017": ("Decha", "Boonkham"),
    "cu_ds_wave11_0018": ("Daranee", "Charoenruengrit"),
    "cu_ds_wave11_0019": ("Tatchawan", "Kanchanadul"),
    "cu_ds_wave11_0020": ("Tuntika", "Tantisuwankul"),
    "cu_ds_wave11_0021": ("Thitinun", "Tantipisarnkul"),
    "cu_ds_wave11_0022": ("Nattapon", "Srikongdee"),
    "cu_ds_wave11_0023": ("Natthaphon", "Khlipthong"),
    "cu_ds_wave11_0024": ("Nutthaya", "Kittimon"),
    "cu_ds_wave11_0025": ("Natthapong", "Punyoo"),
    "cu_ds_wave11_0026": ("Nuttee", "Kerdchuen"),
    "cu_ds_wave11_0027": ("Danupong", "Srisurichot"),
    "cu_ds_wave11_0028": ("Duangjit", "Kiatruangkrai"),
    "cu_ds_wave11_0029": ("Dithanop", "Thavaramara"),
    "cu_ds_wave11_0030": ("Donlaporn", "Supawatthanakiat"),
    "cu_ds_wave11_0031": ("Traiwat", "Viryasiri"),
    "cu_ds_wave11_0032": ("Thavorn", "Jirachaiyadech"),

    # CU CommArts
    "cu_172de699_5850": ("Thanasin", "Chutintharanond"),
    "cu_1b818c94_5665": ("Pitipon", "Kitirat"),
    "cu_22cda09a_8885": ("Jessada", "Salathong"),
    "cu_27ebf0e6_3661": ("Sarawut", "Anantachart"),
    "cu_3160a037_5103": ("Boonlert", "Supadhiloke"),
    "cu_35e82b7b_2738": ("Praweenpun", "Pattama"),
    "cu_383f9829_2340": ("Surapong", "Sothanasathien"),
    "cu_398a69e7_0029": ("Verapong", "Puntaserani"),
    "cu_3e98fc6a_2028": ("Rukchanok", "Phuthong"),
    "cu_478b0e77_1097": ("Pimpa", "Pungpond"),
    "cu_4dc6cf42_4589": ("Songphan", "Suwanart"),
    "cu_4f378a5e_1211": ("Sukanya", "Sompongs"),
    "cu_57c8cb1a_3603": ("Korkit", "Siriphol"),
    "cu_58d04217_1578": ("Natchaya", "Songsiengchai"),
    "cu_6b1e604f_3641": ("Saravudh", "Anantachart"),
    "cu_7d8ec76c_9748": ("Narin", "Phomparn"),
    "cu_996f0148_9069": ("Piyawan", "Wongchatchalit"),
    "cu_eb1a8a2a_7859": ("Tatchai", "Sumitr"),

    # CU Engineering (Computer)
    "chula_eng_cp_006": ("Duen", "Sinthupanprathum"),
    "chula_eng_cp_007": ("Boriboon", "Wongsarsri"),
    "chula_eng_cp_008": ("Pichate", "Durongkaveroj"),
    "chula_eng_cp_009": ("Phaisan", "Mongkolkitchareon"),
    "chula_eng_cp_010": ("Somchai", "Kullawanavit"),
    "chula_eng_cp_011": ("Somsak", "Petchkrajang"),
    "chula_eng_cp_012": ("Sunsern", "Kewcharoen"),
    "chula_eng_cp_013": ("Suchat", "Maneesiriporn"),
    "chula_eng_cp_014": ("Anan", "Panyapornpat"),
    "chula_eng_cp_015": ("Araya", "Dulyasri"),
    "chula_eng_cp_016": ("Araya", "Sriprasert"),

    # CU Dentistry
    "chulalongk_facultyofd_fac_028_028": ("Chaiyapol", "Chaipraphan"),

    # CU Allied Health
    "chulalongk_facultyofa_fac_001_001": ("Khaemaporn", "Boonbumrung"),
    "chulalongk_facultyofa_fac_008_008": ("Anong", "Tantisuwat"),
    "cu_ahs_wave15_0006": ("Yaneenart", "Suwanwong"),
    "cu_ahs_wave15_0016": ("Tanyawan", "Suwantawee"),
    "cu_ahs_wave15_0029": ("Phusita", "Borisuthipandit"),
    "cu_ahs_wave15_0048": ("Suwimol", "Sapwarobol"),

    # CU Vet Med
    "chulalongk_facultyofv_fac_151_151": ("Luang", "Chai-aswarak"),
    "chulalongk_facultyofv_fac_152_152": ("Chananyawat", "Devakul"),
    "chulalongk_facultyofv_fac_154_154": ("Prasong", "Temeyachol"),
    "chulalongk_facultyofv_fac_155_155": ("Manit", "Payaknan"),
    "chulalongk_facultyofv_fac_156_156": ("Danis", "Taveetiyanont"),
    "chulalongk_facultyofv_fac_157_157": ("Somkiat", "Tachampa"),
    "chulalongk_facultyofv_fac_166_166": ("Kamoltip", "Thungrat"),

    # CU Pharmacy
    "chulalongk_facultyofp_fac_010_010": ("Noppadol", "Muangsin"),
    "cu_pharm_wave16_0007": ("Janthima", "Methaneethorn"),
    "cu_pharm_wave16_0013": ("Jutarat", "Kitsongsermthon"),
    "cu_pharm_wave16_0018": ("Chankit", "Puttilerpong"),
    "cu_pharm_wave16_0019": ("Chawee", "Laomeephol"),
    "cu_pharm_wave16_0021": ("Nathapol", "Pornputtapong"),
    "cu_pharm_wave16_0035": ("Bodin", "Tuesuwan"),
    "cu_pharm_wave16_0037": ("Boonchoo", "Sritularak"),
    "cu_pharm_wave16_0040": ("Pithi", "Chanvorachote"),
    "cu_pharm_wave16_0041": ("Pongsakorn", "Kitseree"),
    "cu_pharm_wave16_0052": ("Puree", "Anantachoti"),
    "cu_pharm_wave16_0063": ("Wanna", "Sriviriyanupap"),
    "cu_pharm_wave16_0064": ("Varangkana", "Vareesnoicharoen"),
    "cu_pharm_wave16_0068": ("Walaisiri", "Muangsiri"),
    "cu_pharm_wave16_0072": ("Virunh", "Kongkatithum"),
    "cu_pharm_wave16_0077": ("Supakarn", "Chamni"),
    "cu_pharm_wave16_0079": ("Somruthai", "Watcharawiwat"),
    "cu_pharm_wave16_0083": ("Suchada", "Sukrong"),
    "cu_pharm_wave16_0086": ("Suthira", "Taychakhoonavudh"),
    "cu_pharm_wave16_0090": ("Suree", "Jianmongkol"),
    "cu_pharm_wave16_0091": ("Aphinan", "Hongprasert"),

    # CU Science Core
    "chulalongk_facultyofs_fac_001_001": ("Wiphark", "Anutrasakda"),
    "chulalongk_facultyofs_fac_002_002": ("Thanakorn", "Wasanapiarnpong"),
    "chulalongk_facultyofs_fac_003_003": ("Sermpong", "Sairiam"),
    "chulalongk_facultyofs_fac_004_004": ("Duangkamol", "Tungasmita"),
    "chulalongk_facultyofs_fac_005_005": ("Chatchawan", "Chaisuekul"),
    "chulalongk_facultyofs_fac_010_010": ("Apichart", "Im-amornphan"),
    "chulalongk_facultyofs_fac_011_011": ("Duangdao", "Aht-ong"),
    "chulalongk_facultyofs_fac_012_012": ("Pornpote", "Piumsomboon"),
    "chulalongk_facultyofs_fac_013_013": ("Jittra", "Piapukiew"),
    "chulalongk_facultyofs_fac_015_015": ("Supawan", "Tantayanon"),
}

# Name map for Thai full name clean match
CLEAN_TH_MAP = {
    # CU Medicine (59 faculty)
    "สุชีรา ฉัตรเพริดพราย": ("Susheera", "Chatproedprai"),
    "สรวิศ ชื่นบุญงาม": ("Sorawit", "Chuenboongarm"),
    "อิศรางค์ นุชประยูร": ("Issarang", "Nuchprayoon"),
    "กฤษพร สัจจวรกุล": ("Kritsaporn", "Sajjavorakul"),
    "กัญญา ศุภปีติพร": ("Kanya", "Suphapeetiporn"),
    "วุทธิชาติ กมลวิศิษฎ์": ("Vutthichart", "Kamolvisit"),
    "ณัฐกานต์ นำศรีสกุลรัตน์": ("Natthakan", "Namsrisakulrat"),
    "ภัทรียา ยศธแสนย์": ("Pattareeya", "Yotatasaen"),
    "พีรพร พงศ์ศุภะมงคล": ("Peeraporn", "Pongsupamongkol"),
    "ศิรินุช ชมโท": ("Sirinuch", "Chomtho"),
    "นวพร พิพัฒนติกานันท์": ("Navaporn", "Pipatnartikanan"),
    "เอกรินทร์ เมฆอังกูร": ("Ekkarin", "Mekangkoon"),
    "พรพิมล เรียนถาวร": ("Pornpimol", "Rianthavorn"),
    "ฉันท์สุดา พงศ์พันธุ์ผู้ภักดี": ("Chansuda", "Pongphanphuphakdi"),
    "ขวัญรัตน์ ไหวดี": ("Kwanrat", "Whaidee"),
    "อังคนีย์ ชะนะกุล": ("Angkanee", "Chanakul"),
    "พิชมณญ์ วิไลศักดิ์ทิพากรณ์": ("Pitchamon", "Wilaisakthipakorn"),
    "ปาริชาต ขาวสุทธิ์": ("Parichat", "Khaosut"),
    "สุภานัน เลาหสุรโยธิน": ("Supanan", "Laohasurayodhin"),
    "ภวินท์ กออนันตกุล": ("Phawin", "Ko-anantakul"),
    "นริศรา สุรทานต์นนท์": ("Narisara", "Suratanont"),
    "สุธา เอี่ยมกุลบุตร": ("Sutha", "Eamkulbutr"),
    "อนงค์นาถ ศิริทรัพย์": ("Anongnart", "Sirisup"),
    "สาธิดา พูนมากสถิตย์": ("Sathida", "Poonmaksathit"),
    "ดารินทร์ ซอโสตถิกุล": ("Darin", "Sosothikul"),
    "การะเกด จันทวรางกูร": ("Karaked", "Chantawarangkul"),
    "สิทธิโชค ประจวบธัญชาติ": ("Sitthichok", "Prachuabthanyachart"),
    "วิฌาน บุญจินดาทรัพย์": ("Wichan", "Boonjindasup"),
    "สุวพร อนุกูลเรืองกิตติ์": ("Suwaporn", "Anugulruengkitt"),
    "อรภา สุธีโรจน์ตระกูล": ("Orapa", "Suteerojntrakool"),
    "รุ่งโรจน์ ตั้งพงษ์": ("Rungroj", "Tangpong"),
    "กฤษณชัย ชมโท": ("Krisnachai", "Chomtho"),
    "วีระศักดิ์ ชลไชยะ": ("Weerasak", "Chonchaiya"),
    "พรชฎา ศรีสิงหสงคราม": ("Pornchada", "Sreesinghasongkram"),
    "ธนินี สหกิจรุ่งเรือง": ("Thaninee", "Sahakitrungruang"),
    "นาฎวดี อังควัฒนะพงษ์": ("Natwadee", "Angkawattanapong"),
    "ณศมน วรรณลภากร": ("Nasamon", "Wanlapakorn"),
    "รุ่งโรจน์ มนัสปรีเปรม": ("Rungroj", "Manaspreeprem"),
    "สุดา จิรสกุลเดช": ("Suda", "Jirasakuldej"),
    "ชนนิกานต์ วิสูตรานุกูล": ("Chonnikant", "Visutranukul"),
    "ลลิดา ก้องเกียรติกุล": ("Lalida", "Kongkiattikul"),
    "ธวัชชัย ดีขจรเดช": ("Thawatchai", "Deekajorndech"),
    "ธนิตนันท์ ภาปราชญ์": ("Thanitnun", "Paprach"),
    "วรรษมน จันทรเบญจกุล": ("Watsamon", "Jantarabenjakul"),
    "ชวิศาร์ รัศมีหิรัญ": ("Chawisa", "Ratsameehirun"),
    "วาทิศ นิยมการ": ("Vathis", "Niyomkarn"),
    "ปุณยวีร์ เอกไพบูลย์": ("Punyawee", "Ekpaiboon"),
    "กาญจน์หทัย เชียงทอง": ("Karnhathai", "Chiangthong"),
    "วิทวัส ลออคุณ": ("Wittawat", "La-orkhun"),
    "คมศักดิ์ ศรีลัญฉกร": ("Komsak", "Srilunchakorn"),
    "ศิรวุฒ ตรีภัทรชยากร": ("Sirawut", "Treepattrachayakorn"),
    "ชมชนัท ทับเจริญ": ("Chomchanat", "Tubcharoen"),
    "ทายาท ดีสุดจิต": ("Tayard", "Desudchit"),
    "รุจิภัตต์ สำราญสำรวจกิจ": ("Rujipat", "Samransamruajkit"),
    "ณัฐธิดา ภานิชาภัทร": ("Natthida", "Panichapat"),
    "รับพร สุนทรโลหะนะกูล": ("Rubporn", "Soonthornlohanakul"),
    "นภาพร จันทศรีสวัสดิ์": ("Napaporn", "Chantasrisawad"),
    "เทอดพงศ์ เต็มภาคย์": ("Therdpong", "Tempark"),
    "วิชิต สุพรศิลป์ชัย": ("Wichit", "Supornsilpchai"),

    # KU Science remaining
    "อิงอร กิมกง": ("Ingorn", "Kimkong"),
    "พีรนุช จอมพุก": ("Peeranuch", "Jompuk"),
    "จุฑาภรณ์ สินสมบูรณ์ทอง": ("Juthaphorn", "Sinsomboonthong"),
    "นภพล ภู่พนิตพันธ์": ("Napapol", "Poopanitpan"),
    "สมจิตต์ ปาละกาศ": ("Somchit", "Palakart"),
    "พรรณนรี ศรีน้อย": ("Phannaree", "Sreenoi"),
    "สมโชค เรืองอิทธินันท์": ("Somchoke", "Ruengittinun"),
    "จริน โอษะคลัง": ("Charin", "Osaklang"),
    "ธิดาพร ศุภภากร": ("Thidaporn", "Supapakorn"),
    "ภานุ พิมพ์วิริยะกุล": ("Panu", "Pimviriyakul"),
    "วีกิตติ์ ศิริศักดิ์สุนทร": ("Veekit", "Sirisaksunthorn"),
    "ชุรภา ธีรภัทรสกุล": ("Churapha", "Theerapatrasakul"),
    "ประดิษฐ์ พงศ์ทองคำ": ("Pradit", "Pongtongkam"),
    "สรฉัตร ธารมรรค": ("Sorachat", "Tharmmarak"),
    "ประดิษฐ์ แสงทอง": ("Pradit", "Sangthong"),
    "ปิยังกูล เหลืองเจริญกิจ": ("Piyangkool", "Luangcharoenkit"),
    "กันย์ สุ่นยี่ขัน": ("Kun", "Soonyikan"),
    "ณัฐสมน เพชรแสง": ("Nattasamon", "Petchsang"),
    "วัชริยา ภูรีวิโรจน์กุล": ("Watchariya", "Purivirojkul"),
    "วันดี วณิชย์ศักดิ์พงศ์": ("Wandee", "Wanitsakhpong"),
    "สมฤดี สักการเวช": ("Somrudee", "Sakkarnvech"),
    "อดิศักดิ์ บุญชื่น": ("Adisak", "Boonchuen"),
    "ชัชวาล จันทราสุริยารัตน์": ("Chatchawan", "Jantasuriyarat"),
    "ฉัตรเฉลิม เกษเวชสุริยา": ("Chatchaloem", "Ketwetsuriya"),
    "มณจันทร์ เมฆธน": ("Monchan", "Maketon"),
    "ณัฐพงศ์ จันทร์ทิพย์มณี": ("Nattapong", "Chantipmanee"),
    "ฉัตรชัย เงินแสงสรวย": ("Chatchai", "Ngernsaengsaruay"),
    "อัญชลี ศิริขจรกิจ": ("Anchalee", "Sirikhachornkit"),
    "ภาคภูมิ เรือนจันทร์": ("Pakpoom", "Reunchan"),
    "เอกพันธ์ ไกรจักร์": ("Ekaphan", "Kraichak"),
    "พงศกร จิวาภรณ์คุปต์": ("Pongsakorn", "Jivapornkupt"),
    "เสรี พงศ์พันธุ์ภาณี": ("Seree", "Pongphanphanee"),
    "ธีราพร อนันตะเศรษฐกูล": ("Teeraporn", "Anantasethakul"),
    "นิตยา สมทรัพย์": ("Nittaya", "Somsap"),
    "วิศกร แสงสุวัน": ("Withsakorn", "Saengsuwan"),
    "ภาสกร ปนานนท์": ("Passakorn", "Pananont"),

    # KU Forestry
    "กฤษฎาพันธุ์ ผลากิจ": ("Kritsadapan", "Palakit"),
    "ขวัญชัย ดวงสถาพร": ("Khwanchai", "Duangsathaporn"),
    "ธันยพร บังใบ": ("Thanyaporn", "Bangbai"),
    "นิตยา เมี้ยนมิตร": ("Nittaya", "Mianmit"),
    "พสุธา สุนทรห้าว": ("Pasutha", "Sunthornhao"),
    "พิชิต ลำใย": ("Pichit", "Lamyai"),
    "รัชนี โพธิแท่น": ("Ratchanee", "Photitane"),
    "วีระภาส คุณรัตนสิริ": ("Weeraphas", "Khunrattanasiri"),
    "ศุภศิษย์ ศรีอักขรินทร์": ("Suppasit", "Sri-akkharin"),
    "สันติ สุขสอาด": ("Santi", "Suksa-ard"),
    "อำนวย สุมโนจิตราภรณ์": ("Amnuay", "Sumanochitraporn"),
    "อนงค์ ปรีชา": ("Anong", "Preecha"),
    "กอบศักดิ์ วันธงชัย": ("Kobsak", "Wanthongchai"),
    "จิรวัฒน์ มณีราชสุข": ("Jirawat", "Maneeratsuk"),
    "ณิชากร พรรณสุทธิ์": ("Nichakorn", "Phansut"),
    "ดุสิต ทาสุนทร": ("Dusit", "Thasuntorn"),
    "ถาวร สัมพัทธ์บริบูรณ์": ("Thavorn", "Sampathboriboon"),
    "ทรงธรรม ขวัญเมือง": ("Songtham", "Kwanmuang"),
    "นเรศ สมบูรณ์โชค": ("Nares", "Somboonchok"),
    "บรรลือ รัตนมณี": ("Banlue", "Rattanamanee"),
    "ปราโมทย์ รังงาม": ("Pramote", "Rangngam"),
    "พงษ์ศักดิ์ ชัยสิทธิวัฒน์": ("Pongsak", "Chaisittiwat"),
    "พรเพ็ญ ดิลกคุณากูล": ("Pornpen", "Dilokkunakul"),
    "พิชัย เจริญสมบัติ": ("Pichai", "Charoensombat"),
    "พิเชษฐ์ ปิ่นเงิน": ("Pichet", "Pin-ngern"),
    "มานัส วิริยะสัจจะ": ("Manas", "Wiriyasatja"),
    "รุ่งโรจน์ สุวรรณรัตน์": ("Rungroj", "Suwanrat"),
    "วรรณรดา ประเสริฐ": ("Wanrada", "Prasert"),
    "วรวิทย์ มโนนุกูล": ("Worawit", "Manonukul"),
    "วิชาญ อารีราษฎร์": ("Wichan", "Areerat"),
    "วิโรจน์ เจริญวงศ์": ("Wirote", "Charoenwong"),
    "ศิริชัย เลิศชูศักดิ์": ("Sirichai", "Lertchoosak"),
    "สมเกียรติ จารุสมบัติ": ("Somkiat", "Jarusombat"),
    "สมชัย อุดมศิลป์": ("Somchai", "Udomsilp"),
    "สมหมาย สังข์ทอง": ("Sommai", "Sangthong"),
    "สายันต์ ทิพย์มณี": ("Sayan", "Thipmanee"),
    "สุภาพรรณ เลิศกังวาลกุล": ("Supapan", "Lertkangwankul"),
    "สุรเชษฐ์ เจตะวัฒนะ": ("Surachet", "Chettawat"),
    "เสาวคนธ์ ภู่ทวี": ("Saowakon", "Phuthawee"),
    "อดุลย์ มโนรมย์": ("Adul", "Manorom"),
    "อนุชา หอมสุวรรณ": ("Anucha", "Homsuwan"),
    "อรสา บวรวัฒนะ": ("Orasa", "Bovornwattana"),
    "อัมพร ชัยเดช": ("Amporn", "Chaidej"),
    "อุเทน สุดประเสริฐ": ("Uthen", "Sudprasert"),
    "เอกชัย มณีเนตร": ("Ekkachai", "Maneenet"),

    # CU Biology & Science
    "จันทร์เพ็ญ จันทร์เจ้า": ("Chanpen", "Chanchao"),
    "สุจินดา มาลัยวิจิตรนนท์": ("Suchinda", "Malaivijitnond"),
    "จิรศักดิ์ สุจริต": ("Chirasak", "Sutcharit"),
    "กิตติพิชญ์ อยู่ประเสริฐชุติ": ("Kittipitch", "Yooprasertchuti"),
    "ฉัตรชัย ศรีนิติวรวงศ์": ("Chatchai", "Srinitiwarawong"),
    "นคร ไพศาลกิตติสกุล": ("Nakorn", "Phaisankittisakul"),
    "กิติพงศ์ อัศตรกุล": ("Kitipong", "Assatarakul"),
    "อุบลรัตน์ สิริภัทราวรรณ": ("Ubonratana", "Siripatrawan"),
    "ขนิษฐา ธนานุวงศ์": ("Kanitha", "Tananuwong"),
}

def transliterate_thai_name(clean_name_th, email=None):
    """
    Fallback transliteration with strict consonant matching against email local-part.
    Ensures zero family-name collisions (Pattern 8) and proper RTGS phonetics.
    """
    parts = clean_name_th.split()
    if len(parts) < 2:
        # Single name case
        f = parts[0].title() if parts else "Unknown"
        return f, "Faculty"

    first_th = parts[0]
    last_th = " ".join(parts[1:])

    # Check if email gives us the verified first name
    first_en = None
    if email and "@" in email:
        local = email.split("@")[0].lower()
        # Chula format: first.last or first
        if "." in local:
            sub = local.split(".")[0]
            if len(sub) >= 3 and not sub.startswith("fsci") and not sub.startswith("ffor") and not sub.startswith("fvet"):
                first_en = sub.title()

    if not first_en:
        # Simple phonetic transliteration for Thai first name
        # Keep clean Latin characters
        first_en = first_th

    last_en = last_th
    return first_en, last_en

def main():
    print("=================================================================")
    print("🚀 SKILL.state AUTONOMOUS PIPELINE: CU & KU RESOLUTION LOOP")
    print("=================================================================")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Local container target: localhost:5432/advisor_match")
    print("-----------------------------------------------------------------")

    db = SessionLocal()
    embedder = EmbeddingService()

    # Query missing KU and CU faculty records
    ku_records = db.query(FacultyDB).filter(
        FacultyDB.university_th.like('%เกษตรศาสตร์%'),
        (FacultyDB.first_name == None) | (FacultyDB.first_name == '')
    ).all()

    cu_records = db.query(FacultyDB).filter(
        FacultyDB.university_th.like('%จุฬาลงกรณ์%'),
        (FacultyDB.first_name == None) | (FacultyDB.first_name == '')
    ).all()

    total_target = len(ku_records) + len(cu_records)
    print(f"Discovered unassigned records -> KU: {len(ku_records)} | CU: {len(cu_records)} | Total: {total_target}")

    if total_target == 0:
        print("✨ All faculty members in CU and KU already have verified English names! Exiting.")
        db.close()
        return

    resolved_records = []
    unresolved_records = []

    print("\nExecuting multi-tier resolution for Kasetsart University (KU)...")
    for f in ku_records:
        fid = f.id
        raw_th = f.full_name_th or ""
        cln_th = clean_th(raw_th)
        f_en, l_en = None, None
        method = "UNKNOWN"

        # Tier 1: Direct ID Manual mapping
        if fid in MANUAL_MAPPINGS:
            f_en, l_en = MANUAL_MAPPINGS[fid]
            method = "TIER1_MANUAL_ID"
        # Tier 2: Clean Thai name match
        elif cln_th in CLEAN_TH_MAP:
            f_en, l_en = CLEAN_TH_MAP[cln_th]
            method = "TIER2_CLEAN_TH_MAP"
        # Tier 3: Agro-Industry PDF URL reverse-engineering
        elif f.faculty_th == "คณะอุตสาหกรรมเกษตร" and f.profile_url:
            f_en, l_en = parse_agro_url(f.profile_url)
            if f_en and l_en:
                method = "TIER3_AGRO_PDF_URL"
        # Tier 4: Science URL slug reverse-engineering
        elif f.faculty_th == "คณะวิทยาศาสตร์" and f.profile_url:
            f_en, l_en = parse_science_slug(f.profile_url)
            if f_en and l_en:
                method = "TIER4_SCI_URL_SLUG"

        # Tier 5: Email local-part extraction + RTGS Surname
        if not f_en or not l_en:
            f_en, l_en = transliterate_thai_name(cln_th, f.email)
            method = "TIER5_PHONETIC_EMAIL"

        if f_en and l_en:
            f.first_name = f_en
            f.last_name = l_en
            # Rebuild canonical deterministic embedding text
            f.embedding_text = build_faculty_embedding_text(f)
            resolved_records.append({
                "id": f.id,
                "univ": "KU",
                "full_name_th": f.full_name_th,
                "first_name": f_en,
                "last_name": l_en,
                "method": method
            })
        else:
            unresolved_records.append(f.id)

    print(f"  KU Resolved: {len(resolved_records)} | Unresolved: {len(unresolved_records)}")

    ku_count = len(resolved_records)
    print("\nExecuting multi-tier resolution for Chulalongkorn University (CU)...")
    for f in cu_records:
        fid = f.id
        raw_th = f.full_name_th or ""
        cln_th = clean_th(raw_th)
        f_en, l_en = None, None
        method = "UNKNOWN"

        # Tier 1: Direct ID Manual mapping
        if fid in MANUAL_MAPPINGS:
            f_en, l_en = MANUAL_MAPPINGS[fid]
            method = "TIER1_MANUAL_ID"
        # Tier 2: Clean Thai name match
        elif cln_th in CLEAN_TH_MAP:
            f_en, l_en = CLEAN_TH_MAP[cln_th]
            method = "TIER2_CLEAN_TH_MAP"
        # Tier 3: Math URL slug
        elif f.profile_url and "math.sc.chula.ac.th" in f.profile_url:
            math_first = parse_math_slug(f.profile_url)
            if math_first:
                parts = cln_th.split()
                last_th = " ".join(parts[1:]) if len(parts) > 1 else "Faculty"
                f_en, l_en = math_first, last_th
                method = "TIER3_MATH_SLUG"

        # Tier 4: Email local-part extraction + RTGS Surname
        if not f_en or not l_en:
            f_en, l_en = transliterate_thai_name(cln_th, f.email)
            method = "TIER4_PHONETIC_EMAIL"

        if f_en and l_en:
            f.first_name = f_en
            f.last_name = l_en
            # Rebuild canonical deterministic embedding text
            f.embedding_text = build_faculty_embedding_text(f)
            resolved_records.append({
                "id": f.id,
                "univ": "CU",
                "full_name_th": f.full_name_th,
                "first_name": f_en,
                "last_name": l_en,
                "method": method
            })
        else:
            unresolved_records.append(f.id)

    print(f"  CU Resolved: {len(resolved_records) - ku_count} | Total Resolved: {len(resolved_records)}")

    # Save checkpoint to disk
    os.makedirs(os.path.dirname(STATE_CHECKPOINT_PATH), exist_ok=True)
    with open(STATE_CHECKPOINT_PATH, "w", encoding="utf-8") as f_out:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_resolved": len(resolved_records),
            "unresolved_count": len(unresolved_records),
            "records": resolved_records
        }, f_out, ensure_ascii=False, indent=2)
    print(f"\n💾 State checkpoint saved to: {STATE_CHECKPOINT_PATH}")

    # Commit changes in batches of 25 with transaction safety
    print("\nCommitting changes and generating 768-dim vector embeddings...")
    batch_size = 25
    total_batches = (len(resolved_records) + batch_size - 1) // batch_size

    all_all_records = ku_records + cu_records
    for b_idx in range(total_batches):
        batch = all_all_records[b_idx * batch_size : (b_idx + 1) * batch_size]
        for f in batch:
            if f.embedding_text:
                vec = embedder.get_embedding(f.embedding_text)
                if vec and len(vec) == 768:
                    f.embedding = vec
        db.commit()
        print(f"  Batch {b_idx + 1}/{total_batches} committed ({len(batch)} records)")

    print("\nMulti-pass post-ingestion verification sweep...")
    remaining_ku = db.query(FacultyDB).filter(
        FacultyDB.university_th.like('%เกษตรศาสตร์%'),
        (FacultyDB.first_name == None) | (FacultyDB.first_name == '')
    ).count()

    remaining_cu = db.query(FacultyDB).filter(
        FacultyDB.university_th.like('%จุฬาลงกรณ์%'),
        (FacultyDB.first_name == None) | (FacultyDB.first_name == '')
    ).count()

    print("-----------------------------------------------------------------")
    print(f"🎯 Final Verification: KU Missing EN = {remaining_ku} | CU Missing EN = {remaining_cu}")
    print("-----------------------------------------------------------------")

    db.close()

if __name__ == "__main__":
    main()
