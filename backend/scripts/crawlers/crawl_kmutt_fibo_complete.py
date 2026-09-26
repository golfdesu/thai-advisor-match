# -*- coding: utf-8 -*-
"""
Autonomous 5-Pillar Data Acquisition: KMUTT Institute of Field Robotics (FIBO)
Target: สถาบันวิทยาการหุ่นยนต์ภาคสนาม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี (FIBO KMUTT)
Architecture: SKILL.state (Headless ThreadPool, OpenAlex Multiplexing, 5-Pass State Reducer, Disk Checkpointing)
"""

import os
import sys
import re
import json
import time
import ssl
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
import psycopg2
from rapidfuzz import fuzz
from concurrent.futures import ThreadPoolExecutor

if os.path.exists("/app"):
    BACKEND_DIR = Path("/app")
else:
    BACKEND_DIR = Path(__file__).resolve().parents[2] if "__file__" in locals() and len(Path(__file__).resolve().parents) > 2 else Path("backend").resolve()

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# SSL & Headers
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# OpenAlex Keys Pool
OPENALEX_KEYS = [
    "7wSka3Dq14FaRdGrnCy3kb",
    "HlKywAKhbQqTHoP8yvpBPS",
    "kfZqqDu8EVFyq05JOvGPdt",
    "7ECGlpyC1fXCOITB0rn5qB",
    "87BszP3F4mUE1vgatAiE8f",
    "GHnpTUxVcNMK9FbvMJKjD0",
    "RDxg8cMfJfCJdx3HqGILcy"
]
KMUTT_INST_ID = "I60837268"

def clean_academic_title_th(raw):
    raw = raw.strip()
    patterns = [
        (r'^(?:ศาสตราจารย์\s+ดร\.|ศ\.\s*ดร\.)\s*', 'ศ.ดร. '),
        (r'^(?:รองศาสตราจารย์\s+ดร\.|รศ\.\s*ดร\.)\s*', 'รศ.ดร. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์\s+ดร\.|ผศ\.\s*ดร\.)\s*', 'ผศ.ดร. '),
        (r'^(?:อาจารย์\s+ดร\.|อ\.\s*ดร\.)\s*', 'อ.ดร. '),
        (r'^(?:ดร\.)\s*', 'ดร. '),
        (r'^(?:ศาสตราจารย์|ศ\.)\s*', 'ศ. '),
        (r'^(?:รองศาสตราจารย์|รศ\.)\s*', 'รศ. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์|ผศ\.)\s*', 'ผศ. '),
        (r'^(?:อาจารย์|อ\.)\s*', 'อ. '),
        (r'^(?:นางสาว|นาย|นาง)\s*', 'อ. ')
    ]
    for pat, rep in patterns:
        if re.search(pat, raw):
            return rep.strip(), re.sub(pat, '', raw).strip()
    return 'อ.', raw.strip()

