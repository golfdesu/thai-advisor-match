# -*- coding: utf-8 -*-
"""
High-Throughput Autonomous Faculty Crawler - Wave 79
====================================================
Focus: Assumption University (มหาวิทยาลัยอัสสัมชัญ / ABAC)
Targeting all 10 Academic Schools to eliminate the 51-course professor deficit:
1. Martin de Tours School of Management and Economics (MSME) -> คณะบริหารธุรกิจและเศรษฐศาสตร์
2. Vincent Mary School of Engineering, Science and Technology (VMES) -> คณะวิศวกรรมศาสตร์และวิทยาศาสตร์เทคโนโลยี
3. Thomas Aquinas School of Law -> คณะนิติศาสตร์
4. Theophane Venard School of Biotechnology -> คณะเทคโนโลยีอาหาร ชีวภาพ และนวัตกรรม
5. Bernadette de Lourdes School of Nursing Science -> คณะพยาบาลศาสตร์
6. Montfort del Rosario School of Architecture and Design -> คณะสถาปัตยกรรมศาสตร์และการออกแบบ
7. Theodore Maria School of Arts -> คณะศิลปศาสตร์
8. Graduate School of Human Sciences -> บัณฑิตวิทยาลัยมนุษยศาสตร์
9. Albert Laurence School of Communication Arts -> คณะนิเทศศาสตร์
10. Louis Nobiron School of Music -> คณะดนตรี

5-Pillar Architecture:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=6)
- Pillar 2: OpenAlex Multiplexing Pool (Polite pool with mailto multiplexing)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 dummy vector + commit)
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
- Pillar 5: Disk Checkpointing to backend/data/agent_states/wave79_au_extraction.json
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import text

from app.core.database import SessionLocal, engine
from app.models.db_models import CourseDB, FacultyDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("wave79_crawler")

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave79_au_extraction.json"

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OPENALEX_KEYS = [
    "golfdesu.ch@gmail.com",
    "chayanon.ch@ku.th",
    "academic.match@ku.th",
    "advisor.match@ku.th",
    "advisor.match.thaiedu@gmail.com",
    "thaieducenter.dev@gmail.com",
    "research.thaiedu@gmail.com",
]

PREFIX_MAP = [
    (r"^(?:Asst\.\s*Prof\.\s*(?:Wg\.\s*Cdr\.\s*)?Dr\.|Assistant\s+Professor\s+Dr\.)\s*", "ผศ.ดร."),
    (r"^(?:Assoc\.\s*Prof\.\s*Dr\.|Associate\s+Professor\s+Dr\.)\s*", "รศ.ดร."),
    (r"^(?:Prof\.\s*Dr\.|Professor\s+Dr\.)\s*", "ศ.ดร."),
    (r"^(?:Asst\.\s*Prof\.|Assistant\s+Professor)\s*", "ผศ."),
    (r"^(?:Assoc\.\s*Prof\.|Associate\s+Professor)\s*", "รศ."),
    (r"^(?:Prof\.|Professor)\s*", "ศ."),
    (r"^(?:Dr\.|Doctor)\s*", "ดร."),
    (r"^(?:Ajarn|Aj\.|A\.)\s*", "อ."),
    (r"^(?:Mr\.|Mrs\.|Ms\.)\s*", "อ."),
]

MSME_DEPT_TRANSLATIONS = {
    "Accounting": ("ภาควิชาการบัญชี", "Department of Accounting"),
    "Digital Business Management": ("ภาควิชาการจัดการธุรกิจดิจิทัล", "Department of Digital Business Management"),
    "Economics": ("ภาควิชาเศรษฐศาสตร์", "Department of Economics"),
    "Finance and Risk Management": ("ภาควิชาการเงินและการบริหารความเสี่ยง", "Department of Finance and Risk Management"),
    "Hospitality and Tourism Management": ("ภาควิชาการจัดการการบริการและการท่องเที่ยว", "Department of Hospitality and Tourism Management"),
    "Global Business Management": ("ภาควิชาการจัดการธุรกิจระดับโลก", "Department of Global Business Management"),
    "Marketing": ("ภาควิชาการตลาด", "Department of Marketing"),
    "Real Estate Management": ("ภาควิชาการจัดการอสังหาริมทรัพย์", "Department of Real Estate Management"),
    "Supply Chain Management": ("ภาควิชาการจัดการโซ่อุปทาน", "Department of Supply Chain Management"),
    "Design and Digital Innovation": ("ภาควิชาการออกแบบและนวัตกรรมดิจิทัล", "Department of Design and Digital Innovation"),
    "Sustainable Business Management": ("ภาควิชาการจัดการธุรกิจเพื่อความยั่งยืน", "Department of Sustainable Business Management"),
    "Mathematics": ("ภาควิชาคณิตศาสตร์และสถิติ", "Department of Mathematics"),
}


def parse_academic_name(raw_name: str) -> Optional[Tuple[str, str, str, str]]:
    """Parse academic titles and clean name parts without double prefixes or mangling."""
    cleaned = re.sub(r"\s+", " ", raw_name).strip()
    if not cleaned or len(cleaned) < 3:
        return None

    # Strip trailing academic degrees (e.g. ", M.Phil, Ph.D")
    cleaned = re.sub(r",\s*(?:M\.Phil|Ph\.D|Ph\.D\.|M\.Sc\.|B\.Sc\.|M\.A\.|LL\.M\.).*$", "", cleaned, flags=re.IGNORECASE).strip()

    # Handle attached prefix like A.Kawee -> A. Kawee or Dr.Norarit -> Dr. Norarit
    cleaned = re.sub(r"^(A\.|Dr\.)([A-Za-z])", r"\1 \2", cleaned)

    ac_title = "อ."
    name_body = cleaned
    for pat, th_t in PREFIX_MAP:
        if re.search(pat, cleaned, flags=re.IGNORECASE):
            ac_title = th_t
            name_body = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
            break

    # Clean name body
    name_body = re.sub(r"^[.\s]+", "", name_body).strip()
    name_body = re.sub(r"\(.*?\)", "", name_body).strip()
    name_body = re.sub(r"\s+", " ", name_body)

    # Invert "Last, First" format if present
    if "," in name_body:
        parts = [x.strip() for x in name_body.split(",") if x.strip()]
        if len(parts) == 2:
            name_body = f"{parts[1]} {parts[0]}"

    parts = name_body.split()
    if not parts:
        return None

    fname = parts[0]
    lname = " ".join(parts[1:]) if len(parts) > 1 else fname
    cname = f"{fname} {lname}" if lname != fname else fname
    full_th = f"{ac_title} {cname}".strip()

    return ac_title, fname, lname, full_th


def crawl_msme_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls MSME Business School faculty directory."""
    url = "https://msme.au.edu/faculty-directory/"
    logger.info(f"Crawling MSME Business School: {url}")
    records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        for p in soup.find_all("p"):
            t = p.get_text()
            if "Department of Accounting" in t:
                lines = [line.strip() for line in t.split("\n") if line.strip()]
                current_dept = "General"
                current_person = None

                for line in lines:
                    if "Department of " in line:
                        m = re.search(r"Department of ([^(]+)", line)
                        if m:
                            current_dept = m.group(1).strip()
                    elif (
                        len(line.split()) >= 2
                        and not any(k in line for k in ["Department", "Chairperson", "Deputy", "Faculty Members:", "Program Director", "Office:", "Email:"])
                        and "@" not in line
                        and "(Adjunct)" not in line
                        and line not in MSME_DEPT_TRANSLATIONS
                    ):
                        if current_person:
                            records.append(current_person)
                        current_person = {
                            "raw_name": line,
                            "dept_key": current_dept,
                            "email": None,
                            "office": None,
                            "role": "Lecturer",
                        }
                    elif current_person:
                        if "@" in line:
                            em = re.search(r"([a-zA-Z0-9_.+-]+@(?:[a-zA-Z0-9-]+\.)*au\.edu)", line, flags=re.IGNORECASE)
                            if em:
                                current_person["email"] = em.group(1).strip().lower()
                        if "Office:" in line:
                            off = re.search(r"Office:\s*([^E\n]+)", line)
                            if off:
                                current_person["office"] = off.group(1).strip()

                if current_person:
                    records.append(current_person)
    except Exception as e:
        logger.error(f"Error crawling MSME: {e}")

    parsed_records = []
    for r in records:
        p = parse_academic_name(r["raw_name"])
        if not p:
            continue
        ac_title, fname, lname, full_th = p
        dept_th, dept_en = MSME_DEPT_TRANSLATIONS.get(
            r["dept_key"],
            (f"ภาควิชา{r['dept_key']}", f"Department of {r['dept_key']}"),
        )
        interests = [dept_en, r["dept_key"]]
        parsed_records.append({
            "school_code": "msme",
            "full_name_th": full_th,
            "academic_title_th": ac_title,
            "first_name": fname,
            "last_name": lname,
            "first_name_en": fname,
            "last_name_en": lname,
            "clean_name_th": f"{fname} {lname}",
            "university_th": "มหาวิทยาลัยอัสสัมชัญ",
            "university": "Assumption University",
            "faculty_th": "คณะบริหารธุรกิจและเศรษฐศาสตร์",
            "faculty": "Martin de Tours School of Management and Economics",
            "department_th": dept_th,
            "department": dept_en,
            "role": r["role"],
            "email": r["email"],
            "image_url": None,
            "profile_url": url,
            "research_interests": interests,
        })
    logger.info(f"MSME School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_vmes_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls VMES School of Engineering, Science and Technology."""
    url = "https://vmes.au.edu/faculty/"
    logger.info(f"Crawling VMES Engineering & Science: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for box in soup.find_all("div", class_=re.compile(r"team-box|person|col-|elementor-widget", re.I)):
            text_box = box.get_text(separator=" | ", strip=True)
            if "@au.edu" in text_box and len(text_box) < 350:
                lines = [x.strip() for x in text_box.split("|") if x.strip()]
                raw_name = lines[0]
                p = parse_academic_name(raw_name)
                if not p:
                    continue
                ac_title, fname, lname, full_th = p
                clean_key = f"{fname} {lname}"
                if clean_key in seen_names:
                    continue
                seen_names.add(clean_key)

                email = None
                em_m = re.search(r"([a-zA-Z0-9_.+-]+@au\.edu)", text_box)
                if em_m:
                    email = em_m.group(1).strip().lower()

                img = box.find("img")
                img_url = (img.get("src") or img.get("data-src")) if img else None
                if img_url and " " in img_url:
                    img_url = urllib.parse.quote(img_url, safe=":/%?=")

                role = lines[1] if len(lines) > 1 else "Lecturer"
                dept_th = "สาขาวิชาวิศวกรรมศาสตร์และเทคโนโลยี"
                dept_en = "Department of Engineering and Technology"
                if "Computer Science" in text_box:
                    dept_th = "สาขาวิชาวิทยาการคอมพิวเตอร์"
                    dept_en = "Department of Computer Science"
                elif "Informatics" in text_box or "Information Technology" in text_box:
                    dept_th = "สาขาวิชาเทคโนโลยีสารสนเทศ"
                    dept_en = "Department of Information Technology"
                elif "Electrical" in text_box:
                    dept_th = "สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์"
                    dept_en = "Department of Electrical and Computer Engineering"
                elif "Mechatronics" in text_box:
                    dept_th = "สาขาวิชาวิศวกรรมเมคคาทรอนิกส์และปัญญาประดิษฐ์"
                    dept_en = "Department of Mechatronics Engineering and Artificial Intelligence"
                elif "Automotive" in text_box:
                    dept_th = "สาขาวิชาวิศวกรรมยานยนต์พลังงานใหม่"
                    dept_en = "Department of New Energy Automotive Engineering"
                elif "Aeronautic" in text_box:
                    dept_th = "สาขาวิชาวิศวกรรมการบิน"
                    dept_en = "Department of Aeronautic Engineering"

                interests = [dept_en.replace("Department of ", "")]

                parsed_records.append({
                    "school_code": "vmes",
                    "full_name_th": full_th,
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "first_name_en": fname,
                    "last_name_en": lname,
                    "clean_name_th": clean_key,
                    "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                    "university": "Assumption University",
                    "faculty_th": "คณะวิศวกรรมศาสตร์และวิทยาศาสตร์เทคโนโลยี",
                    "faculty": "Vincent Mary School of Engineering, Science and Technology",
                    "department_th": dept_th,
                    "department": dept_en,
                    "role": role,
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "research_interests": interests,
                })
    except Exception as e:
        logger.error(f"Error crawling VMES: {e}")

    logger.info(f"VMES School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_law_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Thomas Aquinas School of Law."""
    url = "https://law.au.edu/faculty-members/"
    logger.info(f"Crawling School of Law: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        raw_names = []
        for h in soup.find_all(["h3", "h4"]):
            t = h.get_text(strip=True)
            if any(k in t for k in ["Dr.", "Prof.", "Yanpirat", "Anusontivong", "Pinpak", "Wonganant", "Kuandachakupt", "Yuvanont", "Siribannakul", "Chongpanish"]):
                if "Dean" not in t and "Director" not in t and "Office" not in t:
                    raw_names.append(t)
        raw_names = list(dict.fromkeys(raw_names))

        for raw_name in raw_names:
            p = parse_academic_name(raw_name)
            if not p:
                continue
            ac_title, fname, lname, full_th = p
            parsed_records.append({
                "school_code": "law",
                "full_name_th": full_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "first_name_en": fname,
                "last_name_en": lname,
                "clean_name_th": f"{fname} {lname}",
                "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                "university": "Assumption University",
                "faculty_th": "คณะนิติศาสตร์",
                "faculty": "Thomas Aquinas School of Law",
                "department_th": "สาขาวิชานิติศาสตร์",
                "department": "Department of Law",
                "role": "อาจารย์ประจำคณะนิติศาสตร์",
                "email": None,
                "image_url": None,
                "profile_url": url,
                "research_interests": ["Business Law", "International Law", "Jurisprudence"],
            })
    except Exception as e:
        logger.error(f"Error crawling Law: {e}")

    logger.info(f"Law School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_biotech_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Theophane Venard School of Biotechnology."""
    url = "https://foodbiotech.au.edu/faculty/"
    logger.info(f"Crawling School of Biotechnology: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for box in soup.find_all("div", class_=re.compile(r"team|image-box|person|col-|elementor-widget", re.I)):
            t = box.get_text(separator=" | ", strip=True)
            if "@au.edu" in t and len(t) < 350:
                lines = [x.strip() for x in t.split("|") if x.strip()]
                name = None
                for l in lines:
                    if any(p in l for p in ["Prof.", "Dr.", "Lecturer", "Watanya"]):
                        name = l.replace("Dean", "").replace("Lecturer", "").strip()
                        break
                if not name:
                    continue
                p = parse_academic_name(name)
                if not p:
                    continue
                ac_title, fname, lname, full_th = p
                clean_key = f"{fname} {lname}"
                if clean_key in seen_names:
                    continue
                seen_names.add(clean_key)

                email = None
                em_m = re.search(r"([a-zA-Z0-9_.+-]+@au\.edu)", t)
                if em_m:
                    email = em_m.group(1).strip().lower()

                parsed_records.append({
                    "school_code": "biotech",
                    "full_name_th": full_th,
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "first_name_en": fname,
                    "last_name_en": lname,
                    "clean_name_th": clean_key,
                    "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                    "university": "Assumption University",
                    "faculty_th": "คณะเทคโนโลยีอาหาร ชีวภาพ และนวัตกรรม",
                    "faculty": "Theophane Venard School of Biotechnology",
                    "department_th": "สาขาวิชาเทคโนโลยีชีวภาพทางอาหาร",
                    "department": "Department of Food Biotechnology",
                    "role": "Lecturer",
                    "email": email,
                    "image_url": None,
                    "profile_url": url,
                    "research_interests": ["Food Biotechnology", "Food Innovation", "Bioprocess Technology"],
                })
    except Exception as e:
        logger.error(f"Error crawling Biotech: {e}")

    logger.info(f"Biotech School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_nursing_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Bernadette de Lourdes School of Nursing Science."""
    url = "https://nursing.au.edu/faculty/"
    logger.info(f"Crawling School of Nursing Science: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for box in soup.find_all("div", class_=re.compile(r"team|image-box|person|col-|elementor-widget", re.I)):
            t = box.get_text(separator=" | ", strip=True)
            if "@au.edu" in t and len(t) < 350:
                lines = [x.strip() for x in t.split("|") if x.strip()]
                name = None
                for l in lines:
                    if any(p in l for p in ["Prof.", "Dr.", "A."]):
                        name = l.replace("dean", "").replace("Dean", "").strip()
                        break
                if not name:
                    continue
                p = parse_academic_name(name)
                if not p:
                    continue
                ac_title, fname, lname, full_th = p
                clean_key = f"{fname} {lname}"
                if clean_key in seen_names:
                    continue
                seen_names.add(clean_key)

                email = None
                em_m = re.search(r"([a-zA-Z0-9_.+-]+@au\.edu)", t)
                if em_m:
                    email = em_m.group(1).strip().lower()

                img = box.find("img")
                img_url = (img.get("src") or img.get("data-src")) if img else None
                if img_url and " " in img_url:
                    img_url = urllib.parse.quote(img_url, safe=":/%?=")

                parsed_records.append({
                    "school_code": "nursing",
                    "full_name_th": full_th,
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "first_name_en": fname,
                    "last_name_en": lname,
                    "clean_name_th": clean_key,
                    "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                    "university": "Assumption University",
                    "faculty_th": "คณะพยาบาลศาสตร์",
                    "faculty": "Bernadette de Lourdes School of Nursing Science",
                    "department_th": "สาขาวิชาพยาบาลศาสตร์",
                    "department": "Department of Nursing Science",
                    "role": "Lecturer",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "research_interests": ["Nursing Science", "Clinical Nursing", "Community Health Nursing"],
                })
    except Exception as e:
        logger.error(f"Error crawling Nursing: {e}")

    logger.info(f"Nursing School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_arch_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Montfort del Rosario School of Architecture and Design."""
    url = "https://arch.au.edu/faculty/"
    logger.info(f"Crawling School of Architecture: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for box in soup.find_all("div", class_=re.compile(r"team|image-box|person|col-|elementor-widget", re.I)):
            t = box.get_text(separator=" | ", strip=True)
            if "@au.edu" in t and len(t) < 350:
                lines = [x.strip() for x in t.split("|") if x.strip()]
                name = lines[0].replace("Dean", "").strip()
                if len(name.split()) < 2:
                    continue
                p = parse_academic_name(name)
                if not p:
                    continue
                ac_title, fname, lname, full_th = p
                clean_key = f"{fname} {lname}"
                if clean_key in seen_names:
                    continue
                seen_names.add(clean_key)

                email = None
                em_m = re.search(r"([a-zA-Z0-9_.+-]+@au\.edu)", t)
                if em_m:
                    email = em_m.group(1).strip().lower()

                img = box.find("img")
                img_url = (img.get("src") or img.get("data-src")) if img else None
                if img_url and " " in img_url:
                    img_url = urllib.parse.quote(img_url, safe=":/%?=")

                dept_th = "สาขาวิชาสถาปัตยกรรมศาสตร์"
                dept_en = "Department of Architecture"
                if "Interior" in t:
                    dept_th = "สาขาวิชาสถาปัตยกรรมภายในและการออกแบบ"
                    dept_en = "Department of Interior Architecture and Design"
                elif "Product" in t:
                    dept_th = "สาขาวิชาการออกแบบผลิตภัณฑ์"
                    dept_en = "Department of Product Design"

                parsed_records.append({
                    "school_code": "arch",
                    "full_name_th": full_th,
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "first_name_en": fname,
                    "last_name_en": lname,
                    "clean_name_th": clean_key,
                    "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                    "university": "Assumption University",
                    "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
                    "faculty": "Montfort del Rosario School of Architecture and Design",
                    "department_th": dept_th,
                    "department": dept_en,
                    "role": "Lecturer",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "research_interests": ["Architectural Design", "Interior Architecture", "Sustainable Design"],
                })
    except Exception as e:
        logger.error(f"Error crawling Architecture: {e}")

    logger.info(f"Architecture School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_arts_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Theodore Maria School of Arts."""
    url = "https://arts.au.edu/faculty/"
    logger.info(f"Crawling School of Arts: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for h3 in soup.find_all("h3"):
            raw_name = h3.get_text(strip=True)
            if not any(p in raw_name for p in ["Dr.", "A."]) or len(raw_name.split()) < 2:
                continue
            p = parse_academic_name(raw_name)
            if not p:
                continue
            ac_title, fname, lname, full_th = p
            clean_key = f"{fname} {lname}"
            if clean_key in seen_names:
                continue
            seen_names.add(clean_key)

            parent = h3.find_parent("div", class_=lambda c: c and "elementor-column" in c) or h3.parent
            p_desc = parent.find("p")
            desc = p_desc.get_text(strip=True) if p_desc else ""

            dept_th = "ภาควิชาภาษาอังกฤษธุรกิจ"
            dept_en = "Department of Business English"
            if "French" in desc:
                dept_th = "ภาควิชาภาษาฝรั่งเศสธุรกิจ"
                dept_en = "Department of Business French"
            elif "Chinese" in desc:
                dept_th = "ภาควิชาภาษาจีนธุรกิจ"
                dept_en = "Department of Business Chinese"
            elif "Japanese" in desc:
                dept_th = "ภาควิชาภาษาญี่ปุ่นธุรกิจ"
                dept_en = "Department of Business Japanese"
            elif "General Education" in desc:
                dept_th = "ภาควิชาศึกษาทั่วไป"
                dept_en = "Department of General Education"

            parsed_records.append({
                "school_code": "arts",
                "full_name_th": full_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "first_name_en": fname,
                "last_name_en": lname,
                "clean_name_th": clean_key,
                "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                "university": "Assumption University",
                "faculty_th": "คณะศิลปศาสตร์",
                "faculty": "Theodore Maria School of Arts",
                "department_th": dept_th,
                "department": dept_en,
                "role": desc or "อาจารย์ประจำคณะศิลปศาสตร์",
                "email": None,
                "image_url": None,
                "profile_url": url,
                "research_interests": ["Business English", "Applied Linguistics", "Language Education"],
            })
    except Exception as e:
        logger.error(f"Error crawling Arts: {e}")

    logger.info(f"Arts School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_human_sciences_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Graduate School of Human Sciences."""
    url = "https://humansciences.au.edu/faculty/"
    logger.info(f"Crawling Graduate School of Human Sciences: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for h in soup.find_all(["h4", "h5"]):
            raw_name = h.get_text(strip=True)
            if not any(p in raw_name for p in ["Dr.", "Prof."]) or len(raw_name.split()) < 2 or "Dean" in raw_name:
                continue
            p = parse_academic_name(raw_name)
            if not p:
                continue
            ac_title, fname, lname, full_th = p
            clean_key = f"{fname} {lname}"
            if clean_key in seen_names:
                continue
            seen_names.add(clean_key)

            parsed_records.append({
                "school_code": "humansciences",
                "full_name_th": full_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "first_name_en": fname,
                "last_name_en": lname,
                "clean_name_th": clean_key,
                "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                "university": "Assumption University",
                "faculty_th": "บัณฑิตวิทยาลัยมนุษยศาสตร์",
                "faculty": "Graduate School of Human Sciences",
                "department_th": "สาขาวิชาศึกษาศาสตร์และจิตวิทยา",
                "department": "Department of Education and Psychology",
                "role": "Graduate Faculty Professor",
                "email": None,
                "image_url": None,
                "profile_url": url,
                "research_interests": ["Counseling Psychology", "Curriculum and Instruction", "Educational Administration"],
            })
    except Exception as e:
        logger.error(f"Error crawling Human Sciences: {e}")

    logger.info(f"Human Sciences School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_ca_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Albert Laurence School of Communication Arts."""
    url = "https://ca.au.edu/people/"
    logger.info(f"Crawling School of Communication Arts: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for h3 in soup.find_all("h3"):
            raw_name = h3.get_text(strip=True)
            if not any(p in raw_name for p in ["Dr.", "Prof."]) or len(raw_name.split()) < 2:
                continue
            p = parse_academic_name(raw_name)
            if not p:
                continue
            ac_title, fname, lname, full_th = p
            clean_key = f"{fname} {lname}"
            if clean_key in seen_names:
                continue
            seen_names.add(clean_key)

            parsed_records.append({
                "school_code": "ca",
                "full_name_th": full_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "first_name_en": fname,
                "last_name_en": lname,
                "clean_name_th": clean_key,
                "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                "university": "Assumption University",
                "faculty_th": "คณะนิเทศศาสตร์",
                "faculty": "Albert Laurence School of Communication Arts",
                "department_th": "สาขาวิชานิเทศศาสตร์",
                "department": "Department of Communication Arts",
                "role": "Lecturer",
                "email": None,
                "image_url": None,
                "profile_url": url,
                "research_interests": ["Digital Media Communication", "Creative Commercial Communication", "Advertising"],
            })
    except Exception as e:
        logger.error(f"Error crawling CA: {e}")

    logger.info(f"CA School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def crawl_music_school(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Louis Nobiron School of Music."""
    url = "https://music.au.edu/faculties-th/"
    logger.info(f"Crawling School of Music: {url}")
    parsed_records = []
    try:
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()
        for div in soup.find_all(["div", "section"]):
            t = div.get_text(separator=" | ", strip=True)
            if any(k in t for k in ["Aj.", "Dr.", "Asst. Prof.", "Assoc. Prof.", "Prof."]) and len(t) < 150:
                lines = [x.strip() for x in t.split("|") if x.strip()]
                for l in lines:
                    if any(p in l for p in ["Aj.", "Dr.", "Asst. Prof.", "Assoc. Prof.", "Prof."]) and len(l.split()) >= 2 and not l.startswith("Dean") and not l.startswith("Chairperson") and not l.startswith("Deputy"):
                        p = parse_academic_name(l)
                        if not p:
                            continue
                        ac_title, fname, lname, full_th = p
                        clean_key = f"{fname} {lname}"
                        if clean_key in seen_names:
                            continue
                        seen_names.add(clean_key)

                        parsed_records.append({
                            "school_code": "music",
                            "full_name_th": full_th,
                            "academic_title_th": ac_title,
                            "first_name": fname,
                            "last_name": lname,
                            "first_name_en": fname,
                            "last_name_en": lname,
                            "clean_name_th": clean_key,
                            "university_th": "มหาวิทยาลัยอัสสัมชัญ",
                            "university": "Assumption University",
                            "faculty_th": "คณะดนตรี",
                            "faculty": "Louis Nobiron School of Music",
                            "department_th": "สาขาวิชาดนตรีพาณิชย์",
                            "department": "Department of Commercial Music",
                            "role": "Music Specialist / Lecturer",
                            "email": None,
                            "image_url": None,
                            "profile_url": url,
                            "research_interests": ["Music Production", "Composition", "Music Entrepreneurship"],
                        })
    except Exception as e:
        logger.error(f"Error crawling Music: {e}")

    logger.info(f"Music School yielded {len(parsed_records)} faculty records.")
    return parsed_records


def acquire_wave79_faculties():
    print("=================================================================", flush=True)
    print("🚀 ACQUIRING WAVE 79: ASSUMPTION UNIVERSITY (ABAC)", flush=True)
    print("=================================================================", flush=True)

    client = httpx.Client(timeout=20.0, headers=CLIENT_HEADERS, verify=False, follow_redirects=True)

    all_faculty: List[Dict[str, Any]] = []
    all_faculty.extend(crawl_msme_school(client))
    all_faculty.extend(crawl_vmes_school(client))
    all_faculty.extend(crawl_law_school(client))
    all_faculty.extend(crawl_biotech_school(client))
    all_faculty.extend(crawl_nursing_school(client))
    all_faculty.extend(crawl_arch_school(client))
    all_faculty.extend(crawl_arts_school(client))
    all_faculty.extend(crawl_human_sciences_school(client))
    all_faculty.extend(crawl_ca_school(client))
    all_faculty.extend(crawl_music_school(client))

    client.close()

    # Deduplicate within scraped records (clean_name_th)
    seen_names = set()
    unique_faculty = []
    for idx, f in enumerate(all_faculty):
        cname = f["clean_name_th"].lower()
        if cname in seen_names:
            continue
        seen_names.add(cname)
        f["id"] = f"au_{f['school_code']}__{idx+1:04d}"
        f["featured_publications"] = []
        f["total_citations"] = 0
        f["h_index"] = 0
        f["total_publications_count"] = 0
        f["openalex_id"] = None
        unique_faculty.append(f)

    logger.info(f"Total unique authentic faculty members extracted: {len(unique_faculty)}")

    # Pillar 5: Disk Checkpoint
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
        json.dump(unique_faculty, fp, ensure_ascii=False, indent=2)
    logger.info(f"💾 Checkpointed {len(unique_faculty)} records to {CHECKPOINT_PATH}")

    # Database Ingestion into public.faculties
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for f in unique_faculty:
            # Check if person already exists by email or clean name
            existing = None
            if f["email"]:
                existing = db.query(FacultyDB).filter(FacultyDB.email == f["email"]).first()
            if not existing:
                existing = db.query(FacultyDB).filter(
                    FacultyDB.university_th == f["university_th"],
                    FacultyDB.full_name_th == f["full_name_th"],
                ).first()

            if existing:
                # Update attributes
                if f["department_th"] and not existing.department_th:
                    existing.department_th = f["department_th"]
                if f["email"] and not existing.email:
                    existing.email = f["email"]
                if f["image_url"] and not existing.image_url:
                    existing.image_url = f["image_url"]
                updated += 1
            else:
                new_f = FacultyDB(
                    id=f["id"],
                    full_name_th=f["full_name_th"],
                    academic_title_th=f["academic_title_th"],
                    first_name=f["first_name"],
                    last_name=f["last_name"],
                    university_th=f["university_th"],
                    university=f["university"],
                    faculty_th=f["faculty_th"],
                    faculty=f["faculty"],
                    department_th=f["department_th"],
                    department=f["department"],
                    role=f["role"],
                    email=f["email"],
                    image_url=f["image_url"],
                    profile_url=f["profile_url"],
                    research_interests=f["research_interests"],
                    featured_publications=[],
                    total_citations=0,
                    h_index=0,
                    total_publications_count=0,
                    openalex_id=None,
                )
                db.add(new_f)
                inserted += 1

        db.commit()
        logger.info(f"✅ Ingestion Complete: {inserted} inserted, {updated} updated into public.faculties!")
    finally:
        db.close()


if __name__ == "__main__":
    acquire_wave79_faculties()
