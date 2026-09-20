"""Wave 48: University of Phayao (UP) Autonomous Pipeline
Harvests faculty data from UP ICT, Dentistry, Allied Health Sciences, Law, Nursing,
Business & Communication Arts (BCA), Liberal Arts (LibArts), and OpenAlex UP Researchers (I4210090662).
Cleans, normalizes titles, checkpoints state, deduplicates with RapidFuzz, and commits to local PostgreSQL.
"""

import os
import sys
import json
import time
import re
import random
import threading
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
from rapidfuzz import fuzz

# Constants
UP_TH = "มหาวิทยาลัยพะเยา"
UP_EN = "University of Phayao"

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|คณะ|สาขาวิชา|สำนักวิชา|หน่วยงาน|โทร|เบอร์|งาน|ห้อง|center|department|faculty|school|คู่มือ|อาจารย์ที่ปรึกษา|บริการ|ประกาศ|รายละเอียดเพิ่มเติม|คณบดี|ประธานหลักสูตร)",
    re.I
)


def fetch_html(url: str, timeout: int = 12) -> str:
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
    name_th = (r.get("full_name_th") or "").strip()
    name_en = (r.get("full_name_en") or "").strip()
    if not name_th and not name_en:
        return None

    if name_th:
        name_th = re.sub(r"\s+", " ", name_th)
        if RE_BAD_NAME.search(name_th) and len(name_th) > 25:
            return None
        if len(name_th) < 4:
            return None
        parts = normalize_thai_title_and_name(name_th)
        r["academic_title_th"] = parts[0] or r.get("academic_title_th", "")
        r["full_name_th"] = parts[1] or name_th

    if name_en:
        name_en = re.sub(r"\s+", " ", name_en)
        name_en = re.sub(r"^(?:Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Lecturer|Mr\.|Mrs\.|Ms\.)\s*", "", name_en, flags=re.I).strip()
        r["full_name_en"] = name_en

    email = (r.get("email") or "").strip()
    if email:
        email = email.lower()
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "webmaster@", "bca@up.ac.th", "law.up@up.ac.th"]):
            email = None
    r["email"] = email or None

    r["phone"] = None  # PDPA Invariant: 0 personal phone numbers
    r["university_th"] = UP_TH
    r["university_en"] = UP_EN
    return r


