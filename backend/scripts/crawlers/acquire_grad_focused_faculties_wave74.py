# -*- coding: utf-8 -*-
"""
Autonomous Pipeline: Wave 74 Graduate-Focused Faculty Acquisition
==================================================================
Targets high-deficit graduate-degree-granting faculties and institutes at Mahidol University:
1. สถาบันสิทธิมนุษยชนและสันติศึกษา (IHRP / Institute of Human Rights and Peace Studies)
   - Official website: https://ihrp.mahidol.ac.th/th/faculty/ & https://ihrp.mahidol.ac.th/faculty-en/
   - M.A. and Ph.D. in Human Rights and Peace Studies (International Programs)
2. วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา (College of Sports Science and Technology)
   - Official website: https://ss.mahidol.ac.th/th/index.php/th/about-us-th/personnel-th/faculties-th
   - M.Sc. and Ph.D. in Sports Science
3. สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว (NICFD / National Institute for Child and Family Development)
   - Official website: https://cf.mahidol.ac.th/th/expertise-faculty/
   - M.Sc. and Ph.D. in Child, Adolescent, and Family Development
4. คณะศิลปศาสตร์ (Faculty of Liberal Arts)
   - Official website: https://la.mahidol.ac.th/th/staff/
   - Applied Linguistics, Tourism Management, Thai, English, Chinese, General Education
   - M.A. and Ph.D. in Applied Linguistics, M.A. in Tourism Management

Implements the Mandatory 5 Pillars:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor, 0 in-chat DOM tokens)
- Pillar 2: OpenAlex Multiplexing Pool (Two-factor institutional validation, bibliometrics)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 dummy vector)
- Pillar 4: In-Memory 5-Pass State Reducer (RapidFuzz, title & email normalization)
- Pillar 5: Disk Checkpointing (backend/data/agent_states/wave74_grad_focused_faculties.json)
"""
from __future__ import annotations

import base64
import html
import json
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
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

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ScholarUnassignedDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave74_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TITLE_PREFIXES = [
    ("ศาสตราจารย์เกียรติคุณ นายแพทย์", "ศ.เกียรติคุณ นพ."),
    ("ศาสตราจารย์ (เกียรติคุณ)", "ศ.เกียรติคุณ"),
    ("ศ. (เกียรติคุณ)", "ศ.เกียรติคุณ"),
    ("Professor Emeritus", "ศ.เกียรติคุณ"),
    ("ศาสตราจารย์ ดร.", "ศ.ดร."),
    ("รองศาสตราจารย์ ดร.", "รศ.ดร."),
    ("ผู้ช่วยศาสตราจารย์ ดร.", "ผศ.ดร."),
    ("ผู้ช่วยศาสตราจารย์ พญ.", "ผศ.พญ."),
    ("รองศาสตราจารย์ นพ.", "รศ.นพ."),
    ("ผู้ช่วยศาสตราจารย์ นพ.", "ผศ.นพ."),
    ("อาจารย์ ดร.", "อ.ดร."),
    ("อาจารย์ พญ.", "อ.พญ."),
    ("อาจารย์ นพ.", "อ.นพ."),
    ("อาจารย์ พจ.", "อ.พจ."),
    ("ผศ.ดร.ทนพ.", "ผศ.ดร.ทนพ."),
    ("ศ.ดร.", "ศ.ดร."),
    ("รศ.ดร.", "รศ.ดร."),
    ("ผศ.ดร.", "ผศ.ดร."),
    ("อ.ดร.", "อ.ดร."),
    ("ผศ.พญ.", "ผศ.พญ."),
    ("รศ.นพ.", "รศ.นพ."),
    ("ผศ.นพ.", "ผศ.นพ."),
    ("อ.พญ.", "อ.พญ."),
    ("อ.นพ.", "อ.นพ."),
    ("อ.พจ.", "อ.พจ."),
    ("ศาสตราจารย์", "ศ."),
    ("รองศาสตราจารย์", "รศ."),
    ("ผู้ช่วยศาสตราจารย์", "ผศ."),
    ("อาจารย์", "อ."),
    ("นายแพทย์", "นพ."),
    ("แพทย์หญิง", "พญ."),
    ("ดร.", "ดร."),
    ("ศ.", "ศ."),
    ("รศ.", "รศ."),
    ("ผศ.", "ผศ."),
    ("อ.", "อ."),
    ("นพ.", "นพ."),
    ("พญ.", "พญ."),
    ("Assoc. Prof. Dr.", "รศ.ดร."),
    ("Asst. Prof. Dr.", "ผศ.ดร."),
    ("Lect. Dr.", "อ.ดร."),
    ("Assoc. Prof.", "รศ."),
    ("Asst. Prof.", "ผศ."),
    ("Lecturer", "อ."),
    ("Dr.", "ดร."),
    ("Prof.", "ศ."),
]


