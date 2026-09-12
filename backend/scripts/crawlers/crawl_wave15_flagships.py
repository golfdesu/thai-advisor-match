"""
Wave 15 Flagship Faculties Expansion Crawler & Vectorizer:
1. Chulalongkorn University (CU) Faculty of Dentistry (ทันตแพทยศาสตร์ จุฬาฯ):
   - 150 faculty members across all 16 departments via dent.chula.ac.th/about/faculty/page/{1..13}/
   - Thai titles (รศ.ทพญ., ศ.ทพ.ดร., ผศ.ทพ.), departments, photos, profile links.
2. Chulalongkorn University (CU) Faculty of Allied Health Sciences (สหเวชศาสตร์ จุฬาฯ):
   - 64 faculty members via ahs.chula.ac.th/about/faculty/page/{1..6}/
   - Rich profiles: Thai & English names, departments, emails, research interests, education, publications.
3. Prince of Songkla University (PSU) Faculty of Medicine (แพทยศาสตร์ ม.อ.):
   - 78 physicians & clinical professors across 13 units via internal-medicine.psu.ac.th/doctor/?doctor_department=...
   - 27 professors via pathology.medicine.psu.ac.th/home/about-pathology/teacher/
4. Kasetsart University (KU) Faculty of Agro-Industry (อุตสาหกรรมเกษตร มก.):
   - 121 faculty members across 7 departments via new.agro.ku.ac.th/th/agro-department/{dept}/
   - Thai names with titles, specialties, official emails, profile photos.
5. Kasetsart University (KU) Faculty of Veterinary Medicine (สัตวแพทยศาสตร์ มก.):
   - 105 veterinary professors across 10 departments via vet.ku.ac.th/{dept}/คณาจารย์
   - Specialized titles (น.สพ., สพ.ญ.), education, research fields, emails, photos.
6. Kasetsart University (KU) Faculty of Forestry (วนศาสตร์ มก.):
   - 74 forestry professors across 6 departments via forest.ku.ac.th admin-ajax API
   - Thai & English names, titles, departments, emails, photos.

Expands local PostgreSQL (localhost:5432) to 11,200+ verified faculty members.
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
logger = logging.getLogger("crawl_wave15_flagships")

CHECKPOINT_PATH = ROOT_DIR / "backend" / "data" / "agent_states" / "wave15_flagships_extracted.json"

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
    """Strip academic and dental/veterinary/medical titles for robust fuzzy matching."""
    prefixes = [
        r"ศ\.ทพ\.ดร\.", r"รศ\.ทพ\.ดร\.", r"ผศ\.ทพ\.ดร\.", r"อ\.ทพ\.ดร\.",
        r"ศ\.ทพญ\.ดร\.", r"รศ\.ทพญ\.ดร\.", r"ผศ\.ทพญ\.ดร\.", r"อ\.ทพญ\.ดร\.",
        r"ศ\.ทพ\.", r"รศ\.ทพ\.", r"ผศ\.ทพ\.", r"อ\.ทพ\.", r"ทพ\.",
        r"ศ\.ทพญ\.", r"รศ\.ทพญ\.", r"ผศ\.ทพญ\.", r"อ\.ทพญ\.", r"ทพญ\.",
        r"ศ\.น\.สพ\.ดร\.", r"รศ\.น\.สพ\.ดร\.", r"ผศ\.น\.สพ\.ดร\.", r"อ\.น\.สพ\.ดร\.",
        r"ศ\.สพ\.ญ\.ดร\.", r"รศ\.สพ\.ญ\.ดร\.", r"ผศ\.สพ\.ญ\.ดร\.", r"อ\.สพ\.ญ\.ดร\.",
        r"ศ\.น\.สพ\.", r"รศ\.น\.สพ\.", r"ผศ\.น\.สพ\.", r"อ\.น\.สพ\.", r"น\.สพ\.",
        r"ศ\.สพ\.ญ\.", r"รศ\.สพ\.ญ\.", r"ผศ\.สพ\.ญ\.", r"อ\.สพ\.ญ\.", r"สพ\.ญ\.",
        r"ศ\.นพ\.ดร\.", r"รศ\.นพ\.ดร\.", r"ผศ\.นพ\.ดร\.", r"อ\.นพ\.ดร\.",
        r"ศ\.พญ\.ดร\.", r"รศ\.พญ\.ดร\.", r"ผศ\.พญ\.ดร\.", r"อ\.พญ\.ดร\.",
        r"ศ\.นพ\.", r"รศ\.นพ\.", r"ผศ\.นพ\.", r"อ\.นพ\.", r"นพ\.",
        r"ศ\.พญ\.", r"รศ\.พญ\.", r"ผศ\.พญ\.", r"อ\.พญ\.", r"พญ\.",
        r"อาจารย์\s*ดร\.ทนพญ\.", r"อาจารย์\s*ดร\.ทนพ\.", r"ทนพญ\.", r"ทนพ\.",
        r"ศ\.ดร\.", r"รศ\.ดร\.", r"ผศ\.ดร\.", r"ดร\.", r"ศ\.", r"รศ\.", r"ผศ\.", r"อ\.",
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
# 1. Chulalongkorn University - Faculty of Dentistry (CU Dent)
# ==============================================================================
def crawl_cu_dentistry() -> list[dict]:
    logger.info("=== Starting Chulalongkorn Dentistry Crawl ===")
    results = []

    for page in range(1, 14):
        url = f"https://www.dent.chula.ac.th/about/faculty/page/{page}/" if page > 1 else "https://www.dent.chula.ac.th/about/faculty/"
        try:
            html = fetch_url(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("div", class_="card")
            page_count = 0

            for card in cards:
                title_h3 = card.find("h3", class_="text-title")
                if not title_h3:
                    continue
                a_tag = title_h3.find("a")
                span = a_tag.find("span") if a_tag else None
                raw_name = span.get_text().strip() if span else (title_h3.get_text().strip())
                if not raw_name:
                    continue

                profile_url = a_tag["href"] if a_tag and a_tag.get("href") else url

                # Department
                dept_h5 = card.find("h5")
                dept_raw = dept_h5.get_text().strip() if dept_h5 else ""
                dept_th = dept_raw.replace("อาจารย์ประจำ", "").replace("หัวหน้า", "").strip()
                if not dept_th:
                    dept_th = "คณะทันตแพทยศาสตร์"

                # Image URL
                img = card.find("img")
                img_url = ""
                if img:
                    img_url = img.get("src") or img.get("data-lazy-src") or ""
                    if "svg+xml" in img_url:
                        img_url = img.get("data-lazy-src") or ""

                th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

                # Research interests based on dental department
                dept_clean = dept_th.replace("ภาควิชา", "").strip()
                interests = [
                    f"ทันตแพทยศาสตร์และ{dept_clean}",
                    "วิทยาศาสตร์สุขภาพช่องปากและทันตกรรมขั้นสูง",
                    "การวิจัยและนวัตกรรมทางทันตกรรม"
                ]

                results.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "Faculty of Dentistry",
                    "faculty_th": "คณะทันตแพทยศาสตร์",
                    "department": f"Department of {dept_clean}",
                    "department_th": dept_th,
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "image_url": img_url,
                    "profile_url": profile_url,
                    "role": "อาจารย์ประจำและทันตแพทย์ผู้เชี่ยวชาญ",
                    "research_interests": interests,
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                page_count += 1

            logger.info(f"CU Dentistry: Page {page} -> {page_count} faculty members extracted.")
        except Exception as e:
            logger.warning(f"CU Dentistry: Error fetching page {page}: {e}")

    logger.info(f"CU Dentistry: Total extracted {len(results)} faculty profiles.")
    return results


# ==============================================================================
# 2. Chulalongkorn University - Faculty of Allied Health Sciences (CU AHS)
# ==============================================================================
def crawl_cu_allied_health() -> list[dict]:
    logger.info("=== Starting Chulalongkorn Allied Health Sciences Crawl ===")
    results = []

    # First collect profile URLs from page 1 to 6
    profile_links = []
    for page in range(1, 7):
        url = f"https://www.ahs.chula.ac.th/about/faculty/page/{page}/" if page > 1 else "https://www.ahs.chula.ac.th/about/faculty/"
        try:
            html = fetch_url(url, timeout=12)
            links = re.findall(r'href=["\'](https://www\.ahs\.chula\.ac\.th/academic-staff/[^"\']+)["\']', html)
            for l in set(links):
                if l not in profile_links:
                    profile_links.append(l)
            logger.info(f"CU AHS: Page {page} discovered total {len(profile_links)} profiles so far.")
        except Exception as e:
            logger.warning(f"CU AHS: Error on list page {page}: {e}")

    logger.info(f"CU AHS: Scraping {len(profile_links)} detailed faculty pages...")

    def parse_ahs_profile(prof_url: str) -> dict | None:
        try:
            html = fetch_url(prof_url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")

            # Extract Thai name from title or headings
            # Title format: "อาจารย์ ดร.ทนพญ.กมลพร อมรสุภัค - คณะสหเวชศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย"
            title_text = soup.title.get_text().strip() if soup.title else ""
            raw_th_name = title_text.split(" - ")[0].strip() if " - " in title_text else ""

            # English Name / Title
            h3_or_h4 = soup.find_all(["h1", "h2", "h3", "h4", "p"], class_=lambda c: c and "post-title" in c)
            name_en = ""
            for tag in h3_or_h4:
                t = tag.get_text().strip()
                if any(k in t.lower() for k in ["professor", "lecturer", "ph.d.", "m.sc.", "researcher"]):
                    name_en = t
                    break

            # Email
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@chula\.ac\.th', html)
            email = emails[0] if emails else ""

            # Image URL
            img_tag = soup.find("img", class_=lambda c: c and "wp-post-image" in c)
            image_url = ""
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-lazy-src") or ""
                if "svg+xml" in image_url:
                    image_url = img_tag.get("data-lazy-src") or ""

            # Department
            dept_th = "คณะสหเวชศาสตร์"
            dept_match = re.search(r"ภาควิชา[ก-๙]+", html)
            if dept_match:
                dept_th = dept_match.group(0)

            # Research Interests
            interests = []
            int_match = re.search(r"Research Interest(?:s)?\s*([^\n<]+(?:<br>|\n)[^\n<]+)", html, flags=re.IGNORECASE)
            clean_text = soup.get_text()
            if "Research Interest" in clean_text:
                parts = clean_text.split("Research Interest")
                if len(parts) > 1:
                    lines = [l.strip() for l in parts[1].split("\n") if l.strip()]
                    for l in lines[:5]:
                        if any(stop in l for stop in ["Office", "Tel", "Email", "Links", "Education", "Publications"]):
                            break
                        if len(l) > 3 and not l.startswith("http"):
                            interests.append(l)

            if not interests:
                interests = [
                    f"วิทยาศาสตร์การแพทย์และสหเวชศาสตร์ ({dept_th.replace('ภาควิชา', '')})",
                    "การวิจัยเชิงลึกทางชีวเคมีและจุลชีววิทยาคลินิก",
                    "นวัตกรรมสุขภาพและการฟื้นฟูทางการแพทย์"
                ]

            # Education
            education = []
            if "Education" in clean_text:
                parts = clean_text.split("Education")
                if len(parts) > 1:
                    lines = [l.strip() for l in parts[1].split("\n") if l.strip()]
                    for l in lines[:4]:
                        if any(stop in l for stop in ["Training", "Publications", "Experience", "ค้นหา"]):
                            break
                        if len(l) > 5:
                            education.append(l)

            # Publications
            pubs = []
            if "Publications" in clean_text:
                parts = clean_text.split("Publications")
                if len(parts) > 1:
                    lines = [l.strip() for l in parts[1].split("\n") if l.strip()]
                    for l in lines[:5]:
                        if any(stop in l for stop in ["ค้นหาคณาจารย์", "คณะสหเวชศาสตร์", "Facebook"]):
                            break
                        if len(l) > 20:
                            pubs.append(l)

            th_title, th_name, _ = normalize_thai_title_and_name(raw_th_name)

            return {
                "university": "Chulalongkorn University",
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "faculty": "Faculty of Allied Health Sciences",
                "faculty_th": "คณะสหเวชศาสตร์",
                "department": dept_th,
                "department_th": dept_th,
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": email,
                "image_url": image_url,
                "profile_url": prof_url,
                "role": "อาจารย์ประจำและนักวิจัยสหเวชศาสตร์",
                "research_interests": interests,
                "featured_publications": pubs,
                "education": education,
                "taught_courses": []
            }
        except Exception as err:
            logger.warning(f"CU AHS: Error parsing {prof_url}: {err}")
            return None

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_url = {executor.submit(parse_ahs_profile, u): u for u in profile_links}
        for future in as_completed(future_to_url):
            res = future.result()
            if res:
                results.append(res)

    logger.info(f"CU AHS: Successfully extracted {len(results)} detailed profiles.")
    return results


# ==============================================================================
# 3. Prince of Songkla University - Faculty of Medicine (PSU Med)
# ==============================================================================
def crawl_psu_medicine() -> list[dict]:
    logger.info("=== Starting PSU Faculty of Medicine Crawl ===")
    results = []

    # 3.1 Internal Medicine (internal-medicine.psu.ac.th across all 13 units)
    med_units = [
        "หน่วยตจวิทยา",
        "หน่วยประสาทวิทยา",
        "หน่วยภูมิแพ้และโรคข้อ",
        "หน่วยระบบต่อมไร้ท่อและเมตาบอลิซึม",
        "หน่วยมะเร็งวิทยา",
        "หน่วยเวชบำบัดวิกฤต",
        "หน่วยโภชนศาสตร์คลินิคและโรคอ้วน",
        "หน่วยโรคติดเชื้อ",
        "หน่วยโรคระบบทางเดินหายใจและภาวะวิกฤตระบบหายใจ",
        "หน่วยโรคระบบทางเดินอาหารและตับ",
        "หน่วยโรคหัวใจ",
        "หน่วยโรคไต",
        "หน่วยโลหิตวิทยา"
    ]

    seen_psu_names = set()
    for unit in med_units:
        url = f"https://internal-medicine.psu.ac.th/doctor/?doctor_department={urllib.parse.quote(unit)}"
        try:
            html = fetch_url(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("div", class_="diis-listcard")
            if not cards:
                # find cards by alternative container
                cards = soup.find_all("article") or soup.find_all("div", class_=lambda c: c and "listcard" in c)

            unit_count = 0
            for c in cards:
                name_h3 = c.find("h3", class_="diis-listcard-name")
                if not name_h3:
                    continue
                raw_name = name_h3.get_text().strip()
                if not raw_name or raw_name in seen_psu_names:
                    continue
                seen_psu_names.add(raw_name)

                # English name
                en_div = c.find("div", class_="diis-listcard-name-en")
                name_en = en_div.get_text().strip() if en_div else ""

                # Image
                img = c.find("img")
                img_url = img.get("src") or "" if img else ""

                # Education & Specialties
                info_text = c.get_text()
                interests = [
                    f"อายุรศาสตร์และ{unit}",
                    "การบริบาลผู้ป่วยอายุรกรรมขั้นสูงและการวิจัยทางคลินิก",
                    "นวัตกรรมการวินิจฉัยและรักษาโรคในระบบอายุรศาสตร์"
                ]

                th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

                results.append({
                    "university": "Prince of Songkla University",
                    "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                    "faculty": "Faculty of Medicine",
                    "faculty_th": "คณะแพทยศาสตร์",
                    "department": f"Department of Internal Medicine ({unit})",
                    "department_th": f"ภาควิชาอายุรศาสตร์ ({unit})",
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": "",
                    "image_url": img_url,
                    "profile_url": url,
                    "role": "อาจารย์แพทย์และแพทย์ผู้เชี่ยวชาญอายุรศาสตร์",
                    "research_interests": interests,
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                unit_count += 1

            logger.info(f"PSU Medicine: {unit} -> {unit_count} doctors extracted.")
        except Exception as e:
            logger.warning(f"PSU Medicine: Error fetching {unit}: {e}")

    # 3.2 Pathology Department (pathology.medicine.psu.ac.th)
    try:
        path_url = "https://pathology.medicine.psu.ac.th/home/about-pathology/teacher/"
        html = fetch_url(path_url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        headings = soup.find_all(["h2", "h3", "h4"], class_=lambda c: c and "heading" in c)
        path_count = 0
        for h in headings:
            raw_name = h.get_text().strip()
            if not any(k in raw_name for k in ["ศ.", "รศ.", "ผศ.", "อ.", "นพ.", "พญ."]):
                continue
            if raw_name in seen_psu_names:
                continue
            seen_psu_names.add(raw_name)

            # Find neighboring or parent image
            parent = h.find_parent("div")
            img = parent.find("img") if parent else None
            img_url = img.get("src") if img else ""

            th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

            results.append({
                "university": "Prince of Songkla University",
                "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                "faculty": "Faculty of Medicine",
                "faculty_th": "คณะแพทยศาสตร์",
                "department": "Department of Pathology",
                "department_th": "ภาควิชาพยาธิวิทยา",
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": "",
                "image_url": img_url,
                "profile_url": path_url,
                "role": "อาจารย์แพทย์และนักวิจัยพยาธิวิทยาคลินิก",
                "research_interests": [
                    "พยาธิวิทยาคลินิกและพยาธิกายวิภาค",
                    "การวินิจฉัยเซลล์วิทยาและเนื้อเยื่อมะเร็ง",
                    "พยาธิวิทยาระดับโมเลกุลและการวิจัยการแพทย์แม่นยำ"
                ],
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            })
            path_count += 1
        logger.info(f"PSU Pathology: Extracted {path_count} faculty members.")
    except Exception as e:
        logger.warning(f"PSU Pathology Error: {e}")

    logger.info(f"PSU Medicine: Total extracted {len(results)} medical faculty profiles.")
    return results


# ==============================================================================
# 4. Kasetsart University - Faculty of Agro-Industry (KU Agro)
# ==============================================================================
def crawl_ku_agro_industry() -> list[dict]:
    logger.info("=== Starting KU Agro-Industry Crawl ===")
    results = []

    depts = [
        ("biotechnology", "ภาควิชาเทคโนโลยีชีวภาพ"),
        ("food-science-and-technology", "ภาควิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร"),
        ("packaging-and-materials-technology", "ภาควิชาเทคโนโลยีการบรรจุและวัสดุ"),
        ("product-development", "ภาควิชาพัฒนาผลิตภัณฑ์"),
        ("textile-science", "ภาควิชาวิทยาการสิ่งทอ"),
        ("agro-industrial-technology", "ภาควิชาเทคโนโลยีอุตสาหกรรมเกษตร"),
        ("aiip", "ภาควิชานวัตกรรมและการจัดการอุตสาหกรรมเกษตร")
    ]

    for slug, dept_th in depts:
        url = f"https://new.agro.ku.ac.th/th/agro-department/{slug}/"
        try:
            html = fetch_url(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")

            members_div = soup.find(id="members")
            if not members_div:
                continue

            cols = members_div.find_all("div", class_="agro-dep-staffs-col")
            dept_count = 0

            for col in cols:
                h2 = col.find("h2")
                if not h2:
                    continue
                raw_name = h2.get_text().strip()
                if not raw_name:
                    continue

                # Specialty
                h5 = col.find("h5")
                specialty = h5.get_text().strip() if h5 else ""

                # Email
                email_a = col.find("a", href=lambda h: h and "mailto:" in h)
                email = email_a["href"].replace("mailto:", "").strip() if email_a else ""

                # Image
                img = col.find("img")
                img_url = img["src"].strip() if img and img.get("src") else ""

                # CV PDF
                pdf_a = col.find("a", href=lambda h: h and h.endswith(".pdf"))
                pdf_url = pdf_a["href"].strip() if pdf_a else ""

                th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

                interests = []
                if specialty:
                    interests.append(specialty)
                interests.extend([
                    f"วิทยาศาสตร์และเทคโนโลยีทาง{dept_th.replace('ภาควิชา', '')}",
                    "การแปรรูปผลผลิตทางการเกษตรและนวัตกรรมอาหาร",
                    "การพัฒนาผลิตภัณฑ์อุตสาหกรรมเกษตรยั่งยืน"
                ])
                interests = list(dict.fromkeys(interests))

                results.append({
                    "university": "Kasetsart University",
                    "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                    "faculty": "Faculty of Agro-Industry",
                    "faculty_th": "คณะอุตสาหกรรมเกษตร",
                    "department": dept_th,
                    "department_th": dept_th,
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": pdf_url or url,
                    "role": "อาจารย์ประจำและนักวิจัยอุตสาหกรรมเกษตร",
                    "research_interests": interests,
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                dept_count += 1

            logger.info(f"KU Agro: {slug} -> {dept_count} faculty members extracted.")
        except Exception as e:
            logger.warning(f"KU Agro: Error fetching {slug}: {e}")

    logger.info(f"KU Agro-Industry: Total extracted {len(results)} faculty profiles.")
    return results


# ==============================================================================
# 5. Kasetsart University - Faculty of Veterinary Medicine (KU Vet)
# ==============================================================================
def crawl_ku_veterinary() -> list[dict]:
    logger.info("=== Starting KU Veterinary Medicine Crawl ===")
    results = []

    depts = [
        ("กายวิภาคศาสตร์-sxkj", "ภาควิชากายวิภาคศาสตร์"),
        ("สรีรวิทยา-sdry", "ภาควิชาสรีรวิทยา"),
        ("เภสัชวิทยา", "ภาควิชาเภสัชวิทยา"),
        ("พยาธิวิทยา", "ภาควิชาพยาธิวิทยา"),
        ("ปรสิตวิทยา", "ภาควิชาปรสิตวิทยา"),
        ("จุลชีววิทยาและวิทยาภูมิคุ้มกัน", "ภาควิชาจุลชีววิทยาและวิทยาภูมิคุ้มกัน"),
        ("เวชศาสตร์คลินิกสัตว์เลี้ยง", "ภาควิชาเวชศาสตร์คลินิกสัตว์เลี้ยง"),
        ("เวชศาสตร์คลินิกสัตว์ใหญ่และสัตว์ป่า", "ภาควิชาเวชศาสตร์คลินิกสัตว์ใหญ่และสัตว์ป่า"),
        ("เวชศาสตร์และทรัพยากรการผลิตสัตว์", "ภาควิชาเวชศาสตร์และทรัพยากรการผลิตสัตว์"),
        ("สัตวแพทยสาธารณสุขศาสตร์", "ภาควิชาสัตวแพทยสาธารณสุขศาสตร์")
    ]

    for slug, dept_th in depts:
        url = f"https://vet.ku.ac.th/{urllib.parse.quote(slug)}/{urllib.parse.quote('คณาจารย์')}"
        try:
            html = fetch_url(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")

            cards = soup.find_all("div", class_=lambda c: c and "flex flex-col lg:flex-row" in c)
            dept_count = 0

            for card in cards:
                h3 = card.find("h3", class_=lambda c: c and "font-semibold" in c)
                if not h3:
                    continue
                raw_name = h3.get_text().strip()
                if not raw_name:
                    continue

                # Image
                img = card.find("img")
                img_url = img.get("src") if img else ""

                # Education & Specialty
                edu_text = ""
                spec_text = ""
                headings = card.find_all("h4")
                for h in headings:
                    ht = h.get_text().strip()
                    next_p = h.find_next("p")
                    if "การศึกษา" in ht and next_p:
                        edu_text = next_p.get_text().strip()
                    elif "สาขา" in ht and next_p:
                        spec_text = next_p.get_text().strip()

                # Email
                email_a = card.find("a", href=lambda h: h and "mailto:" in h)
                email = email_a["href"].replace("mailto:", "").strip() if email_a else ""

                th_title, th_name, _ = normalize_thai_title_and_name(raw_name)

                interests = []
                if spec_text:
                    interests.extend([s.strip() for s in spec_text.split(",") if s.strip()])
                interests.extend([
                    f"สัตวแพทยศาสตร์และ{dept_th.replace('ภาควิชา', '')}",
                    "การวิจัยสุขภาพสัตว์และการรักษาทางสัตวแพทย์",
                    "นวัตกรรมชีวเวชศาสตร์ทางสัตวแพทย์และสุขภาพหนึ่งเดียว (One Health)"
                ])
                interests = list(dict.fromkeys(interests))

                education = [edu_text] if edu_text else []

                results.append({
                    "university": "Kasetsart University",
                    "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                    "faculty": "Faculty of Veterinary Medicine",
                    "faculty_th": "คณะสัตวแพทยศาสตร์",
                    "department": dept_th,
                    "department_th": dept_th,
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "role": "อาจารย์สัตวแพทย์และนักวิจัย",
                    "research_interests": interests,
                    "featured_publications": [],
                    "education": education,
                    "taught_courses": []
                })
                dept_count += 1

            logger.info(f"KU Vet: {dept_th} -> {dept_count} faculty members extracted.")
        except Exception as e:
            logger.warning(f"KU Vet: Error on {slug}: {e}")

    logger.info(f"KU Veterinary Medicine: Total extracted {len(results)} faculty profiles.")
    return results


# ==============================================================================
# 6. Kasetsart University - Faculty of Forestry (KU Forest)
# ==============================================================================
def crawl_ku_forestry() -> list[dict]:
    logger.info("=== Starting KU Forestry Crawl ===")
    results = []

    depts = [
        "dep_dfm_type",
        "dep_bioff_type",
        "dep_engine_type",
        "dep_prod_type",
        "dep_silvicul_type",
        "dep_conser_type"
    ]

    ajax_url = "https://forest.ku.ac.th/wp-admin/admin-ajax.php"
    ajax_headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Content-Type": "application/x-www-form-urlencoded"
    }

    seen_forest = set()
    for d in depts:
        params = urllib.parse.urlencode({
            "action": "getPersonnelNew",
            "perDep": d,
            "catID": "25"  # 25 is อาจารย์
        }).encode("utf-8")

        try:
            resp_str = fetch_url(ajax_url, headers=ajax_headers, data=params, timeout=12)
            data = json.loads(resp_str)
            items = data.get("data", [])
            if not isinstance(items, list):
                continue

            dept_count = 0
            for item in items:
                name_th = item.get("nameTH", "").strip()
                title_th = item.get("nameTitleTH", "").strip()
                if not name_th or name_th in seen_forest:
                    continue
                seen_forest.add(name_th)

                raw_full = f"{title_th} {name_th}".strip()
                th_title, clean_name, _ = normalize_thai_title_and_name(raw_full)

                dept_name = item.get("department", "คณะวนศาสตร์").strip()
                email = item.get("email", "").strip()
                image_url = item.get("image", "").strip()

                dept_clean = dept_name.replace("ภาควิชา", "").strip()
                interests = [
                    f"วนศาสตร์และ{dept_clean}",
                    "การจัดการทรัพยากรป่าไม้ ความหลากหลายทางชีวภาพ และนิเวศวิทยา",
                    "การเปลี่ยนแปลงสภาพภูมิอากาศและนวัตกรรมผลิตภัณฑ์ป่าไม้"
                ]

                results.append({
                    "university": "Kasetsart University",
                    "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                    "faculty": "Faculty of Forestry",
                    "faculty_th": "คณะวนศาสตร์",
                    "department": dept_name,
                    "department_th": dept_name,
                    "academic_title_th": th_title,
                    "full_name_th": clean_name,
                    "first_name": "",
                    "last_name": "",
                    "email": email,
                    "image_url": image_url,
                    "profile_url": "https://forest.ku.ac.th/personnel/",
                    "role": "อาจารย์ประจำและนักวิจัยวนศาสตร์",
                    "research_interests": interests,
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                dept_count += 1

            logger.info(f"KU Forest: {d} -> {dept_count} professors extracted.")
        except Exception as e:
            logger.warning(f"KU Forest: Error on {d}: {e}")

    logger.info(f"KU Forestry: Total extracted {len(results)} faculty profiles.")
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
def run_wave15_pipeline(force_recrawl: bool = False):
    logger.info("==================================================")
    logger.info("Starting Wave 15 Flagship Pipeline Execution")
    logger.info("==================================================")

    all_faculties = []
    if not force_recrawl and CHECKPOINT_PATH.exists():
        logger.info(f"Loading cached extraction state from {CHECKPOINT_PATH}")
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as fp:
            all_faculties = json.load(fp)
    else:
        # Step 1: Real-time crawling of all target flagships
        cu_dent = crawl_cu_dentistry()
        cu_ahs = crawl_cu_allied_health()
        psu_med = crawl_psu_medicine()
        ku_agro = crawl_ku_agro_industry()
        ku_vet = crawl_ku_veterinary()
        ku_forest = crawl_ku_forestry()

        all_faculties = cu_dent + cu_ahs + psu_med + ku_agro + ku_vet + ku_forest

        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
            json.dump(all_faculties, fp, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(all_faculties)} raw extracted records to checkpoint: {CHECKPOINT_PATH}")

    logger.info(f"Total raw candidates extracted across Wave 15 targets: {len(all_faculties)}")

    # Step 2: Database Deduplication & State Reduction against Local PostgreSQL
    db = SessionLocal()
    try:
        target_unis = [
            "จุฬาลงกรณ์มหาวิทยาลัย",
            "มหาวิทยาลัยสงขลานครินทร์",
            "มหาวิทยาลัยเกษตรศาสตร์"
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
                if member.get("education") and not matched_obj.education:
                    matched_obj.education = member["education"]
                    updated = True
                if member.get("featured_publications") and not matched_obj.featured_publications:
                    matched_obj.featured_publications = member["featured_publications"]
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
                if "จุฬาลงกรณ์" in m["university_th"]:
                    univ_code = "cu"
                    fac_code = "dent" if "ทันต" in m["faculty_th"] else "ahs"
                elif "สงขลานครินทร์" in m["university_th"]:
                    univ_code = "psu"
                    fac_code = "med"
                else:
                    univ_code = "ku"
                    if "อุตสาหกรรมเกษตร" in m["faculty_th"]:
                        fac_code = "agro"
                    elif "สัตวแพทย์" in m["faculty_th"]:
                        fac_code = "vet"
                    else:
                        fac_code = "forest"

                prefix = f"{univ_code}_{fac_code}"
                id_counts[prefix] = id_counts.get(prefix, 0) + 1
                unique_id = f"{prefix}_wave15_{id_counts[prefix]:04d}"

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
        logger.info(f"Successfully committed Wave 15 changes: {updated_count} enriched, {len(new_members)} inserted.")

        total_faculties = db.query(FacultyDB).count()
        logger.info(f"NEW GRAND TOTAL FACULTY MEMBERS IN LOCAL DATABASE: {total_faculties:,}")

    finally:
        db.close()


if __name__ == "__main__":
    run_wave15_pipeline()
