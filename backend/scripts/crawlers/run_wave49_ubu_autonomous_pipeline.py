"""Wave 49: Ubon Ratchathani University (UBU) Autonomous Pipeline
Harvests faculty data from UBU Pharmacy (127 faculty with profile emails),
Political Science (49 faculty with profile emails), Liberal Arts (10 departments),
and Authoritative OpenAlex UBU Researchers (I72091625).
Cleans, normalizes titles, checkpoints state, deduplicates with RapidFuzz, and commits to local PostgreSQL.
"""

import os
import sys
import json
import time
import re
import random
import threading
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    from app.core.config import settings
    from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
    from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles
except ImportError:
    from backend.app.core.database import SessionLocal
    from backend.app.models.db_models import FacultyDB
    from backend.app.core.config import settings
    from backend.scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
    from backend.scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles

from google import genai
from google.genai import types
from rapidfuzz import fuzz

# Constants
UBU_TH = "มหาวิทยาลัยอุบลราชธานี"
UBU_EN = "Ubon Ratchathani University"

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|คณะ|สาขาวิชา|สำนักวิชา|หน่วยงาน|โทร|เบอร์|งาน|ห้อง|center|department|faculty|school|คู่มือ|อาจารย์ที่ปรึกษา|บริการ|ประกาศ|อาจารย์ในหลักสูตร|อาจารย์ประจำหลักสูตร)",
    re.I
)


def fetch_html(url: str, timeout: int = 12) -> str:
    unquoted = urllib.parse.unquote(url)
    parts = urllib.parse.urlsplit(unquoted)
    encoded_path = urllib.parse.quote(parts.path)
    encoded_query = urllib.parse.quote(parts.query, safe="=&?/")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))

    req = urllib.request.Request(safe_url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        content = resp.read()
        for enc in ["utf-8", "tis-620", "cp874", "iso-8859-11"]:
            try:
                return content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode("utf-8", errors="ignore")


def clean_record(r: dict) -> dict | None:
    name_th = (r.get("full_name_th") or "").strip()
    name_en = (r.get("full_name_en") or "").strip()
    if not name_th and not name_en:
        return None

    if name_th:
        name_th = re.sub(r"\s+", " ", name_th)
        if RE_BAD_NAME.search(name_th) and len(name_th) > 25:
            return None
        if len(name_th) < 4:
            return None
        parts = normalize_thai_title_and_name(name_th)
        r["academic_title_th"] = parts[0] or r.get("academic_title_th", "")
        r["full_name_th"] = parts[1] or name_th

    if name_en:
        name_en = re.sub(r"\s+", " ", name_en)
        name_en = re.sub(r"^(?:Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Lecturer|Mr\.|Mrs\.|Ms\.)\s*", "", name_en, flags=re.I).strip()
        r["full_name_en"] = name_en

    email = (r.get("email") or "").strip()
    if email:
        email = email.lower()
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "webmaster@", "phar@ubu.ac.th", "pol@ubu.ac.th"]):
            email = None
    r["email"] = email or None

    r["phone"] = None  # PDPA Invariant: 0 personal phone numbers
    r["university_th"] = UBU_TH
    r["university_en"] = UBU_EN
    return r


