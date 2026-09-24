# -*- coding: utf-8 -*-
"""
Acquire Graduate-Focused Faculties Pipeline (Wave 60)
=====================================================
Acquires verified faculty members for graduate-degree offering faculties (ป.โท / ป.เอก)
with low density from their official faculty directories:
1. มหาวิทยาลัยขอนแก่น: คณะเทคโนโลยี (https://te.kku.ac.th/board/?page_id=315)
2. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ: คณะบริหารธุรกิจ (https://fba.kmutnb.ac.th/main/...)
3. มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี: คณะศิลปศาสตร์ (https://sola.pr.kmutt.ac.th/...)
4. มหาวิทยาลัยสงขลานครินทร์: คณะพยาบาลศาสตร์ (https://www.nur.psu.ac.th/nur/teacher.aspx)
5. มหาวิทยาลัยธรรมศาสตร์: วิทยาลัยโลกคดีศึกษา (https://sgs.tu.ac.th/faculty/)

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
from rapidfuzz import fuzz
from sqlalchemy import text

from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

CHECKPOINT_DIR = BACKEND_DIR / "data" / "agent_states"
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave60_grad_focused_faculties.json"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}


# =====================================================================
# 1. Target Web Scrapers (Grounded strictly to official portals)
# =====================================================================

def crawl_kku_technology(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KKU Faculty of Technology official staff directory."""
    print("  [1/5] Fetching KKU Faculty of Technology...", flush=True)
    url = "https://te.kku.ac.th/board/?page_id=315"
    resp = client.get(url, timeout=35.0)
    if resp.status_code != 200:
        print(f"    ❌ Failed to fetch KKU Tech (Status: {resp.status_code})")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.find_all("div", class_=re.compile(r"ugb-feature-grid__item"))
    results = []

    # Map sections by checking headings before items
    current_dept = "สาขาวิชาเทคโนโลยีชีวภาพ"
    dept_map = {
        "ชีวภาพ": "สาขาวิชาเทคโนโลยีชีวภาพ",
        "อาหาร": "สาขาวิชาเทคโนโลยีการอาหาร",
        "ธรณี": "สาขาวิชาเทคโนโลยีธรณี",
    }

    for it in items:
        # Check if preceded by a department header
        prev_h = it.find_previous(["h2", "h3", "h4", "h5"])
        if prev_h:
            h_text = prev_h.get_text().strip()
            for kw, d_name in dept_map.items():
                if kw in h_text:
                    current_dept = d_name
                    break

        img = it.find("img")
        img_alt = (img.get("alt") or "").strip() if img else ""
        img_src = (img.get("src") or "").strip() if img else ""

        text_content = it.get_text(separator=" ").strip()
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@kku\.ac\.th", text_content)
        email = emails[0] if emails else None

        title_el = it.find(class_=re.compile(r"title"))
        title_txt = title_el.get_text().strip() if title_el else ""

        desc_el = it.find(class_=re.compile(r"description"))
        desc_txt = desc_el.get_text(separator=" ").strip() if desc_el else ""

        raw_name = title_txt or img_alt
        if not raw_name and desc_txt:
            raw_name = desc_txt.split(" ")[0]

        if raw_name and any(k in raw_name for k in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]):
            # Clean name
            raw_name = re.sub(r"^(อาจารย์|คณาจารย์)\s*", "", raw_name).strip()
            results.append({
                "university_th": "มหาวิทยาลัยขอนแก่น",
                "university": "Khon Kaen University",
                "faculty_th": "คณะเทคโนโลยี",
                "faculty": "Faculty of Technology",
                "department_th": current_dept,
                "department": "Faculty of Technology",
                "raw_name_th": raw_name,
                "email": email,
                "image_url": img_src or None,
                "profile_url": url,
            })

    print(f"    ✅ Extracted {len(results)} faculty members from KKU Tech")
    return results


