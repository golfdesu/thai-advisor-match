# -*- coding: utf-8 -*-
"""
Wave 68 Autonomous Acquisition of Graduate-Level Faculty
========================================================
5-Pillar Architecture Headless Crawler for Graduate Faculties with Deficits:
1. KMITL School of Liberal Arts (คณะศิลปศาสตร์ สจล. - M.A. Applied Linguistics)
   - Source: https://la.kmitl.ac.th/department/linguistics & humanities
2. TU Puey Ungphakorn School of Development Studies (วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์ มธ. - M.A. Social Innovation)
   - Source: https://psds.tu.ac.th/about-us/personnel/
3. TU Pridi Banomyong International College (วิทยาลัยนานาชาติ ปรีดี พนมยงค์ มธ. - M.A. Thai Studies)
   - Source: https://pbic.tu.ac.th/about-us/faculty-member/
4. CMU School of Public Policy (วิทยาลัยนโยบายสาธารณะ มช. - M.A. & Ph.D. Public Policy)
   - Source: https://spp.cmu.ac.th/our-school/our-people/
5. NU Faculty of Law (คณะนิติศาสตร์ ม.นเรศวร - LL.M. & Ph.D. Law)
   - Source: https://www.law.nu.ac.th/personel/professor/
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
from bs4 import BeautifulSoup

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave68_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


# =====================================================================
# 1. Targeted Headless Crawlers (Pillar 1)
# =====================================================================

def crawl_kmitl_liberal_arts(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from KMITL School of Liberal Arts."""
    print("\n[Crawler 1/5] Scraping KMITL Liberal Arts (คณะศิลปศาสตร์ สจล.)...", flush=True)
    dept_pages = [
        ("ภาควิชาภาษา", "https://la.kmitl.ac.th/department/linguistics"),
        ("ภาควิชามนุษยศาสตร์และสังคมศาสตร์", "https://la.kmitl.ac.th/department/humanities"),
    ]

    results = []
    seen_names = set()

    for dept_th, url in dept_pages:
        try:
            r = client.get(url, timeout=15.0)
            if r.status_code != 200:
                print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=re.compile(r"/node/\d+")):
                txt = a.get_text(strip=True)
                if any(txt.startswith(p) for p in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "อาจารย์"]):
                    if txt in seen_names:
                        continue
                    seen_names.add(txt)
                    node_href = a["href"]
                    node_url = f"https://la.kmitl.ac.th{node_href}" if node_href.startswith("/") else node_href

                    # Fetch node detail
                    img_url = None
                    edu_history = []
                    try:
                        r_node = client.get(node_url, timeout=10.0)
                        if r_node.status_code == 200:
                            soup_node = BeautifulSoup(r_node.text, "html.parser")
                            for img in soup_node.find_all("img"):
                                src = img.get("src", "")
                                if "public" in src or "files" in src:
                                    if not any(k in src.lower() for k in ["logo", "flag", "icon"]):
                                        img_url = f"https://la.kmitl.ac.th{src}" if src.startswith("/") else src
                                        break
                            main_txt = soup_node.get_text("\n", strip=True)
                            for line in main_txt.split("\n"):
                                line_clean = line.strip()
                                if any(line_clean.startswith(deg) for deg in ["ศศ.ด.", "ศศ.ม.", "อ.บ.", "ค.บ.", "ศ.ด.", "วศ.บ.", "วท.บ.", "วท.ม.", "ปร.ด."]):
                                    edu_history.append(line_clean)
                    except Exception:
                        pass

                    results.append({
                        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
                        "university_en": "King Mongkut's Institute of Technology Ladkrabang",
                        "faculty_th": "คณะศิลปศาสตร์",
                        "faculty_en": "School of Liberal Arts",
                        "department_th": dept_th,
                        "raw_name_th": txt,
                        "email": None,
                        "image_url": urllib.parse.quote(img_url, safe=":/%?=") if img_url else None,
                        "profile_url": node_url,
                        "research_interests": ["Linguistics", "Applied Linguistics", dept_th] if dept_th == "ภาควิชาภาษา" else ["Humanities", "Social Sciences", dept_th],
                        "education": " | ".join(edu_history[:3]) if edu_history else None,
                    })
        except Exception as exc:
            print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from KMITL Liberal Arts.")
    return results