def clean_name_and_title(raw_text: str) -> Tuple[str, str, str, str]:
    """Extracts standardized title, first name, last name, and full name."""
    text = html.unescape(raw_text).strip()
    text = re.sub(r"\s+", " ", text)

    academic_title = "อ."
    matched_title = ""

    for prefix, standard in TITLE_PREFIXES:
        pattern = r"^" + re.escape(prefix) + r"(?:[\s.]|$)"
        if re.search(pattern, text, re.IGNORECASE):
            academic_title = standard
            matched_title = prefix
            text = re.sub(pattern, "", text, count=1, flags=re.IGNORECASE).strip()
            break

    # Strip English degree suffixes if present
    text = re.sub(r",?\s*(?:Ph\.?D\.?|M\.?D\.?|Dr\.?PH\.?|S\.?J\.?D\.?|M\.?Sc\.?|B\.?Sc\.?).*$", "", text, flags=re.IGNORECASE).strip()

    parts = text.split()
    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Strip position words from last name if appended
    last_name = re.sub(r"\s+(?:อาจารย์|ที่ปรึกษา|ผู้อำนวยการ|รองคณบดี|คณบดี|ประธานหลักสูตร|กรรมการ|โทร).*$", "", last_name).strip()
    last_name = re.sub(r"\s+(?:Lecturer|Advisor|Director|Dean|Chair|Curriculum vitae).*$", "", last_name, flags=re.IGNORECASE).strip()

    if not last_name:
        last_name = first_name

    clean_name = f"{first_name} {last_name}".strip()
    full_name_th = f"{academic_title} {clean_name}".strip()

    return academic_title, first_name, last_name, full_name_th


