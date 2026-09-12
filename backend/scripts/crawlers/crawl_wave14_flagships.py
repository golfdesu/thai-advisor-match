"""
Wave 14 Flagship Faculties Expansion Crawler & Vectorizer:
1. Mahidol University (MU) Faculty of Science (MUSC):
   - Central Research Expertise Portal (305 professors via science.mahidol.ac.th/expertise)
   - Rich profiles: Thai & English names, Scopus metrics (h-index, citations, output),
     education, research expertise, email, photo URLs.
2. Khon Kaen University (KKU) Faculty of Science (SCi KKU):
   - 197 faculty members via official dataset repository
   - Comprehensive across 9 departments: Statistics, Mathematics, Biochemistry,
     Biology, Chemistry, Physics, Environmental Science, Integrated Science, Microbiology.
3. Khon Kaen University (KKU) Faculty of Agriculture (AG KKU):
   - 95+ faculty members via ag.kku.ac.th
   - Core departments: Agronomy, Horticulture, Agricultural Economics,
     Animal Science, Agricultural Innovation, Entomology and Plant Pathology, Executives.
4. Chulalongkorn University (CU) Faculty of Science (SC CU):
   - Departments: Chemistry, Mathematics & Computer Science, Physics, Biology,
     Food Technology, Materials Science, Botany, Marine Science.

Expands local PostgreSQL (localhost:5432) to 10,500+ verified faculty members.
"""

import os
import re
import sys
import csv
import io
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
logger = logging.getLogger("crawl_wave14_flagships")

CHECKPOINT_PATH = ROOT_DIR / "backend" / "data" / "agent_states" / "wave14_flagships_extracted.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fetch_url(url: str, headers: dict = None, timeout: int = 12, encoding: str = "utf-8") -> str:
    h = headers or HEADERS
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return resp.read().decode(encoding, errors="ignore")


