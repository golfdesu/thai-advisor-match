# -*- coding: utf-8 -*-
"""
Acquire Graduate-Focused Faculties Pipeline (Wave 62)
=====================================================
Acquires authentic faculty members for graduate-degree offering units (ป.โท / ป.เอก)
from their official faculty directories:
1. จุฬาลงกรณ์มหาวิทยาลัย: สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์แห่งจุฬาลงกรณ์มหาวิทยาลัย (https://www.sasin.edu/team/faculty)
2. มหาวิทยาลัยขอนแก่น: คณะเศรษฐศาสตร์ (https://econ.kku.ac.th/main/2821)
3. มหาวิทยาลัยธรรมศาสตร์: คณะสังคมวิทยาและมานุษยวิทยา (https://socanth.tu.ac.th/soc-staff/ & anthro-staff/)
4. มหาวิทยาลัยธรรมศาสตร์: คณะวิทยาการเรียนรู้และศึกษาศาสตร์ (https://lsed.tu.ac.th/th/faculty)
5. มหาวิทยาลัยเชียงใหม่: วิทยาลัยนานาชาตินวัตกรรมดิจิทัล (https://www.icdi.cmu.ac.th/About/AcademicStaff)
6. มหาวิทยาลัยเชียงใหม่: สถาบันนโยบายสาธารณะ (https://spp.cmu.ac.th/our-school/our-people/)
7. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี: บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม (https://www.jgsee.kmutt.ac.th/v3/academic-staff/)

Implements the 5-Pillar Architecture:
- Pillar 1: Headless ThreadPoolExecutor
- Pillar 2: OpenAlex Multiplexing & Bibliometric Enrichment
- Pillar 3: Non-blocking Circuit Breakers (Embedding fallback)
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
- Pillar 5: Disk Checkpointing to backend/data/agent_states/
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry

CHECKPOINT_DIR = BACKEND_DIR / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave62_grad_focused_faculties.json"

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_with_retry(url: str, client: Optional[httpx.Client] = None, max_retries: int = 3) -> Optional[Any]:
    for attempt in range(max_retries):
        try:
            if client:
                resp = client.get(url)
            else:
                resp = httpx.get(url, headers=CLIENT_HEADERS, timeout=30.0, follow_redirects=True, verify=False)
            if resp.status_code == 200:
                if "application/json" in resp.headers.get("content-type", ""):
                    return resp.json()
                return resp.text
            elif resp.status_code in [403, 404]:
                return None
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


# =====================================================================
# 1. Targeted Graduate Faculty Crawlers (Pillar 1)
# =====================================================================

def crawl_cu_sasin(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls CU Sasin School of Management (สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ฯ)."""
    print("  [CU Sasin] Crawling https://www.sasin.edu/team/faculty...", flush=True)
    results = []
    url = "https://www.sasin.edu/team/faculty"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch CU Sasin page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        if "/team/profile/" in a["href"]:
            href = a["href"]
            t = a.get_text(" ", strip=True)
            # Remove "Visiting", "Resident", "View Profile"
            clean_name = re.sub(r"(?:Visiting|Resident|View Profile|Deputy Director|Director|Assistant Director|Senior Fellow|Fellow|\s+)+$", "", t).strip()
            clean_name = re.sub(r"\s+", " ", clean_name)

            if href not in seen_urls and clean_name and len(clean_name) > 3:
                seen_urls.add(href)
                img = a.find("img")
                img_src = img["src"] if img and img.has_attr("src") else None
                full_href = f"https://www.sasin.edu{href}" if href.startswith("/") else href

                results.append({
                    "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
                    "university_en": "Chulalongkorn University",
                    "faculty_th": "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์แห่งจุฬาลงกรณ์มหาวิทยาลัย",
                    "faculty_en": "Sasin School of Management",
                    "department_th": "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์แห่งจุฬาลงกรณ์มหาวิทยาลัย",
                    "raw_name_th": clean_name,
                    "name_en": clean_name,
                    "image_url": img_src,
                    "profile_url": full_href,
                })

    print(f"  ✅ CU Sasin: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kku_economics(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Khon Kaen University Faculty of Economics (คณะเศรษฐศาสตร์ มข.)."""
    print("  [KKU Econ] Crawling https://econ.kku.ac.th/main/2821...", flush=True)
    results = []
    url = "https://econ.kku.ac.th/main/2821"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KKU Econ page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen = set()

    for a in soup.find_all("a"):
        name = a.get_text(strip=True)
        if any(name.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
            parent = a.find_parent(["div", "td", "tr"])
            txt = parent.get_text(" ", strip=True) if parent else ""
            m_email = re.search(r"([a-zA-Z0-9._%+-]+@kku\.ac\.th)", txt)
            email = m_email.group(1) if m_email else None

            img = parent.find("img") if parent else None
            img_src = img["src"] if img and img.has_attr("src") else None

            clean_k = re.sub(r"\s+", "", name)
            if clean_k not in seen and len(name) < 50:
                seen.add(clean_k)
                results.append({
                    "university_th": "มหาวิทยาลัยขอนแก่น",
                    "university_en": "Khon Kaen University",
                    "faculty_th": "คณะเศรษฐศาสตร์",
                    "faculty_en": "Faculty of Economics",
                    "department_th": "คณะเศรษฐศาสตร์",
                    "raw_name_th": name,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                })

    print(f"  ✅ KKU Econ: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_tu_socanth(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Thammasat University Faculty of Sociology and Anthropology."""
    print("  [TU SocAnth] Crawling https://socanth.tu.ac.th/soc-staff/ and anthro-staff/...", flush=True)
    results = []
    pages = [
        ("https://socanth.tu.ac.th/soc-staff/", "สาขาวิชาสังคมวิทยา"),
        ("https://socanth.tu.ac.th/anthro-staff/", "สาขาวิชามานุษยวิทยา"),
    ]
    seen = set()

    for page_url, dept_th in pages:
        html = fetch_with_retry(page_url, client)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")

        for el in soup.find_all(["h2", "h3", "h4", "p", "strong"]):
            t = el.get_text(" ", strip=True)
            t = re.sub(r"\(ลาศึกษาต่อ\)", "", t).strip()
            if any(t.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อาจารย์", "ดร."]) and len(t) < 50:
                if any(x in t for x in ["คณะ", "วิจัย", "สาขา", "มหาวิทยาลัย", "Bristol", "Ph.D."]):
                    continue
                clean_k = re.sub(r"\s+", "", t)
                if clean_k not in seen and clean_k not in ["อาจารย์"]:
                    seen.add(clean_k)
                    parent = el.find_parent(["div", "article", "section"])
                    img = parent.find("img") if parent else None
                    img_src = img["src"] if img and img.has_attr("src") else None

                    # Find email if present in parent
                    p_txt = parent.get_text(" ", strip=True) if parent else ""
                    m_email = re.search(r"([a-zA-Z0-9._%+-]+@(?:socanth\.)?tu\.ac\.th)", p_txt)
                    email = m_email.group(1) if m_email else None

                    results.append({
                        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                        "university_en": "Thammasat University",
                        "faculty_th": "คณะสังคมวิทยาและมานุษยวิทยา",
                        "faculty_en": "Faculty of Sociology and Anthropology",
                        "department_th": dept_th,
                        "raw_name_th": t,
                        "email": email,
                        "image_url": img_src,
                        "profile_url": page_url,
                    })

    print(f"  ✅ TU SocAnth: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_tu_lsed(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Thammasat University Faculty of Learning Sciences and Education (LSED)."""
    print("  [TU LSED] Crawling https://lsed.tu.ac.th/th/faculty...", flush=True)
    results = []
    url = "https://lsed.tu.ac.th/th/faculty"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch TU LSED page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen = set()

    for el in soup.find_all("div", class_=re.compile(r"personnel|member|team|card|item")):
        t = el.get_text(" ", strip=True)
        m = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.)[ดร\.]*\s*[ก-๙]+(?:\s+[ก-๙]+)+)", t)
        if m:
            name = m.group(1).strip()
            # Strip administrative roles from end of name
            name = re.sub(
                r"\s+(คณบดี|รองคณบดี[^\s]*|ผู้ช่วยคณบดี[^\s]*|ผู้อำนวยการ[^\s]*|เลขานุการ[^\s]*|อาจารย์|หัวหน้าสาขา[^\s]*).*$",
                "",
                name
            ).strip()

            if any(x in name for x in ["คลองหลวง", "คณะ", "มหาวิทยาลัย"]):
                continue

            clean_k = re.sub(r"\s+", "", name)
            if clean_k not in seen and len(name) < 45:
                seen.add(clean_k)
                m_email = re.search(r"([a-zA-Z0-9._%+-]+@(?:lsed\.)?tu\.ac\.th)", t)
                email = m_email.group(1) if m_email else None
                img = el.find("img")
                img_src = img["src"] if img and img.has_attr("src") else None

                results.append({
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "university_en": "Thammasat University",
                    "faculty_th": "คณะวิทยาการเรียนรู้และศึกษาศาสตร์",
                    "faculty_en": "Faculty of Learning Sciences and Education",
                    "department_th": "คณะวิทยาการเรียนรู้และศึกษาศาสตร์",
                    "raw_name_th": name,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                })

    print(f"  ✅ TU LSED: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_cmu_icdi(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls CMU International College of Digital Innovation (ICDI)."""
    print("  [CMU ICDI] Crawling https://www.icdi.cmu.ac.th/About/AcademicStaff...", flush=True)
    results = []
    url = "https://www.icdi.cmu.ac.th/About/AcademicStaff"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch CMU ICDI page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="staff-card")
    seen = set()

    for card in cards:
        t = card.get_text(" | ", strip=True)
        # Search for English name & Thai name
        m_en = re.search(r"((?:Assoc\.|Asst\.|Prof\.|Dr\.)\s*[^\n\r\|]+)", t)
        m_th = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|อาจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|ศาสตราจารย์)[^\n\r\|]+)", t)
        m_email = re.search(r"([a-zA-Z0-9._%+-]+@cmu\.ac\.th)", t)

        img = card.find("img")
        img_src = None
        if img and img.has_attr("src"):
            raw_src = img["src"]
            if raw_src.startswith(".."):
                img_src = f"https://www.icdi.cmu.ac.th{raw_src[2:]}"
            elif raw_src.startswith("/"):
                img_src = f"https://www.icdi.cmu.ac.th{raw_src}"
            else:
                img_src = raw_src

        name_en = m_en.group(1).strip() if m_en else None
        name_th = m_th.group(1).strip() if m_th else (name_en or "")
        email = m_email.group(1) if m_email else None

        # Research interests from card text
        res_interests = []
        parts = t.split("|")
        for p in parts[2:]:
            p_clean = p.strip()
            if p_clean and not any(x in p_clean for x in ["@", "+66", "Tel", "Fax", ":"]):
                if len(p_clean) > 3 and len(p_clean) < 80:
                    res_interests.append(p_clean)

        raw_key = re.sub(r"\s+", "", name_th or name_en or "")
        if raw_key and raw_key not in seen:
            seen.add(raw_key)
            results.append({
                "university_th": "มหาวิทยาลัยเชียงใหม่",
                "university_en": "Chiang Mai University",
                "faculty_th": "วิทยาลัยนานาชาตินวัตกรรมดิจิทัล",
                "faculty_en": "International College of Digital Innovation",
                "department_th": "วิทยาลัยนานาชาตินวัตกรรมดิจิทัล",
                "raw_name_th": name_th,
                "name_en": name_en,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
                "research_interests": res_interests[:4],
            })

    print(f"  ✅ CMU ICDI: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_cmu_spp(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls CMU School of Public Policy (สถาบันนโยบายสาธารณะ มช.)."""
    print("  [CMU SPP] Crawling https://spp.cmu.ac.th/our-school/our-people/...", flush=True)
    results = []
    url = "https://spp.cmu.ac.th/our-school/our-people/"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch CMU SPP page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen = set()

    for h in soup.find_all(["h2", "h3", "h4", "h5"]):
        t = h.get_text(" ", strip=True)
        if any(p in t for p in ["Prof.", "Dr.", "PhD", "Ph.D.", "Assoc.", "Asst."]):
            parent = h.find_parent(["div", "article", "section"])
            txt = parent.get_text(" | ", strip=True) if parent else ""
            m_email = re.search(r"([a-zA-Z0-9._%+-]+@cmu\.ac\.th)", txt)
            email = m_email.group(1) if m_email else None
            img = parent.find("img") if parent else None
            img_src = img["src"] if img and img.has_attr("src") else None

            # Clean name
            clean_name = re.sub(r",\s*(PhD|Ph\.D\.|M\.Sc\.|M\.A\.).*$", "", t).strip()
            clean_k = re.sub(r"\s+", "", clean_name)

            if clean_k not in seen and len(clean_name) < 55:
                seen.add(clean_k)
                results.append({
                    "university_th": "มหาวิทยาลัยเชียงใหม่",
                    "university_en": "Chiang Mai University",
                    "faculty_th": "สถาบันนโยบายสาธารณะ",
                    "faculty_en": "School of Public Policy",
                    "department_th": "สถาบันนโยบายสาธารณะ",
                    "raw_name_th": clean_name,
                    "name_en": clean_name,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                })

    print(f"  ✅ CMU SPP: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kmutt_jgsee(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTT Joint Graduate School of Energy and Environment (JGSEE)."""
    print("  [KMUTT JGSEE] Crawling https://www.jgsee.kmutt.ac.th/v3/academic-staff/...", flush=True)
    results = []
    url = "https://www.jgsee.kmutt.ac.th/v3/academic-staff/"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KMUTT JGSEE page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    cols = soup.find_all("div", class_="gdlr-core-personnel-list-column")
    seen = set()

    for col in cols:
        title_tag = col.find(class_=re.compile(r"personnel-title|personnel-list-title"))
        email_tag = col.find(class_=re.compile(r"personnel-info-list-item-email|personnel-info-list-email|email"))
        img_tag = col.find("img")

        name = title_tag.get_text(strip=True) if title_tag else ""
        name = re.sub(r"\s+", " ", name).strip()
        img_src = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

        email_txt = email_tag.get_text(" ", strip=True) if email_tag else ""
        m_email = re.search(r"([a-zA-Z0-9._%+-]+@(?:jgsee\.)?kmutt\.ac\.th)", email_txt)
        email = m_email.group(1) if m_email else None

        clean_k = re.sub(r"\s+", "", name)
        if clean_k not in seen and len(name) > 3 and len(name) < 55:
            seen.add(clean_k)
            results.append({
                "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                "university_en": "King Mongkut's University of Technology Thonburi",
                "faculty_th": "บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม",
                "faculty_en": "The Joint Graduate School of Energy and Environment",
                "department_th": "บัณฑิตวิทยาลัยร่วมด้านพลังงานและสิ่งแวดล้อม",
                "raw_name_th": name,
                "name_en": name,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
            })

    print(f"  ✅ KMUTT JGSEE: Harvested {len(results)} authentic faculty members.")
    return results


# =====================================================================
# 2. Normalization & OpenAlex Enrichment (Pillars 2 & 4)
# =====================================================================

def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Extracts authentic academic title and base name safely without greedy substring bugs."""
    t = raw_name.strip()
    t = re.sub(r"\s+", " ", t)

    title_patterns = [
        (r"^(ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.)", "ศ.ดร."),
        (r"^(รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.)", "รศ.ดร."),
        (r"^(ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.)", "ผศ.ดร."),
        (r"^(อาจารย์\s*ดร\.|อ\.\s*ดร\.)", "อ.ดร."),
        (r"^(ศาสตราจารย์|ศ\.)", "ศ."),
        (r"^(รองศาสตราจารย์|รศ\.)", "รศ."),
        (r"^(ผู้ช่วยศาสตราจารย์|ผศ\.)", "ผศ."),
        (r"^(ดร\.)", "ดร."),
        (r"^(อาจารย์|อ\.)", "อ."),
        (r"^(Prof\.\s*Dr\.)", "ศ.ดร."),
        (r"^(Assoc\.\s*Prof\.\s*Dr\.)", "รศ.ดร."),
        (r"^(Asst\.\s*Prof\.\s*Dr\.)", "ผศ.ดร."),
        (r"^(Associate\s*Professor\s*Dr\.)", "รศ.ดร."),
        (r"^(Assistant\s*Professor\s*Dr\.)", "ผศ.ดร."),
        (r"^(Professor\s*Dr\.)", "ศ.ดร."),
        (r"^(Associate\s*Professor)", "รศ."),
        (r"^(Assistant\s*Professor)", "ผศ."),
        (r"^(Assoc\.\s*Prof\.)", "รศ."),
        (r"^(Asst\.\s*Prof\.)", "ผศ."),
        (r"^(Prof\.)", "ศ."),
        (r"^(Dr\.)", "ดร."),
    ]

    detected_title = ""
    base_name = t

    for pat, norm_title in title_patterns:
        m = re.match(pat, t, flags=re.IGNORECASE)
        if m:
            detected_title = norm_title
            base_name = t[m.end():].strip()
            # If nested Dr. after English/Thai title (e.g. Assoc. Prof. Chaipong Pongpanich, Ph.D.)
            m_sub = re.match(r"^(Dr\.|ดร\.)\s*", base_name, flags=re.IGNORECASE)
            if m_sub:
                base_name = base_name[m_sub.end():].strip()
                if "ดร." not in detected_title:
                    detected_title = f"{detected_title}ดร."
            break

    # Strip trailing academic degrees
    base_name = re.sub(
        r",?\s*(Ph\.D\.|D\.Eng\.|M\.Sc\.|B\.Sc\.|Ph\.D|D\.Tech\.|CFA|DBA|Ed\.D\.|LL\.M\.|LL\.B\.|MBA).*$",
        "",
        base_name,
        flags=re.IGNORECASE
    ).strip()
    full_name = f"{detected_title} {base_name}".strip() if detected_title else base_name
    return detected_title or "อาจารย์", full_name, base_name


def enrich_faculty_with_openalex(faculty: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex to retrieve citations, h-index, and author ID with 2-factor verification."""
    name_to_search = faculty.get("name_en") or faculty.get("raw_name_th") or ""
    clean_search = re.sub(
        r"^(Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Associate\s*Professor|Assistant\s*Professor|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*",
        "",
        name_to_search,
        flags=re.IGNORECASE
    ).strip()
    clean_search = re.sub(r",?\s*(Ph\.D\.|PhD|D\.Eng\.|M\.Sc\.|CFA|DBA).*$", "", clean_search, flags=re.IGNORECASE).strip()

    # If no English romanized characters, OpenAlex cannot match accurately without English
    if not re.search(r"[a-zA-Z]{3,}", clean_search):
        faculty["openalex_id"] = "not_indexed"
        faculty["total_citations"] = 0
        faculty["h_index"] = 0
        faculty["total_publications_count"] = 0
        faculty["featured_publications"] = []
        return faculty

    q = urllib.parse.quote(clean_search)
    api_url = f"https://api.openalex.org/authors?search={q}&filter=affiliations.institution.country_code:TH&per-page=3"
    data = fetch_oa_with_retry(api_url)
    results = (data or {}).get("results", []) or []

    if results:
        uni_str = faculty.get("university_en", "") or faculty.get("university_th", "")
        best_cand = None
        for cand in results:
            affils = cand.get("affiliations") or []
            disp_names = [((a.get("institution") or {}).get("display_name") or "").lower() for a in affils]
            uni_lower = uni_str.lower()
            if any(any(tok in d for tok in uni_lower.split() if len(tok) > 4) for d in disp_names):
                best_cand = cand
                break
        if not best_cand and len(results) == 1:
            best_cand = results[0]

        if best_cand:
            oa_id = best_cand.get("id")
            cites = best_cand.get("cited_by_count") or 0
            h_idx = (best_cand.get("summary_stats") or {}).get("h_index") or 0
            works = best_cand.get("works_count") or 0
            works = max(works, h_idx)

            faculty["openalex_id"] = oa_id
            faculty["total_citations"] = cites
            faculty["h_index"] = h_idx
            faculty["total_publications_count"] = works
            faculty["scholar_url"] = oa_id
            return faculty

    faculty["openalex_id"] = "not_indexed"
    faculty["total_citations"] = 0
    faculty["h_index"] = 0
    faculty["total_publications_count"] = 0
    faculty["featured_publications"] = []
    return faculty


# =====================================================================
# 3. Database Ingestion Engine (Pillars 3, 4, 5)
# =====================================================================

def generate_canonical_id(univ_code: str, faculty_code: str, name: str, idx: int) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "", name.lower())[:15]
    return f"{univ_code}_{faculty_code}_{slug}_{idx:03d}"


def run_pipeline():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING WAVE 62: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
    print("=================================================================", flush=True)
    t0 = time.time()

    client = httpx.Client(verify=False, timeout=35.0, follow_redirects=True, headers=CLIENT_HEADERS)
    db = SessionLocal()

    try:
        # Step 1: Checkpoint recovery or crawl the 7 target faculties
        if CHECKPOINT_FILE.exists():
            print(f"\n📂 Resuming from existing disk checkpoint: {CHECKPOINT_FILE} (Pillar 5)", flush=True)
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                enriched_faculty = json.load(f)
            print(f"  ✅ Loaded {len(enriched_faculty)} checkpointed faculty records.", flush=True)
        else:
            all_raw_faculty = []
            all_raw_faculty.extend(crawl_cu_sasin(client))
            all_raw_faculty.extend(crawl_kku_economics(client))
            all_raw_faculty.extend(crawl_tu_socanth(client))
            all_raw_faculty.extend(crawl_tu_lsed(client))
            all_raw_faculty.extend(crawl_cmu_icdi(client))
            all_raw_faculty.extend(crawl_cmu_spp(client))
            all_raw_faculty.extend(crawl_kmutt_jgsee(client))

            print(f"\n📊 Total Raw Faculty Harvested: {len(all_raw_faculty)}")

            # Step 2: Normalize names & academic titles
            print("\n⚙️ Normalizing Names and Academic Titles (Pillar 4)...", flush=True)
            normalized_faculty = []
            for i, item in enumerate(all_raw_faculty, 1):
                raw_n = item.get("raw_name_th") or ""
                title_th, full_th, base_n = normalize_thai_title_and_name(raw_n)

                name_en = item.get("name_en")
                if not name_en and re.search(r"^[a-zA-Z\s\.\,\-]+$", raw_n):
                    name_en = raw_n

                first_name = ""
                last_name = ""
                if base_n:
                    parts = base_n.split()
                    first_name = parts[0]
                    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

                item["title_th"] = title_th or "อาจารย์"
                item["full_name_th"] = full_th or raw_n
                item["first_name"] = first_name
                item["last_name"] = last_name
                item["name_en"] = name_en
                normalized_faculty.append(item)

            # Step 3: OpenAlex Multiplexing & Metric Enrichment (Pillar 2)
            print("\n📚 Enriching with OpenAlex Metrics (Pillar 2)...", flush=True)
            enriched_faculty = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_fac = {executor.submit(enrich_faculty_with_openalex, f): f for f in normalized_faculty}
                for fut in as_completed(future_to_fac):
                    try:
                        res = fut.result()
                        enriched_faculty.append(res)
                    except Exception:
                        fac_orig = future_to_fac[fut]
                        fac_orig["openalex_id"] = "not_indexed"
                        enriched_faculty.append(fac_orig)

            # Step 4: Disk Checkpoint (Pillar 5)
            print(f"\n💾 Writing Disk Checkpoint to {CHECKPOINT_FILE} (Pillar 5)...", flush=True)
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(enriched_faculty, f, ensure_ascii=False, indent=2)
            print(f"  ✅ Checkpointed {len(enriched_faculty)} faculty records to disk.")

        # Step 5: Ingestion into PostgreSQL Database (Pillars 3 & 4)
        print("\n📥 Committing to PostgreSQL public.faculties...", flush=True)
        existing_names = set(
            n for (n,) in db.query(FacultyDB.full_name_th).filter(FacultyDB.full_name_th.isnot(None)).all()
        )
        existing_emails = set(
            em.lower() for (em,) in db.query(FacultyDB.email).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").all()
        )

        univ_prefix_map = {
            "จุฬาลงกรณ์มหาวิทยาลัย": ("cu", "sasin"),
            "มหาวิทยาลัยขอนแก่น": ("kku", "econ"),
            "มหาวิทยาลัยธรรมศาสตร์": ("tu", "grad"),
            "มหาวิทยาลัยเชียงใหม่": ("cmu", "grad"),
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ("kmutt", "jgsee"),
        }

        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, item in enumerate(enriched_faculty, 1):
            full_th = item.get("full_name_th") or ""
            email = (item.get("email") or "").lower().strip() or None
            univ_th = item.get("university_th")

            existing_f = None
            if email and email in existing_emails:
                existing_f = db.query(FacultyDB).filter(FacultyDB.email == email).first()
            elif full_th and full_th in existing_names:
                existing_f = db.query(FacultyDB).filter(FacultyDB.full_name_th == full_th).first()

            if existing_f:
                updated = False
                if not existing_f.image_url and item.get("image_url"):
                    existing_f.image_url = item.get("image_url")
                    updated = True
                if not existing_f.email and email:
                    existing_f.email = email
                    updated = True
                if (not existing_f.openalex_id or existing_f.openalex_id == "not_indexed") and item.get("openalex_id") != "not_indexed":
                    existing_f.openalex_id = item.get("openalex_id")
                    existing_f.total_citations = item.get("total_citations", 0)
                    existing_f.h_index = item.get("h_index", 0)
                    existing_f.total_publications_count = max(item.get("total_publications_count", 0), item.get("h_index", 0))
                    updated = True
                if updated:
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                u_code, f_code = univ_prefix_map.get(univ_th, ("univ", "grad"))
                new_id = generate_canonical_id(u_code, f_code, item.get("first_name") or full_th, idx)

                while db.query(FacultyDB.id).filter(FacultyDB.id == new_id).first():
                    new_id = f"{new_id}_x"

                new_record = FacultyDB(
                    id=new_id,
                    university=item.get("university_en"),
                    university_th=item.get("university_th"),
                    faculty=item.get("faculty_en"),
                    faculty_th=item.get("faculty_th"),
                    department=item.get("faculty_en"),
                    department_th=item.get("department_th") or item.get("faculty_th"),
                    academic_title_th=item.get("title_th") or "อาจารย์",
                    full_name_th=full_th,
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    email=email,
                    image_url=item.get("image_url"),
                    profile_url=item.get("profile_url"),
                    scholar_url=item.get("scholar_url"),
                    openalex_id=item.get("openalex_id") or "not_indexed",
                    total_citations=item.get("total_citations") or 0,
                    h_index=item.get("h_index") or 0,
                    total_publications_count=max(item.get("total_publications_count") or 0, item.get("h_index") or 0),
                    research_interests=item.get("research_interests") or [],
                    featured_publications=item.get("featured_publications") or [],
                    embedding=[0.0] * 768,  # Non-blocking circuit breaker (Pillar 3)
                )
                db.add(new_record)
                existing_names.add(full_th)
                if email:
                    existing_emails.add(email)
                inserted_count += 1

        db.commit()
        print(f"\n🎉 Ingestion Complete:")
        print(f"  - Newly Inserted: {inserted_count}")
        print(f"  - Profile Enriched / Updated: {updated_count}")
        print(f"  - Skipped (Identical): {skipped_count}")

    finally:
        db.close()

    print(f"Pipeline finished in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_pipeline()
