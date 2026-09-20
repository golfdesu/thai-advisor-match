"""Wave 41 PSU Autonomous Acquisition Pipeline (SKILL.state compliant).

Target: Prince of Songkla University (PSU)
        มหาวิทยาลัยสงขลานครินทร์

Scope:
1. Faculty of Engineering (คณะวิศวกรรมศาสตร์):
   - Department of Computer Engineering (https://coe.psu.ac.th/staffs)
   - Department of Mechanical & Mechatronics Engineering (https://me.psu.ac.th/menu-people/lecturers)
   - Department of Industrial & Manufacturing Engineering (https://ie.psu.ac.th/about/member/teacher.html)
   - Department of Chemical Engineering (https://www.eng.psu.ac.th/chem/about/member/teacher)
   - Department of Electrical & Biomedical Engineering (https://www.eng.psu.ac.th/ee/about/member/teacher)
   - Department of Civil & Environmental Engineering (https://www.eng.psu.ac.th/ce/about/member/teacher)
   - Department of Mining & Materials Engineering (https://mne.eng.psu.ac.th/about/personnel/teacher)
2. College of Computing, Phuket Campus (วิทยาลัยการคอมพิวเตอร์ วิทยาเขตภูเก็ต):
   - Academic Staff & CV Profiles (https://computing.psu.ac.th/th/academic-staff/)
3. Faculty of Science and Industrial Technology, Surat Thani Campus (คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม วิทยาเขตสุราษฎร์ธานี):
   - Academic Staff (https://scit.surat.psu.ac.th/p_about_scit?id=6)
4. Faculty of Science, Hat Yai Campus (คณะวิทยาศาสตร์):
   - Division of Physical Science (https://www.sci.psu.ac.th/personnel-lists/?id=01)
   - Division of Biological Science (https://www.sci.psu.ac.th/personnel-lists/?id=02)
   - Division of Computational Science (https://www.sci.psu.ac.th/personnel-lists/?id=03)
   - Division of Health and Applied Science (https://www.sci.psu.ac.th/personnel-lists/?id=04)

Execution Standard:
- Headless extraction with specialized high-fidelity DOM extractors & Trafilatura heuristics.
- State reduction, title normalization, and PDPA compliance (no phone numbers).
- Checkpointing to backend/data/agent_states/wave41_psu_extraction.json.
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

# Google GenAI
from google import genai
from google.genai import types

PSU_TH = "มหาวิทยาลัยสงขลานครินทร์"
PSU_EN = "Prince of Songkla University"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.9,en;q=0.8"
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(r"(?:หน้าแรก|ติดต่อ|โทรศัพท์|โทรสาร|admin|menu|home|service|download|ห้องปฏิบัติการ|สาขาวิชา|ภาควิชา|คณะ|เพลิงอาจารย์ใหญ่|สถิติ)", re.IGNORECASE)


def fetch_html(url: str, timeout: int = 12) -> str:
    """Fetch HTML with pre-unquoting to prevent double encoding."""
    unquoted = urllib.parse.unquote(url)
    parts = urllib.parse.urlsplit(unquoted)
    encoded_path = urllib.parse.quote(parts.path)
    encoded_query = urllib.parse.quote(parts.query, safe="=&?/")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))

    req = urllib.request.Request(safe_url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


# ------------------------------------------------------------
# 1. CoE - Computer Engineering
# ------------------------------------------------------------
def extract_psu_coe() -> list[dict]:
    print("-> Scraping CoE PSU (Computer Engineering)...")
    html = fetch_html("https://coe.psu.ac.th/staffs")
    soup = BeautifulSoup(html, "html.parser")
    links = list(dict.fromkeys(a.get("href") for a in soup.find_all("a") if a.get("href") and "/staffs/" in a.get("href")))
    print(f"   Discovered {len(links)} CoE profile links.")

    def parse_coe_profile(p_url: str) -> dict | None:
        full_url = urllib.parse.urljoin("https://coe.psu.ac.th", p_url)
        try:
            p_html = fetch_html(full_url, timeout=7)
            p_soup = BeautifulSoup(p_html, "html.parser")
            main = p_soup.find("main") or p_soup
            lines = [l.strip() for l in main.get_text(separator="|", strip=True).split("|") if l.strip()]
            th_name = lines[1] if len(lines) > 1 else ""
            en_name = lines[2] if len(lines) > 2 else ""

            # Extract email
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*psu\.ac\.th", p_html)
            email = next((e for e in emails if not any(x in e.lower() for x in ["bongkot", "info@", "contact@"])), "")

            # Image
            img = main.find("img", src=re.compile(r"/images/"))
            img_url = urllib.parse.urljoin("https://coe.psu.ac.th", img["src"]) if img else ""

            # Research interests
            interests = []
            txt_all = main.get_text(separator="\n", strip=True)
            if "Fields of Interest" in txt_all or "Expertise" in txt_all:
                lines_all = [l.strip() for l in txt_all.split("\n") if l.strip()]
                capturing = False
                for l in lines_all:
                    if l in ["Fields of Interest", "Expertise"]:
                        capturing = True
                        continue
                    if capturing:
                        if any(l.startswith(h) for h in ["Teaching", "Education", "Research Profiles", "Work Experience", "Publications"]):
                            break
                        if len(l) > 2 and not l.isdigit() and len(l) < 100:
                            interests.append(l)

            return {
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "faculty": "Faculty of Engineering",
                "department_th": "สาขาวิชาวิศวกรรมคอมพิวเตอร์",
                "department": "Department of Computer Engineering",
                "full_name_th": th_name,
                "full_name_en": en_name,
                "email": email.lower(),
                "image_url": img_url,
                "profile_url": full_url,
                "research_interests": interests[:8]
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = [r for r in ex.map(parse_coe_profile, links) if r and r["full_name_th"]]
    print(f"   CoE Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 2. ME - Mechanical & Mechatronics Engineering
# ------------------------------------------------------------
def extract_psu_me() -> list[dict]:
    print("-> Scraping ME PSU (Mechanical & Mechatronics Engineering)...")
    url = "https://me.psu.ac.th/menu-people/lecturers"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    results, seen_names = [], set()

    lines = [l.strip() for l in soup.get_text(separator="\n", strip=True).split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if any(t in l for t in ["ศาสตราจารย์", "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "อาจารย์"]) and len(l) < 50:
            if any(x in l for x in ["คณะ", "ภาควิชา", "สาขา", "เจ้าหน้าที่", "ที่ปรึกษา", "Board", "หลักสูตร"]):
                continue
            if l.strip() in ["อาจารย์", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"]:
                continue
            th_name = l
            if th_name in seen_names:
                continue

            en_name = ""
            email = ""
            for j in range(i + 1, min(len(lines), i + 6)):
                ahead = lines[j]
                if any(t in ahead for t in ["Prof.", "Assoc.", "Asst.", "Dr.", "Mr.", "Ms."]) or (re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$", ahead) and not re.search(r"[฀-๿]", ahead)):
                    if not en_name:
                        en_name = ahead
                if "@" in ahead:
                    em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*(?:psu\.ac\.th|gmail\.com|yahoo\.com)", ahead)
                    if em_match:
                        email = em_match.group(0).lower()
                    break
                if any(t in ahead for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "อาจารย์"]):
                    break

            seen_names.add(th_name)
            results.append({
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "faculty": "Faculty of Engineering",
                "department_th": "สาขาวิชาวิศวกรรมเครื่องกลและเมคาทรอนิกส์",
                "department": "Department of Mechanical and Mechatronics Engineering",
                "full_name_th": th_name,
                "full_name_en": en_name,
                "email": email,
                "profile_url": url,
                "image_url": ""
            })

    print(f"   ME Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 3. IE - Industrial & Manufacturing Engineering
# ------------------------------------------------------------
def extract_psu_ie() -> list[dict]:
    print("-> Scraping IE PSU (Industrial & Manufacturing Engineering)...")
    url = "https://ie.psu.ac.th/about/member/teacher.html"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    results, seen_names = [], set()

    lines = [l.strip() for l in soup.get_text(separator="\n", strip=True).split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if any(t in l for t in ["ศาสตราจารย์", "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "รศ.", "ผศ.", "อ.", "อาจารย์"]) and len(l) < 50:
            if any(x in l for x in ["ผู้บริหาร", "อาจารย์", "เจ้าหน้าที่", "คณะวิศวกรรมศาสตร์", "อำเภอหาดใหญ่", "Social Media"]):
                continue
            if l.strip() in ["อาจารย์", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"]:
                continue
            th_name = l
            if th_name in seen_names:
                continue

            email = ""
            for j in range(i + 1, min(len(lines), i + 4)):
                ahead = lines[j]
                if "@" in ahead:
                    em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*psu\.ac\.th", ahead)
                    if em_match:
                        email = em_match.group(0).lower()
                    break
                if any(t in ahead for t in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "ดร.", "รศ.", "ผศ.", "อ."]):
                    break

            seen_names.add(th_name)
            results.append({
                "faculty_th": "คณะวิศวกรรมศาสตร์",
                "faculty": "Faculty of Engineering",
                "department_th": "สาขาวิชาวิศวกรรมอุตสาหการและการผลิต",
                "department": "Department of Industrial and Manufacturing Engineering",
                "full_name_th": th_name,
                "email": email,
                "profile_url": url,
                "image_url": ""
            })

    print(f"   IE Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 4. Chem, EE, CE, MNE - Card-Staff Template Departments
# ------------------------------------------------------------
def extract_psu_card_staff(url: str, dept_th: str, dept_en: str) -> list[dict]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="card-staff")
    results, seen_names = [], set()

    for c in cards:
        name_div = c.find("div", class_="contact-name")
        if not name_div:
            continue
        th_name = name_div.get_text(strip=True)
        th_name = re.sub(r"\s*\(\d+\)$", "", th_name).strip()
        if not th_name or th_name in seen_names:
            continue
        seen_names.add(th_name)

        email = ""
        email_span = c.find("span")
        if email_span and "@" in email_span.get_text():
            email = email_span.get_text(strip=True)
        if not email:
            em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*psu\.ac\.th", c.get_text())
            if em_match:
                email = em_match.group(0)

        img = c.find("img")
        img_url = img.get("src", "") if img else ""

        results.append({
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "faculty": "Faculty of Engineering",
            "department_th": dept_th,
            "department": dept_en,
            "full_name_th": th_name,
            "email": email.lower().strip(),
            "image_url": img_url,
            "profile_url": url
        })

    return results


def extract_psu_chem() -> list[dict]:
    print("-> Scraping Chemical Engineering PSU...")
    res = extract_psu_card_staff(
        "https://www.eng.psu.ac.th/chem/about/member/teacher",
        "สาขาวิชาวิศวกรรมเคมี",
        "Department of Chemical Engineering"
    )
    print(f"   Chem Extracted: {len(res)} records.")
    return res


def extract_psu_ee() -> list[dict]:
    print("-> Scraping Electrical & Biomedical Engineering PSU...")
    res = extract_psu_card_staff(
        "https://www.eng.psu.ac.th/ee/about/member/teacher",
        "สาขาวิชาวิศวกรรมไฟฟ้าและชีวการแพทย์",
        "Department of Electrical and Biomedical Engineering"
    )
    print(f"   EE Extracted: {len(res)} records.")
    return res


def extract_psu_ce() -> list[dict]:
    print("-> Scraping Civil & Environmental Engineering PSU...")
    res = extract_psu_card_staff(
        "https://www.eng.psu.ac.th/ce/about/member/teacher",
        "สาขาวิชาวิศวกรรมโยธาและสิ่งแวดล้อม",
        "Department of Civil and Environmental Engineering"
    )
    print(f"   CE Extracted: {len(res)} records.")
    return res


def extract_psu_mne() -> list[dict]:
    print("-> Scraping Mining & Materials Engineering PSU...")
    res = extract_psu_card_staff(
        "https://mne.eng.psu.ac.th/about/personnel/teacher",
        "สาขาวิชาวิศวกรรมเหมืองแร่และวัสดุ",
        "Department of Mining and Materials Engineering"
    )
    print(f"   MNE Extracted: {len(res)} records.")
    return res


# ------------------------------------------------------------
# 5. College of Computing, Phuket Campus
# ------------------------------------------------------------
def extract_psu_computing_phuket() -> list[dict]:
    print("-> Scraping College of Computing PSU (Phuket Campus)...")
    url = "https://computing.psu.ac.th/th/academic-staff/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    cv_links = list(dict.fromkeys(a.get("href") for a in soup.find_all("a") if a.get("href") and "/cv/index?encode_id=" in a.get("href")))
    print(f"   Discovered {len(cv_links)} Phuket CV profiles.")

    def parse_cv_profile(cv_url: str) -> dict | None:
        try:
            p_html = fetch_html(cv_url, timeout=7)
            p_soup = BeautifulSoup(p_html, "html.parser")
            lines = [l.strip() for l in p_soup.get_text(separator="|", strip=True).split("|") if l.strip()]
            en_name, pos, email = "", "", ""
            for i, l in enumerate(lines):
                if l == "Name" and i + 1 < len(lines):
                    en_name = lines[i + 1]
                elif l == "Position" and i + 1 < len(lines):
                    pos = lines[i + 1]
                elif l == "Email" and i + 1 < len(lines):
                    email = lines[i + 1].replace("(at)", "@").replace("[at]", "@").replace(" ", "")

            img = p_soup.find("img", src=re.compile(r"(storage|upload|staff|photo)", re.I))
            img_url = img.get("src", "") if img else ""

            # Extract Thai name from image unquoted filename
            th_name = ""
            if img_url:
                unquoted = urllib.parse.unquote(img_url)
                filename = unquoted.split("/")[-1]
                m = re.match(r"^([฀-๿\.\s\-]+?)(?:-\d+x\d+.*|\.\w+)$", filename)
                if m:
                    th_name = m.group(1).replace("-", " ").strip()

            if not th_name and en_name:
                th_name = en_name

            return {
                "faculty_th": "วิทยาลัยการคอมพิวเตอร์ (วิทยาเขตภูเก็ต)",
                "faculty": "College of Computing (Phuket Campus)",
                "department_th": "วิทยาลัยการคอมพิวเตอร์",
                "department": "College of Computing",
                "full_name_th": th_name,
                "full_name_en": en_name,
                "email": email.lower(),
                "image_url": img_url,
                "profile_url": cv_url
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = [r for r in ex.map(parse_cv_profile, cv_links) if r and (r["full_name_th"] or r["full_name_en"])]

    print(f"   Computing Phuket Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 6. Faculty of Science & Industrial Technology (Surat Thani)
# ------------------------------------------------------------
def extract_psu_scit_surat() -> list[dict]:
    print("-> Scraping SCIT PSU (Surat Thani Campus)...")
    url = "https://scit.surat.psu.ac.th/p_about_scit?id=6"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    results, seen_names = [], set()

    for a in soup.find_all("a"):
        txt = a.get_text(separator="|", strip=True)
        if "E-mail:" in txt and "@" in txt:
            lines = [l.strip() for l in txt.split("|") if l.strip()]
            th_name = lines[0] if lines else ""
            en_name = lines[1] if len(lines) > 1 and not "E-mail" in lines[1] else ""
            em_match = re.search(r"([a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*psu\.ac\.th)", txt)
            email = em_match.group(1).lower() if em_match else ""

            img = a.find("img")
            img_url = urllib.parse.urljoin("https://scit.surat.psu.ac.th", img["src"]) if img and img.get("src") else ""
            prof_url = urllib.parse.urljoin("https://scit.surat.psu.ac.th", a.get("href", ""))

            if th_name and th_name not in seen_names:
                seen_names.add(th_name)
                results.append({
                    "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม (วิทยาเขตสุราษฎร์ธานี)",
                    "faculty": "Faculty of Science and Industrial Technology (Surat Thani Campus)",
                    "department_th": "คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม",
                    "department": "Faculty of Science and Industrial Technology",
                    "full_name_th": th_name,
                    "full_name_en": en_name,
                    "email": email,
                    "image_url": img_url,
                    "profile_url": prof_url
                })

    print(f"   SCIT Surat Extracted: {len(results)} records.")
    return results


# ------------------------------------------------------------
# 7. Faculty of Science (Hat Yai Campus) - 4 Divisions
# ------------------------------------------------------------
def extract_psu_science_hatyai() -> list[dict]:
    print("-> Scraping Faculty of Science PSU (Hat Yai Campus, 4 Divisions)...")
    divs = [
        ("01", "สาขาวิทยาศาสตร์กายภาพ", "Division of Physical Science"),
        ("02", "สาขาวิทยาศาสตร์ชีวภาพ", "Division of Biological Science"),
        ("03", "สาขาวิทยาศาสตร์การคำนวณ", "Division of Computational Science"),
        ("04", "สาขาวิทยาศาสตร์สุขภาพและวิทยาศาสตร์ประยุกต์", "Division of Health and Applied Science"),
    ]

    all_sci = []
    seen_names = set()

    for did, dth, den in divs:
        url = f"https://www.sci.psu.ac.th/personnel-lists/?id={did}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            in_academic = False
            current_subdept = dth

            for i, line in enumerate(lines):
                if "บุคลากรสายวิชาการ" in line:
                    in_academic = True
                    if i > 0 and len(lines[i - 1]) < 40 and not any(x in lines[i - 1] for x in ["ชื่อ-สกุล", "รายชื่อ", "←", "สาขา"]):
                        current_subdept = lines[i - 1]
                    continue
                elif "บุคลากรสายสนับสนุน" in line or "ผู้ประสานงาน" in line:
                    in_academic = False
                    continue

                if in_academic:
                    if any(t in line for t in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์", "ดร.", "ศ.", "รศ.", "ผศ.", "อ."]) and len(line) < 50:
                        if line.strip() in ["อาจารย์", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"]:
                            continue
                        th_name = line
                        if th_name in seen_names:
                            continue

                        email = ""
                        for j in range(i + 1, min(len(lines), i + 4)):
                            ahead = lines[j]
                            if "@" in ahead:
                                em_match = re.search(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*psu\.ac\.th", ahead)
                                if em_match:
                                    email = em_match.group(0).lower()
                                    break
                            if any(t in ahead for t in ["ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์"]):
                                break

                        seen_names.add(th_name)
                        all_sci.append({
                            "faculty_th": "คณะวิทยาศาสตร์",
                            "faculty": "Faculty of Science",
                            "department_th": f"{dth} ({current_subdept})",
                            "department": den,
                            "full_name_th": th_name,
                            "email": email,
                            "profile_url": url,
                            "image_url": ""
                        })
        except Exception as ex:
            print(f"   ERR fetching {dth}: {ex}")

    print(f"   Science Hat Yai Extracted: {len(all_sci)} records.")
    return all_sci


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

    if not clean_name or len(clean_name.split()) < 2:
        return None

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""
    if any(email.startswith(g) for g in ["info@", "contact@", "admin@", "support@", "office@"]):
        email = ""

    return {
        "university_th": PSU_TH,
        "university": PSU_EN,
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


# ------------------------------------------------------------
# Main Autonomous Execution Pipeline
# ------------------------------------------------------------
def main():
    print(f"============================================================")
    print(f"🌊 Starting Wave 41: PSU Autonomous Data Pipeline")
    print(f"============================================================")

    all_harvested = []

    # 1. Engineering
    all_harvested.extend(extract_psu_coe())
    all_harvested.extend(extract_psu_me())
    all_harvested.extend(extract_psu_ie())
    all_harvested.extend(extract_psu_chem())
    all_harvested.extend(extract_psu_ee())
    all_harvested.extend(extract_psu_ce())
    all_harvested.extend(extract_psu_mne())

    # 2. College of Computing (Phuket)
    all_harvested.extend(extract_psu_computing_phuket())

    # 3. Science & Industrial Tech (Surat Thani)
    all_harvested.extend(extract_psu_scit_surat())

    # 4. Science (Hat Yai)
    all_harvested.extend(extract_psu_science_hatyai())

    print(f"\nTotal raw records harvested: {len(all_harvested)}")

    # Clean and reduce records
    all_cleaned = []
    for r in all_harvested:
        c = clean_record(r)
        if c:
            all_cleaned.append(c)

    print(f"Total cleaned and verified records: {len(all_cleaned)}")
    with_em = sum(1 for r in all_cleaned if r["email"])
    print(f"Records with verified email: {with_em} ({with_em / len(all_cleaned) * 100:.1f}%)")

    # Checkpoint state to disk
    ckpt_dir = Path("backend/data/agent_states")
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / "wave41_psu_extraction.json"
    with open(ckpt_path, "w", encoding="utf-8") as f:
        json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved to: {ckpt_path}")

    # Database Deduplication & Ingestion
    print("\n--- Initiating RapidFuzz Database Deduplication Against Local PostgreSQL ---")
    db = SessionLocal()
    try:
        existing_psu = db.query(FacultyDB).filter(
            FacultyDB.university_th == PSU_TH
        ).all()
        print(f"Current PSU faculty in database: {len(existing_psu)}")

        existing_names_cache = {}
        for ex in existing_psu:
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
                ex_rec = next((e for e in existing_psu if e.id == match_id), None)
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
                uid = f"psu_w41_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"psu_w41_{seq:04d}_{random.randint(100, 999)}"
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
        final_count = db.query(FacultyDB).filter(FacultyDB.university_th == PSU_TH).count()
        print(f"🎉 PSU Ingestion Complete! Final count in database: {final_count} faculty members.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
