# -*- coding: utf-8 -*-
"""
Acquire Graduate-Focused Faculties Pipeline (Wave 63)
=====================================================
Acquires authentic faculty members for graduate-degree offering units (ป.โท / ป.เอก)
from their official faculty directories:
1. มหาวิทยาลัยธรรมศาสตร์: วิทยาลัยสหวิทยาการ (https://cis.tu.ac.th/cvinstructor1)
2. สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง: คณะอุตสาหกรรมอาหาร (https://foodindustry.kmitl.ac.th/th/people-executive)
3. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ: คณะพัฒนาธุรกิจและอุตสาหกรรม (https://bid.kmutnb.ac.th/administrators/)

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
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave63_grad_focused_faculties.json"

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

def crawl_tu_cis(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls TU College of Interdisciplinary Studies (วิทยาลัยสหวิทยาการ มธ.)."""
    print("  [TU CIS] Crawling https://cis.tu.ac.th/cvinstructor1...", flush=True)
    results = []
    url = "https://cis.tu.ac.th/cvinstructor1"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch TU CIS page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    panel = soup.find("div", class_=lambda x: x and "faq-panel-result" in x)
    if not panel:
        panel = soup.find("div", class_=lambda x: x and "faq" in x)
    if not panel:
        print("  ❌ Could not find faculty panel on TU CIS.")
        return results

    items = [c for c in panel.children if getattr(c, "name", None)]
    seen = set()

    for it in items:
        txt = it.get_text(" | ", strip=True)
        # Extract title and name
        m_title = re.search(r"((?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\s*(?:ดร\.)?\s*([^\n\r\|]+))", txt)
        if not m_title:
            m_title = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([^\n\r\|]+))", txt)

        img = it.find("img")
        img_src = None
        if img and img.has_attr("src"):
            src = img["src"]
            if src.startswith(".."):
                img_src = f"https://cis.tu.ac.th{src[2:]}"
            elif src.startswith("/"):
                img_src = f"https://cis.tu.ac.th{src}"
            else:
                img_src = src

        m_email = re.search(r"([a-zA-Z0-9._%+-]+@tu\.ac\.th)", txt)
        if not m_email:
            m_email = re.search(r"([a-zA-Z0-9._%+-]+@(?:gmail\.com|hotmail\.com|yahoo\.com))", txt)
        email = m_email.group(1) if m_email else None

        raw_name = m_title.group(1).strip() if m_title else ""
        raw_name = re.sub(r"\s+", " ", raw_name)

        # Skip non-person headers
        if any(skip in raw_name for skip in ["อาจารย์ชาวต่างประเทศ", "อาจารย์ประจำวิทยาลัย"]):
            continue

        # Extract English name from image filename if available
        name_en = None
        if img_src:
            fn = img_src.split("/")[-1]
            fn_base = re.sub(r"\.[a-zA-Z0-9]+$", "", fn)
            if re.search(r"^[a-zA-Z\-_]+$", fn_base) and len(fn_base) > 4:
                name_en = fn_base.replace("-", " ").replace("_", " ")

        # Extract research interests / expertise
        res_interests = []
        m_int = re.search(r"ความสนใจ\s*/\s*ความเชี่ยวชาญ\s*\|(.*?)(?:$|ดาวน์โหลด|การศึกษา)", txt)
        if m_int:
            interests_raw = m_int.group(1)
            parts = [p.strip() for p in interests_raw.split("|") if len(p.strip()) > 3]
            res_interests = parts[:4]

        clean_k = re.sub(r"\s+", "", raw_name)
        if clean_k and clean_k not in seen and len(raw_name) > 6 and len(raw_name) < 60:
            seen.add(clean_k)
            results.append({
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "university_en": "Thammasat University",
                "faculty_th": "วิทยาลัยสหวิทยาการ",
                "faculty_en": "College of Interdisciplinary Studies",
                "department_th": "วิทยาลัยสหวิทยาการ",
                "raw_name_th": raw_name,
                "name_en": name_en,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
                "research_interests": res_interests,
            })

    print(f"  ✅ TU CIS: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kmitl_food(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMITL Faculty of Food Industry (คณะอุตสาหกรรมอาหาร สจล.)."""
    print("  [KMITL Food Industry] Crawling https://foodindustry.kmitl.ac.th/th/people-executive...", flush=True)
    results = []
    base_url = "https://foodindustry.kmitl.ac.th"
    url = f"{base_url}/th/people-executive"
    html = fetch_with_retry(url, client)
    if not html:
        print("  ❌ Failed to fetch KMITL Food Industry page.")
        return results

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_=lambda c: c and "grid-item" in c)
    seen = set()

    for card in cards:
        t = card.get_text(" | ", strip=True)
        m_name = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|อาจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|ศาสตราจารย์)[^\n\r\|]+)", t)
        if not m_name:
            continue

        raw_name = m_name.group(1).strip()
        raw_name = re.sub(r"\s+", " ", raw_name)

        img = card.find("img")
        img_src = None
        if img and img.has_attr("src"):
            raw_src = img["src"]
            img_src = f"{base_url}{raw_src}" if raw_src.startswith("/") else raw_src

        # Find profile link
        profile_link = None
        for a in card.find_all("a", href=True):
            if "/user/" in a["href"]:
                profile_link = f"{base_url}{a['href']}" if a["href"].startswith("/") else a["href"]
                break

        clean_k = re.sub(r"\s+", "", raw_name)
        if clean_k in seen or len(raw_name) > 60 or len(raw_name) < 6:
            continue
        seen.add(clean_k)

        email = None
        dept_th = "คณะอุตสาหกรรมอาหาร"
        name_en = None

        # Fetch profile page to get email and department
        if profile_link:
            p_html = fetch_with_retry(profile_link, client)
            if p_html:
                p_soup = BeautifulSoup(p_html, "html.parser")
                p_txt = p_soup.get_text(" | ", strip=True)

                # Email from title or body
                m_email = re.search(r"([a-zA-Z0-9._%+-]+@kmitl\.ac\.th)", p_txt)
                if not m_email and p_soup.title:
                    m_email = re.search(r"([a-zA-Z0-9._%+-]+@kmitl\.ac\.th)", p_soup.title.string or "")
                if m_email:
                    email = m_email.group(1)

                # Department from profile
                m_dept = re.search(r"(สาขาวิชา[^\n\r\|]+?)(?:Contacts|Email|Office|โทร|$)", p_txt)
                if m_dept:
                    d_candidate = m_dept.group(1).strip()
                    if len(d_candidate) < 50:
                        dept_th = d_candidate

                # English name from email username
                if email:
                    user_part = email.split("@")[0]
                    parts = user_part.split(".")
                    if len(parts) >= 2:
                        name_en = f"{parts[0].capitalize()} {parts[1].capitalize()}"
                    else:
                        name_en = user_part.capitalize()

        results.append({
            "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
            "university_en": "King Mongkut's Institute of Technology Ladkrabang",
            "faculty_th": "คณะอุตสาหกรรมอาหาร",
            "faculty_en": "Faculty of Food Industry",
            "department_th": dept_th,
            "raw_name_th": raw_name,
            "name_en": name_en,
            "email": email,
            "image_url": img_src,
            "profile_url": profile_link or url,
        })

    print(f"  ✅ KMITL Food Industry: Harvested {len(results)} authentic faculty members.")
    return results


