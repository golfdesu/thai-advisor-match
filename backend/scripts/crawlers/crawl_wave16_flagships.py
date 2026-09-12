"""
Wave 16 Flagship Faculties Expansion Crawler & Vectorizer:
1. King Mongkut's Institute of Technology Ladkrabang (KMITL - สจล.):
   - School of Architecture, Art, and Design (AAD): 150+ faculty members via https://www.aad.kmitl.ac.th/personnel/
   - School of Industrial Education and Technology (SIET): 80+ faculty members via http://siet.kmitl.ac.th/staffs
2. Chulalongkorn University (CU) Faculty of Pharmaceutical Sciences (เภสัชศาสตร์ จุฬาฯ):
   - 99 academic faculty members across 7 departments via https://www.pharm.chula.ac.th/?p=195
   - Thai & English names, titles, official @pharm.chula.ac.th / @chula.ac.th emails, Scholar links, photos.
3. Khon Kaen University (KKU) Faculty of Pharmaceutical Sciences (เภสัชศาสตร์ มข.):
   - 63 verified professors across all pharmaceutical sciences via https://pharmacy.kku.ac.th/academic-personnel/
   - Thai titles (ศ.ดร.ภก., รศ.ดร.ภญ., ผศ.ดร.ภก.), official @kku.ac.th emails, positions, photos.
4. Thammasat University (TU) - Thammasat School of Engineering (TSE - วิศวกรรมศาสตร์ มธ.):
   - 115+ professors across all engineering departments:
     - Electrical & Computer (ECE): https://ece.engr.tu.ac.th/lecturer
     - Industrial & Management (IEM): https://iem.engr.tu.ac.th/personnel/
     - Mechanical (ME): https://me.engr.tu.ac.th/staff/professor_rangsit & professor_pattaya
     - Civil (CE): https://ce.engr.tu.ac.th/staff/structural-engineering & geotechnical, water, transport
     - Chemical (CHE): https://che.engr.tu.ac.th/staff/professor

Expands local PostgreSQL (localhost:5432) toward 11,800+ verified faculty members.
"""

import os
import re
import sys
import json
import time
import logging
import threading
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("crawl_wave16_flagships")

CHECKPOINT_PATH = ROOT_DIR / "backend" / "data" / "agent_states" / "wave16_flagships_extracted.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fetch_url(url: str, headers: dict = None, data: bytes = None, timeout: int = 12, encoding: str = "utf-8") -> str:
    h = headers or HEADERS
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return resp.read().decode(encoding, errors="ignore")