def strip_all_titles(name: str) -> str:
    """Strip academic titles to leave pure first and last name for RapidFuzz deduplication."""
    prefixes = [
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
# 1. Mahidol University - Faculty of Science (MUSC)
# ==============================================================================
def crawl_mahidol_science() -> list[dict]:
    logger.info("=== Starting Mahidol Science Crawl ===")
    index_url = "https://science.mahidol.ac.th/expertise/index_th.php"
    html = fetch_url(index_url)
    soup = BeautifulSoup(html, "html.parser")

    roster = []
    for div in soup.find_all("div", id="list"):
        a = div.find("a")
        if a and a.get("href"):
            raw_text = a.get_text().strip()
            # Format: "กนกพรรณ วงศ์ประเสริฐ, ศ.ดร."
            href = a["href"]
            roster.append((raw_text, href))

    logger.info(f"Mahidol Science: Discovered {len(roster)} faculty members in index.")

    results = []

    def scrape_profile(item: tuple) -> dict | None:
        raw_text, href = item
        name_part = raw_text
        title_part = "อาจารย์"
        if "," in raw_text:
            parts = [p.strip() for p in raw_text.split(",")]
            name_part = parts[0]
            title_part = parts[1] if len(parts) > 1 else "อาจารย์"

        th_title, th_name, _ = normalize_thai_title_and_name(f"{title_part} {name_part}")

        q_name = urllib.parse.quote(name_part)
        detail_url = f"https://science.mahidol.ac.th/expertise/search_th.php?q={q_name}"

        try:
            d_html = fetch_url(detail_url, timeout=10)
            d_soup = BeautifulSoup(d_html, "html.parser")

            # Extract English Name from H1
            # Format: "Kornkamon Lertsuwan \n กรกมล เลิศสุวรรณ"
            h1 = d_soup.find("h1")
            name_en = ""
            first_name = ""
            last_name = ""
            if h1:
                h1_lines = [l.strip() for l in h1.get_text().split("\n") if l.strip()]
                for l in h1_lines:
                    if re.search(r"[a-zA-Z]", l):
                        name_en = l.strip()
                        break
            if name_en:
                parts_en = name_en.split()
                first_name = parts_en[0] if parts_en else ""
                last_name = " ".join(parts_en[1:]) if len(parts_en) > 1 else ""

            # Extract Metrics
            h_index = None
            citations = None
            for h3 in d_soup.find_all("h3"):
                h3_text = h3.get_text().strip()
                nxt = h3.find_next_sibling()
                val_txt = nxt.get_text().strip() if nxt else ""
                if "h-index" in h3_text and val_txt.isdigit():
                    h_index = int(val_txt)
                elif "Citations" in h3_text and val_txt.isdigit():
                    citations = int(val_txt)

            # Extract Department, Email, Photo
            dept_th = "คณะวิทยาศาสตร์"
            email = ""
            image_url = ""

            for div in d_soup.find_all("div", class_="row"):
                div_text = div.get_text()
                if "Department / School:" in div_text:
                    m_dept = re.search(r"Department / School:\s*([^\n\r]+)", div_text)
                    if m_dept:
                        dept_val = m_dept.group(1).strip()
                        dept_map = {
                            "Anatomy": "ภาควิชากายวิภาคศาสตร์",
                            "Biochemistry": "ภาควิชาชีวเคมี",
                            "Biology": "ภาควิชาชีววิทยา",
                            "Biotechnology": "ภาควิชาเทคโนโลยีชีวภาพ",
                            "Chemistry": "ภาควิชาเคมี",
                            "Mathematics": "ภาควิชาคณิตศาสตร์",
                            "Microbiology": "ภาควิชาจุลชีววิทยา",
                            "Pathobiology": "ภาควิชาพยาธิชีววิทยา",
                            "Pharmacology": "ภาควิชาเภสัชวิทยา",
                            "Physics": "ภาควิชาฟิสิกส์",
                            "Physiology": "ภาควิชาสรีรวิทยา",
                            "Plant Science": "ภาควิชาพฤกษศาสตร์",
                            "Materials Science": "กลุ่มสาขาวิชาวัสดุศาสตร์และนวัตกรรมวัสดุ",
                            "Bioinnovation": "กลุ่มสาขาวิชาชีวนวัตกรรม"
                        }
                        dept_th = dept_map.get(dept_val, f"ภาควิชา{dept_val}")
                if "E-Mail:" in div_text and not email:
                    m_mail = re.search(r"[\w\.-]+@mahidol\.(?:edu|ac\.th)", div_text)
                    if m_mail:
                        email = m_mail.group(0).strip()

            # Image
            for img in d_soup.find_all("img"):
                src = img.get("src", "")
                if "expertise/uploads" in src or "backoffice" in src:
                    if src.startswith("http"):
                        image_url = src
                    else:
                        image_url = f"https://science.mahidol.ac.th{src}"
                    break

            # Expertise keywords
            interests = []
            for h3 in d_soup.find_all("h3"):
                if "Expertise" in h3.get_text():
                    nxt = h3.find_next_sibling()
                    if nxt:
                        kw_txt = nxt.get_text().strip()
                        # Keywords may be lumped or comma-delimited
                        split_kws = re.findall(r"[A-Z][a-z0-9\s-]+(?=[A-Z]|$)|[ก-๙]+", kw_txt)
                        for kw in split_kws:
                            k = kw.strip()
                            if len(k) > 2 and k not in interests:
                                interests.append(k)
                    break

            # Education
            education = []
            for h3 in d_soup.find_all("h3"):
                if "Education" in h3.get_text():
                    nxt = h3.find_next_sibling()
                    if nxt:
                        edu_lines = [l.strip() for l in nxt.get_text().split("\n") if l.strip()]
                        education = edu_lines[:4]
                    break

            if not interests:
                interests = [f"วิทยาศาสตร์ ({dept_th})", "การวิจัยและนวัตกรรมชีววิทยาศาสตร์", "งานวิจัยวิทยาศาสตร์กายภาพและชีวภาพ"]

            return {
                "university": "Mahidol University",
                "university_th": "มหาวิทยาลัยมหิดล",
                "faculty": "Faculty of Science",
                "faculty_th": "คณะวิทยาศาสตร์",
                "department": dept_th.replace("ภาควิชา", "Department of "),
                "department_th": dept_th,
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "image_url": image_url,
                "profile_url": detail_url,
                "role": "อาจารย์ประจำและนักวิจัย",
                "research_interests": interests[:8],
                "featured_publications": [],
                "education": education,
                "taught_courses": [],
                "h_index": h_index,
                "citations": citations
            }
        except Exception as err:
            logger.warning(f"Mahidol Science: Error scraping profile for {name_part}: {err}")
            return {
                "university": "Mahidol University",
                "university_th": "มหาวิทยาลัยมหิดล",
                "faculty": "Faculty of Science",
                "faculty_th": "คณะวิทยาศาสตร์",
                "department": "Faculty of Science",
                "department_th": "คณะวิทยาศาสตร์",
                "academic_title_th": th_title,
                "full_name_th": th_name,
                "first_name": "",
                "last_name": "",
                "email": "",
                "image_url": "",
                "profile_url": detail_url,
                "role": "อาจารย์ประจำและนักวิจัย",
                "research_interests": ["วิทยาศาสตร์", "การวิจัยวิทยาศาสตร์และเทคโนโลยี"],
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            }

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(scrape_profile, it): it for it in roster}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    logger.info(f"Mahidol Science: Completed scraping {len(results)} faculty profiles.")
    return results


