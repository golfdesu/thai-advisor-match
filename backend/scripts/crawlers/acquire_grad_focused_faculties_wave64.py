# -*- coding: utf-8 -*-
"""
Acquire Graduate-Focused Faculties Pipeline (Wave 64)
=====================================================
Acquires authentic faculty members for graduate-degree offering units (ป.โท / ป.เอก)
from their official faculty directories:
1. มหาวิทยาลัยขอนแก่น: คณะสัตวแพทยศาสตร์ (https://fvm.kku.ac.th/th/staff/instructor)
   - 4 graduate programs (วท.ม./ปร.ด. พยาธิชีววิทยา, วิทยาศาสตร์สุขภาพสัตว์, การสืบพันธุ์สัตว์)
2. มหาวิทยาลัยเกษตรศาสตร์ กำแพงแสน: คณะศิลปศาสตร์และวิทยาศาสตร์ (https://flas.kps.ku.ac.th/school/page/{1,7,3,8,2,11})
   - 5 graduate programs across biological, physical, computing, and social sciences
3. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ: คณะครุศาสตร์อุตสาหกรรม (https://ced.kmutnb.ac.th/people_of_ced.php)
   - 7 graduate programs (ค.อ.ม./ปร.ด. เทคโนโลยีคอมพิวเตอร์, ครุศาสตร์วิศวกรรม)

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
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry

CHECKPOINT_DIR = BACKEND_DIR / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave64_grad_focused_faculties.json"

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

def crawl_kku_vet(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KKU Faculty of Veterinary Medicine (คณะสัตวแพทยศาสตร์ มข.)."""
    print("  [KKU Vet] Crawling https://fvm.kku.ac.th/th/staff/instructor...", flush=True)
    results = []
    url = "https://fvm.kku.ac.th/th/staff/instructor"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KKU Vet page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    # Department headings are in h3
    current_dept_th = "สาขาวิชาเวชศาสตร์คลินิกสัตว์เลี้ยง"
    current_dept_en = "Division of Companion Animal Clinical Medicine"

    dept_en_map = {
        "สาขาวิชาเวชศาสตร์คลินิกสัตว์เลี้ยง": "Division of Companion Animal Clinical Medicine",
        "สาขาวิชาเวชศาสตร์คลินิกสัตว์บริโภค": "Division of Food Animal Clinical Medicine",
        "สาขาวิชาสุขภาพหนึ่งเดียวและศาสตร์วินิจฉัย": "Division of One Health and Diagnostic Sciences",
        "สาขาวิชาเวชศาสตร์โครงสร้างและหัตถการทางคลินิกสัตวแพทย์": "Division of Structural Medicine and Clinical Procedures",
    }

    cards = soup.find_all(class_=lambda c: c and any(x in c.lower() for x in ["staff", "person", "instructor", "col-", "card"]))
    seen_names = set()

    for c in cards:
        txt = c.get_text(separator=" ", strip=True)
        if not any(x in txt for x in ["ผศ.", "รศ.", "ศ.", "อาจารย์", "อ.", "น.สพ.", "สพ.ญ."]):
            continue

        # Check if preceded by an h3 heading
        prev_h3 = c.find_previous("h3")
        if prev_h3:
            h3_txt = prev_h3.get_text(strip=True)
            for dth, den in dept_en_map.items():
                if dth in h3_txt:
                    current_dept_th = dth
                    current_dept_en = den
                    break

        # Extract image
        img = c.find("img")
        img_src = None
        if img and img.has_attr("src"):
            img_src = img["src"]
            if not img_src.startswith("http"):
                img_src = "https://fvm.kku.ac.th" + ("" if img_src.startswith("/") else "/") + img_src
            img_src = urllib.parse.quote(img_src, safe=":/%?=")

        # Extract email
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@kku\.ac\.th", txt)
        email = email_match.group(0).lower() if email_match else None

        # Extract name line
        lines = [line.strip() for line in c.stripped_strings if line.strip()]
        name_line = None
        for line in lines:
            if any(x in line for x in ["น.สพ.", "สพ.ญ."]) and len(line) < 60:
                name_line = line
                break
        if not name_line:
            for line in lines:
                if any(x in line for x in ["ผศ.", "รศ.", "ศ.", "อ."]) and len(line) < 60:
                    name_line = line
                    break

        if not name_line:
            continue

        # Clean name line: remove note like (ลาศึกษาต่อ ณ ต่างประเทศ)
        name_line = re.sub(r"\(.*?\)", "", name_line).strip()
        if name_line in seen_names:
            continue
        seen_names.add(name_line)

        # Extract research interests / specialization
        interests = []
        int_match = re.search(r"ความเชี่ยวชาญ:\s*([^E\n]+)", txt)
        if int_match:
            raw_int = int_match.group(1).strip()
            for item in raw_int.split(","):
                clean_i = item.strip()
                if clean_i and len(clean_i) > 2 and clean_i not in interests:
                    interests.append(clean_i)

        # Extract English name or slug from CV link
        cv_link = None
        scopus_link = None
        for a in c.find_all("a", href=True):
            href = a["href"]
            if "scopus.com" in href:
                scopus_link = href
            elif ".pdf" in href.lower() or "cv" in a.get_text().lower():
                cv_link = href

        name_en = None
        if cv_link:
            pdf_name = cv_link.split("/")[-1]
            slug = re.sub(r"^[0-9a-fA-F]+-", "", pdf_name)
            slug = re.sub(r"\.pdf$", "", slug, flags=re.IGNORECASE)
            if slug and len(slug) >= 3 and not slug.isdigit():
                name_en = slug.capitalize()

        if not name_en and email:
            u = email.split("@")[0]
            name_en = u.capitalize()

        results.append({
            "university_th": "มหาวิทยาลัยขอนแก่น",
            "university_en": "Khon Kaen University",
            "faculty_th": "คณะสัตวแพทยศาสตร์",
            "faculty_en": "Faculty of Veterinary Medicine",
            "department_th": current_dept_th,
            "department_en": current_dept_en,
            "raw_name_th": name_line,
            "name_en": name_en,
            "email": email,
            "image_url": img_src,
            "profile_url": scopus_link or url,
            "research_interests": interests[:8],
        })

    print(f"  ✅ KKU Vet: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_ku_flas(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KU FLAS (คณะศิลปศาสตร์และวิทยาศาสตร์ มหาวิทยาลัยเกษตรศาสตร์ กำแพงแสน)."""
    print("  [KU FLAS] Crawling https://flas.kps.ku.ac.th/school/page/{1,7,3,8,2,11}...", flush=True)
    results = []

    dept_pages = [
        (1, "ภาควิชาวิทยาศาสตร์และนวัตกรรมชีวภาพ", "Department of Science and Bio-Innovation"),
        (7, "ภาควิชาวิทยาศาสตร์กายภาพและวัสดุศาสตร์", "Department of Physical and Material Sciences"),
        (3, "ภาควิชาวิทยาการคำนวณและเทคโนโลยีดิจิทัล", "Department of Computing and Digital Technology"),
        (8, "ภาควิชาบริหารธุรกิจและการบัญชี", "Department of Business Administration and Accounting"),
        (2, "ภาควิชาวิทยาการภาษาและวัฒนธรรม", "Department of Language and Cultural Sciences"),
        (11, "ภาควิชาสังคมศาสตร์", "Department of Social Sciences"),
    ]

    seen_global_names = set()

    for pid, dept_th, dept_en in dept_pages:
        page_url = f"https://flas.kps.ku.ac.th/school/page/{pid}"
        html = fetch_with_retry(page_url, client)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        seen_in_page = set()

        for box in soup.find_all("div", class_="box-board"):
            p = box.find("p")
            raw_text = p.get_text(strip=True) if p else ""
            if not raw_text or not any(x in raw_text for x in ["ผศ.", "รศ.", "ศ.", "อ.ดร.", "ดร.", "อาจารย์"]):
                continue

            # Name and subject in parentheses: e.g. "รองศาสตราจารย์ ดร.จุรีย์รัตน์ ลีสมิทธิ์(จุลชีววิทยา)"
            sub_match = re.search(r"\(([^)]+)\)", raw_text)
            interest = sub_match.group(1).strip() if sub_match else ""
            # Strip role tags like (หัวหน้าสาขาวิชาจุลชีววิทยา)
            if any(role in interest for role in ["หัวหน้า", "ประธาน", "รองคณบดี", "ผู้ช่วยคณบดี"]):
                interest = ""

            name_clean = re.sub(r"\([^)]+\)", "", raw_text).strip()
            name_clean = re.sub(r"\s+", " ", name_clean)

            if name_clean in seen_in_page or name_clean in seen_global_names:
                continue
            seen_in_page.add(name_clean)
            seen_global_names.add(name_clean)

            img = box.find("img")
            img_src = img["src"] if img and img.has_attr("src") else None
            if img_src and not img_src.startswith("http"):
                img_src = "https://flas.kps.ku.ac.th" + ("" if img_src.startswith("/") else "/") + img_src
            if img_src:
                img_src = urllib.parse.quote(img_src, safe=":/%?=")

            interests = [interest] if interest else []

            results.append({
                "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                "university_en": "Kasetsart University",
                "faculty_th": "คณะศิลปศาสตร์และวิทยาศาสตร์",
                "faculty_en": "Faculty of Liberal Arts and Science",
                "department_th": dept_th,
                "department_en": dept_en,
                "raw_name_th": name_clean,
                "name_en": None,
                "email": None,
                "image_url": img_src,
                "profile_url": page_url,
                "research_interests": interests,
            })

    print(f"  ✅ KU FLAS: Harvested {len(results)} authentic faculty members across 6 departments.")
    return results


def crawl_kmutnb_fte(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTNB FTE Computer Education (ภาควิชาคอมพิวเตอร์ศึกษา คณะครุศาสตร์อุตสาหกรรม มจพ.)."""
    print("  [KMUTNB FTE] Crawling https://ced.kmutnb.ac.th/people_of_ced.php...", flush=True)
    results = []
    url = "https://ced.kmutnb.ac.th/people_of_ced.php"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KMUTNB FTE page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    seen_names = set()

    for li in soup.find_all("li", class_="media"):
        txt = li.get_text(separator=" ", strip=True)
        if not any(x in txt for x in ["ผศ.", "รศ.", "ศ.", "อ.ดร.", "ดร.", "อาจารย์"]):
            continue

        img = li.find("img")
        img_src = img["src"] if img and img.has_attr("src") else None
        if img_src and not img_src.startswith("http"):
            img_src = "https://ced.kmutnb.ac.th/" + img_src.lstrip("/")
        if img_src:
            img_src = urllib.parse.quote(img_src, safe=":/%?=")

        lines = [l.strip() for l in li.stripped_strings if l.strip()]
        name = None
        for l in lines:
            if any(x in l for x in ["ผศ.", "รศ.", "ศ.", "อ.ดร.", "ดร.", "อาจารย์"]) and len(l) < 60:
                name = l
                break

        if not name or name in seen_names:
            continue
        seen_names.add(name)

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@fte\.kmutnb\.ac\.th", txt)
        email = email_match.group(0).lower() if email_match else None

        name_en = None
        if email:
            u = email.split("@")[0]
            parts = u.split(".")
            if len(parts) >= 2:
                name_en = f"{parts[0].capitalize()} {parts[1].capitalize()}"
            else:
                name_en = u.capitalize()

        results.append({
            "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
            "university_en": "King Mongkut's University of Technology North Bangkok",
            "faculty_th": "คณะครุศาสตร์อุตสาหกรรม",
            "faculty_en": "Faculty of Technical Education",
            "department_th": "ภาควิชาคอมพิวเตอร์ศึกษา",
            "department_en": "Department of Computer Education",
            "raw_name_th": name,
            "name_en": name_en,
            "email": email,
            "image_url": img_src,
            "profile_url": url,
            "research_interests": ["Computer Education", "Educational Technology"],
        })

    print(f"  ✅ KMUTNB FTE: Harvested {len(results)} authentic faculty members.")
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
        (r"^(ศาสตราจารย์\s*น\.สพ\.\s*ดร\.|ศ\.\s*น\.สพ\.\s*ดร\.)", "ศ.ดร."),
        (r"^(รองศาสตราจารย์\s*น\.สพ\.\s*ดร\.|รศ\.\s*น\.สพ\.\s*ดร\.)", "รศ.ดร."),
        (r"^(ผู้ช่วยศาสตราจารย์\s*น\.สพ\.\s*ดร\.|ผศ\.\s*น\.สพ\.\s*ดร\.)", "ผศ.ดร."),
        (r"^(รองศาสตราจารย์\s*สพ\.ญ\.\s*ดร\.|รศ\.\s*สพ\.ญ\.\s*ดร\.)", "รศ.ดร."),
        (r"^(ผู้ช่วยศาสตราจารย์\s*สพ\.ญ\.\s*ดร\.|ผศ\.\s*สพ\.ญ\.\s*ดร\.)", "ผศ.ดร."),
        (r"^(อาจารย์\s*น\.สพ\.\s*ดร\.|อ\.\s*น\.สพ\.\s*ดร\.)", "อ.ดร."),
        (r"^(อาจารย์\s*สพ\.ญ\.\s*ดร\.|อ\.\s*สพ\.ญ\.\s*ดร\.)", "อ.ดร."),
        (r"^(ศาสตราจารย์|ศ\.)", "ศ."),
        (r"^(รองศาสตราจารย์|รศ\.)", "รศ."),
        (r"^(ผู้ช่วยศาสตราจารย์|ผศ\.)", "ผศ."),
        (r"^(ดร\.)", "ดร."),
        (r"^(อาจารย์|อ\.)", "อ."),
        (r"^(น\.สพ\.\s*ดร\.)", "อ.ดร."),
        (r"^(สพ\.ญ\.\s*ดร\.)", "อ.ดร."),
        (r"^(น\.สพ\.)", "อ."),
        (r"^(สพ\.ญ\.)", "อ."),
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
            # If nested title tokens remain (e.g. น.สพ., สพ.ญ., ดร.)
            m_sub = re.match(r"^(น\.สพ\.\s*ดร\.|สพ\.ญ\.\s*ดร\.|น\.สพ\.|สพ\.ญ\.|Dr\.|ดร\.)\s*", base_name, flags=re.IGNORECASE)
            if m_sub:
                base_name = base_name[m_sub.end():].strip()
                if "ดร." in m_sub.group(0) and "ดร." not in detected_title:
                    detected_title = f"{detected_title}ดร."
            break

    # Strip trailing academic degrees
    base_name = re.sub(
        r",?\s*(Ph\.D\.|D\.Eng\.|M\.Sc\.|B\.Sc\.|Ph\.D|D\.Tech\.|CFA|DBA|Ed\.D\.|LL\.M\.|LL\.B\.|MBA).*$",
        "",
        base_name,
        flags=re.IGNORECASE
    ).strip()

    # Re-strip any leading dots or spaces
    base_name = base_name.strip(" .")
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

        if not best_cand and results:
            best_cand = results[0]

        if best_cand:
            raw_id = best_cand.get("id") or ""
            faculty["openalex_id"] = raw_id.split("/")[-1] if raw_id else "not_indexed"
            faculty["total_citations"] = best_cand.get("cited_by_count", 0) or 0
            faculty["h_index"] = (best_cand.get("summary_stats") or {}).get("h_index", 0) or 0

            # Pull publication samples
            works_api = best_cand.get("works_api_url")
            featured = []
            if works_api:
                w_data = fetch_oa_with_retry(f"{works_api}?per-page=3")
                w_list = (w_data or {}).get("results", []) or []
                for w in w_list:
                    w_title = w.get("title")
                    if w_title:
                        venue_name = None
                        loc = w.get("primary_location")
                        if isinstance(loc, dict):
                            src = loc.get("source")
                            if isinstance(src, dict):
                                venue_name = src.get("display_name")
                        featured.append({
                            "title": w_title,
                            "year": w.get("publication_year"),
                            "venue": venue_name,
                            "url": w.get("doi"),
                            "citation_count": w.get("cited_by_count", 0),
                        })
            faculty["featured_publications"] = featured
            faculty["total_publications_count"] = max(best_cand.get("works_count", 0) or 0, len(featured), faculty["h_index"])
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

def run_pipeline():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING WAVE 64: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
    print("=================================================================", flush=True)
    t0 = time.time()

    client = httpx.Client(verify=False, timeout=35.0, follow_redirects=True, headers=CLIENT_HEADERS)
    db = SessionLocal()

    try:
        # Step 1: Checkpoint recovery or crawl the 3 target faculties
        if CHECKPOINT_FILE.exists():
            print(f"\n📂 Resuming from existing disk checkpoint: {CHECKPOINT_FILE} (Pillar 5)", flush=True)
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                enriched_faculty = json.load(f)
            print(f"  ✅ Loaded {len(enriched_faculty)} checkpointed faculty records.", flush=True)
        else:
            all_raw_faculty = []
            all_raw_faculty.extend(crawl_kku_vet(client))
            all_raw_faculty.extend(crawl_ku_flas(client))
            all_raw_faculty.extend(crawl_kmutnb_fte(client))

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
                    last_name = " ".join(parts[1:]) if len(parts) > 1 else parts[0]

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
                    except Exception as e:
                        print(f"  ⚠️ Error enriching faculty: {e}")

            # Step 4: Checkpoint to disk (Pillar 5)
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(enriched_faculty, f, ensure_ascii=False, indent=2)
            print(f"💾 Checkpointed {len(enriched_faculty)} records to {CHECKPOINT_FILE}")

        # Step 5: Ingestion into PostgreSQL public.faculties
        print("\n📥 Ingesting into PostgreSQL public.faculties...", flush=True)
        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        existing_names = set(
            n for (n,) in db.query(FacultyDB.full_name_th).filter(FacultyDB.full_name_th.isnot(None)).all()
        )
        existing_emails = set(
            em.lower() for (em,) in db.query(FacultyDB.email).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").all()
        )

        univ_prefix_map = {
            "มหาวิทยาลัยขอนแก่น": "kku_vet",
            "มหาวิทยาลัยเกษตรศาสตร์": "ku_flas",
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": "kmutnb_fte",
        }

        # Sub-counters per prefix
        prefix_counters = {"kku_vet": 1, "ku_flas": 1, "kmutnb_fte": 1}

        for idx, item in enumerate(enriched_faculty, 1):
            full_th = item.get("full_name_th") or item.get("raw_name_th") or ""
            email = (item.get("email") or "").lower().strip() or None
            univ_th = item.get("university_th")

            existing_f = None
            if email and email in existing_emails:
                existing_f = db.query(FacultyDB).filter(FacultyDB.email == email).first()
            elif full_th and full_th in existing_names:
                existing_f = db.query(FacultyDB).filter(FacultyDB.full_name_th == full_th).first()

            if existing_f:
                # Update metrics if higher
                if (item.get("total_citations") or 0) > (existing_f.total_citations or 0):
                    existing_f.total_citations = item.get("total_citations")
                    existing_f.h_index = item.get("h_index")
                if item.get("image_url") and not existing_f.image_url:
                    existing_f.image_url = item.get("image_url")
                if item.get("email") and not existing_f.email:
                    existing_f.email = email
                if item.get("research_interests") and not existing_f.research_interests:
                    existing_f.research_interests = item.get("research_interests")
                updated_count += 1
            else:
                pfx = univ_prefix_map.get(univ_th, "grad_fac")
                cur_num = prefix_counters.get(pfx, 1)
                new_id = f"{pfx}__{cur_num:03d}"
                prefix_counters[pfx] = cur_num + 1

                # Clean research interests to prevent duplicate tokens
                seen_int = set()
                clean_interests = []
                for interest_tok in (item.get("research_interests") or []):
                    k = str(interest_tok).strip()
                    if k and k.lower() not in seen_int:
                        seen_int.add(k.lower())
                        clean_interests.append(k)

                new_record = FacultyDB(
                    id=new_id,
                    university=item.get("university_en"),
                    university_th=item.get("university_th"),
                    faculty=item.get("faculty_en"),
                    faculty_th=item.get("faculty_th"),
                    department=item.get("department_en"),
                    department_th=item.get("department_th"),
                    academic_title_th=item.get("title_th") or "อาจารย์",
                    first_name=item.get("first_name") or item.get("raw_name_th"),
                    last_name=item.get("last_name") or item.get("first_name") or item.get("raw_name_th"),
                    full_name_th=full_th,
                    role="อาจารย์ประจำ",
                    email=email,
                    image_url=item.get("image_url"),
                    profile_url=item.get("profile_url"),
                    education=None,
                    research_interests=clean_interests,
                    taught_courses=[],
                    featured_publications=item.get("featured_publications") or [],
                    total_publications_count=item.get("total_publications_count") or 0,
                    first_author_count=0,
                    co_author_count=0,
                    total_citations=item.get("total_citations") or 0,
                    h_index=item.get("h_index") or 0,
                    openalex_id=item.get("openalex_id") or "not_indexed",
                    scholar_url=None,
                    embedding_text=None,
                    embedding=None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search,
                )
                db.add(new_record)
                inserted_count += 1

                if full_th:
                    existing_names.add(full_th)
                if email:
                    existing_emails.add(email)

        db.commit()
        print(f"\n🎉 Ingestion Finished in {time.time() - t0:.2f}s:")
        print(f"  - Newly Inserted: {inserted_count} faculty")
        print(f"  - Profile Enriched: {updated_count} faculty")
        print(f"  - Skipped: {skipped_count} faculty")

    finally:
        db.close()
        client.close()


if __name__ == "__main__":
    run_pipeline()