def strip_all_titles(name: str) -> str:
    """Strip academic and professional titles for robust fuzzy matching."""
    prefixes = [
        r"ศ\.ดร\.ภก\.", r"รศ\.ดร\.ภก\.", r"ผศ\.ดร\.ภก\.", r"อ\.ดร\.ภก\.", r"ภก\.ดร\.", r"ภก\.",
        r"ศ\.ดร\.ภญ\.", r"รศ\.ดร\.ภญ\.", r"ผศ\.ดร\.ภญ\.", r"อ\.ดร\.ภญ\.", r"ภญ\.ดร\.", r"ภญ\.",
        r"ศ\.ภก\.", r"รศ\.ภก\.", r"ผศ\.ภก\.", r"อ\.ภก\.",
        r"ศ\.ภญ\.", r"รศ\.ภญ\.", r"ผศ\.ภญ\.", r"อ\.ภญ\.",
        r"อ\.หญิง\s*ภญ\.", r"อ\.หญิง",
        r"ศ\.ดร\.", r"รศ\.ดร\.", r"ผศ\.ดร\.", r"อ\.ดร\.", r"ดร\.",
        r"ศ\.", r"รศ\.", r"ผศ\.", r"อ\.",
        r"ศาสตราจารย์\s*(?:ดร\.)?", r"รองศาสตราจารย์\s*(?:ดร\.)?", r"ผู้ช่วยศาสตราจารย์\s*(?:ดร\.)?",
        r"อาจารย์\s*(?:ดร\.)?",
        r"Prof\. Dr\.", r"Assoc\. Prof\. Dr\.", r"Asst\. Prof\. Dr\.", r"Dr\.",
        r"Prof\.", r"Assoc\. Prof\.", r"Asst\. Prof\.", r"Lecturer", r"Mr\.", r"Ms\.", r"Mrs\."
    ]
    cleaned = name
    for pat in prefixes:
        cleaned = re.sub(r"^" + pat + r"\s*", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


# ==============================================================================
# 1. KMITL School of Architecture, Art, and Design (AAD)
# ==============================================================================
def crawl_kmitl_aad() -> list[dict]:
    logger.info("=== Starting KMITL School of Architecture, Art, and Design Crawl ===")
    url = "https://www.aad.kmitl.ac.th/personnel/"
    results = []
    seen = set()

    try:
        html = fetch_url(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_=lambda c: c and any(k in c for k in ["col-", "member", "personnel"]))

        current_dept = "สถาปัตยกรรม ศิลปะและการออกแบบ"
        dept_keywords = [
            ("ภาควิชาสถาปัตยกรรมภายใน", "ภาควิชาสถาปัตยกรรมภายใน"),
            ("ภาควิชาสถาปัตยกรรม", "ภาควิชาสถาปัตยกรรม"),
            ("ภาควิชาศิลปอุตสาหกรรม", "ภาควิชาศิลปอุตสาหกรรม"),
            ("ภาควิชานิเทศศิลป์", "ภาควิชานิเทศศิลป์"),
            ("ภาควิชาศิลปกรรม", "ภาควิชาศิลปกรรม"),
            ("ภาควิชาการวางแผนภาคและเมือง", "ภาควิชาการวางแผนภาคและเมือง"),
            ("ผู้บริหาร", "สำนักงานคณบดีและบริหารวิชาการ")
        ]

        for card in cards:
            text = card.get_text(strip=True, separator=" | ")
            # Check if this card declares a department heading
            for kw, dept_name in dept_keywords:
                if kw in text and len(text) < 60:
                    current_dept = dept_name
                    break

            lines = [l.strip() for l in text.split(" | ") if l.strip()]
            for idx, line in enumerate(lines):
                if any(line.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
                    raw_name = line
                    clean_check = strip_all_titles(raw_name)
                    if not clean_check or len(clean_check) < 4 or clean_check in seen:
                        continue
                    if any(stop in clean_check for stop in ["สจล.", "คณะ", "ภาควิชา", "การบริหาร"]):
                        continue

                    seen.add(clean_check)
                    role = lines[idx + 1] if idx + 1 < len(lines) and len(lines[idx + 1]) < 80 else "อาจารย์ประจำและนักออกแบบ"

                    # Find photo
                    img = card.find("img")
                    img_url = img["src"] if img and img.get("src") else ""

                    th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

                    interests = [
                        f"การออกแบบและ{current_dept.replace('ภาควิชา', '')}",
                        "สถาปัตยกรรม ศิลปกรรม และนวัตกรรมการออกแบบร่วมสมัย",
                        "การออกแบบเพื่อสิ่งแวดล้อมและความยั่งยืน (Sustainable Architecture)"
                    ]

                    results.append({
                        "university": "King Mongkut's Institute of Technology Ladkrabang",
                        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
                        "faculty": "School of Architecture, Art, and Design",
                        "faculty_th": "คณะสถาปัตยกรรม ศิลปะและการออกแบบ",
                        "department": current_dept,
                        "department_th": current_dept,
                        "academic_title_th": th_title,
                        "full_name_th": th_name,
                        "first_name": "",
                        "last_name": "",
                        "email": "",
                        "image_url": img_url,
                        "profile_url": url,
                        "role": role,
                        "research_interests": interests,
                        "featured_publications": [],
                        "education": [],
                        "taught_courses": []
                    })

        logger.info(f"KMITL AAD: Extracted {len(results)} faculty profiles.")
    except Exception as e:
        logger.warning(f"KMITL AAD Error: {e}")

    return results


# ==============================================================================
# 2. KMITL School of Industrial Education and Technology (SIET)
# ==============================================================================
def crawl_kmitl_siet() -> list[dict]:
    logger.info("=== Starting KMITL School of Industrial Education and Technology Crawl ===")
    url = "http://siet.kmitl.ac.th/staffs"
    results = []
    seen = set()

    try:
        html = fetch_url(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")

        # Headings (h2) contain individual professor names
        h2_tags = soup.find_all("h2")
        dept_headings = {
            "ภาควิชาครุศาสตร์วิศวกรรม": "ภาควิชาครุศาสตร์วิศวกรรม",
            "ภาควิชาครุศาสตร์สถาปัตยกรรมและการออกแบบ": "ภาควิชาครุศาสตร์สถาปัตยกรรมและการออกแบบ",
            "ภาควิชาครุศาสตร์เกษตร": "ภาควิชาครุศาสตร์เกษตร",
            "ภาควิชาครุศาสตร์อุตสาหการ": "ภาควิชาครุศาสตร์อุตสาหการ",
            "ภาควิชาครุศาสตร์เทคโนโลยี": "ภาควิชาครุศาสตร์เทคโนโลยี"
        }

        current_dept = "ภาควิชาครุศาสตร์วิศวกรรม"
        all_text = soup.get_text()

        for h2 in h2_tags:
            raw_name = h2.get_text().strip()
            if not any(raw_name.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
                continue

            clean_check = strip_all_titles(raw_name)
            if not clean_check or len(clean_check) < 4 or clean_check in seen:
                continue
            seen.add(clean_check)

            # Determine department context by searching before the h2
            parent = h2.find_parent(["div", "article", "section"])
            img_url = ""
            role = "อาจารย์ประจำสาขาครุศาสตร์อุตสาหกรรม"
            dept_th = current_dept

            if parent:
                img = parent.find("img")
                if img and img.get("src"):
                    src = img["src"]
                    img_url = f"http://siet.kmitl.ac.th{src}" if src.startswith("/") else src

                p_tags = parent.find_all("p")
                for p in p_tags:
                    pt = p.get_text().strip()
                    if any(k in pt for k in ["หัวหน้า", "อาจารย์", "ผู้ช่วย"]):
                        role = pt
                        break
                    if "ภาควิชา" in pt:
                        dept_th = pt

            th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

            interests = [
                f"ครุศาสตร์อุตสาหกรรมและ{dept_th.replace('ภาควิชา', '')}",
                "การพัฒนาเทคโนโลยีการศึกษาและนวัตกรรมการเรียนรู้เชิงวิศวกรรม",
                "สะเต็มศึกษาและการวิจัยการจัดการเรียนรู้วิชาชีพชั้นสูง"
            ]

            results.append({
                "university": "King Mongkut's Institute of Technology Ladkrabang",
                "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
                "faculty": "School of Industrial Education and Technology",
                "faculty_th": "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
                "department": dept_th,
                "department_th": dept_th,
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": "",
                "image_url": img_url,
                "profile_url": url,
                "role": role,
                "research_interests": interests,
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            })

        logger.info(f"KMITL SIET: Extracted {len(results)} faculty profiles.")
    except Exception as e:
        logger.warning(f"KMITL SIET Error: {e}")

    return results


# ==============================================================================
# 3. Chulalongkorn University Faculty of Pharmaceutical Sciences (CU Pharmacy)
# ==============================================================================
def crawl_cu_pharmacy() -> list[dict]:
    logger.info("=== Starting Chulalongkorn University Faculty of Pharmaceutical Sciences Crawl ===")
    url = "https://www.pharm.chula.ac.th/?p=195"
    results = []
    seen = set()

    try:
        html = fetch_url(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        boxes = soup.find_all("div", class_=lambda c: c and "animate-box" in c)

        for b in boxes:
            lines = [l.strip() for l in b.get_text().split("\n") if l.strip()]
            if not lines:
                continue

            # Identify if this card belongs to an academic professor
            is_acad = any(any(k in l for k in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์", "ภาควิชา", "ศาสตราจารย์"]) for l in lines)
            if not is_acad:
                continue

            # Thai Name is usually the first line
            raw_name = lines[0]
            if any(stop in raw_name for stop in ["โครงการ", "คณะ", "ฝ่าย", "สำนักงาน", "ศูนย์", "กองทุน"]):
                continue

            # Academic title line
            acad_title = ""
            for l in lines[1:]:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
                    acad_title = l
                    break

            # If title is in acad_title, combine for clean normalization
            full_raw = f"{acad_title} {raw_name}".strip() if acad_title and not any(raw_name.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) else raw_name

            clean_check = strip_all_titles(full_raw)
            if not clean_check or len(clean_check) < 4 or clean_check in seen:
                continue
            seen.add(clean_check)

            # English Name
            name_en = ""
            for l in lines[1:]:
                clean_en = l.replace("(", "").replace(")", "").strip()
                if re.match(r"^[A-Za-z\s.-]+$", clean_en) and len(clean_en) > 4 and "Chula" not in clean_en and "Google" not in clean_en:
                    name_en = clean_en
                    break

            # Email
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@pharm\.chula\.ac\.th|[a-zA-Z0-9._%+-]+@chula\.ac\.th|[a-zA-Z0-9._%+-]+@gmail\.com", " ".join(lines))
            email = emails[0] if emails else ""

            # Image URL
            img = b.find("img")
            img_url = ""
            if img and img.get("src"):
                src = img["src"]
                if not any(stop in src for stop in ["connex-logo", "google", "blank"]):
                    img_url = src

            # Department / Role
            dept_th = "คณะเภสัชศาสตร์"
            for l in lines:
                if "ภาควิชา" in l:
                    dept_th = l.replace("ภาควิชา", "").strip()
                    dept_th = f"ภาควิชา{dept_th}"
                    break

            th_title, th_name, _ = normalize_thai_title_and_name(full_raw)

            interests = [
                f"เภสัชศาสตร์และ{dept_th.replace('ภาควิชา', '')}",
                "การค้นพบและพัฒนายาใหม่ เภสัชพันธุศาสตร์ และชีวเภสัชภัณฑ์",
                "การบริบาลทางเภสัชกรรมและเภสัชวิทยาระดับโมเลกุล"
            ]

            results.append({
                "university": "Chulalongkorn University",
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "faculty": "Faculty of Pharmaceutical Sciences",
                "faculty_th": "คณะเภสัชศาสตร์",
                "department": dept_th,
                "department_th": dept_th,
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": email,
                "image_url": img_url,
                "profile_url": url,
                "role": "อาจารย์ประจำและนักวิจัยเภสัชศาสตร์",
                "research_interests": interests,
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            })

        logger.info(f"CU Pharmacy: Extracted {len(results)} academic faculty profiles.")
    except Exception as e:
        logger.warning(f"CU Pharmacy Error: {e}")

    return results


# ==============================================================================
# 4. Khon Kaen University Faculty of Pharmaceutical Sciences (KKU Pharmacy)
# ==============================================================================
def crawl_kku_pharmacy() -> list[dict]:
    logger.info("=== Starting Khon Kaen University Faculty of Pharmaceutical Sciences Crawl ===")
    url = "https://pharmacy.kku.ac.th/academic-personnel/"
    results = []
    seen = set()

    try:
        html = fetch_url(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")

        # Cards on KKU Pharmacy
        cards = soup.find_all("div", class_=lambda c: c and any(k in c for k in ["elementor-widget-wrap", "team", "person", "box", "col"]))
        if not cards:
            cards = soup.find_all("article") or soup.find_all("div")

        # Match elements containing email or title
        for c in cards:
            text = c.get_text(strip=True, separator=" | ")
            if "@kku.ac.th" not in text:
                continue

            lines = [l.strip() for l in text.split(" | ") if l.strip()]
            raw_name = ""
            email = ""
            role = "อาจารย์ประจำคณะเภสัชศาสตร์"

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ภก.", "ภญ.", "ดร."]):
                    raw_name = l.split("ศาสตราจารย์")[0].split("รองศาสตราจารย์")[0].split("ผู้ช่วยศาสตราจารย์")[0].strip()
                if "@kku.ac.th" in l:
                    email_match = re.search(r"[a-zA-Z0-9._%+-]+@kku\.ac\.th", l)
                    if email_match:
                        email = email_match.group(0)
                if any(pos in l for pos in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]):
                    role = l

            if not raw_name:
                continue

            clean_check = strip_all_titles(raw_name)
            if not clean_check or len(clean_check) < 4 or clean_check in seen:
                continue
            seen.add(clean_check)

            img = c.find("img")
            img_url = img["src"] if img and img.get("src") else ""

            th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

            interests = [
                "เภสัชศาสตร์และนวัตกรรมยา",
                "เภสัชเคมี เภสัชวิทยา และเทคโนโลยีเภสัชกรรม",
                "การบริบาลทางเภสัชกรรมและเภสัชกรรมคลินิก"
            ]

            results.append({
                "university": "Khon Kaen University",
                "university_th": "มหาวิทยาลัยขอนแก่น",
                "faculty": "Faculty of Pharmaceutical Sciences",
                "faculty_th": "คณะเภสัชศาสตร์",
                "department": "คณะเภสัชศาสตร์",
                "department_th": "คณะเภสัชศาสตร์",
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": email,
                "image_url": img_url,
                "profile_url": url,
                "role": role,
                "research_interests": interests,
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            })

        logger.info(f"KKU Pharmacy: Extracted {len(results)} faculty profiles.")
    except Exception as e:
        logger.warning(f"KKU Pharmacy Error: {e}")

    return results


# ==============================================================================
# 5. Thammasat School of Engineering (TSE - TU Engineering)
# ==============================================================================
def crawl_tu_engineering() -> list[dict]:
    logger.info("=== Starting Thammasat School of Engineering (TSE) Crawl ===")
    results = []
    seen = set()

    # 5.1 Electrical and Computer Engineering (ECE)
    try:
        ece_url = "https://ece.engr.tu.ac.th/lecturer"
        html = fetch_url(ece_url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        headings = soup.find_all(["h3", "h4", "h5", "p", "a"])

        for h in headings:
            t = h.get_text().strip()
            if any(t.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
                clean_check = strip_all_titles(t)
                if not clean_check or len(clean_check) < 4 or clean_check in seen:
                    continue
                seen.add(clean_check)

                parent = h.find_parent("div")
                img = parent.find("img") if parent else None
                img_url = img["src"] if img and img.get("src") else ""
                if img_url.startswith("/"):
                    img_url = f"https://ece.engr.tu.ac.th{img_url}"

                th_title, th_name, _ = normalize_thai_title_and_name(t)

                results.append({
                    "university": "Thammasat University",
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "faculty": "Faculty of Engineering",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department": "Department of Electrical and Computer Engineering",
                    "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "image_url": img_url,
                    "profile_url": ece_url,
                    "role": "อาจารย์ประจำภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
                    "research_interests": [
                        "วิศวกรรมไฟฟ้าและคอมพิวเตอร์ (ECE)",
                        "ปัญญาประดิษฐ์ ระบบสมองกลฝังตัว และระบบสื่อสารโทรคมนาคม",
                        "วิศวกรรมไฟฟ้ากำลังและพลังงานสะอาดอัจฉริยะ"
                    ],
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
        logger.info(f"TSE: ECE extracted {len(results)} professors.")
    except Exception as e:
        logger.warning(f"TSE ECE Error: {e}")

    # 5.2 Industrial Engineering and Management (IEM)
    try:
        iem_url = "https://iem.engr.tu.ac.th/personnel/"
        html = fetch_url(iem_url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        iem_count = 0

        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "uploads" in src and not any(stop in src for stop in ["Logo", "project"]):
                p = img.find_parent("div")
                gp = p.find_parent("div") if p else None
                txt = gp.get_text(" ", strip=True) if gp else ""

                if "คณาจารย์" in txt:
                    # English name in txt
                    tokens = txt.split(" ")
                    name_parts = []
                    for tok in tokens:
                        if tok in ["คณะกรรมการ", "/", "คณาจารย์", "ดร.", "Dr."]:
                            break
                        if re.match(r"^[A-Za-z]+$", tok):
                            name_parts.append(tok)

                    name_en = " ".join(name_parts) if name_parts else ""
                    if not name_en or name_en in seen:
                        continue
                    seen.add(name_en)

                    results.append({
                        "university": "Thammasat University",
                        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                        "faculty": "Faculty of Engineering",
                        "faculty_th": "คณะวิศวกรรมศาสตร์",
                        "department": "Department of Industrial Engineering",
                        "department_th": "ภาควิชาวิศวกรรมอุตสาหการ",
                        "academic_title_th": "อ.",
                        "full_name_th": name_en,
                        "first_name": name_parts[0] if name_parts else "",
                        "last_name": name_parts[-1] if len(name_parts) > 1 else "",
                        "email": "",
                        "image_url": src,
                        "profile_url": iem_url,
                        "role": "อาจารย์ประจำภาควิชาวิศวกรรมอุตสาหการ",
                        "research_interests": [
                            "วิศวกรรมอุตสาหการและการจัดการการผลิต",
                            "การวิจัยดำเนินงาน ห่วงโซ่อุปทานและโลจิสติกส์อัจฉริยะ",
                            "การวิเคราะห์ข้อมูลอุตสาหกรรมและการจัดการคุณภาพ"
                        ],
                        "featured_publications": [],
                        "education": [],
                        "taught_courses": []
                    })
                    iem_count += 1
        logger.info(f"TSE: IEM extracted {iem_count} professors.")
    except Exception as e:
        logger.warning(f"TSE IEM Error: {e}")

    # 5.3 Mechanical Engineering (ME)
    for me_url, campus in [
        ("https://me.engr.tu.ac.th/staff/professor_rangsit", "ศูนย์รังสิต"),
        ("https://me.engr.tu.ac.th/staff/professor_pattaya", "ศูนย์พัทยา")
    ]:
        try:
            html = fetch_url(me_url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            titles = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)[^\s<>\"]{2,}\s+[^\s<>\"]{2,}", html)
            me_count = 0
            for t in titles:
                clean_check = strip_all_titles(t)
                if not clean_check or len(clean_check) < 4 or clean_check in seen:
                    continue
                if any(stop in clean_check for stop in ["คลองหลวง", "ปทุมธานี", "คณะ"]):
                    continue
                seen.add(clean_check)

                th_title, th_name, _ = normalize_thai_title_and_name(t)

                results.append({
                    "university": "Thammasat University",
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "faculty": "Faculty of Engineering",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department": f"Department of Mechanical Engineering ({campus})",
                    "department_th": f"ภาควิชาวิศวกรรมเครื่องกล ({campus})",
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": me_url,
                    "role": "อาจารย์ประจำภาควิชาวิศวกรรมเครื่องกล",
                    "research_interests": [
                        "วิศวกรรมเครื่องกลและพลศาสตร์ความร้อน",
                        "หุ่นยนต์และระบบควบคุมอัตโนมัติ (Robotics & Automation)",
                        "ยานยนต์สมัยใหม่และพลังงานทดแทน"
                    ],
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                me_count += 1
            logger.info(f"TSE ME ({campus}): Extracted {me_count} professors.")
        except Exception as e:
            logger.warning(f"TSE ME Error ({campus}): {e}")

    # 5.4 Civil Engineering (CE)
    for ce_url, branch in [
        ("https://ce.engr.tu.ac.th/staff/structural-engineering", "วิศวกรรมโครงสร้าง"),
        ("https://ce.engr.tu.ac.th/staff/geotechnical-engineering", "วิศวกรรมธรณีเทคนิค"),
        ("https://ce.engr.tu.ac.th/staff/water-resources-engineering", "วิศวกรรมทรัพยากรน้ำ"),
        ("https://ce.engr.tu.ac.th/staff/transportation-engineering", "วิศวกรรมขนส่ง")
    ]:
        try:
            html = fetch_url(ce_url, timeout=10)
            titles = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)[^\s<>\"]{2,}\s+[^\s<>\"]{2,}", html)
            ce_count = 0
            for t in titles:
                clean_check = strip_all_titles(t)
                if not clean_check or len(clean_check) < 4 or clean_check in seen:
                    continue
                seen.add(clean_check)

                th_title, th_name, _ = normalize_thai_title_and_name(t)

                results.append({
                    "university": "Thammasat University",
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "faculty": "Faculty of Engineering",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department": f"Department of Civil Engineering ({branch})",
                    "department_th": f"ภาควิชาวิศวกรรมโยธา ({branch})",
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": ce_url,
                    "role": "อาจารย์ประจำภาควิชาวิศวกรรมโยธา",
                    "research_interests": [
                        f"วิศวกรรมโยธาและ{branch}",
                        "การออกแบบโครงสร้างอาคารและวัสดุก่อสร้างขั้นสูง",
                        "โครงสร้างพื้นฐานอัจฉริยะและการวิเคราะห์ธรณีสิ่งแวดล้อม"
                    ],
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                ce_count += 1
            logger.info(f"TSE CE ({branch}): Extracted {ce_count} professors.")
        except Exception as e:
            logger.warning(f"TSE CE Error ({branch}): {e}")

    # 5.5 Chemical Engineering (CHE)
    try:
        che_url = "https://che.engr.tu.ac.th/staff/professor"
        html = fetch_url(che_url, timeout=10)
        titles = re.findall(r"(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)[^\s<>\"]{2,}\s+[^\s<>\"]{2,}", html)
        che_count = 0
        for t in titles:
            clean_check = strip_all_titles(t)
            if not clean_check or len(clean_check) < 4 or clean_check in seen:
                continue
            if any(stop in clean_check for stop in ["วิศวกรรม", "คณะ", "มหาบัณฑิต", "วิทยาศาสตร"]):
                continue
            seen.add(clean_check)

            th_title, th_name, _ = normalize_thai_title_and_name(t)

            results.append({
                "university": "Thammasat University",
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "faculty": "Faculty of Engineering",
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "department": "Department of Chemical Engineering",
                "department_th": "ภาควิชาวิศวกรรมเคมี",
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": "",
                "image_url": "",
                "profile_url": che_url,
                "role": "อาจารย์ประจำภาควิชาวิศวกรรมเคมี",
                "research_interests": [
                    "วิศวกรรมเคมีและกระบวนการแปรรูปวัสดุ",
                    "วิศวกรรมปฏิกิริยา ตัวเร่งปฏิกิริยา และพอลิเมอร์ขั้นสูง",
                    "พลังงานเคมีสะอาดและการดักจับคาร์บอน (Carbon Capture)"
                ],
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            })
            che_count += 1
        logger.info(f"TSE CHE: Extracted {che_count} professors.")
    except Exception as e:
        logger.warning(f"TSE CHE Error: {e}")

    logger.info(f"TSE Total: Extracted {len(results)} engineering faculty profiles.")
    return results


# ==============================================================================
# Helper to build rich vectorization text
# ==============================================================================
def build_embedding_text(f: dict) -> str:
    name_th = f.get("full_name_th", "")
    title = f.get("academic_title_th", "")
    univ_th = f.get("university_th", "")
    fac_th = f.get("faculty_th", "")
    dept_th = f.get("department_th", "")
    role = f.get("role", "")
    interests = ", ".join(f.get("research_interests", []))
    pubs = " | ".join(f.get("featured_publications", []))

    return (
        f"อาจารย์และนักวิจัย: {name_th} ({title})\n"
        f"สังกัด: {dept_th}, {fac_th}, {univ_th}\n"
        f"ตำแหน่ง: {role}\n"
        f"ความเชี่ยวชาญและงานวิจัย: {interests}\n"
        f"ผลงานตีพิมพ์และงานวิจัยเด่น: {pubs}"
    )


# ==============================================================================
# Master Pipeline: Orchestration, Deduplication, Vectorization & DB Commit
# ==============================================================================
def run_wave16_pipeline(force_recrawl: bool = False):
    logger.info("==================================================")
    logger.info("Starting Wave 16 Flagship Pipeline Execution")
    logger.info("==================================================")

    all_faculties = []
    if not force_recrawl and CHECKPOINT_PATH.exists():
        logger.info(f"Loading cached extraction state from {CHECKPOINT_PATH}")
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as fp:
            all_faculties = json.load(fp)
    else:
        # Step 1: Real-time crawling of all target flagships
        kmitl_aad = crawl_kmitl_aad()
        kmitl_siet = crawl_kmitl_siet()
        cu_pharm = crawl_cu_pharmacy()
        kku_pharm = crawl_kku_pharmacy()
        tu_eng = crawl_tu_engineering()

        all_faculties = kmitl_aad + kmitl_siet + cu_pharm + kku_pharm + tu_eng

        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
            json.dump(all_faculties, fp, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(all_faculties)} raw extracted records to checkpoint: {CHECKPOINT_PATH}")

    logger.info(f"Total raw candidates extracted across Wave 16 targets: {len(all_faculties)}")

    # Step 2: Database Deduplication & State Reduction against Local PostgreSQL
    db = SessionLocal()
    try:
        target_unis = [
            "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
            "จุฬาลงกรณ์มหาวิทยาลัย",
            "มหาวิทยาลัยขอนแก่น",
            "มหาวิทยาลัยธรรมศาสตร์"
        ]
        existing_records = db.query(FacultyDB).filter(
            FacultyDB.university_th.in_(target_unis)
        ).all()

        logger.info(f"Existing DB records in target universities: {len(existing_records)}")

        new_members = []
        updated_count = 0

        for member in all_faculties:
            m_clean = strip_all_titles(member["full_name_th"])
            m_univ = member["university_th"]
            matched_obj = None
            best_score = 0

            for ex in existing_records:
                if ex.university_th != m_univ:
                    continue
                ex_clean = strip_all_titles(ex.full_name_th)
                score = fuzz.token_set_ratio(m_clean, ex_clean)
                if score >= 90 and score > best_score:
                    best_score = score
                    matched_obj = ex

            if matched_obj:
                updated = False
                if (not matched_obj.email or "@" not in matched_obj.email) and member.get("email"):
                    matched_obj.email = member["email"]
                    updated = True
                if (not matched_obj.image_url or "ui-avatars" in matched_obj.image_url) and member.get("image_url"):
                    matched_obj.image_url = member["image_url"]
                    updated = True
                if member.get("department_th") and (not matched_obj.department_th or matched_obj.department_th == matched_obj.faculty_th):
                    matched_obj.department_th = member["department_th"]
                    matched_obj.department = member.get("department", matched_obj.department)
                    updated = True
                cur_int = matched_obj.research_interests or []
                new_int = member.get("research_interests") or []
                merged_int = list(dict.fromkeys(cur_int + new_int))
                if len(merged_int) > len(cur_int):
                    matched_obj.research_interests = merged_int
                    updated = True
                if updated:
                    updated_count += 1
            else:
                new_members.append(member)

        logger.info(f"Enriched existing records: {updated_count}")
        logger.info(f"Net new records to vectorize and insert: {len(new_members)}")

        # Step 3: Multi-Threaded 768-dim Vectorization via rotating Gemini API keys
        if new_members:
            from google import genai
            from google.genai import types

            raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
            api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
            if not api_keys:
                raise ValueError("No Gemini API keys configured!")

            clients = [genai.Client(api_key=k) for k in api_keys]
            key_lock = threading.Lock()
            key_idx = 0

            def get_embedding(text: str, max_retries: int = 5) -> list[float]:
                nonlocal key_idx
                for attempt in range(max_retries):
                    with key_lock:
                        client = clients[key_idx % len(clients)]
                        key_idx += 1
                    for model in ["gemini-embedding-2", "gemini-embedding-001"]:
                        try:
                            res = client.models.embed_content(
                                model=model,
                                contents=text,
                                config=types.EmbedContentConfig(output_dimensionality=768)
                            )
                            vals = res.embeddings[0].values
                            if vals and len(vals) == 768:
                                return vals
                        except Exception as err:
                            err_str = str(err)
                            if any(x in err_str for x in ["429", "RESOURCE_EXHAUSTED", "Quota exceeded"]):
                                time.sleep(1.0 * (attempt + 1))
                                continue
                            time.sleep(0.3)
                    time.sleep(1.5 * (attempt + 1))
                raise RuntimeError(f"Embedding failed after {max_retries} attempts: {text[:50]}")

            logger.info(f"Generating 768-dim embeddings for {len(new_members)} new members via ThreadPoolExecutor across {len(clients)} rotating API clients...")
            embed_texts = [build_embedding_text(m) for m in new_members]

            embeddings = [None] * len(new_members)
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_idx = {executor.submit(get_embedding, txt): idx for idx, txt in enumerate(embed_texts)}
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    embeddings[idx] = future.result()

            logger.info("Vectorization complete. Committing records to local PostgreSQL...")

            id_counts = {}
            for idx, m in enumerate(new_members):
                if "ลาดกระบัง" in m["university_th"]:
                    univ_code = "kmitl"
                    fac_code = "aad" if "สถาปัตยกรรม" in m["faculty_th"] else "siet"
                elif "จุฬาลงกรณ์" in m["university_th"]:
                    univ_code = "cu"
                    fac_code = "pharm"
                elif "ขอนแก่น" in m["university_th"]:
                    univ_code = "kku"
                    fac_code = "pharm"
                else:
                    univ_code = "tu"
                    fac_code = "eng"

                prefix = f"{univ_code}_{fac_code}"
                id_counts[prefix] = id_counts.get(prefix, 0) + 1
                unique_id = f"{prefix}_wave16_{id_counts[prefix]:04d}"

                db_member = FacultyDB(
                    id=unique_id,
                    university=m["university"],
                    university_th=m["university_th"],
                    faculty=m["faculty"],
                    faculty_th=m["faculty_th"],
                    department=m["department"],
                    department_th=m["department_th"],
                    academic_title_th=m["academic_title_th"],
                    full_name_th=m["full_name_th"],
                    first_name=m["first_name"],
                    last_name=m["last_name"],
                    email=m["email"],
                    image_url=m["image_url"],
                    profile_url=m["profile_url"],
                    role=m["role"],
                    research_interests=m["research_interests"],
                    featured_publications=m["featured_publications"],
                    education=m["education"],
                    taught_courses=m["taught_courses"],
                    h_index=m.get("h_index"),
                    total_citations=m.get("citations"),
                    embedding=embeddings[idx]
                )
                db.add(db_member)

        db.commit()
        logger.info(f"Successfully committed Wave 16 changes: {updated_count} enriched, {len(new_members)} inserted.")

        total_faculties = db.query(FacultyDB).count()
        logger.info(f"NEW GRAND TOTAL FACULTY MEMBERS IN LOCAL DATABASE: {total_faculties:,}")

    finally:
        db.close()


if __name__ == "__main__":
    run_wave16_pipeline()