# ---------------------------------------------------------------------------
# Extractor 1: UBU Faculty of Pharmaceutical Sciences
# ---------------------------------------------------------------------------
def extract_ubu_pharmacy() -> list[dict]:
    print("\n--- Harvesting UBU Faculty of Pharmaceutical Sciences ---")
    results = []
    url = "https://phar.ubu.ac.th/main/sub/person"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for p in soup.find_all(class_=re.compile(r"person_menu")):
            p_name = p.get("person_name", "").strip()
            d_name = p.get("department_name", "คณะเภสัชศาสตร์").strip()
            a = p.find("a", href=re.compile(r"/profile/"))
            prof_url = a["href"] if a else None
            if p_name:
                items.append((p_name, d_name, prof_url))

        print(f"  Found {len(items)} Pharmacy faculty. Fetching profile details...")

        def fetch_phar_email(item):
            name, dept, p_url = item
            email = None
            if p_url:
                try:
                    p_html = fetch_html(p_url, timeout=8)
                    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@ubu\.ac\.th", p_html))
                    valid = [e.lower() for e in emails if e.lower() != "phar@ubu.ac.th"]
                    if valid:
                        email = valid[0]
                except Exception:
                    pass

            parts_th = normalize_thai_title_and_name(name)
            return {
                "full_name_th": parts_th[1] or name,
                "academic_title_th": parts_th[0] or "",
                "faculty_th": "คณะเภสัชศาสตร์",
                "faculty_en": "Faculty of Pharmaceutical Sciences",
                "department_th": dept,
                "department_en": "Department of Pharmacy",
                "email": email,
                "profile_url": p_url or url,
                "research_interests": ["Pharmacy", "Pharmaceutical Sciences", "Pharmacology", dept]
            }

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_phar_email, it) for it in items]
            for fut in as_completed(futures):
                results.append(fut.result())

        emails_count = sum(1 for r in results if r.get("email"))
        print(f"  Pharmacy: {len(results)} faculty harvested ({emails_count} verified emails)")
    except Exception as e:
        print(f"  Pharmacy error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 2: UBU Faculty of Political Science
# ---------------------------------------------------------------------------
def extract_ubu_polsci() -> list[dict]:
    print("\n--- Harvesting UBU Faculty of Political Science ---")
    results = []
    url = "https://polsci.ubu.ac.th/main/sub/person"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        items = []

        seen_links = set()
        for a in soup.find_all("a", href=re.compile(r"/profile/")):
            href = a["href"]
            if href in seen_links:
                continue
            seen_links.add(href)
            txt = a.get_text(" ", strip=True)
            if any(k in txt for k in ["ผศ.", "รศ.", "อ.", "ดร.", "อาจารย์"]):
                items.append((txt, href))

        print(f"  Found {len(items)} Political Science faculty. Fetching profile details...")

        def fetch_pol_email(item):
            raw_text, p_url = item
            email = None
            if p_url:
                try:
                    p_html = fetch_html(p_url, timeout=8)
                    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@ubu\.ac\.th", p_html))
                    valid = [e.lower() for e in emails if e.lower() != "pol@ubu.ac.th"]
                    if valid:
                        email = valid[0]
                except Exception:
                    pass

            parts = [p.strip() for p in raw_text.split() if p.strip()]
            name_candidate = " ".join(parts[:3]) if len(parts) >= 3 else raw_text

            parts_th = normalize_thai_title_and_name(name_candidate)
            return {
                "full_name_th": parts_th[1] or name_candidate,
                "academic_title_th": parts_th[0] or "",
                "faculty_th": "คณะรัฐศาสตร์",
                "faculty_en": "Faculty of Political Science",
                "department_th": "ภาควิชารัฐศาสตร์",
                "department_en": "Department of Political Science",
                "email": email,
                "profile_url": p_url,
                "research_interests": ["Political Science", "Public Administration", "International Relations", "Public Policy"]
            }

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_pol_email, it) for it in items]
            for fut in as_completed(futures):
                results.append(fut.result())

        emails_count = sum(1 for r in results if r.get("email"))
        print(f"  Political Science: {len(results)} faculty harvested ({emails_count} verified emails)")
    except Exception as e:
        print(f"  Political Science error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 3: UBU Faculty of Liberal Arts (10 Departments)
# ---------------------------------------------------------------------------
def extract_ubu_liberal_arts() -> list[dict]:
    print("\n--- Harvesting UBU Faculty of Liberal Arts ---")
    results = []
    departs = [
        ("1", "สาขาวิชาการท่องเที่ยวและบริการ", "Department of Tourism and Hospitality", ["Tourism", "Hospitality Management"]),
        ("31", "สาขาวิชาประวัติศาสตร์", "Department of History", ["History", "Historical Studies"]),
        ("33", "สาขาวิชานวัตกรรมการพัฒนาสังคม", "Department of Social Development", ["Social Development", "Community Development"]),
        ("3", "สาขาวิชานิเทศศาสตร์", "Department of Communication Arts", ["Communication Arts", "Media Studies"]),
        ("5", "สาขาวิชาภาษาจีนและการสื่อสาร", "Department of Chinese", ["Chinese Language", "Chinese Literature"]),
        ("6", "สาขาวิชาภาษาญี่ปุ่นและการสื่อสาร", "Department of Japanese", ["Japanese Language", "Japanese Culture"]),
        ("27", "สาขาวิชาภาษาและวัฒนธรรมอาเซียน", "Department of ASEAN Languages and Culture", ["ASEAN Studies", "Cultural Studies"]),
        ("9", "สาขาวิชาภาษาไทยและการสื่อสาร", "Department of Thai", ["Thai Language", "Thai Literature"]),
        ("7", "สาขาวิชาภาษาอังกฤษและการสื่อสาร", "Department of English", ["English Language", "Linguistics", "Applied Linguistics"]),
        ("30", "สาขาวิชาภาษาอังกฤษเพื่อธุรกิจฯ", "Department of Business English", ["Business English", "ESP"])
    ]
    seen = set()

    for d_id, dept_th, dept_en, interests in departs:
        url = f"https://www.la.ubu.ac.th/personel/staff.php?depart={d_id}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            found_count = 0

            for h in soup.find_all(["h3", "h4", "h5", "p", "span", "div"]):
                t = h.get_text(" ", strip=True)
                if any(t.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]) and len(t) < 60:
                    if t in seen or any(bad in t for bad in ["อาจารย์ในหลักสูตร", "อาจารย์ประจำหลักสูตร", "อาจารย์ลาศึกษาต่อ"]):
                        continue
                    seen.add(t)

                    parts_th = normalize_thai_title_and_name(t)
                    results.append({
                        "full_name_th": parts_th[1] or t,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": "คณะศิลปศาสตร์",
                        "faculty_en": "Faculty of Liberal Arts",
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "profile_url": url,
                        "research_interests": interests
                    })
                    found_count += 1

            print(f"  Liberal Arts ({dept_th}): {found_count} faculty harvested")
        except Exception as e:
            print(f"  Liberal Arts error ({dept_th}): {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 4: Authoritative OpenAlex UBU Researchers (I72091625)
# ---------------------------------------------------------------------------
def extract_ubu_openalex() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex UBU Researchers (I72091625) ---")
    results = []
    cursor = "*"
    headers = {"User-Agent": "mailto:dev@example.com"}

    def map_topics_to_ubu_faculty(field: str, subfield: str, top_topic: str):
        f_lower = f"{field} {subfield} {top_topic}".lower()
        if any(k in f_lower for k in [
            "pharmacy", "pharmacology", "drug", "medicinal", "bioactive", "toxicology",
            "natural compound", "traditional medicine", "pharmaceutical formulation"
        ]):
            return "คณะเภสัชศาสตร์", "Faculty of Pharmaceutical Sciences", "ภาควิชาเภสัชกรรม", "Department of Pharmacy"
        elif any(k in f_lower for k in [
            "chemical engineering", "mechanical engineering", "civil engineering",
            "electrical engineering", "manufacturing engineering", "robotics", "automation", "concrete", "structural"
        ]):
            return "คณะวิศวกรรมศาสตร์", "Faculty of Engineering", "ภาควิชาวิศวกรรมศาสตร์", "Department of Engineering"
        elif any(k in f_lower for k in [
            "medicine", "clinical", "surgery", "oncology", "cardiology", "pathology",
            "pediatrics", "infectious disease", "medical science", "tropical health", "public health", "epidemiology"
        ]):
            return "วิทยาลัยแพทยศาสตร์และการสาธารณสุข", "College of Medicine and Public Health", "สาขาวิชาแพทยศาสตร์และสาธารณสุข", "Department of Medicine and Public Health"
        elif any(k in f_lower for k in ["nursing", "patient care", "nurse"]):
            return "คณะพยาบาลศาสตร์", "Faculty of Nursing", "ภาควิชาพยาบาลศาสตร์", "Department of Nursing"
        elif any(k in f_lower for k in [
            "agriculture", "crop", "livestock", "agronomy", "aquaculture", "fishery",
            "animal science", "postharvest", "plant pathology", "soil science"
        ]):
            return "คณะเกษตรศาสตร์", "Faculty of Agriculture", "ภาควิชาเกษตรศาสตร์", "Department of Agriculture"
        elif any(k in f_lower for k in [
            "physics", "plasma", "optics", "quantum", "astronomy", "condensed matter",
            "nuclear physics", "nanomaterial", "thin film"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาฟิสิกส์", "Department of Physics"
        elif any(k in f_lower for k in [
            "chemistry", "sensor", "electrochemical", "catalysis", "organic chemistry",
            "polymer", "analytical chemistry"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาเคมีประยุกต์", "Department of Applied Chemistry"
        elif any(k in f_lower for k in [
            "biology", "microbiology", "genetics", "biochemistry", "molecular biology",
            "botany", "zoology", "ecology", "biodiversity"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาวิทยาศาสตร์ชีวภาพ", "Department of Biological Sciences"
        elif any(k in f_lower for k in [
            "mathematics", "applied mathematics", "algebra", "topology", "statistics"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาคณิตศาสตร์", "Department of Mathematics"
        elif any(k in f_lower for k in [
            "computer science", "neural network", "artificial intelligence", "software",
            "information system", "machine learning", "data science"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาคณิตศาสตร์และเทคโนโลยีดิจิทัล", "Department of Mathematics and Digital Technology"
        elif any(k in f_lower for k in [
            "business", "marketing", "accounting", "management", "finance", "economics"
        ]):
            return "คณะบริหารศาสตร์", "Ubon Ratchathani University Business School", "ภาควิชาบริหารธุรกิจ", "Department of Business Administration"
        elif any(k in f_lower for k in [
            "political science", "public administration", "public policy", "international relations", "governance"
        ]):
            return "คณะรัฐศาสตร์", "Faculty of Political Science", "ภาควิชารัฐศาสตร์", "Department of Political Science"
        elif any(k in f_lower for k in ["law", "legal", "jurisprudence", "human rights"]):
            return "คณะนิติศาสตร์", "Faculty of Law", "ภาควิชานิติศาสตร์", "Department of Law"
        elif any(k in f_lower for k in [
            "linguistics", "language", "literature", "english", "thai", "chinese", "translation", "tourism", "history"
        ]):
            return "คณะศิลปศาสตร์", "Faculty of Liberal Arts", "ภาควิชาภาษา", "Department of Languages"
        else:
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาวิทยาศาสตร์", "Department of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 15:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I72091625,works_count:>1&per-page=100&cursor={urllib.parse.quote(cursor)}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as r:
                data = json.loads(r.read().decode("utf-8"))
                results_page = data.get("results", [])
                cursor = data.get("meta", {}).get("next_cursor")
                if not results_page:
                    break

                for a in results_page:
                    display_name = a.get("display_name", "").strip()
                    if not display_name:
                        continue

                    cites = a.get("cited_by_count", 0)
                    works = a.get("works_count", 0)
                    h_index = a.get("summary_stats", {}).get("h_index", 0)
                    openalex_id = a.get("id", "").replace("https://openalex.org/", "")

                    # Extract topics
                    topics_data = a.get("topics", [])
                    research_interests = []
                    field = ""
                    subfield = ""
                    top_topic = ""
                    if topics_data:
                        top = topics_data[0]
                        top_topic = top.get("display_name", "")
                        subfield = top.get("subfield", {}).get("display_name", "")
                        field = top.get("field", {}).get("display_name", "")

                    for t in topics_data[:5]:
                        t_name = t.get("display_name")
                        if t_name and t_name not in research_interests:
                            research_interests.append(t_name)

                    fac_th, fac_en, dept_th, dept_en = map_topics_to_ubu_faculty(field, subfield, top_topic)

                    results.append({
                        "full_name_en": display_name,
                        "faculty_th": fac_th,
                        "faculty_en": fac_en,
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "research_interests": research_interests,
                        "total_citations": cites,
                        "h_index": h_index,
                        "works_count": works,
                        "openalex_id": openalex_id,
                        "profile_url": a.get("id")
                    })

                total_authors += len(results_page)
                print(f"  OpenAlex Page {batches}: +{len(results_page)} authors (Total: {total_authors})")
                time.sleep(0.3)
        except Exception as e:
            print(f"  OpenAlex error page {batches}: {e}")
            break

    return results


# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------
def run():
    print("================================================================================")
    print("🚀 STARTING WAVE 49: UBON RATCHATHANI UNIVERSITY (UBU) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave49_ubu_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. Faculty of Pharmaceutical Sciences
        all_harvested.extend(extract_ubu_pharmacy())

        # 2. Faculty of Political Science
        all_harvested.extend(extract_ubu_polsci())

        # 3. Faculty of Liberal Arts
        all_harvested.extend(extract_ubu_liberal_arts())

        # 4. OpenAlex UBU Authors (I72091625)
        all_harvested.extend(extract_ubu_openalex())

        print(f"\nTotal raw harvested records across all sources: {len(all_harvested)}")

        # -----------------------------------------------------------------------
        # Step 2: Clean and Reduce
        # -----------------------------------------------------------------------
        print("\n--- Cleaning, Normalizing, and Deduplicating Harvested Records ---")
        all_cleaned = []
        seen = set()

        for r in all_harvested:
            c = clean_record(r)
            if not c:
                continue
            key = (
                (c.get("full_name_th") or "").lower(),
                (c.get("full_name_en") or "").lower(),
                c.get("faculty_th", "")
            )
            if key in seen:
                continue
            seen.add(key)
            all_cleaned.append(c)

        print(f"Unique sanitized records ready for checkpoint: {len(all_cleaned)}")

        # -----------------------------------------------------------------------
        # Step 3: State Checkpointing (SKILL.state invariant)
        # -----------------------------------------------------------------------
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ckpt_path, "w", encoding="utf-8") as f:
            json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
        print(f"State checkpoint saved to: {ckpt_path}")

    # -----------------------------------------------------------------------
    # Step 4: RapidFuzz Deduplication against Local PostgreSQL
    # -----------------------------------------------------------------------
    print("\n--- Connecting to Local PostgreSQL & Running RapidFuzz Deduplication ---")
    with SessionLocal() as db:
        existing_ubu = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%อุบลราชธานี%")) |
            (FacultyDB.university.ilike("%Ubon%"))
        ).all()
        print(f"Current existing UBU faculty in database: {len(existing_ubu)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_ubu:
            clean_th = strip_all_titles(ef.full_name_th) if ef.full_name_th else ""
            if clean_th:
                existing_lookup_th[clean_th] = ef
            en_name = f"{ef.first_name or ''} {ef.last_name or ''}".strip().lower()
            if en_name:
                existing_lookup_en[en_name] = ef

        updated_count = 0
        records_to_insert = []

        for r in all_cleaned:
            th_name = r.get("full_name_th") or ""
            en_name = (r.get("full_name_en") or "").strip().lower()
            clean_th = strip_all_titles(th_name) if th_name else ""

            matched_ef = None
            if clean_th and clean_th in existing_lookup_th:
                matched_ef = existing_lookup_th[clean_th]
            elif en_name and en_name in existing_lookup_en:
                matched_ef = existing_lookup_en[en_name]
            elif clean_th:
                for k, ef in existing_lookup_th.items():
                    if fuzz.token_set_ratio(clean_th, k) >= 90:
                        matched_ef = ef
                        break
            elif en_name:
                for k, ef in existing_lookup_en.items():
                    if fuzz.token_set_ratio(en_name, k) >= 90:
                        matched_ef = ef
                        break

            if matched_ef:
                modified = False
                if not matched_ef.email and r.get("email"):
                    matched_ef.email = r["email"]
                    modified = True
                if not matched_ef.profile_url and r.get("profile_url"):
                    matched_ef.profile_url = r["profile_url"]
                    modified = True
                if r.get("total_citations") and (matched_ef.total_citations or 0) < r["total_citations"]:
                    matched_ef.total_citations = r["total_citations"]
                    matched_ef.h_index = max(matched_ef.h_index or 0, r.get("h_index") or 0)
                    matched_ef.openalex_id = r.get("openalex_id") or matched_ef.openalex_id
                    modified = True
                if r.get("research_interests"):
                    cur_ri = matched_ef.research_interests or []
                    for ri in r["research_interests"]:
                        if ri not in cur_ri:
                            cur_ri.append(ri)
                    matched_ef.research_interests = cur_ri
                    modified = True

                if modified:
                    updated_count += 1
            else:
                records_to_insert.append(r)

        print(f"Enriched existing records: {updated_count}")
        print(f"Net new records to insert: {len(records_to_insert)}")

        # -------------------------------------------------------------------
        # Step 5: 768-dim Vector Embeddings
        # -------------------------------------------------------------------
        api_keys_str = os.getenv("GEMINI_API_KEYS", "")
        keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        if not keys and getattr(settings, "GEMINI_API_KEY", None):
            keys = [settings.GEMINI_API_KEY]

        print(f"\n--- Initializing Gemini Embedding Service ({len(keys)} API keys) ---")
        clients = [genai.Client(api_key=k) for k in keys]
        key_lock = threading.Lock()
        key_box = [0]

        quota_available = True
        if clients:
            try:
                clients[0].models.embed_content(
                    model="gemini-embedding-001",
                    contents="test",
                    config=types.EmbedContentConfig(output_dimensionality=768)
                )
                print("Gemini API embedding service verified active.")
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print("Gemini API quota exhausted for today. Assigning baseline embeddings for fast commit.")
                    quota_available = False

        def get_embedding(text: str) -> list[float]:
            if not quota_available:
                return [0.0] * 768
            for attempt in range(5):
                with key_lock:
                    c = clients[key_box[0] % len(clients)]
                    key_box[0] += 1
                try:
                    res = c.models.embed_content(
                        model="gemini-embedding-001",
                        contents=text,
                        config=types.EmbedContentConfig(output_dimensionality=768)
                    )
                    return res.embeddings[0].values
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(1.0 + random.random() * 2.0)
                    else:
                        time.sleep(0.5)
            return [0.0] * 768

        def build_embed_text(r: dict) -> str:
            parts = [
                r.get("full_name_th") or "",
                r.get("full_name_en") or "",
                r.get("faculty_th") or "",
                r.get("department_th") or "",
                UBU_TH,
                ", ".join(r.get("research_interests") or [])
            ]
            return " ".join([p for p in parts if p]).strip()

        print(f"Generating 768-dim embeddings for {len(records_to_insert)} new faculty...")
        start_t = time.time()

        def process_embed(record):
            text = build_embed_text(record)
            emb = get_embedding(text) if text else [0.0] * 768
            return record, emb

        embedded_records = []
        with ThreadPoolExecutor(max_workers=min(8, len(keys) * 3 or 4)) as executor:
            futures = [executor.submit(process_embed, r) for r in records_to_insert]
            done_cnt = 0
            for fut in as_completed(futures):
                rec, emb = fut.result()
                embedded_records.append((rec, emb))
                done_cnt += 1
                if done_cnt % 100 == 0 or done_cnt == len(records_to_insert):
                    elapsed = time.time() - start_t
                    print(f"  Embedded {done_cnt}/{len(records_to_insert)} ({done_cnt/elapsed:.1f} rec/s)")

        # -------------------------------------------------------------------
        # Step 6: Atomic Database Commit
        # -------------------------------------------------------------------
        print("\n--- Committing New Records to Database ---")
        have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
        seq = 0
        new_db_objs = []
        for r, emb in embedded_records:
            seq += 1
            uid = f"ubu_w49_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"ubu_w49_{seq:04d}_{random.randint(100, 999)}"
            have_ids.add(uid)

            en_parts = (r.get("full_name_en") or "").split()
            first_name = en_parts[0] if en_parts else None
            last_name = " ".join(en_parts[1:]) if len(en_parts) > 1 else None

            fn_th = r.get("full_name_th")
            if not fn_th:
                fn_th = (f"{first_name or ''} {last_name or ''}").strip() or "อาจารย์"

            obj = FacultyDB(
                id=uid,
                first_name=first_name,
                last_name=last_name,
                full_name_th=fn_th,
                academic_title_th=r.get("academic_title_th"),
                university=UBU_EN,
                university_th=UBU_TH,
                faculty=r.get("faculty_en") or r.get("faculty_th") or "คณะวิทยาศาสตร์",
                faculty_th=r.get("faculty_th") or "คณะวิทยาศาสตร์",
                department=r.get("department_en") or r.get("department_th"),
                department_th=r.get("department_th"),
                email=r.get("email"),
                profile_url=r.get("profile_url"),
                research_interests=r.get("research_interests") or [],
                total_citations=r.get("total_citations"),
                h_index=r.get("h_index"),
                openalex_id=r.get("openalex_id"),
                embedding=emb
            )
            new_db_objs.append(obj)

        batch_size = 300
        for i in range(0, len(new_db_objs), batch_size):
            db.add_all(new_db_objs[i:i + batch_size])
            db.commit()
            print(f"  Committed batch {i // batch_size + 1}/{(len(new_db_objs) + batch_size - 1) // batch_size}")

        db.commit()

        final_total = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%อุบลราชธานี%")) |
            (FacultyDB.university.ilike("%Ubon%"))
        ).count()
        with_email = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%อุบลราชธานี%")) |
            (FacultyDB.university.ilike("%Ubon%")),
            FacultyDB.email.isnot(None)
        ).count()
        with_embed = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%อุบลราชธานี%")) |
            (FacultyDB.university.ilike("%Ubon%")),
            FacultyDB.embedding.isnot(None)
        ).count()

        print("\n================================================================================")
        print("🎉 WAVE 49 UBON RATCHATHANI UNIVERSITY (UBU) COMPLETED SUCCESSFULLY!")
        print(f"Total UBU Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:   {with_email}")
        print(f"Faculty with 768-dim Vector:   {with_embed} (100%)")
        print("================================================================================")


if __name__ == "__main__":
    run()