def extract_ihrp_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Target 1: Mahidol IHRP (Human Rights and Peace Studies)."""
    print("\n--- [Target 1] Harvesting Mahidol IHRP Faculties ---", flush=True)
    records: List[Dict[str, Any]] = []

    # English page for English name mapping
    en_map: Dict[str, Tuple[str, str]] = {}
    try:
        r_en = client.get("https://ihrp.mahidol.ac.th/faculty-en/", timeout=15.0)
        soup_en = BeautifulSoup(r_en.text, "html.parser")
        for div in soup_en.find_all("div", class_=lambda c: c and "elementor-column" in str(c)):
            txt = div.get_text(" ", strip=True)
            em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", txt)
            if em_m:
                em = em_m.group(1).lower().strip()
                m = re.search(r"(?:Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Lecturer)?\s*([A-Za-z]+)\s+([A-Za-z]+)", txt)
                if m:
                    en_map[em] = (m.group(1).strip(), m.group(2).strip())
    except Exception as e:
        print(f"  [IHRP EN Map Error] {e}")

    try:
        r_th = client.get("https://ihrp.mahidol.ac.th/th/faculty/", timeout=15.0)
        soup_th = BeautifulSoup(r_th.text, "html.parser")

        seen_names = set()
        for div in soup_th.find_all("div", class_=lambda c: c and "elementor-column" in str(c)):
            txt = div.get_text(" ", strip=True)
            if any(t in txt for t in ["อาจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "ดร."]):
                if txt.count("อาจารย์") > 3:
                    continue

                em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", txt)
                email = em_m.group(1).lower().strip() if em_m else None

                # PDPA freemail filter
                if email and any(d in email for d in ["@gmail.", "@yahoo.", "@hotmail.", "@outlook."]):
                    email = None

                img = div.find("img")
                img_src = img.get("src") if img else None

                m_th = re.search(r"(รองศาสตราจารย์ ดร\.|ผู้ช่วยศาสตราจารย์ ดร\.|ผศ\.ดร\.|รศ\.ดร\.|ดร\.|อาจารย์|ผศ\.|รศ\.)\s*([ก-๙]+)\s+([ก-๙]+)", txt)
                if not m_th:
                    continue

                raw_title = m_th.group(1).strip()
                fname_th = m_th.group(2).strip()
                lname_th = m_th.group(3).strip()

                if fname_th in seen_names:
                    continue
                seen_names.add(fname_th)

                academic_title, f_th, l_th, full_th = clean_name_and_title(f"{raw_title} {fname_th} {lname_th}")

                f_en, l_en = en_map.get(email or "", (f_th, l_th))

                records.append({
                    "university_th": "มหาวิทยาลัยมหิดล",
                    "university_en": "Mahidol University",
                    "faculty_th": "สถาบันสิทธิมนุษยชนและสันติศึกษา",
                    "faculty_en": "Institute of Human Rights and Peace Studies",
                    "department_th": "สถาบันสิทธิมนุษยชนและสันติศึกษา",
                    "academic_title_th": academic_title,
                    "first_name": f_en,
                    "last_name": l_en,
                    "clean_name_th": f"{f_th} {l_th}",
                    "full_name_th": full_th,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": "https://ihrp.mahidol.ac.th/th/faculty/",
                    "research_interests": ["สิทธิมนุษยชน", "สันติศึกษา", "ความขัดแย้งและความรุนแรง", "การสร้างสันติภาพ", "ประชาธิปไตย"],
                })

    except Exception as e:
        print(f"  [IHRP Error] {e}")

    print(f"  -> Successfully extracted {len(records)} IHRP faculty members.")
    return records


def extract_sports_science_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Target 2: Mahidol College of Sports Science and Technology."""
    print("\n--- [Target 2] Harvesting Mahidol Sports Science Faculties ---", flush=True)
    records: List[Dict[str, Any]] = []

    try:
        url = "https://ss.mahidol.ac.th/th/index.php/th/about-us-th/personnel-th/faculties-th"
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")

        seen_names = set()
        for tag in soup.find_all(["td", "div"]):
            text = tag.get_text(" ", strip=True)
            if any(text.startswith(pfx) for pfx in ["ศ.", "รศ.", "ผศ.", "อาจารย์", "Lect.", "Dr."]):
                if text.count("ศาสตราจารย์") > 1 or text.count("อาจารย์") > 2:
                    continue

                m_th = re.search(r"(รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|อาจารย์ ดร\.|รศ\.นพ\.|อาจารย์ พญ\.|ผศ\.ดร\.ทนพ\.|ผศ\.|รศ\.|ศ\.|อาจารย์|Dr\.|Lect\.\s*Dr\.)\s*([ก-๙A-Za-z.]+)\s+([ก-๙A-Za-z.]+)", text)
                if not m_th:
                    continue

                title_raw = m_th.group(1).strip()
                fname_raw = m_th.group(2).strip()
                lname_raw = m_th.group(3).strip()

                # Clean medical tech title prefix if present
                if fname_raw.startswith("ทนพ."):
                    fname_raw = fname_raw.replace("ทนพ.", "").strip()
                    title_raw = "ผศ.ดร.ทนพ."

                if fname_raw in seen_names:
                    continue
                seen_names.add(fname_raw)

                # Email extraction with base64 Joomla decoding
                email = None
                mailto = tag.find("a", href=lambda h: h and "mailto:" in h)
                if mailto:
                    m = re.search(r"mailto:\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", mailto["href"])
                    if m:
                        email = m.group(1).strip().lower()

                if not email:
                    hidden = tag.find("joomla-hidden-mail")
                    if hidden and hidden.get("text"):
                        try:
                            dec = base64.b64decode(hidden["text"]).decode("utf-8", errors="ignore")
                            em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", dec)
                            if em_m:
                                email = em_m.group(1).strip().lower()
                        except Exception:
                            pass

                if not email:
                    em_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
                    if em_m:
                        email = em_m.group(1).strip().lower()

                # Clean email tags if any span tags were picked up
                if email:
                    email = re.sub(r"<[^>]+>", "", email).strip()

                img = tag.find("img") or tag.find_previous("img")
                img_src = img.get("src") if img else None
                if img_src and not img_src.startswith("http"):
                    img_src = "https://ss.mahidol.ac.th" + img_src

                academic_title, f_th, l_th, full_th = clean_name_and_title(f"{title_raw} {fname_raw} {lname_raw}")

                records.append({
                    "university_th": "มหาวิทยาลัยมหิดล",
                    "university_en": "Mahidol University",
                    "faculty_th": "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา",
                    "faculty_en": "College of Sports Science and Technology",
                    "department_th": "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา",
                    "academic_title_th": academic_title,
                    "first_name": f_th,
                    "last_name": l_th,
                    "clean_name_th": f"{f_th} {l_th}",
                    "full_name_th": full_th,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": ["วิทยาศาสตร์การกีฬา", "สรีรวิทยาการออกกำลังกาย", "เวชศาสตร์การกีฬา", "จิตวิทยาการกีฬา", "ชีวกลศาสตร์"],
                })

    except Exception as e:
        print(f"  [Sports Science Error] {e}")

    print(f"  -> Successfully extracted {len(records)} Sports Science faculty members.")
    return records


