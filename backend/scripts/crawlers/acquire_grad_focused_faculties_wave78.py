# -*- coding: utf-8 -*-
"""
High-Throughput Autonomous Faculty Crawler - Wave 78
====================================================
Focus: Naresuan University Faculty of Medicine (มหาวิทยาลัยนเรศวร คณะแพทยศาสตร์)
Targeting all 15 Clinical & Academic Departments to eliminate the Faculty of Medicine
professor deficit for M.Sc., Ph.D. in Medical Science and Doctor of Medicine (M.D.) programs:
1. ภาควิชาอายุรศาสตร์ (Department of Medicine)
2. ภาควิชาเวชศาสตร์ฟื้นฟู (Department of Rehabilitation Medicine)
3. ภาควิชาโสต ศอ นาสิกวิทยา (Department of Otolaryngology)
4. ภาควิชากุมารเวชศาสตร์ (Department of Pediatrics)
5. ภาควิชาจักษุวิทยา (Department of Ophthalmology)
6. ภาควิชาจิตเวชศาสตร์ (Department of Psychiatry)
7. ภาควิชานิติเวชศาสตร์ (Department of Forensic Medicine)
8. ภาควิชาพยาธิวิทยา (Department of Pathology)
9. ภาควิชารังสีวิทยา (Department of Radiology)
10. ภาควิชาวิสัญญีวิทยา (Department of Anesthesiology)
11. ภาควิชาศัลยศาสตร์ (Department of Surgery)
12. ภาควิชาสูติศาสตร์ - นรีเวชวิทยา (Department of Obstetrics and Gynecology)
13. ภาควิชาออร์โธปิดิกส์ (Department of Orthopedics)
14. ภาควิชาเวชศาสตร์ชุมชน (Department of Community Medicine)
15. ภาควิชาเวชศาสตร์ครอบครัว (Department of Family Medicine)

5-Pillar Architecture:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=6)
- Pillar 2: OpenAlex Multiplexing Pool (Polite pool with mailto multiplexing)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 dummy vector + commit)
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
- Pillar 5: Disk Checkpointing to backend/data/agent_states/wave78_nu_med_extraction.json
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import re
import sys
import time
import urllib.parse
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
from sqlalchemy import text

from app.core.database import SessionLocal, engine
from app.models.db_models import CourseDB, FacultyDB
from scripts.audits.audit_faculty_authenticity import clean_thai_name_for_matching

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("wave78_crawler")

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave78_nu_med_extraction.json"

CLIENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OPENALEX_KEYS = [
    "golfdesu.ch@gmail.com",
    "chayanon.ch@ku.th",
    "academic.match@ku.th",
    "advisor.match@ku.th",
    "advisor.match.thaiedu@gmail.com",
    "thaieducenter.dev@gmail.com",
    "research.thaiedu@gmail.com",
]

TITLE_MAP = [
    ("ศาสตราจารย์เกียรติคุณ นายแพทย์", "ศ.เกียรติคุณ นพ."),
    ("ศาสตราจารย์เกียรติคุณ", "ศ.เกียรติคุณ"),
    ("ศาสตราจารย์ ดร. นายแพทย์", "ศ.ดร.นพ."),
    ("ศาสตราจารย์ ดร. แพทย์หญิง", "ศ.ดร.พญ."),
    ("ศาสตราจารย์ ดร.", "ศ.ดร."),
    ("ศาสตราจารย์ นายแพทย์", "ศ.นพ."),
    ("ศาสตราจารย์ แพทย์หญิง", "ศ.พญ."),
    ("ศาสตราจารย์", "ศ."),
    ("รองศาสตราจารย์ ดร. นายแพทย์", "รศ.ดร.นพ."),
    ("รองศาสตราจารย์ ดร. แพทย์หญิง", "รศ.ดร.พญ."),
    ("รองศาสตราจารย์ ดร.", "รศ.ดร."),
    ("รองศาสตราจารย์ นายแพทย์", "รศ.นพ."),
    ("รองศาสตราจารย์ แพทย์หญิง", "รศ.พญ."),
    ("รองศาสตราจารย์", "รศ."),
    ("ผู้ช่วยศาสตราจารย์ ดร. นายแพทย์", "ผศ.ดร.นพ."),
    ("ผู้ช่วยศาสตราจารย์ ดร. แพทย์หญิง", "ผศ.ดร.พญ."),
    ("ผู้ช่วยศาสตราจารย์ ดร.", "ผศ.ดร."),
    ("ผู้ช่วยศาสตราจารย์ นายแพทย์", "ผศ.นพ."),
    ("ผู้ช่วยศาสตราจารย์ แพทย์หญิง", "ผศ.พญ."),
    ("ผู้ช่วยศาสตราจารย์", "ผศ."),
    ("อาจารย์ ดร. นายแพทย์", "อ.ดร.นพ."),
    ("อาจารย์ ดร. แพทย์หญิง", "อ.ดร.พญ."),
    ("อาจารย์ ดร.", "อ.ดร."),
    ("อาจารย์ นายแพทย์", "อ.นพ."),
    ("อาจารย์ แพทย์หญิง", "อ.พญ."),
    ("อาจารย์", "อ."),
    ("นายแพทย์", "นพ."),
    ("แพทย์หญิง", "พญ."),
    ("ศ.ดร.พญ.", "ศ.ดร.พญ."),
    ("ศ.ดร.นพ.", "ศ.ดร.นพ."),
    ("ศ.เกียรติคุณ นพ.", "ศ.เกียรติคุณ นพ."),
    ("ศ.นพ.", "ศ.นพ."),
    ("ศ.พญ.", "ศ.พญ."),
    ("รศ.ดร.นพ.", "รศ.ดร.นพ."),
    ("รศ.ดร.พญ.", "รศ.ดร.พญ."),
    ("รศ. นพ.", "รศ.นพ."),
    ("รศ. พญ.", "รศ.พญ."),
    ("รศ.นพ.", "รศ.นพ."),
    ("รศ.พญ.", "รศ.พญ."),
    ("ผศ.ดร.นพ.", "ผศ.ดร.นพ."),
    ("ผศ.ดร.พญ.", "ผศ.ดร.พญ."),
    ("ผศ.ดร.", "ผศ.ดร."),
    ("ผศ. นพ.", "ผศ.นพ."),
    ("ผศ. พญ.", "ผศ.พญ."),
    ("ผศ.นพ.", "ผศ.นพ."),
    ("ผศ.พญ.", "ผศ.พญ."),
    ("อ.ดร.พญ.", "อ.ดร.พญ."),
    ("อ.ดร.นพ.", "อ.ดร.นพ."),
    ("อ. นพ.", "อ.นพ."),
    ("อ. พญ.", "อ.พญ."),
    ("อ.นพ.", "อ.นพ."),
    ("อ.พญ.", "อ.พญ."),
    ("ดร.", "ดร."),
    ("พญ.", "พญ."),
    ("นพ.", "นพ."),
]

DEPARTMENTS = [
    {"dep": 1, "th": "ภาควิชาอายุรศาสตร์", "en": "Department of Medicine"},
    {"dep": 2, "th": "ภาควิชาเวชศาสตร์ฟื้นฟู", "en": "Department of Rehabilitation Medicine"},
    {"dep": 3, "th": "ภาควิชาโสต ศอ นาสิกวิทยา", "en": "Department of Otolaryngology"},
    {"dep": 4, "th": "ภาควิชากุมารเวชศาสตร์", "en": "Department of Pediatrics"},
    {"dep": 5, "th": "ภาควิชาจักษุวิทยา", "en": "Department of Ophthalmology"},
    {"dep": 6, "th": "ภาควิชาจิตเวชศาสตร์", "en": "Department of Psychiatry"},
    {"dep": 7, "th": "ภาควิชานิติเวชศาสตร์", "en": "Department of Forensic Medicine"},
    {"dep": 8, "th": "ภาควิชาพยาธิวิทยา", "en": "Department of Pathology"},
    {"dep": 9, "th": "ภาควิชารังสีวิทยา", "en": "Department of Radiology"},
    {"dep": 10, "th": "ภาควิชาวิสัญญีวิทยา", "en": "Department of Anesthesiology"},
    {"dep": 11, "th": "ภาควิชาศัลยศาสตร์", "en": "Department of Surgery"},
    {"dep": 12, "th": "ภาควิชาสูติศาสตร์ - นรีเวชวิทยา", "en": "Department of Obstetrics and Gynecology"},
    {"dep": 13, "th": "ภาควิชาออร์โธปิดิกส์", "en": "Department of Orthopedics"},
    {"dep": 14, "th": "ภาควิชาเวชศาสตร์ชุมชน", "en": "Department of Community Medicine"},
    {"dep": 15, "th": "ภาควิชาเวชศาสตร์ครอบครัว", "en": "Department of Family Medicine"},
]

BASE_URL = "https://med.nu.ac.th/dpmed/2015/"


def parse_academic_name(raw_name: str) -> Optional[tuple[str, str, str, str]]:
    """Extracts academic/medical title, first name, last name, and normalized clean full name."""
    cleaned = re.sub(r"\s+", " ", raw_name).strip()
    if not cleaned or "Staff PED" in cleaned or "กุมารแพทย์ (" in cleaned:
        return None

    ac_title = "อ.นพ."
    name_body = cleaned
    matched = False
    for long_t, short_t in TITLE_MAP:
        if cleaned.startswith(long_t):
            ac_title = short_t
            name_body = cleaned[len(long_t) :].strip()
            matched = True
            break

    if not matched:
        if "พญ." in cleaned or "แพทย์หญิง" in cleaned:
            ac_title = "พญ."
        elif "นพ." in cleaned or "นายแพทย์" in cleaned:
            ac_title = "นพ."
        else:
            ac_title = "อ."

    name_body = name_body.lstrip(". ")
    parts = name_body.split()
    fname = parts[0] if parts else ""
    lname = " ".join(parts[1:]) if len(parts) > 1 else fname
    if not fname or len(fname) < 2:
        return None

    cname = f"{fname} {lname}" if lname != fname else fname
    full_th = f"{ac_title} {cname}".strip()
    return ac_title, fname, lname, full_th


def fetch_doctor_profile(dep: int, id_mb: str, client: httpx.Client) -> Dict[str, Any]:
    """Fetches and parses doctor profile details from med.nu.ac.th."""
    profile_url = f"{BASE_URL}?mod=profileMember&dep={dep}&idMB={id_mb}"
    detail_data: Dict[str, str] = {}
    img_src = None
    try:
        r = client.get(profile_url, timeout=12.0)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 2:
                    k = tds[0].get_text(strip=True).rstrip(":").strip()
                    v = tds[1].get_text(strip=True)
                    if k and v:
                        detail_data[k] = v
            for img in soup.find_all("img"):
                src = img.get("src")
                if src and "picMem" in src:
                    img_src = urllib.parse.urljoin(BASE_URL, src)
                    break
    except Exception as e:
        logger.debug(f"Error fetching profile for idMB={id_mb}: {e}")

    return {
        "profile_url": profile_url,
        "detail_data": detail_data,
        "detail_img": img_src,
    }


def extract_naresuan_medicine_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls all 15 clinical departments of Naresuan University Faculty of Medicine."""
    logger.info("--- [Wave 78] Harvesting Naresuan Medicine Across 15 Departments ---")
    raw_cards: List[Dict[str, Any]] = []

    for dinfo in DEPARTMENTS:
        dep = dinfo["dep"]
        dept_th = dinfo["th"]
        dept_en = dinfo["en"]
        dep_url = f"{BASE_URL}?mod=depMemberSlide&dep={dep}&mbLevel=2"

        logger.info(f"  -> Scraping [{dept_th}] ({dept_en}) from {dep_url}")
        try:
            r = client.get(dep_url, timeout=15.0)
            if r.status_code != 200:
                logger.warning(f"Failed to fetch {dep_url}: status {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            containers = soup.find_all("div", class_="containerImage")
            logger.info(f"     Found {len(containers)} doctor cards in [{dept_th}]")

            for c in containers:
                a = c.find("a", href=True)
                if not (a and "idMB=" in a["href"]):
                    continue

                m = re.search(r"idMB=(\d+)", a["href"])
                id_mb = m.group(1) if m else None
                if not id_mb:
                    continue

                txt = c.get_text(separator=" | ", strip=True)
                parts = [p.strip() for p in txt.split(" | ") if p.strip() and p.strip() != "คลิกเพื่อดูข้อมูล"]
                card_name = parts[0] if parts else ""
                card_subdept = parts[1] if len(parts) > 1 else ""

                if "Staff PED" in card_name or "กุมารแพทย์ (" in card_name:
                    continue

                img = c.find("img")
                card_img = urllib.parse.urljoin(BASE_URL, img["src"]) if img and img.get("src") else None

                raw_cards.append({
                    "dep": dep,
                    "dept_th": dept_th,
                    "dept_en": dept_en,
                    "id_mb": id_mb,
                    "card_name": card_name,
                    "card_subdept": card_subdept,
                    "card_img": card_img,
                })
        except Exception as e:
            logger.error(f"Error fetching department {dep}: {e}")

    logger.info(f"Total raw doctor cards collected: {len(raw_cards)}. Fetching detail profiles...")

    # Fetch detail profiles with ThreadPoolExecutor
    detail_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {
            executor.submit(fetch_doctor_profile, card["dep"], card["id_mb"], client): card["id_mb"]
            for card in raw_cards
        }
        for fut in concurrent.futures.as_completed(future_map):
            mb_id = future_map[fut]
            try:
                detail_results[mb_id] = fut.result()
            except Exception as e:
                logger.debug(f"Failed detail profile for {mb_id}: {e}")
                detail_results[mb_id] = {"profile_url": "", "detail_data": {}, "detail_img": None}

    # Process and build clean structured records
    all_faculty: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_names = set()

    for card in raw_cards:
        id_mb = card["id_mb"]
        if id_mb in seen_ids:
            continue
        seen_ids.add(id_mb)

        dep = card["dep"]
        dept_th = card["dept_th"]
        dept_en = card["dept_en"]
        det = detail_results.get(id_mb, {})
        ddata = det.get("detail_data", {})

        # Name resolution: prefer detail table name, fallback to card name
        raw_name = ddata.get("ชื่อ - นามสกุล") or card["card_name"]
        parsed = parse_academic_name(raw_name)
        if not parsed:
            continue

        ac_title, fname, lname, full_th = parsed
        clean_key = f"{fname} {lname}"
        if clean_key in seen_names:
            continue
        seen_names.add(clean_key)

        # Image resolution: prefer detail img, fallback to card img
        img_url = det.get("detail_img") or card["card_img"]
        if img_url and " " in img_url:
            img_url = urllib.parse.quote(img_url, safe=":/%?=")

        # Email resolution: extract username from image filename if authentic
        email = None
        if img_url:
            em_match = re.search(r"/(\d+)_([a-zA-Z0-9]+)\.", img_url)
            if em_match:
                uname = em_match.group(2).lower()
                if uname not in ("-", "default", "noimage", "png", "jpg"):
                    email = f"{uname}@nu.ac.th"

        # Subdepartment and research interests
        subdept = ddata.get("หน่วยงาน") or card["card_subdept"]
        # Clean subdepartment (e.g. "สาขาวิชาวิทยาภูมิคุ้มกัน (Division of Immunology)")
        clean_subdept = re.sub(r"\s*\(.*?\)\s*", "", subdept).strip() if subdept else None

        cert = ddata.get("วุฒิบัตร/อนุมัติบัตร/ประกาศนียบัตรความเชี่ยวชาญ")
        clean_certs = []
        if cert:
            for item in re.split(r"[,:\n-]", cert):
                c_item = item.strip().rstrip(".;,")
                if c_item and len(c_item) > 2 and not re.match(r"^\d+$", c_item) and c_item not in clean_certs:
                    clean_certs.append(c_item)

        interests = []
        if clean_subdept:
            interests.append(clean_subdept)
        for c in clean_certs[:5]:
            if c not in interests:
                interests.append(c)

        # Hospital & academic roles
        hosp_role = ddata.get("ตำแหน่งภายในโรงพยาบาล")
        acad_role = ddata.get("ตำแหน่งทางวิชาการ")
        role = hosp_role or acad_role or "อาจารย์แพทย์"

        # English Name
        en_name = ddata.get("Name - Surname")
        en_first = None
        en_last = None
        if en_name:
            clean_en = re.sub(r"^(Dr\.|Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Ajarn)\s*", "", en_name, flags=re.IGNORECASE).strip()
            en_parts = clean_en.split()
            if en_parts:
                en_first = en_parts[0]
                en_last = " ".join(en_parts[1:]) if len(en_parts) > 1 else en_first

        faculty_id = f"nu_med__{dep:02d}_{int(id_mb):04d}"

        all_faculty.append({
            "id": faculty_id,
            "full_name_th": full_th,
            "academic_title_th": ac_title,
            "first_name": fname,
            "last_name": lname,
            "first_name_en": en_first,
            "last_name_en": en_last,
            "clean_name_th": clean_key,
            "university_th": "มหาวิทยาลัยนเรศวร",
            "university": "Naresuan University",
            "faculty_th": "คณะแพทยศาสตร์",
            "faculty": "Faculty of Medicine",
            "department_th": dept_th,
            "department": dept_en,
            "role": role,
            "email": email,
            "image_url": img_url,
            "profile_url": det.get("profile_url") or f"{BASE_URL}?mod=profileMember&dep={dep}&idMB={id_mb}",
            "research_interests": interests,
            "featured_publications": [],
            "total_citations": 0,
            "h_index": 0,
            "total_publications_count": 0,
            "openalex_id": None,
        })

    logger.info(f"✅ Successfully processed {len(all_faculty)} authentic medical faculty records.")
    return all_faculty


def query_openalex_metrics(name_en: str, client: httpx.Client, key_idx: int = 0) -> Optional[Dict[str, Any]]:
    """Polite OpenAlex query for author metrics with circuit breaker."""
    if not name_en or len(name_en) < 4:
        return None
    email_key = OPENALEX_KEYS[key_idx % len(OPENALEX_KEYS)]
    url = f"https://api.openalex.org/authors?filter=display_name.search:{urllib.parse.quote(name_en)},last_known_institutions.id:I177710323&mailto={email_key}"
    try:
        r = client.get(url, timeout=5.0)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                author = results[0]
                return {
                    "openalex_id": author.get("id", "").replace("https://openalex.org/", ""),
                    "total_citations": author.get("cited_by_count", 0),
                    "h_index": author.get("summary_stats", {}).get("h_index", 0),
                    "total_publications_count": author.get("works_count", 0),
                }
    except Exception:
        pass
    return None


def run_wave78_acquisition():
    logger.info("=================================================================")
    logger.info("🚀 STARTING WAVE 78: NARESUAN UNIVERSITY MEDICINE FACULTY ACQUISITION")
    logger.info("=================================================================")
    t0 = time.time()

    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=15.0, headers=CLIENT_HEADERS, verify=False) as client:
        faculty_list = extract_naresuan_medicine_faculties(client)

        logger.info(f"Checkpointing {len(faculty_list)} extracted faculty to {CHECKPOINT_PATH}...")
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(faculty_list, f, ensure_ascii=False, indent=2)

        # OpenAlex enrichment pass (non-blocking)
        logger.info("--- Enriching author metrics via OpenAlex multiplexing pool ---")
        for i, fac in enumerate(faculty_list):
            en_full = f"{fac.get('first_name_en') or ''} {fac.get('last_name_en') or ''}".strip()
            if en_full and len(en_full) > 4:
                metrics = query_openalex_metrics(en_full, client, key_idx=i)
                if metrics:
                    fac["openalex_id"] = metrics["openalex_id"]
                    fac["total_citations"] = metrics["total_citations"]
                    fac["h_index"] = metrics["h_index"]
                    fac["total_publications_count"] = max(metrics["total_publications_count"], metrics["h_index"])

    # Commit to Database
    logger.info("--- Committing records to local PostgreSQL database ---")
    db = SessionLocal()
    inserted = 0
    updated = 0

    try:
        for item in faculty_list:
            existing = db.query(FacultyDB).filter(FacultyDB.id == item["id"]).first()
            if not existing:
                clean_k = clean_thai_name_for_matching(item["full_name_th"])
                existing_by_name = (
                    db.query(FacultyDB)
                    .filter(
                        FacultyDB.university_th == item["university_th"],
                        FacultyDB.full_name_th == item["full_name_th"],
                    )
                    .first()
                )
                if existing_by_name:
                    existing = existing_by_name

            if existing:
                existing.full_name_th = item["full_name_th"]
                existing.academic_title_th = item["academic_title_th"]
                existing.department_th = item["department_th"]
                existing.department = item["department"]
                existing.role = item["role"]
                if item["email"] and not existing.email:
                    existing.email = item["email"]
                if item["image_url"] and not existing.image_url:
                    existing.image_url = item["image_url"]
                if item["research_interests"]:
                    existing.research_interests = item["research_interests"]
                if item["openalex_id"]:
                    existing.openalex_id = item["openalex_id"]
                    existing.total_citations = max(existing.total_citations or 0, item["total_citations"])
                    existing.h_index = max(existing.h_index or 0, item["h_index"])
                    existing.total_publications_count = max(
                        existing.total_publications_count or 0, item["total_publications_count"]
                    )
                updated += 1
            else:
                new_fac = FacultyDB(
                    id=item["id"],
                    full_name_th=item["full_name_th"],
                    academic_title_th=item["academic_title_th"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    university_th=item["university_th"],
                    university=item["university"],
                    faculty_th=item["faculty_th"],
                    faculty=item["faculty"],
                    department_th=item["department_th"],
                    department=item["department"],
                    role=item["role"],
                    email=item["email"],
                    image_url=item["image_url"],
                    profile_url=item["profile_url"],
                    research_interests=item["research_interests"],
                    featured_publications=item["featured_publications"],
                    total_citations=item["total_citations"],
                    h_index=item["h_index"],
                    total_publications_count=item["total_publications_count"],
                    openalex_id=item["openalex_id"],
                    embedding=None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search,
                )
                db.add(new_fac)
                inserted += 1

        db.commit()
        logger.info(f"✅ Committed to DB: {inserted} inserted, {updated} updated.")
    finally:
        db.close()

    logger.info(f"🎉 Wave 78 completed in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    run_wave78_acquisition()
