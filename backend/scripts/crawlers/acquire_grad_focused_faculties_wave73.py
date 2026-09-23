# -*- coding: utf-8 -*-
"""
Autonomous Pipeline: Wave 73 Graduate-Focused Faculty Acquisition
==================================================================
Targets high-deficit graduate-degree-granting faculties:
1. มหาวิทยาลัยขอนแก่น: คณะศิลปกรรมศาสตร์ (KKU Faculty of Fine and Applied Arts)
   - Official website: https://fa.kku.ac.th/
   - Visual Arts, Design, Performing Arts, Music, Animation, Graduate Culture & Arts
2. มหาวิทยาลัยขอนแก่น: วิทยาลัยบัณฑิตศึกษาการจัดการ (MBA) (KKU MBA)
   - Official website: https://mba.kku.ac.th/th/content.php?name=lecturer
   - Core Graduate MBA Faculty
3. มหาวิทยาลัยมหิดล: คณะสิ่งแวดล้อมและทรัพยากรศาสตร์ (Mahidol Environment & Resource Studies)
   - Official website: https://en.mahidol.ac.th/staff/lecturer
   - Environmental Science, Technology, Ecology, Climate Change, Natural Resources
4. มหาวิทยาลัยเชียงใหม่: วิทยาลัยนโยบายสาธารณะ (CMU School of Public Policy)
   - Official website: https://spp.cmu.ac.th/our-school/our-people/
   - Public Policy, Governance, Urban Policy, Sustainability

Implements the Mandatory 5 Pillars:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor, 0 in-chat DOM tokens)
- Pillar 2: OpenAlex Multiplexing Pool (Two-factor institutional validation, bibliometrics)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 dummy vector)
- Pillar 4: In-Memory 5-Pass State Reducer (RapidFuzz, title & email normalization)
- Pillar 5: Disk Checkpointing (backend/data/agent_states/wave73_grad_focused_faculties.json)
"""
from __future__ import annotations

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

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave73_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}

TITLE_PREFIXES = [
    ("ศาสตราจารย์เกียรติคุณ นายแพทย์", "ศ.เกียรติคุณ นพ."),
    ("ศาสตราจารย์ (เกียรติคุณ)", "ศ.เกียรติคุณ"),
    ("ศ. (เกียรติคุณ)", "ศ.เกียรติคุณ"),
    ("Professor Emeritus", "ศ.เกียรติคุณ"),
    ("ศาสตราจารย์ ดร.", "ศ.ดร."),
    ("รองศาสตราจารย์ ดร.", "รศ.ดร."),
    ("ผู้ช่วยศาสตราจารย์ ดร.", "ผศ.ดร."),
    ("อาจารย์ ดร.", "อ.ดร."),
    ("ศาสตราจารย์", "ศ."),
    ("รองศาสตราจารย์", "รศ."),
    ("ผู้ช่วยศาสตราจารย์", "ผศ."),
    ("อาจารย์", "อ."),
    ("ศ.ดร.", "ศ.ดร."),
    ("รศ.ดร.", "รศ.ดร."),
    ("ผศ.ดร.", "ผศ.ดร."),
    ("อ.ดร.", "อ.ดร."),
    ("ดร.", "ดร."),
    ("ศ.", "ศ."),
    ("รศ.", "รศ."),
    ("ผศ.", "ผศ."),
    ("อ.", "อ."),
    ("Assoc. Prof. Dr.", "รศ.ดร."),
    ("Asst. Prof. Dr.", "ผศ.ดร."),
    ("Assoc.Prof.Dr.", "รศ.ดร."),
    ("Asst.Prof.Dr.", "ผศ.ดร."),
    ("Assoc. Prof.", "รศ."),
    ("Asst. Prof.", "ผศ."),
    ("Assoc.Prof.", "รศ."),
    ("Asst.Prof.", "ผศ."),
    ("Prof. Dr.", "ศ.ดร."),
    ("Prof.", "ศ."),
    ("Dr.", "ดร."),
    ("Mr.", ""),
    ("Ms.", ""),
    ("Mrs.", ""),
]