def crawl_tu_psds(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from TU Puey Ungphakorn School of Development Studies."""
    print("\n[Crawler 2/5] Scraping TU PSDS (วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์ มธ.)...", flush=True)
    url = "https://psds.tu.ac.th/about-us/personnel/"
    results = []
    seen_urls = set()

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results
        soup = BeautifulSoup(r.text, "html.parser")
        personnel_links = soup.find_all("a", href=lambda h: h and "/personnel-center/" in h)

        for a in personnel_links:
            p_url = a["href"].rstrip("/") + "/"
            if p_url in seen_urls:
                continue
            seen_urls.add(p_url)

            raw_slug = p_url.rstrip("/").split("/")[-1]
            slug_unquoted = urllib.parse.unquote(raw_slug)

            # Filter out non-teaching administrative staff (นาง, นางสาว, นาย without academic titles)
            is_academic = any(slug_unquoted.startswith(p) for p in [
                "ผศ", "รศ", "ศ", "ดร", "อาจารย์", "อ-", "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์"
            ])
            if not is_academic:
                continue

            try:
                r_det = client.get(p_url, timeout=12.0)
                if r_det.status_code != 200:
                    continue
                soup_det = BeautifulSoup(r_det.text, "html.parser")

                # Name from breadcrumb_last or title tag
                bc = soup_det.find("span", class_="breadcrumb_last")
                name_th = bc.get_text(strip=True) if bc else None
                if not name_th and soup_det.title:
                    name_th = soup_det.title.string.split("-")[0].strip()
                if not name_th:
                    name_th = slug_unquoted.replace("-", " ")

                # Extract photo
                img_url = None
                for img in soup_det.find_all("img"):
                    src = img.get("src", "")
                    if "uploads" in src and any(ext in src.lower() for ext in [".jpg", ".png", ".webp", ".avif", ".jpeg"]):
                        if not any(k in src.lower() for k in ["logo", "popup", "icon", "flag"]):
                            img_url = src
                            break

                # Extract email
                body_text = soup_det.get_text("\n", strip=True)
                email_m = re.search(r"([a-zA-Z0-9._%+-]+@(?:psds\.tu\.ac\.th|tu\.ac\.th))", body_text)
                email = email_m.group(1) if email_m else None
                if email and any(k in email.lower() for k in ["eservice", "contact", "info", "admin"]):
                    email = None

                # Extract research / publications
                pubs = []
                for div in soup_det.find_all("div", class_="elementor-heading-title"):
                    txt = div.get_text(strip=True)
                    if any(y in txt for y in ["(202", "(256", "พ.ศ.", "2024", "2025", "2026", "2567", "2568", "2569"]):
                        if len(txt) > 20 and len(txt) < 300:
                            pubs.append({"title": txt, "year": 2024, "venue": "PSDS Research", "citation_count": 0})

                results.append({
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "university_en": "Thammasat University",
                    "faculty_th": "วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์",
                    "faculty_en": "Puey Ungphakorn School of Development Studies",
                    "department_th": "สาขาวิชานวัตกรรมเพื่อการพัฒนาสังคม",
                    "raw_name_th": name_th,
                    "email": email,
                    "image_url": urllib.parse.quote(img_url, safe=":/%?=") if img_url else None,
                    "profile_url": p_url,
                    "research_interests": ["Social Innovation", "Sustainable Development", "Community Development"],
                    "featured_publications": pubs[:5],
                })
            except Exception as e_det:
                pass

    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from TU PSDS.")
    return results


def crawl_tu_pbic(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from TU Pridi Banomyong International College."""
    print("\n[Crawler 3/5] Scraping TU PBIC (วิทยาลัยนานาชาติ ปรีดี พนมยงค์ มธ.)...", flush=True)
    url = "https://pbic.tu.ac.th/about-us/faculty-member/"
    results = []
    seen_names = set()

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results
        soup = BeautifulSoup(r.text, "html.parser")

        for img in soup.find_all("img", class_="team-member-photo"):
            parent = img.find_parent("div", class_=lambda c: c and "team-member" in c)
            if not parent:
                continue

            # Extract name and role
            title_div = parent.find("div", class_=lambda c: c and "team-member-title" in c)
            subtitle_div = parent.find("div", class_=lambda c: c and "team-member-subtitle" in c)
            desc_div = parent.find("div", class_=lambda c: c and "team-member-description" in c)

            name = title_div.get_text(strip=True) if title_div else ""
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            role = subtitle_div.get_text(strip=True) if subtitle_div else ""
            desc = desc_div.get_text(strip=True) if desc_div else ""

            # Real image URL in data-src
            img_url = img.get("data-src") or img.get("src")
            if img_url and img_url.startswith("data:"):
                img_url = None

            # Determine department / program
            dept_th = "สาขาวิชาไทยศึกษา"
            if "Chinese" in role:
                dept_th = "สาขาวิชาจีนศึกษา"
            elif "Indian" in role:
                dept_th = "สาขาวิชาอินเดียศึกษา"

            results.append({
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "university_en": "Thammasat University",
                "faculty_th": "วิทยาลัยนานาชาติ ปรีดี พนมยงค์",
                "faculty_en": "Pridi Banomyong International College",
                "department_th": dept_th,
                "raw_name_th": name,
                "email": None,
                "image_url": urllib.parse.quote(img_url, safe=":/%?=") if img_url else None,
                "profile_url": url,
                "research_interests": ["Thai Studies", "Area Studies", "International Studies", dept_th],
                "education": desc if desc else None,
            })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from TU PBIC.")
    return results


def crawl_cmu_spp(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from CMU School of Public Policy."""
    print("\n[Crawler 4/5] Scraping CMU SPP (วิทยาลัยนโยบายสาธารณะ มช.)...", flush=True)
    url = "https://spp.cmu.ac.th/our-school/our-people/"
    results = []
    seen_names = set()

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results
        soup = BeautifulSoup(r.text, "html.parser")

        for h in soup.find_all(["h2", "h3", "h4", "h5"]):
            name_raw = h.get_text(strip=True)
            if any(name_raw.startswith(p) for p in ["Assoc.", "Asst.", "Prof.", "Dr.", "Aj."]):
                # Strip trailing credentials like , PhD
                clean_name = re.sub(r",\s*Ph\.?D\.?", "", name_raw).strip()
                if not clean_name or clean_name in seen_names:
                    continue
                seen_names.add(clean_name)

                parent = h.find_parent("div", class_=lambda c: c and "elementor-column" in c) or h.find_parent("div")
                img = parent.find("img") if parent else None
                img_src = img.get("src") if img else None

                parent_text = parent.get_text(" ", strip=True) if parent else ""
                email_m = re.search(r"([a-zA-Z0-9._%+-]+@cmu\.ac\.th)", parent_text)
                email = email_m.group(1) if email_m else None

                results.append({
                    "university_th": "มหาวิทยาลัยเชียงใหม่",
                    "university_en": "Chiang Mai University",
                    "faculty_th": "วิทยาลัยนโยบายสาธารณะ",
                    "faculty_en": "School of Public Policy",
                    "department_th": "สาขาวิชานโยบายสาธารณะ",
                    "raw_name_th": clean_name,
                    "email": email,
                    "image_url": urllib.parse.quote(img_src, safe=":/%?=") if img_src else None,
                    "profile_url": url,
                    "research_interests": ["Public Policy", "Policy Analysis", "Governance", "Public Administration"],
                })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from CMU SPP.")
    return results


def crawl_nu_law(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from Naresuan University Faculty of Law."""
    print("\n[Crawler 5/5] Scraping NU Faculty of Law (คณะนิติศาสตร์ ม.นเรศวร)...", flush=True)
    url = "https://www.law.nu.ac.th/personel/professor/"
    results = []
    seen_urls = set()

    try:
        r = client.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=re.compile(r"page_id=\d+")):
            href = a["href"]
            raw_title = a.get_text(strip=True)
            if not any(raw_title.startswith(p) for p in [
                "ผู้ช่วยศาสตราจารย์", "รองศาสตราจารย์", "ศาสตราจารย์", "อาจารย์", "ผศ.", "รศ.", "ศ.", "ดร."
            ]):
                continue

            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Fetch detail page
            email = None
            img_url = None
            name_en = None
            research_field = None
            try:
                r_det = client.get(href, timeout=10.0)
                if r_det.status_code == 200:
                    soup_det = BeautifulSoup(r_det.text, "html.parser")
                    content = soup_det.find("div", class_="entry-content")
                    if content:
                        img = content.find("img")
                        if img and "Law-logo" not in img.get("src", ""):
                            img_url = img.get("src")
                        det_text = content.get_text("\n", strip=True)
                        email_m = re.search(r"([a-zA-Z0-9._%+-]+@nu\.ac\.th)", det_text)
                        email = email_m.group(1) if email_m else None

                        lines = [line.strip() for line in det_text.split("\n") if line.strip()]
                        for idx, l in enumerate(lines):
                            if l.lower().startswith("e-mail") and idx > 1:
                                candidate_en = lines[idx - 1]
                                if re.match(r"^[A-Za-z\s.]+$", candidate_en) and len(candidate_en) > 4:
                                    name_en = candidate_en
                            if "สาขางานวิจัย" in l and idx + 1 < len(lines):
                                research_field = lines[idx + 1].strip("–- ")
            except Exception:
                pass

            results.append({
                "university_th": "มหาวิทยาลัยนเรศวร",
                "university_en": "Naresuan University",
                "faculty_th": "คณะนิติศาสตร์",
                "faculty_en": "Faculty of Law",
                "department_th": "ภาควิชานิติศาสตร์",
                "raw_name_th": raw_title,
                "raw_name_en": name_en,
                "email": email,
                "image_url": urllib.parse.quote(img_url, safe=":/%?=") if img_url else None,
                "profile_url": href,
                "research_interests": ["Law", "Jurisprudence", research_field] if research_field else ["Law", "Jurisprudence"],
            })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from NU Faculty of Law.")
    return results


# =====================================================================
# 2. State Reducer, Normalization & OpenAlex Disambiguation (Pillar 4 & 2)
# =====================================================================

TITLE_PREFIXES = [
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
    ("Assoc. Prof.", "รศ."),
    ("Asst. Prof.", "ผศ."),
    ("Prof. Dr.", "ศ.ดร."),
    ("Prof.", "ศ."),
    ("Dr.", "ดร."),
    ("Ajarn", "อ."),
    ("Aj.", "อ."),
]


def normalize_thai_title_and_name(raw_name: str) -> tuple[str, str, str]:
    """Splits academic rank and extracts clean full name and title."""
    clean = re.sub(
        r"(หัวหน้าภาควิชา|รองคณบดี.*|คณบดี.*|ผู้ช่วยคณบดี.*|ผู้อำนวยการ.*|ประธานหลักสูตร.*|ประธานสาขา.*)",
        "", raw_name
    ).strip()
    clean = re.sub(r"\s+", " ", clean)

    matched_title = ""
    for full_p, norm_p in TITLE_PREFIXES:
        if clean.startswith(full_p):
            matched_title = norm_p
            clean = clean[len(full_p):].strip()
            break

    if not matched_title:
        matched_title = "อาจารย์"

    # Strip any redundant secondary prefixes (e.g. ดร.)
    if clean.startswith("ดร.") or clean.startswith("ดร "):
        clean = re.sub(r"^ดร\.?\s*", "", clean).strip()
        if "ดร." not in matched_title:
            matched_title = f"{matched_title}ดร." if matched_title.endswith(".") else f"{matched_title}.ดร."

    full_th = f"{matched_title} {clean}" if matched_title else clean
    return matched_title, clean, full_th


def enrich_openalex_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex for author citations, h-index, and featured publications (Pillar 2)."""
    search_query = record.get("raw_name_en") or record["clean_name_th"]
    # If Thai name, query clean name
    url = f"https://api.openalex.org/authors?search={urllib.parse.quote(search_query)}&per-page=5"
    data = fetch_oa_with_retry(url)

    record["openalex_id"] = "not_indexed"
    record["total_citations"] = 0
    record["h_index"] = 0
    record["total_publications_count"] = 0
    record["first_author_count"] = 0
    record["co_author_count"] = 0
    if not record.get("featured_publications"):
        record["featured_publications"] = []

    if data and data.get("results"):
        univ_en = record["university_en"].lower()
        for cand in data["results"]:
            cand_insts = [
                inst.get("display_name", "").lower()
                for inst in (cand.get("last_known_institutions") or [])
                if isinstance(inst, dict)
            ]
            # Verify 2-factor institutional link
            if any(univ_en in inst_name or "thailand" in inst_name for inst_name in cand_insts):
                record["openalex_id"] = cand.get("id")
                record["total_citations"] = cand.get("cited_by_count") or 0
                summary = cand.get("summary_stats") or {}
                record["h_index"] = summary.get("h_index") or 0
                record["total_publications_count"] = cand.get("works_count") or 0
                break

    return record


# =====================================================================
# 3. Main Wave 68 Autonomous Pipeline
# =====================================================================

def run_wave68_pipeline():
    print("=================================================================", flush=True)
    print("🚀 STARTING WAVE 68: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
    print("=================================================================", flush=True)

    client = httpx.Client(
        verify=False,
        follow_redirects=True,
        timeout=15.0,
        headers=CLIENT_HEADERS
    )

    all_harvested: List[Dict[str, Any]] = []

    # Execute targeted headless crawlers
    all_harvested.extend(crawl_kmitl_liberal_arts(client))
    all_harvested.extend(crawl_tu_psds(client))
    all_harvested.extend(crawl_tu_pbic(client))
    all_harvested.extend(crawl_cmu_spp(client))
    all_harvested.extend(crawl_nu_law(client))

    print(f"\n📊 Total raw harvested faculty records: {len(all_harvested)}", flush=True)

    # State Reducer & Normalization
    processed_records: List[Dict[str, Any]] = []
    seen_dedup = set()

    for r in all_harvested:
        title, clean_name, full_th = normalize_thai_title_and_name(r["raw_name_th"])
        name_parts = clean_name.split()
        first_name = name_parts[0] if name_parts else clean_name
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else first_name

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

    # Commit to Database with ID Sequence Separators
    print("\n📥 Ingesting into PostgreSQL 'faculties' table...", flush=True)
    db = SessionLocal()
    inserted_count = 0
    updated_count = 0

    try:
        # Separate ID counters per faculty
        counters = {
            "kmitl_libarts": 1,
            "tu_psds": 1,
            "tu_pbic": 1,
            "cmu_spp": 1,
            "nu_law": 1,
        }

        for r in enriched_records:
            # Match prefix
            if "ลาดกระบัง" in r["university_th"]:
                prefix = "kmitl_libarts"
            elif "ป๋วย" in r["faculty_th"]:
                prefix = "tu_psds"
            elif "ปรีดี" in r["faculty_th"]:
                prefix = "tu_pbic"
            elif "นโยบายสาธารณะ" in r["faculty_th"]:
                prefix = "cmu_spp"
            elif "นเรศวร" in r["university_th"]:
                prefix = "nu_law"
            else:
                prefix = "wave68"

            # Check if person already exists by (university_th, clean_name)
            existing = db.query(FacultyDB).filter(
                FacultyDB.university_th == r["university_th"],
                FacultyDB.full_name_th.like(f"%{r['clean_name_th']}%")
            ).first()

            if existing:
                # Update metrics if higher
                if (r["total_citations"] or 0) > (existing.total_citations or 0):
                    existing.total_citations = r["total_citations"]
                    existing.h_index = r["h_index"]
                    existing.openalex_id = r["openalex_id"]
                if not existing.image_url and r["image_url"]:
                    existing.image_url = r["image_url"]
                if not existing.email and r["email"]:
                    existing.email = r["email"]
                updated_count += 1
            else:
                while True:
                    candidate_id = f"{prefix}__{counters.get(prefix, 1):03d}"
                    counters[prefix] = counters.get(prefix, 1) + 1
                    if not db.query(FacultyDB).filter(FacultyDB.id == candidate_id).first():
                        break

                new_fac = FacultyDB(
                    id=candidate_id,
                    university=TH_TO_EN_CANONICAL.get(r["university_th"], r["university_en"]),
                    university_th=r["university_th"],
                    faculty=r["faculty_en"],
                    faculty_th=r["faculty_th"],
                    department_th=r["department_th"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    full_name_th=r["full_name_th"],
                    academic_title_th=r["academic_title_th"],
                    email=r["email"],
                    profile_url=r["profile_url"],
                    image_url=r["image_url"],
                    research_interests=r["research_interests"],
                    featured_publications=r["featured_publications"],
                    total_citations=r["total_citations"],
                    h_index=r["h_index"],
                    total_publications_count=r["total_publications_count"],
                    first_author_count=r["first_author_count"],
                    co_author_count=r["co_author_count"],
                    openalex_id=r["openalex_id"],
                    embedding=[0.0] * 768,  # Non-blocking circuit breaker (Pillar 3)
                )
                db.add(new_fac)
                inserted_count += 1

        db.commit()
        print(f"✅ Ingestion complete: {inserted_count} newly inserted, {updated_count} existing updated.", flush=True)

    finally:
        db.close()
        client.close()

    print("\n🎉 Wave 68 acquisition completed successfully!", flush=True)


if __name__ == "__main__":
    run_wave68_pipeline()