def crawl_kmutnb_business(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTNB Faculty of Business Administration (Rayong) official directory."""
    print("  [2/5] Fetching KMUTNB Faculty of Business Administration...", flush=True)
    url = "https://fba.kmutnb.ac.th/main/%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c%e0%b8%9b%e0%b8%a3%e0%b8%b0%e0%b8%88%e0%b8%b3%e0%b8%ab%e0%b8%a5%e0%b8%b1%e0%b8%81%e0%b8%aa%e0%b8%b9%e0%b8%95%e0%b8%a3/"
    resp = client.get(url, timeout=30.0)
    if resp.status_code != 200:
        print(f"    ❌ Failed to fetch KMUTNB FBA (Status: {resp.status_code})")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    lines = [l.strip() for l in soup.get_text(separator="\n").split("\n") if l.strip()]

    results = []
    seen_names = set()

    for line in lines:
        # Match lines like "1. ศาสตราจารย์ ดร.ธานินทร์ ศิลป์จารุ" or "ผศ.ดร.อนุชา ถาพยอม"
        cleaned_line = re.sub(r"^\d+\.\s*", "", line).strip()
        if any(cleaned_line.startswith(p) for p in [
            "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ดร.", "ศ.", "รศ.", "ผศ.", "อ.",
            "ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์"
        ]):
            if "ประจำหลักสูตร" not in cleaned_line and len(cleaned_line) < 60 and len(cleaned_line) > 5:
                # Check for military rank like "รองศาสตราจารย์ เรือโท ดร.ทวีศักดิ์ รูปสิงห์"
                norm_th = cleaned_line
                if norm_th not in seen_names:
                    seen_names.add(norm_th)
                    results.append({
                        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
                        "university": "King Mongkut's University of Technology North Bangkok",
                        "faculty_th": "คณะบริหารธุรกิจ",
                        "faculty": "Faculty of Business Administration",
                        "department_th": "ภาควิชาบริหารธุรกิจอุตสาหกรรม",
                        "department": "Department of Industrial Business Administration",
                        "raw_name_th": norm_th,
                        "email": None,
                        "image_url": None,
                        "profile_url": url,
                    })

    print(f"    ✅ Extracted {len(results)} faculty members from KMUTNB FBA")
    return results


def crawl_kmutt_sola(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls KMUTT School of Liberal Arts official department directories."""
    print("  [3/5] Fetching KMUTT School of Liberal Arts...", flush=True)
    results = []
    seen_names = set()

    dept_urls = [
        ("https://sola.pr.kmutt.ac.th/home/lng_en/", "สายวิชาภาษา", "Department of Language Studies"),
        ("https://sola.pr.kmutt.ac.th/home/ssc_en/", "สายวิชาสังคมศาสตร์และมนุษยศาสตร์", "Department of Social Sciences and Humanities"),
    ]

    for url, dept_th, dept_en in dept_urls:
        try:
            resp = client.get(url, timeout=30.0)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            titles = soup.find_all(class_=re.compile(r"kt-blocks-info-box-title|kt-info-box"))
            for t in titles:
                name_raw = t.get_text().strip()
                if not name_raw or len(name_raw) < 4 or len(name_raw) > 60:
                    continue
                if name_raw not in seen_names:
                    seen_names.add(name_raw)
                    # Extract photo from parent block if available
                    box = t.find_parent("div", class_=re.compile(r"kt-info-box|wp-block-kadence-infobox"))
                    img = box.find("img") if box else None
                    img_src = img.get("src") if img else None

                    results.append({
                        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                        "university": "King Mongkut's University of Technology Thonburi",
                        "faculty_th": "คณะศิลปศาสตร์",
                        "faculty": "School of Liberal Arts",
                        "department_th": dept_th,
                        "department": dept_en,
                        "raw_name_th": name_raw,
                        "email": None,
                        "image_url": img_src,
                        "profile_url": url,
                    })
        except Exception as e:
            print(f"    ⚠️ Warning fetching KMUTT SoLA ({url}): {e}")

    # Also grab Thai names from main Thai lecturer page
    th_url = "https://sola.pr.kmutt.ac.th/homesola/index.php/lecturer/"
    try:
        resp = client.get(th_url, timeout=30.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for s in soup(["script", "style", "noscript"]):
                s.decompose()
            lines = [l.strip() for l in soup.get_text(separator="\n").split("\n") if l.strip()]
            for l in lines:
                if any(l.startswith(p) for p in ["ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "อ.ดร.", "ดร."]) and len(l) < 50:
                    cleaned_th = re.sub(r"\s+", " ", l).strip()
                    if cleaned_th not in seen_names:
                        seen_names.add(cleaned_th)
                        results.append({
                            "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                            "university": "King Mongkut's University of Technology Thonburi",
                            "faculty_th": "คณะศิลปศาสตร์",
                            "faculty": "School of Liberal Arts",
                            "department_th": "สายวิชาภาษา",
                            "department": "Department of Language Studies",
                            "raw_name_th": cleaned_th,
                            "email": None,
                            "image_url": None,
                            "profile_url": th_url,
                        })
    except Exception as e:
        print(f"    ⚠️ Warning fetching KMUTT SoLA Thai ({th_url}): {e}")

    print(f"    ✅ Extracted {len(results)} faculty members from KMUTT SoLA")
    return results


def crawl_psu_nursing(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls PSU Faculty of Nursing official staff directory."""
    print("  [4/5] Fetching PSU Faculty of Nursing...", flush=True)
    url = "https://www.nur.psu.ac.th/nur/teacher.aspx"
    resp = client.get(url, timeout=35.0)
    if resp.status_code != 200:
        print(f"    ❌ Failed to fetch PSU Nurse (Status: {resp.status_code})")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    seen_names = set()

    for row in soup.find_all("tr"):
        th_a = row.find("a", id=re.compile(r"LinkButton1"))
        en_a = row.find("a", id=re.compile(r"LinkButton2"))
        if th_a and en_a:
            th_name = th_a.get_text().strip()
            en_name = en_a.get_text().strip()
            if not th_name or th_name in seen_names:
                continue
            seen_names.add(th_name)

            img = row.find("img")
            img_src = img.get("src") if img else None
            if img_src and not img_src.startswith("http"):
                img_src = urllib.parse.urljoin("https://www.nur.psu.ac.th/nur/", img_src)

            emails = re.findall(r"[a-zA-Z0-9._%+-]+@psu\.ac\.th", row.text)
            email = emails[0].lower() if emails else None

            # Extract department
            dept_th = "สาขาวิชาพยาบาลศาสตร์"
            dept_matches = re.findall(r"(สาขาวิชา[^\n\r<]+)", row.text)
            if dept_matches:
                dept_th = dept_matches[0].strip()

            results.append({
                "university_th": "มหาวิทยาลัยสงขลานครินทร์",
                "university": "Prince of Songkla University",
                "faculty_th": "คณะพยาบาลศาสตร์",
                "faculty": "Faculty of Nursing",
                "department_th": dept_th,
                "department": "Faculty of Nursing",
                "raw_name_th": th_name,
                "name_en": en_name,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
            })

    print(f"    ✅ Extracted {len(results)} faculty members from PSU Nursing")
    return results


def crawl_tu_sgs(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls Thammasat University School of Global Studies (SGS) official faculty directory."""
    print("  [5/5] Fetching TU School of Global Studies...", flush=True)
    url = "https://sgs.tu.ac.th/faculty/"
    resp = client.get(url, timeout=30.0)
    if resp.status_code != 200:
        print(f"    ❌ Failed to fetch TU SGS (Status: {resp.status_code})")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    seen_names = set()

    for col in soup.find_all("div", class_=re.compile(r"elementor-widget-wrap")):
        mailto = col.find("a", href=re.compile(r"^mailto:", re.I))
        if mailto:
            name_h = col.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            img = col.find("img")
            img_src = img.get("src") if img else None
            email = mailto["href"].replace("mailto:", "").strip().lower()

            if name_h:
                raw_name = name_h.get_text().strip()
                if raw_name in ["FACULTY MEMBER", "FACULTY", "ABOUT US"]:
                    continue
                if raw_name and raw_name not in seen_names:
                    seen_names.add(raw_name)
                    results.append({
                        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                        "university": "Thammasat University",
                        "faculty_th": "วิทยาลัยโลกคดีศึกษา",
                        "faculty": "School of Global Studies",
                        "department_th": "สาขาวิชาการพัฒนานวัตกรรมและโลกคดีศึกษา",
                        "department": "School of Global Studies",
                        "raw_name_th": raw_name,
                        "email": email,
                        "image_url": img_src,
                        "profile_url": url,
                    })

    print(f"    ✅ Extracted {len(results)} faculty members from TU SGS")
    return results


# =====================================================================
# 2. Normalization & OpenAlex Enrichment
# =====================================================================

def enrich_faculty_with_openalex(faculty: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex to retrieve bibliometrics, citations, h-index, and OpenAlex author ID."""
    name_to_search = faculty.get("name_en") or faculty.get("raw_name_th") or ""
    # Strip titles from name for search
    clean_search = re.sub(
        r"^(Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*",
        "",
        name_to_search,
        flags=re.IGNORECASE
    ).strip()

    # If Thai name only, OpenAlex text search won't match well without English
    if not re.search(r"[a-zA-Z]{3,}", clean_search):
        # Leave as un-indexed for now to avoid false homonym matches
        faculty["openalex_id"] = "not_indexed"
        faculty["total_citations"] = 0
        faculty["h_index"] = 0
        faculty["total_publications_count"] = 0
        faculty["featured_publications"] = []
        return faculty

    # Query OpenAlex API
    q = urllib.parse.quote(clean_search)
    api_url = f"https://api.openalex.org/authors?search={q}&per-page=3"
    data = fetch_with_retry(api_url, max_retries=3)
    results = (data or {}).get("results", []) or []

    if results:
        # Check institution corroboration
        uni_str = faculty.get("university", "")
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
            # Monotonicity check
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
# 3. Database Ingestion Engine
# =====================================================================

def generate_canonical_id(univ_code: str, faculty_code: str, name: str, idx: int) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "", name.lower())[:15]
    return f"{univ_code}_{faculty_code}_{slug}_{idx:03d}"


def run_pipeline():
    print("=================================================================", flush=True)
    print("🚀 EXECUTING WAVE 60: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
    print("=================================================================", flush=True)
    t0 = time.time()

    client = httpx.Client(verify=False, timeout=35.0, follow_redirects=True, headers=CLIENT_HEADERS)
    db = SessionLocal()

    try:
        # Step 1: Crawl the 5 target faculties
        all_raw_faculty = []
        all_raw_faculty.extend(crawl_kku_technology(client))
        all_raw_faculty.extend(crawl_kmutnb_business(client))
        all_raw_faculty.extend(crawl_kmutt_sola(client))
        all_raw_faculty.extend(crawl_psu_nursing(client))
        all_raw_faculty.extend(crawl_tu_sgs(client))

        print(f"\n📊 Total Raw Faculty Harvested: {len(all_raw_faculty)}")

        # Step 2: Normalize names & academic titles
        print("\n⚙️ Normalizing Names and Academic Titles...", flush=True)
        normalized_faculty = []
        for i, item in enumerate(all_raw_faculty, 1):
            raw_n = item.get("raw_name_th") or ""
            # If English title (Dr., Prof., Asst. Prof., etc.)
            title_th, full_th, base_n = normalize_thai_title_and_name(raw_n)

            # English name fallback
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

        # Step 3: OpenAlex Multiplexing & Metric Enrichment
        print("\n📚 Enriching with OpenAlex Metrics (Pillar 2)...", flush=True)
        enriched_faculty = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_fac = {executor.submit(enrich_faculty_with_openalex, f): f for f in normalized_faculty}
            for fut in as_completed(future_to_fac):
                try:
                    res = fut.result()
                    enriched_faculty.append(res)
                except Exception as e:
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
        # Prefetch existing faculties for fast in-memory deduplication
        existing_names = set(
            n for (n,) in db.query(FacultyDB.full_name_th).filter(FacultyDB.full_name_th.isnot(None)).all()
        )
        existing_emails = set(
            em.lower() for (em,) in db.query(FacultyDB.email).filter(FacultyDB.email.isnot(None), FacultyDB.email != "").all()
        )

        univ_prefix_map = {
            "มหาวิทยาลัยขอนแก่น": ("kku", "tech"),
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": ("kmutnb", "fba"),
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ("kmutt", "sola"),
            "มหาวิทยาลัยสงขลานครินทร์": ("psu", "nur"),
            "มหาวิทยาลัยธรรมศาสตร์": ("tu", "sgs"),
        }

        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, item in enumerate(enriched_faculty, 1):
            full_th = item.get("full_name_th") or ""
            email = (item.get("email") or "").lower().strip() or None
            univ_th = item.get("university_th")

            # Check duplication by email or exact name
            existing_f = None
            if email and email in existing_emails:
                existing_f = db.query(FacultyDB).filter(FacultyDB.email == email).first()
            elif full_th and full_th in existing_names:
                existing_f = db.query(FacultyDB).filter(FacultyDB.full_name_th == full_th).first()

            if existing_f:
                # Update missing fields only
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
                # Generate canonical ID
                u_code, f_code = univ_prefix_map.get(univ_th, ("univ", "fac"))
                new_id = generate_canonical_id(u_code, f_code, item.get("first_name") or full_th, idx)

                # Ensure ID uniqueness
                while db.query(FacultyDB.id).filter(FacultyDB.id == new_id).first():
                    new_id = f"{new_id}_x"

                # Bibliometric Monotonicity Invariant: total_publications_count >= h_index
                h_idx = item.get("h_index", 0) or 0
                pubs_count = max(item.get("total_publications_count", 0) or 0, h_idx)

                new_record = FacultyDB(
                    id=new_id,
                    university=item.get("university"),
                    university_th=item.get("university_th"),
                    faculty=item.get("faculty"),
                    faculty_th=item.get("faculty_th"),
                    department=item.get("department"),
                    department_th=item.get("department_th"),
                    academic_title_th=item.get("title_th"),
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    full_name_th=full_th,
                    email=email,
                    image_url=item.get("image_url"),
                    profile_url=item.get("profile_url"),
                    education=[],
                    research_interests=[],
                    taught_courses=[],
                    featured_publications=item.get("featured_publications", []),
                    total_publications_count=pubs_count,
                    first_author_count=0,
                    co_author_count=0,
                    total_citations=item.get("total_citations", 0) or 0,
                    h_index=h_idx,
                    openalex_id=item.get("openalex_id"),
                    scholar_url=item.get("scholar_url"),
                    embedding_text=f"{full_th} {item.get('faculty_th')} {item.get('department_th')} {item.get('university_th')}",
                    embedding=None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search,  # Non-blocking circuit breaker fallback
                )
                db.add(new_record)
                if email:
                    existing_emails.add(email)
                if full_th:
                    existing_names.add(full_th)
                inserted_count += 1

        db.commit()
        print(f"  ✅ Database Commit Completed:")
        print(f"     - Inserted new authentic faculty: {inserted_count}")
        print(f"     - Updated existing records:      {updated_count}")
        print(f"     - Skipped duplicate records:      {skipped_count}")

    finally:
        client.close()
        db.close()

    print(f"\n🎉 Wave 60 Completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_pipeline()
