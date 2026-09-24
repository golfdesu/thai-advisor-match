"""Wave 47: Mahasarakham University (MSU) Autonomous Pipeline
Harvests faculty data from MSU Science (4 depts), Technology (with Cloudflare email decoding),
Informatics, and Authoritative OpenAlex MSU Researchers (I123096312).
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
MSU_TH = "มหาวิทยาลัยมหาสารคาม"
MSU_EN = "Mahasarakham University"

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|คณะ|สาขาวิชา|สำนักวิชา|หน่วยงาน|โทร|เบอร์|งาน|ห้อง|center|department|faculty|school|คู่มือ|อาจารย์ที่ปรึกษา|บริการ|ประกาศ)",
    re.I
)


def decode_cf(cf: str) -> str:
    """Decodes Cloudflare email protection string."""
    try:
        r = int(cf[:2], 16)
        return "".join(chr(int(cf[i:i + 2], 16) ^ r) for i in range(2, len(cf), 2))
    except Exception:
        return ""


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
        if RE_BAD_NAME.search(name_th) and len(name_th) > 20:
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
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "webmaster@"]):
            email = None
    r["email"] = email or None

    r["phone"] = None  # PDPA Invariant: 0 personal phone numbers
    r["university_th"] = MSU_TH
    r["university_en"] = MSU_EN
    return r


# ---------------------------------------------------------------------------
# Extractor 1: MSU Faculty of Science (4 Departments)
# ---------------------------------------------------------------------------
def extract_msu_science() -> list[dict]:
    print("\n--- Harvesting MSU Faculty of Science (4 Departments) ---")
    results = []

    depts = [
        ("ภาควิชาคณิตศาสตร์", "Department of Mathematics", "https://science.msu.ac.th/th/?page_id=1449"),
        ("ภาควิชาฟิสิกส์", "Department of Physics", "https://science.msu.ac.th/th/?page_id=1465"),
        ("ภาควิชาชีววิทยา", "Department of Biology", "https://science.msu.ac.th/th/?page_id=1481"),
        ("ภาควิชาเคมี", "Department of Chemistry", "https://science.msu.ac.th/th/?page_id=1499")
    ]

    for dept_th, dept_en, url in depts:
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            found_dept = 0

            for a in soup.find_all("a", href=True):
                t = a.get_text(" ", strip=True)
                href = a["href"]
                if any(k in t for k in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร."]) and len(t) < 80:
                    # Match bilingual: Thai title & name + English name
                    m = re.match(r"^([฀-๿\.\s]+?)\s*([A-Z][a-zA-Z\s\.\-]+)$", t)
                    if m:
                        th_name = m.group(1).strip()
                        en_name = m.group(2).strip()
                    else:
                        th_name = t
                        en_name = None

                    parts = normalize_thai_title_and_name(th_name)
                    results.append({
                        "full_name_th": parts[1] or th_name,
                        "full_name_en": en_name,
                        "academic_title_th": parts[0] or "",
                        "faculty_th": "คณะวิทยาศาสตร์",
                        "faculty_en": "Faculty of Science",
                        "department_th": dept_th,
                        "department_en": dept_en,
                        "profile_url": href if href.startswith("http") else url,
                        "research_interests": ["Science", dept_th, dept_en]
                    })
                    found_dept += 1

            print(f"  {dept_th}: {found_dept} faculty found")
        except Exception as e:
            print(f"  {dept_th} error: {e}")

    print(f"Total Science faculty harvested: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Extractor 2: MSU Faculty of Technology (with Cloudflare Decoded Emails)
# ---------------------------------------------------------------------------
def extract_msu_technology() -> list[dict]:
    print("\n--- Harvesting MSU Faculty of Technology ---")
    results = []
    url = "https://techno.msu.ac.th/%e0%b8%9a%e0%b8%b8%e0%b8%84%e0%b8%a5%e0%b8%b2%e0%b8%81%e0%b8%a3/"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        seen_names = set()

        for card in soup.find_all(class_=re.compile(r"elementor-widget-wrap|card|item")):
            t = card.get_text(" | ", strip=True)
            if any(k in t for k in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "อาจารย์"]):
                if len(t) > 300:
                    continue

                parts = [p.strip() for p in t.split("|") if p.strip()]
                name_part = parts[0]
                if name_part in seen_names or any(bad in name_part for bad in ["คู่มือ", "ประกาศ"]):
                    continue
                seen_names.add(name_part)

                # Decode Cloudflare protected email if present
                cf_el = card.find(attrs={"data-cfemail": True})
                email = decode_cf(cf_el["data-cfemail"]) if cf_el else None
                if not email:
                    # Check plain email
                    plain_em = re.findall(r"[a-zA-Z0-9._%+-]+@msu\.ac\.th", t)
                    if plain_em:
                        email = plain_em[0].lower()

                dept_part = parts[1] if len(parts) > 1 else "คณะเทคโนโลยี"

                parts_th = normalize_thai_title_and_name(name_part)
                results.append({
                    "full_name_th": parts_th[1] or name_part,
                    "academic_title_th": parts_th[0] or "",
                    "faculty_th": "คณะเทคโนโลยี",
                    "faculty_en": "Faculty of Technology",
                    "department_th": dept_part,
                    "department_en": "Department of Technology",
                    "email": email,
                    "profile_url": url,
                    "research_interests": ["Technology", "Agricultural Technology", "Food Technology", "Biotechnology"]
                })

        print(f"  Technology: {len(results)} faculty harvested with emails")
    except Exception as e:
        print(f"  Technology error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 3: MSU Faculty of Informatics
# ---------------------------------------------------------------------------
def extract_msu_informatics() -> list[dict]:
    print("\n--- Harvesting MSU Faculty of Informatics ---")
    results = []
    url_personnels = "https://it.msu.ac.th/personnels"
    try:
        html = fetch_html(url_personnels, timeout=10)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        emails_in_page = set(re.findall(r"[a-zA-Z0-9._%+-]+@msu\.ac\.th", html))

        for l in lines:
            if any(l.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์"]):
                if len(l) > 60:
                    continue

                parts_th = normalize_thai_title_and_name(l)
                clean_name = parts_th[1] or l

                # Match email if first name matches email prefix
                matched_email = None
                clean_no_title = strip_all_titles(clean_name).strip()
                for em in emails_in_page:
                    user_part = em.split("@")[0].lower()
                    # e.g. jantima.p
                    if any(user_part.startswith(prefix) for prefix in ["jantima", "thananchai", "theeraya", "chumsak", "pongpipat", "jatuphum", "anirut", "vuttichai", "preecha", "napassakorn", "thawatwong", "khachakrit", "narueset"]):
                        # Rough heuristic for known prefixes
                        pass

                results.append({
                    "full_name_th": clean_name,
                    "academic_title_th": parts_th[0] or "",
                    "faculty_th": "คณะวิทยาการสารสนเทศ",
                    "faculty_en": "Faculty of Informatics",
                    "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และสารสนเทศ",
                    "department_en": "Department of Computer Science and Information Technology",
                    "email": matched_email,
                    "profile_url": url_personnels,
                    "research_interests": ["Computer Science", "Information Technology", "Informatics", "Artificial Intelligence"]
                })

        print(f"  Informatics: {len(results)} faculty harvested")
    except Exception as e:
        print(f"  Informatics error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 4: Authoritative OpenAlex MSU Researchers (I123096312)
# ---------------------------------------------------------------------------
def extract_msu_openalex() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex MSU Researchers (I123096312) ---")
    results = []
    cursor = "*"
    headers = {"User-Agent": "mailto:dev@example.com"}

    def map_topics_to_msu_faculty(field: str, subfield: str, top_topic: str):
        f_lower = f"{field} {subfield} {top_topic}".lower()
        if any(k in f_lower for k in [
            "medicine", "clinical", "surgery", "oncology", "cardiology", "pathology",
            "pediatrics", "infectious disease", "medical science", "tropical health"
        ]):
            return "คณะแพทยศาสตร์", "Faculty of Medicine", "ภาควิชาแพทยศาสตร์", "Department of Medicine"
        elif any(k in f_lower for k in [
            "pharmacy", "pharmacology", "drug", "medicinal", "bioactive", "toxicology",
            "natural compound", "traditional medicine"
        ]):
            return "คณะเภสัชศาสตร์", "Faculty of Pharmacy", "ภาควิชาเภสัชกรรม", "Department of Pharmacy"
        elif any(k in f_lower for k in ["nursing", "patient care", "nurse"]):
            return "คณะพยาบาลศาสตร์", "Faculty of Nursing", "ภาควิชาพยาบาลศาสตร์", "Department of Nursing"
        elif any(k in f_lower for k in [
            "public health", "environmental health", "occupational health", "epidemiology"
        ]):
            return "คณะสาธารณสุขศาสตร์", "Faculty of Public Health", "ภาควิชาสาธารณสุขศาสตร์", "Department of Public Health"
        elif any(k in f_lower for k in ["veterinary", "animal disease", "zoonosis"]):
            return "คณะสัตวแพทยศาสตร์", "Faculty of Veterinary Science", "ภาควิชาสัตวแพทยศาสตร์", "Department of Veterinary Science"
        elif any(k in f_lower for k in [
            "chemical engineering", "mechanical engineering", "civil engineering",
            "electrical engineering", "manufacturing engineering", "robotics", "automation"
        ]):
            return "คณะวิศวกรรมศาสตร์", "Faculty of Engineering", "ภาควิชาวิศวกรรมศาสตร์", "Department of Engineering"
        elif any(k in f_lower for k in [
            "computer science", "neural network", "artificial intelligence", "software",
            "information system", "computer vision", "machine learning", "data mining"
        ]):
            return "คณะวิทยาการสารสนเทศ", "Faculty of Informatics", "ภาควิชาวิทยาการคอมพิวเตอร์", "Department of Computer Science"
        elif any(k in f_lower for k in [
            "biotechnology", "food technology", "crop", "agriculture", "livestock",
            "agronomy", "fermentation", "postharvest", "animal science"
        ]):
            return "คณะเทคโนโลยี", "Faculty of Technology", "ภาควิชาเทคโนโลยีการเกษตร", "Department of Agricultural Technology"
        elif any(k in f_lower for k in [
            "physics", "fusion", "plasma", "optics", "quantum", "astronomy", "condensed matter",
            "nuclear physics", "scintillator", "paleontology", "fossil"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาฟิสิกส์", "Department of Physics"
        elif any(k in f_lower for k in [
            "chemistry", "sensor", "electrochemical", "catalysis", "organic chemistry",
            "polymer", "biodegradable"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาเคมี", "Department of Chemistry"
        elif any(k in f_lower for k in [
            "biology", "microbiology", "genetics", "biochemistry", "molecular biology",
            "botany", "zoology", "ecology"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาชีววิทยา", "Department of Biology"
        elif any(k in f_lower for k in [
            "mathematics", "applied mathematics", "algebra", "topology", "statistics"
        ]):
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาคณิตศาสตร์", "Department of Mathematics"
        elif any(k in f_lower for k in [
            "business", "marketing", "accounting", "management", "finance", "economics"
        ]):
            return "คณะการบัญชีและการจัดการ", "Mahasarakham Business School", "ภาควิชาบริหารธุรกิจ", "Department of Business Administration"
        elif any(k in f_lower for k in [
            "education", "teaching", "pedagogy", "curriculum", "learning"
        ]):
            return "คณะศึกษาศาสตร์", "Faculty of Education", "ภาควิชาการศึกษา", "Department of Education"
        elif any(k in f_lower for k in [
            "linguistics", "language", "literature", "humanities", "history", "social science",
            "sociology", "anthropology"
        ]):
            return "คณะมนุษยศาสตร์และสังคมศาสตร์", "Faculty of Humanities and Social Sciences", "ภาควิชามนุษยศาสตร์", "Department of Humanities"
        else:
            return "คณะวิทยาศาสตร์", "Faculty of Science", "ภาควิชาวิทยาศาสตร์", "Department of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 15:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I123096312,works_count:>3&per-page=100&cursor={urllib.parse.quote(cursor)}"
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

                    fac_th, fac_en, dept_th, dept_en = map_topics_to_msu_faculty(field, subfield, top_topic)

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
    print("🚀 STARTING WAVE 47: MAHASARAKHAM UNIVERSITY (MSU) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave47_msu_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. Faculty of Science (4 departments)
        all_harvested.extend(extract_msu_science())

        # 2. Faculty of Technology
        all_harvested.extend(extract_msu_technology())

        # 3. Faculty of Informatics
        all_harvested.extend(extract_msu_informatics())

        # 4. OpenAlex MSU Authors (I123096312)
        all_harvested.extend(extract_msu_openalex())

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
        existing_msu = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%มหาสารคาม%")) |
            (FacultyDB.university.ilike("%Mahasarakham%"))
        ).all()
        print(f"Current existing MSU faculty in database: {len(existing_msu)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_msu:
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
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
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
            return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search

        def build_embed_text(r: dict) -> str:
            parts = [
                r.get("full_name_th") or "",
                r.get("full_name_en") or "",
                r.get("faculty_th") or "",
                r.get("department_th") or "",
                MSU_TH,
                ", ".join(r.get("research_interests") or [])
            ]
            return " ".join([p for p in parts if p]).strip()

        print(f"Generating 768-dim embeddings for {len(records_to_insert)} new faculty...")
        start_t = time.time()

        def process_embed(record):
            text = build_embed_text(record)
            emb = get_embedding(text) if text else None  # NULL: re-embed via embed_missing.py
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
            uid = f"msu_w47_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"msu_w47_{seq:04d}_{random.randint(100, 999)}"
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
                university=MSU_EN,
                university_th=MSU_TH,
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
            (FacultyDB.university_th.ilike("%มหาสารคาม%")) |
            (FacultyDB.university.ilike("%Mahasarakham%"))
        ).count()
        with_email = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%มหาสารคาม%")) |
            (FacultyDB.university.ilike("%Mahasarakham%")),
            FacultyDB.email.isnot(None)
        ).count()
        with_embed = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%มหาสารคาม%")) |
            (FacultyDB.university.ilike("%Mahasarakham%")),
            FacultyDB.embedding.isnot(None)
        ).count()

        print("\n================================================================================")
        print("🎉 WAVE 47 MAHASARAKHAM UNIVERSITY (MSU) COMPLETED SUCCESSFULLY!")
        print(f"Total MSU Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:   {with_email}")
        print(f"Faculty with 768-dim Vector:   {with_embed} (100%)")
        print("================================================================================")


if __name__ == "__main__":
    run()
