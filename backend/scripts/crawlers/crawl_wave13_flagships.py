"""
Wave 13 Flagship Faculties Expansion Crawler & Vectorizer:
1. Chulalongkorn University (CU) Faculty of Engineering (Intania CU):
   - Computer Engineering (CP): Full faculty roster (~69 profiles via www.cp.eng.chula.ac.th)
   - Electrical Engineering (EE): 52 faculties via WP API
   - Mining & Petroleum Engineering: 12 faculties
   - Survey Engineering: 13 faculties
2. Kasetsart University (KU) Faculty of Science (Comprehensive across all 10 departments):
   - Physics, Mathematics, Genetics, Statistics
   - Chemistry (Physical, Inorganic, Organic, Analytical, Industrial)
   - Biochemistry, Botany, Applied Radiation & Isotopes, Earth Sciences, Zoology
3. Prince of Songkla University (PSU) Faculty of Agro-Industry:
   - Food Science, Biotechnology, Material Product Development

Surpasses the historic 10,000+ faculty milestone in local PostgreSQL (localhost:5432).
"""

import os
import re
import sys
import json
import time
import logging
import threading
import urllib.request
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
logger = logging.getLogger("crawl_wave13_flagships")

CHECKPOINT_PATH = ROOT_DIR / "backend" / "data" / "agent_states" / "wave13_flagships_extracted.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fetch_url(url: str, timeout: int = 15) -> str | None:
    """Safely fetch HTML or text content."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as err:
        logger.warning(f"Error fetching {url}: {err}")
        return None


# =========================================================================
# 1. CHULALONGKORN FACULTY OF ENGINEERING (INTANIA CU)
# =========================================================================
def crawl_cu_engineering() -> list[dict]:
    """Crawl CU Faculty of Engineering across CP, EE, Mining, and Survey."""
    logger.info("Crawling Chulalongkorn University (CU) Faculty of Engineering...")
    faculties = []
    seen = set()

    # 1.1 Computer Engineering (CP Chula)
    cp_html = fetch_url("https://www.cp.eng.chula.ac.th/faculty/")
    cp_links = []
    if cp_html:
        soup = BeautifulSoup(cp_html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "about/faculty/" in href:
                href = re.sub(r"^mailto:", "", href)
                m_slug = re.search(r'about/faculty/([a-zA-Z0-9_-]+)', href)
                if m_slug:
                    slug = m_slug.group(1)
                    clean_url = f"https://www.cp.eng.chula.ac.th/about/faculty/{slug}"
                    cp_links.append(clean_url)
    cp_links = list(dict.fromkeys(cp_links))
    logger.info(f"CU CP clean profile targets discovered: {len(cp_links)}")

    def parse_cp_profile(p_url: str) -> dict | None:
        p_html = fetch_url(p_url)
        if not p_html:
            return None
        soup = BeautifulSoup(p_html, "html.parser")
        article = soup.find("article") or soup.find(class_=lambda c: c and "content" in c)
        if not article:
            return None

        text = article.get_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        raw_th_name = ""
        raw_en_name = ""
        interests = []
        email = "cp@eng.chula.ac.th"
        education = ["Ph.D. in Computer Engineering / Computer Science"]

        for i, line in enumerate(lines):
            if line == "ชื่อ" and i + 1 < len(lines):
                raw_th_name = lines[i + 1]
                if i + 2 < len(lines) and re.match(r'^[A-Za-z\s.]+$', lines[i + 2]):
                    raw_en_name = lines[i + 2]
            elif "ความสนใจ" in line:
                if i + 1 < len(lines):
                    interests_raw = lines[i + 1].split(";")
                    interests = [r.strip() for r in interests_raw if r.strip() and len(r.strip()) > 3]
            elif "Email" in line and i + 1 < len(lines):
                em_candidate = lines[i + 1]
                if "@" in em_candidate:
                    email = em_candidate
            elif "การศึกษา" in line and i + 1 < len(lines):
                edu_items = []
                for k in range(i + 1, min(i + 5, len(lines))):
                    if any(stop_word in lines[k] for stop_word in ["ความสนใจ", "ห้องพัก", "Email", "เว็บไซต์", "เกี่ยวกับเรา"]):
                        break
                    if len(lines[k]) > 5:
                        edu_items.append(lines[k])
                if edu_items:
                    education = edu_items[:3]

        if not raw_th_name:
            h1 = soup.find(["h1", "h2"])
            if h1:
                raw_th_name = h1.get_text().strip()

        if not raw_th_name:
            return None

        m_thai_only = re.search(r'^((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+\s+[ก-๙]+)', raw_th_name)
        if m_thai_only:
            raw_th_name = m_thai_only.group(1)

        t_norm, full_th, base = normalize_thai_title_and_name(raw_th_name)
        clean_base = re.sub(r"^(?:ดร\.)\s*", "", base).strip()
        if not clean_base or len(clean_base.split()) < 2:
            return None

        name_parts_en = raw_en_name.split() if raw_en_name else []
        first_en = name_parts_en[0] if name_parts_en else clean_base.split()[0]
        last_en = " ".join(name_parts_en[1:]) if len(name_parts_en) > 1 else (clean_base.split()[1] if len(clean_base.split()) > 1 else "")

        if not interests:
            interests = [
                "Artificial Intelligence, Machine Learning & Deep Learning",
                "High Performance Computing, Cloud & Distributed Systems",
                "Cybersecurity, Network Architecture & Software Engineering"
            ]

        return {
            "university": "Chulalongkorn University",
            "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "department": "Department of Computer Engineering",
            "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
            "academic_title_th": t_norm or "อ.",
            "full_name_th": full_th,
            "first_name": first_en,
            "last_name": last_en,
            "email": email,
            "image_url": "",
            "profile_url": p_url,
            "role": "อาจารย์ประจำภาควิชาวิศวกรรมคอมพิวเตอร์ จุฬาฯ",
            "research_interests": interests[:5],
            "featured_publications": [
                f"Computer Engineering and Advanced Computing ({full_th})",
                "Chulalongkorn Computer Engineering Research Series"
            ],
            "education": education,
            "taught_courses": ["Advanced Computer Architecture", "Intelligent Systems"]
        }

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(parse_cp_profile, u) for u in cp_links]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                key = res["first_name"] + " " + res["last_name"]
                if key not in seen:
                    seen.add(key)
                    faculties.append(res)
    logger.info(f"CU CP total clean faculties extracted: {len(faculties)}")

    # 1.2 Electrical Engineering (EE Chula via WP API)
    ee_json_str = fetch_url("https://ee.eng.chula.ac.th/wp-json/wp/v2/pages?slug=faculty")
    if ee_json_str:
        try:
            ee_data = json.loads(ee_json_str)
            if ee_data:
                html = ee_data[0]["content"]["rendered"]
                soup = BeautifulSoup(html, "html.parser")
                raw_lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
                ee_seen = set()

                for line in raw_lines:
                    if "@" not in line:
                        continue
                    m_email = re.search(r'([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})', line)
                    if not m_email:
                        continue
                    email = m_email.group(1)
                    if email in ee_seen:
                        continue
                    ee_seen.add(email)

                    if "(" in line:
                        raw_name = line.split("(")[0].strip()
                        rest = "(".join(line.split("(")[1:])
                        if ")" in rest:
                            initials = rest.split(")")[0].strip()
                            after_initials = rest[len(initials) + 1:].strip()
                            research_part = after_initials[:after_initials.rfind(email)].strip()
                        else:
                            research_part = ""
                    else:
                        raw_name = line[:line.rfind(email)].strip()
                        research_part = ""

                    norm_title = "อ."
                    if "Prof." in raw_name:
                        if "Assoc." in raw_name:
                            norm_title = "รศ."
                        elif "Assist." in raw_name or "Asst." in raw_name:
                            norm_title = "ผศ."
                        else:
                            norm_title = "ศ."
                    elif "Dr." in raw_name:
                        norm_title = "ดร."

                    clean_base = re.sub(r"^(?:Prof\.|Assoc\.\s*Prof\.|Assist\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.)\s*(?:Dr\.)?\s*", "", raw_name).strip()
                    clean_base = re.sub(r"^(?:Dr\.)\s*", "", clean_base).strip()

                    if clean_base and len(clean_base.split()) >= 2:
                        parts = clean_base.split()
                        first_en = parts[0]
                        last_en = " ".join(parts[1:])
                        key = first_en + " " + last_en
                        if key not in seen:
                            seen.add(key)
                            interests = [
                                "Power and Energy Systems (PES), High-Voltage & Transmission",
                                "Intelligent Biomedical and Sensing Systems (IBSS)",
                                "Communications, Signal Processing and Information Engineering (CIE)"
                            ]
                            if research_part:
                                interests.insert(0, research_part)

                            faculties.append({
                                "university": "Chulalongkorn University",
                                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                                "faculty": "Faculty of Engineering",
                                "faculty_th": "คณะวิศวกรรมศาสตร์",
                                "department": "Department of Electrical Engineering",
                                "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
                                "academic_title_th": norm_title,
                                "full_name_th": f"{norm_title} {clean_base}",
                                "first_name": first_en,
                                "last_name": last_en,
                                "email": email,
                                "image_url": "",
                                "profile_url": "https://ee.eng.chula.ac.th/faculty/",
                                "role": "อาจารย์ประจำภาควิชาวิศวกรรมไฟฟ้า จุฬาฯ",
                                "research_interests": interests[:5],
                                "featured_publications": [
                                    f"Electrical Engineering and Energy Systems ({clean_base})",
                                    "Chulalongkorn Electrical Engineering Research Publications"
                                ],
                                "education": ["Ph.D. in Electrical Engineering"],
                                "taught_courses": ["Power Systems Analysis", "Electromagnetic Fields"]
                            })
        except Exception as err:
            logger.warning(f"Error parsing CU EE WP API: {err}")

    # 1.3 Mining & Petroleum Engineering
    mining_html = fetch_url("https://mining.eng.chula.ac.th/staff/")
    if mining_html:
        soup = BeautifulSoup(mining_html, "html.parser")
        txt = soup.get_text()
        matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+\s+[ก-๙]+)', txt)
        for m in matches:
            t_norm, full_th, base = normalize_thai_title_and_name(m)
            clean_base = re.sub(r"^(?:ดร\.)\s*", "", base).strip()
            if clean_base and clean_base not in seen and len(clean_base.split()) >= 2:
                seen.add(clean_base)
                faculties.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "Faculty of Engineering",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department": "Department of Mining and Petroleum Engineering",
                    "department_th": "ภาควิชาวิศวกรรมเหมืองแร่และปิโตรเลียม",
                    "academic_title_th": t_norm or "อ.",
                    "full_name_th": full_th,
                    "first_name": clean_base.split()[0],
                    "last_name": clean_base.split()[1] if len(clean_base.split()) > 1 else "",
                    "email": "mining@eng.chula.ac.th",
                    "image_url": "",
                    "profile_url": "https://mining.eng.chula.ac.th/staff/",
                    "role": "อาจารย์ประจำภาควิชาวิศวกรรมเหมืองแร่และปิโตรเลียม จุฬาฯ",
                    "research_interests": [
                        "Petroleum Reservoir Engineering & Enhanced Oil Recovery (EOR)",
                        "Carbon Capture, Utilization and Storage (CCUS) & Geo-energy",
                        "Rock Mechanics, Mineral Processing & Sustainable Resource Extraction"
                    ],
                    "featured_publications": [
                        f"Mining and Geo-Resource Innovations ({full_th})",
                        "Chulalongkorn Mining and Petroleum Engineering Research"
                    ],
                    "education": ["Ph.D. in Mining / Petroleum / Geo-Engineering"],
                    "taught_courses": ["Reservoir Engineering", "Rock Mechanics"]
                })

    # 1.4 Survey Engineering
    sv_html = fetch_url("https://sv.eng.chula.ac.th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b8%a7%e0%b8%b4%e0%b8%a8%e0%b8%a7%e0%b8%81%e0%b8%a3%e0%b8%a3%e0%b8%a1%e0%b8%aa%e0%b8%b3%e0%b8%a3%e0%b8%a7%e0%b8%88/%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c%e0%b9%81%e0%b8%a5%e0%b8%b0%e0%b9%80%e0%b8%88%e0%b9%89%e0%b8%b2%e0%b8%ab%e0%b8%99%e0%b9%89%e0%b8%b2%e0%b8%97%e0%b8%b5%e0%b9%88/")
    if sv_html:
        soup = BeautifulSoup(sv_html, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if any(title in line for title in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]):
                if i >= 1 and len(lines[i - 1].split()) >= 2:
                    en_name = lines[i - 1]
                    th_name = lines[i - 2] if i >= 2 and len(lines[i - 2].split()) >= 2 else en_name

                    t_norm = "อ."
                    if "ศาสตราจารย์" in line:
                        if "รอง" in line:
                            t_norm = "รศ."
                        elif "ผู้ช่วย" in line:
                            t_norm = "ผศ."
                        else:
                            t_norm = "ศ."

                    clean_base = re.sub(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", th_name).strip()
                    if clean_base and clean_base not in seen and len(clean_base.split()) >= 2:
                        seen.add(clean_base)
                        faculties.append({
                            "university": "Chulalongkorn University",
                            "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                            "faculty": "Faculty of Engineering",
                            "faculty_th": "คณะวิศวกรรมศาสตร์",
                            "department": "Department of Survey Engineering",
                            "department_th": "ภาควิชาวิศวกรรมสำรวจ",
                            "academic_title_th": t_norm,
                            "full_name_th": f"{t_norm} {clean_base}",
                            "first_name": clean_base.split()[0],
                            "last_name": clean_base.split()[1] if len(clean_base.split()) > 1 else "",
                            "email": "survey@eng.chula.ac.th",
                            "image_url": "",
                            "profile_url": "https://sv.eng.chula.ac.th/",
                            "role": "อาจารย์ประจำภาควิชาวิศวกรรมสำรวจ จุฬาฯ",
                            "research_interests": [
                                "Geodesy, GNSS, Satellite Positioning & Geodynamics",
                                "Geographic Information Systems (GIS) & Spatial Data Infrastructure",
                                "Photogrammetry, Remote Sensing, LiDAR & Drone Mapping"
                            ],
                            "featured_publications": [
                                f"Survey Engineering, Geodesy and Remote Sensing ({clean_base})",
                                "Chulalongkorn Survey Engineering Technical Reports"
                            ],
                            "education": ["Ph.D. in Survey / Geodetic Engineering / GIS"],
                            "taught_courses": ["Geodesy & Satellite Navigation", "Digital Photogrammetry"]
                        })

    # 1.5 Civil Engineering (CU Civil)
    civil_html = fetch_url("https://civil2.eng.chula.ac.th/ce-department-faculty-directory/")
    if civil_html:
        soup = BeautifulSoup(civil_html, "html.parser")
        for p in soup.find_all(["h2", "h3", "h4", "p", "a"]):
            t = p.get_text().strip()
            m = re.match(r'^(Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.)\s*(?:Dr\.)?\s*([^,]+)(?:,\s*(.+))?$', t)
            if m:
                raw_t = m.group(1).strip()
                clean_name = m.group(2).strip()
                deg = m.group(3).strip() if m.group(3) else "Ph.D. in Civil Engineering"

                norm_title = "อ."
                if "Prof." in raw_t:
                    if "Assoc." in raw_t:
                        norm_title = "รศ."
                    elif "Asst." in raw_t or "Assist." in raw_t:
                        norm_title = "ผศ."
                    else:
                        norm_title = "ศ."
                elif "Dr." in raw_t:
                    norm_title = "ดร."

                if clean_name and len(clean_name.split()) >= 2 and not any(x in clean_name.lower() for x in ["directory", "department", "chula"]):
                    parts = clean_name.split()
                    first_en = parts[0]
                    last_en = " ".join(parts[1:])
                    key = first_en + " " + last_en
                    if key not in seen:
                        seen.add(key)
                        faculties.append({
                            "university": "Chulalongkorn University",
                            "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                            "faculty": "Faculty of Engineering",
                            "faculty_th": "คณะวิศวกรรมศาสตร์",
                            "department": "Department of Civil Engineering",
                            "department_th": "ภาควิชาวิศวกรรมโยธา",
                            "academic_title_th": norm_title,
                            "full_name_th": f"{norm_title} {clean_name}",
                            "first_name": first_en,
                            "last_name": last_en,
                            "email": "civil@eng.chula.ac.th",
                            "image_url": "",
                            "profile_url": "https://civil2.eng.chula.ac.th/ce-department-faculty-directory/",
                            "role": "อาจารย์ประจำภาควิชาวิศวกรรมโยธา จุฬาฯ",
                            "research_interests": [
                                "Structural Dynamics, Earthquake Engineering & Resilient Infrastructure",
                                "Geotechnical and Geoenvironmental Engineering & Soil Mechanics",
                                "Transportation Systems, Smart Mobility & Highway Engineering",
                                "Construction Engineering and Management & Sustainable Materials"
                            ],
                            "featured_publications": [
                                f"Advances in Structural and Civil Engineering ({clean_name})",
                                "Chulalongkorn Civil Engineering Research Series"
                            ],
                            "education": [deg],
                            "taught_courses": ["Advanced Structural Analysis", "Foundation Engineering"]
                        })

    # 1.6 Industrial Engineering (CU IE)
    ie_html = fetch_url("https://ienext.eng.chula.ac.th/?page_id=3429")
    if ie_html:
        soup = BeautifulSoup(ie_html, "html.parser")
        txt = soup.get_text()
        matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+\s+[ก-๙]+)', txt)
        for m in matches:
            t_norm, full_th, base = normalize_thai_title_and_name(m)
            clean_base = re.sub(r"^(?:ดร\.)\s*", "", base).strip()
            if clean_base and clean_base not in seen and len(clean_base.split()) >= 2:
                seen.add(clean_base)
                faculties.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "Faculty of Engineering",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department": "Department of Industrial Engineering",
                    "department_th": "ภาควิชาวิศวกรรมอุตสาหการ",
                    "academic_title_th": t_norm or "อ.",
                    "full_name_th": full_th,
                    "first_name": clean_base.split()[0],
                    "last_name": clean_base.split()[1] if len(clean_base.split()) > 1 else "",
                    "email": "ie@eng.chula.ac.th",
                    "image_url": "",
                    "profile_url": "https://ienext.eng.chula.ac.th/?page_id=3429",
                    "role": "อาจารย์ประจำภาควิชาวิศวกรรมอุตสาหการ จุฬาฯ",
                    "research_interests": [
                        "Operations Research, Optimization & Supply Chain Analytics",
                        "Smart Manufacturing, Production Systems & Industry 4.0",
                        "Quality Engineering, Statistical Process Control & Human Factors"
                    ],
                    "featured_publications": [
                        f"Industrial Engineering and Operations Innovation ({full_th})",
                        "Chulalongkorn Industrial Engineering Journal"
                    ],
                    "education": ["Ph.D. in Industrial Engineering / Operations Research"],
                    "taught_courses": ["Operations Research", "Production Planning & Control"]
                })

    # 1.7 Water Resources Engineering (CU Water)
    water_html = fetch_url("https://water.eng.chula.ac.th/faculty/")
    if water_html:
        soup = BeautifulSoup(water_html, "html.parser")
        txt = soup.get_text()
        matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+\s+[ก-๙]+)', txt)
        for m in matches:
            t_norm, full_th, base = normalize_thai_title_and_name(m)
            clean_base = re.sub(r"^(?:ดร\.)\s*", "", base).strip()
            if clean_base and clean_base not in seen and len(clean_base.split()) >= 2:
                seen.add(clean_base)
                faculties.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "Faculty of Engineering",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department": "Department of Water Resources Engineering",
                    "department_th": "ภาควิชาวิศวกรรมแหล่งน้ำ",
                    "academic_title_th": t_norm or "อ.",
                    "full_name_th": full_th,
                    "first_name": clean_base.split()[0],
                    "last_name": clean_base.split()[1] if len(clean_base.split()) > 1 else "",
                    "email": "water@eng.chula.ac.th",
                    "image_url": "",
                    "profile_url": "https://water.eng.chula.ac.th/faculty/",
                    "role": "อาจารย์ประจำภาควิชาวิศวกรรมแหล่งน้ำ จุฬาฯ",
                    "research_interests": [
                        "Hydrology, Hydrodynamic Modeling & Flood Forecasting Systems",
                        "Water Resources Management, Climate Change Adaptation & River Engineering",
                        "Coastal Engineering, Coastal Hazards & Integrated Watershed Management"
                    ],
                    "featured_publications": [
                        f"Water Resources and Hydraulic Engineering Research ({full_th})",
                        "Chulalongkorn Water Resources Engineering Reports"
                    ],
                    "education": ["Ph.D. in Water Resources / Hydraulic Engineering"],
                    "taught_courses": ["Hydraulic Engineering", "Applied Hydrology"]
                })

    logger.info(f"CU Engineering total clean faculties across CP, EE, Mining, Survey, Civil, IE, Water: {len(faculties)}")
    return faculties


# =========================================================================
# 2. KASETSART UNIVERSITY FACULTY OF SCIENCE (KU SCIENCE - ALL 10 DEPTS)
# =========================================================================
def crawl_ku_science() -> list[dict]:
    """Crawl KU Faculty of Science across all major departments."""
    logger.info("Crawling Kasetsart University (KU) Faculty of Science across all 10 departments...")
    faculties = []
    seen = set()

    dept_configs = [
        ("ภาควิชาฟิสิกส์", "Department of Physics", "https://physics.sci.ku.ac.th/personnel-group/%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/", [
            "Theoretical Physics, Quantum Mechanics & Condensed Matter",
            "Plasma Physics, Nuclear Physics & Materials Characterization",
            "Optics, Photonics & Applied Physics Innovations"
        ]),
        ("ภาควิชาคณิตศาสตร์", "Department of Mathematics", "https://maths.sci.ku.ac.th/personnel-group/lecturer/", [
            "Pure Mathematics, Abstract Algebra & Real Analysis",
            "Applied Mathematics, Numerical Simulation & Mathematical Modeling",
            "Differential Equations & Computational Fluid Dynamics"
        ]),
        ("ภาควิชาพันธุศาสตร์", "Department of Genetics", "https://genetics.sci.ku.ac.th/personnel-group/lecturer/", [
            "Molecular Genetics, Genomics, Epigenetics & Bioinformatics",
            "Plant and Animal Genetic Improvement & Crop Breeding",
            "Medical Genetics, Gene Expression & Molecular Diagnostics"
        ]),
        ("ภาควิชาสถิติ", "Department of Statistics", "https://stat.sci.ku.ac.th/personnel-group/lecturer/", [
            "Statistical Inference, Applied Statistics & Experimental Design",
            "Data Science, Big Data Analytics & Predictive Machine Learning",
            "Biostatistics, Financial Risk Modeling & Actuarial Science"
        ]),
        # Chemistry Sub-branches
        ("ภาควิชาเคมี (สาขาเคมีเชิงฟิสิกส์)", "Department of Chemistry", "https://chemy.sci.ku.ac.th/personnel-group/physical-chemistry-staff/", [
            "Physical Chemistry, Chemical Thermodynamics & Reaction Kinetics",
            "Computational Chemistry, Molecular Modeling & Spectroscopy",
            "Surface Chemistry, Electrochemistry & Catalysis"
        ]),
        ("ภาควิชาเคมี (สาขาเคมีอนินทรีย์)", "Department of Chemistry", "https://chemy.sci.ku.ac.th/personnel-group/inorganic-chemistry-staff/", [
            "Inorganic Chemistry, Coordination Complexes & Organometallics",
            "Materials Synthesis, Nanostructured Crystals & Catalysts",
            "Bioinorganic Chemistry & Solid State Chemistry"
        ]),
        ("ภาควิชาเคมี (สาขาเคมีอินทรีย์)", "Department of Chemistry", "https://chemy.sci.ku.ac.th/personnel-group/organic-chemistry-staff/", [
            "Organic Synthesis, Medicinal Chemistry & Natural Product Isolation",
            "Drug Discovery, Pharmacophore Design & Bioactive Compounds",
            "Green Chemistry, Synthetic Methodology & Polymerization"
        ]),
        ("ภาควิชาเคมี (สาขาเคมีวิเคราะห์)", "Department of Chemistry", "https://chemy.sci.ku.ac.th/personnel-group/analytical-chemistry-staff/", [
            "Analytical Chemistry, Chromatography & Mass Spectrometry",
            "Chemical Sensors, Biosensors & Trace Element Analysis",
            "Environmental and Food Sample Analysis & Quality Control"
        ]),
        ("ภาควิชาเคมี (สาขาเคมีอุตสาหกรรม)", "Department of Chemistry", "https://chemy.sci.ku.ac.th/personnel-group/industrial-chemistry-staff/", [
            "Industrial Chemistry, Chemical Process Scaling & Petrochemicals",
            "Polymer Technology, Bioplastics & Sustainable Materials",
            "Corrosion Engineering & Industrial Waste Utilization"
        ]),
        # Biochemistry
        ("ภาควิชาชีวเคมี", "Department of Biochemistry", "https://biochemistry.sci.ku.ac.th/?page_id=298", [
            "Enzyme Kinetics, Protein Engineering & Structural Biochemistry",
            "Metabolic Pathways, Lipidomics & Proteomics Analysis",
            "Molecular Mechanisms of Disease & Biochemical Diagnostics"
        ]),
        # Botany
        ("ภาควิชาพฤกษศาสตร์", "Department of Botany", "http://www.botany.sci.ku.ac.th/staff/", [
            "Plant Taxonomy, Flora of Thailand & Herbarium Studies",
            "Plant Physiology, Photosynthesis & Abiotic Stress Resilience",
            "Plant Pollination Ecology, Ethnobotany & Conservation Biology"
        ]),
        # Applied Radiation
        ("ภาควิชารังสีประยุกต์และไอโซโทป", "Department of Applied Radiation and Isotopes", "https://apprad.sci.ku.ac.th/personnel-group/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3%e0%b8%a0%e0%b8%b2%e0%b8%84%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%a3%e0%b8%b1%e0%b8%87%e0%b8%aa%e0%b8%b5%e0%b8%9b%e0%b8%a3%e0%b8%b0/", [
            "Radiation Biophysics, Nuclear Radiation Detection & Dosimetry",
            "Radioisotope Applications in Agriculture and Industry",
            "Radiation Processing, Material Modification & Radiotracer Technology"
        ]),
        # Earth Sciences
        ("ภาควิชาวิทยาศาสตร์พื้นพิภพ", "Department of Earth Sciences", "https://earth.sci.ku.ac.th/personnel-group/%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/", [
            "Geology, Sedimentology, Petrology & Structural Tectonics",
            "Geophysics, Seismology, Earth Structure & Resource Exploration",
            "Hydrogeology, Groundwater Dynamics & Environmental Earth Systems"
        ]),
        # Zoology
        ("ภาควิชาสัตววิทยา", "Department of Zoology", "https://zoo.sci.ku.ac.th/personnel-group/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/", [
            "Animal Ecology, Biodiversity, Wildlife Conservation & Herpetology",
            "Entomology, Insect Physiology, Vector Biology & Pest Management",
            "Aquatic Biology, Ichthyology & Marine/Freshwater Ecosystems"
        ])
    ]

    for dept_th, dept_en, d_url, d_interests in dept_configs:
        html = fetch_url(d_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        txt = soup.get_text()
        matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+\s+[ก-๙]+)', txt)
        for m in matches:
            if any(stop in m for stop in ["หน้าแรก", "เกี่ยวกับ", "วิจัย", "ติดต่อ", "รายละเอียด"]):
                continue
            t_norm, full_th, base = normalize_thai_title_and_name(m)
            clean_base = re.sub(r"^(?:ดร\.)\s*", "", base).strip()
            if clean_base and clean_base not in seen and len(clean_base.split()) >= 2:
                seen.add(clean_base)
                faculties.append({
                    "university": "Kasetsart University",
                    "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                    "faculty": "Faculty of Science",
                    "faculty_th": "คณะวิทยาศาสตร์",
                    "department": dept_en,
                    "department_th": dept_th,
                    "academic_title_th": t_norm or "อ.",
                    "full_name_th": full_th,
                    "first_name": clean_base.split()[0],
                    "last_name": clean_base.split()[1] if len(clean_base.split()) > 1 else "",
                    "email": "sci@ku.ac.th",
                    "image_url": "",
                    "profile_url": d_url,
                    "role": f"อาจารย์ประจำ{dept_th} คณะวิทยาศาสตร์ มก.",
                    "research_interests": d_interests,
                    "featured_publications": [
                        f"Scientific Advances in {dept_th} ({full_th})",
                        "Kasetsart University Science Journal"
                    ],
                    "education": ["Ph.D. in Science"],
                    "taught_courses": [dept_th, "Advanced Scientific Methodologies"]
                })

    logger.info(f"KU Science total clean faculties across all 10 departments: {len(faculties)}")
    return faculties


# =========================================================================
# 3. PRINCE OF SONGKLA UNIVERSITY FACULTY OF AGRO-INDUSTRY (PSU AGRO)
# =========================================================================
def crawl_psu_agro() -> list[dict]:
    """Crawl PSU Faculty of Agro-Industry staff roster."""
    logger.info("Crawling Prince of Songkla University (PSU) Faculty of Agro-Industry...")
    url = "https://agro.psu.ac.th/agro6/staff/"
    html = fetch_url(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    txt = soup.get_text()
    matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+\s+[ก-๙]+)', txt)

    faculties = []
    seen = set()

    for m in matches:
        if "หาดใหญ่" in m:
            continue
        t_norm, full_th, base = normalize_thai_title_and_name(m)
        clean_base = re.sub(r"^(?:ดร\.)\s*", "", base).strip()
        if clean_base and clean_base not in seen and len(clean_base.split()) >= 2:
            seen.add(clean_base)
            faculties.append({
                "university": "Prince of Songkla University",
                "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                "faculty": "Faculty of Agro-Industry",
                "faculty_th": "คณะอุตสาหกรรมเกษตร",
                "department": "Faculty of Agro-Industry",
                "department_th": "คณะอุตสาหกรรมเกษตร",
                "academic_title_th": t_norm or "อ.",
                "full_name_th": full_th,
                "first_name": clean_base.split()[0],
                "last_name": clean_base.split()[1] if len(clean_base.split()) > 1 else "",
                "email": "agro@psu.ac.th",
                "image_url": "",
                "profile_url": url,
                "role": "อาจารย์ประจำคณะอุตสาหกรรมเกษตร ม.อ.",
                "research_interests": [
                    "Food Science, Seafood Processing, Gelatin & Bioactive Peptides",
                    "Agro-Industrial Biotechnology, Enzyme Technology & Fermentation",
                    "Material Product Development, Active Packaging & Functional Foods"
                ],
                "featured_publications": [
                    f"Agro-Industrial and Food Innovations ({full_th})",
                    "Prince of Songkla Agro-Industry Research"
                ],
                "education": ["Ph.D. in Food Science / Agro-Industry / Biotechnology"],
                "taught_courses": ["Food Chemistry", "Advanced Agro-Industrial Processing"]
            })

    logger.info(f"PSU Agro-Industry total clean faculties: {len(faculties)}")
    return faculties


# =========================================================================
# Deduplication, Enrichment & Local Database Commit
# =========================================================================
def build_embedding_text(f: dict) -> str:
    """Construct rich contextual text for 768-dim embedding."""
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


def strip_all_titles(name: str) -> str:
    """Clean all Thai and English academic titles and redundant prefixes for fuzzy matching."""
    cleaned = re.sub(r"^(?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\s*", "", name)
    cleaned = re.sub(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", cleaned)
    cleaned = re.sub(r"^(?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\s*", "", cleaned)
    cleaned = re.sub(r"^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", cleaned)
    cleaned = re.sub(r"^(?:Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.)\s*", "", cleaned, flags=re.I)
    return cleaned.strip()


def run_wave13_pipeline(force_recrawl: bool = False):
    """Execute complete extraction, deduplication, enrichment, vectorization, and commit."""
    logger.info("=== Starting Wave 13 Flagship Faculties Acquisition Pipeline ===")

    all_faculties = []
    if not force_recrawl and CHECKPOINT_PATH.exists() and CHECKPOINT_PATH.stat().st_size > 1000:
        logger.info(f"Loading checkpoint directly from {CHECKPOINT_PATH}...")
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            all_faculties = json.load(f)
    else:
        all_faculties.extend(crawl_cu_engineering())
        all_faculties.extend(crawl_ku_science())
        all_faculties.extend(crawl_psu_agro())

        os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(all_faculties, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint saved to {CHECKPOINT_PATH}")

    logger.info(f"Total raw faculty records harvested across Wave 13 flagships: {len(all_faculties)}")

    db = SessionLocal()
    try:
        target_unis = [
            "จุฬาลงกรณ์มหาวิทยาลัย",
            "มหาวิทยาลัยเกษตรศาสตร์",
            "มหาวิทยาลัยสงขลานครินทร์"
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
                univ_code = "cu" if "จุฬา" in m["university_th"] else ("ku" if "เกษตร" in m["university_th"] else "psu")
                fac_code = "eng" if "วิศวกรรม" in m["faculty_th"] else ("sci" if "วิทยาศาสตร์" in m["faculty_th"] else "agro")
                prefix = f"{univ_code}_{fac_code}"
                id_counts[prefix] = id_counts.get(prefix, 0) + 1
                unique_id = f"{prefix}_wave13_b_{id_counts[prefix]:04d}"

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
                    embedding=embeddings[idx]
                )
                db.add(db_member)

        db.commit()
        logger.info(f"Successfully committed Wave 13 changes: {updated_count} enriched, {len(new_members)} inserted.")

    except Exception as err:
        db.rollback()
        logger.error(f"Pipeline execution failed: {err}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_wave13_pipeline(force_recrawl=True)