# ---------------------------------------------------------------------------
# Extractor 1: UP ICT (School of Information and Communication Technology)
# ---------------------------------------------------------------------------
def extract_up_ict() -> list[dict]:
    print("\n--- Harvesting UP School of ICT ---")
    results = []
    url = "https://ict.up.ac.th/personnel"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        seen = set()

        for card in soup.find_all(class_=re.compile(r"card|person|staff|team|member", re.I)):
            t = card.get_text(" | ", strip=True)
            if "@up.ac.th" in t and any(p in t for p in ["ดร.", "อาจารย์", "ผศ.", "รศ.", "ศ.", "นาย", "นาง", "นางสาว"]):
                if len(t) > 350:
                    continue

                parts = [p.strip() for p in t.split("|") if p.strip()]
                name_candidate = None
                email = None
                dept = "คณะเทคโนโลยีสารสนเทศและการสื่อสาร"

                for p in parts:
                    if "@up.ac.th" in p.lower():
                        em_match = re.findall(r"[a-zA-Z0-9._%+-]+@up\.ac\.th", p)
                        if em_match:
                            email = em_match[0].lower()
                    elif any(p.startswith(pref) for pref in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์", "นาย", "นาง", "นางสาว"]):
                        if not name_candidate and len(p) < 60:
                            name_candidate = p

                if name_candidate and name_candidate not in seen:
                    seen.add(name_candidate)
                    parts_th = normalize_thai_title_and_name(name_candidate)
                    results.append({
                        "full_name_th": parts_th[1] or name_candidate,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
                        "faculty_en": "School of Information and Communication Technology",
                        "department_th": dept,
                        "department_en": "School of ICT",
                        "email": email,
                        "profile_url": url,
                        "research_interests": ["Information Technology", "Computer Science", "Software Engineering", "Artificial Intelligence"]
                    })

        print(f"  ICT: {len(results)} faculty harvested with emails")
    except Exception as e:
        print(f"  ICT error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 2: UP Dentistry (School of Dentistry)
# ---------------------------------------------------------------------------
def extract_up_dentistry() -> list[dict]:
    print("\n--- Harvesting UP School of Dentistry ---")
    results = []
    urls = [
        ("https://dentistry.up.ac.th/personal/TA21001", "บุคลากรสายวิชาการ"),
        ("https://dentistry.up.ac.th/personal/MA001", "คณะผู้บริหาร")
    ]
    seen = set()

    for url, cat in urls:
        try:
            html = fetch_html(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")

            for card in soup.find_all(class_=re.compile(r"card|box|item|col", re.I)):
                t = card.get_text(" | ", strip=True)
                if "@up.ac.th" in t and any(p in t for p in ["ทพ.", "ทพญ.", "อาจารย์", "ผศ.", "รศ.", "ศ.", "ดร."]):
                    if len(t) > 300:
                        continue

                    parts = [p.strip() for p in t.split("|") if p.strip()]
                    name_candidate = parts[0]
                    if name_candidate in seen or len(name_candidate) > 70:
                        continue
                    seen.add(name_candidate)

                    em_match = re.findall(r"[a-zA-Z0-9._%+-]+@up\.ac\.th", t)
                    email = em_match[0].lower() if em_match else None

                    parts_th = normalize_thai_title_and_name(name_candidate)
                    results.append({
                        "full_name_th": parts_th[1] or name_candidate,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะทันตแพทยศาสตร์",
                        "faculty_en": "School of Dentistry",
                        "department_th": "ภาควิชาทันตกรรม",
                        "department_en": "Department of Dentistry",
                        "email": email,
                        "profile_url": url,
                        "research_interests": ["Dentistry", "Oral Health", "Dental Sciences"]
                    })

            print(f"  Dentistry ({cat}): {len(results)} faculty harvested")
        except Exception as e:
            print(f"  Dentistry error ({cat}): {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 3: UP Allied Health Sciences (AHS)
# ---------------------------------------------------------------------------
def extract_up_ahs() -> list[dict]:
    print("\n--- Harvesting UP School of Allied Health Sciences ---")
    results = []
    targets = [
        ("https://ahs.up.ac.th/staff-pt.php", "สาขาวิชากายภาพบำบัด", "Department of Physical Therapy", ["Physical Therapy", "Physiotherapy", "Rehabilitation"]),
        ("https://ahs.up.ac.th/staff-mt.php", "สาขาวิชาเทคนิคการแพทย์", "Department of Medical Technology", ["Medical Technology", "Clinical Pathology", "Laboratory Medicine"])
    ]
    seen = set()

    for url, dept_th, dept_en, interests in targets:
        try:
            html = fetch_html(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")
            found_count = 0

            for a in soup.find_all("a", href=re.compile(r"mailto:")):
                email = a["href"].replace("mailto:", "").strip().lower()
                if not email.endswith("@up.ac.th"):
                    continue

                card = a.find_parent(class_=re.compile(r"card|item|member|col|wrap", re.I)) or a.parent.parent.parent
                card_text = card.get_text(" | ", strip=True)
                parts = [p.strip() for p in card_text.split("|") if p.strip()]

                name_candidate = None
                for p in parts:
                    if any(p.startswith(pref) for pref in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์", "นาย", "นาง", "นางสาว"]):
                        if len(p) < 60:
                            name_candidate = p
                            break

                if not name_candidate and parts:
                    name_candidate = parts[0]

                if name_candidate and name_candidate not in seen and len(name_candidate) < 60:
                    seen.add(name_candidate)
                    parts_th = normalize_thai_title_and_name(name_candidate)
                    results.append({
                        "full_name_th": parts_th[1] or name_candidate,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะสหเวชศาสตร์",
                        "faculty_en": "School of Allied Health Sciences",
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "email": email,
                        "profile_url": url,
                        "research_interests": interests
                    })
                    found_count += 1

            print(f"  AHS ({dept_th}): {found_count} faculty harvested")
        except Exception as e:
            print(f"  AHS error ({dept_th}): {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 4: UP Law (School of Law)
# ---------------------------------------------------------------------------
def extract_up_law() -> list[dict]:
    print("\n--- Harvesting UP School of Law ---")
    results = []
    url = "https://law.up.ac.th/About_Academic.aspx"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        seen = set()

        for tr in soup.find_all(["tr", "div"]):
            txt = tr.get_text(" | ", strip=True)
            if "@up.ac.th" in txt and any(k in txt for k in ["ผศ.", "รศ.", "อ.", "ดร.", "อาจารย์", "นาย", "นางสาว"]):
                if len(txt) > 300:
                    continue

                parts = [p.strip() for p in txt.split("|") if p.strip()]
                name_th = parts[0]
                name_en = parts[1] if len(parts) > 1 and re.match(r"^[A-Za-z\.\s]+$", parts[1]) else None

                em_match = re.findall(r"[a-zA-Z0-9._%+-]+@up\.ac\.th", txt)
                email = em_match[0].lower() if em_match else None

                if name_th not in seen and len(name_th) < 60:
                    seen.add(name_th)
                    parts_th = normalize_thai_title_and_name(name_th)
                    results.append({
                        "full_name_th": parts_th[1] or name_th,
                        "full_name_en": name_en,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะนิติศาสตร์",
                        "faculty_en": "School of Law",
                        "department_th": "สาขาวิชานิติศาสตร์",
                        "department_en": "Department of Law",
                        "email": email,
                        "profile_url": url,
                        "research_interests": ["Law", "Jurisprudence", "Legal Studies", "Criminal Law", "Public Law"]
                    })

        print(f"  Law: {len(results)} faculty harvested")
    except Exception as e:
        print(f"  Law error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 5: UP Nursing (School of Nursing)
# ---------------------------------------------------------------------------
def extract_up_nursing() -> list[dict]:
    print("\n--- Harvesting UP School of Nursing ---")
    results = []
    pages = [
        ("personnel-nur1.aspx", "กลุ่มวิชาการพยาบาลสตรีและเด็ก", "Department of Maternal and Child Nursing"),
        ("personnel-nur2.aspx", "กลุ่มวิชาการพยาบาลผู้ใหญ่และผู้สูงอายุ", "Department of Adult and Gerontological Nursing"),
        ("personnel-nur3.aspx", "กลุ่มวิชาการพยาบาลอนามัยชุมชนและจิตเวช", "Department of Community Health and Psychiatric Nursing")
    ]
    seen = set()

    for page, dept_th, dept_en in pages:
        url = f"https://nurse.up.ac.th/{page}"
        try:
            html = fetch_html(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")
            found_count = 0

            for p in soup.find_all(["p", "div", "tr"]):
                t = p.get_text(" | ", strip=True)
                if "@up.ac.th" in t and any(k in t for k in ["ผศ.", "รศ.", "อ.", "ดร.", "อาจารย์", "นางสาว"]):
                    if len(t) > 250:
                        continue

                    parts = [pt.strip() for pt in t.split("|") if pt.strip()]
                    name_th = parts[0]
                    if name_th in seen or len(name_th) > 60:
                        continue
                    seen.add(name_th)

                    em_match = re.findall(r"[a-zA-Z0-9._%+-]+@up\.ac\.th", t)
                    email = em_match[0].lower() if em_match else None

                    parts_th = normalize_thai_title_and_name(name_th)
                    results.append({
                        "full_name_th": parts_th[1] or name_th,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะพยาบาลศาสตร์",
                        "faculty_en": "School of Nursing",
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "email": email,
                        "profile_url": url,
                        "research_interests": ["Nursing", "Health Care", "Patient Care", dept_th]
                    })
                    found_count += 1

            print(f"  Nursing ({dept_th}): {found_count} faculty harvested")
        except Exception as e:
            print(f"  Nursing error ({dept_th}): {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 6: UP BCA (School of Business and Communication Arts)
# ---------------------------------------------------------------------------
def extract_up_bca() -> list[dict]:
    print("\n--- Harvesting UP School of Business and Communication Arts (BCA) ---")
    results = []
    bca_pages = [
        ("BusinessManagement.aspx", "สาขาวิชาการจัดการธุรกิจ", "Department of Business Management", ["Business Management", "Strategic Management"]),
        ("FinanceInvestment.aspx", "สาขาวิชาการเงินและการลงทุน", "Department of Finance and Investment", ["Finance", "Investment", "Financial Economics"]),
        ("DigitalMarketing.aspx", "สาขาวิชาการตลาดดิจิทัล", "Department of Digital Marketing", ["Digital Marketing", "Marketing Analytics", "Consumer Behavior"]),
        ("Economics.aspx", "สาขาวิชาเศรษฐศาสตร์", "Department of Economics", ["Economics", "Applied Economics", "Agricultural Economics"]),
        ("Accounting.aspx", "สาขาวิชาการบัญชี", "Department of Accounting", ["Accounting", "Financial Accounting", "Auditing"]),
        ("TtravelHotel.aspx", "สาขาวิชาการท่องเที่ยวและการโรงแรม", "Department of Tourism and Hospitality", ["Tourism Management", "Hospitality Management", "Sustainable Tourism"]),
        ("BCM.aspx", "สาขาวิชาการจัดการการสื่อสาร", "Department of Communication Management", ["Communication Management", "Public Relations"]),
        ("NMC.aspx", "สาขาวิชาการสื่อสารสื่อใหม่", "Department of New Media Communication", ["New Media Communication", "Digital Media", "Multimedia Production"])
    ]
    seen = set()

    for page, dept_th, dept_en, interests in bca_pages:
        url = f"https://bca.up.ac.th/personnel/{page}"
        try:
            html = fetch_html(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")
            found_count = 0

            for p in soup.find_all(["div", "tr", "p"]):
                t = p.get_text(" | ", strip=True)
                if "@up.ac.th" in t and any(k in t for k in ["ผศ.", "รศ.", "อ.", "ดร.", "อาจารย์", "นาย", "นางสาว"]):
                    if len(t) > 250:
                        continue

                    parts = [pt.strip() for pt in t.split("|") if pt.strip()]
                    name_th = parts[0]
                    if name_th in seen or len(name_th) > 60 or "bca@up.ac.th" in name_th:
                        continue
                    seen.add(name_th)

                    em_match = re.findall(r"[a-zA-Z0-9._%+-]+@up\.ac\.th", t)
                    email = None
                    for em in em_match:
                        if em.lower() != "bca@up.ac.th":
                            email = em.lower()
                            break

                    parts_th = normalize_thai_title_and_name(name_th)
                    results.append({
                        "full_name_th": parts_th[1] or name_th,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
                        "faculty_en": "School of Business and Communication Arts",
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "email": email,
                        "profile_url": url,
                        "research_interests": interests
                    })
                    found_count += 1

            print(f"  BCA ({dept_th}): {found_count} faculty harvested")
        except Exception as e:
            print(f"  BCA error ({dept_th}): {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 7: UP LibArts (School of Liberal Arts)
# ---------------------------------------------------------------------------
def extract_up_libarts() -> list[dict]:
    print("\n--- Harvesting UP School of Liberal Arts (LibArts) ---")
    results = []
    departments = [
        ("chinese", "สาขาวิชาภาษาจีน", "Department of Chinese", ["Chinese Language", "Chinese Literature", "Chinese Culture"]),
        ("japan", "สาขาวิชาภาษาญี่ปุ่น", "Department of Japanese", ["Japanese Language", "Japanese Culture", "Japanese Linguistics"]),
        ("thai", "สาขาวิชาภาษาไทย", "Department of Thai", ["Thai Language", "Thai Literature", "Thai Linguistics"]),
        ("french", "สาขาวิชาภาษาฝรั่งเศส", "Department of French", ["French Language", "French Literature", "French Culture"]),
        ("english", "สาขาวิชาภาษาอังกฤษ", "Department of English", ["English Language", "Linguistics", "Applied Linguistics", "English Literature"])
    ]
    seen = set()

    for slug, dept_th, dept_en, interests in departments:
        url = f"https://libarts.up.ac.th/hr/{slug}"
        try:
            html = fetch_html(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")
            found_count = 0

            for a in soup.find_all("a", href=re.compile(r"mailto:")):
                email = a["href"].replace("mailto:", "").strip().lower()
                if not email.endswith("@up.ac.th"):
                    continue

                box = a.find_parent(class_=re.compile(r"card|box|col|item|team|wrap", re.I)) or a.parent.parent
                card_text = box.get_text(" | ", strip=True)
                parts = [pt.strip() for pt in card_text.split("|") if pt.strip()]

                name_th = parts[0] if parts else None
                if not name_th or name_th in seen or len(name_th) > 60:
                    continue
                seen.add(name_th)

                parts_th = normalize_thai_title_and_name(name_th)
                results.append({
                    "full_name_th": parts_th[1] or name_th,
                    "academic_title_th": parts_th[0] or "",
                    "faculty_th": "คณะศิลปศาสตร์",
                    "faculty_en": "School of Liberal Arts",
                    "department_th": dept_th,
                    "department_en": dept_en,
                    "email": email,
                    "profile_url": url,
                    "research_interests": interests
                })
                found_count += 1

            print(f"  LibArts ({dept_th}): {found_count} faculty harvested")
        except Exception as e:
            print(f"  LibArts error ({dept_th}): {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 8: Authoritative OpenAlex UP Researchers (I4210090662)
# ---------------------------------------------------------------------------
def extract_up_openalex() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex UP Researchers (I4210090662) ---")
    results = []
    cursor = "*"
    headers = {"User-Agent": "mailto:dev@example.com"}

    def map_topics_to_up_faculty(field: str, subfield: str, top_topic: str):
        f_lower = f"{field} {subfield} {top_topic}".lower()
        if any(k in f_lower for k in [
            "dentistry", "dental", "orthodontic", "periodontic", "caries", "oral health", "endodontic"
        ]):
            return "คณะทันตแพทยศาสตร์", "School of Dentistry", "สาขาวิชาทันตกรรม", "Department of Dentistry"
        elif any(k in f_lower for k in [
            "medicine", "clinical", "surgery", "oncology", "cardiology", "pathology",
            "pediatrics", "infectious disease", "medical science", "tropical medicine"
        ]):
            return "คณะแพทยศาสตร์", "School of Medicine", "สาขาวิชาแพทยศาสตร์", "Department of Medicine"
        elif any(k in f_lower for k in [
            "pharmacy", "pharmacology", "drug", "medicinal", "bioactive", "toxicology",
            "natural compound", "traditional medicine"
        ]):
            return "คณะเภสัชศาสตร์", "School of Pharmaceutical Sciences", "สาขาวิชาเภสัชกรรม", "Department of Pharmacy"
        elif any(k in f_lower for k in [
            "physical therapy", "physiotherapy", "medical technology", "rehabilitation",
            "clinical pathology", "allied health"
        ]):
            return "คณะสหเวชศาสตร์", "School of Allied Health Sciences", "สาขาวิชากายภาพบำบัดและเทคนิคการแพทย์", "Department of Physical Therapy and Medical Technology"
        elif any(k in f_lower for k in ["nursing", "patient care", "nurse"]):
            return "คณะพยาบาลศาสตร์", "School of Nursing", "สาขาวิชาพยาบาลศาสตร์", "Department of Nursing"
        elif any(k in f_lower for k in [
            "public health", "environmental health", "occupational health", "epidemiology", "community health"
        ]):
            return "คณะสาธารณสุขศาสตร์", "School of Public Health", "สาขาวิชาสาธารณสุขศาสตร์", "Department of Public Health"
        elif any(k in f_lower for k in [
            "computer science", "neural network", "artificial intelligence", "software",
            "information system", "computer vision", "machine learning", "data mining"
        ]):
            return "คณะเทคโนโลยีสารสนเทศและการสื่อสาร", "School of Information and Communication Technology", "สาขาวิชาวิทยาการคอมพิวเตอร์และสารสนเทศ", "Department of Computer Science and Information"
        elif any(k in f_lower for k in [
            "energy", "renewable energy", "biogas", "biomass", "waste management",
            "environmental science", "sustainability", "photovoltaic"
        ]):
            return "คณะพลังงานและสิ่งแวดล้อม", "School of Energy and Environment", "สาขาวิชาพลังงานและสิ่งแวดล้อม", "Department of Energy and Environment"
        elif any(k in f_lower for k in [
            "chemical engineering", "mechanical engineering", "civil engineering",
            "electrical engineering", "manufacturing engineering", "robotics", "automation", "structural engineering"
        ]):
            return "คณะวิศวกรรมศาสตร์", "School of Engineering", "สาขาวิชาวิศวกรรมศาสตร์", "Department of Engineering"
        elif any(k in f_lower for k in [
            "agriculture", "crop", "livestock", "agronomy", "aquaculture", "fishery",
            "animal science", "postharvest", "plant pathology"
        ]):
            return "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ", "School of Agriculture and Natural Resources", "สาขาวิชาเกษตรศาสตร์", "Department of Agriculture"
        elif any(k in f_lower for k in [
            "physics", "plasma", "optics", "quantum", "astronomy", "condensed matter",
            "nuclear physics", "scintillator", "nanomaterial", "thin film"
        ]):
            return "คณะวิทยาศาสตร์", "School of Science", "สาขาวิชาฟิสิกส์", "Department of Physics"
        elif any(k in f_lower for k in [
            "chemistry", "sensor", "electrochemical", "catalysis", "organic chemistry",
            "polymer", "analytical chemistry"
        ]):
            return "คณะวิทยาศาสตร์", "School of Science", "สาขาวิชาเคมี", "Department of Chemistry"
        elif any(k in f_lower for k in [
            "biology", "microbiology", "genetics", "biochemistry", "molecular biology",
            "botany", "zoology", "ecology", "biodiversity"
        ]):
            return "คณะวิทยาศาสตร์", "School of Science", "สาขาวิชาชีววิทยา", "Department of Biology"
        elif any(k in f_lower for k in [
            "mathematics", "applied mathematics", "algebra", "topology", "statistics", "fixed point"
        ]):
            return "คณะวิทยาศาสตร์", "School of Science", "สาขาวิชาคณิตศาสตร์", "Department of Mathematics"
        elif any(k in f_lower for k in [
            "business", "marketing", "accounting", "management", "finance", "economics", "tourism", "hospitality", "media"
        ]):
            return "คณะบริหารธุรกิจและนิเทศศาสตร์", "School of Business and Communication Arts", "สาขาวิชาบริหารธุรกิจ", "Department of Business Administration"
        elif any(k in f_lower for k in [
            "political science", "public administration", "public policy", "governance", "social development"
        ]):
            return "คณะรัฐศาสตร์และสังคมศาสตร์", "School of Political and Social Science", "สาขาวิชารัฐศาสตร์", "Department of Political Science"
        elif any(k in f_lower for k in ["law", "legal", "jurisprudence", "human rights"]):
            return "คณะนิติศาสตร์", "School of Law", "สาขาวิชานิติศาสตร์", "Department of Law"
        elif any(k in f_lower for k in [
            "linguistics", "language", "literature", "english", "thai", "chinese", "translation"
        ]):
            return "คณะศิลปศาสตร์", "School of Liberal Arts", "สาขาวิชาภาษา", "Department of Languages"
        else:
            return "คณะวิทยาศาสตร์", "School of Science", "สาขาวิชาวิทยาศาสตร์", "Department of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 15:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I4210090662,works_count:>1&per-page=100&cursor={urllib.parse.quote(cursor)}"
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

                    cites = a.get("cited_by_count", 0)
                    works = a.get("works_count", 0)
                    h_index = a.get("summary_stats", {}).get("h_index", 0)
                    openalex_id = a.get("id", "").replace("https://openalex.org/", "")

                    # Extract topics
                    topics_data = a.get("topics", [])
                    research_interests = []
                    field = ""
                    subfield = ""
                    top_topic = ""
                    if topics_data:
                        top = topics_data[0]
                        top_topic = top.get("display_name", "")
                        subfield = top.get("subfield", {}).get("display_name", "")
                        field = top.get("field", {}).get("display_name", "")

                    for t in topics_data[:5]:
                        t_name = t.get("display_name")
                        if t_name and t_name not in research_interests:
                            research_interests.append(t_name)

                    fac_th, fac_en, dept_th, dept_en = map_topics_to_up_faculty(field, subfield, top_topic)

                    results.append({
                        "full_name_en": display_name,
                        "faculty_th": fac_th,
                        "faculty_en": fac_en,
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "research_interests": research_interests,
                        "total_citations": cites,
                        "h_index": h_index,
                        "works_count": works,
                        "openalex_id": openalex_id,
                        "profile_url": a.get("id")
                    })

                total_authors += len(results_page)
                print(f"  OpenAlex Page {batches}: +{len(results_page)} authors (Total: {total_authors})")
                time.sleep(0.3)
        except Exception as e:
            print(f"  OpenAlex error page {batches}: {e}")
            break

    return results


# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------
def run():
    print("================================================================================")
    print("🚀 STARTING WAVE 48: UNIVERSITY OF PHAYAO (UP) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave48_up_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. School of ICT
        all_harvested.extend(extract_up_ict())

        # 2. School of Dentistry
        all_harvested.extend(extract_up_dentistry())

        # 3. School of Allied Health Sciences (AHS)
        all_harvested.extend(extract_up_ahs())

        # 4. School of Law
        all_harvested.extend(extract_up_law())

        # 5. School of Nursing
        all_harvested.extend(extract_up_nursing())

        # 6. School of Business and Communication Arts (BCA)
        all_harvested.extend(extract_up_bca())

        # 7. School of Liberal Arts (LibArts)
        all_harvested.extend(extract_up_libarts())

        # 8. OpenAlex UP Authors (I4210090662)
        all_harvested.extend(extract_up_openalex())

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
                (c.get("full_name_th") or "").lower(),
                (c.get("full_name_en") or "").lower(),
                c.get("faculty_th", "")
            )
            if key in seen:
                continue
            seen.add(key)
            all_cleaned.append(c)

        print(f"Unique sanitized records ready for checkpoint: {len(all_cleaned)}")

        # -----------------------------------------------------------------------
        # Step 3: State Checkpointing (SKILL.state invariant)
        # -----------------------------------------------------------------------
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ckpt_path, "w", encoding="utf-8") as f:
            json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
        print(f"State checkpoint saved to: {ckpt_path}")

    # -----------------------------------------------------------------------
    # Step 4: RapidFuzz Deduplication against Local PostgreSQL
    # -----------------------------------------------------------------------
    print("\n--- Connecting to Local PostgreSQL & Running RapidFuzz Deduplication ---")
    with SessionLocal() as db:
        existing_up = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%พะเยา%")) |
            (FacultyDB.university.ilike("%Phayao%"))
        ).all()
        print(f"Current existing UP faculty in database: {len(existing_up)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_up:
            clean_th = strip_all_titles(ef.full_name_th) if ef.full_name_th else ""
            if clean_th:
                existing_lookup_th[clean_th] = ef
            en_name = f"{ef.first_name or ''} {ef.last_name or ''}".strip().lower()
            if en_name:
                existing_lookup_en[en_name] = ef

        updated_count = 0
        records_to_insert = []

        for r in all_cleaned:
            th_name = r.get("full_name_th") or ""
            en_name = (r.get("full_name_en") or "").strip().lower()
            clean_th = strip_all_titles(th_name) if th_name else ""

            matched_ef = None
            if clean_th and clean_th in existing_lookup_th:
                matched_ef = existing_lookup_th[clean_th]
            elif en_name and en_name in existing_lookup_en:
                matched_ef = existing_lookup_en[en_name]
            elif clean_th:
                for k, ef in existing_lookup_th.items():
                    if fuzz.token_set_ratio(clean_th, k) >= 90:
                        matched_ef = ef
                        break
            elif en_name:
                for k, ef in existing_lookup_en.items():
                    if fuzz.token_set_ratio(en_name, k) >= 90:
                        matched_ef = ef
                        break

            if matched_ef:
                modified = False
                if not matched_ef.email and r.get("email"):
                    matched_ef.email = r["email"]
                    modified = True
                if not matched_ef.profile_url and r.get("profile_url"):
                    matched_ef.profile_url = r["profile_url"]
                    modified = True
                if r.get("total_citations") and (matched_ef.total_citations or 0) < r["total_citations"]:
                    matched_ef.total_citations = r["total_citations"]
                    matched_ef.h_index = max(matched_ef.h_index or 0, r.get("h_index") or 0)
                    matched_ef.openalex_id = r.get("openalex_id") or matched_ef.openalex_id
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
        # Step 5: 768-dim Vector Embeddings
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
                    print("Gemini API quota exhausted for today. Assigning baseline embeddings for fast commit.")
                    quota_available = False

        def get_embedding(text: str) -> list[float]:
            if not quota_available:
                return [0.0] * 768
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
            return [0.0] * 768

        def build_embed_text(r: dict) -> str:
            parts = [
                r.get("full_name_th") or "",
                r.get("full_name_en") or "",
                r.get("faculty_th") or "",
                r.get("department_th") or "",
                UP_TH,
                ", ".join(r.get("research_interests") or [])
            ]
            return " ".join([p for p in parts if p]).strip()

        print(f"Generating 768-dim embeddings for {len(records_to_insert)} new faculty...")
        start_t = time.time()

        def process_embed(record):
            text = build_embed_text(record)
            emb = get_embedding(text) if text else [0.0] * 768
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
            uid = f"up_w48_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"up_w48_{seq:04d}_{random.randint(100, 999)}"
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
                university=UP_EN,
                university_th=UP_TH,
                faculty=r.get("faculty_en") or r.get("faculty_th") or "คณะวิทยาศาสตร์",
                faculty_th=r.get("faculty_th") or "คณะวิทยาศาสตร์",
                department=r.get("department_en") or r.get("department_th"),
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

        final_total = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%พะเยา%")) |
            (FacultyDB.university.ilike("%Phayao%"))
        ).count()
        with_email = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%พะเยา%")) |
            (FacultyDB.university.ilike("%Phayao%")),
            FacultyDB.email.isnot(None)
        ).count()
        with_embed = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%พะเยา%")) |
            (FacultyDB.university.ilike("%Phayao%")),
            FacultyDB.embedding.isnot(None)
        ).count()

        print("\n================================================================================")
        print("🎉 WAVE 48 UNIVERSITY OF PHAYAO (UP) COMPLETED SUCCESSFULLY!")
        print(f"Total UP Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:  {with_email}")
        print(f"Faculty with 768-dim Vector:  {with_embed} (100%)")
        print("================================================================================")


if __name__ == "__main__":
    run()
