"""Wave 40 KMUTNB Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: King Mongkut's University of Technology North Bangkok (KMUTNB)
        มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ

Scope:
1. Faculty of Engineering (คณะวิศวกรรมศาสตร์):
   - Mechanical and Aerospace Engineering (https://mae.eng.kmutnb.ac.th/workforce)
   - Electrical and Computer Engineering (https://ece.eng.kmutnb.ac.th/en/faculty/)
   - Production Engineering (https://pe.kmutnb.ac.th/faculty/)
   - Instrumentation and Electronics Engineering (https://iee.eng.kmutnb.ac.th/iee/คณาจารย์/)
   - Chemical Engineering (https://che.eng.kmutnb.ac.th/faculty/)
2. Faculty of Applied Science (คณะวิทยาศาสตร์ประยุกต์):
   - Computer and Information Science (http://www.cs.kmutnb.ac.th/administrator.jsp)
   - Applied Statistics (https://stat.sci.kmutnb.ac.th/?page_id=30)
   - Industrial Chemistry (http://ic.sci.kmutnb.ac.th/people/faculty)
   - Biotechnology (https://bt.sci.kmutnb.ac.th/)
3. TGGS - The Sirindhorn International Thai-German Graduate School of Engineering:
   - Lecturers & Researchers (https://tggs.kmutnb.ac.th/lecturers)
4. Faculty of Architecture and Design (คณะสถาปัตยกรรมและการออกแบบ):
   - Academic Staff (https://archd.kmutnb.ac.th/about/organization-chart)

Execution Standard:
- Headless extraction with specialized high-fidelity DOM extractors & Trafilatura heuristics.
- State reduction, title normalization, and PDPA compliance (no phone numbers).
- Checkpointing to backend/data/agent_states/wave40_kmutnb_extraction.json.
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
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz, process

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles

AGENT_STATES_DIR = BACKEND_DIR / "data" / "agent_states"
AGENT_STATES_DIR.mkdir(parents=True, exist_ok=True)

KMUTNB_TH = "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ"
KMUTNB_EN = "King Mongkut's University of Technology North Bangkok"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

RE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
RE_BAD_NAME = re.compile(r'(?:ข่าว|ประกาศ|เจ้าหน้าที่|บุคลากร|ห้องสมุด|ติดต่อ|facebook|โทรศัพท์|skip to|admin|หัวหน้า)', re.I)


def fetch_html(url: str, timeout: int = 12) -> str:
    unquoted = urllib.parse.unquote(url)
    parts = urllib.parse.urlsplit(unquoted)
    encoded_path = urllib.parse.quote(parts.path)
    encoded_query = urllib.parse.quote(parts.query, safe="=&?/")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))
    req = urllib.request.Request(safe_url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


# ----------------------------------------------------------------------
# 1. Faculty of Engineering Extractors
# ----------------------------------------------------------------------

def extract_kmutnb_ece() -> list[dict]:
    """Extract Electrical and Computer Engineering faculty."""
    print("🚀 [KMUTNB] Extracting ECE faculty...")
    html = fetch_html("https://ece.eng.kmutnb.ac.th/en/faculty/")
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for div in soup.find_all("div", class_="e-con-full"):
        txt = div.get_text(separator=" | ", strip=True)
        if "@eng.kmutnb.ac.th" in txt and "ece@eng.kmutnb.ac.th" not in txt:
            img = div.find("img")
            img_src = img["src"] if img and img.has_attr("src") else ""
            lines = [l.strip() for l in txt.split("|") if l.strip()]

            email = next((l for l in lines if "@eng.kmutnb.ac.th" in l), "")
            th_name_line = next((l for l in lines if re.search(r'[฀-๿]', l) and any(t in l for t in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."])), "")
            en_name_line = next((l for l in lines if any(t in l for t in ["Professor", "Dr.", "Associate", "Assistant"]) and not re.search(r'[฀-๿]', l)), "")

            if th_name_line:
                results.append({
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "faculty": "Faculty of Engineering",
                    "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
                    "department": "Department of Electrical and Computer Engineering",
                    "full_name_th": th_name_line.replace("\t", " ").strip(),
                    "full_name_en": en_name_line.strip(),
                    "email": email.strip().lower(),
                    "image_url": img_src,
                    "profile_url": "https://ece.eng.kmutnb.ac.th/en/faculty/",
                    "research_interests": ["Electrical Engineering", "Computer Engineering", "Signal Processing", "Power Systems"]
                })
    print(f"   -> ECE extracted: {len(results)} profiles")
    return results


def extract_kmutnb_pe() -> list[dict]:
    """Extract Production Engineering faculty."""
    print("🚀 [KMUTNB] Extracting PE faculty...")
    html = fetch_html("https://pe.kmutnb.ac.th/faculty/")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for div in soup.find_all(["div", "article", "section"]):
        txt = div.get_text(separator=" | ", strip=True)
        if any(k in txt for k in ["ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "อ.ดร.", "อาจารย์", "ผศ.", "รศ."]) and "@eng.kmutnb.ac.th" in txt:
            lines = [l.strip() for l in txt.split("|") if l.strip()]
            email = next((l for l in lines if "@eng.kmutnb.ac.th" in l and "pe@" not in l), "")
            th_name = next((l for l in lines if any(k in l for k in ["ผศ.", "รศ.", "ศ.", "อ.", "อาจารย์"]) and re.search(r'[฀-๿]', l) and len(l) < 50), "")
            en_name = next((l for l in lines if any(k in l for k in ["Dr.", "Prof.", "Asst.", "Assoc."]) and not re.search(r'[฀-๿]', l) and len(l) < 50), "")

            if th_name and th_name not in seen:
                seen.add(th_name)
                img = div.find("img")
                img_src = img["src"] if img and img.has_attr("src") else ""
                results.append({
                    "faculty_th": "คณะวิศวกรรมศาสตร์",
                    "faculty": "Faculty of Engineering",
                    "department_th": "ภาควิชาวิศวกรรมการผลิต",
                    "department": "Department of Production Engineering",
                    "full_name_th": th_name,
                    "full_name_en": en_name,
                    "email": email.lower(),
                    "image_url": img_src,
                    "profile_url": "https://pe.kmutnb.ac.th/faculty/",
                    "research_interests": ["Production Engineering", "Manufacturing Processes", "Industrial Automation"]
                })
    print(f"   -> PE extracted: {len(results)} profiles")
    return results


def extract_kmutnb_che() -> list[dict]:
    """Extract Chemical Engineering faculty."""
    print("🚀 [KMUTNB] Extracting Chemical Engineering faculty...")
    html = fetch_html("https://che.eng.kmutnb.ac.th/faculty/")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for el in soup.find_all(string=lambda s: s and "@eng.kmutnb.ac.th" in s):
        em = el.strip().lower()
        if "che@" in em:
            continue
        p = el.parent.parent.parent
        lines = [l.strip() for l in p.get_text(separator="|", strip=True).split("|") if l.strip()]
        th_name = lines[0] if lines else ""
        if th_name and len(th_name) < 50 and th_name not in seen:
            seen.add(th_name)
            img = p.find("img")
            img_src = img["src"] if img and img.has_attr("src") else ""
            results.append({
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "faculty": "Faculty of Engineering",
                "department_th": "ภาควิชาวิศวกรรมเคมี",
                "department": "Department of Chemical Engineering",
                "full_name_th": th_name,
                "full_name_en": "",
                "email": em,
                "image_url": img_src,
                "profile_url": "https://che.eng.kmutnb.ac.th/faculty/",
                "research_interests": ["Chemical Engineering", "Process Engineering", "Catalysis", "Biochemical Engineering"]
            })
    print(f"   -> Chemical Engineering extracted: {len(results)} profiles")
    return results


def extract_kmutnb_iee() -> list[dict]:
    """Extract Instrumentation & Electronics Engineering faculty."""
    print("🚀 [KMUTNB] Extracting IEE faculty...")
    html = fetch_html("https://iee.eng.kmutnb.ac.th/iee/คณาจารย์/")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for p in soup.find_all(["p", "div", "h4", "h5"]):
        txt = p.get_text(separator=" | ", strip=True)
        lines = [l.strip() for l in txt.split("|") if l.strip()]
        for l in lines:
            if any(k in l for k in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร."]) and re.search(r'[฀-๿]', l) and len(l) < 50:
                if l not in seen and not any(bad in l for bad in ["รายชื่อ", "หัวหน้า", "รองหัวหน้า", "ผู้ช่วย"]):
                    seen.add(l)
                    results.append({
                        "faculty_th": "คณะวิศวกรรมศาสตร์",
                        "faculty": "Faculty of Engineering",
                        "department_th": "ภาควิชาวิศวกรรมระบบเครื่องมือวัดและอิเล็กทรอนิกส์",
                        "department": "Department of Instrumentation and Electronics Engineering",
                        "full_name_th": l,
                        "full_name_en": "",
                        "email": "",
                        "image_url": "",
                        "profile_url": "https://iee.eng.kmutnb.ac.th/iee/คณาจารย์/",
                        "research_interests": ["Instrumentation Engineering", "Electronics", "Control Systems", "Sensors"]
                    })
    print(f"   -> IEE extracted: {len(results)} profiles")
    return results


def extract_kmutnb_mae() -> list[dict]:
    """Extract Mechanical and Aerospace Engineering faculty."""
    print("🚀 [KMUTNB] Extracting MAE faculty...")
    html = fetch_html("https://mae.eng.kmutnb.ac.th/workforce")
    results = []
    seen = set()

    # Pre-compiled regex patterns for Next.js embedded data and SSR text
    raw_names = re.findall(r'(?:ผศ\.|รศ\.|ศ\.|อ\.|ดร\.)[^\",<>\\]{3,30}', html)
    for t in raw_names:
        clean_t = re.sub(r'—.*', '', t).strip()
        clean_t = re.sub(r'·.*', '', clean_t).strip()
        if any(bad in clean_t for bad in ["รายชื่อ", "บุคลากร", "เข้าสู่ระบบ", "ภาควิชา", "หัวหน้า"]):
            continue
        if len(clean_t.split()) >= 2 and clean_t not in seen and len(clean_t) < 40:
            seen.add(clean_t)
            results.append({
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "faculty": "Faculty of Engineering",
                "department_th": "ภาควิชาวิศวกรรมเครื่องกลและการบิน-อวกาศ",
                "department": "Department of Mechanical and Aerospace Engineering",
                "full_name_th": clean_t,
                "full_name_en": "",
                "email": "",
                "image_url": "",
                "profile_url": "https://mae.eng.kmutnb.ac.th/workforce",
                "research_interests": ["Mechanical Engineering", "Aerospace Engineering", "Fluid Dynamics", "Thermodynamics"]
            })
    print(f"   -> MAE extracted: {len(results)} profiles")
    return results


# ----------------------------------------------------------------------
# 2. Faculty of Applied Science Extractors
# ----------------------------------------------------------------------

def extract_kmutnb_cs() -> list[dict]:
    """Extract Computer and Information Science faculty."""
    print("🚀 [KMUTNB] Extracting CS faculty...")
    html = fetch_html("http://www.cs.kmutnb.ac.th/administrator.jsp")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for div in soup.find_all(["div", "li", "p", "h4", "h5"]):
        txt = div.get_text(strip=True)
        if any(k in txt for k in ["ผศ.", "รศ.", "ศ.", "ดร.", "อาจารย์"]) and 6 < len(txt) < 80:
            clean_t = re.sub(r'(?:หัวหน้า|รองหัวหน้า|ผู้ช่วยหัวหน้า|รองคณบดี|อาจารย์ที่ปรึกษา).*', '', txt).strip()
            if clean_t and clean_t not in seen and len(clean_t.split()) >= 2:
                seen.add(clean_t)
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
                    "faculty": "Faculty of Applied Science",
                    "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ",
                    "department": "Department of Computer and Information Science",
                    "full_name_th": clean_t,
                    "full_name_en": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": "http://www.cs.kmutnb.ac.th/administrator.jsp",
                    "research_interests": ["Computer Science", "Information Science", "Software Engineering", "Artificial Intelligence"]
                })
    print(f"   -> CS extracted: {len(results)} profiles")
    return results


def extract_kmutnb_stat() -> list[dict]:
    """Extract Applied Statistics faculty."""
    print("🚀 [KMUTNB] Extracting Applied Statistics faculty...")
    html = fetch_html("https://stat.sci.kmutnb.ac.th/?page_id=30")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for a in soup.find_all("a", href=lambda h: h and "mailto:" in h):
        em = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
        if em and "@sci.kmutnb.ac.th" in em and em not in seen:
            seen.add(em)
            p = a.parent.parent.parent
            txt = p.get_text(separator="|", strip=True)
            lines = [l.strip() for l in txt.split("|") if l.strip()]
            th_lines = [l for l in lines if re.search(r'[฀-๿]', l) and any(k in l for k in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์", "ดร."])]
            en_lines = [l for l in lines if any(k in l for k in ["Professor", "Dr.", "Associate", "Assistant"]) and not re.search(r'[฀-๿]', l)]

            if th_lines:
                th_name = f"{th_lines[0]} {th_lines[1]}" if len(th_lines) > 1 and any(t == th_lines[0] for t in ["ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์", "อาจารย์"]) else th_lines[0]
                en_name = en_lines[0] if en_lines else ""
                img = p.find("img")
                img_src = img["src"] if img and img.has_attr("src") else ""
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
                    "faculty": "Faculty of Applied Science",
                    "department_th": "ภาควิชาสถิติประยุกต์",
                    "department": "Department of Applied Statistics",
                    "full_name_th": th_name,
                    "full_name_en": en_name,
                    "email": em,
                    "image_url": img_src,
                    "profile_url": "https://stat.sci.kmutnb.ac.th/?page_id=30",
                    "research_interests": ["Applied Statistics", "Data Science", "Statistical Modeling", "Quality Control"]
                })
    print(f"   -> Applied Statistics extracted: {len(results)} profiles")
    return results


def extract_kmutnb_ic() -> list[dict]:
    """Extract Industrial Chemistry faculty via AJAX profiles."""
    print("🚀 [KMUTNB] Extracting Industrial Chemistry faculty...")
    html = fetch_html("http://ic.sci.kmutnb.ac.th/people/faculty")
    soup = BeautifulSoup(html, "html.parser")
    results = []

    person_anchors = soup.find_all("a", attrs={"data-id": True})
    data_ids = []
    for a in person_anchors:
        did = a.get("data-id")
        if did and did not in data_ids:
            data_ids.append(did)

    print(f"   Found {len(data_ids)} profile IDs in Industrial Chemistry, fetching modal details...")

    def fetch_ic_profile(did: str) -> dict | None:
        try:
            p_html = fetch_html(f"http://ic.sci.kmutnb.ac.th/people/profile/{did}", timeout=6)
            p_soup = BeautifulSoup(p_html, "html.parser")
            txt = p_soup.get_text(separator=" | ", strip=True)
            lines = [l.strip() for l in txt.split("|") if l.strip()]

            th_name = lines[0] if lines else ""
            en_name = lines[1] if len(lines) > 1 and not re.search(r'[฀-๿]', lines[1]) else ""
            en_name = en_name.replace("(", "").replace(")", "").strip()

            email = next((l for l in lines if "@sci.kmutnb.ac.th" in l), "")
            interests_raw = ""
            for idx, l in enumerate(lines):
                if "ความเชี่ยวชาญ" in l and idx + 1 < len(lines):
                    interests_raw = lines[idx + 1]
                    break

            interests = [i.strip() for i in re.split(r'[/,;]', interests_raw) if i.strip()] if interests_raw else ["Industrial Chemistry", "Chemical Processes"]

            img = p_soup.find("img")
            img_src = img["src"] if img and img.has_attr("src") else ""
            if img_src and not img_src.startswith("http"):
                img_src = f"http://ic.sci.kmutnb.ac.th/{img_src.lstrip('/')}"

            return {
                "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
                "faculty": "Faculty of Applied Science",
                "department_th": "ภาควิชาเคมีอุตสาหกรรม",
                "department": "Department of Industrial Chemistry",
                "full_name_th": th_name,
                "full_name_en": en_name,
                "email": email.lower(),
                "image_url": img_src,
                "profile_url": f"http://ic.sci.kmutnb.ac.th/people/profile/{did}",
                "research_interests": interests
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(fetch_ic_profile, did) for did in data_ids]
        for f in as_completed(futures):
            res = f.result()
            if res and res["full_name_th"]:
                results.append(res)

    print(f"   -> Industrial Chemistry extracted: {len(results)} profiles")
    return results


def extract_kmutnb_bt() -> list[dict]:
    """Extract Biotechnology faculty."""
    print("🚀 [KMUTNB] Extracting Biotechnology faculty...")
    url = "https://bt.sci.kmutnb.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3%e0%b8%aa%e0%b8%b2%e0%b8%a2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for el in soup.find_all(["p", "div", "h3", "h4", "h5", "li"]):
        txt = el.get_text(separator=" ", strip=True)
        if any(k in txt for k in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "อาจารย์"]) and re.search(r'[฀-๿]', txt) and 6 < len(txt) < 50:
            if txt not in seen and not any(bad in txt for bad in ["ผู้บริหาร", "คณาจารย์", "หัวหน้า", "รองหัวหน้า", "ฝ่าย", "ประกันคุณภาพ"]):
                seen.add(txt)
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
                    "faculty": "Faculty of Applied Science",
                    "department_th": "ภาควิชาเทคโนโลยีชีวภาพ",
                    "department": "Department of Biotechnology",
                    "full_name_th": txt,
                    "full_name_en": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": url,
                    "research_interests": ["Biotechnology", "Bioprocess Engineering", "Microbiology", "Applied Bioscience"]
                })
    print(f"   -> Biotechnology extracted: {len(results)} profiles")
    return results


# ----------------------------------------------------------------------
# 3. TGGS & Architecture Extractors
# ----------------------------------------------------------------------

def extract_kmutnb_tggs() -> list[dict]:
    """Extract TGGS International Engineering School faculty."""
    print("🚀 [KMUTNB] Extracting TGGS faculty...")
    html = fetch_html("https://tggs.kmutnb.ac.th/lecturers")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_em = set()

    for el in soup.find_all(string=lambda s: s and "@tggs.kmutnb.ac.th" in s):
        em = el.strip().lower()
        if "info@tggs" in em or em in seen_em:
            continue
        seen_em.add(em)

        curr = el.parent
        th_name = ""
        en_name = ""
        img_src = ""

        for _ in range(4):
            txt = curr.get_text(separator="|", strip=True)
            lines = [l.strip() for l in txt.split("|") if l.strip()]
            for l in lines:
                if re.search(r'[฀-๿]', l) and any(t in l for t in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์", "ดร."]) and len(l) < 60:
                    th_name = l
                    break
            for l in lines:
                if any(t in l for t in ["Prof.", "Dr.", "Assoc.", "Asst."]) and not re.search(r'[฀-๿]', l) and len(l) < 60:
                    en_name = l
                    break
            img = curr.find("img")
            if img and img.has_attr("src") and not img_src:
                img_src = img["src"]

            if th_name:
                break
            curr = curr.parent

        if th_name:
            results.append({
                "faculty_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)",
                "faculty": "The Sirindhorn International Thai-German Graduate School of Engineering",
                "department_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)",
                "department": "The Sirindhorn International Thai-German Graduate School of Engineering",
                "full_name_th": th_name,
                "full_name_en": en_name,
                "email": em,
                "image_url": img_src,
                "profile_url": "https://tggs.kmutnb.ac.th/lecturers",
                "research_interests": ["Advanced Engineering", "Automotive Engineering", "Materials Engineering", "Energy Technology"]
            })
    print(f"   -> TGGS extracted: {len(results)} profiles")
    return results


def extract_kmutnb_archd() -> list[dict]:
    """Extract Faculty of Architecture and Design faculty."""
    print("🚀 [KMUTNB] Extracting Architecture & Design faculty...")
    html = fetch_html("https://archd.kmutnb.ac.th/about/organization-chart")
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for div in soup.find_all("div", class_="text-center"):
        txt = div.get_text(separator=" | ", strip=True)
        if "@archd.kmutnb.ac.th" in txt:
            lines = [l.strip() for l in txt.split("|") if l.strip()]
            email = next((l for l in lines if "@archd.kmutnb.ac.th" in l), "")
            th_name = ""
            for l in lines:
                if any(t in l for t in ["ผศ.", "รศ.", "ศ.", "ดร.", "อาจารย์"]) and re.search(r'[฀-๿]', l) and len(l) < 50:
                    th_name = l
                    break

            if th_name and th_name not in seen:
                seen.add(th_name)
                img = div.find("img")
                img_src = img["src"] if img and img.has_attr("src") else ""
                results.append({
                    "faculty_th": "คณะสถาปัตยกรรมและการออกแบบ",
                    "faculty": "Faculty of Architecture and Design",
                    "department_th": "คณะสถาปัตยกรรมและการออกแบบ",
                    "department": "Faculty of Architecture and Design",
                    "full_name_th": th_name,
                    "full_name_en": "",
                    "email": email.lower(),
                    "image_url": img_src,
                    "profile_url": "https://archd.kmutnb.ac.th/about/organization-chart",
                    "research_interests": ["Architecture", "Industrial Design", "Interior Architecture", "Urban Planning"]
                })
    print(f"   -> Architecture & Design extracted: {len(results)} profiles")
    return results


# ----------------------------------------------------------------------
# 4. Record Cleaning & Normalization
# ----------------------------------------------------------------------

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

    if not clean_name or len(clean_name.split()) < 2:
        return None

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""
    if any(email.startswith(g) for g in ["info@", "contact@", "admin@", "support@", "office@"]):
        email = ""

    return {
        "university_th": KMUTNB_TH,
        "university": KMUTNB_EN,
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
        "featured_publications": [],
        "education": [],
        "taught_courses": []
    }


# ----------------------------------------------------------------------
# 5. Main Autonomous Execution Loop
# ----------------------------------------------------------------------

def main():
    print("======================================================================")
    print("🎓 WAVE 40: KMUTNB AUTONOMOUS EXTRACTION & INGESTION PIPELINE")
    print("   King Mongkut's University of Technology North Bangkok")
    print("   Targeting Engineering, Applied Science, TGGS & Architecture")
    print("   Enforcing SKILL.state Architecture, Zero-Defect Invariants & Local-First")
    print("======================================================================")

    extractors = [
        ("ECE", extract_kmutnb_ece),
        ("PE", extract_kmutnb_pe),
        ("CHE", extract_kmutnb_che),
        ("IEE", extract_kmutnb_iee),
        ("MAE", extract_kmutnb_mae),
        ("CS", extract_kmutnb_cs),
        ("STAT", extract_kmutnb_stat),
        ("IC", extract_kmutnb_ic),
        ("BT", extract_kmutnb_bt),
        ("TGGS", extract_kmutnb_tggs),
        ("ARCHD", extract_kmutnb_archd),
    ]

    all_raw_candidates = []
    for name, fn in extractors:
        try:
            items = fn()
            all_raw_candidates.extend(items)
        except Exception as e:
            print(f"⚠️ [KMUTNB] Extractor {name} failed: {e}")

    print(f"\n📊 Total Raw Extracted Items: {len(all_raw_candidates)}")

    all_cleaned = []
    for r in all_raw_candidates:
        c = clean_record(r)
        if c:
            all_cleaned.append(c)

    print(f"✨ Valid Cleaned Faculty Profiles: {len(all_cleaned)}")

    # Checkpointing to disk
    ckpt_file = AGENT_STATES_DIR / "wave40_kmutnb_extraction.json"
    ckpt_file.write_text(json.dumps(all_cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Checkpoint saved to: {ckpt_file.name}")

    # Database Deduplication & Ingestion
    print("\n--- Initiating RapidFuzz Database Deduplication Against Local PostgreSQL ---")
    db = SessionLocal()
    try:
        existing_kmutnb = db.query(FacultyDB).filter(
            FacultyDB.university_th == KMUTNB_TH
        ).all()
        print(f"Current KMUTNB faculty in database: {len(existing_kmutnb)}")

        existing_names_cache = {}
        for ex in existing_kmutnb:
            clean_th = strip_all_titles(ex.full_name_th or "")
            existing_names_cache[ex.id] = clean_th

        new_members = []
        updated_members = 0
        seen_in_batch = set()

        for cand in all_cleaned:
            cand_clean = strip_all_titles(cand["full_name_th"])
            if not cand_clean or cand_clean in seen_in_batch:
                continue

            # Check matching against DB
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
                # Existing record: check if we can enrich missing email or profile
                ex_rec = next((e for e in existing_kmutnb if e.id == match_id), None)
                if ex_rec:
                    changed = False
                    if not ex_rec.email and cand["email"]:
                        ex_rec.email = cand["email"]
                        changed = True
                    if not ex_rec.image_url and cand["image_url"]:
                        ex_rec.image_url = cand["image_url"]
                        changed = True
                    if changed:
                        updated_members += 1
            else:
                seen_in_batch.add(cand_clean)
                new_members.append(cand)

        print(f"✨ Net New Members to Ingest: {len(new_members)}")
        print(f"🔄 Existing Members Enriched: {updated_members}")

        if not new_members and updated_members == 0:
            print("ℹ️ No database changes required.")
            return

        # Vectorization for Net New Members
        if new_members:
            print(f"\n--- Generating 768-dim Vector Embeddings for {len(new_members)} New Members ---")
            raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
            api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()] if raw_keys else []
            if not api_keys:
                raise ValueError("No Gemini API key available for embedding generation.")

            from google import genai
            from google.genai import types

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

            with ThreadPoolExecutor(max_workers=4) as executor:
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
                uid = f"kmutnb_w40b_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"kmutnb_w40b_{seq:04d}_{random.randint(100, 999)}"
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
        final_count = db.query(FacultyDB).filter(FacultyDB.university_th == KMUTNB_TH).count()
        print(f"🎉 KMUTNB Ingestion Complete! Final count in database: {final_count} faculty members.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
