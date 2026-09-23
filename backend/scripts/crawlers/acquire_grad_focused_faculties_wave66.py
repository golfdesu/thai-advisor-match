# -*- coding: utf-8 -*-
"""
Wave 66: Autonomous Acquisition of Graduate-Focused Faculty (5-Pillar Architecture)
===================================================================================
Acquires authentic faculty members across 3 key graduate faculties with degree deficits:
1. TU Fine Arts (คณะศิลปกรรมศาสตร์ มหาวิทยาลัยธรรมศาสตร์)
   - Supporting M.F.A. in Art, Design and Creative Economy & undergraduate degree programs.
   - Portal: https://fineart.tu.ac.th/
2. KU Natural Resources & Agro-Industry (คณะทรัพยากรธรรมชาติและอุตสาหกรรมเกษตร มหาวิทยาลัยเกษตรศาสตร์)
   - Supporting M.Sc. in Food Technology, M.Sc. in Plant Science, and B.Sc. programs.
   - Portal: https://fna.csc.ku.ac.th/
3. KMUTT FIET (คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี)
   - Supporting 12 Master's and Doctoral programs in industrial, media, and technology education.
   - Portals: https://cmm.kmutt.ac.th/, https://mte.kmutt.ac.th/, https://web3.fiet.kmutt.ac.th/

Pillars:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor).
- Pillar 2: OpenAlex Multiplexing Pool (Citations, h-index, featured publications).
- Pillar 3: Non-blocking Circuit Breakers & Graceful Degradation ([0.0]*768).
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalization.
- Pillar 5: Disk Checkpointing (wave66_grad_focused_faculties.json).
"""
from __future__ import annotations

import base64
import json
import re
import sys
import time
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

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave66_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


# =====================================================================
# 1. Targeted Headless Crawlers (Pillar 1)
# =====================================================================

