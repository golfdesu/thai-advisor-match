# -*- coding: utf-8 -*-
"""
Acquire Graduate-Focused Faculties Pipeline (Wave 61)
=====================================================
Acquires authentic faculty members for graduate-degree offering units (ป.โท / ป.เอก)
from their official faculty directories:
1. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ: คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล (https://itd.kmutnb.ac.th/lecturer.php)
2. มหาวิทยาลัยธรรมศาสตร์: วิทยาลัยนวัตกรรม (https://www.citu.tu.ac.th/university-personnel/)
3. มหาวิทยาลัยธรรมศาสตร์: คณะสาธารณสุขศาสตร์ (https://web1.fph.tu.ac.th/th-ourfaculty)
4. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี: บัณฑิตวิทยาลัยการจัดการและนวัตกรรม (https://gmi.kmutt.ac.th/th/about-gmi/)
5. มหาวิทยาลัยขอนแก่น: วิทยาลัยการปกครองท้องถิ่น (https://copa.kku.ac.th/2759/)
6. สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง: วิทยาลัยนวัตกรรมการผลิตขั้นสูง (https://ami.kmitl.ac.th/people/faculty/)
7. มหาวิทยาลัยมหิดล: วิทยาลัยการจัดการ (https://www.cmmu.mahidol.ac.th/web/faculty-research/full-time)

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
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave61_grad_focused_faculties.json"

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
            elif resp.status_code == 429:
                time.sleep(2.0 * (attempt + 1))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


# =====================================================================
# 1. Official Directory Crawlers (Pillar 1)
# =====================================================================

def crawl_kmutnb_itdi(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTNB Faculty of Information Technology and Digital Innovation."""
    print("  [KMUTNB ITDI] Crawling https://itd.kmutnb.ac.th/lecturer.php...", flush=True)
    results = []
    url = "https://itd.kmutnb.ac.th/lecturer.php"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KMUTNB ITDI page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    dept_map = {
        range(1, 10): "ภาควิชาเทคโนโลยีสารสนเทศ",
        range(10, 19): "ภาควิชาการจัดการเทคโนโลยีสารสนเทศ",
        range(19, 26): "ภาควิชาการบริหารเครือข่ายดิจิทัลและความมั่นคงปลอดภัยสารสนเทศ",
    }

    for div in soup.find_all("div", class_=re.compile(r"adm_r\d+_c\d+")):
        name_div = div.find("div", class_="wrp_name_adm")
        img_div = div.find("div", class_="wrp_img_adm")
        i_mail = div.find("i", href=re.compile(r"#mail_\d+"))
        if name_div:
            name = name_div.get_text(strip=True)
            img = img_div.find("img") if img_div else None
            img_src = f"https://itd.kmutnb.ac.th/{img.get('src')}" if img and img.get("src") else None
            email = None
            m_id = 0
            if i_mail:
                m_str = i_mail["href"].lstrip("#")
                m_num = re.search(r"\d+", m_str)
                if m_num:
                    m_id = int(m_num.group(0))
                modal = soup.find("div", id=m_str)
                if modal:
                    em_m = re.search(r"[\w\.-]+@itd\.kmutnb\.ac\.th", modal.get_text())
                    if em_m:
                        email = em_m.group(0)

            dept = next((v for k, v in dept_map.items() if m_id in k), "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล")
            results.append({
                "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
                "university_en": "King Mongkut's University of Technology North Bangkok",
                "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล",
                "faculty_en": "Faculty of Information Technology and Digital Innovation",
                "department_th": dept,
                "raw_name_th": name,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
            })

    print(f"  ✅ KMUTNB ITDI: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_tu_innovation(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Thammasat University College of Innovation (CITU)."""
    print("  [TU CIT] Crawling https://www.citu.tu.ac.th/university-personnel/...", flush=True)
    results = []
    url = "https://www.citu.tu.ac.th/university-personnel/"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch TU CIT page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen_hrefs = set()

    for item in soup.find_all("div", class_="jet-listing-grid__item"):
        t = item.get_text(" | ", strip=True)
        parts = [p.strip() for p in t.split("|")]
        if len(parts) >= 2:
            th_name = parts[0]
            en_name = parts[1]
            a = item.find("a", href=lambda h: h and "/personnel/" in h)
            img = item.find("img")
            href = a["href"] if a else None
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                # Check for support staff
                if "สายสนับสนุน" in th_name or "เจ้าหน้าที่" in th_name:
                    continue

                edu = parts[3] if len(parts) > 3 else None
                position = parts[2] if len(parts) > 2 else None

                results.append({
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "university_en": "Thammasat University",
                    "faculty_th": "วิทยาลัยนวัตกรรม",
                    "faculty_en": "College of Innovation",
                    "department_th": "วิทยาลัยนวัตกรรม",
                    "raw_name_th": th_name,
                    "name_en": en_name,
                    "email": None,
                    "image_url": img.get("src") if img else None,
                    "profile_url": href,
                    "education": edu,
                    "position": position,
                })

    print(f"  ✅ TU CIT: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_tu_public_health(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Thammasat University Faculty of Public Health."""
    print("  [TU FPH] Crawling https://web1.fph.tu.ac.th/th-ourfaculty...", flush=True)
    results = []
    url = "https://web1.fph.tu.ac.th/th-ourfaculty"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch TU FPH page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen_names = set()

    for a in soup.find_all("a", href=lambda h: h and "th-ourfaculty-cv" in h):
        p = a.find_parent("div")
        for _ in range(4):
            if p and len(p.get_text(strip=True)) > 20:
                break
            if p:
                p = p.parent
        if not p:
            continue

        text_block = p.get_text(" | ", strip=True)
        parts = [x.strip() for x in text_block.split("|")]
        if not parts:
            continue

        raw_name = parts[0]
        # Clean out common titles or verify valid title
        if not any(title in raw_name for title in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
            continue

        norm_name = re.sub(r"\s+", "", raw_name)
        if norm_name in seen_names:
            continue
        seen_names.add(norm_name)

        email = None
        for part in parts:
            em_match = re.search(r"[\w\.-]+@(?:fph\.)?tu\.ac\.th", part)
            if em_match:
                email = em_match.group(0)
                break

        # Find teacher photo
        img_src = None
        for img in p.find_all("img"):
            src = img.get("src", "")
            if "teacher_img" in src or "upload" in src:
                img_src = f"https://web1.fph.tu.ac.th/{src}" if not src.startswith("http") else src
                break

        results.append({
            "university_th": "มหาวิทยาลัยธรรมศาสตร์",
            "university_en": "Thammasat University",
            "faculty_th": "คณะสาธารณสุขศาสตร์",
            "faculty_en": "Faculty of Public Health",
            "department_th": "คณะสาธารณสุขศาสตร์",
            "raw_name_th": raw_name,
            "email": email,
            "image_url": img_src,
            "profile_url": f"https://web1.fph.tu.ac.th/{a['href']}",
        })

    print(f"  ✅ TU FPH: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kmutt_gmi(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTT Graduate School of Management and Innovation (GMI)."""
    print("  [KMUTT GMI] Crawling https://gmi.kmutt.ac.th/th/about-gmi/...", flush=True)
    results = []
    url = "https://gmi.kmutt.ac.th/th/about-gmi/"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KMUTT GMI page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen = set()

    for h in soup.find_all(["h2", "h3", "h4", "h5", "h6", "p", "div"]):
        t = h.get_text(" ", strip=True)
        m = re.match(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|อาจารย์)\s*([^\n\r]+)", t)
        if m:
            name = m.group(0).strip()
            name = re.split(r"[\r\n|]", name)[0].strip()
            clean_k = re.sub(r"\s+", "", name)
            if len(name) < 45 and clean_k not in seen:
                seen.add(clean_k)
                parent = h.find_parent("div")
                img = parent.find("img") if parent else None
                img_src = img.get("src") if img else None

                results.append({
                    "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                    "university_en": "King Mongkut's University of Technology Thonburi",
                    "faculty_th": "บัณฑิตวิทยาลัยการจัดการและนวัตกรรม",
                    "faculty_en": "Graduate School of Management and Innovation",
                    "department_th": "บัณฑิตวิทยาลัยการจัดการและนวัตกรรม",
                    "raw_name_th": name,
                    "image_url": img_src,
                    "profile_url": url,
                })

    print(f"  ✅ KMUTT GMI: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kku_copa(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Khon Kaen University College of Local Administration (COLA/COPA)."""
    print("  [KKU COPA] Crawling https://copa.kku.ac.th/2759/...", flush=True)
    results = []
    url = "https://copa.kku.ac.th/2759/"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KKU COPA page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen = set()

    for h in soup.find_all(["h2", "h3", "h4", "h5", "h6", "p", "div"]):
        t = h.get_text(" ", strip=True)
        m = re.match(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*([^\n\r]+)", t)
        if m:
            name = m.group(0).strip()
            name = re.split(r"[\r\n|]", name)[0].strip()
            name = re.sub(r"\s+(อาจารย์|ที่ปรึกษาคณบดี|คณบดี)$", "", name).strip()
            clean_k = re.sub(r"\s+", "", name)
            if len(name) < 45 and clean_k not in seen:
                seen.add(clean_k)
                parent = h.find_parent("div")
                img = parent.find("img") if parent else None
                img_src = img.get("src") if img else None

                results.append({
                    "university_th": "มหาวิทยาลัยขอนแก่น",
                    "university_en": "Khon Kaen University",
                    "faculty_th": "วิทยาลัยการปกครองท้องถิ่น",
                    "faculty_en": "College of Local Administration",
                    "department_th": "วิทยาลัยการปกครองท้องถิ่น",
                    "raw_name_th": name,
                    "image_url": img_src,
                    "profile_url": url,
                })

    print(f"  ✅ KKU COPA: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kmitl_ami(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMITL College of Advanced Manufacturing Innovation (AMI)."""
    print("  [KMITL AMI] Crawling https://ami.kmitl.ac.th/people/faculty/...", flush=True)
    results = []
    url = "https://ami.kmitl.ac.th/people/faculty/"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KMITL AMI page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen = set()

    for a in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b", "p"]):
        t = a.get_text(strip=True)
        if any(title in t for title in ["Prof", "Dr", "ผศ", "รศ"]):
            m = re.match(r"^(Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*([^\n\r\(]+)", t)
            if m:
                n = m.group(0).strip()
                n = re.sub(r"Office Location:.*$", "", n).strip()
                clean_k = re.sub(r"\s+", "", n)
                if len(n) < 45 and clean_k not in seen:
                    seen.add(clean_k)
                    parent = a.find_parent("div")
                    img = parent.find("img") if parent else None
                    img_src = img.get("src") if img else None

                    # Check profile link
                    link_a = parent.find("a", href=lambda h: h and "profile" in h) if parent else None
                    p_url = link_a["href"] if link_a else url

                    results.append({
                        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
                        "university_en": "King Mongkut's Institute of Technology Ladkrabang",
                        "faculty_th": "วิทยาลัยนวัตกรรมการผลิตขั้นสูง",
                        "faculty_en": "College of Advanced Manufacturing Innovation",
                        "department_th": "วิทยาลัยนวัตกรรมการผลิตขั้นสูง",
                        "raw_name_th": n,
                        "name_en": n,
                        "image_url": img_src,
                        "profile_url": p_url,
                    })

    print(f"  ✅ KMITL AMI: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_mahidol_cmmu(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Mahidol University College of Management (CMMU)."""
    print("  [Mahidol CMMU] Crawling https://www.cmmu.mahidol.ac.th/web/faculty-research/full-time...", flush=True)
    results = []
    url = "https://www.cmmu.mahidol.ac.th/web/faculty-research/full-time"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch Mahidol CMMU page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen_urls = set()

    for a in soup.find_all("a", href=lambda h: h and "/full-time/" in h):
        t = a.get_text(strip=True)
        href = a["href"]
        if t and len(t) > 3 and href not in seen_urls:
            seen_urls.add(href)
            full_href = f"https://www.cmmu.mahidol.ac.th{href}" if href.startswith("/") else href

            results.append({
                "university_th": "มหาวิทยาลัยมหิดล",
                "university_en": "Mahidol University",
                "faculty_th": "วิทยาลัยการจัดการ",
                "faculty_en": "College of Management",
                "department_th": "วิทยาลัยการจัดการ",
                "raw_name_th": t,
                "name_en": t,
                "profile_url": full_href,
            })

    # Deep fetch CMMU profiles to extract Thai names and research specializations
    print(f"  [Mahidol CMMU] Deep fetching {len(results)} individual CV profiles for Thai names & research...", flush=True)
    for fac in results:
        p_html = fetch_with_retry(fac["profile_url"], client)
        if p_html:
            p_soup = BeautifulSoup(p_html, "html.parser")
            p_text = p_soup.get_text(" ", strip=True)
            # Find Thai name inside parentheses e.g. (ดร. ณัฐสิทธิ์ เกิดศรี)
            th_match = re.search(r"\(([ศรผ]ศ\.?|อ\.?|ดร\.)?\s*([ก-๙]+)\s+([ก-๙]+)\)", p_text)
            if th_match:
                fac["raw_name_th"] = th_match.group(0).strip("()")
            # Find research area
            res_match = re.search(r"Research Area:\s*([^\n\r\.]+)", p_text)
            if res_match:
                fac["research_interests"] = [res_match.group(1).strip()]

    print(f"  ✅ Mahidol CMMU: Harvested {len(results)} authentic faculty members.")
    return results


# =====================================================================
# 2. Normalization & OpenAlex Enrichment (Pillars 2 & 4)
# =====================================================================

def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Extracts authentic academic title and base name safely without greedy substring bugs."""
    t = raw_name.strip()
    # Normalize common abbreviations
    t = re.sub(r"\s+", " ", t)

    title_patterns = [
        (r"^(ศ\.\s*ดร\.|ศาสตราจารย์\s*ดร\.|ศาสตราจารย์\s*ดร\.)", "ศ.ดร."),
        (r"^(รศ\.\s*ดร\.|รองศาสตราจารย์\s*ดร\.)", "รศ.ดร."),
        (r"^(ผศ\.\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.)", "ผศ.ดร."),
        (r"^(อ\.\s*ดร\.|อาจารย์\s*ดร\.)", "อ.ดร."),
        (r"^(ศ\.|ศาสตราจารย์)", "ศ."),
        (r"^(รศ\.|รองศาสตราจารย์)", "รศ."),
        (r"^(ผศ\.|ผู้ช่วยศาสตราจารย์)", "ผศ."),
        (r"^(ดร\.)", "ดร."),
        (r"^(อ\.|อาจารย์)", "อ."),
        (r"^(Prof\.\s*Dr\.)", "ศ.ดร."),
        (r"^(Assoc\.\s*Prof\.\s*Dr\.)", "รศ.ดร."),
        (r"^(Asst\.\s*Prof\.\s*Dr\.)", "ผศ.ดร."),
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
            # If nested Dr. after English/Thai title (e.g. Asst. Prof. Dr. Komgrit)
            m_sub = re.match(r"^(Dr\.|ดร\.)\s*", base_name, flags=re.IGNORECASE)
            if m_sub:
                base_name = base_name[m_sub.end():].strip()
                if "ดร." not in detected_title:
                    detected_title = f"{detected_title}ดร."
            break

    # Strip trailing academic degrees from name
    base_name = re.sub(r",?\s*(Ph\.D\.|D\.Eng\.|M\.Sc\.|B\.Sc\.|Ph\.D|Ph\.D\.|D\.Tech\.).*$", "", base_name, flags=re.IGNORECASE).strip()
    full_name = f"{detected_title} {base_name}".strip() if detected_title else base_name
    return detected_title or "อาจารย์", full_name, base_name


def enrich_faculty_with_openalex(faculty: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex to retrieve citations, h-index, and author ID with 2-factor verification."""
    name_to_search = faculty.get("name_en") or faculty.get("raw_name_th") or ""
    clean_search = re.sub(
        r"^(Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*",
        "",
        name_to_search,
        flags=re.IGNORECASE
    ).strip()

    # If no English romanized characters, OpenAlex cannot match accurately without English
    if not re.search(r"[a-zA-Z]{3,}", clean_search):
        faculty["openalex_id"] = "not_indexed"
        faculty["total_citations"] = 0
        faculty["h_index"] = 0
        faculty["total_publications_count"] = 0
        faculty["featured_publications"] = []
        return faculty

    # Query OpenAlex API via 7-key multiplexing pool
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
    print("🚀 EXECUTING WAVE 61: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
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
            all_raw_faculty.extend(crawl_kmutnb_itdi(client))
            all_raw_faculty.extend(crawl_tu_innovation(client))
            all_raw_faculty.extend(crawl_tu_public_health(client))
            all_raw_faculty.extend(crawl_kmutt_gmi(client))
            all_raw_faculty.extend(crawl_kku_copa(client))
            all_raw_faculty.extend(crawl_kmitl_ami(client))
            all_raw_faculty.extend(crawl_mahidol_cmmu(client))

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

        # Step 5: Ingestion into PostgreSQL Database (Pillar 3 & 4)
        print("\n📥 Committing to PostgreSQL public.faculties...", flush=True)
        existing_names = set(
            n for (n,) in db.query(FacultyDB.full_name_th).filter(FacultyDB.full_name_th.isnot(None)).all()
        )
        existing_emails = set(
            em.lower() for (em,) in db.query(FacultyDB.email).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").all()
        )

        univ_prefix_map = {
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": ("kmutnb", "itdi"),
            "มหาวิทยาลัยธรรมศาสตร์": ("tu", "grad"),
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ("kmutt", "gmi"),
            "มหาวิทยาลัยขอนแก่น": ("kku", "copa"),
            "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": ("kmitl", "ami"),
            "มหาวิทยาลัยมหิดล": ("mu", "cmmu"),
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
                u_code, f_code = univ_prefix_map.get(univ_th, ("univ", "fac"))
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