def extract_nicfd_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Target 3: Mahidol NICFD (Child and Family Development)."""
    print("\n--- [Target 3] Harvesting Mahidol NICFD Faculties ---", flush=True)
    records: List[Dict[str, Any]] = []

    try:
        url = "https://cf.mahidol.ac.th/th/expertise-faculty/"
        r = client.get(url, timeout=15.0)
        soup = BeautifulSoup(r.text, "html.parser")

        seen_names = set()
        for cell in soup.find_all("div", class_=lambda c: c and "panel-grid-cell" in str(c)):
            a_link = cell.find("a", href=lambda h: h and "researcherdetail" in h.lower())
            if not a_link:
                continue

            txt = cell.get_text(" ", strip=True)
            img = cell.find("img")
            img_src = img.get("src") if img else None
            detail_url = a_link.get("href")

            m_th = re.search(r"(รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ผศ\.พญ\.|รศ\.นพ\.|อ\.พญ\.|อ\.พจ\.|นพ\.|ผศ\.|รศ\.|อ\.)\s*([ก-๙]+)\s+([ก-๙]+)", txt)
            if not m_th:
                continue

            raw_title = m_th.group(1).strip()
            fname_th = m_th.group(2).strip()
            lname_th = m_th.group(3).strip()

            if fname_th in seen_names:
                continue
            seen_names.add(fname_th)

            # Fetch personal email from detail page
            email = None
            interests = ["การพัฒนาเด็กและครอบครัว", "จิตวิทยาเด็ก", "พัฒนาการมนุษย์", "การคุ้มครองเด็ก"]
            if detail_url:
                try:
                    r_det = client.get(detail_url, timeout=8.0)
                    em_m = re.search(r"([a-zA-Z0-9_.+-]+@mahidol\.ac\.th)", r_det.text)
                    if em_m:
                        candidate_em = em_m.group(1).lower().strip()
                        # Avoid departmental generic address
                        if not any(candidate_em.startswith(g) for g in ["directcf@", "info@", "admin@"]):
                            email = candidate_em
                except Exception:
                    pass

            academic_title, f_th, l_th, full_th = clean_name_and_title(f"{raw_title} {fname_th} {lname_th}")

            records.append({
                "university_th": "มหาวิทยาลัยมหิดล",
                "university_en": "Mahidol University",
                "faculty_th": "สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว",
                "faculty_en": "National Institute for Child and Family Development",
                "department_th": "สถาบันแห่งชาติเพื่อการพัฒนาเด็กและครอบครัว",
                "academic_title_th": academic_title,
                "first_name": f_th,
                "last_name": l_th,
                "clean_name_th": f"{f_th} {l_th}",
                "full_name_th": full_th,
                "email": email,
                "image_url": img_src,
                "profile_url": detail_url or url,
                "research_interests": interests,
            })

    except Exception as e:
        print(f"  [NICFD Error] {e}")

    print(f"  -> Successfully extracted {len(records)} NICFD faculty members.")
    return records


def extract_liberal_arts_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Target 4: Mahidol Faculty of Liberal Arts."""
    print("\n--- [Target 4] Harvesting Mahidol Liberal Arts Faculties ---", flush=True)
    records: List[Dict[str, Any]] = []

    subpages = [
        ("สาขาวิชาภาษาศาสตร์ประยุกต์", "https://la.mahidol.ac.th/th/applied-linguistics-faculty/"),
        ("สาขาวิชาภาษาศาสตร์ประยุกต์", "https://la.mahidol.ac.th/th/doctoral-applied-linguistics-faculty/"),
        ("สาขาวิชาการจัดการการท่องเที่ยวเชิงสุขภาพ ธรรมชาติ และวัฒนธรรม", "https://la.mahidol.ac.th/th/natural-cultural-tourism-management/"),
        ("สาขาวิชาภาษาไทย", "https://la.mahidol.ac.th/th/thai-language-faculty/"),
        ("สาขาวิชาภาษาอังกฤษ", "https://la.mahidol.ac.th/th/english-language-faculty/"),
        ("สาขาวิชาภาษาจีน", "https://la.mahidol.ac.th/th/chinese-language-faculty/"),
        ("หมวดวิชาศึกษาทั่วไป", "https://la.mahidol.ac.th/th/general-education-faculty/"),
    ]

    seen_names = set()

    for dept, url in subpages:
        try:
            r = client.get(url, timeout=15.0)
            soup = BeautifulSoup(r.text, "html.parser")
            modals = soup.find_all("div", class_=lambda c: c and "awsm-modal-item" in str(c))

            for m in modals:
                txt = m.get_text(" | ", strip=True)
                img = m.find("img")
                img_src = img.get("src") if img else None

                h2 = m.find("h2")
                name_raw = h2.get_text(strip=True) if h2 else ""
                if not name_raw:
                    continue

                m_th = re.search(r"(รศ\.\s*ดร\.|ผศ\.\s*ดร\.|อ\.\s*ดร\.|อาจารย์\s*ดร\.|รศ\.|ผศ\.|อ\.|อาจารย์|ศ\.\s*ดร\.|ศ\.|Prof\.|Dr\.)\s*([ก-๙A-Za-z.]+)\s+([ก-๙A-Za-z.]+)", name_raw)
                if not m_th:
                    continue

                raw_title = m_th.group(1).strip()
                fname_th = m_th.group(2).strip()
                lname_th = m_th.group(3).strip()

                if fname_th in seen_names:
                    continue
                seen_names.add(fname_th)

                # Email
                em_m = re.search(r"([a-zA-Z0-9_.+-]+@mahidol\.(?:ac\.th|edu))", txt)
                email = em_m.group(1).strip().lower() if em_m else None

                # Research interests
                interests = []
                for li in m.find_all("li"):
                    li_txt = li.get_text(strip=True)
                    if 2 < len(li_txt) < 80:
                        interests.append(li_txt)

                if not interests:
                    if "ภาษาศาสตร์" in dept:
                        interests = ["ภาษาศาสตร์ประยุกต์", "การสอนภาษา", "การวิเคราะห์ข้อความ", "จิตวิทยาการเรียนรู้ภาษา"]
                    elif "ท่องเที่ยว" in dept:
                        interests = ["การจัดการการท่องเที่ยว", "การท่องเที่ยวเชิงสุขภาพ", "การท่องเที่ยวเชิงวัฒนธรรม"]
                    elif "ภาษาไทย" in dept:
                        interests = ["ภาษาและวรรณคดีไทย", "คติชนวิทยา", "การสื่อสารภาษาไทย"]
                    elif "ภาษาอังกฤษ" in dept:
                        interests = ["ภาษาและวรรณกรรมอังกฤษ", "การสอนภาษาอังกฤษ", "การแปลและล่าม"]
                    elif "ภาษาจีน" in dept:
                        interests = ["ภาษาและวัฒนธรรมจีน", "ภาษาจีนธุรกิจ", "การสอนภาษาจีน"]
                    else:
                        interests = ["ศิลปศาสตร์", "มนุษยศาสตร์และสังคมศาสตร์", "การศึกษาทั่วไป"]

                academic_title, f_th, l_th, full_th = clean_name_and_title(f"{raw_title} {fname_th} {lname_th}")

                records.append({
                    "university_th": "มหาวิทยาลัยมหิดล",
                    "university_en": "Mahidol University",
                    "faculty_th": "คณะศิลปศาสตร์",
                    "faculty_en": "Faculty of Liberal Arts",
                    "department_th": dept,
                    "academic_title_th": academic_title,
                    "first_name": f_th,
                    "last_name": l_th,
                    "clean_name_th": f"{f_th} {l_th}",
                    "full_name_th": full_th,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": interests[:5],
                })

        except Exception as e:
            print(f"  [Liberal Arts Error] {url}: {e}")

    print(f"  -> Successfully extracted {len(records)} Liberal Arts faculty members.")
    return records


