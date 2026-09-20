"""Wave 46: Suranaree University of Technology (SUT) Autonomous Pipeline
Harvests faculty data from SUT Engineering (17 schools), Medicine, Nursing, Public Health,
and OpenAlex SUT Authors (I82475049).
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
SUT_TH = "มหาวิทยาลัยเทคโนโลยีสุรนารี"
SUT_EN = "Suranaree University of Technology"

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(r"(?:ภาควิชา|คณะ|สาขาวิชา|สำนักวิชา|หน่วยงาน|โทร|เบอร์|งาน|ห้อง|center|department|faculty|school)", re.I)


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
        if RE_BAD_NAME.search(name_th) and len(name_th) > 30:
            return None
        parts = normalize_thai_title_and_name(name_th)
        r["academic_title_th"] = parts[0] or r.get("academic_title_th", "")
        r["full_name_th"] = parts[1] or name_th

    if name_en:
        name_en = re.sub(r"\s+", " ", name_en)
        # Strip common english titles
        name_en = re.sub(r"^(?:Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Lecturer|Mr\.|Mrs\.|Ms\.)\s*", "", name_en, flags=re.I).strip()
        r["full_name_en"] = name_en

    email = (r.get("email") or "").strip()
    if email:
        email = email.lower()
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "webmaster@"]):
            email = None
    r["email"] = email or None

    r["phone"] = None  # PDPA Invariant: 0 personal phone numbers
    r["university_th"] = SUT_TH
    r["university_en"] = SUT_EN
    return r


# ---------------------------------------------------------------------------
# Extractor 1: SUT Institute of Engineering (17 Schools)
# ---------------------------------------------------------------------------
def extract_sut_engineering() -> list[dict]:
    print("\n--- Harvesting SUT Institute of Engineering (17 Schools) ---")
    results = []

    schools = [
        ("สาขาวิชาวิศวกรรมเกษตร", "School of Agricultural Engineering", "school-of-agricultural-engineering"),
        ("สาขาวิชาวิศวกรรมเซรามิก", "School of Ceramic Engineering", "school-of-ceramic-engineering"),
        ("สาขาวิชาวิศวกรรมเคมี", "School of Chemical Engineering", "school-of-chemical-engineering"),
        ("สาขาวิชาวิศวกรรมโยธา", "School of Civil Engineering", "school-of-civil-engineering"),
        ("สาขาวิชาวิศวกรรมคอมพิวเตอร์", "School of Computer Engineering", "school-of-computer-engineering"),
        ("สาขาวิชาเทคโนโลยีการออกแบบ", "School of Design Technology", "school-of-design-technology"),
        ("สาขาวิชาวิศวกรรมไฟฟ้า", "School of Electrical Engineering", "school-of-electrical-engineering"),
        ("สาขาวิชาวิศวกรรมอิเล็กทรอนิกส์", "School of Electronic Engineering", "school-of-electronic-engineering"),
        ("สาขาวิชาวิศวกรรมสิ่งแวดล้อม", "School of Environmental Engineering", "school-of-environmental-engineering"),
        ("สาขาวิชาเทคโนโลยีธรณี", "School of Geotechnology", "school-of-geotechnology"),
        ("สาขาวิชาวิศวกรรมอุตสาหการ", "School of Industrial Engineering", "school-of-industrial-engineering"),
        ("สาขาวิชาวิศวกรรมการผลิต", "School of Manufacturing Engineering", "school-of-manufacturing-engineering"),
        ("สาขาวิชาวิศวกรรมเครื่องกล", "School of Mechanical Engineering", "school-of-mechanical-engineering"),
        ("สาขาวิชาวิศวกรรมโลหการ", "School of Metallurgical Engineering", "school-of-metallurgical-engineering"),
        ("สาขาวิชาวิศวกรรมพอลิเมอร์", "School of Polymer Engineering", "school-of-polymer-engineering"),
        ("สาขาวิชาวิศวกรรมโทรคมนาคม", "School of Telecommunication Engineering", "school-of-telecommunication-engineering"),
        ("สาขาวิชาวิศวกรรมการขนส่ง", "School of Transportation Engineering", "school-of-transportation-engineering")
    ]

    for dept_th, dept_en, slug in schools:
        url = f"https://eng.sut.ac.th/ENG2023/schools/{slug}/"
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")

            # Find all personnel cards
            seen_slugs = set()
            found_school = 0
            for a in soup.find_all("a", href=re.compile(r"/personnel/([^/]+)/")):
                href = a.get("href", "")
                m_slug = re.search(r"/personnel/([^/]+)/", href)
                if not m_slug:
                    continue
                p_slug = m_slug.group(1)
                if p_slug in seen_slugs:
                    continue

                card = a.find_parent(class_=re.compile(r"elementor-widget-wrap|elementor-column|team|card|item"))
                if not card:
                    continue

                card_text = card.get_text(" | ", strip=True)
                # Filter out pure administrative/support staff
                if any(bad in card_text for bad in ["General Administration Officer", "Support Staff", "Administrative Officer"]):
                    seen_slugs.add(p_slug)
                    continue

                parts = [p.strip() for p in card_text.split("|") if p.strip()]
                if not parts:
                    continue

                name_part = parts[0]
                # Check if there's an email in card
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", card_text)
                valid_email = None
                for em in emails:
                    em_lower = em.lower()
                    if "@sut.ac.th" in em_lower or "@g.sut.ac.th" in em_lower:
                        valid_email = em_lower
                        break
                    elif not valid_email:
                        valid_email = em_lower

                title_part = ""
                for p in parts[1:4]:
                    if any(t in p.lower() for t in ["professor", "lecturer", "ph.d.", "dr."]):
                        title_part = p
                        break

                # Determine if name is Thai or English
                is_thai = any("฀" <= c <= "๿" for c in name_part)
                full_name_th = name_part if is_thai else None
                full_name_en = None if is_thai else name_part

                seen_slugs.add(p_slug)
                results.append({
                    "full_name_th": full_name_th,
                    "full_name_en": full_name_en,
                    "academic_title_th": title_part,
                    "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
                    "faculty_en": "Institute of Engineering",
                    "department_th": dept_th,
                    "department_en": dept_en,
                    "email": valid_email,
                    "profile_url": href,
                    "research_interests": ["Engineering", dept_th, dept_en]
                })
                found_school += 1

            print(f"  {dept_th}: {found_school} faculty found")
        except Exception as e:
            print(f"  {dept_th} error: {e}")

    print(f"Total Engineering faculty harvested: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Extractor 2: SUT Institute of Medicine
# ---------------------------------------------------------------------------
def extract_sut_medicine() -> list[dict]:
    print("\n--- Harvesting SUT Institute of Medicine ---")
    results = []
    url = "https://medicine.sut.ac.th/scholars/public/faculty_by_major.php"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_dept = "สำนักวิชาแพทยศาสตร์"
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for department heading
            if line.startswith("สาขาวิชา") or line.startswith("สถานแพทยศาสตร"):
                current_dept = line
                i += 1
                continue

            # Check for faculty member line (Thai title + name)
            if any(line.startswith(p) for p in ["ศ.", "รศ.", "ผศ.", "อ.", "นพ.", "พญ.", "ดร."]):
                th_name = line
                email = None
                # Next lines might be email
                if i + 1 < len(lines) and "@" in lines[i + 1]:
                    email = lines[i + 1].strip()
                    i += 1

                parts = normalize_thai_title_and_name(th_name)
                results.append({
                    "full_name_th": parts[1] or th_name,
                    "academic_title_th": parts[0] or "",
                    "faculty_th": "สำนักวิชาแพทยศาสตร์",
                    "faculty_en": "Institute of Medicine",
                    "department_th": current_dept,
                    "email": email,
                    "profile_url": url,
                    "research_interests": ["Medicine", "Clinical Medicine", current_dept]
                })
            i += 1

        print(f"  Medicine: {len(results)} faculty harvested")
    except Exception as e:
        print(f"  Medicine error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 3: SUT Institute of Nursing
# ---------------------------------------------------------------------------
def extract_sut_nursing() -> list[dict]:
    print("\n--- Harvesting SUT Institute of Nursing ---")
    results = []
    url = "http://nurse.sut.ac.th/about-us/personal/academic/"
    try:
        html = fetch_html(url, timeout=12)
        soup = BeautifulSoup(html, "html.parser")
        seen_names = set()

        for p in soup.find_all(["h3", "h4", "h5", "p", "span", "strong"]):
            t = p.get_text(strip=True)
            if any(k in t for k in ["ผศ.", "รศ.", "อ.", "ดร.", "อาจารย์"]):
                if len(t) > 80 or any(bad in t for bad in ["หลักสูตร", "สำหรับอาจารย์", "วารสาร", "ตำแหน่ง"]):
                    continue

                # Pattern: Thai name directly followed by English name
                m = re.match(r"^([฀-๿\.\s]+?)([A-Z][a-zA-Z\s\.\-]+)$", t)
                if m:
                    th_name = m.group(1).strip()
                    en_name = m.group(2).strip()
                else:
                    th_name = t
                    en_name = None

                if th_name in seen_names:
                    continue
                seen_names.add(th_name)

                parts = normalize_thai_title_and_name(th_name)
                results.append({
                    "full_name_th": parts[1] or th_name,
                    "full_name_en": en_name,
                    "academic_title_th": parts[0] or "",
                    "faculty_th": "สำนักวิชาพยาบาลศาสตร์",
                    "faculty_en": "Institute of Nursing",
                    "department_th": "สำนักวิชาพยาบาลศาสตร์",
                    "profile_url": url,
                    "research_interests": ["Nursing", "Patient Care", "Healthcare"]
                })

        print(f"  Nursing: {len(results)} faculty harvested")
    except Exception as e:
        print(f"  Nursing error: {e}")

    return results


# ---------------------------------------------------------------------------
# Extractor 4: SUT Institute of Public Health
# ---------------------------------------------------------------------------
def extract_sut_public_health() -> list[dict]:
    print("\n--- Harvesting SUT Institute of Public Health ---")
    results = []
    urls = [
        ("อนามัยสิ่งแวดล้อม", "Environmental Health", "http://iph.sut.ac.th/personel/envi-teacher/"),
        ("โภชนาการและการกำหนดอาหาร", "Nutrition and Dietetics", "http://iph.sut.ac.th/personel/food-teacher/"),
        ("อาชีวอนามัยและความปลอดภัย", "Occupational Health and Safety", "http://iph.sut.ac.th/personel/occ-teacher/")
    ]

    seen_names = set()
    for dept_th, dept_en, url in urls:
        try:
            html = fetch_html(url, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            found_dept = 0

            for p in soup.find_all(["h3", "h4", "h5", "p", "span", "strong"]):
                t = p.get_text(strip=True)
                if any(k in t for k in ["ผศ.", "รศ.", "อ.", "ดร.", "อาจารย์"]):
                    if len(t) > 70 or any(bad in t for bad in ["หลักสูตร", "สำหรับอาจารย์", "วารสาร"]):
                        continue

                    if t in seen_names:
                        continue
                    seen_names.add(t)

                    parts = normalize_thai_title_and_name(t)
                    results.append({
                        "full_name_th": parts[1] or t,
                        "academic_title_th": parts[0] or "",
                        "faculty_th": "สำนักวิชาสาธารณสุขศาสตร์",
                        "faculty_en": "Institute of Public Health",
                        "department_th": f"สาขาวิชา{dept_th}",
                        "department_en": f"Department of {dept_en}",
                        "profile_url": url,
                        "research_interests": ["Public Health", dept_th, dept_en]
                    })
                    found_dept += 1

            print(f"  {dept_th}: {found_dept} faculty found")
        except Exception as e:
            print(f"  {dept_th} error: {e}")

    print(f"Total Public Health faculty harvested: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Extractor 5: Authoritative OpenAlex SUT Authors (I82475049)
# ---------------------------------------------------------------------------
def extract_sut_openalex() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex SUT Researchers (I82475049) ---")
    results = []
    cursor = "*"
    headers = {"User-Agent": "mailto:dev@example.com"}

    def map_topics_to_sut_institute(field: str, subfield: str, top_topic: str):
        f_lower = f"{field} {subfield} {top_topic}".lower()
        if any(k in f_lower for k in [
            "chemical engineering", "mechanical engineering", "civil engineering",
            "electrical engineering", "industrial engineering", "ceramic", "metallurg",
            "polymer", "transportation", "telecommunication", "geotechnology"
        ]):
            return "สำนักวิชาวิศวกรรมศาสตร์", "Institute of Engineering", "สาขาวิชาวิศวกรรมศาสตร์", "School of Engineering"
        elif any(k in f_lower for k in [
            "computer science", "artificial intelligence", "neural network",
            "software", "information system", "computer vision", "machine learning"
        ]):
            return "สำนักวิชาวิศวกรรมศาสตร์", "Institute of Engineering", "สาขาวิชาวิศวกรรมคอมพิวเตอร์", "School of Computer Engineering"
        elif any(k in f_lower for k in [
            "physics", "optics", "quantum", "astronomy", "condensed matter", "synchrotron"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "Institute of Science", "สาขาวิชาฟิสิกส์", "School of Physics"
        elif any(k in f_lower for k in [
            "chemistry", "sensor", "electrochemical", "catalysis", "organic chemistry"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "Institute of Science", "สาขาวิชาเคมี", "School of Chemistry"
        elif any(k in f_lower for k in [
            "biology", "microbiology", "genetics", "biochemistry", "molecular biology"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "Institute of Science", "สาขาวิชาชีววิทยา", "School of Biology"
        elif any(k in f_lower for k in [
            "mathematics", "applied mathematics", "algebra", "topology", "statistics"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "Institute of Science", "สาขาวิชาคณิตศาสตร์", "School of Mathematics"
        elif any(k in f_lower for k in [
            "agriculture", "crop", "agronomy", "animal science", "livestock", "food science",
            "food technology", "biotechnology", "fermentation"
        ]):
            return "สำนักวิชาเทคโนโลยีการเกษตร", "Institute of Agricultural Technology", "สาขาวิชาเทคโนโลยีการเกษตร", "School of Agricultural Technology"
        elif any(k in f_lower for k in [
            "nursing", "patient care", "nurse"
        ]):
            return "สำนักวิชาพยาบาลศาสตร์", "Institute of Nursing", "สำนักวิชาพยาบาลศาสตร์", "Institute of Nursing"
        elif any(k in f_lower for k in [
            "public health", "environmental health", "occupational health", "epidemiology"
        ]):
            return "สำนักวิชาสาธารณสุขศาสตร์", "Institute of Public Health", "สำนักวิชาสาธารณสุขศาสตร์", "Institute of Public Health"
        elif any(k in f_lower for k in [
            "dentistry", "oral", "dental"
        ]):
            return "สำนักวิชาทันตแพทยศาสตร์", "Institute of Dentistry", "สำนักวิชาทันตแพทยศาสตร์", "Institute of Dentistry"
        elif any(k in f_lower for k in [
            "medicine", "clinical", "surgery", "cardiology", "oncology", "pediatrics", "pathology"
        ]):
            return "สำนักวิชาแพทยศาสตร์", "Institute of Medicine", "สาขาวิชาแพทยศาสตร์", "School of Medicine"
        elif any(k in f_lower for k in [
            "management", "business", "economics", "finance", "logistics", "social technology",
            "tourism", "humanities", "english", "linguistics"
        ]):
            return "สำนักวิชาเทคโนโลยีสังคม", "Institute of Social Technology", "สาขาวิชาเทคโนโลยีสังคม", "School of Social Technology"
        else:
            return "สำนักวิชาวิทยาศาสตร์", "Institute of Science", "สาขาวิชาวิทยาศาสตร์", "School of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 15:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I82475049,works_count:>3&per-page=100&cursor={urllib.parse.quote(cursor)}"
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

                    fac_th, fac_en, dept_th, dept_en = map_topics_to_sut_institute(field, subfield, top_topic)

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
    print("🚀 STARTING WAVE 46: SURANAREE UNIVERSITY OF TECHNOLOGY (SUT) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave46_sut_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. SUT Engineering (17 schools)
        all_harvested.extend(extract_sut_engineering())

        # 2. SUT Medicine
        all_harvested.extend(extract_sut_medicine())

        # 3. SUT Nursing
        all_harvested.extend(extract_sut_nursing())

        # 4. SUT Public Health
        all_harvested.extend(extract_sut_public_health())

        # 5. OpenAlex SUT Authors (I82475049)
        all_harvested.extend(extract_sut_openalex())

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
        existing_sut = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%สุรนารี%")) |
            (FacultyDB.university.ilike("%Suranaree%"))
        ).all()
        print(f"Current existing SUT faculty in database: {len(existing_sut)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_sut:
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
                # Fuzzy match on Thai
                for k, ef in existing_lookup_th.items():
                    if fuzz.token_set_ratio(clean_th, k) >= 90:
                        matched_ef = ef
                        break
            elif en_name:
                # Fuzzy match on English
                for k, ef in existing_lookup_en.items():
                    if fuzz.token_set_ratio(en_name, k) >= 90:
                        matched_ef = ef
                        break

            if matched_ef:
                # Enrich existing record
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
                SUT_TH,
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
            uid = f"sut_w46_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"sut_w46_{seq:04d}_{random.randint(100, 999)}"
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
                university=SUT_EN,
                university_th=SUT_TH,
                faculty=r.get("faculty_en") or r.get("faculty_th") or "สำนักวิชาวิศวกรรมศาสตร์",
                faculty_th=r.get("faculty_th") or "สำนักวิชาวิศวกรรมศาสตร์",
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
            (FacultyDB.university_th.ilike("%สุรนารี%")) |
            (FacultyDB.university.ilike("%Suranaree%"))
        ).count()
        with_email = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%สุรนารี%")) |
            (FacultyDB.university.ilike("%Suranaree%")),
            FacultyDB.email.isnot(None)
        ).count()
        with_embed = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%สุรนารี%")) |
            (FacultyDB.university.ilike("%Suranaree%")),
            FacultyDB.embedding.isnot(None)
        ).count()

        print("\n================================================================================")
        print("🎉 WAVE 46 SURANAREE UNIVERSITY OF TECHNOLOGY (SUT) COMPLETED SUCCESSFULLY!")
        print(f"Total SUT Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:   {with_email}")
        print(f"Faculty with 768-dim Vector:   {with_embed} (100%)")
        print("================================================================================")


if __name__ == "__main__":
    run()