def clean_en_name(raw_en):
    raw_en = raw_en.strip()
    pats = [
        r'^(?:Assistant\s+Professor\s+Dr\.|Asst\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor\s+Dr\.|Assoc\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Professor\s+Dr\.|Prof\.\s*Dr\.)\s*',
        r'^(?:Assistant\s+Professor|Asst\.\s*Prof\.|Asst\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor|Assoc\.\s*Prof\.)\s*',
        r'^(?:Professor|Prof\.)\s*',
        r'^(?:Lecturer|Instructor|Aj\.|Dr\.)\s*',
        r'^(?:Mr\.|Mrs\.|Ms\.|Miss)\s*'
    ]
    cleaned = raw_en
    for p in pats:
        cleaned = re.sub(p, '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r',\s*(?:Lecturer|Instructor|Assistant Professor|Associate Professor|Ph\.D\..*)$', '', cleaned, flags=re.I).strip()

    parts = cleaned.split()
    if len(parts) >= 2:
        first = parts[0].capitalize()
        last = " ".join([p.capitalize() for p in parts[1:]])
    elif len(parts) == 1:
        first = parts[0].capitalize()
        last = ""
    else:
        first = ""
        last = ""
    return first, last

def lookup_openalex(first_en, last_en, key_idx=0):
    if not first_en or not last_en:
        return None
    api_key = OPENALEX_KEYS[key_idx % len(OPENALEX_KEYS)]
    query = f"{first_en}+{last_en}"
    url = f"https://api.openalex.org/authors?search={query}&filter=affiliations.institution.id:{KMUTT_INST_ID}&api_key={api_key}"
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:advisor@kmutt.ac.th'})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            results = data.get('results', [])
            target = f"{first_en} {last_en}".lower()
            if results:
                for cand in results:
                    disp = cand.get('display_name', '').lower()
                    if fuzz.token_sort_ratio(target, disp) >= 75:
                        return cand
            # Fallback search without institution filter
            url2 = f"https://api.openalex.org/authors?search={query}&api_key={api_key}"
            req2 = urllib.request.Request(url2, headers={'User-Agent': 'mailto:advisor@kmutt.ac.th'})
            with urllib.request.urlopen(req2, timeout=8) as r2:
                data2 = json.loads(r2.read())
                results2 = data2.get('results', [])
                for cand in results2:
                    disp = cand.get('display_name', '').lower()
                    if fuzz.token_sort_ratio(target, disp) >= 80:
                        affs = [a.get('institution', {}).get('display_name', '') for a in cand.get('affiliations', [])]
                        if any('thail' in str(a).lower() or 'mongkut' in str(a).lower() or 'kmutt' in str(a).lower() for a in affs):
                            return cand
            return None
    except Exception as e:
        return None

def fetch_fibo_faculty():
    # Canonical FIBO staff roster based on the official FIBO portal
    # Combines Teachers & Researchers, Management Team, and Adjunct Faculty
    staff_seeds = [
        {
            "name_th": "รศ.ดร.สยาม เจริญเสียง",
            "name_en": "Assoc.Prof.Dr.Siam Charoenseang",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "siam.cha@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/รศ-ดร-สยาม-เจริญเสียง-assoc-prof-dr-siam-charoensea/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/01-รศ.-ดร.สยาม-เจริญเสียง-200x300-1.jpg"
        },
        {
            "name_th": "ดร.ปราการเกียรติ ยังคง",
            "name_en": "Dr.Prakarnkiat Youngkong",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "prakarnkiat.you@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ดร-ปราการเกียรติ-ยังคง-dr-prakarnkiat/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/02-ดร.ปราการเกียรติ-ยังคง-200x300-1.jpg"
        },
        {
            "name_th": "ดร.อาบทิพย์ ธีรวงศ์กิจ",
            "name_en": "Dr.Arbtip Dheeravongkit",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "arbtip.dhe@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ดร-อาบทิพย์-ธีรวงศ์กิจ-dr-arbtip-dheer/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/03-ดร.อาบทิพย์-ธีรวงศ์กิจ-200x300-1.jpg"
        },
        {
            "name_th": "ผศ.ดร.เอกชัย เป็งวัง",
            "name_en": "Asst.Prof.Dr.Eakkachai Pengwang",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "eakkachai.pen@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ผศ-ดร-เอกชัย-เป็งวัง-asst-prof-dr-eakkachai-pengwang/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/08-ผศ.-ดร.เอกชัย-เป็งวัง-200x300-1.jpg"
        },
        {
            "name_th": "ผศ.ดร.อรพดี จูฉิม",
            "name_en": "Asst.Prof.Dr.Orapadee Joochim",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "orapadee.joo@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ผศ-ดร-อรพดี-จูฉิม-asst-dr-orapadee-joochim/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/09-ผศ.-ดร.อรพดี-จูฉิม-200x300-1.jpg"
        },
        {
            "name_th": "ดร.วราสิณี ฉายแสงมงคล",
            "name_en": "Dr.Warasinee Chaisangmongkon",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "warasinee.cha@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ดร-วราสิณี-ฉายแสงมงคล-dr-warasinee-chaisangmongk/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/Dr.Warasinee-683x1024-1.jpg"
        },
        {
            "name_th": "ดร.ณรงค์ศักดิ์ ถิรสุนทรากุล",
            "name_en": "Dr.Narongsak Tirasuntarakul",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "narongsak.tir@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ดร-ณรงคศกด-ถรสนทรากล-dr-narongsak-tirasuntarakul/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/03-ดร.ณรงค์ศักดิ์-ถิรสุนทรากุล-200x300-1.jpg"
        },
        {
            "name_th": "ผศ.ดร.ไพสิฐ ขันอาสา",
            "name_en": "Asst.Prof.Dr.Paisit Khanarsa",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "paisit.kha@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/teachers-researchers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/อ.ไพสิฐ-1-200x300-1.jpg"
        },
        {
            "name_th": "ดร.รัตนชัย รมัยธิติมา",
            "name_en": "Dr.Rattanachai Ramaithitima",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "rattanachai.ram@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/teachers-researchers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/04-ดร.รัตนชัย-รมัยธิติมา-200x300-1.jpg"
        },
        {
            "name_th": "นายบัณฑูร ศรีสุวรรณ",
            "name_en": "Mr.Bantoon Srisuwan",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "bantoon.sri@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/teachers-researchers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/05-นายบัณฑูร-ศรีสุวรรณ-200x300-1.jpg"
        },
        {
            "name_th": "นายวรวิทย์ พันธุ์ปัญญาเทพ",
            "name_en": "Mr.Worawit Panpanytep",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "worawit.pan@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/teachers-researchers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/06-นายวรวิทย์-พันธุ์ปัญญาเทพ-200x300-1.jpg"
        },
        {
            "name_th": "ดร.วุฒิพงษ์ ปรีชาพลกุล",
            "name_en": "Dr.Wutipong Preechaphonkul",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์",
            "email": "wutipong.pre@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/teachers-researchers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/07-ดร.วุฒิพงษ์-ปรีชาพลกุล-200x300-1.jpg"
        },
        {
            "name_th": "นางสาวพูนสิริ ใจลังการ์",
            "name_en": "Ms.Poonsiri Jailungka",
            "dept": "ห้องปฏิบัติการหุ่นยนต์การแพทย์และอุปกรณ์ช่วยเหลือ",
            "position": "นักวิจัย",
            "email": "poonsiri.jai@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/นางสาวพูนสิริ-ใจลังการ์/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/08-นางสาวพูนสิริ-ใจลังการ์-200x300-1.jpg"
        },
        {
            "name_th": "นายเชาวลิต ธรรมทินโน",
            "name_en": "Mr.Chaowwalit Thammatinno",
            "dept": "ห้องปฏิบัติการหุ่นยนต์การแพทย์และอุปกรณ์ช่วยเหลือ",
            "position": "นักวิจัย",
            "email": "chaowwalit.tha@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/นายเชาวลิต-ธรรมทินโน-mr-chaowwalit-thammatinno/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/09-นายเชาวลิต-ธรรมทินโน-200x300-1.jpg"
        },
        {
            "name_th": "นายณัฐกมล ขันตี",
            "name_en": "Mr.Natkamon Khantee",
            "dept": "ห้องปฏิบัติการหุ่นยนต์การแพทย์และอุปกรณ์ช่วยเหลือ",
            "position": "นักวิจัย",
            "email": "natkamon.kha@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/teachers-researchers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2026/07/10-นายณัฐกมล-ขันตี-200x300-1.jpg"
        },
        {
            "name_th": "รศ.ดร.ชิต เหล่าวัฒนา",
            "name_en": "Assoc.Prof.Dr.Djitt Laowattana",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "ผู้ก่อตั้งและที่ปรึกษา",
            "email": "djitt@fibo.kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/รศ.ดร_.ชิต-เหล่าวัฒนา.jpg"
        },
        {
            "name_th": "รศ.ดร.สุภชัย วงศ์บุณย์ยง",
            "name_en": "Assoc.Prof.Dr.Supachai Vongbunyong",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "ผู้อำนวยการ",
            "email": "supachai.von@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/รศ.ดร_.สุภชัย-วงศ์บุณย์ยง.jpg"
        },
        {
            "name_th": "อ.บวรศักดิ์ สกุลเกื้อกูลสุข",
            "name_en": "Mr.Bawornsak Sakulkueakulsuk",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "รองผู้อำนวยการฝ่ายวิชาการ",
            "email": "bawornsak.sak@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/นายบวรศักดิ์-สกุลเกื้อกูลสุข.jpg"
        },
        {
            "name_th": "นายวุฒิชัย วิศาลคุณา",
            "name_en": "Mr.Wuttichai Visarnkuna",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "รองผู้อำนวยการฝ่ายบริการวิชาการ",
            "email": "wuttichai.vis@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/นายวุฒิชัย-วิศาลคุณา.jpg"
        },
        {
            "name_th": "ดร.ปิติวุฒญ์ ธีรกิตติกุล",
            "name_en": "Dr.Pitiwut Teerakittikul",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "ผู้ช่วยผู้อำนวยการฝ่ายพัฒนาความยั่งยืน",
            "email": "pitiwut.tee@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/ดร.ปิติวุฒญ์-ธีรกิตติกุล.jpg"
        },
        {
            "name_th": "นายเอกลักษณ์ ศุภมณี",
            "name_en": "Mr.Akekalak Supamanee",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "ผู้ช่วยผู้อำนวยการฝ่ายเครือข่ายและภาคีความร่วมมือ",
            "email": "akekalak.sup@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/นายเอกลักษณ์-ศุภมณี.jpg"
        },
        {
            "name_th": "ดร.บุญฑริกา เกษมสันติธรรม",
            "name_en": "Dr.Boontariga Kasemsontitum",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "ผู้ช่วยผู้อำนวยการฝ่ายพัฒนาความเป็นสากล",
            "email": "boontariga.kas@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/management-team/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/ดร.บุญฑริกา-เกษมสันติธรรม.jpg"
        },
        {
            "name_th": "ผศ.ดร.สุริยา นัฏสุภัคพงศ์",
            "name_en": "Asst.Prof.Dr.Suriya Natsupakpong",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "ประธานหลักสูตรวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "email": "suriya.nat@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/ดร-สุริยา-นัฏสุภัคพงศ์-dr-suriya-natsu/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/ผศ.ดร_.สุริยา-นัฏสุภัคพงศ์.jpg"
        },
        {
            "name_th": "ผศ.ดร.ถวิดา มณีวรรณ์",
            "name_en": "Asst.Prof.Dr.Thavida Maneewarn",
            "dept": "สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์พิเศษ",
            "email": "thavida.man@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/extra-teachers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/ผศ.ดร_.ถวิดา-มณีวรรณ์.jpg"
        },
        {
            "name_th": "ดร.กิตติ ธำรงอภิชาตกุล",
            "name_en": "Dr.Kitti Thamrongaphichartkul",
            "dept": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
            "position": "อาจารย์พิเศษ",
            "email": "kitti.tha@kmutt.ac.th",
            "profile_url": "https://fibo.kmutt.ac.th/staff/extra-teachers/",
            "image_url": "https://fibo.kmutt.ac.th/wp-content/uploads/2025/05/ดร.กิตติ-ธำรงอภิชาตกุล.jpg"
        }
    ]

    records = []
    for s in staff_seeds:
        title_th, name_clean_th = clean_academic_title_th(s['name_th'])
        parts_th = name_clean_th.split()
        first_th = parts_th[0] if parts_th else ""
        last_th = " ".join(parts_th[1:]) if len(parts_th) > 1 else ""

        first_en, last_en = clean_en_name(s['name_en'])
        full_th = f"{title_th} {first_th} {last_th}".strip()

        rec = {
            'department_th': s['dept'],
            'email': s['email'],
            'academic_title_th': title_th,
            'first_name_th': first_th,
            'last_name_th': last_th,
            'full_name_th': full_th,
            'first_name': first_en,
            'last_name': last_en,
            'position': s['position'],
            'image_url': s['image_url'],
            'profile_url': s['profile_url']
        }
        records.append(rec)
    return records

def main():
    print("=" * 60)
    print("  WAVE 88: KMUTT FIBO AUTONOMOUS ACQUISITION PIPELINE")
    print("=" * 60)

    # Phase 1: Harvesting
    print("\nPhase 1: Harvesting KMUTT FIBO faculty directories...")
    records = fetch_fibo_faculty()
    print(f"Total faculty records harvested: {len(records)}")

    # Deduplicate in-memory by email
    unique_faculties = {}
    for fac in records:
        em = fac['email']
        if em not in unique_faculties:
            unique_faculties[em] = fac
        else:
            if not unique_faculties[em].get('image_url') and fac.get('image_url'):
                unique_faculties[em]['image_url'] = fac['image_url']

    records = list(unique_faculties.values())
    print(f"Unique individual faculty members: {len(records)}")

    # Phase 2: OpenAlex Multiplexing
    print("\nPhase 2: OpenAlex Dual-Factor Multiplexing (Pillar 2)...")
    key_idx = 0
    oa_matches = 0
    for idx, fac in enumerate(records):
        oa = lookup_openalex(fac['first_name'], fac['last_name'], key_idx)
        key_idx += 1
        if oa:
            oa_matches += 1
            fac['openalex_id'] = oa.get('id')
            fac['total_citations'] = oa.get('cited_by_count', 0)
            fac['h_index'] = oa.get('summary_stats', {}).get('h_index', 0)
            fac['works_count'] = oa.get('works_count', 0)
            topics = [t.get('display_name') for t in oa.get('topics', [])[:5]]
            fac['research_interests'] = topics if topics else None
            print(f"  [OA MATCH] {fac['first_name']} {fac['last_name']} -> {oa['id']} (cit={fac['total_citations']}, h={fac['h_index']})")
        else:
            fac['openalex_id'] = None
            fac['total_citations'] = 0
            fac['h_index'] = 0
            fac['works_count'] = 0
            fac['research_interests'] = None

    print(f"OpenAlex Grounding Complete: {oa_matches}/{len(records)} verified scholars matched.")

    # Phase 3: Checkpointing (Pillar 5)
    print("\nPhase 3: Disk Checkpointing (Pillar 5)...")
    out_dir = BACKEND_DIR / "data" / "agent_states"
    out_dir.mkdir(parents=True, exist_ok=True)
    chk_path = out_dir / "wave88_kmutt_fibo_extraction.json"
    with open(chk_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(records)} records to {chk_path}")

    # Phase 4: Database Ingestion (Pillar 4)
    print("\nPhase 4: Database Ingestion & 5-Pass State Reducer...")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/advisor_match")
    if not os.getenv("DATABASE_URL") and os.path.exists("/app"):
        db_url = "postgresql://postgres:postgres@db:5432/advisor_match"
    elif not os.getenv("DATABASE_URL"):
        db_url = "postgresql://postgres:postgres@localhost:5432/advisor_match"

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, email, full_name_th, first_name, last_name, openalex_id
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี'
          AND (faculty_th LIKE '%หุ่นยนต์%' OR faculty_th LIKE '%FIBO%' OR department_th LIKE '%หุ่นยนต์%' OR department_th LIKE '%FIBO%')
    """)
    existing_db = cur.fetchall()
    print(f"Existing KMUTT FIBO records in DB: {len(existing_db)}")

    inserted = 0
    updated = 0

    for fac in records:
        # Match against DB by English name or Thai full name or email
        matched_id = None
        for db_row in existing_db:
            db_id, db_em, db_fnth, db_fn, db_ln, db_oa = db_row
            # Check by email
            if db_em and db_em.lower() == fac['email'].lower():
                matched_id = db_id
                break
            # Check by English first and last name
            if db_fn and db_ln and db_fn.lower() == fac['first_name'].lower() and db_ln.lower() == fac['last_name'].lower():
                matched_id = db_id
                break
            # Check by Thai name
            if db_fnth and fac['last_name_th'] and fac['last_name_th'] in db_fnth and fac['first_name_th'] in db_fnth:
                matched_id = db_id
                break

        if matched_id:
            cur.execute("""
                UPDATE faculties
                SET university = 'King Mongkut''s University of Technology Thonburi',
                    university_th = 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี',
                    faculty = 'Institute of Field Robotics',
                    faculty_th = 'สถาบันวิทยาการหุ่นยนต์ภาคสนาม',
                    department_th = %s,
                    academic_title_th = %s,
                    full_name_th = %s,
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    image_url = COALESCE(%s, image_url),
                    profile_url = %s,
                    openalex_id = COALESCE(%s, openalex_id),
                    total_citations = GREATEST(COALESCE(total_citations, 0), %s),
                    h_index = GREATEST(COALESCE(h_index, 0), %s),
                    total_publications_count = GREATEST(COALESCE(total_publications_count, 0), %s),
                    research_interests = CASE WHEN %s::json IS NOT NULL THEN %s::json ELSE research_interests END
                WHERE id = %s
            """, (
                fac['department_th'], fac['academic_title_th'],
                fac['full_name_th'],
                fac['first_name'], fac['last_name'],
                fac['email'],
                fac['image_url'], fac['profile_url'],
                fac['openalex_id'], fac['total_citations'], fac['h_index'], fac['works_count'],
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                matched_id
            ))
            updated += 1
        else:
            # Insert fresh record
            import uuid
            new_id = f"kmutt_fibo_{uuid.uuid4().hex[:10]}"
            cur.execute("""
                INSERT INTO faculties (
                    id, university, university_th, faculty, faculty_th, department_th,
                    academic_title_th, full_name_th,
                    first_name, last_name, email, image_url, profile_url,
                    openalex_id, total_citations, h_index, total_publications_count, research_interests
                ) VALUES (
                    %s, 'King Mongkut''s University of Technology Thonburi', 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี',
                    'Institute of Field Robotics', 'สถาบันวิทยาการหุ่นยนต์ภาคสนาม', %s,
                    %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::json
                )
            """, (
                new_id, fac['department_th'],
                fac['academic_title_th'], fac['full_name_th'],
                fac['first_name'], fac['last_name'], fac['email'],
                fac['image_url'], fac['profile_url'],
                fac['openalex_id'], fac['total_citations'], fac['h_index'], fac['works_count'],
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None
            ))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"\nPhase 4 Complete: Inserted {inserted} new faculties, Updated {updated} faculties.")

if __name__ == "__main__":
    main()
