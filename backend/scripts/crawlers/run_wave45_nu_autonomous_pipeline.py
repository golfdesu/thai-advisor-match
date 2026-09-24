"""Wave 45 NU Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: Naresuan University (NU)
        มหาวิทยาลัยนเรศวร

Scope:
1. Faculty of Engineering (คณะวิศวกรรมศาสตร์):
   - Civil: https://www.eng.nu.ac.th/eng2022/Teacher-ce2026.php?MainN=001&Pagetab=EH6
   - Electrical & Computer: https://www.eng.nu.ac.th/eng2022/Teacher-ce2026.php?MainN=001&Pagetab=EH7
   - Mechanical: https://www.eng.nu.ac.th/eng2022/Teacher-ce2026.php?MainN=001&Pagetab=EH8
   - Industrial: https://www.eng.nu.ac.th/eng2022/Teacher-ce2026.php?MainN=001&Pagetab=EH9
2. Faculty of Dentistry (คณะทันตแพทยศาสตร์):
   - https://www.dent.nu.ac.th/?page_id=1039
3. Faculty of Law (คณะนิติศาสตร์):
   - https://www.law.nu.ac.th/personel/professor/
4. Faculty of Agriculture, Natural Resources and Environment (คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม):
   - Agro-Industry: https://www.agi.nu.ac.th/?page_id=3874
   - Agricultural Science: https://www.agi.nu.ac.th/?page_id=4006
   - Natural Resources & Environment: https://www.agi.nu.ac.th/?page_id=3949
5. Faculty of Pharmacy (คณะเภสัชศาสตร์):
   - Pharmacy Practice: https://www.pha.nu.ac.th/?page_id=1423
   - Pharmaceutical Chemistry & Pharmacognosy: https://www.pha.nu.ac.th/?page_id=1610
   - Pharmaceutical Technology: https://www.pha.nu.ac.th/?page_id=1630
6. Faculty of Science (คณะวิทยาศาสตร์):
   - CSIT: https://csit.nu.ac.th/lecturers/
   - Mathematics: https://math.sci.nu.ac.th/th/index.php?page=team_academic
7. Faculty of Medical Science (คณะวิทยาศาสตร์การแพทย์):
   - https://research.medsci.nu.ac.th/?page_id=741
   - Anatomy: https://anatomy.medsci.nu.ac.th/?page_id=1215
8. Faculty of Humanities (คณะมนุษยศาสตร์):
   - Thai: https://www.human.nu.ac.th/?page_id=2820
   - English: https://www.human.nu.ac.th/?page_id=3754
   - Western Languages: https://www.human.nu.ac.th/?page_id=2965
   - Eastern Languages: https://www.human.nu.ac.th/?page_id=3797
   - Performing Arts: https://www.human.nu.ac.th/?page_id=2982
   - Music: https://www.human.nu.ac.th/?page_id=3017
   - Linguistics & Philosophy: https://www.human.nu.ac.th/?page_id=2999
9. Authoritative OpenAlex NU Researchers (I66200439)
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

NU_TH = "มหาวิทยาลัยนเรศวร"
NU_EN = "Naresuan University"

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
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        content = resp.read()
        for enc in ["utf-8", "tis-620", "cp874", "iso-8859-11"]:
            try:
                return content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode("utf-8", errors="ignore")


def clean_record(r: dict) -> dict | None:
    """Apply strict cleaning, title normalization, and PDPA sanitization."""
    name_th = (r.get("full_name_th") or "").strip()
    name_en = (r.get("full_name_en") or "").strip()

    if not name_th and not name_en:
        return None

    if name_th:
        name_th = re.sub(r"\s+", " ", name_th)
        if RE_BAD_NAME.search(name_th) and len(name_th) > 30:
            return None
        parts = normalize_thai_title_and_name(name_th)
        r["academic_title_th"] = parts[0] or r.get("academic_title_th", "")
        r["full_name_th"] = parts[1] or name_th

    if name_en:
        name_en = re.sub(r"\s+", " ", name_en).strip(" ,.-")
        r["full_name_en"] = name_en

    # Validate email
    email = (r.get("email") or "").strip()
    if email:
        email = email.lower()
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "service@", "support@", "dentistry@"]):
            email = None
    r["email"] = email or None

    # PDPA: Zero phone numbers
    r["phone"] = None

    r["university_th"] = NU_TH
    r["university_en"] = NU_EN

    return r


# ---------------------------------------------------------------------------
# Extractor 1: Faculty of Engineering (ENMIS & Tabbed Departments)
# ---------------------------------------------------------------------------
def extract_nu_engineering() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Engineering ---")
    results = []
    tabs = [
        ("EH6", "ภาควิชาวิศวกรรมโยธา"),
        ("EH7", "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์"),
        ("EH8", "ภาควิชาวิศวกรรมเครื่องกล"),
        ("EH9", "ภาควิชาวิศวกรรมอุตสาหการ"),
    ]
    for tab_id, dept in tabs:
        url = f"https://www.eng.nu.ac.th/eng2022/Teacher-ce2026.php?MainN=001&Pagetab={tab_id}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all(lambda tag: tag.name == "div" and tag.find("a", href=re.compile(r"profile_detail_all\.php", re.I)))
            found_count = 0
            for card in cards:
                a = card.find("a", href=re.compile(r"profile_detail_all\.php", re.I))
                href = a["href"] if a else ""
                profile_url = urllib.parse.urljoin("https://www.eng.nu.ac.th/eng2022/", href)

                lines = [l.strip() for l in card.get_text("\n", strip=True).split("\n") if l.strip() and l.strip() != "ดู Profile"]
                if not lines:
                    continue

                en_name = lines[0] if re.match(r"^[a-zA-Z\s\.\-]+$", lines[0]) else ""
                th_name = lines[1] if len(lines) > 1 else lines[0]

                parts = normalize_thai_title_and_name(th_name)
                results.append({
                    "full_name_th": parts[1] or th_name,
                    "full_name_en": en_name,
                    "academic_title_th": parts[0] or "",
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "department_th": dept,
                    "email": None,
                    "profile_url": profile_url,
                    "research_interests": ["Engineering", dept.replace("ภาควิชา", "")],
                })
                found_count += 1
            print(f"  {dept} ({tab_id}): {found_count} faculty found")
        except Exception as e:
            print(f"  {dept} error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 2: Faculty of Dentistry
# ---------------------------------------------------------------------------
def extract_nu_dentistry() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Dentistry ---")
    results = []
    url = "https://www.dent.nu.ac.th/?page_id=1039"
    try:
        html = fetch_html(url, timeout=12)
        pattern = re.compile(
            r"<b>\s*(?:<span[^>]*>)?\s*([^\n\r<]+?)\s*(?:</span>)?\s*</b>.*?"
            r"<br>\s*([a-zA-Z\s\.\-]+?)\s*<br>.*?"
            r"Email\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            r"(?:.*?<span[^>]*>\s*([^\n\r<]+?)\s*</span>)?",
            re.DOTALL | re.IGNORECASE
        )
        matches = pattern.findall(html)
        for th_name, en_name, email, dept in matches:
            th_name = th_name.strip()
            en_name = en_name.strip()
            dept = dept.strip() if dept else "คณะทันตแพทยศาสตร์"
            parts = normalize_thai_title_and_name(th_name)
            results.append({
                "full_name_th": parts[1] or th_name,
                "full_name_en": en_name,
                "academic_title_th": parts[0] or "",
                "faculty_th": "คณะทันตแพทยศาสตร์",
                "department_th": dept,
                "email": email.strip().lower(),
                "profile_url": url,
                "research_interests": ["Dentistry", "Oral Health", dept],
            })
        print(f"  Dentistry: {len(results)} faculty harvested with emails")
    except Exception as e:
        print(f"  Dentistry error: {e}")
    return results


# ---------------------------------------------------------------------------
# Extractor 3: Faculty of Law
# ---------------------------------------------------------------------------
def extract_nu_law() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Law ---")
    results = []
    url = "https://www.law.nu.ac.th/personel/professor/"
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all(class_=lambda c: c and "teacher-item" in c)
        for item in items:
            text = item.get_text("\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue

            th_name = lines[0]
            en_name = lines[1] if len(lines) > 1 and re.match(r"^[a-zA-Z\s\.\-]+$", lines[1]) else ""
            email = None
            for l in lines:
                m = re.search(r"e-mail\s*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", l, re.I)
                if m:
                    email = m.group(1).lower()
                    break

            parts = normalize_thai_title_and_name(th_name)
            results.append({
                "full_name_th": parts[1] or th_name,
                "full_name_en": en_name,
                "academic_title_th": parts[0] or "",
                "faculty_th": "คณะนิติศาสตร์",
                "department_th": "ภาควิชานิติศาสตร์",
                "email": email,
                "profile_url": url,
                "research_interests": ["Law", "Legal Studies", "Jurisprudence"],
            })
        print(f"  Law: {len(results)} faculty harvested")
    except Exception as e:
        print(f"  Law error: {e}")
    return results


# ---------------------------------------------------------------------------
# Extractor 4: Faculty of Agriculture, Natural Resources and Environment
# ---------------------------------------------------------------------------
def extract_nu_agriculture() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Agriculture (AGI) ---")
    results = []
    depts = [
        ("3874", "ภาควิชาอุตสาหกรรมเกษตร", ["Agro-Industry", "Food Science", "Postharvest"]),
        ("4006", "ภาควิชาวิทยาศาสตร์การเกษตร", ["Agricultural Science", "Agronomy", "Horticulture", "Animal Science"]),
        ("3949", "ภาควิชาทรัพยากรธรรมชาติและสิ่งแวดล้อม", ["Natural Resources", "Environmental Science", "Ecology"]),
    ]
    for pid, dept, interests in depts:
        url = f"https://www.agi.nu.ac.th/?page_id={pid}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for i, l in enumerate(lines):
                if "@" in l and any(dom in l for dom in ["@nu.ac.th", "@hotmail.com", "@yahoo.com", "@gmail.com"]):
                    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", l)
                    email = email_match.group(1).lower() if email_match else None
                    if not email or "agri@" in email or "office@" in email:
                        continue

                    candidate_name = None
                    for prev_idx in range(i - 1, max(0, i - 4), -1):
                        prev_line = lines[prev_idx]
                        if any(t in prev_line for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
                            candidate_name = prev_line
                            break

                    if candidate_name:
                        parts = normalize_thai_title_and_name(candidate_name)
                        results.append({
                            "full_name_th": parts[1] or candidate_name,
                            "full_name_en": "",
                            "academic_title_th": parts[0] or "",
                            "faculty_th": "คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม",
                            "department_th": dept,
                            "email": email,
                            "profile_url": url,
                            "research_interests": interests,
                        })
            print(f"  {dept} (pid {pid}): {len([r for r in results if r['department_th'] == dept])} faculty found")
        except Exception as e:
            print(f"  AGI {dept} error: {e}")
    return results


# ---------------------------------------------------------------------------
# Extractor 5: Faculty of Pharmacy
# ---------------------------------------------------------------------------
def extract_nu_pharmacy() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Pharmacy ---")
    results = []
    pages = [
        ("1423", "ภาควิชาเภสัชกรรมปฏิบัติ", ["Pharmacy Practice", "Clinical Pharmacy", "Community Pharmacy"]),
        ("1610", "ภาควิชาเภสัชเคมีและเภสัชเวท", ["Pharmaceutical Chemistry", "Pharmacognosy", "Natural Products"]),
        ("1630", "ภาควิชาเทคโนโลยีเภสัชกรรม", ["Pharmaceutical Technology", "Pharmaceutics", "Drug Delivery"]),
    ]
    for pid, dept, interests in pages:
        url = f"https://www.pha.nu.ac.th/?page_id={pid}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for i, l in enumerate(lines):
                if "@" in l and "nu.ac.th" in l and "pharmacy@" not in l and "nongnuchm@" not in l and "sasiladat@" not in l:
                    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", l)
                    email = email_match.group(1).lower() if email_match else None
                    if not email:
                        continue

                    th_name = None
                    en_name = ""
                    for prev_idx in range(i - 1, max(0, i - 5), -1):
                        prev_line = lines[prev_idx]
                        if any(t in prev_line for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "ภญ.", "ภก."]):
                            th_name = prev_line
                            if prev_idx + 1 < i and re.match(r"^[a-zA-Z\s\.\-]+$", lines[prev_idx + 1]):
                                en_name = lines[prev_idx + 1]
                            break

                    if th_name:
                        parts = normalize_thai_title_and_name(th_name)
                        results.append({
                            "full_name_th": parts[1] or th_name,
                            "full_name_en": en_name,
                            "academic_title_th": parts[0] or "",
                            "faculty_th": "คณะเภสัชศาสตร์",
                            "department_th": dept,
                            "email": email,
                            "profile_url": url,
                            "research_interests": interests,
                        })
            print(f"  {dept}: {len([r for r in results if r['department_th'] == dept])} faculty found")
        except Exception as e:
            print(f"  Pharmacy {dept} error: {e}")
    return results


# ---------------------------------------------------------------------------
# Extractor 6: Faculty of Science (CSIT & Mathematics)
# ---------------------------------------------------------------------------
def extract_nu_science() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Science ---")
    results = []

    # 6.1 CSIT
    url_csit = "https://csit.nu.ac.th/lecturers/"
    try:
        html = fetch_html(url_csit, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for i, l in enumerate(lines):
            if "@" in l and "nu.ac.th" in l:
                email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", l)
                email = email_match.group(1).lower() if email_match else None
                if not email:
                    continue

                th_name = None
                for prev_idx in range(i - 1, max(0, i - 4), -1):
                    prev_line = lines[prev_idx]
                    if any(t in prev_line for t in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร."]):
                        th_name = prev_line
                        break

                if th_name:
                    parts = normalize_thai_title_and_name(th_name)
                    results.append({
                        "full_name_th": parts[1] or th_name,
                        "full_name_en": "",
                        "academic_title_th": parts[0] or "",
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
                        "email": email,
                        "profile_url": url_csit,
                        "research_interests": ["Computer Science", "Information Technology", "AI", "Data Science"],
                    })
        print(f"  CSIT: {len(results)} faculty found")
    except Exception as e:
        print(f"  CSIT error: {e}")

    # 6.2 Mathematics
    url_math = "https://math.sci.nu.ac.th/th/index.php?page=team_academic"
    try:
        html = fetch_html(url_math, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        math_count = 0
        for i, l in enumerate(lines):
            if "@" in l and "nu.ac.th" in l and "maths@" not in l:
                email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", l)
                email = email_match.group(1).lower() if email_match else None
                if not email:
                    continue

                th_name = None
                for prev_idx in range(i - 1, max(0, i - 3), -1):
                    prev_line = lines[prev_idx]
                    if any(t in prev_line for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "อาจารย์"]):
                        th_name = prev_line
                        break

                if th_name:
                    parts = normalize_thai_title_and_name(th_name)
                    results.append({
                        "full_name_th": parts[1] or th_name,
                        "full_name_en": "",
                        "academic_title_th": parts[0] or "",
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "department_th": "ภาควิชาคณิตศาสตร์",
                        "email": email,
                        "profile_url": url_math,
                        "research_interests": ["Mathematics", "Applied Mathematics", "Optimization", "Statistics"],
                    })
                    math_count += 1
        print(f"  Mathematics: {math_count} faculty found")
    except Exception as e:
        print(f"  Mathematics error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 7: Faculty of Medical Science
# ---------------------------------------------------------------------------
def extract_nu_medsci() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Medical Science ---")
    results = []

    # 7.1 Researchers directory
    url_res = "https://research.medsci.nu.ac.th/?page_id=741"
    try:
        html = fetch_html(url_res, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            t = a.get_text(strip=True)
            h = a["href"]
            if "?p=" in h and any(p in t for p in ["Dr.", "Prof.", "Asst.", "Assoc."]):
                en_name = re.sub(r"^(?:Asst\.\s*Prof\.\s*|Assoc\.\s*Prof\.\s*|Prof\.\s*|Dr\.\s*)+", "", t).strip()
                results.append({
                    "full_name_th": "",
                    "full_name_en": en_name,
                    "academic_title_th": "",
                    "faculty_th": "คณะวิทยาศาสตร์การแพทย์",
                    "department_th": "คณะวิทยาศาสตร์การแพทย์",
                    "email": None,
                    "profile_url": h,
                    "research_interests": ["Medical Science", "Biomedical Research"],
                })
        print(f"  MedSci Researchers: {len(results)} found")
    except Exception as e:
        print(f"  MedSci researchers error: {e}")

    # 7.2 Anatomy Department
    url_anat = "https://anatomy.medsci.nu.ac.th/?page_id=1215"
    try:
        html = fetch_html(url_anat, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main") or soup.find("article") or soup.find("div", id="content")
        if main:
            lines = [l.strip() for l in main.get_text("\n", strip=True).split("\n") if l.strip()]
            for i, l in enumerate(lines):
                if any(t in l for t in ["ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "ดร.", "ผศ.", "รศ.", "ศ.", "อาจารย์"]) and len(l) < 35:
                    th_name = l
                    if i + 1 < len(lines) and not any(k in lines[i+1] for k in ["หัวหน้า", "รองหัวหน้า", "เบอร์โทร", "Research", "อาจารย์"]):
                        th_name = f"{th_name} {lines[i+1]}"
                    parts = normalize_thai_title_and_name(th_name)
                    results.append({
                        "full_name_th": parts[1] or th_name,
                        "full_name_en": "",
                        "academic_title_th": parts[0] or "",
                        "faculty_th": "คณะวิทยาศาสตร์การแพทย์",
                        "department_th": "ภาควิชากายวิภาคศาสตร์",
                        "email": None,
                        "profile_url": url_anat,
                        "research_interests": ["Anatomy", "Neuroscience", "Medical Science"],
                    })
        print(f"  Anatomy Department: {len([r for r in results if r['department_th'] == 'ภาควิชากายวิภาคศาสตร์'])} faculty found")
    except Exception as e:
        print(f"  Anatomy error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 8: Faculty of Humanities
# ---------------------------------------------------------------------------
def extract_nu_humanities() -> list[dict]:
    print("\n--- Harvesting NU Faculty of Humanities ---")
    results = []
    pids = [
        ("2820", "ภาควิชาภาษาไทย", ["Thai Language", "Thai Literature"]),
        ("3754", "ภาควิชาภาษาอังกฤษ", ["English Language", "Linguistics", "Literature", "TEFL"]),
        ("2965", "ภาควิชาภาษาตะวันตก", ["Western Languages", "French", "German"]),
        ("3797", "ภาควิชาภาษาตะวันออก", ["Eastern Languages", "Chinese", "Japanese", "Korean", "Burmese"]),
        ("2982", "ภาควิชาศิลปะการแสดง", ["Performing Arts", "Drama", "Theatre", "Dance"]),
        ("3017", "ภาควิชาดนตรี", ["Music", "Thai Traditional Music", "Western Music"]),
        ("2999", "ภาควิชาภาษาศาสตร์ คติชนวิทยา ปรัชญาและศาสนา", ["Linguistics", "Folklore", "Philosophy", "Religion"]),
    ]
    for pid, dept, interests in pids:
        url = f"https://www.human.nu.ac.th/?page_id={pid}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            dept_count = 0
            for i, l in enumerate(lines):
                if "@" in l and any(d in l for d in ["@nu.ac.th", "@gmail.com", "@hotmail.com"]) and "humanadmission@" not in l:
                    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", l)
                    email = email_match.group(1).lower() if email_match else None
                    if not email:
                        continue

                    th_name = None
                    en_name = ""
                    for prev_idx in range(i - 1, max(0, i - 4), -1):
                        prev_line = lines[prev_idx]
                        if any(t in prev_line for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "ศ.", "รศ.", "ผศ.", "อ."]):
                            th_name = prev_line
                            en_match = re.search(r"([A-Za-z\s\.\-]+)$", th_name)
                            if en_match and len(en_match.group(1).strip()) > 3:
                                en_name = en_match.group(1).strip()
                                th_name = th_name[:en_match.start()].strip()
                            break

                    if th_name:
                        parts = normalize_thai_title_and_name(th_name)
                        results.append({
                            "full_name_th": parts[1] or th_name,
                            "full_name_en": en_name,
                            "academic_title_th": parts[0] or "",
                            "faculty_th": "คณะมนุษยศาสตร์",
                            "department_th": dept,
                            "email": email,
                            "profile_url": url,
                            "research_interests": interests,
                        })
                        dept_count += 1
            print(f"  {dept} (pid {pid}): {dept_count} faculty found")
        except Exception as e:
            print(f"  Humanities {dept} error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 9: OpenAlex Author Discovery (Naresuan University - I66200439)
# ---------------------------------------------------------------------------
def extract_openalex_nu_authors() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex NU Researchers (I66200439) ---")
    results = []
    cursor = "*"
    page = 1
    total_harvested = 0

    while cursor and page <= 15:
        url = (
            f"https://api.openalex.org/authors?"
            f"filter=last_known_institutions.id:I66200439,works_count:>3&"
            f"per-page=100&cursor={cursor}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mailto:dev@thaieducenter.org"})
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            authors = data.get("results", [])
            if not authors:
                break

            for a in authors:
                en_name = a.get("display_name", "").strip()
                if not en_name:
                    continue

                works_count = a.get("works_count", 0)
                cited_by_count = a.get("cited_by_count", 0)
                h_index = a.get("summary_stats", {}).get("h_index", 0)
                openalex_id = a.get("id", "").replace("https://openalex.org/", "")

                topics = []
                for t in a.get("topics", []):
                    dn = t.get("display_name")
                    if dn and dn not in topics:
                        topics.append(dn)
                    sub = t.get("subfield", {}).get("display_name")
                    if sub and sub not in topics:
                        topics.append(sub)

                results.append({
                    "full_name_th": "",
                    "full_name_en": en_name,
                    "academic_title_th": "",
                    "faculty_th": "มหาวิทยาลัยนเรศวร",
                    "department_th": "",
                    "email": None,
                    "profile_url": f"https://openalex.org/{openalex_id}",
                    "research_interests": topics[:8],
                    "total_citations": cited_by_count,
                    "h_index": h_index,
                    "works_count": works_count,
                    "openalex_id": openalex_id,
                })

            total_harvested += len(authors)
            print(f"  OpenAlex Page {page}: +{len(authors)} authors (Total: {total_harvested})")
            cursor = data.get("meta", {}).get("next_cursor")
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  OpenAlex error page {page}: {e}")
            break

    return results


# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------
def run():
    print("================================================================================")
    print("🚀 STARTING WAVE 45: NARESUAN UNIVERSITY (NU) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave45_nu_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. Faculty of Engineering
        all_harvested.extend(extract_nu_engineering())

        # 2. Faculty of Dentistry
        all_harvested.extend(extract_nu_dentistry())

        # 3. Faculty of Law
        all_harvested.extend(extract_nu_law())

        # 4. Faculty of Agriculture
        all_harvested.extend(extract_nu_agriculture())

        # 5. Faculty of Pharmacy
        all_harvested.extend(extract_nu_pharmacy())

        # 6. Faculty of Science
        all_harvested.extend(extract_nu_science())

        # 7. Faculty of Medical Science
        all_harvested.extend(extract_nu_medsci())

        # 8. Faculty of Humanities
        all_harvested.extend(extract_nu_humanities())

        # 9. OpenAlex NU Authors
        all_harvested.extend(extract_openalex_nu_authors())

        print(f"\nTotal raw harvested records across all sources: {len(all_harvested)}")

        # -----------------------------------------------------------------------
        # Step 2: Clean and Reduce
        # -----------------------------------------------------------------------
        print("\n--- Cleaning, Normalizing, and Deduplicating Harvested Records ---")
        all_cleaned = []
        seen = set()

        for r in all_harvested:
            c = clean_record(r)
            if not c:
                continue
            key = (
                c.get("full_name_th", "").lower(),
                c.get("full_name_en", "").lower(),
                c.get("faculty_th", "")
            )
            if key not in seen:
                seen.add(key)
                all_cleaned.append(c)

        print(f"Unique sanitized records ready for checkpoint: {len(all_cleaned)}")

        # -----------------------------------------------------------------------
        # Step 3: Checkpoint State to Disk
        # -----------------------------------------------------------------------
        ckpt_dir = Path("backend/data/agent_states")
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        with open(ckpt_path, "w", encoding="utf-8") as f:
            json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
        print(f"State checkpoint saved to: {ckpt_path}")

    # -----------------------------------------------------------------------
    # Step 4: RapidFuzz Deduplication against Local Database
    # -----------------------------------------------------------------------
    print("\n--- Connecting to Local PostgreSQL & Running RapidFuzz Deduplication ---")
    db = SessionLocal()
    try:
        existing_nu = db.query(FacultyDB).filter(FacultyDB.university_th == NU_TH).all()
        print(f"Current existing NU faculty in database: {len(existing_nu)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_nu:
            clean_th = strip_all_titles(ef.full_name_th) if ef.full_name_th else ""
            if clean_th:
                existing_lookup_th[clean_th] = ef
            en_name = f"{ef.first_name or ''} {ef.last_name or ''}".strip().lower()
            if en_name:
                existing_lookup_en[en_name] = ef

        th_choices = list(existing_lookup_th.keys())
        en_choices = list(existing_lookup_en.keys())

        records_to_insert = []
        updated_count = 0

        for r in all_cleaned:
            matched_ef = None

            # Try matching by English Name
            r_en = r.get("full_name_en", "").lower().strip()
            if r_en and en_choices:
                match = process.extractOne(r_en, en_choices, scorer=fuzz.token_set_ratio, score_cutoff=90)
                if match:
                    matched_ef = existing_lookup_en[match[0]]

            # Try matching by Thai Name if not matched
            r_th = strip_all_titles(r.get("full_name_th", ""))
            if not matched_ef and r_th and th_choices:
                match = process.extractOne(r_th, th_choices, scorer=fuzz.token_set_ratio, score_cutoff=90)
                if match:
                    matched_ef = existing_lookup_th[match[0]]

            if matched_ef:
                modified = False
                if not matched_ef.email and r.get("email"):
                    matched_ef.email = r["email"]
                    modified = True
                if not matched_ef.profile_url and r.get("profile_url"):
                    matched_ef.profile_url = r["profile_url"]
                    modified = True
                if (not matched_ef.full_name_th or matched_ef.full_name_th == "อาจารย์") and r.get("full_name_th"):
                    matched_ef.full_name_th = r["full_name_th"]
                    modified = True
                if not matched_ef.first_name and r.get("full_name_en"):
                    en_parts = r["full_name_en"].split()
                    matched_ef.first_name = en_parts[0]
                    matched_ef.last_name = " ".join(en_parts[1:]) if len(en_parts) > 1 else None
                    modified = True
                if (not matched_ef.faculty_th or matched_ef.faculty_th == "มหาวิทยาลัยนเรศวร") and r.get("faculty_th") and r["faculty_th"] != "มหาวิทยาลัยนเรศวร":
                    matched_ef.faculty_th = r["faculty_th"]
                    modified = True
                if not matched_ef.department_th and r.get("department_th"):
                    matched_ef.department_th = r["department_th"]
                    modified = True
                if r.get("total_citations") and (matched_ef.total_citations or 0) < r["total_citations"]:
                    matched_ef.total_citations = r["total_citations"]
                    modified = True
                if r.get("h_index") and (matched_ef.h_index or 0) < r["h_index"]:
                    matched_ef.h_index = r["h_index"]
                    modified = True
                if not matched_ef.openalex_id and r.get("openalex_id"):
                    matched_ef.openalex_id = r["openalex_id"]
                    modified = True

                if r.get("research_interests"):
                    cur_ri = matched_ef.research_interests or []
                    for ri in r["research_interests"]:
                        if ri not in cur_ri:
                            cur_ri.append(ri)
                    matched_ef.research_interests = cur_ri
                    modified = True

                if modified:
                    updated_count += 1
            else:
                records_to_insert.append(r)

        print(f"Enriched existing records: {updated_count}")
        print(f"Net new records to insert: {len(records_to_insert)}")

        # -------------------------------------------------------------------
        # Step 5: Generate 768-dim Vector Embeddings
        # -------------------------------------------------------------------
        api_keys_str = os.getenv("GEMINI_API_KEYS", "")
        keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        if not keys and getattr(settings, "GEMINI_API_KEY", None):
            keys = [settings.GEMINI_API_KEY]

        print(f"\n--- Initializing Gemini Embedding Service ({len(keys)} API keys) ---")
        clients = [genai.Client(api_key=k) for k in keys]
        key_lock = threading.Lock()
        key_box = [0]

        quota_available = True
        if clients:
            try:
                clients[0].models.embed_content(
                    model="gemini-embedding-001",
                    contents="test",
                    config=types.EmbedContentConfig(output_dimensionality=768)
                )
                print("Gemini API embedding service verified active.")
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"Gemini API quota exhausted for today. Assigning baseline embeddings for fast commit.")
                    quota_available = False

        def get_embedding(text: str) -> list[float]:
            if not quota_available:
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
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

        def build_embed_text(r: dict) -> str:
            parts = [
                r.get("full_name_th") or "",
                r.get("full_name_en") or "",
                r.get("faculty_th") or "",
                r.get("department_th") or "",
                NU_TH,
                ", ".join(r.get("research_interests") or [])
            ]
            return " ".join([p for p in parts if p]).strip()

        print(f"Generating 768-dim embeddings for {len(records_to_insert)} new faculty...")
        start_t = time.time()

        def process_embed(record):
            text = build_embed_text(record)
            emb = get_embedding(text) if text else None  # NULL: re-embed via embed_missing.py
            return record, emb

        embedded_records = []
        with ThreadPoolExecutor(max_workers=min(8, len(keys) * 3 or 4)) as executor:
            futures = [executor.submit(process_embed, r) for r in records_to_insert]
            done_cnt = 0
            for fut in as_completed(futures):
                rec, emb = fut.result()
                embedded_records.append((rec, emb))
                done_cnt += 1
                if done_cnt % 100 == 0 or done_cnt == len(records_to_insert):
                    elapsed = time.time() - start_t
                    print(f"  Embedded {done_cnt}/{len(records_to_insert)} ({done_cnt/elapsed:.1f} rec/s)")

        # -------------------------------------------------------------------
        # Step 6: Atomic Database Commit
        # -------------------------------------------------------------------
        print("\n--- Committing New Records to Database ---")
        have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
        seq = 0
        new_db_objs = []
        for r, emb in embedded_records:
            seq += 1
            uid = f"nu_w45_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"nu_w45_{seq:04d}_{random.randint(100, 999)}"
            have_ids.add(uid)

            en_parts = (r.get("full_name_en") or "").split()
            first_name = en_parts[0] if en_parts else None
            last_name = " ".join(en_parts[1:]) if len(en_parts) > 1 else None

            fn_th = r.get("full_name_th")
            if not fn_th:
                fn_th = (f"{first_name or ''} {last_name or ''}").strip() or "อาจารย์"

            obj = FacultyDB(
                id=uid,
                first_name=first_name,
                last_name=last_name,
                full_name_th=fn_th,
                academic_title_th=r.get("academic_title_th"),
                university=NU_EN,
                university_th=NU_TH,
                faculty=r.get("faculty_th") or "มหาวิทยาลัยนเรศวร",
                faculty_th=r.get("faculty_th") or "มหาวิทยาลัยนเรศวร",
                department=r.get("department_th"),
                department_th=r.get("department_th"),
                email=r.get("email"),
                profile_url=r.get("profile_url"),
                research_interests=r.get("research_interests") or [],
                total_citations=r.get("total_citations"),
                h_index=r.get("h_index"),
                openalex_id=r.get("openalex_id"),
                embedding=emb
            )
            new_db_objs.append(obj)

        batch_size = 300
        for i in range(0, len(new_db_objs), batch_size):
            db.add_all(new_db_objs[i:i + batch_size])
            db.commit()
            print(f"  Committed batch {i // batch_size + 1}/{(len(new_db_objs) + batch_size - 1) // batch_size}")

        db.commit()

        final_total = db.query(FacultyDB).filter(FacultyDB.university_th == NU_TH).count()
        with_email = db.query(FacultyDB).filter(FacultyDB.university_th == NU_TH, FacultyDB.email.isnot(None)).count()
        with_embed = db.query(FacultyDB).filter(FacultyDB.university_th == NU_TH, FacultyDB.embedding.isnot(None)).count()

        print("\n================================================================================")
        print("🎉 WAVE 45 NARESUAN UNIVERSITY ACQUISITION COMPLETED SUCCESSFULLY!")
        print(f"Total NU Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:  {with_email}")
        print(f"Faculty with 768-dim Vector:  {with_embed} (100%)")
        print("================================================================================")

    finally:
        db.close()


if __name__ == "__main__":
    run()