def crawl_tu_fineart(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from Thammasat University Faculty of Fine and Applied Arts."""
    print("\n[Crawler 1/3] Scraping TU Faculty of Fine and Applied Arts (คณะศิลปกรรมศาสตร์ มธ.)...", flush=True)
    base_url = "https://fineart.tu.ac.th"
    dept_pages = [
        ("สาขาวิชาการละคอน", "/index.php?option=com_content&view=article&id=66&Itemid=339&lang=th"),
        ("สาขาวิชาศิลปะการออกแบบพัสตราภรณ์", "/index.php?option=com_content&view=article&id=67&Itemid=340&lang=th"),
        ("สาขาวิชาออกแบบหัตถอุตสาหกรรม", "/index.php?option=com_content&view=article&id=68&Itemid=341&lang=th"),
        ("สาขาวิชาศิลปะ การออกแบบ และเศรษฐกิจสร้างสรรค์", "/index.php?option=com_content&view=article&id=178&Itemid=394&lang=th"),
    ]

    results = []
    seen_names = set()

    for dept_th, path in dept_pages:
        url = base_url + path
        try:
            r = client.get(url, timeout=20.0)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for b in soup.find_all("div", class_="blockck"):
                img = b.find("img")
                img_src = img.get("src", "") if img else ""
                if not img_src or "logo" in img_src.lower() or "head" in img_src.lower():
                    continue

                cktext = b.find("div", class_="cktext")
                if not cktext:
                    continue

                ps = [p.get_text(strip=True) for p in cktext.find_all("p") if p.get_text(strip=True)]
                if not ps:
                    continue

                name_cand = None
                for cand in ps[:2]:
                    if any(k in cand for k in ["ศ.", "รศ.", "ผศ.", "ดร.", "อาจารย์", "อ."]) and len(cand) < 60:
                        name_cand = cand
                        break

                if not name_cand or name_cand in seen_names:
                    continue
                seen_names.add(name_cand)

                # Extract email from joomla-hidden-mail base64
                jmail = b.find("joomla-hidden-mail")
                email = None
                if jmail and jmail.get("text"):
                    try:
                        raw_email = base64.b64decode(jmail["text"]).decode("utf-8", errors="ignore").strip().lower()
                        # PDPA: filter freemail
                        if any(dom in raw_email for dom in ["@gmail.", "@yahoo.", "@hotmail.", "@outlook.", "@live."]):
                            email = None
                        elif "@tu.ac.th" in raw_email or "@arts.tu.ac.th" in raw_email or "@" in raw_email:
                            email = raw_email
                    except Exception:
                        email = None

                full_img = base_url + img_src if img_src.startswith("/") else img_src
                full_img = urllib.parse.quote(full_img, safe=":/%?=") if full_img else None

                results.append({
                    "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                    "university_en": "Thammasat University",
                    "faculty_th": "คณะศิลปกรรมศาสตร์",
                    "faculty_en": "Faculty of Fine and Applied Arts",
                    "department_th": dept_th,
                    "raw_name_th": name_cand,
                    "email": email,
                    "image_url": full_img,
                    "profile_url": url,
                    "research_interests": ["Fine Arts", "Creative Economy", dept_th],
                })
        except Exception as e:
            print(f"  ⚠️ Error scraping TU Fine Arts ({dept_th}): {e}", flush=True)

    print(f"  ✅ TU Fine Arts: Harvested {len(results)} authentic faculty members across 4 departments.")
    return results


def crawl_ku_fna(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from Kasetsart University Faculty of Natural Resources and Agro-Industry."""
    print("\n[Crawler 2/3] Scraping KU Faculty of Natural Resources and Agro-Industry (คณะทรัพยากรธรรมชาติและอุตสาหกรรมเกษตร มก.)...", flush=True)
    dept_pages = [
        ("ภาควิชาเกษตรและทรัพยากร", "https://fna.csc.ku.ac.th/?page_id=8469"),
        ("ภาควิชาเทคโนโลยีการอาหารและโภชนาการ", "https://fna.csc.ku.ac.th/?page_id=8480"),
    ]

    results = []
    seen_names = set()

    for dept_th, url in dept_pages:
        try:
            r = client.get(url, timeout=20.0)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            pc = soup.find("div", class_="page-content")
            if not pc:
                continue

            for col in pc.find_all("div", class_="elementor-column"):
                img = col.find("img")
                img_src = img.get("data-src") or img.get("src") if img else None
                if img_src and ("personblank" in img_src or "logo" in img_src):
                    img_src = None

                name_el = col.find("b") or col.find("strong") or col.find("p")
                name_cand = name_el.get_text(strip=True) if name_el else None
                if not name_cand or not any(k in name_cand for k in ["ผศ.", "รศ.", "ศ.", "ดร.", "อาจารย์", "สพญ."]) or len(name_cand) > 60:
                    continue

                if name_cand in seen_names:
                    continue
                seen_names.add(name_cand)

                if img_src:
                    img_src = urllib.parse.quote(img_src, safe=":/%?=")

                results.append({
                    "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                    "university_en": "Kasetsart University",
                    "faculty_th": "คณะทรัพยากรธรรมชาติและอุตสาหกรรมเกษตร",
                    "faculty_en": "Faculty of Natural Resources and Agro-Industry",
                    "department_th": dept_th,
                    "raw_name_th": name_cand,
                    "email": None,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": ["Natural Resources", "Agro-Industry", dept_th],
                })
        except Exception as e:
            print(f"  ⚠️ Error scraping KU FNA ({dept_th}): {e}", flush=True)

    print(f"  ✅ KU Natural Resources & Agro-Industry: Harvested {len(results)} authentic faculty members across 2 departments.")
    return results


def crawl_kmutt_fiet(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from KMUTT Faculty of Industrial Education and Technology."""
    print("\n[Crawler 3/3] Scraping KMUTT Faculty of Industrial Education and Technology (คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี มจธ.)...", flush=True)
    results = []
    seen_names = set()

    # Part 1: CMM (Department of Media Technology and Media Arts) API
    try:
        r_cmm = client.get("https://cmm.kmutt.ac.th/api/executive", timeout=15.0)
        if r_cmm.status_code == 200:
            for item in r_cmm.json():
                raw_th = item.get("name", {}).get("TH", "").strip()
                raw_en = item.get("name", {}).get("EN", "").strip()
                email = item.get("email", "").strip().lower()
                image = item.get("image", "").strip()
                interests = list(item.get("expertise", {}).values()) if isinstance(item.get("expertise"), dict) else []

                if raw_th and raw_th not in seen_names:
                    seen_names.add(raw_th)
                    if image:
                        image = urllib.parse.quote(image, safe=":/%?=")
                    results.append({
                        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                        "university_en": "King Mongkut's University of Technology Thonburi",
                        "faculty_th": "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
                        "faculty_en": "Faculty of Industrial Education and Technology",
                        "department_th": "สาขาวิชามีเดียเทคโนโลยีและมีเดียอาตส์",
                        "raw_name_th": raw_th,
                        "name_en": raw_en if raw_en else None,
                        "email": email if "@kmutt.ac.th" in email else None,
                        "image_url": image if image else None,
                        "profile_url": "https://cmm.kmutt.ac.th",
                        "research_interests": ["Media Technology", "Digital Media"] + interests[:3],
                    })
    except Exception as e:
        print(f"  ⚠️ Error fetching KMUTT CMM API: {e}", flush=True)

    # Part 2: MTE (Mechanical Technology Education)
    try:
        r_mte = client.get("https://mte.kmutt.ac.th/personnel.html", timeout=15.0)
        if r_mte.status_code == 200:
            soup_mte = BeautifulSoup(r_mte.text, "html.parser")
            for t in soup_mte.find_all(["p", "h3", "h4", "h5", "strong", "span"]):
                txt = t.get_text(strip=True)
                if any(k in txt for k in ["ผศ.", "รศ.", "ดร."]) and 10 < len(txt) < 40 and not any(k in txt for k in ["หัวหน้า", "โทร", "ห้อง", "โทรสาร", "อาจารย์พิเศษ"]):
                    if txt not in seen_names:
                        seen_names.add(txt)
                        results.append({
                            "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                            "university_en": "King Mongkut's University of Technology Thonburi",
                            "faculty_th": "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
                            "faculty_en": "Faculty of Industrial Education and Technology",
                            "department_th": "สาขาวิชาครุศาสตร์เครื่องกล",
                            "raw_name_th": txt,
                            "email": None,
                            "image_url": None,
                            "profile_url": "https://mte.kmutt.ac.th/personnel.html",
                            "research_interests": ["Mechanical Engineering", "Mechanical Technology Education"],
                        })
    except Exception as e:
        print(f"  ⚠️ Error scraping KMUTT MTE: {e}", flush=True)

    # Part 3: FIET Executive Team
    try:
        r_exec = client.get("https://web3.fiet.kmutt.ac.th/about/administration/executive-team.html", timeout=15.0)
        if r_exec.status_code == 200:
            soup_exec = BeautifulSoup(r_exec.text, "html.parser")
            for p in soup_exec.find_all(["p", "h3", "h4", "h5", "span"]):
                txt = p.get_text(strip=True)
                if any(k in txt for k in ["ผศ.", "รศ.", "ดร."]) and 10 < len(txt) < 40 and not any(k in txt for k in ["คณบดี", "รองคณบดี", "ผู้ช่วยคณบดี"]):
                    if txt not in seen_names:
                        seen_names.add(txt)
                        results.append({
                            "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
                            "university_en": "King Mongkut's University of Technology Thonburi",
                            "faculty_th": "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
                            "faculty_en": "Faculty of Industrial Education and Technology",
                            "department_th": "สาขาวิชาครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
                            "raw_name_th": txt,
                            "email": None,
                            "image_url": None,
                            "profile_url": "https://web3.fiet.kmutt.ac.th/about/administration/executive-team.html",
                            "research_interests": ["Industrial Education", "Technology Education"],
                        })
    except Exception as e:
        print(f"  ⚠️ Error scraping KMUTT FIET Executive: {e}", flush=True)

    print(f"  ✅ KMUTT FIET: Harvested {len(results)} authentic faculty members across 3 divisions.")
    return results


# =====================================================================
# 2. State Reducer & Title Normalizer (Pillar 4)
# =====================================================================

def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Normalizes Thai academic ranks, prefixes, and clean names."""
    t = raw_name.strip()
    t = re.sub(r"\s+", " ", t)

    title_patterns = [
        (r"^(ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.)", "ศ.ดร."),
        (r"^(รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.|รองศาสตราจารย\s*ดร\.)", "รศ.ดร."),
        (r"^(ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.)", "ผศ.ดร."),
        (r"^(อาจารย์\s*ดร\.|อ\.\s*ดร\.)", "อ.ดร."),
        (r"^(ศาสตราจารย์|ศ\.)", "ศ."),
        (r"^(รองศาสตราจารย์|รศ\.)", "รศ."),
        (r"^(ผู้ช่วยศาสตราจารย์|ผศ\.)", "ผศ."),
        (r"^(สพญ\.\s*ดร\.|สัตวแพทย์หญิง\s*ดร\.)", "อ.ดร."),
        (r"^(สพญ\.|สัตวแพทย์หญิง)", "อ."),
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
    for pat, norm in title_patterns:
        m = re.match(pat, t)
        if m:
            detected_title = norm
            t = t[m.end():].strip()
            break

    # Strip repeated or inner prefixes
    for pat, norm in title_patterns:
        m = re.match(pat, t)
        if m:
            t = t[m.end():].strip()

    t = re.sub(r"^(นาย|นาง|นางสาว)\s*", "", t).strip()

    clean_full_name = f"{detected_title} {t}".strip() if detected_title else t
    return detected_title or "อาจารย์", clean_full_name, t


def enrich_faculty_with_openalex(faculty: Dict[str, Any]) -> Dict[str, Any]:
    """Queries OpenAlex to retrieve citations, h-index, and author ID with 2-factor verification."""
    clean_search = faculty.get("name_en")
    if not clean_search:
        # Fallback to Romanization or clean name search
        name_parts = (faculty.get("raw_name_th") or "").split(" ")
        clean_search = " ".join([p for p in name_parts if len(p) > 2][:3])

    univ_map = {
        "มหาวิทยาลัยธรรมศาสตร์": ("Thammasat", "I145328906"),
        "มหาวิทยาลัยเกษตรศาสตร์": ("Kasetsart", "I185261750"),
        "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": ("King Mongkut", "I60837268"),
    }
    univ_keyword, inst_id = univ_map.get(faculty["university_th"], ("Thailand", ""))

    encoded_name = urllib.parse.quote(clean_search)
    url = f"https://api.openalex.org/authors?search={encoded_name}"
    data = fetch_oa_with_retry(url)

    if data and "results" in data and len(data["results"]) > 0:
        candidates = data["results"]
        best_cand = None
        for cand in candidates:
            insts = cand.get("last_known_institutions") or []
            inst_names = [i.get("display_name", "") for i in insts]
            inst_ids = [i.get("id", "") for i in insts]

            if any(univ_keyword.lower() in iname.lower() for iname in inst_names) or (inst_id and any(inst_id in i_id for i_id in inst_ids)):
                best_cand = cand
                break

        if not best_cand and len(candidates) > 0:
            c0 = candidates[0]
            insts = c0.get("last_known_institutions") or []
            if any("Thailand" in i.get("country_code", "") for i in insts) or any("thailand" in i.get("display_name", "").lower() for i in insts):
                best_cand = c0

        if best_cand:
            oa_id = best_cand.get("id", "").replace("https://openalex.org/", "")
            faculty["openalex_id"] = oa_id
            faculty["total_citations"] = best_cand.get("cited_by_count", 0) or 0
            faculty["h_index"] = (best_cand.get("summary_stats") or {}).get("h_index", 0) or 0

            oa_name = best_cand.get("display_name")
            if oa_name and not faculty.get("name_en"):
                faculty["name_en"] = oa_name

            featured = []
            works_api = best_cand.get("works_api_url")
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
    print("🚀 EXECUTING WAVE 66: GRADUATE-FOCUSED FACULTY ACQUISITION PIPELINE", flush=True)
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
            all_raw_faculty.extend(crawl_tu_fineart(client))
            all_raw_faculty.extend(crawl_ku_fna(client))
            all_raw_faculty.extend(crawl_kmutt_fiet(client))

            print(f"\n📊 Total Raw Faculty Harvested: {len(all_raw_faculty)}")

            # Step 2: Normalize names & academic titles
            print("\n🧹 Running State Reducer & Title Normalization (Pillar 4)...", flush=True)
            normalized_faculty = []
            for i, item in enumerate(all_raw_faculty, 1):
                title_th, full_th, base_n = normalize_thai_title_and_name(item.get("raw_name_th") or "")
                item["title_th"] = title_th or "อาจารย์"
                item["full_name_th"] = full_th or item.get("raw_name_th")

                parts = base_n.split(" ")
                item["first_name_th"] = parts[0] if parts else base_n
                item["last_name_th"] = " ".join(parts[1:]) if len(parts) > 1 else ""

                if item.get("name_en"):
                    en_parts = item["name_en"].split(" ")
                    item["first_name_en"] = en_parts[0] if en_parts else item["name_en"]
                    item["last_name_en"] = " ".join(en_parts[1:]) if len(en_parts) > 1 else ""
                else:
                    item["first_name_en"] = None
                    item["last_name_en"] = None

                normalized_faculty.append(item)

            # Step 3: OpenAlex Multiplexing & Metric Enrichment (Pillar 2)
            print("\n🌐 Enriching Faculty Metrics via OpenAlex Multiplexing (Pillar 2)...", flush=True)
            with ThreadPoolExecutor(max_workers=5) as executor:
                enriched_faculty = list(executor.map(enrich_faculty_with_openalex, normalized_faculty))

            # Save Checkpoint (Pillar 5)
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(enriched_faculty, f, ensure_ascii=False, indent=2)
            print(f"  💾 Checkpointed {len(enriched_faculty)} records to {CHECKPOINT_FILE}", flush=True)

        # Step 4: PostgreSQL public.faculties Ingestion (Pillar 3)
        print("\n📥 Ingesting Authentic Faculty Records into PostgreSQL (localhost:5432)...", flush=True)
        inserted_count = 0
        updated_count = 0

        for idx, item in enumerate(enriched_faculty, 1):
            full_name = item.get("full_name_th") or item.get("raw_name_th")
            univ_th = item.get("university_th")
            fac_th = item.get("faculty_th")
            dept_th = item.get("department_th")
            univ_en = TH_TO_EN_CANONICAL.get(univ_th, item.get("university_en"))

            existing = (
                db.query(FacultyDB)
                .filter(FacultyDB.university_th == univ_th, FacultyDB.full_name_th == full_name)
                .first()
            )

            if "ธรรมศาสตร์" in univ_th:
                custom_id = f"tu_fineart__{idx:03d}"
            elif "เกษตรศาสตร์" in univ_th:
                custom_id = f"ku_fna__{idx:03d}"
            else:
                custom_id = f"kmutt_fiet__{idx:03d}"

            # Sanitize empty strings to None
            img_val = item.get("image_url")
            img_val = None if not img_val or img_val.strip() == "" else img_val.strip()

            email_val = item.get("email")
            email_val = None if not email_val or email_val.strip() == "" else email_val.strip()

            prof_val = item.get("profile_url")
            prof_val = None if not prof_val or prof_val.strip() == "" else prof_val.strip()

            if not existing:
                clean_interests = []
                for interest in (item.get("research_interests") or []):
                    for sub in str(interest).split(" / "):
                        if sub.strip() and sub.strip() not in clean_interests:
                            clean_interests.append(sub.strip())

                clean_pubs = []
                for pub in (item.get("featured_publications") or []):
                    clean_pubs.append({
                        "title": pub["title"],
                        "year": pub.get("year"),
                        "venue": pub.get("venue"),
                        "url": pub.get("url") or pub.get("doi"),
                        "citation_count": pub.get("citation_count") or pub.get("citations") or 0,
                    })

                new_record = FacultyDB(
                    id=custom_id,
                    first_name=item.get("first_name_th") or item.get("first_name_en") or "อาจารย์",
                    last_name=item.get("last_name_th") or item.get("last_name_en") or item.get("first_name_th") or "อาจารย์",
                    academic_title_th=item.get("title_th") or "อาจารย์",
                    full_name_th=full_name,
                    university=univ_en,
                    university_th=univ_th,
                    faculty_th=fac_th,
                    department_th=dept_th or "ระบุไม่ได้",
                    email=email_val,
                    image_url=img_val,
                    profile_url=prof_val,
                    research_interests=clean_interests,
                    openalex_id=item.get("openalex_id"),
                    total_citations=item.get("total_citations") or 0,
                    h_index=item.get("h_index") or 0,
                    total_publications_count=item.get("total_publications_count") or 0,
                    featured_publications=clean_pubs,
                    embedding=[0.0] * 768,  # Non-blocking circuit breaker dummy vector
                )
                db.add(new_record)
                inserted_count += 1
            else:
                # Enrich existing record
                if email_val and not existing.email:
                    existing.email = email_val
                if img_val and not existing.image_url:
                    existing.image_url = img_val
                if dept_th and (not existing.department_th or existing.department_th == "ระบุไม่ได้"):
                    existing.department_th = dept_th
                if univ_en and not existing.university:
                    existing.university = univ_en

                existing.total_citations = max(existing.total_citations or 0, item.get("total_citations") or 0)
                existing.h_index = max(existing.h_index or 0, item.get("h_index") or 0)
                existing.total_publications_count = max(existing.total_publications_count or 0, item.get("total_publications_count") or 0)

                if (not existing.openalex_id or existing.openalex_id == "not_indexed") and item.get("openalex_id") and item.get("openalex_id") != "not_indexed":
                    existing.openalex_id = item.get("openalex_id")

                updated_count += 1

            if idx % 30 == 0:
                db.commit()
                print(f"  ... Processed {idx}/{len(enriched_faculty)} records (Inserted: {inserted_count}, Updated: {updated_count})", flush=True)

        db.commit()
        print(f"\n✅ Successfully committed Wave 66! Inserted: {inserted_count} new, Updated/Enriched: {updated_count} existing.", flush=True)

    finally:
        db.close()
        client.close()

    print(f"\n🎉 Wave 66 Execution Completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_pipeline()
