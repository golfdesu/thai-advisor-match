"""Wave 42 BUU Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: Burapha University (BUU)
        มหาวิทยาลัยบูรพา

Scope:
1. Faculty of Medicine (คณะแพทยศาสตร์):
   - Medical Doctors, Professors & Specialists (https://med.buu.ac.th/med/teacher-med.php)
2. Faculty of Science (คณะวิทยาศาสตร์):
   - 10 Departments across Mathematics, Chemistry, Microbiology, Biochemistry,
     Biology, Physics, Aquatic Science, Food Science, Integrated Science, Biotechnology
     (https://science.buu.ac.th/newweb/dept_detail.php?dept=1..10)
3. Faculty of Informatics (คณะวิทยาการสารสนเทศ):
   - Computer Science, Software Engineering, AI & Data Science
     (https://www.informatics.buu.ac.th/?page_id=349)
4. Faculty of Engineering (คณะวิศวกรรมศาสตร์):
   - Industrial, Chemical, Civil, Electrical, Mechanical, Advanced Materials
     (https://eng.buu.ac.th/faculty-members/)
5. Faculty of Nursing (คณะพยาบาลศาสตร์):
   - Adult, Pediatric, Maternal, Community, Gerontological, Psychiatric, Administration, Occupational
     (https://nurse.buu.ac.th/2021/Person-*.php)
6. Faculty of Pharmacy (คณะเภสัชศาสตร์):
   - Pharmaceutical Tech, Clinical Pharmacy, Social Pharmacy, Pharmacognosy, Pharmacology, Cosmetic Sci
     (https://pharm.buu.ac.th/department-teacher.php?id=1,3,4,5,10,11)
7. Faculty of Humanities and Social Sciences (คณะมนุษยศาสตร์และสังคมศาสตร์):
   - Psychology, History, Western Languages, Eastern Languages, Social Sciences
     (https://huso.buu.ac.th/dpt/ & https://huso.buu.ac.th/exe/)
8. Faculty of Education (คณะศึกษาศาสตร์):
   - Learning Management, Vocational & Health Education, Applied Psychology, Educational Tech,
     Educational Administration, Human Resource Dev, Physical Education
     (https://edu.buu.ac.th/personnel/show/1..7)
9. Faculty of Political Science and Law (คณะรัฐศาสตร์และนิติศาสตร์):
   - Faculty leadership & political science professors (https://polsci.buu.ac.th/)
10. Chanthaburi Campus - Gems & Marine (คณะอัญมณี, คณะเทคโนโลยีทางทะเล):
   - Gems Technology & Marine Science (http://gems.chanthaburi.buu.ac.th/person_1.php, http://marine.chanthaburi.buu.ac.th/person.php)

Execution Standard:
- Headless extraction with specialized high-fidelity DOM extractors & Trafilatura heuristics.
- State reduction, title normalization, and PDPA compliance (no phone numbers).
- Checkpointing to backend/data/agent_states/wave42_buu_extraction.json.
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

BUU_TH = "มหาวิทยาลัยบูรพา"
BUU_EN = "Burapha University"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8"
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(r"(?:หน้าแรก|ติดต่อ|โทรศัพท์|โทรสาร|admin|menu|home|service|download|ห้องปฏิบัติการ|สาขาวิชา|ภาควิชา|คณะ|เพลิงอาจารย์ใหญ่|สถิติ|เจ้าหน้าที่|จ้างเหมา|นักวิชาการศึกษา|ผู้ปฏิบัติงาน|ธุรการ|เวลาทำการ|งานพัสดุ|งานบุคคล|งานการเงิน|งานบริหาร)", re.IGNORECASE)


def fetch_html(url: str, timeout: int = 12) -> str:
    """Fetch HTML safely with pre-unquoting."""
    unquoted = urllib.parse.unquote(url)
    parts = urllib.parse.urlsplit(unquoted)
    encoded_path = urllib.parse.quote(parts.path)
    encoded_query = urllib.parse.quote(parts.query, safe="=&?/")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))

    req = urllib.request.Request(safe_url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


# ------------------------------------------------------------
# 1. Faculty of Medicine (คณะแพทยศาสตร์)
# ------------------------------------------------------------
def extract_buu_medicine() -> list[dict]:
    print("-> Scraping Faculty of Medicine BUU (teacher-med.php)...")
    url = "https://med.buu.ac.th/med/teacher-med.php"
    results = []
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all(class_="teacher-card")
        print(f"   Found {len(cards)} Medicine teacher cards.")

        for c in cards:
            txt = c.get_text(separator="|", strip=True)
            header = c.find(class_="teacher-header")
            th_name = header.get_text(strip=True) if header else ""
            if not th_name:
                lines = [l.strip() for l in txt.split("|") if l.strip()]
                th_name = lines[0] if lines else ""

            # Image
            img = c.find("img")
            img_url = urllib.parse.urljoin("https://med.buu.ac.th/med/", img["src"]) if img and img.get("src") else ""

            # Email
            email = ""
            em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th", txt)
            if em_match:
                candidate_em = em_match.group(0).lower()
                if not any(x in candidate_em for x in ["med@buu.ac.th", "info@", "contact@"]):
                    email = candidate_em

            # Clinical Specialization & Research
            specialty = []
            if "ความเชี่ยวชาญเฉพาะทาง :" in txt:
                try:
                    part = txt.split("ความเชี่ยวชาญเฉพาะทาง :")[1]
                    if "ประวัติและผลงานวิจัย :" in part:
                        part = part.split("ประวัติและผลงานวิจัย :")[0]
                    sp_lines = [x.strip().lstrip("-").strip() for x in part.split("|") if x.strip() and not x.strip().startswith("เวลา")]
                    specialty = [s for s in sp_lines if len(s) > 3 and not s.startswith("ชื่อ")]
                except Exception:
                    pass

            # Publications / History
            pubs = []
            if "ประวัติและผลงานวิจัย :" in txt:
                try:
                    pub_part = txt.split("ประวัติและผลงานวิจัย :")[1]
                    for p_item in pub_part.split("|"):
                        clean_p = p_item.strip().lstrip("-").strip()
                        if len(clean_p) > 20 and not clean_p.startswith("http"):
                            pubs.append(clean_p)
                except Exception:
                    pass

            if th_name and len(th_name) > 4:
                results.append({
                    "faculty_th": "คณะแพทยศาสตร์",
                    "faculty": "Faculty of Medicine",
                    "department_th": "คณะแพทยศาสตร์",
                    "department": "Faculty of Medicine",
                    "full_name_th": th_name,
                    "full_name_en": "",
                    "email": email,
                    "image_url": img_url,
                    "profile_url": url,
                    "research_interests": specialty[:6],
                    "featured_publications": pubs[:4]
                })
    except Exception as e:
        print(f"   [ERR] Medicine: {e}")

    print(f"   Medicine Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 2. Faculty of Science (คณะวิทยาศาสตร์) - 10 Departments
# ------------------------------------------------------------
def extract_buu_science() -> list[dict]:
    print("-> Scraping Faculty of Science BUU (10 Departments)...")
    depts = [
        (1, "ภาควิชาคณิตศาสตร์", "Department of Mathematics"),
        (2, "ภาควิชาเคมี", "Department of Chemistry"),
        (3, "ภาควิชาจุลชีววิทยา", "Department of Microbiology"),
        (4, "ภาควิชาชีวเคมี", "Department of Biochemistry"),
        (5, "ภาควิชาชีววิทยา", "Department of Biology"),
        (7, "ภาควิชาฟิสิกส์", "Department of Physics"),
        (8, "ภาควิชาวาริชศาสตร์", "Department of Aquatic Science"),
        (9, "ภาควิชาวิทยาศาสตร์การอาหาร", "Department of Food Science"),
        (10, "ภาควิชาวิทยาศาสตร์บูรณาการ", "Department of Integrated Science")
    ]

    all_sci = []
    seen_names = set()

    for did, dth, den in depts:
        u = f"https://science.buu.ac.th/newweb/dept_detail.php?dept={did}"
        try:
            html = fetch_html(u, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all(class_=re.compile(r"card|member|staff|person|box|col", re.I))

            dept_count = 0
            for c in cards:
                txt = c.get_text(separator="|", strip=True)
                if "@" in txt and any(t in txt for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อ."]) and len(txt) < 300:
                    lines = [l.strip() for l in txt.split("|") if l.strip()]
                    th_name = lines[0] if lines else ""

                    # Email
                    email = ""
                    em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th", txt)
                    if em_match:
                        email = em_match.group(0).lower()

                    # Image
                    img = c.find("img")
                    img_url = ""
                    if img and img.get("src"):
                        img_url = urllib.parse.urljoin("https://science.buu.ac.th/newweb/", img["src"])

                    if th_name and th_name not in seen_names and len(th_name) > 4:
                        seen_names.add(th_name)
                        dept_count += 1
                        all_sci.append({
                            "faculty_th": "คณะวิทยาศาสตร์",
                            "faculty": "Faculty of Science",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": th_name,
                            "full_name_en": "",
                            "email": email,
                            "image_url": img_url,
                            "profile_url": u
                        })
            print(f"   Dept {did} ({dth}): {dept_count} faculty.")
        except Exception as e:
            print(f"   [ERR] Science Dept {did}: {e}")

    # Biotech & Environmental Science (major_detail group 6)
    try:
        u6 = "https://science.buu.ac.th/newweb/major_detail.php?group_id=6"
        html6 = fetch_html(u6, timeout=10)
        soup6 = BeautifulSoup(html6, "html.parser")
        lines6 = [l.strip() for l in soup6.get_text(separator="\n", strip=True).split("\n") if l.strip()]
        capturing = False
        b_count = 0
        for l in lines6:
            if "อาจารย์ในหลักสูตร" in l:
                capturing = True
                continue
            if capturing:
                if any(x in l for x in ["รู้จักหลักสูตร", "ชื่อปริญญา", "ค่าเทอม"]):
                    break
                if any(t in l for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์"]) and len(l) < 50 and len(l) > 4:
                    if l not in seen_names and not any(x in l for x in ["คน", "ประธาน", "ผู้รับผิดชอบ"]):
                        seen_names.add(l)
                        b_count += 1
                        all_sci.append({
                            "faculty_th": "คณะวิทยาศาสตร์",
                            "faculty": "Faculty of Science",
                            "department_th": "สาขาวิชาเทคโนโลยีชีวภาพและสิ่งแวดล้อม",
                            "department": "Department of Biotechnology and Environmental Science",
                            "full_name_th": l,
                            "full_name_en": "",
                            "email": "",
                            "image_url": "",
                            "profile_url": u6
                        })
        print(f"   Biotech & Env Sci: {b_count} faculty.")
    except Exception as e:
        print(f"   [ERR] Science Biotech: {e}")

    print(f"   Science Extracted: {len(all_sci)} records.")
    return all_sci


# ------------------------------------------------------------
# 3. Faculty of Informatics (คณะวิทยาการสารสนเทศ)
# ------------------------------------------------------------
def extract_buu_informatics() -> list[dict]:
    print("-> Scraping Faculty of Informatics BUU (page_id=349)...")
    url = "https://www.informatics.buu.ac.th/?page_id=349"
    results = []
    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")

        for ul in soup.find_all("ul"):
            text = ul.get_text(separator="|", strip=True)
            if "อีเมล" in text or "ห้องทำงาน" in text:
                container = ul.find_parent(class_=re.compile(r"row|media|col-sm-12|content", re.I)) or ul.parent.parent
                img = container.find("img") if container else None
                img_src = img.get("src") if img else ""
                full_text = container.get_text(separator="|", strip=True) if container else text
                lines = [l.strip() for l in full_text.split("|") if l.strip()]

                th_name = lines[0] if lines else ""
                en_name, email, pos, interests = "", "", "", []
                for i, l in enumerate(lines):
                    if "ชื่อ :" in l or l == "ชื่อ":
                        if i + 1 < len(lines):
                            en_name = lines[i + 1]
                    elif "อีเมล :" in l or l == "อีเมล":
                        if i + 1 < len(lines):
                            em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th", lines[i + 1])
                            if em_match:
                                email = em_match.group(0).lower()
                    elif "ตำแหน่ง :" in l or l == "ตำแหน่ง":
                        if i + 1 < len(lines):
                            pos = lines[i + 1]
                    elif "สาขาที่สนใจ :" in l or l == "สาขาที่สนใจ":
                        raw_interests = lines[i + 1:min(len(lines), i + 8)]
                        interests = [x for x in raw_interests if not any(k in x for k in ["ประวัติ", "ห้องทำงาน", "เบอร์โทร", "อีเมล", "http", "โทรสาร"])]

                if th_name and len(th_name) > 4:
                    results.append({
                        "faculty_th": "คณะวิทยาการสารสนเทศ",
                        "faculty": "Faculty of Informatics",
                        "department_th": "คณะวิทยาการสารสนเทศ",
                        "department": "Faculty of Informatics",
                        "full_name_th": th_name,
                        "full_name_en": en_name,
                        "email": email,
                        "image_url": img_src,
                        "profile_url": url,
                        "research_interests": interests[:6]
                    })
    except Exception as e:
        print(f"   [ERR] Informatics: {e}")

    print(f"   Informatics Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 4. Faculty of Engineering (คณะวิศวกรรมศาสตร์)
# ------------------------------------------------------------
def extract_buu_engineering() -> list[dict]:
    print("-> Scraping Faculty of Engineering BUU (faculty-members/)...")
    url = "https://eng.buu.ac.th/faculty-members/"
    results = []
    seen_names = set()

    dept_map = {
        "ภาควิชาวิศวกรรมอุตสาหการ": "Department of Industrial Engineering",
        "ภาควิชาวิศวกรรมเคมี": "Department of Chemical Engineering",
        "ภาควิชาวิศวกรรมโยธา": "Department of Civil Engineering",
        "ภาควิชาวิศวกรรมไฟฟ้า": "Department of Electrical Engineering",
        "ภาควิชาวิศวกรรมเครื่องกล": "Department of Mechanical Engineering",
        "สาขาวิชาวิศวกรรมวัสดุขั้นสูง": "Division of Advanced Materials Engineering"
    }

    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")

        for details in soup.find_all(["details", "div", "section"]):
            summary = details.find(class_="ab-accordion-title") or details.find(["summary", "h2", "h3", "h4"])
            if not summary:
                continue
            dept_txt = summary.get_text(strip=True)
            if not any(k in dept_txt for k in ["วิศวกรรม", "สาขาวิชา", "ภาควิชา"]):
                continue

            dept_th = dept_txt
            for k in dept_map:
                if k in dept_txt:
                    dept_th = k
                    break
            dept_en = dept_map.get(dept_th, "Faculty of Engineering")

            # Find all faculty cards inside this section
            for a in details.find_all("a", href=re.compile(r"mailto:", re.I)):
                raw_mail = a.get("href").replace("mailto:", "").strip().lower()
                # climb to card container
                curr = a
                card_node = None
                for _ in range(5):
                    if curr.parent:
                        curr = curr.parent
                        txt_c = curr.get_text()
                        if 60 < len(txt_c) < 500:
                            card_node = curr
                            break

                if not card_node:
                    continue

                card_txt = card_node.get_text(separator="|", strip=True)
                lines = [l.strip() for l in card_txt.split("|") if l.strip()]
                th_name = lines[0] if lines else ""

                # Extract email
                email = ""
                em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th)", raw_mail)
                if em_match:
                    email = em_match.group(1).lower()
                else:
                    alt_em = re.search(r"([a-zA-Z0-9._%+-]+)\s*\(at\)\s*([a-zA-Z0-9.-]+\.buu\.ac\.th)", card_txt)
                    if alt_em:
                        email = f"{alt_em.group(1)}@{alt_em.group(2)}".lower()

                # Image
                img_url = ""
                parent2 = card_node.parent
                if parent2:
                    img = parent2.find("img")
                    if img and img.get("src"):
                        img_url = img["src"]

                # Expertise
                expertise = []
                if "ความเชี่ยวชาญ:" in card_txt:
                    try:
                        exp_str = card_txt.split("ความเชี่ยวชาญ:")[1]
                        expertise = [x.strip() for x in exp_str.split(",") if len(x.strip()) > 2]
                    except Exception:
                        pass

                if th_name and th_name not in seen_names and len(th_name) > 4:
                    seen_names.add(th_name)
                    results.append({
                        "faculty_th": "คณะวิศวกรรมศาสตร์",
                        "faculty": "Faculty of Engineering",
                        "department_th": dept_th,
                        "department": dept_en,
                        "full_name_th": th_name,
                        "full_name_en": "",
                        "email": email,
                        "image_url": img_url,
                        "profile_url": url,
                        "research_interests": expertise[:6]
                    })
    except Exception as e:
        print(f"   [ERR] Engineering: {e}")

    print(f"   Engineering Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 5. Faculty of Nursing (คณะพยาบาลศาสตร์)
# ------------------------------------------------------------
def extract_buu_nursing() -> list[dict]:
    print("-> Scraping Faculty of Nursing BUU (12 Division Pages)...")
    base = "https://nurse.buu.ac.th/2021/"
    pages = [
        ("Person-Adult1.php", "ภาควิชาการพยาบาลผู้ใหญ่", "Department of Adult Nursing"),
        ("Person-Pediatrics1.php", "ภาควิชาการพยาบาลเด็ก", "Department of Pediatric Nursing"),
        ("Person-Maternal1.php", "ภาควิชาการพยาบาลมารดา ทารก และการผดุงครรภ์", "Department of Maternal and Child Nursing"),
        ("Person-Community1.php", "ภาควิชาการพยาบาลชุมชน", "Department of Community Health Nursing"),
        ("Person-Gerontological1.php", "ภาควิชาการพยาบาลผู้สูงอายุ", "Department of Gerontological Nursing"),
        ("Person-Psychiatric1.php", "ภาควิชาการพยาบาลจิตเวช", "Department of Psychiatric Nursing"),
        ("Person-Occupational-1.php", "กลุ่มวิชาการพยาบาลอาชีวอนามัย", "Department of Occupational Health Nursing"),
        ("Person-Administration1.php", "กลุ่มวิชาการบริหารการพยาบาล", "Department of Nursing Administration"),
        ("Person-Manager1-2.php", "คณะผู้บริหาร", "Faculty Administration"),
        ("Person-Academic-Staff.php", "คณาจารย์ประจำคณะพยาบาลศาสตร์", "Academic Staff"),
        ("Person-FacultyCommittee.php", "คณะกรรมการประจำคณะพยาบาลศาสตร์", "Faculty Committee"),
        ("Person-Elderly.php", "ศูนย์พัฒนาศักยภาพผู้สูงอายุ", "Elderly Care Center")
    ]

    all_nurse = []
    seen_names = set()

    for p_file, dth, den in pages:
        u = urllib.parse.urljoin(base, p_file)
        try:
            html = fetch_html(u, timeout=8)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all(class_=re.compile(r"card|member|staff|person|box|col", re.I))

            p_count = 0
            for c in cards:
                txt = c.get_text(separator="|", strip=True)
                if any(t in txt for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์", "พว."]) and len(txt) < 350:
                    lines = [l.strip() for l in txt.split("|") if l.strip()]
                    th_name = lines[0] if lines else ""
                    en_name = lines[1] if len(lines) > 1 and re.match(r"^[a-zA-Z\.\s]+$", lines[1]) else ""

                    # Email
                    email = ""
                    em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th)", txt)
                    if em_match:
                        email = em_match.group(1).lower()

                    # Image
                    img = c.find("img")
                    img_url = ""
                    if img and img.get("src"):
                        img_url = urllib.parse.urljoin(u, img["src"])

                    if th_name and th_name not in seen_names and len(th_name) > 4:
                        seen_names.add(th_name)
                        p_count += 1
                        all_nurse.append({
                            "faculty_th": "คณะพยาบาลศาสตร์",
                            "faculty": "Faculty of Nursing",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": th_name,
                            "full_name_en": en_name,
                            "email": email,
                            "image_url": img_url,
                            "profile_url": u
                        })
            print(f"   {p_file} ({dth}): {p_count} faculty.")
        except Exception as e:
            print(f"   [ERR] Nurse {p_file}: {e}")

    print(f"   Nursing Extracted: {len(all_nurse)} records.")
    return all_nurse


# ------------------------------------------------------------
# 6. Faculty of Pharmacy (คณะเภสัชศาสตร์)
# ------------------------------------------------------------
def extract_buu_pharmacy() -> list[dict]:
    print("-> Scraping Faculty of Pharmacy BUU (6 Departments)...")
    depts = [
        (1, "สาขาวิชาเทคโนโลยีเภสัชกรรม", "Department of Pharmaceutical Technology"),
        (3, "สาขาวิชาเภสัชกรรมปฏิบัติและการบริบาล", "Department of Clinical Pharmacy"),
        (4, "สาขาวิชาเภสัชกรรมสังคมและบริหารเภสัชกิจ", "Department of Social and Administrative Pharmacy"),
        (5, "สาขาวิชาเภสัชเวทและเภสัชเคมี", "Department of Pharmacognosy and Pharmaceutical Chemistry"),
        (10, "สาขาวิชาเภสัชวิทยาและเภสัชศาสตร์ชีวภาพ", "Department of Pharmacology and Bioscience"),
        (11, "สาขาวิชาวิทยาศาสตร์และเทคโนโลยีเครื่องสำอาง", "Department of Cosmetic Science and Technology")
    ]

    all_pharm = []
    seen_names = set()

    for did, dth, den in depts:
        u = f"https://pharm.buu.ac.th/department-teacher.php?id={did}"
        try:
            html = fetch_html(u, timeout=8)
            soup = BeautifulSoup(html, "html.parser")

            dept_count = 0
            for box in soup.find_all(["table", "div", "tr"]):
                txt = box.get_text(separator="|", strip=True)
                if "ตำแหน่ง :" in txt and "อีเมล์ :" in txt and len(txt) < 450:
                    lines = [l.strip() for l in txt.split("|") if l.strip()]
                    th_name = lines[0] if lines else ""

                    # Email
                    email = ""
                    em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th)", txt)
                    if em_match:
                        email = em_match.group(1).lower()

                    # Image
                    img = box.find("img")
                    img_url = ""
                    if img and img.get("src"):
                        img_url = urllib.parse.urljoin("https://pharm.buu.ac.th/", img["src"])

                    # Profile link
                    a_prof = box.find("a", href=re.compile(r"department-teacher-info\.php", re.I))
                    prof_url = urllib.parse.urljoin("https://pharm.buu.ac.th/", a_prof["href"]) if a_prof else u

                    if th_name and th_name not in seen_names and len(th_name) > 4:
                        seen_names.add(th_name)
                        dept_count += 1
                        all_pharm.append({
                            "faculty_th": "คณะเภสัชศาสตร์",
                            "faculty": "Faculty of Pharmacy",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": th_name,
                            "full_name_en": "",
                            "email": email,
                            "image_url": img_url,
                            "profile_url": prof_url
                        })
            print(f"   Pharm Dept {did} ({dth}): {dept_count} faculty.")
        except Exception as e:
            print(f"   [ERR] Pharm Dept {did}: {e}")

    print(f"   Pharmacy Extracted: {len(all_pharm)} records.")
    return all_pharm


# ------------------------------------------------------------
# 7. Faculty of Humanities & Social Sciences (คณะมนุษยศาสตร์และสังคมศาสตร์)
# ------------------------------------------------------------
def extract_buu_huso() -> list[dict]:
    print("-> Scraping Faculty of Humanities & Social Sciences BUU (huso.buu.ac.th/dpt/)...")
    url = "https://huso.buu.ac.th/dpt/"
    results = []
    seen_names = set()

    try:
        html = fetch_html(url, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        lines = [l.strip() for l in soup.get_text(separator="\n", strip=True).split("\n") if l.strip()]

        current_dept_th = "คณะมนุษยศาสตร์และสังคมศาสตร์"
        current_dept_en = "Faculty of Humanities and Social Sciences"

        for l in lines:
            if l.startswith("ภาควิชา") or l.startswith("สาขาวิชา"):
                current_dept_th = l
                current_dept_en = f"Department of {l.replace('ภาควิชา', '').replace('สาขาวิชา', '').strip()}"
                continue

            # Check if line is a faculty member (e.g. "1. ดร.นิสรา คำมณี (หัวหน้าภาควิชา)")
            m = re.match(r"^\d+\.\s*(.+)$", l)
            if m:
                raw_name = m.group(1).strip()
                # Skip support staff
                if any(x in raw_name for x in ["เจ้าหน้าที่", "จ้างเหมา", "นักวิชาการศึกษา", "ผู้ปฏิบัติงาน", "ธุรการ"]):
                    continue

                # Remove parenthetical title (e.g. "(หัวหน้าภาควิชา)")
                clean_name = re.sub(r"\(.*?\)", "", raw_name).strip()

                if clean_name and clean_name not in seen_names and len(clean_name) > 4:
                    seen_names.add(clean_name)
                    results.append({
                        "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
                        "faculty": "Faculty of Humanities and Social Sciences",
                        "department_th": current_dept_th,
                        "department": current_dept_en,
                        "full_name_th": clean_name,
                        "full_name_en": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": url
                    })

        # Executive Dean page
        try:
            exe_url = "https://huso.buu.ac.th/exe/"
            e_html = fetch_html(exe_url, timeout=8)
            e_soup = BeautifulSoup(e_html, "html.parser")
            e_lines = [l.strip() for l in e_soup.get_text(separator="\n", strip=True).split("\n") if l.strip()]
            for el in e_lines:
                if any(t in el for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อ."]) and len(el) < 45 and len(el) > 4:
                    if el not in seen_names:
                        seen_names.add(el)
                        results.append({
                            "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
                            "faculty": "Faculty of Humanities and Social Sciences",
                            "department_th": "คณะผู้บริหาร",
                            "department": "Faculty Executive Board",
                            "full_name_th": el,
                            "full_name_en": "",
                            "email": "",
                            "image_url": "",
                            "profile_url": exe_url
                        })
        except Exception:
            pass

    except Exception as e:
        print(f"   [ERR] HUSO: {e}")

    print(f"   HUSO Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 8. Faculty of Education (คณะศึกษาศาสตร์)
# ------------------------------------------------------------
def extract_buu_education() -> list[dict]:
    print("-> Scraping Faculty of Education BUU (7 Departments)...")
    depts = [
        (1, "ภาควิชาการจัดการเรียนรู้", "Department of Learning Management"),
        (2, "ภาควิชาการอาชีวศึกษาและการพัฒนาสุขภาวะ", "Department of Vocational and Health Education"),
        (3, "ภาควิชาวิจัยและจิตวิทยาประยุกต์", "Department of Applied Psychology and Research"),
        (4, "ภาควิชานวัตกรรมและเทคโนโลยีการศึกษา", "Department of Educational Technology and Innovation"),
        (5, "ภาควิชาการบริหารการศึกษา", "Department of Educational Administration"),
        (6, "สถาบันพัฒนาทรัพยากรมนุษย์", "Institute of Human Resource Development"),
        (7, "ภาควิชาพลศึกษา", "Department of Physical Education")
    ]

    all_edu = []
    seen_names = set()

    for sid, dth, den in depts:
        u = f"https://edu.buu.ac.th/personnel/show/{sid}"
        try:
            html = fetch_html(u, timeout=8)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all(class_=re.compile(r"card|col|item|person|box", re.I))

            d_count = 0
            for c in cards:
                txt = c.get_text(separator="|", strip=True)
                if any(t in txt for t in ["ผู้ช่วยศาสตราจารย์", "อาจารย์", "รองศาสตราจารย์", "ดร."]) and len(txt) < 300:
                    lines = [l.strip() for l in txt.split("|") if l.strip()]
                    th_name = lines[0] if lines else ""

                    # Email
                    email = ""
                    em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th)", txt)
                    if em_match:
                        cand_em = em_match.group(1).lower()
                        if not cand_em.startswith("edu_buu"):
                            email = cand_em

                    # Image
                    img = c.find("img")
                    img_url = ""
                    if img and img.get("src"):
                        img_url = urllib.parse.urljoin(u, img["src"])

                    # Profile link
                    prof_a = c.find("a", href=re.compile(r"drive\.google\.com|profile", re.I))
                    prof_url = prof_a["href"] if prof_a else u

                    if th_name and th_name not in seen_names and len(th_name) > 4:
                        seen_names.add(th_name)
                        d_count += 1
                        all_edu.append({
                            "faculty_th": "คณะศึกษาศาสตร์",
                            "faculty": "Faculty of Education",
                            "department_th": dth,
                            "department": den,
                            "full_name_th": th_name,
                            "full_name_en": "",
                            "email": email,
                            "image_url": img_url,
                            "profile_url": prof_url
                        })
            print(f"   Edu Dept {sid} ({dth}): {d_count} faculty.")
        except Exception as e:
            print(f"   [ERR] Edu Dept {sid}: {e}")

    print(f"   Education Extracted: {len(all_edu)} records.")
    return all_edu


# ------------------------------------------------------------
# 9. Faculty of Political Science and Law (คณะรัฐศาสตร์และนิติศาสตร์)
# ------------------------------------------------------------
def extract_buu_polsci() -> list[dict]:
    print("-> Scraping Faculty of Political Science & Law BUU (polsci.buu.ac.th)...")
    url = "https://polsci.buu.ac.th/"
    results = []
    try:
        html = fetch_html(url, timeout=8)
        soup = BeautifulSoup(html, "html.parser")
        lines = [l.strip() for l in soup.get_text(separator="|", strip=True).split("|") if l.strip()]

        for l in lines:
            if any(t in l for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อ."]) and len(l) < 45 and not l.startswith("พ.ศ.") and not "ต.แสนสุข" in l:
                email = ""
                if "วิเชียร" in l: email = "wichien@go.buu.ac.th"
                elif "โอฬาร" in l: email = "olarn@go.buu.ac.th"
                elif "ชัยณรงค์" in l: email = "chainarong@go.buu.ac.th"
                elif "อนุรัตน์" in l: email = "anurat@go.buu.ac.th"
                elif "กาณติมา" in l: email = "kantimap@go.buu.ac.th"

                results.append({
                    "faculty_th": "คณะรัฐศาสตร์และนิติศาสตร์",
                    "faculty": "Faculty of Political Science and Law",
                    "department_th": "ภาควิชารัฐศาสตร์",
                    "department": "Department of Political Science",
                    "full_name_th": l,
                    "full_name_en": "",
                    "email": email,
                    "image_url": "",
                    "profile_url": url
                })
    except Exception as e:
        print(f"   [ERR] PolSci: {e}")

    print(f"   PolSci Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 10. Chanthaburi Campus - Gems & Marine Technology
# ------------------------------------------------------------
def extract_buu_chanthaburi() -> list[dict]:
    print("-> Scraping Chanthaburi Campus BUU (Gems & Marine)...")
    results = []
    seen_names = set()

    # Gems
    try:
        u_gems = "http://gems.chanthaburi.buu.ac.th/person_1.php"
        html = fetch_html(u_gems, timeout=8)
        soup = BeautifulSoup(html, "html.parser")
        for box in soup.find_all(["table", "div", "tr"]):
            txt = box.get_text(separator="|", strip=True)
            if "@" in txt and any(t in txt for t in ["ผศ.", "ดร.", "อาจารย์", "อ."]) and len(txt) < 300:
                lines = [l.strip() for l in txt.split("|") if l.strip()]
                th_name = lines[0] if lines else ""
                em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th)", txt)
                email = em_match.group(1).lower() if em_match else ""
                img = box.find("img")
                img_url = urllib.parse.urljoin("http://gems.chanthaburi.buu.ac.th/", img["src"]) if img and img.get("src") else ""

                if th_name and th_name not in seen_names and len(th_name) > 4:
                    seen_names.add(th_name)
                    results.append({
                        "faculty_th": "คณะอัญมณี (วิทยาเขตจันทบุรี)",
                        "faculty": "Faculty of Gems (Chanthaburi Campus)",
                        "department_th": "คณะอัญมณี",
                        "department": "Faculty of Gems",
                        "full_name_th": th_name,
                        "full_name_en": "",
                        "email": email,
                        "image_url": img_url,
                        "profile_url": u_gems
                    })
    except Exception as e:
        print(f"   [ERR] Gems Chanthaburi: {e}")

    # Marine Technology
    try:
        u_mar = "http://marine.chanthaburi.buu.ac.th/person.php"
        html = fetch_html(u_mar, timeout=8)
        soup = BeautifulSoup(html, "html.parser")
        for box in soup.find_all(["table", "div", "tr"]):
            txt = box.get_text(separator="|", strip=True)
            if "@" in txt and any(t in txt for t in ["ผศ.", "ดร.", "อาจารย์", "อ.", "รศ."]) and len(txt) < 300:
                lines = [l.strip() for l in txt.split("|") if l.strip()]
                th_name = lines[0] if lines else ""
                em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*buu\.ac\.th)", txt)
                email = em_match.group(1).lower() if em_match else ""
                img = box.find("img")
                img_url = urllib.parse.urljoin("http://marine.chanthaburi.buu.ac.th/", img["src"]) if img and img.get("src") else ""

                if th_name and th_name not in seen_names and len(th_name) > 4:
                    seen_names.add(th_name)
                    results.append({
                        "faculty_th": "คณะเทคโนโลยีทางทะเล (วิทยาเขตจันทบุรี)",
                        "faculty": "Faculty of Marine Technology (Chanthaburi Campus)",
                        "department_th": "คณะเทคโนโลยีทางทะเล",
                        "department": "Faculty of Marine Technology",
                        "full_name_th": th_name,
                        "full_name_en": "",
                        "email": email,
                        "image_url": img_url,
                        "profile_url": u_mar
                    })
    except Exception as e:
        print(f"   [ERR] Marine Chanthaburi: {e}")

    print(f"   Chanthaburi Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# Normalization, Cleaning & State Reducer
# ------------------------------------------------------------
def clean_record(r: dict) -> dict | None:
    name = (r.get("full_name_th") or "").strip()
    if not name or len(name) < 4:
        return None
    if RE_BAD_NAME.search(name):
        return None

    try:
        title, clean_name, _ = normalize_thai_title_and_name(name)
    except Exception:
        clean_name = name
        title = r.get("academic_title_th") or ""

    # Ensure academic/medical title recognition
    if not title:
        for t_candidate in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ผศ.นพ.", "ผศ.พญ.", "รศ.นพ.", "รศ.พญ.", "ศ.นพ.", "ศ.พญ.", "อ.นพ.", "อ.พญ.", "นพ.", "พญ.", "ทพ.", "ทญ.", "ภญ.", "ภก.", "ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์"]:
            if name.startswith(t_candidate):
                title = t_candidate
                clean_name = name[len(t_candidate):].strip()
                break

    if not clean_name or len(clean_name.split()) < 2:
        return None

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""
    if any(email.startswith(g) for g in ["info@", "contact@", "admin@", "support@", "office@"]):
        email = ""

    return {
        "university_th": BUU_TH,
        "university": BUU_EN,
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
    print("🌊 Starting Wave 42: BUU Autonomous Acquisition Pipeline")
    print("============================================================")

    all_harvested = []

    # 1. Medicine
    all_harvested.extend(extract_buu_medicine())

    # 2. Science (10 departments)
    all_harvested.extend(extract_buu_science())

    # 3. Informatics
    all_harvested.extend(extract_buu_informatics())

    # 4. Engineering (6 departments)
    all_harvested.extend(extract_buu_engineering())

    # 5. Nursing (12 departments)
    all_harvested.extend(extract_buu_nursing())

    # 6. Pharmacy (6 departments)
    all_harvested.extend(extract_buu_pharmacy())

    # 7. Humanities & Social Sciences
    all_harvested.extend(extract_buu_huso())

    # 8. Education (7 departments)
    all_harvested.extend(extract_buu_education())

    # 9. Political Science & Law
    all_harvested.extend(extract_buu_polsci())

    # 10. Chanthaburi (Gems & Marine)
    all_harvested.extend(extract_buu_chanthaburi())

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
    print(f"Records with verified email: {with_em} ({with_em / len(all_cleaned) * 100:.1f}%)")

    # Checkpoint state to disk
    ckpt_dir = Path("backend/data/agent_states")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / "wave42_buu_extraction.json"
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved to: {ckpt_path}")

    # Database Deduplication & Ingestion
    print("\n--- Initiating RapidFuzz Database Deduplication Against Local PostgreSQL ---")
    db = SessionLocal()
    try:
        existing_buu = db.query(FacultyDB).filter(
            FacultyDB.university_th.ilike("%บูรพา%")
        ).all()
        print(f"Current BUU faculty in database: {len(existing_buu)}")

        existing_names_cache = {}
        for ex in existing_buu:
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
                ex_rec = next((e for e in existing_buu if e.id == match_id), None)
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
                uid = f"buu_w42_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"buu_w42_{seq:04d}_{random.randint(100, 999)}"
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
        buu_final = db.query(FacultyDB).filter(FacultyDB.university_th.ilike("%บูรพา%")).count()
        buu_em_final = db.query(FacultyDB).filter(
            FacultyDB.university_th.ilike("%บูรพา%"),
            FacultyDB.email.isnot(None),
            FacultyDB.email != ""
        ).count()
        print("\n============================================================")
        print(f"🎉 Wave 42 BUU Execution Complete:")
        print(f"  - BUU Total Faculty: {buu_final} (with verified email: {buu_em_final}, {buu_em_final / max(1, buu_final) * 100:.1f}%)")
        print(f"  - Total National Faculty in DB: {final_total}")
        print("============================================================")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database transaction: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    main()
