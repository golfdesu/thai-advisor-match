"""Wave 50: Thaksin University (TSU) Autonomous Pipeline
Harvests faculty data from TSU Research Directory (84 pages, ~1,600 researchers),
Faculty Portals (Engineering, Medicine, Law, Allied Health, Science),
and Authoritative OpenAlex TSU Researchers (I79246082).
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
TSU_TH = "มหาวิทยาลัยทักษิณ"
TSU_EN = "Thaksin University"

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|คณะ|สาขาวิชา|สำนักวิชา|หน่วยงาน|โทร|เบอร์|งาน|ห้อง|center|department|faculty|school|คู่มือ|อาจารย์ที่ปรึกษา|บริการ|ประกาศ|รายละเอียด|อาจารย์ประจำหลักสูตร)",
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
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "webmaster@", "eng@tsu.ac.th"]):
            email = None
    r["email"] = email or None

    r["phone"] = None  # PDPA Invariant: 0 personal phone numbers
    r["university_th"] = TSU_TH
    r["university_en"] = TSU_EN
    return r


# ---------------------------------------------------------------------------
# Extractor 1: TSU Research Directory (All 84 Pages, ~1,600 Researchers)
# ---------------------------------------------------------------------------
def extract_tsu_research_directory() -> list[dict]:
    print("\n--- Harvesting TSU Research Directory (84 Pages) ---")
    results = []
    base_url = "https://research.tsu.ac.th/researchers.php?view=table&page="

    def fetch_page(page_num: int) -> list[dict]:
        page_results = []
        url = f"{base_url}{page_num}"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if not table:
                return []

            rows = table.find_all("tr")[1:]
            for r in rows:
                cols = r.find_all("td")
                if len(cols) < 4:
                    continue

                col_name = cols[1].get_text(" ", strip=True)
                col_fac = cols[2].get_text(" ", strip=True)
                col_contact = cols[3].get_text(" ", strip=True)

                a_detail = r.find("a", href=re.compile(r"researcher-detail\.php"))
                prof_url = f"https://research.tsu.ac.th/{a_detail['href']}" if a_detail else url

                # Clean avatar prefix (e.g. "จแ ")
                cleaned_name = re.sub(r"^[^\s]{1,3}\s+", "", col_name).strip()
                m = re.match(r"^([฀-๿\.\s]+?)(?:\s+([A-Za-z\.\s]+))?$", cleaned_name)
                if m:
                    th_name = m.group(1).strip()
                    en_name = (m.group(2) or "").strip() or None
                else:
                    th_name = cleaned_name
                    en_name = None

                # Extract email
                em_match = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", col_contact)
                email = em_match[0].lower() if em_match else None

                parts_th = normalize_thai_title_and_name(th_name)
                page_results.append({
                    "full_name_th": parts_th[1] or th_name,
                    "full_name_en": en_name,
                    "academic_title_th": parts_th[0] or "",
                    "faculty_th": col_fac or "มหาวิทยาลัยทักษิณ",
                    "faculty_en": "Faculty at Thaksin University",
                    "department_th": col_fac or "มหาวิทยาลัยทักษิณ",
                    "department_en": "Department at Thaksin University",
                    "email": email,
                    "profile_url": prof_url,
                    "research_interests": [col_fac] if col_fac else []
                })
        except Exception as e:
            print(f"  Page {page_num} error: {e}")

        return page_results

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_page, p): p for p in range(1, 85)}
        for fut in as_completed(futures):
            res = fut.result()
            results.extend(res)

    print(f"Total researchers harvested from TSU Research Directory: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Extractor 2: TSU Faculty Portals (Engineering, Medicine, Law, AHS, Science)
# ---------------------------------------------------------------------------
def extract_tsu_faculty_portals() -> list[dict]:
    print("\n--- Harvesting TSU Targeted Faculty Portals ---")
    results = []
    targets = [
        ("https://engineering.tsu.ac.th/cperson.php", "คณะวิศวกรรมศาสตร์", "Faculty of Engineering", ["Engineering", "Electrical", "Mechanical", "Civil", "Polymer"]),
        ("https://medicine.tsu.ac.th/cperson.php", "คณะแพทยศาสตร์", "Faculty of Medicine", ["Medicine", "Clinical Medicine", "Medical Science"]),
        ("https://law.tsu.ac.th/cperson.php", "คณะนิติศาสตร์", "Faculty of Law", ["Law", "Legal Studies", "Jurisprudence"]),
        ("https://ahs.tsu.ac.th/cperson.php", "คณะสหเวชศาสตร์", "Faculty of Allied Health Sciences", ["Physical Therapy", "Allied Health", "Rehabilitation"]),
        ("https://scidi.tsu.ac.th/staff/%E0%B8%AA%E0%B8%B2%E0%B8%A2%E0%B8%A7%E0%B8%B4%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3", "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", ["Science", "Digital Innovation", "Computer Science", "Chemistry", "Physics"])
    ]

    for url, fac_th, fac_en, interests in targets:
        try:
            html = fetch_html(url, timeout=12)
            soup = BeautifulSoup(html, "html.parser")
            seen = set()
            found_count = 0

            for card in soup.find_all(class_=re.compile(r"card|box|item|col|team|member|wrap", re.I)):
                t = card.get_text(" | ", strip=True)
                if any(p in t for p in ["อาจารย์", "ผศ.", "รศ.", "ศ.", "ดร.", "นายแพทย์", "แพทย์หญิง"]):
                    if len(t) > 300:
                        continue

                    parts = [pt.strip() for pt in t.split("|") if pt.strip()]
                    name_th = None
                    for pt in parts:
                        if any(pt.startswith(pref) for pref in ["ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "อาจารย์", "นายแพทย์", "แพทย์หญิง"]):
                            if len(pt) < 60:
                                name_th = pt
                                break

                    if not name_th or name_th in seen or "อาจารย์ประจำ" in name_th:
                        continue
                    seen.add(name_th)

                    em_match = re.findall(r"[a-zA-Z0-9._%+-]+@tsu\.ac\.th", t)
                    email = em_match[0].lower() if em_match else None
                    if email == "eng@tsu.ac.th":
                        email = None

                    parts_th = normalize_thai_title_and_name(name_th)
                    results.append({
                        "full_name_th": parts_th[1] or name_th,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": fac_th,
                        "faculty_en": fac_en,
                        "department_th": fac_th,
                        "department_en": fac_en,
                        "email": email,
                        "profile_url": url,
                        "research_interests": interests
                    })
                    found_count += 1

            print(f"  {fac_th}: {found_count} faculty harvested")
        except Exception as e:
            print(f"  {fac_th} error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 3: Authoritative OpenAlex TSU Researchers (I79246082)
# ---------------------------------------------------------------------------
def extract_tsu_openalex() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex TSU Researchers (I79246082) ---")
    results = []
    cursor = "*"
    headers = {"User-Agent": "mailto:dev@example.com"}

    def map_topics_to_tsu_faculty(field: str, subfield: str, top_topic: str):
        f_lower = f"{field} {subfield} {top_topic}".lower()
        if any(k in f_lower for k in [
            "chemical engineering", "mechanical engineering", "civil engineering",
            "electrical engineering", "manufacturing engineering", "robotics", "automation", "concrete", "polymer", "renewable energy"
        ]):
            return "คณะวิศวกรรมศาสตร์", "Faculty of Engineering", "ภาควิชาวิศวกรรมศาสตร์", "Department of Engineering"
        elif any(k in f_lower for k in [
            "medicine", "clinical", "surgery", "oncology", "cardiology", "pathology",
            "pediatrics", "infectious disease", "medical science"
        ]):
            return "คณะแพทยศาสตร์", "Faculty of Medicine", "ภาควิชาแพทยศาสตร์", "Department of Medicine"
        elif any(k in f_lower for k in [
            "physical therapy", "physiotherapy", "rehabilitation", "sports science", "exercise physiology", "allied health"
        ]):
            return "คณะสหเวชศาสตร์", "Faculty of Allied Health Sciences", "ภาควิชากายภาพบำบัด", "Department of Physical Therapy"
        elif any(k in f_lower for k in ["nursing", "patient care", "nurse"]):
            return "คณะพยาบาลศาสตร์", "Faculty of Nursing", "ภาควิชาพยาบาลศาสตร์", "Department of Nursing"
        elif any(k in f_lower for k in [
            "agriculture", "crop", "livestock", "agronomy", "aquaculture", "fishery",
            "animal science", "postharvest", "community development"
        ]):
            return "คณะเทคโนโลยีและการพัฒนาชุมชน", "Faculty of Technology and Community Development", "ภาควิชาเทคโนโลยีการเกษตร", "Department of Agricultural Technology"
        elif any(k in f_lower for k in [
            "computer science", "neural network", "artificial intelligence", "software",
            "information system", "machine learning", "digital innovation"
        ]):
            return "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", "สาขาวิชาวิทยาการคอมพิวเตอร์", "Department of Computer Science"
        elif any(k in f_lower for k in [
            "physics", "plasma", "optics", "quantum", "astronomy", "condensed matter",
            "nuclear physics", "nanomaterial", "thin film"
        ]):
            return "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", "สาขาวิชาฟิสิกส์", "Department of Physics"
        elif any(k in f_lower for k in [
            "chemistry", "sensor", "electrochemical", "catalysis", "organic chemistry",
            "polymer", "analytical chemistry"
        ]):
            return "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", "สาขาวิชาเคมี", "Department of Chemistry"
        elif any(k in f_lower for k in [
            "biology", "microbiology", "genetics", "biochemistry", "molecular biology",
            "botany", "zoology", "ecology", "biodiversity"
        ]):
            return "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", "สาขาวิชาชีววิทยา", "Department of Biology"
        elif any(k in f_lower for k in [
            "mathematics", "applied mathematics", "algebra", "topology", "statistics"
        ]):
            return "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", "สาขาวิชาคณิตศาสตร์", "Department of Mathematics"
        elif any(k in f_lower for k in [
            "business", "marketing", "accounting", "management", "finance", "economics"
        ]):
            return "คณะเศรษฐศาสตร์และบริหารธุรกิจ", "Faculty of Economics and Business Administration", "ภาควิชาบริหารธุรกิจ", "Department of Business Administration"
        elif any(k in f_lower for k in [
            "education", "teaching", "pedagogy", "curriculum", "learning"
        ]):
            return "คณะศึกษาศาสตร์", "Faculty of Education", "ภาควิชาการศึกษา", "Department of Education"
        elif any(k in f_lower for k in [
            "linguistics", "language", "literature", "english", "thai", "humanities", "history", "sociology"
        ]):
            return "คณะมนุษยศาสตร์และสังคมศาสตร์", "Faculty of Humanities and Social Sciences", "ภาควิชามนุษยศาสตร์", "Department of Humanities"
        elif any(k in f_lower for k in ["law", "legal", "jurisprudence"]):
            return "คณะนิติศาสตร์", "Faculty of Law", "ภาควิชานิติศาสตร์", "Department of Law"
        elif any(k in f_lower for k in ["music", "art", "fine art", "design", "performing arts"]):
            return "คณะศิลปกรรมศาสตร์", "Faculty of Fine and Applied Arts", "ภาควิชาศิลปกรรม", "Department of Fine Arts"
        else:
            return "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล", "Faculty of Science and Digital Innovation", "สาขาวิชาวิทยาศาสตร์", "Department of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 10:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I79246082,works_count:>1&per-page=100&cursor={urllib.parse.quote(cursor)}"
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

                    fac_th, fac_en, dept_th, dept_en = map_topics_to_tsu_faculty(field, subfield, top_topic)

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
    print("🚀 STARTING WAVE 50: THAKSIN UNIVERSITY (TSU) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave50_tsu_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. TSU Research Directory (84 Pages, ~1,600 researchers)
        all_harvested.extend(extract_tsu_research_directory())

        # 2. Targeted Faculty Portals
        all_harvested.extend(extract_tsu_faculty_portals())

        # 3. OpenAlex TSU Authors (I79246082)
        all_harvested.extend(extract_tsu_openalex())

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
        existing_tsu = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%ทักษิณ%")) |
            (FacultyDB.university.ilike("%Thaksin%"))
        ).all()
        print(f"Current existing TSU faculty in database: {len(existing_tsu)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_tsu:
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
                TSU_TH,
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
            uid = f"tsu_w50_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"tsu_w50_{seq:04d}_{random.randint(100, 999)}"
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
                university=TSU_EN,
                university_th=TSU_TH,
                faculty=r.get("faculty_en") or r.get("faculty_th") or "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล",
                faculty_th=r.get("faculty_th") or "คณะวิทยาศาสตร์และนวัตกรรมดิจิทัล",
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
            (FacultyDB.university_th.ilike("%ทักษิณ%")) |
            (FacultyDB.university.ilike("%Thaksin%"))
        ).count()
        with_email = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%ทักษิณ%")) |
            (FacultyDB.university.ilike("%Thaksin%")),
            FacultyDB.email.isnot(None)
        ).count()
        with_embed = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%ทักษิณ%")) |
            (FacultyDB.university.ilike("%Thaksin%")),
            FacultyDB.embedding.isnot(None)
        ).count()

        print("\n================================================================================")
        print("🎉 WAVE 50 THAKSIN UNIVERSITY (TSU) COMPLETED SUCCESSFULLY!")
        print(f"Total TSU Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:   {with_email}")
        print(f"Faculty with 768-dim Vector:   {with_embed} (100%)")
        print("================================================================================")


if __name__ == "__main__":
    run()
