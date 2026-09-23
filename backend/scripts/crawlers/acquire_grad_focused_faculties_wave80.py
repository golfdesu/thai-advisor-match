# -*- coding: utf-8 -*-
"""
Wave 80: Sripatum University (SPU) Autonomous Faculty Acquisition Pipeline
========================================================================
Harvests authentic teaching faculty across 10 academic faculties and colleges
at Sripatum University (มหาวิทยาลัยศรีปทุม / spu.ac.th), eliminating the 31-course
professor deficit in graduate and undergraduate programs:
  1. คณะนิติศาสตร์ (Faculty of Law) - LL.M. / LL.D. programs
  2. วิทยาลัยบัณฑิตศึกษาด้านการจัดการ (Graduate College of Management) - MBA / D.B.A.
  3. คณะบัญชี (Faculty of Accountancy) - Master of Accountancy
  4. คณะบริหารธุรกิจ (Faculty of Business Administration)
  5. คณะวิศวกรรมศาสตร์ (Faculty of Engineering)
  6. คณะเทคโนโลยีสารสนเทศ (Faculty of Information Technology)
  7. วิทยาลัยโลจิสติกส์และซัพพลายเชน (College of Logistics and Supply Chain)
  8. คณะนิเทศศาสตร์ (Faculty of Communication Arts)
  9. คณะศิลปศาสตร์ (Faculty of Liberal Arts)
  10. วิทยาลัยการบิน การท่องเที่ยวและการบริการ (College of Aviation, Tourism and Hospitality)

Architecture:
- 5-Pillar High-Throughput Autonomous Pipeline
- Normalizes academic titles (longest-match first: ศ.ดร., รศ.ดร., ผศ.ดร., etc.)
- Strips administrative and phone boilerplate (PDPA invariant)
- Checkpoints state to backend/data/agent_states/wave80_spu_extraction.json
- Commits cleanly to local PostgreSQL 17 faculties table
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave80_spu_extraction.json"
CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SPU_TARGETS = [
    {
        "url": "https://www.spu.ac.th/fac/law/faculty/",
        "faculty_th": "คณะนิติศาสตร์",
        "faculty_en": "Faculty of Law",
        "slug": "law",
    },
    {
        "url": "https://www.spu.ac.th/fac/graduate/staff/",
        "faculty_th": "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ",
        "faculty_en": "Graduate College of Management",
        "slug": "grad",
    },
    {
        "url": "https://www.spu.ac.th/fac/account/faculty/",
        "faculty_th": "คณะบัญชี",
        "faculty_en": "Faculty of Accountancy",
        "slug": "acc",
    },
    {
        "url": "https://www.spu.ac.th/fac/business/faculty/",
        "faculty_th": "คณะบริหารธุรกิจ",
        "faculty_en": "Faculty of Business Administration",
        "slug": "bus",
    },
    {
        "url": "https://www.spu.ac.th/fac/engineer/faculty/",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "Faculty of Engineering",
        "slug": "eng",
    },
    {
        "url": "https://www.spu.ac.th/fac/informatics/faculty/",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "faculty_en": "Faculty of Information Technology",
        "slug": "it",
    },
    {
        "url": "https://www.spu.ac.th/fac/logistics/faculty/",
        "faculty_th": "วิทยาลัยโลจิสติกส์และซัพพลายเชน",
        "faculty_en": "College of Logistics and Supply Chain",
        "slug": "log",
    },
    {
        "url": "https://www.spu.ac.th/fac/commarts/faculty/",
        "faculty_th": "คณะนิเทศศาสตร์",
        "faculty_en": "Faculty of Communication Arts",
        "slug": "ca",
    },
    {
        "url": "https://www.spu.ac.th/fac/liberal-arts/faculty/",
        "faculty_th": "คณะศิลปศาสตร์",
        "faculty_en": "Faculty of Liberal Arts",
        "slug": "la",
    },
    {
        "url": "https://www.spu.ac.th/fac/cath/faculty/",
        "faculty_th": "วิทยาลัยการบิน การท่องเที่ยวและการบริการ",
        "faculty_en": "College of Aviation, Tourism and Hospitality",
        "slug": "cath",
    },
]

# Longest-match title alternation
PREFIX_MAP = [
    (r"^(?:ศาสตราจารย์\s*เกียรติคุณ\s*ดร\.|ศ\.\s*เกียรติคุณ\s*ดร\.)\s*", "ศ.ดร."),
    (r"^(?:ศาสตราจารย์\s*ดร\.|ศ\.\s*ดร\.)\s*", "ศ.ดร."),
    (r"^(?:รองศาสตราจารย์\s*ดร\.|รศ\.\s*ดร\.)\s*", "รศ.ดร."),
    (r"^(?:ผู้ช่วยศาสตราจารย์\s*ดร\.|ผศ\.\s*ดร\.)\s*", "ผศ.ดร."),
    (r"^(?:ศาสตราจารย์\s*เกียรติคุณ|ศ\.\s*เกียรติคุณ)\s*", "ศ."),
    (r"^(?:ศาสตราจารย์|ศ\.)\s*", "ศ."),
    (r"^(?:รองศาสตราจารย์|รศ\.)\s*", "รศ."),
    (r"^(?:ผู้ช่วยศาสตราจารย์|ผศ\.)\s*", "ผศ."),
    (r"^(?:ดร\.)\s*", "ดร."),
    (r"^(?:อาจารย์|อ\.)\s*", "อ."),
    (r"^(?:นายแพทย์|นพ\.)\s*", "นพ."),
    (r"^(?:แพทย์หญิง|พญ\.)\s*", "พญ."),
    (r"^(?:นาย|นางสาว|นาง)\s*", "อ."),
]


def parse_thai_academic_name(raw_name: str) -> Optional[Tuple[str, str, str, str]]:
    cleaned = re.sub(r"\s+", " ", raw_name).strip()
    if not cleaned or len(cleaned) < 4:
        return None

    # Remove degree suffixes or parentheses
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    cleaned = re.sub(r",\s*(?:Ph\.D|M\.S|B\.A|LL\.B|LL\.M|Ph\.D\.|MBA).*$", "", cleaned, flags=re.I).strip()

    # Match academic title
    ac_title = "อ."
    name_body = cleaned
    for pat, standard_t in PREFIX_MAP:
        if re.search(pat, cleaned):
            ac_title = standard_t
            name_body = re.sub(pat, "", cleaned).strip()
            break

    # Strip repeated or leftover title markers in body
    for pat, _ in PREFIX_MAP:
        name_body = re.sub(pat, "", name_body).strip()

    name_body = re.sub(r"^[.\s]+", "", name_body).strip()
    name_body = re.sub(r"\s+", " ", name_body)

    # Discard non-name sentences or announcements
    if any(k in name_body for k in ["ร่วมเป็น", "เปิดคลาส", "จัดคลาส", "ยินดีต้อนรับ", "คณะกรรมการ", "ตัวจริงในอุตสาหกรรม"]):
        return None

    # Strip trailing titles or roles
    name_body = re.sub(r"(?:คณบดี|รองคณบดี|ผู้ช่วยคณบดี|หัวหน้าสาขาวิชา|ผู้อำนวยการ).*$", "", name_body).strip()

    parts = name_body.split()
    if not parts:
        return None

    fname = parts[0]
    lname = " ".join(parts[1:]) if len(parts) > 1 else fname
    full_th = f"{ac_title} {fname} {lname}".strip()
    if fname == lname:
        full_th = f"{ac_title} {fname}".strip()

    return ac_title, fname, lname, full_th


def extract_spu_faculty_page(target: dict) -> List[dict]:
    url = target["url"]
    fac_th = target["faculty_th"]
    fac_en = target["faculty_en"]
    slug = target["slug"]

    records = []
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True, verify=False)
        if r.status_code != 200:
            print(f"  [HTTP {r.status_code}] Failed to fetch {url}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".tm-spu-card, .awsm-grid-card, .awsm-grid-item, .elementor-post")

        seen_names = set()
        for idx, card in enumerate(cards, 1):
            name_el = card.select_one(".tm-spu-name, .awsm-personal-info h3, .elementor-post__title, h4, h3, h2")
            if not name_el:
                continue

            raw_name = name_el.get_text(strip=True)
            parsed = parse_thai_academic_name(raw_name)
            if not parsed:
                continue

            ac_title, fname, lname, full_th = parsed
            if full_th in seen_names:
                continue
            seen_names.add(full_th)

            # Image
            img_el = card.find("img")
            img_url = None
            if img_el:
                src = img_el.get("src") or img_el.get("data-src")
                if src and not any(x in src.lower() for x in ["logo", "icon", "arrow", "svg", "banner"]):
                    img_url = src

            # Role / Position
            role_el = card.select_one(".tm-spu-position, .awsm-contact-details, .elementor-post__excerpt, p")
            role_txt = None
            if role_el:
                rt = role_el.get_text(separator=" ", strip=True)
                # Purge phone numbers and repetitive boilerplate
                rt = re.sub(r"โทรศัพท์\s*:\s*[0-9\s-]+(?:\s*ต่อ\s*[0-9]+)?", "", rt)
                rt = re.sub(r"\b02[0-9-]+\b", "", rt)
                rt = re.sub(r"\s+", " ", rt).strip()
                if rt and len(rt) > 2 and len(rt) < 120:
                    role_txt = rt

            # Profile URL if available
            link_el = card.find("a", href=True)
            profile_url = link_el["href"] if link_el and "/teachers/" in link_el["href"] else url

            # Construct unique stable ID
            fid = f"spu_{slug}_{idx:04d}"

            records.append({
                "id": fid,
                "university": "Sripatum University",
                "university_th": "มหาวิทยาลัยศรีปทุม",
                "faculty": fac_en,
                "faculty_th": fac_th,
                "department": fac_en,
                "department_th": fac_th,
                "academic_title_th": ac_title,
                "first_name": fname,
                "last_name": lname,
                "full_name_th": full_th,
                "role": role_txt,
                "email": None,
                "image_url": img_url,
                "profile_url": profile_url,
                "education": [],
                "research_interests": [fac_th],
                "taught_courses": [],
                "featured_publications": [],
                "total_publications_count": 0,
                "first_author_count": 0,
                "co_author_count": 0,
                "total_citations": 0,
                "h_index": 0,
                "openalex_id": "not_indexed",
                "scholar_url": None,
                "embedding_text": f"อาจารย์ {full_th} สังกัด {fac_th} มหาวิทยาลัยศรีปทุม สาขาวิชา {fac_th}",
                "embedding": [0.0] * 768,
            })

        print(f"  [SPU {fac_th}] Harvested {len(records)} authentic faculty members.")
    except Exception as e:
        print(f"  [ERROR SPU {fac_th}] {e}")

    return records


def run_wave80_spu_acquisition():
    print("=================================================================", flush=True)
    print("🚀 WAVE 80: SRIPATUM UNIVERSITY AUTONOMOUS FACULTY ACQUISITION", flush=True)
    print("=================================================================", flush=True)

    all_harvested = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(extract_spu_faculty_page, target): target for target in SPU_TARGETS}
        for fut in as_completed(futures):
            res = fut.result()
            all_harvested.extend(res)

    print(f"\n📦 Total SPU faculty harvested across 10 faculties: {len(all_harvested)}")

    # Dedup by normalized Thai name across SPU
    deduped = {}
    for r in all_harvested:
        k = (r["first_name"], r["last_name"])
        if k not in deduped:
            deduped[k] = r
        else:
            # Prefer card with image or role
            existing = deduped[k]
            if not existing.get("image_url") and r.get("image_url"):
                existing["image_url"] = r["image_url"]
            if not existing.get("role") and r.get("role"):
                existing["role"] = r["role"]

    final_records = list(deduped.values())
    print(f"✅ Distinct SPU faculty after dedup: {len(final_records)}")

    # Checkpoint to JSON
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_records, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpointed state to {CHECKPOINT_PATH}")

    # Commit to PostgreSQL 17
    db = SessionLocal()
    inserted = 0
    updated = 0
    try:
        for r in final_records:
            existing = db.query(FacultyDB).filter(FacultyDB.id == r["id"]).first()
            if not existing:
                # check by full_name_th and university_th
                existing = db.query(FacultyDB).filter(
                    FacultyDB.university_th == r["university_th"],
                    FacultyDB.full_name_th == r["full_name_th"],
                ).first()

            if existing:
                existing.faculty_th = r["faculty_th"]
                existing.faculty = r["faculty"]
                existing.department_th = r["department_th"]
                existing.department = r["department"]
                if r["image_url"] and not existing.image_url:
                    existing.image_url = r["image_url"]
                if r["role"] and not existing.role:
                    existing.role = r["role"]
                updated += 1
            else:
                new_f = FacultyDB(
                    id=r["id"],
                    university=r["university"],
                    university_th=r["university_th"],
                    faculty=r["faculty"],
                    faculty_th=r["faculty_th"],
                    department=r["department"],
                    department_th=r["department_th"],
                    academic_title_th=r["academic_title_th"],
                    first_name=r["first_name"],
                    last_name=r["last_name"],
                    full_name_th=r["full_name_th"],
                    role=r["role"],
                    email=r["email"],
                    image_url=r["image_url"],
                    profile_url=r["profile_url"],
                    education=r["education"],
                    research_interests=r["research_interests"],
                    taught_courses=r["taught_courses"],
                    featured_publications=r["featured_publications"],
                    total_publications_count=r["total_publications_count"],
                    first_author_count=r["first_author_count"],
                    co_author_count=r["co_author_count"],
                    total_citations=r["total_citations"],
                    h_index=r["h_index"],
                    openalex_id=r["openalex_id"],
                    scholar_url=r["scholar_url"],
                    embedding_text=r["embedding_text"],
                    embedding=r["embedding"],
                )
                db.add(new_f)
                inserted += 1

        db.commit()
        print(f"🎉 Successfully committed to PostgreSQL: {inserted} inserted, {updated} updated.")
    finally:
        db.close()


if __name__ == "__main__":
    run_wave80_spu_acquisition()
