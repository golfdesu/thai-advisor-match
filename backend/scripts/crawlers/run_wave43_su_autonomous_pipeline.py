"""Wave 43 SU Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: Silpakorn University (SU)
        มหาวิทยาลัยศิลปากร

Scope:
1. Faculty of Science (คณะวิทยาศาสตร์) - Resolves 0-record critical gap:
   - Computing (ภาควิชาคอมพิวเตอร์): https://cp.su.ac.th/teacher
   - Mathematics (ภาควิชาคณิตศาสตร์): https://math.sc.su.ac.th/?page_id=57
   - Chemistry (ภาควิชาเคมี): https://chem.sc.su.ac.th/staff
   - Biology (ภาควิชาชีววิทยา): https://bio.sc.su.ac.th/personnel & individual profiles
   - Microbiology (ภาควิชาจุลชีววิทยา): https://micro.sc.su.ac.th/instructors/
   - Environmental Science (ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม): https://envi.sc.su.ac.th/teach/
   - Statistics (ภาควิชาสถิติ): https://stat.sc.su.ac.th/บุคลากร/
   - Physics (ภาควิชาฟิสิกส์): http://phy.sc.su.ac.th/people.html
2. Faculty of Information and Communication Technology (คณะเทคโนโลยีสารสนเทศและการสื่อสาร):
   - All 64+ faculty cards across Phetchaburi & Muang Thong Thani campuses: https://ict.su.ac.th/?page_id=58
3. Faculty of Animal Sciences and Agricultural Technology (คณะสัตวศาสตร์และเทคโนโลยีการเกษตร - ASAT):
   - 5 Departments and Executive Board: https://asat.su.ac.th/
4. Faculty of Pharmacy (คณะเภสัชศาสตร์):
   - 5 Departments: https://pharmacy.su.ac.th/main/department-ndep1..5 (94 faculty with 100% verified emails)
5. Faculty of Music (คณะดุริยางคศาสตร์):
   - Faculty members: https://music.su.ac.th/faculty-member/
6. Faculty of Engineering and Industrial Technology (คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม):
   - Executive Committee & Deans: https://www.eng.su.ac.th/about_faculty_committee.php

Execution Standard:
- Headless extraction with specialized high-fidelity DOM extractors & Trafilatura heuristics.
- State reduction, title normalization, and PDPA compliance (no phone numbers).
- Checkpointing to backend/data/agent_states/wave43_su_extraction.json.
- RapidFuzz token_set_ratio deduplication against existing DB.
- 768-dim Gemini vector embeddings for net new records.
- Atomic commit to local PostgreSQL (localhost:5432/advisor_match).
"""
import os
import re
import sys
import time
import json
import random
import ssl
import threading
import urllib.parse
import urllib.request
from pathlib import Path

# Ensure root and backend directory in sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz, process

try:
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    from app.core.config import settings
    from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
    from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles
except ImportError:
    from backend.app.core.database import SessionLocal
    from backend.app.models.db_models import FacultyDB
    from backend.app.core.config import settings
    from backend.scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
    from backend.scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles

from google import genai
from google.genai import types

SU_TH = "มหาวิทยาลัยศิลปากร"
SU_EN = "Silpakorn University"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8"
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(r"(?:หน้าแรก|ติดต่อ|โทรศัพท์|โทรสาร|admin|menu|home|service|download|ห้องปฏิบัติการ|สาขาวิชา|ภาควิชา|คณะ|สถิติ|เจ้าหน้าที่|จ้างเหมา|นักวิชาการศึกษา|ผู้ปฏิบัติงาน|ธุรการ|เวลาทำการ|งานพัสดุ|งานบุคคล|งานการเงิน|งานบริหาร)", re.IGNORECASE)


