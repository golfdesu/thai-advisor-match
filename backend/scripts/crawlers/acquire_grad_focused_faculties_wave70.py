# -*- coding: utf-8 -*-
"""
Wave 70 Autonomous Acquisition of Graduate-Level Faculty
========================================================
5-Pillar Architecture Headless Crawler for Graduate Faculties with Deficits:
1. Thammasat University Faculty of Nursing (คณะพยาบาลศาสตร์ มธ. - Master of Nursing Science)
   - Source: https://nurse.tu.ac.th/th/professor
2. Thammasat University Faculty of Sociology and Anthropology (คณะสังคมวิทยาและมานุษยวิทยา มธ. - M.A. & Ph.D.)
   - Source: https://socanth.tu.ac.th/soc-staff/ & https://socanth.tu.ac.th/anthro-staff/
3. King Mongkut's University of Technology Thonburi School of Bioresources and Technology (คณะทรัพยากรชีวภาพและเทคโนโลยี มจธ. - M.Sc. & Ph.D.)
   - Source: https://sbt.kmutt.ac.th/en/faculty/
4. Chiang Mai University Faculty of Public Health (คณะสาธารณสุขศาสตร์ มช. - Master & Ph.D. Public Health)
   - Source: https://ph.cmu.ac.th/lecturer.php
"""
from __future__ import annotations

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
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry as fetch_oa_with_retry
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave70_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


# =====================================================================
# 1. Targeted Headless Crawlers (Pillar 1)
# =====================================================================

def crawl_tu_nursing(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic nursing faculty from Thammasat University Faculty of Nursing."""
    print("\n[Crawler 1/4] Scraping TU Faculty of Nursing (คณะพยาบาลศาสตร์ มธ.)...", flush=True)
    url = "https://nurse.tu.ac.th/professor"
    results = []

    try:
        r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("div", class_="block-item")
        seen_names = set()

        for it in items:
            title_div = it.find("div", class_="title")
            if not title_div:
                continue
            raw_name = title_div.get_text(strip=True)
            if not raw_name or not any(raw_name.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]):
                continue

            if raw_name in seen_names:
                continue
            seen_names.add(raw_name)

            desc = it.find("div", class_="desc")
            desc_txt = desc.get_text(" ", strip=True) if desc else ""
            em_m = re.search(r"([a-zA-Z0-9._%+-]+@nurse\.tu\.ac\.th)", desc_txt)
            email = em_m.group(1).strip() if em_m else None

            thump = it.find("div", class_="thump")
            img_url = None
            dept = "สาขาวิชาพยาบาลศาสตร์"
            if thump and thump.get("style"):
                st = thump["style"]
                m_img = re.search(r"url\((.*?)\)", st)
                if m_img:
                    raw_img = m_img.group(1).strip("'\"")
                    if raw_img and not raw_img.startswith("http"):
                        raw_img = "https://nurse.tu.ac.th" + ("/" if not raw_img.startswith("/") else "") + raw_img
                    img_url = urllib.parse.quote(raw_img, safe=":/%?=") if raw_img else None

                    if "familyMidwife" in raw_img:
                        dept = "สาขาวิชาการพยาบาลครอบครัวและการผดุงครรภ์"
                    elif "manager" in raw_img:
                        dept = "สาขาวิชาการบริหารการพยาบาล"
                    elif "adult" in raw_img:
                        dept = "สาขาวิชาการพยาบาลผู้ใหญ่และผู้สูงอายุ"
                    elif "child" in raw_img:
                        dept = "สาขาวิชาการพยาบาลเด็ก"
                    elif "psych" in raw_img:
                        dept = "สาขาวิชาการพยาบาลสุขภาพจิตและจิตเวช"
                    elif "community" in raw_img:
                        dept = "สาขาวิชาการพยาบาลอนามัยชุมชน"
                    elif "fundamental" in raw_img:
                        dept = "สาขาวิชาการพยาบาลพื้นฐาน"

            results.append({
                "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                "university_en": "Thammasat University",
                "faculty_th": "คณะพยาบาลศาสตร์",
                "faculty_en": "Faculty of Nursing",
                "department_th": dept,
                "raw_name_th": raw_name,
                "raw_name_en": None,
                "email": email,
                "image_url": img_url,
                "profile_url": url,
                "research_interests": ["Nursing Science", "Clinical Nursing", "Community Health", "Healthcare Administration"],
            })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from TU Faculty of Nursing.")
    return results


def crawl_tu_socanth(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic sociology & anthropology faculty from Thammasat University."""
    print("\n[Crawler 2/4] Scraping TU Faculty of Sociology and Anthropology (คณะสังคมวิทยาและมานุษยวิทยา มธ.)...", flush=True)
    configs = [
        ("https://socanth.tu.ac.th/soc-staff/", "สาขาวิชาสังคมวิทยา", "Department of Sociology", ["Sociology", "Social Theory", "Urban Studies", "Gender Studies"]),
        ("https://socanth.tu.ac.th/anthro-staff/", "สาขาวิชามานุษยวิทยา", "Department of Anthropology", ["Anthropology", "Cultural Anthropology", "Ethnography", "Medical Anthropology"])
    ]
    results = []

    for url, dept_th, dept_en, default_interests in configs:
        try:
            r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
            if r.status_code != 200:
                print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            h3s = soup.find_all("h3")
            seen_names = set()

            for h3 in h3s:
                name = h3.get_text(strip=True)
                if not name or name == "อาจารย์" or not any(p in name for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]):
                    continue
                name_clean = re.sub(r"\(.*?\)", "", name).strip()
                if name_clean in seen_names or len(name_clean) < 4:
                    continue
                seen_names.add(name_clean)

                # Siblings extraction
                interests = []
                email = None

                curr = h3.next_sibling
                count = 0
                while curr and count < 8:
                    if getattr(curr, "name", None) == "p":
                        txt = curr.get_text(" ", strip=True)
                        if "@tu.ac.th" in txt:
                            em_m = re.search(r"([a-zA-Z0-9._%+-]+@tu\.ac\.th)", txt)
                            if em_m:
                                email = em_m.group(1).strip()
                        elif "ความสนใจทางวิชาการ:" in txt or "ความสนใจ:" in txt:
                            raw_int = re.sub(r"ความสนใจ(?:ทางวิชาการ)?:\s*", "", txt).strip()
                            interests = [x.strip() for x in re.split(r"[,;•/]+", raw_int) if len(x.strip()) > 1]
                        count += 1
                    elif getattr(curr, "name", None) in ["h2", "h3"]:
                        break
                    curr = curr.next_sibling

                results.append({
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "university_en": "Thammasat University",
                    "faculty_th": "คณะสังคมวิทยาและมานุษยวิทยา",
                    "faculty_en": "Faculty of Sociology and Anthropology",
                    "department_th": dept_th,
                    "raw_name_th": name_clean,
                    "raw_name_en": None,
                    "email": email,
                    "image_url": None,
                    "profile_url": url,
                    "research_interests": interests if interests else default_interests,
                })
        except Exception as exc:
            print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from TU Faculty of Sociology and Anthropology.")
    return results


