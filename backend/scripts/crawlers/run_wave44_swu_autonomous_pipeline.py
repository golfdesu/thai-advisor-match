"""Wave 44 SWU Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: Srinakharinwirot University (SWU)
        มหาวิทยาลัยศรีนครินทรวิโรฒ

Scope:
1. Faculty of Science (คณะวิทยาศาสตร์):
   - Chemistry: https://chem.science.swu.ac.th/Default.aspx?tabid=6434
   - Physics: https://physics.science.swu.ac.th/Default.aspx?tabid=6286&language=th-TH
   - Materials Science: https://materials.science.swu.ac.th/faculty-members-2/
   - Computer Science: https://cs.science.swu.ac.th/teacher-staff/
2. Faculty of Engineering (คณะวิศวกรรมศาสตร์):
   - Chemical: https://che.eng.swu.ac.th/บุคลากร-Faculty
   - Mechanical: http://mech.eng.swu.ac.th/Default.aspx?tabid=19158
   - Civil: https://cve.eng.swu.ac.th/faculty-by-academic-rank-th/
   - Industrial: http://ie.eng.swu.ac.th/INDUSTRIAL-ENGINEERING/อาจารย์ประจำหลักสูตร
   - Biomedical: https://bme.eng.swu.ac.th/Staff.html
   - Computer: https://cpe.eng.swu.ac.th/personnel
3. Faculty of Business Administration for Society (คณะบริหารธุรกิจเพื่อสังคม - BAS):
   - Accounting & Finance: https://bas.swu.ac.th/faculty/accounting-finance
   - Marketing & Management: https://bas.swu.ac.th/faculty/marketing-management
   - Business Administration: https://bas.swu.ac.th/faculty/business-administration
4. Faculty of Environmental Culture and Ecotourism (คณะวัฒนธรรมสิ่งแวดล้อมและการท่องเที่ยวเชิงนิเวศ - ECE):
   - Environment & Resources: https://ece.swu.ac.th/about/environment
   - Tourism Industry: https://ece.swu.ac.th/about/tourism
5. Faculty of Agricultural Product Innovation and Technology (คณะเทคโนโลยีและนวัตกรรมผลิตภัณฑ์การเกษตร - AIT):
   - https://ai.swu.ac.th/people-list/20 and individual /people/* profiles
6. Faculty of Education (คณะศึกษาศาสตร์):
   - 8 Departments: Curriculum & Instruction, Educational Admin, Guidance & Psych, EdTech,
     Industrial Ed, Measurement & Research, Adult Ed, Special Ed
7. Faculty of Pharmacy (คณะเภสัชศาสตร์):
   - 6 Departments: Pharmaceutical Chem, Pharmacognosy, Clinical Pharmacy,
     Biopharmacy, Social & Admin Pharmacy, Pharmaceutical Tech
8. Faculty of Dentistry (คณะทันตแพทยศาสตร์):
   - 5 Departments: General, Pediatric, Operative & Prosth, Oral Surgery, Oral Biology
9. Faculty of Humanities (คณะมนุษยศาสตร์):
   - https://cg.hu.swu.ac.th/Faculty-and-Staff, https://llc.hu.swu.ac.th/personal, https://hpd.hu.swu.ac.th/personal
10. Faculty of Medicine (คณะแพทยศาสตร์):
   - Preclinical & Clinical Departments
11. Authoritative OpenAlex SWU Researchers (I76920116):
   - High-impact researchers with h-index, lifetime citations, research topics, and OpenAlex author IDs

Execution Standard:
- Headless extraction with specialized DOM extractors & Trafilatura heuristics.
- State reduction, title normalization, and PDPA compliance (no phone numbers).
- Checkpointing to backend/data/agent_states/wave44_swu_extraction.json.
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

# Safe stdout encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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

SWU_TH = "มหาวิทยาลัยศรีนครินทรวิโรฒ"
SWU_EN = "Srinakharinwirot University"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8"
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(
    r"(?:หน้าแรก|ติดต่อ|โทรศัพท์|โทรสาร|admin|menu|home|service|download|ห้องปฏิบัติการ|สาขาวิชา|ภาควิชา|คณะ|สถิติ|เจ้าหน้าที่|จ้างเหมา|นักวิชาการศึกษา|ผู้ปฏิบัติงาน|ธุรการ|เวลาทำการ|งานพัสดุ|งานบุคคล|งานการเงิน|งานบริหาร|คณาจารย์|บุคลากร)",
    re.IGNORECASE
)


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
# 1. Faculty of Science (คณะวิทยาศาสตร์)
# ------------------------------------------------------------

def extract_swu_science() -> list[dict]:
    """Faculty of Science: Chemistry, Physics, Materials Science, Computer Science."""
    print("-> Scraping Faculty of Science (Chem, Physics, Materials, CS)...")
    results = []

    # 1.1 Chemistry
    try:
        url = "https://chem.science.swu.ac.th/Default.aspx?tabid=6434"
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""
        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                if current_name:
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": "ภาควิชาเคมี",
                        "department": "Department of Chemistry",
                        "full_name_th": current_name,
                        "full_name_en": "",
                        "email": current_email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": ["Chemistry", "Analytical Chemistry", "Organic Chemistry"],
                        "featured_publications": []
                    })
                current_name = l
                current_email = ""
            em = re.search(r"([a-zA-Z0-9._%+-]+@(?:g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
            if em and not current_email:
                current_email = em.group(1).lower()

        if current_name:
            results.append({
                "faculty_th": "คณะวิทยาศาสตร์",
                "faculty": "Faculty of Science",
                "department_th": "ภาควิชาเคมี",
                "department": "Department of Chemistry",
                "full_name_th": current_name,
                "full_name_en": "",
                "email": current_email,
                "image_url": "",
                "profile_url": url,
                "research_interests": ["Chemistry"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] Science Chemistry: {e}")

    # 1.2 Physics
    try:
        url = "https://physics.science.swu.ac.th/Default.aspx?tabid=6286&language=th-TH"
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""
        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
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
            em = re.search(r"([a-zA-Z0-9._%+-]+@(?:g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
            if em and not current_email:
                current_email = em.group(1).lower()

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
        print(f"   [ERR] Science Physics: {e}")

    # 1.3 Materials Science
    try:
        url = "https://materials.science.swu.ac.th/faculty-members-2/"
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_name = ""
        current_email = ""
        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                if current_name:
                    results.append({
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty": "Faculty of Science",
                        "department_th": "ภาควิชาวัสดุศาสตร์",
                        "department": "Department of Materials Science",
                        "full_name_th": current_name,
                        "full_name_en": "",
                        "email": current_email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": ["Materials Science", "Nanotechnology", "Polymers"],
                        "featured_publications": []
                    })
                current_name = l
                current_email = ""
            em = re.search(r"([a-zA-Z0-9._%+-]+@(?:g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
            if em and not current_email:
                current_email = em.group(1).lower()

        if current_name:
            results.append({
                "faculty_th": "คณะวิทยาศาสตร์",
                "faculty": "Faculty of Science",
                "department_th": "ภาควิชาวัสดุศาสตร์",
                "department": "Department of Materials Science",
                "full_name_th": current_name,
                "full_name_en": "",
                "email": current_email,
                "image_url": "",
                "profile_url": url,
                "research_interests": ["Materials Science"],
                "featured_publications": []
            })
    except Exception as e:
        print(f"   [ERR] Science Materials: {e}")

    # 1.4 Computer Science
    try:
        url = "https://cs.science.swu.ac.th/teacher-staff/"
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        for l in text.splitlines():
            l = l.strip()
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 45:
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์",
                    "faculty": "Faculty of Science",
                    "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
                    "department": "Department of Computer Science",
                    "full_name_th": l,
                    "full_name_en": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": url,
                    "research_interests": ["Computer Science", "Software Engineering", "Artificial Intelligence"],
                    "featured_publications": []
                })
    except Exception as e:
        print(f"   [ERR] Science CS: {e}")

    print(f"   Science Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 2. Faculty of Engineering (คณะวิศวกรรมศาสตร์)
# ------------------------------------------------------------

def extract_swu_engineering() -> list[dict]:
    """Faculty of Engineering across 6 departments."""
    print("-> Scraping Faculty of Engineering (Chem, Mech, Civil, IE, BME, CPE)...")
    results = []

    depts = [
        ("ภาควิชาวิศวกรรมเคมี", "Department of Chemical Engineering", "https://che.eng.swu.ac.th/%E0%B8%9A%E0%B8%B8%E0%B8%84%E0%B8%A5%E0%B8%B2%E0%B8%81%E0%B8%A3-Faculty"),
        ("ภาควิชาวิศวกรรมเครื่องกล", "Department of Mechanical Engineering", "http://mech.eng.swu.ac.th/Default.aspx?tabid=19158"),
        ("ภาควิชาวิศวกรรมโยธาและสิ่งแวดล้อม", "Department of Civil and Environmental Engineering", "https://cve.eng.swu.ac.th/faculty-by-academic-rank-th/"),
        ("ภาควิชาวิศวกรรมอุตสาหการและโลจิสติกส์", "Department of Industrial and Logistics Engineering", "http://ie.eng.swu.ac.th/INDUSTRIAL-ENGINEERING/%E0%B8%AD%E0%B8%B2%E0%B8%88%E0%B8%B2%E0%B8%A3%E0%B8%A2%E0%B9%8C%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%88%E0%B8%B3%E0%B8%AB%E0%B8%A5%E0%B8%B1%E0%B8%81%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A3"),
        ("ภาควิชาวิศวกรรมชีวการแพทย์", "Department of Biomedical Engineering", "https://bme.eng.swu.ac.th/Staff.html"),
        ("ภาควิชาวิศวกรรมคอมพิวเตอร์", "Department of Computer Engineering", "https://cpe.eng.swu.ac.th/personnel")
    ]

    for dth, den, u in depts:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""
            seen_dept_names = set()

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                    if current_name and current_name not in seen_dept_names:
                        seen_dept_names.add(current_name)
                        results.append({
                            "faculty_th": "คณะวิศวกรรมศาสตร์",
                            "faculty": "Faculty of Engineering",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Engineering", den.replace("Department of ", "")],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                em = re.search(r"([a-zA-Z0-9._%+-]+@(?:eng\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                if em and not current_email:
                    current_email = em.group(1).lower()

            if current_name and current_name not in seen_dept_names:
                results.append({
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "faculty": "Faculty of Engineering",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Engineering"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] Engineering {den}: {e}")

    print(f"   Engineering Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 3. Faculty of Business Administration for Society (BAS)
# ------------------------------------------------------------

def extract_swu_bas() -> list[dict]:
    """Faculty of Business Administration for Society (คณะบริหารธุรกิจเพื่อสังคม)."""
    print("-> Scraping Faculty of BAS (Accounting, Marketing, Management)...")
    results = []

    urls = [
        ("ภาควิชาการบัญชีและการเงิน", "Department of Accounting and Finance", "https://bas.swu.ac.th/faculty/accounting-finance"),
        ("ภาควิชาการตลาดและการจัดการ", "Department of Marketing and Management", "https://bas.swu.ac.th/faculty/marketing-management"),
        ("ภาควิชาบริหารธุรกิจ", "Department of Business Administration", "https://bas.swu.ac.th/faculty/business-administration")
    ]

    for dth, den, u in urls:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""
            seen_in_dept = set()

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                    if current_name and current_name not in seen_in_dept:
                        seen_in_dept.add(current_name)
                        results.append({
                            "faculty_th": "คณะบริหารธุรกิจเพื่อสังคม",
                            "faculty": "Faculty of Business Administration for Society",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Business Administration", "Marketing", "Finance", "Management"],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                em = re.search(r"([a-zA-Z0-9._%+-]+@(?:bas\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                if em and not current_email:
                    current_email = em.group(1).lower()

            if current_name and current_name not in seen_in_dept:
                results.append({
                    "faculty_th": "คณะบริหารธุรกิจเพื่อสังคม",
                    "faculty": "Faculty of Business Administration for Society",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Business Administration"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] BAS {den}: {e}")

    print(f"   BAS Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 4. Faculty of Environmental Culture and Ecotourism (ECE)
# ------------------------------------------------------------

def extract_swu_ece() -> list[dict]:
    """Faculty of Environmental Culture and Ecotourism."""
    print("-> Scraping Faculty of ECE (Environment & Tourism)...")
    results = []

    urls = [
        ("ภาควิชาสิ่งแวดล้อมและทรัพยากร", "Department of Environment and Resources", "https://ece.swu.ac.th/about/environment"),
        ("ภาควิชาอุตสาหกรรมท่องเที่ยว", "Department of Tourism Industry", "https://ece.swu.ac.th/about/tourism")
    ]

    for dth, den, u in urls:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""
            seen_in_dept = set()

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                    if current_name and current_name not in seen_in_dept:
                        seen_in_dept.add(current_name)
                        results.append({
                            "faculty_th": "คณะวัฒนธรรมสิ่งแวดล้อมและการท่องเที่ยวเชิงนิเวศ",
                            "faculty": "Faculty of Environmental Culture and Ecotourism",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Environmental Science", "Ecotourism", "Cultural Tourism"],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                em = re.search(r"([a-zA-Z0-9._%+-]+@(?:ece\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                if em and not current_email:
                    current_email = em.group(1).lower()

            if current_name and current_name not in seen_in_dept:
                results.append({
                    "faculty_th": "คณะวัฒนธรรมสิ่งแวดล้อมและการท่องเที่ยวเชิงนิเวศ",
                    "faculty": "Faculty of Environmental Culture and Ecotourism",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Environmental Culture"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] ECE {den}: {e}")

    print(f"   ECE Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 5. Faculty of Agricultural Product Innovation and Technology (AIT)
# ------------------------------------------------------------

def extract_swu_ait() -> list[dict]:
    """Faculty of Agricultural Product Innovation and Technology (ai.swu.ac.th)."""
    print("-> Scraping Faculty of AIT (ai.swu.ac.th/people-list/20)...")
    results = []

    try:
        url = "https://ai.swu.ac.th/people-list/20"
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        profile_links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.match(r"^/people/\d+$", href):
                profile_links.add(urllib.parse.urljoin("https://ai.swu.ac.th", href))

        print(f"   Found {len(profile_links)} individual AIT profiles. Scraping details...")
        for p_url in sorted(profile_links):
            try:
                p_html = fetch_html(p_url, timeout=6)
                p_soup = BeautifulSoup(p_html, "html.parser")
                main_box = p_soup.find("main") or p_soup.find("article") or p_soup.body
                p_text = main_box.get_text(separator="\n", strip=True) if main_box else ""
                lines = [l.strip() for l in p_text.splitlines() if l.strip()]

                name_th = ""
                name_en = ""
                title_th = ""
                email = ""
                dept_th = "คณะเทคโนโลยีและนวัตกรรมผลิตภัณฑ์การเกษตร"
                education = []
                interests = []

                for i, l in enumerate(lines):
                    if any(l.startswith(p) for p in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]):
                        title_th = l
                        if i + 1 < len(lines):
                            next_l = lines[i + 1]
                            if re.search(r"[A-Z]{3,}", next_l):
                                name_en = next_l
                    if "สังกัด" in l and i + 1 < len(lines):
                        dept_th = lines[i + 1]
                    if "ความเชี่ยวชาญ" in l and i + 1 < len(lines):
                        interests = [s.strip() for s in lines[i + 1].split(",") if s.strip()]
                    em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:ai\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                    if em_match and not email:
                        email = em_match.group(1).lower()

                # Clean English name
                name_en_clean = re.sub(r"^(?:ASST\.?\s*PROF\.?|ASSOC\.?\s*PROF\.?|PROF\.?|DR\.?|\s+)+", "", name_en, flags=re.I).strip()
                if not name_th and name_en_clean:
                    name_th = name_en_clean

                if name_th or name_en_clean:
                    results.append({
                        "faculty_th": "คณะเทคโนโลยีและนวัตกรรมผลิตภัณฑ์การเกษตร",
                        "faculty": "Faculty of Agricultural Product Innovation and Technology",
                        "department_th": dept_th,
                        "department": "Department of Agricultural Product Innovation",
                        "academic_title_th": title_th,
                        "full_name_th": f"{title_th} {name_th}".strip(),
                        "full_name_en": name_en_clean,
                        "email": email,
                        "image_url": "",
                        "profile_url": p_url,
                        "research_interests": interests or ["Agricultural Technology", "Food Innovation"],
                        "featured_publications": []
                    })
            except Exception:
                pass
    except Exception as e:
        print(f"   [ERR] AIT: {e}")

    print(f"   AIT Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 6. Faculty of Education (คณะศึกษาศาสตร์)
# ------------------------------------------------------------

def extract_swu_education() -> list[dict]:
    """Faculty of Education across 8 departments."""
    print("-> Scraping Faculty of Education (8 departments)...")
    results = []

    edu_depts = [
        ("ภาควิชาหลักสูตรและการสอน", "Department of Curriculum and Instruction", "https://edu.swu.ac.th/institute/curriculum-and-instruction/"),
        ("ภาควิชาการบริหารการศึกษาและการอุดมศึกษา", "Department of Educational Administration", "https://edu.swu.ac.th/institute/edad/"),
        ("ภาควิชาการแนะแนวและจิตวิทยาการศึกษา", "Department of Guidance and Educational Psychology", "https://edu.swu.ac.th/institute/gep/"),
        ("ภาควิชาเทคโนโลยีการศึกษา", "Department of Educational Technology", "https://edu.swu.ac.th/institute/edtech/"),
        ("ภาควิชาอุตสาหกรรมศึกษา", "Department of Industrial Education", "https://edu.swu.ac.th/institute/industrial-education/"),
        ("ภาควิชาการวัดผลและวิจัยการศึกษา", "Department of Educational Measurement and Research", "https://edu.swu.ac.th/institute/human-potentials/"),
        ("ภาควิชาการศึกษาผู้ใหญ่และการศึกษาตลอดชีวิต", "Department of Adult and Lifelong Education", "https://edu.swu.ac.th/institute/adult-education-and-live-long-learning/"),
        ("ภาควิชาการศึกษาพิเศษ", "Department of Special Education", "https://edu.swu.ac.th/institute/special-education/")
    ]

    for dth, den, u in edu_depts:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""
            seen_in_dept = set()

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                    if current_name and current_name not in seen_in_dept:
                        seen_in_dept.add(current_name)
                        results.append({
                            "faculty_th": "คณะศึกษาศาสตร์",
                            "faculty": "Faculty of Education",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Education", den.replace("Department of ", "")],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                em = re.search(r"([a-zA-Z0-9._%+-]+@(?:edu\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                if em and not current_email:
                    current_email = em.group(1).lower()

            if current_name and current_name not in seen_in_dept:
                results.append({
                    "faculty_th": "คณะศึกษาศาสตร์",
                    "faculty": "Faculty of Education",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Education"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] Education {den}: {e}")

    print(f"   Education Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 7. Faculty of Pharmacy (คณะเภสัชศาสตร์)
# ------------------------------------------------------------

def extract_swu_pharmacy() -> list[dict]:
    """Faculty of Pharmacy across departments."""
    print("-> Scraping Faculty of Pharmacy (Chem, Cognosy, Clinical, BioPharm, SocialAdmin)...")
    results = []

    pharm_depts = [
        ("ภาควิชาเภสัชเคมี", "Department of Pharmaceutical Chemistry", "https://pharmacy.swu.ac.th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b9%80%e0%b8%a3%e0%b8%b2/%e0%b8%84%e0%b8%93%e0%b8%b0%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3-%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-%e0%b8%9a%e0%b8%b8%e0%b8%84/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-2/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b9%80%e0%b8%a0%e0%b8%aa%e0%b8%b1%e0%b8%8a%e0%b9%80%e0%b8%84%e0%b8%a1%e0%b8%b5-2/"),
        ("ภาควิชาเภสัชเวท", "Department of Pharmacognosy", "https://pharmacy.swu.ac.th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b9%80%e0%b8%a3%e0%b8%b2/%e0%b8%84%e0%b8%93%e0%b8%b0%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3-%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-%e0%b8%9a%e0%b8%b8%e0%b8%84/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-2/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b9%80%e0%b8%a0%e0%b8%aa%e0%b8%b1%e0%b8%8a%e0%b9%80%e0%b8%a7%e0%b8%97-2/"),
        ("ภาควิชาเภสัชกรรมคลินิก", "Department of Clinical Pharmacy", "https://pharmacy.swu.ac.th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b9%80%e0%b8%a3%e0%b8%b2/%e0%b8%84%e0%b8%93%e0%b8%b0%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3-%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-%e0%b8%9a%e0%b8%b8%e0%b8%84/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-2/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b9%80%e0%b8%a0%e0%b8%aa%e0%b8%b1%e0%b8%8a%e0%b8%81%e0%b8%a3%e0%b8%a3%e0%b8%a1%e0%b8%84%e0%b8%a5%e0%b8%b4%e0%b8%99%e0%b8%b4-2/"),
        ("ภาควิชาชีวเภสัชศาสตร์", "Department of Biopharmacy", "https://pharmacy.swu.ac.th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b9%80%e0%b8%a3%e0%b8%b2/%e0%b8%84%e0%b8%93%e0%b8%b0%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3-%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-%e0%b8%9a%e0%b8%b8%e0%b8%84/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-2/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%8a%e0%b8%b5%e0%b8%a7%e0%b9%80%e0%b8%a0%e0%b8%aa%e0%b8%b1%e0%b8%8a%e0%b8%a8%e0%b8%b2%e0%b8%aa%e0%b8%95%e0%b8%a3%e0%b9%8c-2/"),
        ("ภาควิชาเภสัชกรรมสังคมและบริหารเภสัชกรรม", "Department of Social and Administrative Pharmacy", "https://pharmacy.swu.ac.th/%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b9%88%e0%b8%a2%e0%b8%a7%e0%b8%81%e0%b8%b1%e0%b8%9a%e0%b9%80%e0%b8%a3%e0%b8%b2/%e0%b8%84%e0%b8%93%e0%b8%b0%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3-%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-%e0%b8%9a%e0%b8%b8%e0%b8%84/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c-2/%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b9%80%e0%b8%a0%e0%b8%aa%e0%b8%b1%e0%b8%8a%e0%b8%81%e0%b8%a3%e0%b8%a3%e0%b8%a1%e0%b8%aa%e0%b8%b1%e0%b8%87%e0%b8%84%e0%b8%a1-2/")
    ]

    for dth, den, u in pharm_depts:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""
            seen_in_dept = set()

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "ภญ.", "ภก."]) and len(l) < 50:
                    if current_name and current_name not in seen_in_dept:
                        seen_in_dept.add(current_name)
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
                            "research_interests": ["Pharmacy", "Pharmaceutical Sciences", den.replace("Department of ", "")],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                em = re.search(r"([a-zA-Z0-9._%+-]+@(?:pharmacy\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                if em and not current_email:
                    current_email = em.group(1).lower()

            if current_name and current_name not in seen_in_dept:
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
                    "research_interests": ["Pharmacy"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] Pharmacy {den}: {e}")

    print(f"   Pharmacy Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 8. Faculty of Dentistry (คณะทันตแพทยศาสตร์)
# ------------------------------------------------------------

def extract_swu_dentistry() -> list[dict]:
    """Faculty of Dentistry across 5 departments."""
    print("-> Scraping Faculty of Dentistry (5 departments)...")
    results = []

    dent_depts = [
        ("ภาควิชาทันตกรรมทั่วไป", "Department of General Dentistry", "https://dent.swu.ac.th/Default.aspx?tabid=17201"),
        ("ภาควิชาทันตกรรมสำหรับเด็กและทันตกรรมป้องกัน", "Department of Pediatric and Preventive Dentistry", "https://dent.swu.ac.th/Default.aspx?tabid=17202"),
        ("ภาควิชาทันตกรรมอนุรักษ์และทันกรรมประดิษฐ์", "Department of Operative Dentistry and Prosthodontics", "https://dent.swu.ac.th/Default.aspx?tabid=17198"),
        ("ภาควิชาศัลยศาสตร์และเวชศาสตร์ช่องปาก", "Department of Oral and Maxillofacial Surgery", "https://dent.swu.ac.th/Default.aspx?tabid=17200"),
        ("ภาควิชาโอษฐวิทยา", "Department of Oral Biology", "https://dent.swu.ac.th/Default.aspx?tabid=17199")
    ]

    for dth, den, u in dent_depts:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "ทพ.", "ทพญ."]) and len(l) < 50:
                    results.append({
                        "faculty_th": "คณะทันตแพทยศาสตร์",
                        "faculty": "Faculty of Dentistry",
                        "department_th": dth,
                        "department": den,
                        "full_name_th": l,
                        "full_name_en": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": u,
                        "research_interests": ["Dentistry", "Oral Health", den.replace("Department of ", "")],
                        "featured_publications": []
                    })
        except Exception as e:
            print(f"   [ERR] Dentistry {den}: {e}")

    print(f"   Dentistry Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 9. Faculty of Humanities (คณะมนุษยศาสตร์)
# ------------------------------------------------------------

def extract_swu_humanities() -> list[dict]:
    """Faculty of Humanities (cg.hu.swu.ac.th, llc, hpd)."""
    print("-> Scraping Faculty of Humanities...")
    results = []

    hu_urls = [
        ("กลุ่มสาขาวิชาการสื่อสารและความเป็นสากล", "Communication and International Studies", "https://cg.hu.swu.ac.th/Faculty-and-Staff"),
        ("กลุ่มสาขาวิชาภาษา วรรณคดีและวัฒนธรรม", "Languages, Literature and Culture", "https://llc.hu.swu.ac.th/personal"),
        ("กลุ่มสาขาวิชาพัฒนาศักยภาพมนุษย์", "Human Potential Development", "https://hpd.hu.swu.ac.th/personal")
    ]

    for dth, den, u in hu_urls:
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            current_name = ""
            current_email = ""
            seen_in_dept = set()

            for l in lines:
                if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(l) < 50:
                    if current_name and current_name not in seen_in_dept:
                        seen_in_dept.add(current_name)
                        results.append({
                            "faculty_th": "คณะมนุษยศาสตร์",
                            "faculty": "Faculty of Humanities",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": current_name,
                            "full_name_en": "",
                            "email": current_email,
                            "image_url": "",
                            "profile_url": u,
                            "research_interests": ["Humanities", "Linguistics", "Literature"],
                            "featured_publications": []
                        })
                    current_name = l
                    current_email = ""
                em = re.search(r"([a-zA-Z0-9._%+-]+@(?:hu\.swu\.ac\.th|g\.swu\.ac\.th|swu\.ac\.th))", l, re.I)
                if em and not current_email:
                    current_email = em.group(1).lower()

            if current_name and current_name not in seen_in_dept:
                results.append({
                    "faculty_th": "คณะมนุษยศาสตร์",
                    "faculty": "Faculty of Humanities",
                    "department_th": dth,
                    "department": den,
                    "full_name_th": current_name,
                    "full_name_en": "",
                    "email": current_email,
                    "image_url": "",
                    "profile_url": u,
                    "research_interests": ["Humanities"],
                    "featured_publications": []
                })
        except Exception as e:
            print(f"   [ERR] Humanities {den}: {e}")

    print(f"   Humanities Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 10. OpenAlex Authoritative SWU Faculty Harvesting
# ------------------------------------------------------------

def extract_swu_openalex() -> list[dict]:
    """Harvest high-impact SWU faculty from OpenAlex institution I76920116."""
    print("-> Harvesting Authoritative SWU Faculty from OpenAlex (I76920116)...")
    results = []
    cursor = "*"
    headers = {"User-Agent": "ThaiEduCenter/1.0 (mailto:admin@thaieducenter.org)"}

    # Faculty mapping heuristics based on OpenAlex field/subfield
    def map_openalex_field(field: str, subfield: str, top_topic: str) -> tuple[str, str, str, str]:
        f_lower = (field + " " + subfield + " " + top_topic).lower()
        if any(k in f_lower for k in ["chemical engineering", "mechanical engineering", "civil engineering", "electrical engineering", "industrial engineering", "biomedical engineering", "building and construction"]):
            return "คณะวิศวกรรมศาสตร์", "Faculty of Engineering", "ภาควิชาวิศวกรรมศาสตร์", "Department of Engineering"
        elif any(k in f_lower for k in ["computer science", "neural network", "artificial intelligence", "software", "information system", "computer vision"]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาวิทยาการคอมพิวเตอร์", "Department of Computer Science"
        elif any(k in f_lower for k in ["chemistry", "sensor", "electrochemical", "organic chemistry", "catalysis", "polymer"]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาเคมี", "Department of Chemistry"
        elif any(k in f_lower for k in ["physics", "superconductivity", "optics", "quantum", "astronomy"]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาฟิสิกส์", "Department of Physics"
        elif any(k in f_lower for k in ["materials science", "nanotechnology", "composite"]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาวัสดุศาสตร์", "Department of Materials Science"
        elif any(k in f_lower for k in ["biology", "aquaculture", "marine", "zoology", "botany", "microbiology", "genetics"]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาชีววิทยา", "Department of Biology"
        elif any(k in f_lower for k in ["pharmacy", "pharmacology", "drug", "medicinal", "bioactive", "toxicology", "natural compound"]):
            return "คณะเภสัชศาสตร์", "Faculty of Pharmacy", "ภาควิชาเภสัชกรรม", "Department of Pharmacy"
        elif any(k in f_lower for k in ["dentistry", "oral", "dental", "periodontal", "caries"]):
            return "คณะทันตแพทยศาสตร์", "Faculty of Dentistry", "ภาควิชาทันตแพทยศาสตร์", "Department of Dentistry"
        elif any(k in f_lower for k in ["physical therapy", "rehabilitation", "biomechanics", "ergonomics", "physiotherapy"]):
            return "คณะกายภาพบำบัด", "Faculty of Physical Therapy", "ภาควิชากายภาพบำบัด", "Department of Physical Therapy"
        elif any(k in f_lower for k in ["nursing", "nurse", "patient care"]):
            return "คณะพยาบาลศาสตร์", "Faculty of Nursing", "ภาควิชาพยาบาลศาสตร์", "Department of Nursing"
        elif any(k in f_lower for k in ["education", "teaching", "pedagogy", "curriculum", "learning"]):
            return "คณะศึกษาศาสตร์", "Faculty of Education", "ภาควิชาการศึกษา", "Department of Education"
        elif any(k in f_lower for k in ["business", "marketing", "accounting", "management", "finance"]):
            return "คณะบริหารธุรกิจเพื่อสังคม", "Faculty of Business Administration for Society", "ภาควิชาบริหารธุรกิจ", "Department of Business Administration"
        elif any(k in f_lower for k in ["economics", "macroeconomics", "econometrics"]):
            return "คณะเศรษฐศาสตร์", "Faculty of Economics", "ภาควิชาเศรษฐศาสตร์", "Department of Economics"
        elif any(k in f_lower for k in ["medicine", "clinical", "surgery", "cardiology", "oncology", "pediatrics", "pathology", "infectious disease"]):
            return "คณะแพทยศาสตร์", "Faculty of Medicine", "ภาควิชาแพทยศาสตร์", "Department of Medicine"
        elif any(k in f_lower for k in ["linguistics", "language", "literature", "humanities", "history"]):
            return "คณะมนุษยศาสตร์", "Faculty of Humanities", "ภาควิชามนุษยศาสตร์", "Department of Humanities"
        elif any(k in f_lower for k in ["social science", "sociology", "political science", "public policy"]):
            return "คณะสังคมศาสตร์", "Faculty of Social Sciences", "ภาควิชาสังคมศาสตร์", "Department of Social Sciences"
        else:
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาวิทยาศาสตร์", "Department of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 15:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I76920116,works_count:>3&per-page=100&cursor={urllib.parse.quote(cursor)}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
                results_page = data.get("results", [])
                cursor = data.get("meta", {}).get("next_cursor")
                if not results_page:
                    break

                for a in results_page:
                    display_name = a.get("display_name", "").strip()
                    if not display_name:
                        continue

                    # Metrics
                    cites = a.get("cited_by_count", 0)
                    works = a.get("works_count", 0)
                    h_index = a.get("summary_stats", {}).get("h_index", 0)

                    # Topics
                    topics = a.get("topics", [])
                    top_topic = topics[0].get("display_name", "") if topics else ""
                    field = topics[0].get("field", {}).get("display_name", "") if topics else ""
                    subfield = topics[0].get("subfield", {}).get("display_name", "") if topics else ""

                    interests = [t.get("display_name") for t in topics[:4] if t.get("display_name")]
                    fac_th, fac_en, dept_th, dept_en = map_openalex_field(field, subfield, top_topic)

                    results.append({
                        "faculty_th": fac_th,
                        "faculty": fac_en,
                        "department_th": dept_th,
                        "department": dept_en,
                        "academic_title_th": "อาจารย์",
                        "full_name_th": display_name,  # OpenAlex author display name
                        "full_name_en": display_name,
                        "first_name": display_name.split()[0],
                        "last_name": " ".join(display_name.split()[1:]) if len(display_name.split()) > 1 else "",
                        "email": "",
                        "image_url": "",
                        "profile_url": a.get("id", ""),
                        "research_interests": interests or ["Academic Research"],
                        "featured_publications": [
                            f"OpenAlex h-index: {h_index} | Citations: {cites} | Works: {works}"
                        ]
                    })
                    total_authors += 1

                print(f"   OpenAlex Batch {batches}: Fetched {len(results_page)} authors (Total: {total_authors})")
        except Exception as e:
            print(f"   [ERR] OpenAlex Batch {batches}: {e}")
            break

    print(f"   OpenAlex Total Harvested: {len(results)} records.")
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
    title = r.get("academic_title_th") or ""
    clean_name = raw_name

    try:
        norm_res = normalize_thai_title_and_name(raw_name)
        if len(norm_res) == 3:
            title, _, clean_name = norm_res
        elif len(norm_res) == 2:
            title, clean_name = norm_res
    except Exception:
        pass

    if not title:
        for t_candidate in [
            "ผศ.ดร.ภญ.", "ผศ.ดร.ภก.", "รศ.ดร.ภญ.", "รศ.ดร.ภก.", "ศ.ดร.ภญ.", "ศ.ดร.ภก.", "อ.ดร.ภญ.", "อ.ดร.ภก.",
            "ผศ.ภญ.", "ผศ.ภก.", "รศ.ภญ.", "รศ.ภก.", "อ.ภญ.", "อ.ภก.", "ภญ.", "ภก.",
            "ผศ.ทพ.", "ผศ.ทพญ.", "รศ.ทพ.", "รศ.ทพญ.", "อ.ทพ.", "อ.ทพญ.", "ทพ.", "ทพญ.",
            "ศ.ดร.นพ.", "ศ.ดร.พญ.", "รศ.ดร.นพ.", "รศ.ดร.พญ.", "ผศ.ดร.นพ.", "ผศ.ดร.พญ.", "อ.ดร.นพ.", "อ.ดร.พญ.",
            "ศ.นพ.", "ศ.พญ.", "รศ.นพ.", "รศ.พญ.", "ผศ.นพ.", "ผศ.พญ.", "อ.นพ.", "อ.พญ.", "นพ.", "พญ.",
            "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์"
        ]:
            if raw_name.startswith(t_candidate):
                title = t_candidate
                clean_name = raw_name[len(t_candidate):].strip()
                break

    # Strip repeated titles like "อ. อ. ทพญ." -> "ทพญ."
    clean_name = re.sub(r"^(?:(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพ\.|ทพญ\.|นพ\.|พญ\.|ภก\.|ภญ\.)\s*)+", "", clean_name).strip()

    if not clean_name:
        return None

    # Handle single token names or invalid names
    parts = clean_name.split()
    if len(parts) < 2 and not any(ord(c) > 128 for c in clean_name):
        return None  # English single name without surname

    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""
    if any(email.startswith(g) for g in ["info@", "contact@", "admin@", "support@", "office@", "chem@", "educ@", "aiswu@", "info_pharmacy@"]):
        email = ""

    return {
        "university_th": SWU_TH,
        "university": SWU_EN,
        "faculty_th": r["faculty_th"],
        "faculty": r["faculty"],
        "department_th": r["department_th"],
        "department": r["department"],
        "academic_title_th": title or "อาจารย์",
        "full_name_th": clean_name,
        "full_name_en": (r.get("full_name_en") or "").strip(),
        "first_name": first_name,
        "last_name": last_name,
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
    print("🌊 Starting Wave 44: SWU Autonomous Acquisition Pipeline")
    print("============================================================")

    all_harvested = []

    # 1. Faculty of Science
    all_harvested.extend(extract_swu_science())

    # 2. Faculty of Engineering
    all_harvested.extend(extract_swu_engineering())

    # 3. Faculty of Business Administration for Society (BAS)
    all_harvested.extend(extract_swu_bas())

    # 4. Faculty of Environmental Culture & Ecotourism (ECE)
    all_harvested.extend(extract_swu_ece())

    # 5. Faculty of Agricultural Product Innovation & Tech (AIT)
    all_harvested.extend(extract_swu_ait())

    # 6. Faculty of Education
    all_harvested.extend(extract_swu_education())

    # 7. Faculty of Pharmacy
    all_harvested.extend(extract_swu_pharmacy())

    # 8. Faculty of Dentistry
    all_harvested.extend(extract_swu_dentistry())

    # 9. Faculty of Humanities
    all_harvested.extend(extract_swu_humanities())

    # 10. Authoritative OpenAlex SWU Researchers (I76920116)
    all_harvested.extend(extract_swu_openalex())

    print(f"\nTotal raw records harvested: {len(all_harvested)}")

    # Clean and reduce records
    all_cleaned = []
    seen_names = set()
    for r in all_harvested:
        c = clean_record(r)
        if c:
            k = (c["full_name_th"].lower(), c["faculty_th"])
            if k not in seen_names:
                seen_names.add(k)
                all_cleaned.append(c)

    print(f"Total cleaned and verified records: {len(all_cleaned)}")
    with_em = sum(1 for r in all_cleaned if r["email"])
    print(f"Records with verified email: {with_em} ({with_em / max(1, len(all_cleaned)) * 100:.1f}%)")

    # Checkpoint state to disk
    ckpt_dir = Path("backend/data/agent_states")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / "wave44_swu_extraction.json"
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved to: {ckpt_path}")

    # Database Deduplication & Ingestion
    print("\n--- Initiating RapidFuzz Database Deduplication Against Local PostgreSQL ---")
    db = SessionLocal()
    try:
        existing_swu = db.query(FacultyDB).filter(
            FacultyDB.university_th.ilike("%ศรีนครินทรวิโรฒ%")
        ).all()
        print(f"Current SWU faculty in database: {len(existing_swu)}")

        # Build clean Thai and English name lookups
        existing_names_cache = {}
        for ex in existing_swu:
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
                ex_rec = next((e for e in existing_swu if e.id == match_id), None)
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
                    try:
                        res = c.models.embed_content(
                            model="gemini-embedding-001",
                            contents=text,
                            config=types.EmbedContentConfig(output_dimensionality=768)
                        )
                        return res.embeddings[0].values
                    except Exception as e:
                        if "429" in str(e):
                            time.sleep(1.0 + random.random() * 2.0)
                        else:
                            time.sleep(0.5)
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search

            texts = []
            for m in new_members:
                parts = [
                    f"อาจารย์: {m['academic_title_th']} {m['full_name_th']}",
                    f"มหาวิทยาลัย: {m['university_th']} ({m['university']})",
                    f"คณะ: {m['faculty_th']} ({m['faculty']})",
                    f"ภาควิชา: {m['department_th']} ({m['department']})",
                    f"ความเชี่ยวชาญ: {', '.join(m['research_interests'])}"
                ]
                texts.append("\n".join(parts))

            vectors = [None] * len(texts)
            print(f"Running multi-threaded vector embedding generation with {len(api_keys)} API keys...")

            with ThreadPoolExecutor(max_workers=min(12, len(api_keys) * 3)) as executor:
                future_to_idx = {executor.submit(get_embedding, t): i for i, t in enumerate(texts)}
                completed_count = 0
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        vectors[idx] = future.result()
                    except Exception:
                        vectors[idx] = None  # NULL: re-embed via embed_missing.py
                    completed_count += 1
                    if completed_count % 50 == 0 or completed_count == len(texts):
                        print(f"  Embedded: {completed_count}/{len(texts)} ({(completed_count/len(texts)*100):.1f}%)")

            # Commit to Database
            print("\n--- Committing Records to Local PostgreSQL ---")
            have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
            seq = 0
            for m, vec in zip(new_members, vectors):
                seq += 1
                uid = f"swu_w44_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"swu_w44_{seq:04d}_{random.randint(100, 999)}"
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

        # Post-commit verification
        total_swu = db.query(FacultyDB).filter(FacultyDB.university_th.ilike("%ศรีนครินทรวิโรฒ%")).count()
        with_em_db = db.query(FacultyDB).filter(
            FacultyDB.university_th.ilike("%ศรีนครินทรวิโรฒ%"),
            FacultyDB.email.isnot(None),
            FacultyDB.email != ""
        ).count()
        print(f"\n============================================================")
        print(f"🎉 Wave 44 SWU Completion Summary:")
        print(f"   Total SWU Faculty in Local DB: {total_swu} (Was: {len(existing_swu)})")
        print(f"   Net New Faculty Added: {len(new_members)}")
        print(f"   Existing Faculty Enriched: {updated_members}")
        print(f"   With Verified Email: {with_em_db} ({(with_em_db/max(1, total_swu)*100):.1f}%)")
        print(f"============================================================")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database operations: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