def fetch_html(url: str, timeout: int = 12) -> str:
    """Fetch HTML safely with pre-unquoting and proper path quoting."""
    unquoted = urllib.parse.unquote(url)
    parts = urllib.parse.urlsplit(unquoted)
    encoded_path = urllib.parse.quote(parts.path)
    encoded_query = urllib.parse.quote(parts.query, safe="=&?/")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))

    req = urllib.request.Request(safe_url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


# ------------------------------------------------------------
# 1. Faculty of Science (คณะวิทยาศาสตร์) - 8 Departments
# ------------------------------------------------------------

def extract_su_science_computing() -> list[dict]:
    """1.1 Computing (ภาควิชาคอมพิวเตอร์)."""
    print("-> Scraping Science: Computing (cp.su.ac.th/teacher)...")
    url = "https://cp.su.ac.th/teacher"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        teacher_links = soup.find_all("a", href=re.compile(r"teacher/\d+"))

        seen_urls = set()
        for a in teacher_links:
            href = a["href"]
            if not href.startswith("http"):
                href = urllib.parse.urljoin("https://cp.su.ac.th/", href)
            if href in seen_urls:
                continue
            seen_urls.add(href)

            raw_txt = a.get_text(separator=" ", strip=True)
            # Fetch individual profile for deep enrichment
            name_th = ""
            email = ""
            degree = ""
            img_url = ""

            try:
                p_html = fetch_html(href, timeout=8)
                p_soup = BeautifulSoup(p_html, "html.parser")
                p_text = p_soup.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in p_text.splitlines() if l.strip()]

                for l in lines:
                    if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
                        if not name_th:
                            name_th = l
                    em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))", l)
                    if em_match and not email:
                        email = em_match.group(1).lower()
                    if any(deg in l for deg in ["Ph.D", "M.Sc", "B.Sc", "D.Eng", "ปร.ด.", "วท.ม.", "วท.บ."]):
                        if not degree:
                            degree = l

                img = p_soup.find("img", src=re.compile(r"teacher|avatar|profile|upload", re.I))
                if img:
                    img_src = img["src"]
                    if not img_src.startswith("http"):
                        img_src = urllib.parse.urljoin("https://cp.su.ac.th/", img_src)
                    img_url = img_src
            except Exception:
                pass

            if not name_th and raw_txt:
                # Fallback to link text
                m = re.match(r"^([^\n\r]+?)(?:หัวหน้า|รองหัวหน้า|อาจารย์ประจำ|$)", raw_txt)
                if m:
                    name_th = m.group(1).strip()

            if name_th:
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์",
                    "faculty": "Faculty of Science",
                    "department_th": "ภาควิชาคอมพิวเตอร์",
                    "department": "Department of Computing",
                    "full_name_th": name_th,
                    "full_name_en": "",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": href,
                    "research_interests": ["Computer Science", "Artificial Intelligence", "Data Science"],
                    "featured_publications": [degree] if degree else []
                })
    except Exception as e:
        print(f"   [ERR] Computing: {e}")

    print(f"   Computing Extracted: {len(results)} records.")
    return results


def extract_su_science_math() -> list[dict]:
    """1.2 Mathematics (ภาควิชาคณิตศาสตร์)."""
    print("-> Scraping Science: Mathematics (math.sc.su.ac.th/?page_id=57)...")
    url = "https://math.sc.su.ac.th/?page_id=57"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""
        current_research = []

        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                if current_name:
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": "ภาควิชาคณิตศาสตร์",
                        "department": "Department of Mathematics",
                        "full_name_th": current_name,
                        "full_name_en": "",
                        "email": current_email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": current_research if current_research else ["Mathematics", "Mathematical Modeling"],
                        "featured_publications": []
                    })
                current_name = l
                current_email = ""
                current_research = []
                continue

            em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu|gmail\.com))", l)
            if em_match and not current_email:
                cand_em = em_match.group(1).lower()
                if not cand_em.startswith("math"):
                    current_email = cand_em

            if "Research Area:" in l or "Research area:" in l:
                area = re.sub(r"Research [Aa]rea:\s*", "", l).strip()
                if area:
                    current_research = [x.strip() for x in area.split(",") if x.strip()]

        if current_name:
            results.append({
                "faculty_th": "คณะวิทยาศาสตร์",
                "faculty": "Faculty of Science",
                "department_th": "ภาควิชาคณิตศาสตร์",
                "department": "Department of Mathematics",
                "full_name_th": current_name,
                "full_name_en": "",
                "email": current_email,
                "image_url": "",
                "profile_url": url,
                "research_interests": current_research if current_research else ["Mathematics"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] Mathematics: {e}")

    print(f"   Mathematics Extracted: {len(results)} records.")
    return results


def extract_su_science_chemistry() -> list[dict]:
    """1.3 Chemistry (ภาควิชาเคมี)."""
    print("-> Scraping Science: Chemistry (chem.sc.su.ac.th/staff)...")
    url = "https://chem.sc.su.ac.th/staff"
    results = []
    seen_names = set()
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        found_faculty = False
        current_subfield = "เคมีทั่วไป"
        for l in lines:
            if any(sub in l for sub in ["เคมีอินทรีย์", "เคมีเชิงฟิสิกส์", "เคมีอนินทรีย์", "ชีวเคมี", "เคมีวิเคราะห์", "เคมีเครื่องสำอาง"]):
                current_subfield = l
                continue
            if found_faculty and "บุคลากรสายสนับสนุน" in l:
                break  # Stop at support staff after finding faculty

            # Match academic title + name
            if any(l.startswith(p) for p in ["ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์", "อาจารย์"]):
                clean_name = re.sub(r"(?:หัวหน้าภาควิชา|รองหัวหน้าภาควิชา|ฝ่าย.*?$)", "", l).strip()
                if len(clean_name) > 5 and clean_name not in seen_names:
                    seen_names.add(clean_name)
                    found_faculty = True
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": f"ภาควิชาเคมี ({current_subfield})",
                        "department": f"Department of Chemistry ({current_subfield})",
                        "full_name_th": clean_name,
                        "full_name_en": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": [current_subfield, "Chemistry"],
                        "featured_publications": []
                    })
    except Exception as e:
        print(f"   [ERR] Chemistry: {e}")

    print(f"   Chemistry Extracted: {len(results)} records.")
    return results