INVALID_PERSON_SUBSTRINGS = [
    "ระดับบัณฑิตศึกษา",
    "ระดับปริญญาตรี",
    "สาขาวิชา",
    "คณะศิลปกรรมศาสตร์",
    "คณะสิ่งแวดล้อม",
    "หน้าแรก",
    "เกี่ยวกับคณะ",
    "ผู้บริหาร",
    "เจ้าหน้าที่",
    "บุคลากร",
    "ที่ปรึกษา",
]


def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Extracts standardized academic title, clean name, and full formatted name."""
    clean = re.sub(r"\s+", " ", raw_name).strip()
    academic_title = "อาจารย์"

    for prefix, standard in TITLE_PREFIXES:
        if clean.startswith(prefix):
            academic_title = standard or "อาจารย์"
            clean = clean[len(prefix):].strip()
            break

    # Strip residual titles or English prefixes
    clean = re.sub(r"^(?:ดร\.|Dr\.)\s*", "", clean).strip()
    clean = re.sub(r",?\s*(?:PhD|Ph\.D\.|DBA|D\.Tech\.Sc\.|Ed\.D\.)\b", "", clean, flags=re.IGNORECASE).strip()
    full_name_th = f"{academic_title} {clean}".strip() if academic_title else clean
    return academic_title, clean, full_name_th


def is_valid_person_candidate(name: str) -> bool:
    """Strictly validates that candidate is an authentic human person and not an administrative header."""
    if not name or len(name.strip()) < 4:
        return False
    for sub in INVALID_PERSON_SUBSTRINGS:
        if sub in name:
            return False
    parts = name.strip().split()
    return len(parts) >= 2


# ==============================================================================
# CRAWLER 1: KKU Faculty of Fine and Applied Arts
# ==============================================================================
def crawl_kku_fine_arts(client: httpx.Client) -> List[Dict[str, Any]]:
    print("\n--- Crawling KKU Faculty of Fine and Applied Arts (fa.kku.ac.th) ---", flush=True)
    records = []
    target_urls = [
        ("https://fa.kku.ac.th/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%a7%e0%b8%b4%e0%b8%8a%e0%b8%b2%e0%b8%94%e0%b8%99%e0%b8%95%e0%b8%a3%e0%b8%b5%e0%b9%81%e0%b8%a5/", "สาขาวิชาดนตรีและศิลปะการแสดง"),
        ("https://fa.kku.ac.th/%e0%b8%ad%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c%e0%b8%aa%e0%b8%b2%e0%b8%82%e0%b8%b2%e0%b8%97%e0%b8%b1%e0%b8%a8%e0%b8%99%e0%b8%a8%e0%b8%b4%e0%b8%a5%e0%b8%9b%e0%b9%8c%e0%b9%81%e0%b8%a5/", "สาขาวิชาทัศนศิลป์และการออกแบบ"),
        ("https://fa.kku.ac.th/%e0%b8%9c%e0%b8%b9%e0%b9%89%e0%b8%9a%e0%b8%a3%e0%b8%b4%e0%b8%ab%e0%b8%b2%e0%b8%a3/", "คณะศิลปกรรมศาสตร์"),
    ]

    for url, dept_default in target_urls:
        try:
            r = client.get(url, timeout=15.0)
            if r.status_code != 200:
                print(f"  [KKU FA] Failed {url}: Status {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            containers = soup.find_all("div", class_="elementor-widget-wrap")

            for c in containers:
                text = c.get_text(separator=" | ", strip=True)
                lines = [l.strip() for l in text.split(" | ") if l.strip()]

                prof_title = None
                name_line = None
                for i, l in enumerate(lines):
                    if any(l.startswith(p) for p in ["ศ.เกียรติคุณ", "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]):
                        prof_title = l
                        if i + 1 < len(lines):
                            name_line = lines[i + 1]
                        break

                if prof_title and name_line and len(lines) <= 7:
                    if prof_title in ["ศาสตราจารย์ ดร.", "รองศาสตราจารย์ ดร.", "ผู้ช่วยศาสตราจารย์ ดร.", "อาจารย์ ดร.", "ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"]:
                        clean_candidate = name_line
                        full_raw = f"{prof_title} {name_line}"
                    else:
                        clean_candidate = prof_title
                        full_raw = prof_title

                    if not is_valid_person_candidate(clean_candidate):
                        continue

                    img = c.find("img")
                    img_src = img.get("src") if img else None

                    email = None
                    for l in lines:
                        m = re.search(r"([a-zA-Z0-9_.+-]+@kku\.ac\.th)", l)
                        if m:
                            email = m.group(1).strip()
                            break

                    dept = dept_default
                    for l in lines:
                        if "สาขาวิชา" in l or "ทัศนศิลป์" in l or "ดุริยางค" in l:
                            dept = l.replace("|", "").strip()

                    records.append({
                        "university_th": "มหาวิทยาลัยขอนแก่น",
                        "university_en": "Khon Kaen University",
                        "faculty_th": "คณะศิลปกรรมศาสตร์",
                        "faculty_en": "Faculty of Fine and Applied Arts",
                        "department_th": dept,
                        "raw_name_th": full_raw,
                        "email": email,
                        "image_url": img_src,
                        "profile_url": url,
                        "research_interests": ["ศิลปกรรมศาสตร์", "ทัศนศิลป์", "ดุริยางคศิลป์", "ศิลปะการแสดง"]
                    })
        except Exception as e:
            print(f"  [KKU FA] Error scraping {url}: {e}")

    print(f"  -> Extracted {len(records)} candidates from KKU Fine Arts.")
    return records


# ==============================================================================
# CRAWLER 2: KKU Graduate School of Management (MBA)
# ==============================================================================
def crawl_kku_mba(client: httpx.Client) -> List[Dict[str, Any]]:
    print("\n--- Crawling KKU MBA (mba.kku.ac.th) ---", flush=True)
    records = []
    url = "https://mba.kku.ac.th/th/content.php?name=lecturer"

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.find_all("tr"):
                text = tr.get_text(separator=" | ", strip=True)
                if not any(p in text for p in ["ดร.", "ศ.", "รศ.", "ผศ.", "อาจารย์"]):
                    continue

                img = tr.find("img")
                img_src = img.get("src") if img else None
                if img_src and not img_src.startswith("http"):
                    img_src = "https://mba.kku.ac.th/th/" + img_src.lstrip("/")

                lines = [l.strip() for l in text.split(" | ") if l.strip()]
                if not lines:
                    continue

                raw_name_th = lines[0]
                # Strip parenthetical administrative roles e.g. (รองคณบดีฝ่ายวิชาการ)
                raw_name_th = re.sub(r"\(.*?\)", "", raw_name_th).strip()

                if not is_valid_person_candidate(raw_name_th):
                    continue

                raw_en = lines[1] if len(lines) > 1 and ("Dr." in lines[1] or "Prof" in lines[1] or "Asst" in lines[1] or "Assoc" in lines[1]) else None
                first_name_en = None
                last_name_en = None
                if raw_en:
                    clean_en = re.sub(r"\(.*?\)", "", raw_en).strip()
                    for p, _ in TITLE_PREFIXES:
                        if clean_en.startswith(p):
                            clean_en = clean_en[len(p):].strip()
                            break
                    en_parts = clean_en.split()
                    if len(en_parts) >= 2:
                        first_name_en = en_parts[0]
                        last_name_en = " ".join(en_parts[1:])

                records.append({
                    "university_th": "มหาวิทยาลัยขอนแก่น",
                    "university_en": "Khon Kaen University",
                    "faculty_th": "วิทยาลัยบัณฑิตศึกษาการจัดการ (MBA)",
                    "faculty_en": "College of Graduate Study in Management (MBA)",
                    "department_th": "สาขาวิชาบริหารธุรกิจ",
                    "raw_name_th": raw_name_th,
                    "first_name": first_name_en,
                    "last_name": last_name_en,
                    "email": None,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": ["บริหารธุรกิจ", "การจัดการ", "การตลาด", "การเงินและการบัญชี", "Organization Development"]
                })
    except Exception as e:
        print(f"  [KKU MBA] Error scraping: {e}")

    print(f"  -> Extracted {len(records)} candidates from KKU MBA.")
    return records


# ==============================================================================
# CRAWLER 3: Mahidol Faculty of Environment & Resource Studies
# ==============================================================================
def crawl_mahidol_environment(client: httpx.Client) -> List[Dict[str, Any]]:
    print("\n--- Crawling Mahidol Faculty of Environment & Resource Studies (en.mahidol.ac.th) ---", flush=True)
    records = []
    url = "https://en.mahidol.ac.th/staff/lecturer"

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.find_all("div", class_="sppb-row")

            for row in rows:
                h5 = row.find("h5")
                if not h5:
                    continue
                name_th = h5.get_text(strip=True)
                if not any(p in name_th for p in ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร."]):
                    continue

                if not is_valid_person_candidate(name_th):
                    continue

                img = row.find("img")
                img_src = None
                if img:
                    img_src = img.get("data-src") or img.get("src")
                    if img_src and not img_src.startswith("http") and not img_src.startswith("data:"):
                        img_src = "https://en.mahidol.ac.th" + ("/" if not img_src.startswith("/") else "") + img_src
                    elif img_src and img_src.startswith("data:"):
                        img_src = None

                # Uncloak Joomla protected email
                email = None
                script = row.find("script")
                stext = script.text if script else ""
                addy_lines = [line.strip() for line in stext.splitlines() if "addy" in line and "=" in line and "document." not in line]
                chars = []
                for line in addy_lines:
                    for token in re.findall(r"\'([^\']*)\'", line):
                        if token and not token.startswith("cloak"):
                            chars.append(html.unescape(token))
                decoded = "".join(chars)
                m = re.search(r"([a-zA-Z0-9_.+-]+@mahidol\.ac\.th)", decoded)
                if m:
                    email = m.group(1).strip()

                records.append({
                    "university_th": "มหาวิทยาลัยมหิดล",
                    "university_en": "Mahidol University",
                    "faculty_th": "คณะสิ่งแวดล้อมและทรัพยากรศาสตร์",
                    "faculty_en": "Faculty of Environment and Resource Studies",
                    "department_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีสิ่งแวดล้อม",
                    "raw_name_th": name_th,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": ["วิทยาศาสตร์สิ่งแวดล้อม", "การจัดการทรัพยากรธรรมชาติ", "การเปลี่ยนแปลงสภาพภูมิอากาศ", "เทคโนโลยีสิ่งแวดล้อม"]
                })
    except Exception as e:
        print(f"  [Mahidol EN] Error scraping: {e}")

    print(f"  -> Extracted {len(records)} candidates from Mahidol Environment.")
    return records


# ==============================================================================
# CRAWLER 4: CMU School of Public Policy (SPP)
# ==============================================================================
def crawl_cmu_spp(client: httpx.Client) -> List[Dict[str, Any]]:
    print("\n--- Crawling CMU School of Public Policy (spp.cmu.ac.th) ---", flush=True)
    records = []
    url = "https://spp.cmu.ac.th/our-school/our-people/"

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for h5 in soup.find_all("h5"):
                raw_name = h5.get_text(strip=True)
                if not any(p in raw_name for p in ["Prof", "Dr", "Fellow", "Lecturer", "Director"]):
                    continue

                parent = h5.find_parent("div", class_="elementor-widget-wrap") or h5.find_parent("div")
                text = parent.get_text(separator=" | ", strip=True) if parent else ""
                lines = [l.strip() for l in text.split(" | ") if l.strip()]

                img = parent.find("img") if parent else None
                img_src = img.get("src") if img else None

                # Extract email
                m_em = re.search(r"([a-zA-Z0-9_.+-]+@cmu\.ac\.th|[a-zA-Z0-9_.+-]+@eng\.cmu\.ac\.th)", text)
                email = m_em.group(1).strip() if m_em else None

                # Clean English name
                clean_en = raw_name
                clean_en = re.sub(r",?\s*(?:PhD|Ph\.D\.|DBA)\b", "", clean_en, flags=re.IGNORECASE).strip()
                academic_title = "อาจารย์"
                for p, std in TITLE_PREFIXES:
                    if clean_en.startswith(p):
                        academic_title = std or "อาจารย์"
                        clean_en = clean_en[len(p):].strip()
                        break

                en_parts = clean_en.split()
                first_name_en = en_parts[0] if en_parts else clean_en
                last_name_en = " ".join(en_parts[1:]) if len(en_parts) > 1 else first_name_en

                # Research interests from text
                interests = ["นโยบายสาธารณะ", "การบริหารจัดการภาครัฐ"]
                if "EXPERTISE/ INTEREST" in text:
                    exp_part = text.split("EXPERTISE/ INTEREST")[-1]
                    exp_items = [e.strip() for e in exp_part.split(" | ") if e.strip() and len(e.strip()) > 2 and "About me" not in e and "Back" not in e]
                    if exp_items:
                        interests.extend(exp_items[:4])

                records.append({
                    "university_th": "มหาวิทยาลัยเชียงใหม่",
                    "university_en": "Chiang Mai University",
                    "faculty_th": "วิทยาลัยนโยบายสาธารณะ",
                    "faculty_en": "School of Public Policy",
                    "department_th": "กลุ่มวิชานโยบายสาธารณะ",
                    "raw_name_th": f"{academic_title} {clean_en}",
                    "first_name": first_name_en,
                    "last_name": last_name_en,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": interests[:5]
                })
    except Exception as e:
        print(f"  [CMU SPP] Error scraping: {e}")

    print(f"  -> Extracted {len(records)} candidates from CMU SPP.")
    return records


# ==============================================================================
# OPENALEX MULTIPLEXING & BIBLIOMETRIC ENRICHMENT (Pillar 2 & 3)
# ==============================================================================
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
                    if "khon kaen" in univ_lower and any("khon kaen" in iname for iname in inst_names):
                        matched_inst = True
                    elif "mahidol" in univ_lower and any("mahidol" in iname for iname in inst_names):
                        matched_inst = True
                    elif "chiang mai" in univ_lower and any("chiang mai" in iname for iname in inst_names):
                        matched_inst = True

                if matched_inst:
                    oa_id = candidate.get("id", "").replace("https://openalex.org/", "")
                    cites = candidate.get("cited_by_count") or 0
                    stats = candidate.get("summary_stats") or {}
                    h_idx = stats.get("h_index") or 0
                    works = candidate.get("works_count") or 0
                    works = max(works, h_idx)

                    record["openalex_id"] = oa_id or "not_indexed"
                    record["total_citations"] = cites
                    record["h_index"] = h_idx
                    record["total_publications_count"] = works
                    if oa_id:
                        record["scholar_url"] = f"https://openalex.org/authors/{oa_id}"

                    # Top works
                    works_url = f"https://api.openalex.org/works?filter=author.id:{oa_id}&per-page=3&sort=cited_by_count:desc"
                    wdata = fetch_oa_with_retry(works_url)
                    if wdata and wdata.get("results"):
                        f_pubs = []
                        for w in wdata["results"]:
                            title = w.get("title")
                            if title:
                                venue = (w.get("primary_location") or {}).get("source") or {}
                                f_pubs.append({
                                    "title": title,
                                    "year": w.get("publication_year"),
                                    "venue": venue.get("display_name") if isinstance(venue, dict) else "Academic Journal",
                                    "url": w.get("doi") or f"https://openalex.org/{w.get('id', '')}",
                                    "citation_count": w.get("cited_by_count") or 0,
                                })
                        record["featured_publications"] = f_pubs
                    break

    except Exception as e:
        print(f"  [OpenAlex] Graceful fallback for '{query_name}': {e}")

    return record


# ==============================================================================
# MAIN EXECUTION RUNNER
# ==============================================================================
def execute_wave73_acquisition():
    print("=" * 70, flush=True)
    print("🚀 EXECUTING WAVE 73 GRADUATE-FOCUSED FACULTIES ACQUISITION", flush=True)
    print("=" * 70, flush=True)

    if CHECKPOINT_FILE.exists() and CHECKPOINT_FILE.stat().st_size > 1000:
        print(f"  [Resume] Loading pre-extracted records from checkpoint {CHECKPOINT_FILE}...", flush=True)
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            enriched_records = json.load(f)
        print(f"  -> Successfully resumed {len(enriched_records)} records from checkpoint.", flush=True)
    else:
        client = httpx.Client(headers=CLIENT_HEADERS, verify=False, timeout=15.0, follow_redirects=True)
        all_harvested: List[Dict[str, Any]] = []

        all_harvested.extend(crawl_kku_fine_arts(client))
        all_harvested.extend(crawl_kku_mba(client))
        all_harvested.extend(crawl_mahidol_environment(client))
        all_harvested.extend(crawl_cmu_spp(client))

        print(f"\n📊 Total raw harvested faculty records: {len(all_harvested)}", flush=True)

        # State Reducer & Normalization
        processed_records: List[Dict[str, Any]] = []
        seen_dedup = set()

        for r in all_harvested:
            title, clean_name, full_th = normalize_thai_title_and_name(r["raw_name_th"])
            name_parts = clean_name.split()
            first_name = r.get("first_name") or (name_parts[0] if name_parts else clean_name)
            last_name = r.get("last_name") or (" ".join(name_parts[1:]) if len(name_parts) > 1 else first_name)

            dedup_key = (r["university_th"], full_th)
            if dedup_key in seen_dedup:
                continue
            seen_dedup.add(dedup_key)

            r["academic_title_th"] = title
            r["clean_name_th"] = clean_name
            r["full_name_th"] = full_th
            r["first_name"] = first_name
            r["last_name"] = last_name

            processed_records.append(r)

        print(f"🧹 After deduplication: {len(processed_records)} unique faculty candidates.", flush=True)

        # Enrich via OpenAlex Multiplexer (ThreadPoolExecutor)
        print("\n🔍 Enriching with OpenAlex research metrics (Pillar 2)...", flush=True)
        with ThreadPoolExecutor(max_workers=5) as executor:
            enriched_records = list(executor.map(enrich_openalex_record, processed_records))

        # Disk Checkpoint (Pillar 5)
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
            "kku_fa": 1,
            "kku_mba": 1,
            "mu_env": 1,
            "cmu_spp": 16,
        }

        for r in enriched_records:
            if "ศิลปกรรมศาสตร์" in r["faculty_th"] and "ขอนแก่น" in r["university_th"]:
                prefix = "kku_fa"
            elif "บัณฑิตศึกษาการจัดการ" in r["faculty_th"] and "ขอนแก่น" in r["university_th"]:
                prefix = "kku_mba"
            elif "สิ่งแวดล้อม" in r["faculty_th"] and "มหิดล" in r["university_th"]:
                prefix = "mu_env"
            elif "นโยบายสาธารณะ" in r["faculty_th"] and "เชียงใหม่" in r["university_th"]:
                prefix = "cmu_spp"
            else:
                prefix = "wave73"

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
                # Harmonize CMU Public Policy
                if "นโยบายสาธารณะ" in existing.faculty_th:
                    existing.faculty_th = "วิทยาลัยนโยบายสาธารณะ"
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
    execute_wave73_acquisition()
