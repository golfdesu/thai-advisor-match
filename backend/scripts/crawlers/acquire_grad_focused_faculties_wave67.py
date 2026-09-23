# -*- coding: utf-8 -*-
"""
Wave 67: Autonomous Acquisition of Graduate-Focused Faculty (5-Pillar Architecture)
===================================================================================
Acquires authentic faculty members across 2 key KMUTNB faculties with graduate/degree deficits:
1. KMUTNB FITM (คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ ปราจีนบุรี)
   - Supporting 10 active degree programs in courses (IT, IM, CDM, AEI).
   - Portals: https://fitm.kmutnb.ac.th/personnel_IT.html, personnel_IM.html, personnel_CDM.html, personnel_AEI.html
2. KMUTNB FAS (คณะศิลปศาสตร์ประยุกต์ มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ)
   - Supporting 4 Master's & Doctoral programs in courses (M.A. English for Business, M.A. I/O Psychology, M.Econ Applied Economics, Ph.D. I/O Psychology).
   - Portal: https://www.arts.kmutnb.ac.th/th/personal

Pillars:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor).
- Pillar 2: OpenAlex Multiplexing Pool (Citations, h-index, featured publications).
- Pillar 3: Non-blocking Circuit Breakers & Graceful Degradation ([0.0]*768).
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalization.
- Pillar 5: Disk Checkpointing (wave67_grad_focused_faculties.json).
"""
from __future__ import annotations

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

CHECKPOINT_FILE = BACKEND_DIR / "data" / "agent_states" / "wave67_grad_focused_faculties.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}


# =====================================================================
# 1. Targeted Headless Crawlers (Pillar 1)
# =====================================================================