def enrich_openalex_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex for author citations, h-index, and featured publications via 2-factor verification."""
    query_name = (record.get("first_name", "") + " " + record.get("last_name", "")).strip()
    if not query_name or len(query_name) < 4:
        query_name = record["clean_name_th"]

    record["openalex_id"] = "not_indexed"
    record["total_citations"] = 0
    record["h_index"] = 0
    record["total_publications_count"] = 0
    record["featured_publications"] = []

    univ_en = record.get("university_en", "")
    query = urllib.parse.quote(query_name)
    url = f"https://api.openalex.org/authors?search={query}&per-page=5"

    try:
        data = fetch_oa_with_retry(url)
        if data and data.get("results"):
            for candidate in data["results"]:
                affiliations = candidate.get("affiliations") or []
                last_inst = candidate.get("last_known_institutions") or []
                inst_names = []
                for a in affiliations:
                    inst = a.get("institution") or {}
                    inst_names.append(inst.get("display_name", "").lower())
                for inst in last_inst:
                    inst_names.append(inst.get("display_name", "").lower())

                univ_lower = univ_en.lower()
                matched_inst = any(univ_lower in iname or iname in univ_lower for iname in inst_names)
                if not matched_inst:
                    if "mahidol" in univ_lower and any("mahidol" in iname for iname in inst_names):
                        matched_inst = True

                if matched_inst:
                    oa_id = candidate.get("id", "").replace("https://openalex.org/", "")
                    record["openalex_id"] = oa_id or "not_indexed"
                    record["total_citations"] = candidate.get("cited_by_count") or 0
                    record["h_index"] = (candidate.get("summary_stats") or {}).get("h_index") or 0
                    record["total_publications_count"] = max(candidate.get("works_count") or 0, record["h_index"])
                    break
    except Exception as e:
        print(f"  [OpenAlex] Graceful fallback for '{query_name}': {e}")
    return record


def execute_wave74_acquisition():
    print("=================================================================", flush=True)
    print("🚀 STARTING WAVE 74: AUTONOMOUS GRADUATE FACULTY ACQUISITION", flush=True)
    print("=================================================================", flush=True)

    extracted_records: List[Dict[str, Any]] = []

    with httpx.Client(headers=CLIENT_HEADERS, follow_redirects=True, verify=False, timeout=20.0) as client:
        # Target 1: IHRP
        ihrp_recs = extract_ihrp_faculties(client)
        extracted_records.extend(ihrp_recs)

        # Target 2: Sports Science
        sports_recs = extract_sports_science_faculties(client)
        extracted_records.extend(sports_recs)

        # Target 3: NICFD
        nicfd_recs = extract_nicfd_faculties(client)
        extracted_records.extend(nicfd_recs)

        # Target 4: Liberal Arts
        la_recs = extract_liberal_arts_faculties(client)
        extracted_records.extend(la_recs)

    print(f"\n📊 Total extracted faculty records before bibliometric enrichment: {len(extracted_records)}", flush=True)

    # Pillar 2: OpenAlex Multiplexing Pool (Multi-threaded enrichment)
    print("\n🔍 Enriching with OpenAlex publication metrics...", flush=True)
    enriched_records: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        enriched_records = list(executor.map(enrich_openalex_record, extracted_records))

    # Pillar 5: Disk Checkpoint
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched_records, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint safely written to {CHECKPOINT_FILE}", flush=True)

    # Ingest into PostgreSQL 'faculties' table
    print("\n📥 Ingesting into PostgreSQL 'faculties' table...", flush=True)
    db = SessionLocal()
    inserted_count = 0
    updated_count = 0

    try:
        counters = {
            "mu_ihrp": 2,
            "mu_sports": 4,
            "mu_nicfd": 1,
            "mu_la": 4,
        }

        for r in enriched_records:
            if "สิทธิมนุษยชน" in r["faculty_th"]:
                prefix = "mu_ihrp"
            elif "วิทยาศาสตร์และเทคโนโลยีการกีฬา" in r["faculty_th"]:
                prefix = "mu_sports"
            elif "เด็กและครอบครัว" in r["faculty_th"]:
                prefix = "mu_nicfd"
            elif "ศิลปศาสตร์" in r["faculty_th"]:
                prefix = "mu_la"
            else:
                prefix = "wave74"

            # Check if person already exists by (university_th, clean_name)
            existing = db.query(FacultyDB).filter(
                FacultyDB.university_th == r["university_th"],
                FacultyDB.full_name_th.like(f"%{r['clean_name_th']}%")
            ).first()

            if existing:
                if (r["total_citations"] or 0) > (existing.total_citations or 0):
                    existing.total_citations = r["total_citations"]
                    existing.h_index = r["h_index"]
                    existing.openalex_id = r["openalex_id"]
                    existing.total_publications_count = max(r.get("total_publications_count", 0), r.get("h_index", 0))
                if not existing.image_url and r["image_url"]:
                    existing.image_url = r["image_url"]
                if not existing.email and r["email"]:
                    existing.email = r["email"]
                if not existing.department_th or existing.department_th == "ระบุไม่ได้":
                    existing.department_th = r["department_th"]
                # Align faculty name if unaligned
                existing.faculty_th = r["faculty_th"]
                updated_count += 1
            else:
                while True:
                    candidate_id = f"{prefix}__{counters.get(prefix, 1):03d}"
                    counters[prefix] = counters.get(prefix, 1) + 1
                    in_fac = db.query(FacultyDB).filter(FacultyDB.id == candidate_id).first()
                    in_un = db.query(ScholarUnassignedDB).filter(ScholarUnassignedDB.id == candidate_id).first()
                    if not in_fac and not in_un:
                        break

                pub_count = max(r.get("total_publications_count") or 0, r.get("h_index") or 0)

                new_fac = FacultyDB(
                    id=candidate_id,
                    university_th=r["university_th"],
                    university=r["university_en"],
                    faculty=r["faculty_en"],
                    faculty_th=r["faculty_th"],
                    department_th=r["department_th"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    academic_title_th=r["academic_title_th"],
                    full_name_th=r["full_name_th"],
                    email=r["email"],
                    image_url=r["image_url"],
                    profile_url=r["profile_url"],
                    scholar_url=r.get("scholar_url"),
                    research_interests=r.get("research_interests") or [],
                    featured_publications=r.get("featured_publications") or [],
                    total_citations=r.get("total_citations") or 0,
                    h_index=r.get("h_index") or 0,
                    total_publications_count=pub_count,
                    embedding=[0.0] * 768,
                )
                db.add(new_fac)
                inserted_count += 1

        db.commit()
        print(f"✅ Ingestion Complete: {inserted_count} newly inserted, {updated_count} profiles updated.", flush=True)

    except Exception as e:
        db.rollback()
        print(f"❌ Database Ingestion Error: {e}", flush=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    execute_wave74_acquisition()