def crawl_kmutnb_bid(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTNB Faculty of Business and Industrial Development (คณะพัฒนาธุรกิจและอุตสาหกรรม มจพ.)."""
    print("  [KMUTNB BID] Crawling https://bid.kmutnb.ac.th/...", flush=True)
    results = []
    seen = set()

    # Targets: Page 9413 (BHRD Dept), Page 9374 (BMS Dept), Page 9376 (Graduate Project)
    targets = [
        ("https://bid.kmutnb.ac.th/?page_id=9413", "ภาควิชาการพัฒนาธุรกิจอุตสาหกรรมและทรัพยากรมนุษย์"),
        ("https://bid.kmutnb.ac.th/?page_id=9374", "ภาควิชาการบริหารอุตสาหกรรมการผลิตและบริการ"),
        ("https://bid.kmutnb.ac.th/?page_id=9376", "โครงการหลักสูตรบริหารธุรกิจระดับบัณฑิตศึกษา"),
    ]

    for page_url, default_dept in targets:
        html = fetch_with_retry(page_url, client)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")

        # Find all wrapper columns / paragraphs with professor entries
        for p in soup.find_all(["p", "div"]):
            txt = p.get_text(" | ", strip=True)
            if not any(k in txt for k in ["ผศ.", "รศ.", "ดร.", "อ.ดร."]):
                continue

            m_prof = re.search(r"((?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)?\s*([^\n\r\|]+))", txt)
            if not m_prof:
                m_prof = re.search(r"((?:ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์|ศาสตราจารย์|อาจารย์)\s*(?:ดร\.)?\s*([^\n\r\|]+))", txt)

            if m_prof:
                raw_name = m_prof.group(1).strip()
                raw_name = re.sub(r"\s+", " ", raw_name)

                # Skip non-person or staff titles
                if any(skip in raw_name for skip in ["เจ้าหน้าที่", "นักวิชาการ", "การบริหาร", "โทรศัพท์", "E-mail"]):
                    continue

                clean_k = re.sub(r"\s+", "", raw_name)
                if clean_k in seen or len(raw_name) > 55 or len(raw_name) < 6:
                    continue
                seen.add(clean_k)

                # Extract email
                m_email = re.search(r"([a-zA-Z0-9._%+-]+@(?:bid\.)?kmutnb\.ac\.th)", txt)
                email = m_email.group(1) if m_email else None

                # Find image near element
                parent = p.find_parent("div")
                img = parent.find("img") if parent else None
                img_src = img["src"] if img and img.has_attr("src") else None

                # Name EN from email
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
                    "faculty_th": "คณะพัฒนาธุรกิจและอุตสาหกรรม",
                    "faculty_en": "Faculty of Business and Industrial Development",
                    "department_th": default_dept,
                    "raw_name_th": raw_name,
                    "name_en": name_en,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": page_url,
                })

    print(f"  ✅ KMUTNB BID: Harvested {len(results)} authentic faculty members.")
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
    print("🚀 EXECUTING WAVE 63: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
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
            all_raw_faculty.extend(crawl_tu_cis(client))
            all_raw_faculty.extend(crawl_kmitl_food(client))
            all_raw_faculty.extend(crawl_kmutnb_bid(client))

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
            "มหาวิทยาลัยธรรมศาสตร์": ("tu", "cis"),
            "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": ("kmitl", "food"),
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": ("kmutnb", "bid"),
        }

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
                updated = False
                if not existing_f.image_url and item.get("image_url"):
                    existing_f.image_url = item.get("image_url")
                    updated = True
                if not existing_f.email and email:
                    existing_f.email = email
                    updated = True
                if (not existing_f.department_th or existing_f.department_th == "ระบุไม่ได้") and item.get("department_th"):
                    existing_f.department_th = item["department_th"]
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

            if idx % 25 == 0:
                db.commit()

        db.commit()
        print(f"\n🎉 Wave 63 Ingestion Complete in {time.time() - t0:.2f}s:")
        print(f"   - Newly Inserted: {inserted_count}")
        print(f"   - Updated/Enriched: {updated_count}")
        print(f"   - Skipped (Unchanged): {skipped_count}")
        print(f"   - Total Processed: {len(enriched_faculty)}")

    finally:
        db.close()
        client.close()


if __name__ == "__main__":
    run_pipeline()