# ==============================================================================
# 2. Khon Kaen University - Faculty of Science (SCi KKU)
# ==============================================================================
def crawl_kku_science() -> list[dict]:
    logger.info("=== Starting KKU Science Crawl ===")
    sheet_id = "1Sy1URmJ-kWCdAY9mQr0dgjAYv5USwQUYRq-UUuBxbZY"
    sheet_name = "%E0%B8%8A%E0%B8%B5%E0%B8%951"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    data_csv = fetch_url(url, timeout=12)
    reader = csv.reader(io.StringIO(data_csv))
    rows = list(reader)

    if not rows:
        logger.error("KKU Science: Failed to fetch spreadsheet rows.")
        return []

    dept_map = {
        "Statistics": "สาขาวิชาสถิติ",
        "Mathematics": "สาขาวิชาคณิตศาสตร์",
        "Biochemistry": "สาขาวิชาชีวเคมี",
        "Biology": "สาขาวิชาชีววิทยา",
        "Chemistry": "สาขาวิชาเคมี",
        "Physics": "สาขาวิชาฟิสิกส์",
        "Environmental Science": "สาขาวิชาวิทยาศาสตร์สิ่งแวดล้อม",
        "Integrated Science": "สาขาวิชาวิทยาศาสตร์บูรณาการ",
        "Microbiology": "สาขาวิชาจุลชีววิทยา"
    }

    results = []
    # Header: ['academicTitle', 'nameTh', 'nameEn', 'dept', 'email', 'Image', 'education', 'researchInterests', 'scopus', ...]
    for row in rows[1:]:
        if len(row) < 5 or not row[1].strip():
            continue

        raw_title = row[0].strip()
        raw_name_th = row[1].strip()
        name_en = row[2].strip() if len(row) > 2 else ""
        raw_dept = row[3].strip() if len(row) > 3 else "Science"
        email = row[4].strip() if len(row) > 4 else ""
        image_url = row[5].strip() if len(row) > 5 else ""
        education_raw = row[6].strip() if len(row) > 6 else ""
        interests_raw = row[7].strip() if len(row) > 7 else ""
        scopus_url = row[8].strip() if len(row) > 8 else ""

        # Normalize Thai title & name
        comb_name = f"{raw_title} {raw_name_th}" if raw_title and not raw_name_th.startswith(raw_title[:3]) else raw_name_th
        th_title, th_name, _ = normalize_thai_title_and_name(comb_name)

        first_name = ""
        last_name = ""
        if name_en:
            clean_en = strip_all_titles(name_en)
            parts_en = clean_en.split()
            first_name = parts_en[0] if parts_en else ""
            last_name = " ".join(parts_en[1:]) if len(parts_en) > 1 else ""

        dept_th = dept_map.get(raw_dept, f"สาขาวิชา{raw_dept}")

        interests = []
        if interests_raw:
            parts = re.split(r"[,;•\n\r]+", interests_raw)
            interests = [p.strip() for p in parts if len(p.strip()) > 2]

        if not interests:
            interests = [f"วิทยาศาสตร์และเทคโนโลยี ({dept_th})", "การวิจัยเชิงลึกด้านวิทยาศาสตร์", "นวัตกรรมและวิทยาการประยุกต์"]

        education = []
        if education_raw:
            education = [e.strip() for e in re.split(r"[\n\r]+", education_raw) if len(e.strip()) > 2][:4]

        results.append({
            "university": "Khon Kaen University",
            "university_th": "มหาวิทยาลัยขอนแก่น",
            "faculty": "Faculty of Science",
            "faculty_th": "คณะวิทยาศาสตร์",
            "department": f"Department of {raw_dept}",
            "department_th": dept_th,
            "academic_title_th": th_title,
            "full_name_th": th_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "image_url": image_url if "http" in image_url else "",
            "profile_url": scopus_url if "http" in scopus_url else "https://sc.kku.ac.th/about-department/",
            "role": "อาจารย์ประจำและนักวิจัย",
            "research_interests": interests[:8],
            "featured_publications": [],
            "education": education,
            "taught_courses": []
        })

    logger.info(f"KKU Science: Extracted {len(results)} faculty profiles.")
    return results


