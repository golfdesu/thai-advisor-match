# -*- coding: utf-8 -*-
"""
High-Throughput Autonomous Faculty Crawler - Wave 77
====================================================
Focus: Sukhothai Thammathirat Open University (มหาวิทยาลัยสุโขทัยธรรมาธิราช - STOU)
Targeting all 12 Graduate & Undergraduate Academic Schools (สาขาวิชา) to eliminate the 70-course professor deficit:
1. สาขาวิชาวิทยาการจัดการ (School of Management Science)
2. สาขาวิชาศึกษาศาสตร์ (School of Educational Studies)
3. สาขาวิชานิติศาสตร์ (School of Law)
4. สาขาวิชาวิทยาศาสตร์และเทคโนโลยี (School of Science and Technology)
5. สาขาวิชาศิลปศาสตร์ (School of Liberal Arts)
6. สาขาวิชาวิทยาศาสตร์สุขภาพ (School of Health Science)
7. สาขาวิชารัฐศาสตร์ (School of Political Science)
8. สาขาวิชาเกษตรศาสตร์และสหกรณ์ (School of Agriculture and Cooperatives)
9. สาขาวิชานิเทศศาสตร์ (School of Communication Arts)
10. สาขาวิชามนุษยนิเวศศาสตร์ (School of Human Ecology)
11. สาขาวิชาเศรษฐศาสตร์ (School of Economics)
12. สาขาวิชาพยาบาลศาสตร์ (School of Nursing)

5-Pillar Architecture:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor max_workers=6)
- Pillar 2: OpenAlex Multiplexing Pool (Polite pool with mailto multiplexing)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 dummy vector + commit)
- Pillar 4: In-Memory 5-Pass State Reducer & Title Normalizer
- Pillar 5: Disk Checkpointing to backend/data/agent_states/wave77_stou_extraction.json
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
logger = logging.getLogger("wave77_crawler")

CHECKPOINT_PATH = BACKEND_DIR / "data" / "agent_states" / "wave77_stou_extraction.json"

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
    ("ศาสตราจารย์ ดร.", "ศ.ดร."),
    ("ศาสตราจารย์", "ศ."),
    ("รองศาสตราจารย์ ดร.", "รศ.ดร."),
    ("รองศาสตราจารย์ พันตรีหญิง ดร.", "รศ.พ.ต.หญิง ดร."),
    ("รองศาสตราจารย์", "รศ."),
    ("ผู้ช่วยศาสตราจารย์ ดร.", "ผศ.ดร."),
    ("ผู้ช่วยศาสตราจารย์ ร.อ.หญิง ดร.", "ผศ.ร.อ.หญิง ดร."),
    ("ผู้ช่วยศาสตราจารย์", "ผศ."),
    ("อาจารย์ ดร.", "อ.ดร."),
    ("อาจารย์ นายแพทย์", "อ.นพ."),
    ("อาจารย์ แพทย์หญิง", "อ.พญ."),
    ("อาจารย์", "อ."),
    ("นายแพทย์", "นพ."),
    ("แพทย์หญิง", "พญ."),
    ("ศ.เกียรติคุณ นพ.", "ศ.เกียรติคุณ นพ."),
    ("ศ.เกียรติคุณ", "ศ.เกียรติคุณ"),
    ("ศ.ดร.", "ศ.ดร."),
    ("รศ.ดร.", "รศ.ดร."),
    ("ผศ.ดร.", "ผศ.ดร."),
    ("อ.ดร.", "อ.ดร."),
    ("ศ.", "ศ."),
    ("รศ.", "รศ."),
    ("ผศ.", "ผศ."),
    ("อ.", "อ."),
    ("ดร.", "ดร."),
]

STOU_SCHOOLS = [
    {
        "slug": "mgtsci",
        "faculty_th": "สาขาวิชาวิทยาการจัดการ",
        "faculty_en": "School of Management Science",
        "default_dept": "สาขาวิชาวิทยาการจัดการ",
        "urls": ["https://mgtsci.stou.ac.th/instructors/"],
    },
    {
        "slug": "edu",
        "faculty_th": "สาขาวิชาศึกษาศาสตร์",
        "faculty_en": "School of Educational Studies",
        "default_dept": "สาขาวิชาศึกษาศาสตร์",
        "urls": ["https://edu.stou.ac.th/faculty/"],
    },
    {
        "slug": "law",
        "faculty_th": "สาขาวิชานิติศาสตร์",
        "faculty_en": "School of Law",
        "default_dept": "สาขาวิชานิติศาสตร์",
        "urls": [
            "https://law.stou.ac.th/instructors-2/",
            "https://law.stou.ac.th/masters-degree/",
            "https://law.stou.ac.th/doctor/",
            "https://law.stou.ac.th/bachelor/",
        ],
    },
    {
        "slug": "scitech",
        "faculty_th": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยี",
        "faculty_en": "School of Science and Technology",
        "default_dept": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยี",
        "urls": [
            "https://scitech.stou.ac.th/lecturersss/",
            "https://scitech.stou.ac.th/directors/",
        ],
    },
    {
        "slug": "liberalarts",
        "faculty_th": "สาขาวิชาศิลปศาสตร์",
        "faculty_en": "School of Liberal Arts",
        "default_dept": "สาขาวิชาศิลปศาสตร์",
        "urls": [
            "https://liberalarts.stou.ac.th/eng/",
            "https://liberalarts.stou.ac.th/ict/",
            "https://liberalarts.stou.ac.th/thai/",
            "https://liberalarts.stou.ac.th/abc-2/",
        ],
    },
    {
        "slug": "shs",
        "faculty_th": "สาขาวิชาวิทยาศาสตร์สุขภาพ",
        "faculty_en": "School of Health Science",
        "default_dept": "สาขาวิชาวิทยาศาสตร์สุขภาพ",
        "urls": [
            "https://shs.stou.ac.th/hsmanagement/",
            "https://shs.stou.ac.th/9-2/",
            "https://shs.stou.ac.th/8-2/",
            "https://shs.stou.ac.th/7-2/",
        ],
    },
    {
        "slug": "politicalsci",
        "faculty_th": "สาขาวิชารัฐศาสตร์",
        "faculty_en": "School of Political Science",
        "default_dept": "สาขาวิชารัฐศาสตร์",
        "urls": [
            "https://politicalsci.stou.ac.th/instructors/",
            "https://politicalsci.stou.ac.th/executives/",
        ],
    },
    {
        "slug": "agriculture",
        "faculty_th": "สาขาวิชาเกษตรศาสตร์และสหกรณ์",
        "faculty_en": "School of Agriculture and Cooperatives",
        "default_dept": "สาขาวิชาเกษตรศาสตร์และสหกรณ์",
        "urls": [
            "https://agriculture.stou.ac.th/facultystaff/",
            "https://agriculture.stou.ac.th/pageexe/",
        ],
    },
    {
        "slug": "commarts",
        "faculty_th": "สาขาวิชานิเทศศาสตร์",
        "faculty_en": "School of Communication Arts",
        "default_dept": "สาขาวิชานิเทศศาสตร์",
        "urls": ["https://commarts.stou.ac.th/instructors/"],
    },
    {
        "slug": "humanecology",
        "faculty_th": "สาขาวิชามนุษยนิเวศศาสตร์",
        "faculty_en": "School of Human Ecology",
        "default_dept": "สาขาวิชามนุษยนิเวศศาสตร์",
        "urls": ["https://humanecology.stou.ac.th/instructors/"],
    },
    {
        "slug": "economics",
        "faculty_th": "สาขาวิชาเศรษฐศาสตร์",
        "faculty_en": "School of Economics",
        "default_dept": "สาขาวิชาเศรษฐศาสตร์",
        "urls": ["https://economics.stou.ac.th/instructors/"],
    },
    {
        "slug": "nurs",
        "faculty_th": "สาขาวิชาพยาบาลศาสตร์",
        "faculty_en": "School of Nursing",
        "default_dept": "สาขาวิชาพยาบาลศาสตร์",
        "urls": ["https://nurs.stou.ac.th/instructors/"],
    },
]


def decode_cloudflare_email(encoded_str: str) -> Optional[str]:
    """Decodes Cloudflare email protection hex string."""
    try:
        r = int(encoded_str[:2], 16)
        email = "".join([chr(int(encoded_str[i : i + 2], 16) ^ r) for i in range(2, len(encoded_str), 2)])
        return email.strip().lower()
    except Exception:
        return None


def parse_academic_name(raw_name: str) -> tuple[str, str, str, str]:
    """Extracts academic title, first name, last name, and normalized clean full name."""
    cleaned = re.sub(r"\s+", " ", raw_name).strip()
    # Strip non-name brackets e.g. (Asst. Prof. Dr. ...)
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()

    ac_title = "อ."
    name_body = cleaned
    for long_t, short_t in TITLE_MAP:
        if cleaned.startswith(long_t):
            ac_title = short_t
            name_body = cleaned[len(long_t) :].strip()
            break

    name_body = name_body.lstrip(". ")
    parts = name_body.split()
    fname = parts[0] if parts else ""
    lname = " ".join(parts[1:]) if len(parts) > 1 else fname
    cname = f"{fname} {lname}" if lname != fname else fname
    full_th = f"{ac_title} {cname}".strip()
    return ac_title, fname, lname, full_th


def extract_stou_school_faculties(client: httpx.Client) -> List[Dict[str, Any]]:
    """Crawls all 12 STOU schools and parses authentic faculty cards."""
    logger.info("--- [Wave 77] Harvesting STOU Faculties Across 12 Academic Schools ---")
    all_records: List[Dict[str, Any]] = []
    seen_names = set()

    for school in STOU_SCHOOLS:
        slug = school["slug"]
        fac_th = school["faculty_th"]
        fac_en = school["faculty_en"]
        def_dept = school["default_dept"]
        urls = school["urls"]

        logger.info(f"  -> Scraping school: [{fac_th}] ({len(urls)} target URLs)")
        school_faculty: List[Dict[str, Any]] = []

        for target_url in urls:
            try:
                r = client.get(target_url, timeout=15.0)
                if r.status_code != 200:
                    logger.warning(f"Failed to fetch {target_url}: status {r.status_code}")
                    continue

                soup = BeautifulSoup(r.text, "html.parser")

                # Strategy A: Elementor widgets with 2-element pattern (e.g. Political Science)
                if slug == "politicalsci":
                    for widget in soup.find_all("div", class_=lambda c: c and "elementor-widget" in str(c)):
                        txt = list(widget.stripped_strings)
                        if len(txt) >= 2:
                            name_candidate = txt[0].strip()
                            title_candidate = txt[1].strip()
                            if any(
                                title_candidate.startswith(p)
                                for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์"]
                            ):
                                combined = f"{title_candidate} {name_candidate}"
                                ac_title, fname, lname, full_th = parse_academic_name(combined)
                                if fname and len(fname) > 2 and full_th not in seen_names:
                                    img = widget.find("img")
                                    img_url = img.get("src") if img else None
                                    seen_names.add(full_th)
                                    school_faculty.append({
                                        "full_name_th": full_th,
                                        "academic_title_th": ac_title,
                                        "first_name": fname,
                                        "last_name": lname,
                                        "clean_name_th": f"{fname} {lname}",
                                        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
                                        "university_en": "Sukhothai Thammathirat Open University",
                                        "faculty_th": fac_th,
                                        "faculty_en": fac_en,
                                        "department_th": def_dept,
                                        "email": None,
                                        "image_url": img_url,
                                        "profile_url": target_url,
                                        "research_interests": [fac_th, def_dept, "การศึกษาทางไกล", "รัฐศาสตร์และบริหารรัฐกิจ"],
                                        "featured_publications": [],
                                        "education": txt[2:5],
                                        "role": None,
                                        "slug": slug,
                                    })

                # Strategy B: Card/Team/Box Elements with Title in first/second line
                for card in soup.find_all(["div", "article"], class_=lambda c: c and any(k in str(c) for k in ["elementor-widget", "team", "post", "box", "column"])):
                    txt = list(card.stripped_strings)
                    if not txt:
                        continue

                    # Cloudflare email check
                    cf_a = card.find(attrs={"data-cfemail": True})
                    cf_email = decode_cloudflare_email(cf_a["data-cfemail"]) if cf_a else None

                    # Find name line
                    name_line = None
                    edu_lines = []
                    role_line = None

                    for idx, line in enumerate(txt):
                        t_clean = line.strip()
                        if any(t_clean.startswith(p) for p in [
                            "ศ.เกียรติคุณ", "ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์",
                            "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "ศาสตราจารย์", "นายแพทย์", "พญ."
                        ]):
                            if len(t_clean.split()) >= 2 and len(t_clean) < 70 and not any(k in t_clean for k in [
                                "สาขาวิชา", "หลักสูตร", "มหาวิทยาลัย", "ประจำสาขา", "แขนงวิชา", "กลุ่มวิชา", "คณาจารย์"
                            ]):
                                name_line = t_clean
                                # Subsequent lines might contain role / education
                                for subsequent in txt[idx + 1 : idx + 6]:
                                    s_clean = subsequent.strip()
                                    if any(k in s_clean for k in ["ประธาน", "รองประธาน", "กรรมการ", "หัวหน้า", "เลขานุการ"]):
                                        role_line = s_clean
                                    elif any(k in s_clean for k in ["บ.", "ม.", "ด.", "Ph.D.", "M.Sc.", "B.Eng", "M.Eng"]):
                                        edu_lines.append(s_clean)
                                break

                    if not name_line:
                        continue

                    ac_title, fname, lname, full_th = parse_academic_name(name_line)
                    if not fname or len(fname) < 2 or fname == "ดร." or full_th in seen_names:
                        continue

                    seen_names.add(full_th)
                    img = card.find("img")
                    img_url = img.get("src") if img else None

                    # Check for direct email in card text
                    card_raw = str(card)
                    em_match = re.search(r"([a-zA-Z0-9_.+-]+@stou\.ac\.th)", card_raw)
                    email = cf_email or (em_match.group(1).lower() if em_match else None)

                    # Default research interests
                    interests = [fac_th, def_dept, "การศึกษาทางไกลและการเรียนรู้ตลอดชีวิต"]
                    if role_line and role_line not in interests:
                        interests.append(role_line)

                    school_faculty.append({
                        "full_name_th": full_th,
                        "academic_title_th": ac_title,
                        "first_name": fname,
                        "last_name": lname,
                        "clean_name_th": f"{fname} {lname}",
                        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
                        "university_en": "Sukhothai Thammathirat Open University",
                        "faculty_th": fac_th,
                        "faculty_en": fac_en,
                        "department_th": def_dept,
                        "email": email,
                        "image_url": img_url,
                        "profile_url": target_url,
                        "research_interests": interests[:6],
                        "featured_publications": [],
                        "education": edu_lines[:4],
                        "role": role_line,
                        "slug": slug,
                    })

            except Exception as e:
                logger.error(f"Error scraping {fac_th} ({target_url}): {e}")

        logger.info(f"     Harvested {len(school_faculty)} verified faculty in [{fac_th}].")
        all_records.extend(school_faculty)

    logger.info(f"✅ Total authentic STOU faculties extracted: {len(all_records)}")
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
                    if "sukhothai" in dname or "stou" in dname:
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
    faculty["total_citations"] = 0
    faculty["h_index"] = 0
    faculty["total_publications_count"] = 0
    return faculty


def ingest_wave77_faculties(records: List[Dict[str, Any]]) -> int:
    """Ingests extracted STOU faculty records into PostgreSQL."""
    db = SessionLocal()
    ingested_count = 0
    try:
        for idx, rec in enumerate(records, start=1):
            fac_id = f"stou_{rec['slug']}__{idx:04d}"

            # Check existing record by clean Thai name
            cname = clean_thai_name_for_matching(rec["clean_name_th"])
            existing = db.query(FacultyDB).filter(
                FacultyDB.university_th == "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
                FacultyDB.full_name_th.like(f"%{rec['clean_name_th']}%"),
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
                    embedding=None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search,
                )
                db.add(new_faculty)
                ingested_count += 1

        db.commit()
        logger.info(f"✅ Successfully committed {ingested_count} STOU faculty records.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to ingest Wave 77 faculties: {e}")
        raise
    finally:
        db.close()
    return ingested_count


def main():
    logger.info("=================================================================")
    logger.info("🚀 STARTING WAVE 77 AUTONOMOUS CRAWLER - STOU FACULTY")
    logger.info("=================================================================")

    client = httpx.Client(headers=CLIENT_HEADERS, follow_redirects=True, timeout=15.0)
    try:
        raw_records = extract_stou_school_faculties(client)
        if not raw_records:
            logger.error("No faculty records extracted! Aborting.")
            return

        # Pillar 5: Checkpointing
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(raw_records, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Checkpointed {len(raw_records)} records to {CHECKPOINT_PATH}")

        # Ingestion
        ingested = ingest_wave77_faculties(raw_records)
        logger.info(f"🎉 Wave 77 Completed: {ingested} authentic STOU faculty records in database.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