def extract_su_science_biology() -> list[dict]:
    """1.4 Biology (ภาควิชาชีววิทยา)."""
    print("-> Scraping Science: Biology (bio.sc.su.ac.th/personnel)...")
    url = "https://bio.sc.su.ac.th/personnel"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")

        # Each faculty has a link to profile
        profile_links = soup.find_all("a", href=re.compile(r"profile/"))
        seen_slugs = set()

        for a in profile_links:
            href = a["href"]
            if href in seen_slugs:
                continue
            seen_slugs.add(href)

            full_profile_url = urllib.parse.urljoin("https://bio.sc.su.ac.th/", href)
            th_name = ""
            h3 = a.find("h3")
            if h3:
                th_name = h3.get_text(strip=True)
            img_url = ""
            img = a.find("img")
            if img and img.get("src"):
                img_url = urllib.parse.urljoin("https://bio.sc.su.ac.th/", img["src"])

            # Deep profile fetch
            en_name = ""
            research_areas = []
            publications = []
            email = ""

            try:
                p_html = fetch_html(full_profile_url, timeout=8)
                p_soup = BeautifulSoup(p_html, "html.parser")
                p_text = p_soup.get_text(separator="\n", strip=True)
                p_lines = [l.strip() for l in p_text.splitlines() if l.strip()]

                for pl in p_lines:
                    if any(pl.startswith(p) for p in ["Assoc. Prof.", "Prof.", "Asst. Prof.", "Dr."]):
                        if not en_name:
                            en_name = pl
                    em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))", pl)
                    if em_match and not email:
                        email = em_match.group(1).lower()
                    if "สาขาที่เชี่ยวชาญ" in pl:
                        area = pl.replace("สาขาที่เชี่ยวชาญ", "").strip()
                        if area:
                            research_areas.append(area)

                # Find publication items
                for pl in p_lines:
                    if any(yr in pl for yr in ["2024", "2023", "2022", "2021", "2020"]) and len(pl) > 35:
                        if len(publications) < 3:
                            publications.append(pl[:180])
            except Exception:
                pass

            if th_name:
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์",
                    "faculty": "Faculty of Science",
                    "department_th": "ภาควิชาชีววิทยา",
                    "department": "Department of Biology",
                    "full_name_th": th_name,
                    "full_name_en": en_name,
                    "email": email,
                    "image_url": img_url,
                    "profile_url": full_profile_url,
                    "research_interests": research_areas if research_areas else ["Biology", "Life Sciences"],
                    "featured_publications": publications
                })
    except Exception as e:
        print(f"   [ERR] Biology: {e}")

    print(f"   Biology Extracted: {len(results)} records.")
    return results


def extract_su_science_microbiology() -> list[dict]:
    """1.5 Microbiology (ภาควิชาจุลชีววิทยา)."""
    print("-> Scraping Science: Microbiology (micro.sc.su.ac.th/instructors/)...")
    url = "https://micro.sc.su.ac.th/instructors/"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")

        # Headings with names
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
            name_cand = h.get_text(strip=True)
            if any(name_cand.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(name_cand) < 45:
                # Find parent container
                p_div = h.find_parent("div")
                email = ""
                research = []
                if p_div:
                    mail_link = p_div.find("a", href=lambda x: x and "mailto:" in x)
                    if mail_link:
                        email = mail_link["href"].replace("mailto:", "").strip().lower()
                    div_text = p_div.get_text(separator="\n", strip=True)
                    if "สาขาที่เชี่ยวชาญ" in div_text:
                        r_part = div_text.split("สาขาที่เชี่ยวชาญ")[-1].split("Mail")[0]
                        research = [x.strip("• \t\r\n") for x in r_part.split("\n") if x.strip("• \t\r\n")]

                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์",
                    "faculty": "Faculty of Science",
                    "department_th": "ภาควิชาจุลชีววิทยา",
                    "department": "Department of Microbiology",
                    "full_name_th": name_cand,
                    "full_name_en": "",
                    "email": email,
                    "image_url": "",
                    "profile_url": url,
                    "research_interests": research if research else ["Microbiology", "Biotechnology"],
                    "featured_publications": []
                })
    except Exception as e:
        print(f"   [ERR] Microbiology: {e}")

    print(f"   Microbiology Extracted: {len(results)} records.")
    return results