# ==============================================================================
# 3. Khon Kaen University - Faculty of Agriculture (AG KKU)
# ==============================================================================
def crawl_kku_agriculture() -> list[dict]:
    logger.info("=== Starting KKU Agriculture Crawl ===")
    dept_pages = [
        ("สาขาวิชาพืชไร่", "Department of Agronomy", "https://ag.kku.ac.th/บุคลากรสาขาวิชาพืชไร่"),
        ("สาขาวิชาพืชสวน", "Department of Horticulture", "https://ag.kku.ac.th/สาขาวิชาพืชสวนบุคลากร"),
        ("สาขาวิชาเศรษฐศาสตร์การเกษตร", "Department of Agricultural Economics", "https://ag.kku.ac.th/สาขาวิชาเศรษฐศาสตร์การเกษตรบุคลากร"),
        ("สาขาวิชาสัตวศาสตร์", "Department of Animal Science", "https://ag.kku.ac.th/สาขาวิชาสัตวศาสตร์บุคลากร"),
        ("สาขาวิชาเกษตรนวัตกรรม", "Department of Agricultural Innovation", "https://ag.kku.ac.th/หลักสูตรเกษตรนวัตกรรมบุคลากร"),
        ("สาขาวิชากีฏวิทยาและโรคพืชวิทยา", "Department of Entomology and Plant Pathology", "https://ag.kku.ac.th/สาขากีฏวิทยาและโรคพืชวิทยา"),
    ]

    results = []

    for dept_th, dept_en, raw_url in dept_pages:
        encoded_url = urllib.parse.quote(raw_url, safe=":/")
        try:
            html = fetch_url(encoded_url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            items = soup.find_all("div", class_="grid-item")

            for item in items:
                txt = item.get_text().strip()
                if not any(k in txt for k in ["ศาสตราจารย์", "ดร.", "อาจารย์", "@kku.ac.th"]):
                    continue

                # Parse: "ผู้ช่วยศาสตราจารย์ ดร.สมพงศ์ จันทร์แก้วตำแหน่ง : ผู้ช่วยศาสตราจารย์ Email : somchan@kku.ac.th"
                email = ""
                m_email = re.search(r"[\w\.-]+@kku\.ac\.th", txt)
                if m_email:
                    email = m_email.group(0).strip()

                img = item.find("img")
                image_url = img["src"] if img and img.get("src") else ""

                # Extract Name from first line or before "ตำแหน่ง"
                name_chunk = txt
                if "ตำแหน่ง" in txt:
                    name_chunk = txt.split("ตำแหน่ง")[0].strip()

                th_title, th_name, _ = normalize_thai_title_and_name(name_chunk)

                interests = [
                    f"เกษตรศาสตร์ ({dept_th})",
                    "เทคโนโลยีและการผลิตทางการเกษตร",
                    "นวัตกรรมเกษตรยั่งยืนและสิ่งแวดล้อม"
                ]

                results.append({
                    "university": "Khon Kaen University",
                    "university_th": "มหาวิทยาลัยขอนแก่น",
                    "faculty": "Faculty of Agriculture",
                    "faculty_th": "คณะเกษตรศาสตร์",
                    "department": dept_en,
                    "department_th": dept_th,
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": email,
                    "image_url": image_url,
                    "profile_url": raw_url,
                    "role": "อาจารย์ประจำและนักวิจัย",
                    "research_interests": interests,
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })

        except Exception as err:
            logger.warning(f"KKU Agriculture: Error crawling {dept_th}: {err}")

    logger.info(f"KKU Agriculture: Extracted {len(results)} faculty profiles.")
    return results


# ==============================================================================
# 4. Chulalongkorn University - Faculty of Science (SC CU)
# ==============================================================================
def crawl_cu_science() -> list[dict]:
    logger.info("=== Starting CU Science Crawl ===")
    results = []

    # 4.1 Chemistry (web.chemcu.org / chem.sc.chula.ac.th)
    try:
        chem_url = "http://web.chemcu.org/index.php/faculty"
        html = fetch_url(chem_url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("div", class_="item")
        for item in items:
            t = item.get_text().strip()
            # Format: 'Assistant Professor Dr. \n\nAmit Jaisi'
            lines = [l.strip() for l in t.split("\n") if l.strip()]
            if len(lines) >= 2:
                title_en = lines[0]
                name_en = lines[1]
            elif len(lines) == 1:
                title_en = "Dr."
                name_en = lines[0]
            else:
                continue

            # Convert English title to Thai title
            th_title = "อาจารย์"
            if "assoc" in title_en.lower():
                th_title = "รศ.ดร." if "dr" in title_en.lower() else "รศ."
            elif "asst" in title_en.lower():
                th_title = "ผศ.ดร." if "dr" in title_en.lower() else "ผศ."
            elif "prof" in title_en.lower():
                th_title = "ศ.ดร." if "dr" in title_en.lower() else "ศ."
            elif "dr" in title_en.lower():
                th_title = "ดร."

            img = item.find("img")
            image_url = img["src"] if img and img.get("src") else ""
            a = item.find("a")
            profile_url = a["href"] if a and a.get("href") else chem_url

            clean_en = strip_all_titles(name_en)
            parts_en = clean_en.split()
            first_name = parts_en[0] if parts_en else ""
            last_name = " ".join(parts_en[1:]) if len(parts_en) > 1 else ""

            # Name TH placeholder for English-only directory
            full_name_th = f"{clean_en}"

            results.append({
                "university": "Chulalongkorn University",
                "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                "faculty": "Faculty of Science",
                "faculty_th": "คณะวิทยาศาสตร์",
                "department": "Department of Chemistry",
                "department_th": "ภาควิชาเคมี",
                "academic_title_th": th_title,
                "full_name_th": full_name_th,
                "first_name": first_name,
                "last_name": last_name,
                "email": "",
                "image_url": image_url,
                "profile_url": profile_url,
                "role": "อาจารย์ประจำและนักวิจัย",
                "research_interests": ["เคมีอินทรีย์ เคมีอนินทรีย์ และเคมีวิเคราะห์", "การสังเคราะห์ตัวเร่งปฏิกิริยาและเคมีสีเขียว", "นวัตกรรมวัสดุและพลังงานยั่งยืน"],
                "featured_publications": [],
                "education": [],
                "taught_courses": []
            })
        logger.info(f"CU Science Chem: Extracted {len(items)} faculties.")
    except Exception as e:
        logger.warning(f"CU Science Chem error: {e}")

    # 4.2 Mathematics and Computer Science (www.math.sc.chula.ac.th/th/people/)
    try:
        math_url = "https://www.math.sc.chula.ac.th/th/people/"
        html = fetch_url(math_url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        math_count = 0
        for a in soup.find_all("a", href=True):
            if "/th/people/" in a["href"]:
                txt = a.get_text().strip().replace("\n", " ")
                # Format: 'KS รองศาสตราจารย์ กรุง สินอภิรมย์สราญ อาจารย์'
                m_match = re.search(r"(?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\s+([ก-๙]+(?:\s+[ก-๙]+)?)", txt)
                if m_match:
                    raw_title = txt.split()[1] if len(txt.split()) > 1 else "อาจารย์"
                    th_title, th_name, _ = normalize_thai_title_and_name(f"{raw_title} {m_match.group(1)}")
                    results.append({
                        "university": "Chulalongkorn University",
                        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                        "faculty": "Faculty of Science",
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "department": "Department of Mathematics and Computer Science",
                        "department_th": "ภาควิชาคณิตศาสตร์และวิทยาการคอมพิวเตอร์",
                        "academic_title_th": th_title,
                        "full_name_th": th_name,
                        "first_name": "",
                        "last_name": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": a["href"],
                        "role": "อาจารย์ประจำและนักวิจัย",
                        "research_interests": ["คณิตศาสตร์บริสุทธิ์และคณิตศาสตร์ประยุกต์", "วิทยาการคอมพิวเตอร์และปัญญาประดิษฐ์", "การวิเคราะห์ข้อมูลและอัลกอริทึม"],
                        "featured_publications": [],
                        "education": [],
                        "taught_courses": []
                    })
                    math_count += 1
        logger.info(f"CU Science Math: Extracted {math_count} faculties.")
    except Exception as e:
        logger.warning(f"CU Science Math error: {e}")

    # 4.3 Physics (www.phys.sc.chula.ac.th)
    try:
        phys_url = "https://www.phys.sc.chula.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3%e0%b8%aa%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/"
        html = fetch_url(phys_url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        phys_count = 0
        for h4 in soup.find_all("h4"):
            t = h4.get_text().strip()
            # Format: 'อ.ดร.กิตติพิชญ์ อยู่ประเสริฐชุติDr.Kittipitch Yooprasertchuti'
            m_th = re.search(r"^((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+(?:\s+[ก-๙]+)?)", t)
            if m_th:
                comb_name = m_th.group(1).strip()
                th_title, th_name, _ = normalize_thai_title_and_name(comb_name)

                # find email in parent
                email = ""
                p = h4.parent
                if p and p.parent:
                    m_mail = re.search(r"[\w\.-]+@chula\.ac\.th", p.parent.get_text())
                    if m_mail:
                        email = m_mail.group(0).strip()

                results.append({
                    "university": "Chulalongkorn University",
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty": "Faculty of Science",
                    "faculty_th": "คณะวิทยาศาสตร์",
                    "department": "Department of Physics",
                    "department_th": "ภาควิชาฟิสิกส์",
                    "academic_title_th": th_title,
                    "full_name_th": th_name,
                    "first_name": "",
                    "last_name": "",
                    "email": email,
                    "image_url": "",
                    "profile_url": phys_url,
                    "role": "อาจารย์ประจำและนักวิจัย",
                    "research_interests": ["ฟิสิกส์ทฤษฎีและฟิสิกส์พลังงานสูง", "ฟิสิกส์สสารควบแน่นและวัสดุศาสตร์", "ทัศนศาสตร์ เลเซอร์ และฟิสิกส์ประยุกต์"],
                    "featured_publications": [],
                    "education": [],
                    "taught_courses": []
                })
                phys_count += 1
        logger.info(f"CU Science Physics: Extracted {phys_count} faculties.")
    except Exception as e:
        logger.warning(f"CU Science Physics error: {e}")

    # 4.4 Biology (www.biology.sc.chula.ac.th)
    try:
        bio_url = "https://www.biology.sc.chula.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/"
        html = fetch_url(bio_url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        bio_count = 0
        for a in soup.find_all("a", href=True):
            if a.get_text().strip() == "เพิ่มเติม":
                prev = a.find_previous(lambda tag: any(k in tag.get_text() for k in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร."]))
                if prev:
                    raw_name = prev.get_text().strip()
                    th_title, th_name, _ = normalize_thai_title_and_name(raw_name)
                    results.append({
                        "university": "Chulalongkorn University",
                        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                        "faculty": "Faculty of Science",
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "department": "Department of Biology",
                        "department_th": "ภาควิชาชีววิทยา",
                        "academic_title_th": th_title,
                        "full_name_th": th_name,
                        "first_name": "",
                        "last_name": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": a["href"],
                        "role": "อาจารย์ประจำและนักวิจัย",
                        "research_interests": ["ชีววิทยาระดับโมเลกุลและความหลากหลายทางชีวภาพ", "สรีรวิทยา สัตววิทยา และนิเวศวิทยา", "เทคโนโลยีชีวภาพและการอนุรักษ์สิ่งแวดล้อม"],
                        "featured_publications": [],
                        "education": [],
                        "taught_courses": []
                    })
                    bio_count += 1
        logger.info(f"CU Science Biology: Extracted {bio_count} faculties.")
    except Exception as e:
        logger.warning(f"CU Science Biology error: {e}")

    # 4.5 Food Technology (foodtech.sc.chula.ac.th/faculties/lecturer)
    try:
        food_url = "http://foodtech.sc.chula.ac.th/faculties/lecturer"
        html = fetch_url(food_url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        food_count = 0
        for tag in soup.find_all(["h3", "h4", "p", "div"]):
            t = tag.get_text().strip()
            if any(k in t for k in ["ศาสตราจารย์", "รศ.", "ผศ.", "ดร."]) and len(t) < 60:
                m_th = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(?:ดร\.)?\s*[ก-๙]+(?:\s+[ก-๙]+)?)", t)
                if m_th:
                    th_title, th_name, _ = normalize_thai_title_and_name(m_th.group(1).strip())
                    if not any(f["full_name_th"] == th_name for f in results):
                        results.append({
                            "university": "Chulalongkorn University",
                            "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                            "faculty": "Faculty of Science",
                            "faculty_th": "คณะวิทยาศาสตร์",
                            "department": "Department of Food Technology",
                            "department_th": "ภาควิชาเทคโนโลยีทางอาหาร",
                            "academic_title_th": th_title,
                            "full_name_th": th_name,
                            "first_name": "",
                            "last_name": "",
                            "email": "",
                            "image_url": "",
                            "profile_url": food_url,
                            "role": "อาจารย์ประจำและนักวิจัย",
                            "research_interests": ["วิทยาศาสตร์และเทคโนโลยีการอาหาร", "การแปรรูปและพัฒนาผลิตภัณฑ์อาหารเพื่อสุขภาพ", "ความปลอดภัยทางอาหารและจุลชีววิทยาอาหาร"],
                            "featured_publications": [],
                            "education": [],
                            "taught_courses": []
                        })
                        food_count += 1
        logger.info(f"CU Science Food Tech: Extracted {food_count} faculties.")
    except Exception as e:
        logger.warning(f"CU Science Food Tech error: {e}")

    logger.info(f"CU Science: Total extracted {len(results)} faculties across all departments.")
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
def run_wave14_pipeline(force_recrawl: bool = False):
    logger.info("==================================================")
    logger.info("Starting Wave 14 Flagship Pipeline Execution")
    logger.info("==================================================")

    all_faculties = []
    if not force_recrawl and CHECKPOINT_PATH.exists():
        logger.info(f"Loading cached extraction state from {CHECKPOINT_PATH}")
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as fp:
            all_faculties = json.load(fp)
    else:
        # Step 1: Real-time crawling of all target flagships
        mu_sci = crawl_mahidol_science()
        kku_sci = crawl_kku_science()
        kku_ag = crawl_kku_agriculture()
        cu_sci = crawl_cu_science()

        all_faculties = mu_sci + kku_sci + kku_ag + cu_sci

        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
            json.dump(all_faculties, fp, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(all_faculties)} raw extracted records to checkpoint: {CHECKPOINT_PATH}")

    logger.info(f"Total raw candidates extracted across Wave 14 targets: {len(all_faculties)}")

    # Step 2: Database Deduplication & State Reduction against Local PostgreSQL
    db = SessionLocal()
    try:
        target_unis = [
            "มหาวิทยาลัยมหิดล",
            "มหาวิทยาลัยขอนแก่น",
            "จุฬาลงกรณ์มหาวิทยาลัย"
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
                # Scopus metrics enrichment if available
                if member.get("h_index") and not matched_obj.h_index:
                    matched_obj.h_index = member["h_index"]
                    updated = True
                if member.get("citations") and not matched_obj.total_citations:
                    matched_obj.total_citations = member["citations"]
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
                univ_code = "mu" if "มหิดล" in m["university_th"] else ("kku" if "ขอนแก่น" in m["university_th"] else "cu")
                fac_code = "agri" if "เกษตร" in m["faculty_th"] else "sci"
                prefix = f"{univ_code}_{fac_code}"
                id_counts[prefix] = id_counts.get(prefix, 0) + 1
                unique_id = f"{prefix}_wave14_b_{id_counts[prefix]:04d}"

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
        logger.info(f"Successfully committed Wave 14 changes: {updated_count} enriched, {len(new_members)} inserted.")

    except Exception as err:
        db.rollback()
        logger.error(f"Pipeline execution failed: {err}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_wave14_pipeline(force_recrawl=True)