def crawl_kmutnb_fitm(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from KMUTNB Faculty of Industrial Technology and Management (FITM)."""
    print("\n[Crawler 1/2] Scraping KMUTNB FITM (คณะเทคโนโลยีและการจัดการอุตสาหกรรม มจพ.)...", flush=True)
    dept_pages = [
        ("ภาควิชาเทคโนโลยีสารสนเทศ", "https://fitm.kmutnb.ac.th/personnel_IT.html"),
        ("ภาควิชาการจัดการอุตสาหกรรม", "https://fitm.kmutnb.ac.th/personnel_IM.html"),
        ("ภาควิชาเทคโนโลยีการออกแบบและผลิตเครื่องจักรอุตสาหกรรมเกษตร", "https://fitm.kmutnb.ac.th/personnel_AEI.html"),
        ("ภาควิชาคอมพิวเตอร์ช่วยออกแบบและบริหารงานก่อสร้าง", "https://fitm.kmutnb.ac.th/personnel_CDM.html"),
    ]

    results = []
    seen_names = set()

    for dept_th, url in dept_pages:
        try:
            r = client.get(url, timeout=20.0)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if "staff" in src.lower():
                    p = img.parent
                    raw_text = p.get_text(strip=True)
                    # Filter pure teaching faculty (exclude administrative support staff 'คุณ...')
                    if any(raw_text.startswith(pr) for pr in ["ผศ.", "รศ.", "ศ.", "อ.", "ดร.", "อาจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "ศาสตราจารย์"]):
                        if not raw_text.startswith("คุณ"):
                            clean_name = re.sub(
                                r"(หัวหน้าภาควิชา|รองคณบดี.*|ผู้ช่วยคณบดี.*|ประธานสาขา.*|อาจารย์ประจำภาค.*|ผู้อำนวยการ.*|คณบดี.*)",
                                "",
                                raw_text
                            ).strip()

                            if not clean_name or clean_name in seen_names:
                                continue
                            seen_names.add(clean_name)

                            full_img = f"https://fitm.kmutnb.ac.th/{src}" if not src.startswith("http") else src
                            full_img = urllib.parse.quote(full_img, safe=":/%?=")

                            results.append({
                                "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
                                "university_en": "King Mongkut's University of Technology North Bangkok",
                                "faculty_th": "คณะเทคโนโลยีและการจัดการอุตสาหกรรม",
                                "faculty_en": "Faculty of Industrial Technology and Management",
                                "department_th": dept_th,
                                "raw_name_th": clean_name,
                                "email": None,
                                "image_url": full_img,
                                "profile_url": url,
                                "research_interests": ["Industrial Technology", "Engineering Management", dept_th],
                            })
        except Exception as e:
            print(f"  ⚠️ Error scraping KMUTNB FITM ({dept_th}): {e}", flush=True)

    print(f"  ✅ KMUTNB FITM: Harvested {len(results)} authentic faculty members across 4 departments.")
    return results


def crawl_kmutnb_fas(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls authentic faculty from KMUTNB Faculty of Applied Arts (FAS) via Livewire RPC."""
    print("\n[Crawler 2/2] Scraping KMUTNB Faculty of Applied Arts (คณะศิลปศาสตร์ประยุกต์ มจพ.)...", flush=True)
    base_url = "https://www.arts.kmutnb.ac.th"
    personal_url = f"{base_url}/th/personal"

    results = []
    seen_names = set()

    try:
        r = client.get(personal_url, timeout=20.0)
        if r.status_code != 200:
            print(f"  ⚠️ Could not access KMUTNB Arts personal page: Status {r.status_code}")
            return results

        token_match = re.search(r"window\.livewire_token\s*=\s*'([^']+)'", r.text)
        token = token_match.group(1) if token_match else ""

        soup = BeautifulSoup(r.text, "html.parser")
        target_comp = None
        for c in soup.find_all(attrs={"wire:initial-data": True}):
            init_data = json.loads(c["wire:initial-data"])
            if init_data["fingerprint"]["name"] == "abouts.personal":
                target_comp = init_data
                break

        if not target_comp or not token:
            print("  ⚠️ Target Livewire component or token not found on KMUTNB Arts page.")
            return results

        dept_map = [
            (2, "ภาควิชาภาษา"),
            (3, "ภาควิชามนุษยศาสตร์"),
            (4, "ภาควิชาสังคมศาสตร์"),
        ]

        for dept_id, dept_th in dept_map:
            payload = {
                "fingerprint": target_comp["fingerprint"],
                "serverMemo": target_comp["serverMemo"],
                "updates": [
                    {
                        "type": "callMethod",
                        "payload": {
                            "id": f"v{dept_id}",
                            "method": "select",
                            "params": [dept_id]
                        }
                    }
                ]
            }

            resp = client.post(
                f"{base_url}/livewire/message/abouts.personal",
                json=payload,
                headers={
                    "X-Livewire": "true",
                    "X-CSRF-TOKEN": token,
                    "Content-Type": "application/json"
                },
                timeout=20.0
            )

            if resp.status_code == 200:
                html = resp.json().get("effects", {}).get("html", "")
                soup_res = BeautifulSoup(html, "html.parser")
                cards = soup_res.find_all("div", class_=lambda c: c and "col" in c)
                dept_count = 0
                for card in cards:
                    # Look for heading with academic rank
                    h_elem = card.find(["h3", "h4", "h5"])
                    if not h_elem:
                        continue
                    raw_name = h_elem.get_text(strip=True)
                    if not any(prefix in raw_name for prefix in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "ศาสตราจารย์", "Dr.", "Mr."]):
                        continue

                    clean_name = re.sub(
                        r"(หัวหน้าภาควิชา.*|รองคณบดี.*|คณบดี.*|ผู้ช่วยคณบดี.*|อาจารย์)$",
                        "",
                        raw_name
                    ).strip()
                    if not clean_name or clean_name in seen_names:
                        continue
                    seen_names.add(clean_name)

                    # Extract portrait image
                    img = card.find("img")
                    img_src = img.get("src") if img else None
                    if img_src and not img_src.startswith("http"):
                        img_src = f"{base_url}{img_src}"
                    img_src = urllib.parse.quote(img_src, safe=":/%?=") if img_src else None

                    # Extract email
                    email = None
                    mail_link = card.find("a", href=lambda h: h and "mailto:" in h)
                    if mail_link:
                        raw_email = mail_link["href"].replace("mailto:", "").strip().lower()
                        if "@arts.kmutnb.ac.th" in raw_email or "@kmutnb.ac.th" in raw_email:
                            email = raw_email

                    # Extract profile / research URL
                    profile_url = personal_url
                    res_link = card.find("a", href=lambda h: h and "research.kmutnb.ac.th" in h)
                    if res_link:
                        profile_url = res_link["href"].strip()

                    results.append({
                        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
                        "university_en": "King Mongkut's University of Technology North Bangkok",
                        "faculty_th": "คณะศิลปศาสตร์ประยุกต์",
                        "faculty_en": "Faculty of Applied Arts",
                        "department_th": dept_th,
                        "raw_name_th": clean_name,
                        "email": email,
                        "image_url": img_src,
                        "profile_url": profile_url,
                        "research_interests": ["Applied Arts", "Humanities and Social Sciences", dept_th],
                    })
                    dept_count += 1
                print(f"    - {dept_th}: Extracted {dept_count} professors.")
    except Exception as e:
        print(f"  ⚠️ Error scraping KMUTNB Faculty of Applied Arts: {e}", flush=True)

    print(f"  ✅ KMUTNB Applied Arts: Harvested {len(results)} authentic faculty members across 3 departments.")
    return results