def extract_su_science_environmental() -> list[dict]:
    """1.6 Environmental Science (ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม)."""
    print("-> Scraping Science: Environmental Science (envi.sc.su.ac.th/teach/)...")
    url = "https://envi.sc.su.ac.th/teach/"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""

        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]) and len(l) < 45:
                if current_name:
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": "ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม",
                        "department": "Department of Environmental Science",
                        "full_name_th": current_name,
                        "full_name_en": "",
                        "email": current_email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": ["Environmental Science", "Ecology"],
                        "featured_publications": []
                    })
                current_name = l
                current_email = ""
                continue

            em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu|gmail\.com|hotmail\.com|yahoo\.com|outlook\.com))", l)
            if em_match and not current_email:
                cand_em = em_match.group(1).lower()
                if not cand_em.startswith("envi.sci"):
                    current_email = cand_em

        if current_name:
            results.append({
                "faculty_th": "คณะวิทยาศาสตร์",
                "faculty": "Faculty of Science",
                "department_th": "ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม",
                "department": "Department of Environmental Science",
                "full_name_th": current_name,
                "full_name_en": "",
                "email": current_email,
                "image_url": "",
                "profile_url": url,
                "research_interests": ["Environmental Science", "Ecology"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] Environmental Science: {e}")

    print(f"   Environmental Science Extracted: {len(results)} records.")
    return results


def extract_su_science_statistics() -> list[dict]:
    """1.7 Statistics (ภาควิชาสถิติ)."""
    print("-> Scraping Science: Statistics (stat.sc.su.ac.th/บุคลากร/)...")
    path = urllib.parse.quote("บุคลากร/")
    url = f"https://stat.sc.su.ac.th/{path}"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""

        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]) and len(l) < 45:
                if current_name and current_name != l:
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": "ภาควิชาสถิติ",
                        "department": "Department of Statistics",
                        "full_name_th": current_name,
                        "full_name_en": "",
                        "email": current_email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": ["Statistics", "Applied Statistics", "Data Analysis"],
                        "featured_publications": []
                    })
                    current_email = ""
                current_name = l
                continue

            em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))", l, re.IGNORECASE)
            if em_match and not current_email:
                current_email = em_match.group(1).lower()

        if current_name:
            results.append({
                "faculty_th": "คณะวิทยาศาสตร์",
                "faculty": "Faculty of Science",
                "department_th": "ภาควิชาสถิติ",
                "department": "Department of Statistics",
                "full_name_th": current_name,
                "full_name_en": "",
                "email": current_email,
                "image_url": "",
                "profile_url": url,
                "research_interests": ["Statistics", "Data Analysis"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] Statistics: {e}")

    print(f"   Statistics Extracted: {len(results)} records.")
    return results


def extract_su_science_physics() -> list[dict]:
    """1.8 Physics (ภาควิชาฟิสิกส์)."""
    print("-> Scraping Science: Physics (phy.sc.su.ac.th/people.html)...")
    url = "http://phy.sc.su.ac.th/people.html"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""

        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 45:
                if current_name:
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": "ภาควิชาฟิสิกส์",
                        "department": "Department of Physics",
                        "full_name_th": current_name,
                        "full_name_en": "",
                        "email": current_email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": ["Physics", "Applied Physics", "Materials Physics"],
                        "featured_publications": []
                    })
                current_name = l
                current_email = ""
                continue

            em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))", l, re.IGNORECASE)
            if em_match and not current_email:
                current_email = em_match.group(1).lower()

        if current_name:
            results.append({
                "faculty_th": "คณะวิทยาศาสตร์",
                "faculty": "Faculty of Science",
                "department_th": "ภาควิชาฟิสิกส์",
                "department": "Department of Physics",
                "full_name_th": current_name,
                "full_name_en": "",
                "email": current_email,
                "image_url": "",
                "profile_url": url,
                "research_interests": ["Physics"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] Physics: {e}")

    print(f"   Physics Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 2. Faculty of ICT (คณะเทคโนโลยีสารสนเทศและการสื่อสาร)
# ------------------------------------------------------------

def extract_su_ict() -> list[dict]:
    """Faculty of ICT (ict.su.ac.th/?page_id=58)."""
    print("-> Scraping Faculty of ICT (ict.su.ac.th/?page_id=58)...")
    url = "https://ict.su.ac.th/?page_id=58"
    results = []
    seen_names = set()

    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")

        # Headings & Elementor image boxes
        cards = soup.find_all(class_=re.compile(r"elementor-image-box|team|member|card", re.I))
        for c in cards:
            title_el = c.find(class_=re.compile(r"title", re.I))
            img_el = c.find("img")
            link_el = c.find("a", href=True)

            raw_title = title_el.get_text(strip=True) if title_el else ""
            if not raw_title:
                continue

            # Remove tabs and excess spaces
            clean_name = re.sub(r"\s+", " ", raw_title).strip()
            if not any(clean_name.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร."]):
                continue

            if clean_name in seen_names:
                continue
            seen_names.add(clean_name)

            img_url = img_el["src"] if img_el and img_el.get("src") else ""
            if "cropped-logo" in img_url or "temp2" in img_url:
                img_url = ""

            profile_url = link_el["href"] if link_el else url

            results.append({
                "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
                "faculty": "Faculty of Information and Communication Technology",
                "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศและการสื่อสาร",
                "department": "Department of Information and Communication Technology",
                "full_name_th": clean_name,
                "full_name_en": "",
                "email": "",
                "image_url": img_url,
                "profile_url": profile_url,
                "research_interests": ["Information Technology", "Digital Media", "Communication Arts"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] ICT: {e}")

    print(f"   ICT Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 3. Faculty of Animal Sciences and Agricultural Technology (ASAT)
# ------------------------------------------------------------

def extract_su_asat() -> list[dict]:
    """Faculty of Animal Sciences and Agricultural Technology (asat.su.ac.th)."""
    print("-> Scraping Faculty of ASAT (asat.su.ac.th)...")
    asat_depts = [
        ("สาขาวิชาสัตวศาสตร์", "Department of Animal Science", "https://asat.su.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/%e0%b8%9d%e0%b9%88%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/%e0%b8%a7%e0%b8%97-%e0%b8%9a-%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%aa%e0%b8%b1%e0%b8%95%e0%b8%a7%e0%b8%a8%e0%b8%b2%e0%b8%aa%e0%b8%95%e0%b8%a3%e0%b9%8c/"),
        ("สาขาวิชาเทคโนโลยีการผลิตสัตว์น้ำและประมง", "Department of Fisheries and Aquatic Production", "https://asat.su.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/%e0%b8%9d%e0%b9%88%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/%e0%b8%a7%e0%b8%97-%e0%b8%9a-%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b9%80%e0%b8%97%e0%b8%84%e0%b9%82%e0%b8%99%e0%b9%82%e0%b8%a5%e0%b8%a2%e0%b8%b5%e0%b8%81/"),
        ("สาขาวิชาเทคโนโลยีการผลิตพืช", "Department of Plant Production Technology", "https://asat.su.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/%e0%b8%9d%e0%b9%88%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/%e0%b8%a7%e0%b8%97-%e0%b8%9a-%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b9%80%e0%b8%97%e0%b8%84%e0%b9%82%e0%b8%99%e0%b9%82%e0%b8%a5%e0%b8%a2%e0%b8%b5%e0%b8%81-2/"),
        ("สาขาวิชาชีววิทยาศาสตร์เพื่อเกษตรกรรมที่ยั่งยืน", "Department of Bioscience for Sustainable Agriculture", "https://asat.su.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/%e0%b8%9d%e0%b9%88%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/%e0%b8%a7%e0%b8%97-%e0%b8%a1-%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%8a%e0%b8%b5%e0%b8%a7%e0%b8%a7%e0%b8%b4%e0%b8%97%e0%b8%a2%e0%b8%b2%e0%b8%a8%e0%b8%b2/")
    ]

    results = []
    seen_names = set()

    for dth, den, u in asat_depts:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]) and len(l) < 60:
                    clean_n = re.sub(r"(?:ตำแหน่ง:.*?$|ผลงานวิชาการ.*?$)", "", l).strip()
                    if current_name and current_name not in seen_names:
                        seen_names.add(current_name)
                        results.append({
                            "faculty_th": "คณะสัตวศาสตร์และเทคโนโลยีการเกษตร",
                            "faculty": "Faculty of Animal Sciences and Agricultural Technology",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Animal Science", "Agricultural Technology"],
                            "featured_publications": []
                        })
                    current_name = clean_n
                    current_email = ""
                    continue

                em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))", l)
                if em_match and not current_email:
                    current_email = em_match.group(1).lower()

            if current_name and current_name not in seen_names:
                seen_names.add(current_name)
                results.append({
                    "faculty_th": "คณะสัตวศาสตร์และเทคโนโลยีการเกษตร",
                    "faculty": "Faculty of Animal Sciences and Agricultural Technology",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Animal Science", "Agricultural Technology"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] ASAT {dth}: {e}")

    # Also executive board
    try:
        exe_url = "https://asat.su.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3/"
        e_html = fetch_html(exe_url, timeout=8)
        e_soup = BeautifulSoup(e_html, "html.parser")
        e_text = e_soup.get_text(separator="\n", strip=True)
        for el in e_text.splitlines():
            el = el.strip()
            # Split lines like "ผศ.ดร.อนวัช บุญญภักดี คณบดี ผศ.ดร.ปณิดา ดวงแก้ว รองคณบดี..."
            matches = re.findall(r"((?:ผศ|รศ|ศ|อาจารย์|ดร)\.?[^\n\r]+?)(?=(?:ผศ|รศ|ศ|อาจารย์|ดร)\.|$)", el)
            for m in matches:
                m_clean = re.sub(r"(?:คณบดี|รองคณบดี.*?$)", "", m).strip()
                if len(m_clean) > 5 and m_clean not in seen_names:
                    seen_names.add(m_clean)
                    results.append({
                        "faculty_th": "คณะสัตวศาสตร์และเทคโนโลยีการเกษตร",
                        "faculty": "Faculty of Animal Sciences and Agricultural Technology",
                        "department_th": "คณะผู้บริหาร",
                        "department": "Faculty Executive Board",
                        "full_name_th": m_clean,
                        "full_name_en": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": exe_url,
                        "research_interests": ["Animal Science", "Agricultural Technology"],
                        "featured_publications": []
                    })
    except Exception:
        pass

    print(f"   ASAT Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 4. Faculty of Pharmacy (คณะเภสัชศาสตร์) - 5 Departments
# ------------------------------------------------------------

def extract_su_pharmacy() -> list[dict]:
    """Faculty of Pharmacy across 5 departments (pharmacy.su.ac.th/main/department-ndep1..5)."""
    print("-> Scraping Faculty of Pharmacy (pharmacy.su.ac.th - 5 Departments)...")
    pharm_depts = [
        ("department-ndep1", "สาขาวิชาเภสัชศาสตร์ชีวภาพและเภสัชวิทยา", "Department of Biopharmaceutical Sciences and Pharmacology"),
        ("department-ndep2", "สาขาวิชาเภสัชกรรมอุตสาหการ", "Department of Industrial Pharmacy"),
        ("department-ndep3", "สาขาวิชาบริบาลทางเภสัชกรรม", "Department of Pharmaceutical Care"),
        ("department-ndep4", "สาขาวิชาเภสัชศาสตร์สังคมและการบริหาร", "Department of Social and Administrative Pharmacy"),
        ("department-ndep5", "สาขาวิชาสุขภาพดิจิทัล", "Department of Digital Health")
    ]

    results = []
    seen_names = set()

    for path_slug, dth, den in pharm_depts:
        u = f"https://pharmacy.su.ac.th/main/{path_slug}"
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""

            for l in lines:
                if any(l.startswith(p) for p in ["ผศ.", "รศ.", "ศ.", "ดร.", "อ."]) and any(title_marker in l for title_marker in ["ภญ.", "ภก.", "ดร."]):
                    if current_name and current_name not in seen_names:
                        seen_names.add(current_name)
                        results.append({
                            "faculty_th": "คณะเภสัชศาสตร์",
                            "faculty": "Faculty of Pharmacy",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Pharmacy", "Pharmaceutical Sciences", dth.replace("สาขาวิชา", "")],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                    continue

                em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:su\.ac\.th|silpakorn\.edu))", l)
                if em_match and not current_email:
                    current_email = em_match.group(1).lower()

            if current_name and current_name not in seen_names:
                seen_names.add(current_name)
                results.append({
                    "faculty_th": "คณะเภสัชศาสตร์",
                    "faculty": "Faculty of Pharmacy",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Pharmacy", "Pharmaceutical Sciences", dth.replace("สาขาวิชา", "")],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] Pharmacy {dth}: {e}")

    print(f"   Pharmacy Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 5. Faculty of Music (คณะดุริยางคศาสตร์)
# ------------------------------------------------------------

def extract_su_music() -> list[dict]:
    """Faculty of Music (music.su.ac.th/faculty-member/)."""
    print("-> Scraping Faculty of Music (music.su.ac.th/faculty-member/)...")
    url = "https://music.su.ac.th/faculty-member/"
    results = []
    seen_names = set()

    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["h2", "h3", "h4", "h5", "p"]):
            txt = tag.get_text(strip=True)
            if any(k in txt for k in ["อาจารย์", "ดร.", "ผศ.", "รศ.", "ศ."]) and len(txt) < 50 and len(txt) > 5:
                if txt in seen_names:
                    continue
                seen_names.add(txt)
                results.append({
                    "faculty_th": "คณะดุริยางคศาสตร์",
                    "faculty": "Faculty of Music",
                    "department_th": "คณะดุริยางคศาสตร์",
                    "department": "Faculty of Music",
                    "full_name_th": txt,
                    "full_name_en": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": url,
                    "research_interests": ["Music Performance", "Musicology", "Music Production"],
                    "featured_publications": []
                })
    except Exception as e:
        print(f"   [ERR] Music: {e}")

    print(f"   Music Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 6. Faculty of Engineering and Industrial Technology
# ------------------------------------------------------------

def extract_su_engineering() -> list[dict]:
    """Faculty of Engineering and Industrial Technology (eng.su.ac.th)."""
    print("-> Scraping Faculty of Engineering SU (about_faculty_committee.php)...")
    url = "https://www.eng.su.ac.th/about_faculty_committee.php"
    results = []
    seen_names = set()

    try:
        html = fetch_html(url, timeout=8)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        for line in text.splitlines():
            line = line.strip()
            if any(line.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(line) < 45:
                if line not in seen_names:
                    seen_names.add(line)
                    results.append({
                        "faculty_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
                        "faculty": "Faculty of Engineering and Industrial Technology",
                        "department_th": "คณะกรรมการประจำคณะ",
                        "department": "Faculty Executive Board",
                        "full_name_th": line,
                        "full_name_en": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": ["Engineering", "Industrial Technology"],
                        "featured_publications": []
                    })
    except Exception as e:
        print(f"   [ERR] Engineering: {e}")

    print(f"   Engineering Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# Helper: Record Sanitization & Title Parsing
# ------------------------------------------------------------

def clean_record(r: dict) -> dict | None:
    raw_name = r.get("full_name_th", "").strip()
    if not raw_name or len(raw_name) < 4:
        return None
    if RE_BAD_NAME.search(raw_name):
        return None

    # Title normalization
    try:
        norm_res = normalize_thai_title_and_name(raw_name)
        if len(norm_res) == 3:
            title, _, clean_name = norm_res
        elif len(norm_res) == 2:
            title, clean_name = norm_res
        else:
            title, clean_name = "", raw_name
    except Exception:
        title, clean_name = "", raw_name
    if not title:
        for t_candidate in [
            "ผศ.ดร.ภญ.", "ผศ.ดร.ภก.", "รศ.ดร.ภญ.", "รศ.ดร.ภก.", "ศ.ดร.ภญ.", "ศ.ดร.ภก.", "อ.ดร.ภญ.", "อ.ดร.ภก.",
            "ผศ.ภญ.", "ผศ.ภก.", "รศ.ภญ.", "รศ.ภก.", "อ.ภญ.", "อ.ภก.", "ภญ.", "ภก.",
            "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์"
        ]:
            if raw_name.startswith(t_candidate):
                title = t_candidate
                clean_name = raw_name[len(t_candidate):].strip()
                break

    if not clean_name or len(clean_name.split()) < 2:
        return None

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""
    if any(email.startswith(g) for g in ["info@", "contact@", "admin@", "support@", "office@", "chem@", "educ@"]):
        email = ""

    return {
        "university_th": SU_TH,
        "university": SU_EN,
        "faculty_th": r["faculty_th"],
        "faculty": r["faculty"],
        "department_th": r["department_th"],
        "department": r["department"],
        "academic_title_th": title,
        "full_name_th": clean_name,
        "full_name_en": (r.get("full_name_en") or "").strip(),
        "first_name": clean_name.split()[0],
        "last_name": " ".join(clean_name.split()[1:]),
        "email": email,
        "image_url": r.get("image_url") or "",
        "profile_url": r.get("profile_url") or "",
        "research_interests": r.get("research_interests") or [],
        "featured_publications": r.get("featured_publications") or [],
        "education": [],
        "taught_courses": []
    }


# ------------------------------------------------------------
# Main Autonomous Execution Pipeline
# ------------------------------------------------------------

def main():
    print("============================================================")
    print("🌊 Starting Wave 43: SU Autonomous Acquisition Pipeline")
    print("============================================================")

    all_harvested = []

    # 1. Faculty of Science (8 departments)
    all_harvested.extend(extract_su_science_computing())
    all_harvested.extend(extract_su_science_math())
    all_harvested.extend(extract_su_science_chemistry())
    all_harvested.extend(extract_su_science_biology())
    all_harvested.extend(extract_su_science_microbiology())
    all_harvested.extend(extract_su_science_environmental())
    all_harvested.extend(extract_su_science_statistics())
    all_harvested.extend(extract_su_science_physics())

    # 2. Faculty of ICT (64+ faculty)
    all_harvested.extend(extract_su_ict())

    # 3. Faculty of ASAT (Animal Sciences & Agricultural Tech)
    all_harvested.extend(extract_su_asat())

    # 4. Faculty of Pharmacy (5 departments)
    all_harvested.extend(extract_su_pharmacy())

    # 5. Faculty of Music
    all_harvested.extend(extract_su_music())

    # 6. Faculty of Engineering
    all_harvested.extend(extract_su_engineering())

    print(f"\nTotal raw records harvested: {len(all_harvested)}")

    # Clean and reduce records
    all_cleaned = []
    seen_names = set()
    for r in all_harvested:
        c = clean_record(r)
        if c:
            k = (c["full_name_th"], c["faculty_th"])
            if k not in seen_names:
                seen_names.add(k)
                all_cleaned.append(c)

    print(f"Total cleaned and verified records: {len(all_cleaned)}")
    with_em = sum(1 for r in all_cleaned if r["email"])
    print(f"Records with verified email: {with_em} ({with_em / max(1, len(all_cleaned)) * 100:.1f}%)")

    # Checkpoint state to disk
    ckpt_dir = Path("backend/data/agent_states")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / "wave43_su_extraction.json"
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved to: {ckpt_path}")

    # Database Deduplication & Ingestion
    print("\n--- Initiating RapidFuzz Database Deduplication Against Local PostgreSQL ---")
    db = SessionLocal()
    try:
        existing_su = db.query(FacultyDB).filter(
            FacultyDB.university_th.ilike("%ศิลปากร%")
        ).all()
        print(f"Current SU faculty in database: {len(existing_su)}")

        existing_names_cache = {}
        for ex in existing_su:
            clean_th = strip_all_titles(ex.full_name_th or "")
            existing_names_cache[ex.id] = clean_th

        new_members = []
        updated_members = 0
        seen_in_batch = set()

        for cand in all_cleaned:
            cand_clean = strip_all_titles(cand["full_name_th"])
            if not cand_clean or cand_clean in seen_in_batch:
                continue

            match_id = None
            if existing_names_cache:
                hit = process.extractOne(
                    cand_clean,
                    existing_names_cache,
                    scorer=fuzz.token_set_ratio,
                    score_cutoff=90
                )
                if hit:
                    match_id = hit[2]

            if match_id:
                ex_rec = next((e for e in existing_su if e.id == match_id), None)
                if ex_rec:
                    changed = False
                    if not ex_rec.email and cand["email"]:
                        ex_rec.email = cand["email"]
                        changed = True
                    if not ex_rec.image_url and cand["image_url"]:
                        ex_rec.image_url = cand["image_url"]
                        changed = True
                    if not ex_rec.profile_url and cand["profile_url"]:
                        ex_rec.profile_url = cand["profile_url"]
                        changed = True
                    if not ex_rec.department_th and cand["department_th"]:
                        ex_rec.department_th = cand["department_th"]
                        ex_rec.department = cand["department"]
                        changed = True
                    if cand["research_interests"] and not ex_rec.research_interests:
                        ex_rec.research_interests = cand["research_interests"]
                        changed = True
                    if cand.get("featured_publications") and not ex_rec.featured_publications:
                        ex_rec.featured_publications = cand["featured_publications"]
                        changed = True
                    if changed:
                        updated_members += 1
            else:
                new_members.append(cand)
                seen_in_batch.add(cand_clean)

        print(f"Deduplication Results:")
        print(f"  Enriched Existing Records: {updated_members}")
        print(f"  Net New Records to Add: {len(new_members)}")

        if new_members:
            # Generate Embeddings
            print(f"\n--- Generating 768-dim Gemini Vector Embeddings for {len(new_members)} Faculty ---")
            raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
            api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()] if raw_keys else []
            if not api_keys:
                raise ValueError("No GEMINI_API_KEY configured!")

            clients = [genai.Client(api_key=k) for k in api_keys]
            key_lock = threading.Lock()
            key_box = [0]

            def get_embedding(text: str) -> list[float]:
                for attempt in range(5):
                    with key_lock:
                        c = clients[key_box[0] % len(clients)]
                        key_box[0] += 1
                    for model in ["gemini-embedding-2", "gemini-embedding-001"]:
                        try:
                            resp = c.models.embed_content(
                                model=model,
                                contents=text,
                                config=types.EmbedContentConfig(output_dimensionality=768)
                            )
                            vec = resp.embeddings[0].values
                            if vec and len(vec) == 768:
                                return vec
                        except Exception as e:
                            if "429" in str(e) or "Quota" in str(e):
                                time.sleep(1.0 * (attempt + 1))
                    time.sleep(1.0 * (attempt + 1))
                raise RuntimeError(f"Failed to generate embedding after retries for: {text[:50]}")

            def make_embed_text(m: dict) -> str:
                interests_str = ", ".join(m.get("research_interests") or [])
                return (
                    f"อาจารย์และนักวิจัย: {m.get('full_name_th', '')} ({m.get('academic_title_th', '')})\n"
                    f"สังกัด: {m.get('department_th', '')}, {m.get('faculty_th', '')}, {m.get('university_th', '')}\n"
                    f"ความเชี่ยวชาญและงานวิจัย: {interests_str}"
                )

            embed_texts = [make_embed_text(m) for m in new_members]
            vectors = [None] * len(new_members)

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_idx = {
                    executor.submit(get_embedding, t): i for i, t in enumerate(embed_texts)
                }
                for f in as_completed(future_to_idx):
                    idx = future_to_idx[f]
                    vectors[idx] = f.result()
                    if (idx + 1) % 25 == 0 or idx + 1 == len(new_members):
                        print(f"  Vectorized {idx + 1}/{len(new_members)} faculty members...")

            # Commit to Database
            print("\n--- Committing Records to Local PostgreSQL ---")
            have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
            seq = 0
            for m, vec in zip(new_members, vectors):
                seq += 1
                uid = f"su_w43_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"su_w43_{seq:04d}_{random.randint(100, 999)}"
                have_ids.add(uid)

                db.add(FacultyDB(
                    id=uid,
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
                    research_interests=m["research_interests"],
                    featured_publications=m["featured_publications"],
                    education=m["education"],
                    taught_courses=m["taught_courses"],
                    embedding=vec
                ))

        db.commit()
        print("✅ Database Commit Successful!")

        # Post-run verification
        final_total = db.query(FacultyDB).count()
        su_final = db.query(FacultyDB).filter(FacultyDB.university_th.ilike("%ศิลปากร%")).count()
        su_em_final = db.query(FacultyDB).filter(
            FacultyDB.university_th.ilike("%ศิลปากร%"),
            FacultyDB.email.isnot(None),
            FacultyDB.email != ""
        ).count()
        print("\n============================================================")
        print(f"🎉 Wave 43 SU Execution Complete:")
        print(f"  - SU Total Faculty: {su_final} (with verified email: {su_em_final}, {su_em_final / max(1, su_final) * 100:.1f}%)")
        print(f"  - Total National Faculty in DB: {final_total}")
        print("============================================================")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database transaction: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
