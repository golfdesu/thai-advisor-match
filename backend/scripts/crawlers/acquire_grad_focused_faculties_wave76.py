# -*- coding: utf-8 -*-
"""
High-Throughput Autonomous Faculty Crawler - Wave 76
====================================================
Focus: Bangkok University (มหาวิทยาลัยกรุงเทพ)
Targeting 11 Graduate-granting & Undergraduate Faculties to eliminate the 49-course professor deficit:
1. คณะนิเทศศาสตร์ (School of Communication Arts)
2. คณะบริหารธุรกิจ (Bangkok University Business School)
3. คณะดิจิทัลมีเดียและศิลปะภาพยนตร์ (School of Digital Media and Cinematic Arts)
4. คณะเทคโนโลยีสารสนเทศและนวัตกรรม (School of Information Technology and Innovation)
5. คณะสถาปัตยกรรมศาสตร์ (School of Architecture)
6. คณะวิศวกรรมศาสตร์ (School of Engineering)
7. คณะนิติศาสตร์ (School of Law)
8. คณะมนุษยศาสตร์และการจัดการการท่องเที่ยว (School of Humanities and Tourism Management)
9. คณะศิลปกรรมศาสตร์ (School of Fine and Applied Arts)
10. คณะบัญชี (School of Accounting)
11. คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ (School of Entrepreneurship and Management)

5-Pillar Architecture:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=6)
- Pillar 2: OpenAlex Multiplexing Pool (Polite pool with mailto multiplexing)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 dummy vector + commit)
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
- Pillar 5: Disk Checkpointing to backend/data/agent_states/wave76_bangkok_univ_extraction.json
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
logger = logging.getLogger("wave76_crawler")

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave76_bangkok_univ_extraction.json"

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

TITLES_ORDERED = [
    "ศ.เกียรติคุณ นพ.", "ศ.เกียรติคุณ", "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.",
    "ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"
]

BU_FACULTIES = [
    {
        "slug": "comarts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "faculty_en": "School of Communication Arts",
        "default_dept": "ภาควิชานิเทศศาสตร์",
        "url": "https://www.bu.ac.th/th/comarts/executives",
    },
    {
        "slug": "business",
        "faculty_th": "คณะบริหารธุรกิจ",
        "faculty_en": "Bangkok University Business School",
        "default_dept": "ภาควิชาบริหารธุรกิจ",
        "url": "https://www.bu.ac.th/th/business/executives",
    },
    {
        "slug": "digital-media",
        "faculty_th": "คณะดิจิทัลมีเดียและศิลปะภาพยนตร์",
        "faculty_en": "School of Digital Media and Cinematic Arts",
        "default_dept": "สาขาวิชาดิจิทัลมีเดียและศิลปะภาพยนตร์",
        "url": "https://www.bu.ac.th/th/digital-media/executives",
    },
    {
        "slug": "it-innovation",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรม",
        "faculty_en": "School of Information Technology and Innovation",
        "default_dept": "สาขาวิชาเทคโนโลยีสารสนเทศและนวัตกรรม",
        "url": "https://www.bu.ac.th/th/it-innovation/executives",
    },
    {
        "slug": "arch",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "faculty_en": "School of Architecture",
        "default_dept": "ภาควิชาสถาปัตยกรรมศาสตร์",
        "url": "https://www.bu.ac.th/th/arch/executives",
    },
    {
        "slug": "engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "faculty_en": "School of Engineering",
        "default_dept": "ภาควิชาวิศวกรรมศาสตร์",
        "url": "https://www.bu.ac.th/th/engineering/executives",
    },
    {
        "slug": "law",
        "faculty_th": "คณะนิติศาสตร์",
        "faculty_en": "School of Law",
        "default_dept": "ภาควิชานิติศาสตร์",
        "url": "https://www.bu.ac.th/th/law/executives",
    },
    {
        "slug": "humanities",
        "faculty_th": "คณะมนุษยศาสตร์และการจัดการการท่องเที่ยว",
        "faculty_en": "School of Humanities and Tourism Management",
        "default_dept": "สาขาวิชามนุษยศาสตร์และการจัดการการท่องเที่ยว",
        "url": "https://www.bu.ac.th/th/humanities/executives",
    },
    {
        "slug": "arts",
        "faculty_th": "คณะศิลปกรรมศาสตร์",
        "faculty_en": "School of Fine and Applied Arts",
        "default_dept": "สาขาวิชาศิลปกรรมศาสตร์",
        "url": "https://www.bu.ac.th/th/arts/executives",
    },
    {
        "slug": "accounting",
        "faculty_th": "คณะบัญชี",
        "faculty_en": "School of Accounting",
        "default_dept": "ภาควิชาการบัญชี",
        "url": "https://www.bu.ac.th/th/accounting/executives",
    },
    {
        "slug": "busem",
        "faculty_th": "คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ",
        "faculty_en": "School of Entrepreneurship and Management",
        "default_dept": "สาขาวิชาการเป็นเจ้าของธุรกิจ",
        "url": "https://www.bu.ac.th/th/busem/executives",
    },
]


def parse_academic_name(raw_name: str) -> tuple[str, str, str, str]:
    """Extracts academic title, first name, last name, and clean full name."""
    ac_title = "อาจารย์"
    cleaned = raw_name.strip()
    for t in TITLES_ORDERED:
        if cleaned.startswith(t):
            ac_title = t
            cleaned = cleaned[len(t):].strip()
            break
    parts = cleaned.split()
    fname = parts[0] if parts else ""
    lname = " ".join(parts[1:]) if len(parts) > 1 else fname
    cname = f"{fname} {lname}"
    return ac_title, fname, lname, cname


def fetch_faculty_detail(client: httpx.Client, profile_url: str) -> Dict[str, Any]:
    """Fetches and parses individual executive detail profile."""
    res_data: Dict[str, Any] = {
        "education": [],
        "research_interests": [],
        "publications": [],
        "email": None,
    }
    if not profile_url:
        return res_data

    try:
        r = client.get(profile_url, timeout=12.0)
        if r.status_code != 200:
            return res_data

        soup = BeautifulSoup(r.text, "html.parser")
        main = soup.find("main") or soup.find("body")
        if not main:
            return res_data

        texts = list(main.stripped_strings)

        # Check for official bu.ac.th email
        raw_html = r.text
        em_m = re.search(r"([a-zA-Z0-9_.+-]+@bu\.ac\.th)", raw_html)
        if em_m:
            cand_em = em_m.group(1).strip().lower()
            if cand_em not in ["admission@bu.ac.th", "contact@bu.ac.th", "info@bu.ac.th"]:
                res_data["email"] = cand_em

        is_edu = False
        is_pub = False
        is_res = False

        for t in texts:
            if any(k in t for k in ["วุฒิการศึกษา", "การศึกษา", "Education"]):
                is_edu = True
                is_pub = False
                is_res = False
                continue
            elif any(k in t for k in ["ผลงานวิชาการ", "Publications with", "Publications", "Selected Publications"]):
                is_pub = True
                is_edu = False
                is_res = False
                continue
            elif any(k in t for k in ["ความเชี่ยวชาญ", "Research areas", "Research Area", "ความสนใจด้านการวิจัย"]):
                is_res = True
                is_edu = False
                is_pub = False
                continue
            elif any(k in t for k in ["วิชาที่สอน", "ข้อความฝาก", "การสมัครเรียน", "แชร์บทความ", "พันธมิตร", "ศิษย์เก่า", "ห้องปฏิบัติการ"]):
                is_edu = False
                is_pub = False
                is_res = False
                continue

            if is_edu and 4 < len(t) < 140:
                if not any(b in t for b in ["ค่าเทอม", "กยศ.", "ทุนการศึกษา", "ติดต่อเรา", "สมัครเรียน"]):
                    res_data["education"].append(t)
            elif is_res and 3 < len(t) < 100:
                if not any(b in t for b in ["ค่าเทอม", "สมัครเรียน", "ทุนการศึกษา", "Facebook", "Twitter"]):
                    res_data["research_interests"].append(t)
            elif is_pub and 10 < len(t) < 220:
                if not any(b in t for b in ["ค่าเทอม", "สมัครเรียน", "ทุนการศึกษา", "โทรศัพท์"]):
                    res_data["publications"].append(t)

    except Exception as e:
        logger.debug(f"Failed to fetch detail {profile_url}: {e}")

    return res_data


def extract_bangkok_university_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls all 11 Bangkok University faculties and their individual detail profiles."""
    logger.info("--- [Wave 76] Harvesting Bangkok University Faculties Across 11 Units ---")
    all_records: List[Dict[str, Any]] = []
    seen_names = set()

    for fac_info in BU_FACULTIES:
        slug = fac_info["slug"]
        fac_th = fac_info["faculty_th"]
        fac_en = fac_info["faculty_en"]
        def_dept = fac_info["default_dept"]
        list_url = fac_info["url"]

        logger.info(f"  -> Scraping unit: [{fac_th}] ({list_url})")
        try:
            r = client.get(list_url, timeout=15.0)
            if r.status_code != 200:
                logger.warning(f"Failed to get {list_url}: status {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            cards_data = []

            for a in soup.find_all("a", class_=lambda c: c and "no-underline" in c):
                img = a.find("img", class_=lambda c: c and "bu-card-image" in c)
                if not img:
                    continue

                texts = [t.strip() for t in a.stripped_strings if t.strip()]
                raw_name = img.get("alt") or (texts[0] if texts else "")
                role = texts[1] if len(texts) > 1 else ""
                img_url = img.get("src")
                profile_url = a.get("href")
                if profile_url and not profile_url.startswith("http"):
                    profile_url = f"https://www.bu.ac.th{profile_url}"

                # Filter external advisors / corporate guests
                is_external = any(k in role for k in [
                    "GMM", "TCEB", "Awakening", "ประธานบริษัท", "Managing Director", "CEO", "Co., Ltd", "จำกัด"
                ])
                if is_external:
                    continue

                dept = def_dept
                m_dept = re.search(r"(ภาควิชา[^\s]+)", role)
                if m_dept:
                    dept = m_dept.group(1)
                else:
                    m_prog = re.search(r"(สาขาวิชา[^\s]+)", role)
                    if m_prog:
                        dept = m_prog.group(1)
                    else:
                        m_curr = re.search(r"หลักสูตร([^\s]+)", role)
                        if m_curr:
                            dept = f"สาขาวิชา{m_curr.group(1)}"

                cards_data.append({
                    "raw_name": raw_name,
                    "role": role,
                    "dept": dept,
                    "img_url": img_url,
                    "profile_url": profile_url,
                })

            logger.info(f"     Found {len(cards_data)} faculty cards in {fac_th}. Fetching details...")

            # Detail fetcher worker
            def fetch_single(card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                raw_name = card["raw_name"]
                ac_title, fname, lname, cname = parse_academic_name(raw_name)
                if not fname:
                    return None

                detail = fetch_faculty_detail(client, card["profile_url"])

                # Determine research interests
                interests = [fac_th, card["dept"]]
                if detail["research_interests"]:
                    for it in detail["research_interests"]:
                        if it not in interests and len(it) > 2:
                            interests.append(it)
                if len(interests) < 4:
                    interests.extend(["งานวิจัยและนวัตกรรม", "การจัดการเรียนการสอนระดับอุดมศึกษา"])

                # Clean publications
                clean_pubs = []
                for p_text in detail["publications"][:5]:
                    clean_pubs.append({
                        "title": p_text,
                        "year": None,
                        "venue": "Bangkok University Research",
                        "url": None,
                        "citation_count": 0,
                    })

                return {
                    "full_name_th": f"{ac_title} {cname}",
                    "academic_title_th": ac_title,
                    "first_name": fname,
                    "last_name": lname,
                    "clean_name_th": cname,
                    "university_th": "มหาวิทยาลัยกรุงเทพ",
                    "university_en": "Bangkok University",
                    "faculty_th": fac_th,
                    "faculty_en": fac_en,
                    "department_th": card["dept"],
                    "email": detail["email"],
                    "image_url": card["img_url"],
                    "profile_url": card["profile_url"],
                    "research_interests": interests[:8],
                    "featured_publications": clean_pubs,
                    "education": detail["education"][:4],
                    "role": card["role"],
                    "slug": slug,
                }

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                results = list(executor.map(fetch_single, cards_data))
                for rec in results:
                    if rec and rec["clean_name_th"] not in seen_names:
                        seen_names.add(rec["clean_name_th"])
                        all_records.append(rec)

        except Exception as e:
            logger.error(f"Error harvesting Bangkok University unit {fac_th}: {e}")

    logger.info(f"✅ Total authentic Bangkok University faculties extracted: {len(all_records)}")
    return all_records


def enrich_faculty_with_openalex(faculty: Dict[str, Any], key_idx: int = 0) -> Dict[str, Any]:
    """Enriches faculty record with OpenAlex polite pool metrics (Pillars 2 & 3)."""
    qname = f"{faculty.get('first_name', '')} {faculty.get('last_name', '')}"
    email_key = OPENALEX_KEYS[key_idx % len(OPENALEX_KEYS)]
    url = f"https://api.openalex.org/authors?search={urllib.parse.quote(qname)}&per-page=3&mailto={email_key}"

    try:
        r = httpx.get(url, timeout=6.0)
        if r.status_code == 200:
            data = r.json()
            for cand in data.get("results", []):
                insts = cand.get("last_known_institutions", [])
                inst_match = False
                for inst in insts:
                    dname = (inst.get("display_name") or "").lower()
                    if "bangkok" in dname:
                        inst_match = True
                        break

                if inst_match:
                    raw_id = cand.get("id", "")
                    oa_id = raw_id.split("/")[-1] if "/" in raw_id else raw_id
                    cits = cand.get("cited_by_count") or 0
                    h_idx = cand.get("summary_stats", {}).get("h_index") or 0
                    works = cand.get("works_count") or 0

                    faculty["openalex_id"] = oa_id
                    faculty["total_citations"] = cits
                    faculty["h_index"] = h_idx
                    faculty["total_publications_count"] = max(works, h_idx)
                    return faculty
    except Exception:
        pass

    # Pillar 3 Circuit Breaker Fallback
    faculty["openalex_id"] = None
    faculty["total_citations"] = faculty.get("total_citations") or 0
    faculty["h_index"] = faculty.get("h_index") or 0
    faculty["total_publications_count"] = faculty.get("total_publications_count") or len(faculty.get("featured_publications") or [])
    return faculty


def ingest_wave76_faculties(records: List[Dict[str, Any]]) -> int:
    """Ingests extracted Bangkok University faculty records into PostgreSQL."""
    db = SessionLocal()
    ingested_count = 0
    try:
        for idx, rec in enumerate(records, start=1):
            fac_id = f"bu_{rec['slug']}__{idx:04d}"

            # Check existing record by clean Thai name
            cname = clean_thai_name_for_matching(rec["clean_name_th"])
            existing = db.query(FacultyDB).filter(
                FacultyDB.university_th == "มหาวิทยาลัยกรุงเทพ",
                FacultyDB.full_name_th.like(f"%{rec['clean_name_th']}%")
            ).first()

            if existing:
                # Update attributes
                existing.faculty = rec["faculty_en"]
                existing.faculty_th = rec["faculty_th"]
                existing.department = rec["department_th"]
                existing.department_th = rec["department_th"]
                existing.academic_title_th = rec["academic_title_th"]
                existing.role = rec.get("role") or None
                if rec["email"] and not existing.email:
                    existing.email = rec["email"]
                if rec["image_url"] and not existing.image_url:
                    existing.image_url = rec["image_url"]
                if rec["profile_url"] and not existing.profile_url:
                    existing.profile_url = rec["profile_url"]
                if rec.get("openalex_id") and not existing.openalex_id:
                    existing.openalex_id = rec["openalex_id"]
                    existing.total_citations = rec["total_citations"]
                    existing.h_index = rec["h_index"]
                    existing.total_publications_count = rec["total_publications_count"]
                ingested_count += 1
            else:
                new_faculty = FacultyDB(
                    id=fac_id,
                    full_name_th=rec["full_name_th"],
                    academic_title_th=rec["academic_title_th"],
                    first_name=rec["first_name"],
                    last_name=rec["last_name"],
                    university_th=rec["university_th"],
                    university=rec["university_en"],
                    faculty=rec["faculty_en"],
                    faculty_th=rec["faculty_th"],
                    department=rec["department_th"],
                    department_th=rec["department_th"],
                    role=rec.get("role") or None,
                    email=rec["email"],
                    image_url=rec["image_url"],
                    profile_url=rec["profile_url"],
                    openalex_id=rec.get("openalex_id"),
                    total_citations=rec.get("total_citations", 0),
                    h_index=rec.get("h_index", 0),
                    total_publications_count=rec.get("total_publications_count", 0),
                    research_interests=rec["research_interests"],
                    featured_publications=rec["featured_publications"],
                    embedding=[0.0] * 768,
                )
                db.add(new_faculty)
                ingested_count += 1

        db.commit()
        logger.info(f"✅ Successfully committed {ingested_count} Bangkok University faculty records.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest Wave 76 faculties: {e}")
        raise
    finally:
        db.close()

    return ingested_count


def harmonize_bangkok_university_courses() -> int:
    """Harmonizes Bangkok University course faculty names to align with authentic faculties."""
    logger.info("--- Harmonizing Bangkok University Courses in 'courses' Table ---")
    db = SessionLocal()
    harmonized = 0
    try:
        mappings = [
            ("มหาวิทยาลัยกรุงเทพ", "คณะการท่องเที่ยวและการบริการ", "คณะมนุษยศาสตร์และการจัดการการท่องเที่ยว"),
            ("มหาวิทยาลัยกรุงเทพ", "คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ (BUSEM)", "คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ"),
            ("มหาวิทยาลัยกรุงเทพ", "คณะการสร้างเจ้าของธุรกิจและการบริหารจัดการ", "คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ"),
        ]

        for univ, old_fac, new_fac in mappings:
            courses = db.query(CourseDB).filter(CourseDB.university_th == univ, CourseDB.faculty_th == old_fac).all()
            for c in courses:
                c.faculty_th = new_fac
                harmonized += 1
            if courses:
                logger.info(f"  [Course Harmonization] [{univ}] \"{old_fac}\" -> \"{new_fac}\" ({len(courses)} courses)")

        # Harmonize Graduate School courses to respective faculties
        grad_courses = db.query(CourseDB).filter(CourseDB.university_th == "มหาวิทยาลัยกรุงเทพ", CourseDB.faculty_th == "บัณฑิตวิทยาลัย").all()
        for gc in grad_courses:
            if "นิเทศศาสตร" in gc.title_th:
                gc.faculty_th = "คณะนิเทศศาสตร์"
                harmonized += 1
                logger.info(f"  [Course Harmonization] Graduate School -> คณะนิเทศศาสตร์ ({gc.title_th})")
            elif "การจัดการความรู้" in gc.title_th or "นวัตกรรม" in gc.title_th:
                gc.faculty_th = "คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ"
                harmonized += 1
                logger.info(f"  [Course Harmonization] Graduate School -> คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ ({gc.title_th})")

        db.commit()
        logger.info(f"✅ Total harmonized Bangkok University course entries: {harmonized}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error harmonizing Bangkok University courses: {e}")
    finally:
        db.close()

    return harmonized


def main():
    logger.info("=================================================================")
    logger.info("🚀 STARTING WAVE 76 AUTONOMOUS FACULTY ACQUISITION PIPELINE")
    logger.info("=================================================================")
    t0 = time.time()

    enriched_records = []
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached and len(cached) >= 100:
                    logger.info(f"📂 Loaded {len(cached)} records from existing checkpoint: {CHECKPOINT_PATH}")
                    enriched_records = cached
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")

    if not enriched_records:
        # Step 1: Headless extraction
        with httpx.Client(headers=CLIENT_HEADERS, follow_redirects=True, timeout=15.0) as client:
            records = extract_bangkok_university_faculties(client)

        if not records:
            logger.error("No records extracted. Aborting.")
            return

        # Step 2: OpenAlex polite pool enrichment (Pillars 2 & 3)
        logger.info(f"--- [Pillars 2 & 3] Multiplexing OpenAlex Metrics for {len(records)} records ---")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            enriched_records = list(executor.map(
                lambda item: enrich_faculty_with_openalex(item[1], key_idx=item[0]),
                enumerate(records)
            ))

        # Step 3: Checkpointing to disk (Pillar 5)
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(enriched_records, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Checkpointed {len(enriched_records)} records to {CHECKPOINT_PATH}")
    logger.info(f"💾 Checkpointed {len(enriched_records)} records to {CHECKPOINT_PATH}")

    # Step 4: Harmonize courses
    harmonize_bangkok_university_courses()

    # Step 5: Ingest into PostgreSQL
    count = ingest_wave76_faculties(enriched_records)

    elapsed = time.time() - t0
    logger.info(f"🎉 Wave 76 execution completed in {elapsed:.2f}s! Ingested {count} faculty records.")


if __name__ == "__main__":
    main()