def crawl_kmutt_sbt(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic bioresources & biotechnology faculty from KMUTT SBT."""
    print("\n[Crawler 3/4] Scraping KMUTT School of Bioresources and Technology (คณะทรัพยากรชีวภาพและเทคโนโลยี มจธ.)...", flush=True)
    url = "https://sbt.kmutt.ac.th/en/faculty/"
    results = []

    try:
        r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        matches = soup.find_all(string=lambda t: t and "email :" in t)
        seen_emails = set()

        for m in matches:
            raw_str = str(m).strip()
            # Extract email
            raw_email = raw_str.split(":")[-1].strip()
            em_m = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]*kmutt\.ac\.th)", raw_email, re.IGNORECASE)
            email = em_m.group(1).strip() if em_m else (raw_email if "@" in raw_email else None)

            if email and email in seen_emails:
                continue
            if email:
                seen_emails.add(email)

            p = m.parent
            container = p
            while container and not container.find("img") and container.name != "body":
                container = container.parent

            full_text = container.get_text(" ", strip=True) if container else p.get_text(" ", strip=True)
            img = container.find("img") if container else None
            img_src = img.get("src") if img else None
            if img_src and " " in img_src:
                img_src = urllib.parse.quote(img_src, safe=":/%?=")

            m_name = re.search(r"((?:Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.)\s*(?:Dr\.)?\s*[A-Za-z\s.,-]+?)(?:\s+(?:Dean|Associate Dean|Assistant Dean|Chair of|Advisor|Director|Researcher|tel|\+66|email))", full_text)
            name_en = m_name.group(1).strip() if m_name else full_text.split("tel")[0].split("email")[0].strip()

            # Clean name_en
            clean_name_en = re.sub(r"^(Home\s*›\s*Faculty\s*Faculty\s*Members\s*)", "", name_en).strip()

            # Map English title to Thai rank
            rank_th = "อาจารย์"
            if "Prof. Dr." in clean_name_en:
                rank_th = "ศ.ดร."
            elif "Assoc. Prof. Dr." in clean_name_en or "Assoc.Prof.Dr." in clean_name_en:
                rank_th = "รศ.ดร."
            elif "Asst. Prof. Dr." in clean_name_en or "Asst.Prof.Dr." in clean_name_en:
                rank_th = "ผศ.ดร."
            elif "Assoc. Prof." in clean_name_en:
                rank_th = "รศ."
            elif "Asst. Prof." in clean_name_en:
                rank_th = "ผศ."
            elif "Prof." in clean_name_en:
                rank_th = "ศ."
            elif "Dr." in clean_name_en:
                rank_th = "ดร."

            clean_person_en = re.sub(r"^(?:Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.)(?:\s*Dr\.)?\s*", "", clean_name_en).strip()
            raw_name_th = f"{rank_th} {clean_person_en}"

            name_parts = clean_person_en.split()
            first_name = name_parts[0] if name_parts else clean_person_en
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else first_name

            # Department / Specialization
            dept = "สายวิชาเทคโนโลยีชีวภาพและทรัพยากรชีวภาพ"
            if "Bioinformatics" in full_text:
                dept = "สายวิชาวิทยาการชีวมิติและชีวสารสนเทศ"
            elif "Postharvest" in full_text:
                dept = "สายวิชาเทคโนโลยีหลังการเก็บเกี่ยว"
            elif "Biochemical" in full_text:
                dept = "สายวิชาเทคโนโลยีชีวเคมี"
            elif "Natural Resource" in full_text:
                dept = "สายวิชาการจัดการทรัพยากรชีวภาพ"

            results.append({
                "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                "university_en": "King Mongkut's University of Technology Thonburi",
                "faculty_th": "คณะทรัพยากรชีวภาพและเทคโนโลยี",
                "faculty_en": "School of Bioresources and Technology",
                "department_th": dept,
                "raw_name_th": raw_name_th,
                "raw_name_en": clean_name_en,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
                "research_interests": ["Bioresources", "Biotechnology", "Bioinformatics", "Postharvest Technology", "Biochemical Technology"],
            })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from KMUTT SBT.")
    return results


def crawl_cmu_public_health(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic public health faculty from Chiang Mai University Faculty of Public Health."""
    print("\n[Crawler 4/4] Scraping CMU Faculty of Public Health (คณะสาธารณสุขศาสตร์ มช.)...", flush=True)
    url = "https://ph.cmu.ac.th/lecturer.php"
    results = []

    try:
        r = client.get(url, headers=CLIENT_HEADERS, timeout=15.0)
        if r.status_code != 200:
            print(f"  [Warn] Failed {url}: HTTP {r.status_code}")
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        seen_names = set()

        for row in soup.find_all("div", class_="row"):
            txt = row.get_text(" \n ", strip=True)
            if "@cmu.ac.th" not in txt:
                continue

            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            name_th = None
            name_en = None
            interests = ["Public Health", "Epidemiology", "Health Informatics"]

            for i, l in enumerate(lines):
                if any(l.startswith(p) for p in ["ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์", "อ.ดร.", "ผศ.ดร.", "รศ.ดร.", "ศ.ดร.", "ศ.เกียรติคุณ"]):
                    if l not in ["อาจารย์ผู้เชี่ยวชาญ", "อาจารย์"]:
                        name_th = l
                        if i + 1 < len(lines):
                            next_l = lines[i+1]
                            if any(w in next_l for w in ["Professor", "Lect.", "Dr."]):
                                name_en = next_l
                        break

            if not name_th or name_th in seen_names or len(name_th) < 5:
                continue
            seen_names.add(name_th)

            # Email
            em_m = re.search(r"([a-zA-Z0-9._%+-]+@cmu\.ac\.th)", txt)
            email = em_m.group(1).strip() if em_m else None

            # Interests
            m_int = re.search(r"ความเชี่ยวชาญ\s*:\s*([^|\n]+)", txt)
            if m_int:
                raw_i = m_int.group(1).strip()
                interests = [x.strip() for x in re.split(r"[,;]+", raw_i) if len(x.strip()) > 1]

            # Image
            img = row.find("img")
            img_src = None
            if img and img.get("src"):
                s = img["src"]
                img_src = f"https://ph.cmu.ac.th/{s.lstrip('/')}"
                img_src = urllib.parse.quote(img_src, safe=":/%?=")

            results.append({
                "university_th": "มหาวิทยาลัยเชียงใหม่",
                "university_en": "Chiang Mai University",
                "faculty_th": "คณะสาธารณสุขศาสตร์",
                "faculty_en": "Faculty of Public Health",
                "department_th": "สาขาวิชาสาธารณสุขศาสตร์",
                "raw_name_th": name_th,
                "raw_name_en": name_en,
                "email": email,
                "image_url": img_src,
                "profile_url": url,
                "research_interests": interests,
            })
    except Exception as exc:
        print(f"  [Error] Scraping {url}: {exc}")

    print(f"  -> Extracted {len(results)} authentic faculty from CMU Faculty of Public Health.")
    return results


# =====================================================================
# 2. State Reducer, Normalization & OpenAlex Disambiguation (Pillar 4 & 2)
# =====================================================================

TITLE_PREFIXES = [
    ("ศาสตราจารย์เกียรติคุณ นายแพทย์", "ศ.เกียรติคุณ นพ."),
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
]


def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Extracts standardized academic title, clean name, and full formatted name."""
    clean = re.sub(r"\s+", " ", raw_name).strip()
    academic_title = "อาจารย์"

    for prefix, standard in TITLE_PREFIXES:
        if clean.startswith(prefix):
            academic_title = standard
            clean = clean[len(prefix):].strip()
            break

    # Strip residual titles
    clean = re.sub(r"^(?:ดร\.|Dr\.)\s*", "", clean).strip()
    full_name_th = f"{academic_title} {clean}".strip()
    return academic_title, clean, full_name_th


def enrich_openalex_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Disambiguates and enriches author via OpenAlex Multiplexing Pool (Pillar 2)."""
    search_name = record.get("raw_name_en")
    if not search_name:
        clean_th = record.get("clean_name_th", "")
        # If pure Thai characters, search_name can be clean_th
        search_name = clean_th

    # Strip prefixes from search name
    search_name = re.sub(r"^(?:Professor|Associate Professor|Assistant Professor|Emeritus Professor|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Prof\.|Dr\.|Lect\.)(?:\s*Dr\.)?\s*", "", search_name).strip()
    search_name = re.sub(r",\s*(?:MD|Dr\.PH|Ph\.D\.|CFA|DIC).*$", "", search_name).strip()

    record["total_citations"] = 0
    record["h_index"] = 0
    record["total_publications_count"] = 0
    record["first_author_count"] = 0
    record["co_author_count"] = 0
    record["openalex_id"] = "not_indexed"
    record["featured_publications"] = []

    if not search_name or len(search_name) < 3:
        return record

    univ_en = record.get("university_en", "")
    query = urllib.parse.quote(search_name)
    url = f"https://api.openalex.org/authors?search={query}&per-page=5"

    data = fetch_oa_with_retry(url)
    if not data or not data.get("results"):
        return record

    for candidate in data["results"]:
        affiliations = candidate.get("affiliations") or []
        last_inst = candidate.get("last_known_institutions") or []
        matched_institution = False

        # Two-Factor Institutional Verification
        inst_names = []
        for a in affiliations:
            inst = a.get("institution") or {}
            inst_names.append(inst.get("display_name", "").lower())
        for inst in last_inst:
            inst_names.append(inst.get("display_name", "").lower())

        univ_lower = univ_en.lower()
        if any(univ_lower in iname or iname in univ_lower for iname in inst_names) or (
            "thammasat" in univ_lower and any("thammasat" in iname for iname in inst_names)
        ) or (
            "chiang mai" in univ_lower and any("chiang mai" in iname for iname in inst_names)
        ) or (
            "thonburi" in univ_lower and any("thonburi" in iname or "kmutt" in iname for iname in inst_names)
        ):
            matched_institution = True

        if matched_institution:
            oa_id = candidate.get("id", "").replace("https://openalex.org/", "")
            cites = candidate.get("cited_by_count") or 0
            stats = candidate.get("summary_stats") or {}
            h_idx = stats.get("h_index") or 0
            works = candidate.get("works_count") or 0

            # Enforce Bibliometric Monotonicity: works >= h_index
            works = max(works, h_idx)

            record["openalex_id"] = oa_id
            record["total_citations"] = cites
            record["h_index"] = h_idx
            record["total_publications_count"] = works

            # Fetch top works for featured publications
            works_url = f"https://api.openalex.org/works?filter=author.id:{oa_id}&per-page=3&sort=cited_by_count:desc"
            works_data = fetch_oa_with_retry(works_url)
            if works_data and works_data.get("results"):
                f_pubs = []
                for w in works_data["results"]:
                    title = w.get("title")
                    if title:
                        venue = (w.get("primary_location") or {}).get("source") or {}
                        f_pubs.append({
                            "title": title,
                            "year": w.get("publication_year"),
                            "venue": venue.get("display_name") if isinstance(venue, dict) else None,
                            "url": w.get("doi") or f"https://openalex.org/{w.get('id', '')}",
                            "citation_count": w.get("cited_by_count") or 0,
                        })
                record["featured_publications"] = f_pubs
            break

    return record


# =====================================================================
# 3. Execution Pipeline & PostgreSQL Ingestion
# =====================================================================

def execute_wave70_acquisition():
    print("=" * 70, flush=True)
    print("🚀 EXECUTING WAVE 70 GRADUATE-FOCUSED FACULTIES ACQUISITION", flush=True)
    print("=" * 70, flush=True)

    if CHECKPOINT_FILE.exists() and CHECKPOINT_FILE.stat().st_size > 1000:
        print(f"  [Resume] Loading pre-extracted records from checkpoint {CHECKPOINT_FILE}...", flush=True)
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            enriched_records = json.load(f)
        print(f"  -> Successfully resumed {len(enriched_records)} records from checkpoint.", flush=True)
    else:
        client = httpx.Client(headers=CLIENT_HEADERS, verify=False, timeout=15.0, follow_redirects=True)
        all_harvested: List[Dict[str, Any]] = []

        # Execute targeted headless crawlers
        all_harvested.extend(crawl_tu_nursing(client))
        all_harvested.extend(crawl_tu_socanth(client))
        all_harvested.extend(crawl_kmutt_sbt(client))
        all_harvested.extend(crawl_cmu_public_health(client))

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

    # Commit to Database with ID Sequence Separators
    print("\n📥 Ingesting into PostgreSQL 'faculties' table...", flush=True)
    db = SessionLocal()
    inserted_count = 0
    updated_count = 0

    try:
        counters = {
            "tu_nurse": 1,
            "tu_socanth": 1,
            "kmutt_sbt": 1,
            "cmu_ph": 1,
        }

        for r in enriched_records:
            if "พยาบาลศาสตร์" in r["faculty_th"] and "ธรรมศาสตร์" in r["university_th"]:
                prefix = "tu_nurse"
            elif "สังคมวิทยาและมานุษยวิทยา" in r["faculty_th"]:
                prefix = "tu_socanth"
            elif "ทรัพยากรชีวภาพ" in r["faculty_th"]:
                prefix = "kmutt_sbt"
            elif "สาธารณสุขศาสตร์" in r["faculty_th"] and "เชียงใหม่" in r["university_th"]:
                prefix = "cmu_ph"
            else:
                prefix = "wave70"

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
                updated_count += 1
            else:
                while True:
                    candidate_id = f"{prefix}__{counters.get(prefix, 1):03d}"
                    counters[prefix] = counters.get(prefix, 1) + 1
                    if not db.query(FacultyDB).filter(FacultyDB.id == candidate_id).first():
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
                    first_author_count=r.get("first_author_count") or 0,
                    co_author_count=r.get("co_author_count") or 0,
                    openalex_id=r.get("openalex_id") or "not_indexed",
                    embedding=[0.0] * 768,  # Non-blocking circuit breaker (Pillar 3)
                )
                db.add(new_fac)
                inserted_count += 1

        db.commit()
        print(f"✅ Ingestion successful: {inserted_count} new faculty inserted, {updated_count} existing faculty updated.")
    finally:
        db.close()


if __name__ == "__main__":
    execute_wave70_acquisition()