# =====================================================================
# 2. State Reducer, Title Normalizer & OpenAlex Multiplexer
# =====================================================================

def normalize_thai_title_and_name(raw_name: str) -> Tuple[str, str, str]:
    """Normalizes Thai academic title prefixes and returns (academic_title_th, full_name_th, base_name)."""
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
        (r"^(Mrs\.|Mrs\s+)", "อ."),
        (r"^(Mr\.|Mr\s+)", "อ."),
        (r"^(Ms\.|Ms\s+)", "อ."),
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
        # Fallback to name parts
        name_parts = (faculty.get("raw_name_th") or "").split(" ")
        clean_search = " ".join([p for p in name_parts if len(p) > 2][:3])

    univ_keyword = "North Bangkok"
    inst_id = "I82828225"

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

            if any(univ_keyword.lower() in iname.lower() for iname in inst_names) or any(inst_id in i_id for i_id in inst_ids):
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
# 3. Main Acquisition Pipeline (5-Pillar Architecture)
# =====================================================================

def run_wave67_pipeline():
    print("=================================================================", flush=True)
    print("🚀 STARTING WAVE 67: KMUTNB GRADUATE & APPLIED FACULTY ACQUISITION", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        # Step 1: Headless Crawling (Pillar 1)
        with httpx.Client(headers=CLIENT_HEADERS, timeout=25.0, verify=False, follow_redirects=True) as client:
            all_raw_faculty = []
            all_raw_faculty.extend(crawl_kmutnb_fitm(client))
            all_raw_faculty.extend(crawl_kmutnb_fas(client))

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

        fitm_idx = 1
        fas_idx = 1

        for item in enriched_faculty:
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

            if "เทคโนโลยีและการจัดการอุตสาหกรรม" in fac_th:
                custom_id = f"kmutnb_fitm__{fitm_idx:03d}"
                fitm_idx += 1
            else:
                custom_id = f"kmutnb_fas__{fas_idx:03d}"
                fas_idx += 1

            # Sanitize empty strings to None
            img_val = item.get("image_url")
            img_val = None if not img_val or img_val.strip() == "" else img_val.strip()

            email_val = item.get("email")
            email_val = None if not email_val or email_val.strip() == "" else email_val.strip()

            prof_val = item.get("profile_url")
            prof_val = None if not prof_val or prof_val.strip() == "" else prof_val.strip()

            if not existing:
                # Ensure unique ID
                id_cand = custom_id
                id_suffix = 1
                while db.query(FacultyDB).filter(FacultyDB.id == id_cand).first():
                    id_cand = f"{custom_id}_{id_suffix}"
                    id_suffix += 1

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
                    id=id_cand,
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
                    embedding=[0.0] * 768,  # Non-blocking circuit breaker (Pillar 3)
                )
                db.add(new_record)
                inserted_count += 1
            else:
                # Update existing record with verified department, email, photo, and metrics
                if dept_th and (not existing.department_th or existing.department_th == "ระบุไม่ได้"):
                    existing.department_th = dept_th
                if email_val and not existing.email:
                    existing.email = email_val
                if img_val and not existing.image_url:
                    existing.image_url = img_val
                if prof_val and not existing.profile_url:
                    existing.profile_url = prof_val
                if (item.get("total_citations") or 0) > (existing.total_citations or 0):
                    existing.total_citations = item.get("total_citations") or 0
                if (item.get("h_index") or 0) > (existing.h_index or 0):
                    existing.h_index = item.get("h_index") or 0
                if item.get("openalex_id") and item.get("openalex_id") != "not_indexed" and (not existing.openalex_id or existing.openalex_id == "not_indexed"):
                    existing.openalex_id = item.get("openalex_id")
                updated_count += 1

        db.commit()
        print(f"\n🎉 Wave 67 Ingestion Complete: +{inserted_count} new faculty, ~{updated_count} enriched existing records.")
    finally:
        db.close()


if __name__ == "__main__":
    run_wave67_pipeline()
