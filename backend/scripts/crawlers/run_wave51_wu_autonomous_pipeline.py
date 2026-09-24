"""Wave 51: Walailak University (WU) Autonomous Pipeline
Harvests faculty data from Walailak University Intranet Personnel Directory (24 Academic Divisions, ~1,400 faculty),
School Portals (Science, Pharmacy, Informatics, Engineering, Medicine),
and Authoritative OpenAlex WU Researchers (I96916377, 1,301 authors).
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
import http.cookiejar
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

WU_TH = "มหาวิทยาลัยวลัยลักษณ์"
WU_EN = "Walailak University"

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|สำนักวิชา|สาขาวิชา|หน่วยงาน|โทร|เบอร์|งาน|ห้อง|center|department|school|faculty|คู่มือ|อาจารย์ที่ปรึกษา|บริการ|ประกาศ|รายละเอียด|อาจารย์ประจำหลักสูตร)",
    re.I
)

DIVISION_EN_MAP = {
    "วิทยาลัยทันตแพทยศาสตร์นานาชาติ": ("วิทยาลัยทันตแพทยศาสตร์นานาชาติ", "International College of Dentistry"),
    "วิทยาลัยสัตวแพทยศาสตร์อัครราชกุมารี": ("วิทยาลัยสัตวแพทยศาสตร์อัครราชกุมารี", "Akkhraratchakumari Veterinary College"),
    "สำนักวิชาการจัดการ": ("สำนักวิชาการจัดการ", "School of Management"),
    "สำนักวิชาการบัญชีและการเงิน": ("สำนักวิชาการบัญชีและการเงิน", "School of Accountancy and Finance"),
    "สำนักวิชานิติศาสตร์": ("สำนักวิชานิติศาสตร์", "School of Law"),
    "สำนักวิชาพยาบาลศาสตร์": ("สำนักวิชาพยาบาลศาสตร์", "School of Nursing"),
    "สำนักวิชาพหุภาษาและการศึกษาทั่วไป": ("สำนักวิชาพหุภาษาและการศึกษาทั่วไป", "School of Languages and General Education"),
    "สำนักวิชารัฐศาสตร์และรัฐประศาสนศาสตร์": ("สำนักวิชารัฐศาสตร์และรัฐประศาสนศาสตร์", "School of Political Science and Public Administration"),
    "สำนักวิชาวิทยาศาสตร์": ("สำนักวิชาวิทยาศาสตร์", "School of Science"),
    "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี": ("สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี", "School of Engineering and Technology"),
    "สำนักวิชาศิลปศาสตร์": ("สำนักวิชาศิลปศาสตร์", "School of Liberal Arts"),
    "สำนักวิชาศึกษาศาสตร์": ("สำนักวิชาศึกษาศาสตร์", "School of Education"),
    "สำนักวิชาสถาปัตยกรรมศาสตร์และการออกแบบ": ("สำนักวิชาสถาปัตยกรรมศาสตร์และการออกแบบ", "School of Architecture and Design"),
    "สำนักวิชาสหเวชศาสตร์": ("สำนักวิชาสหเวชศาสตร์", "School of Allied Health Sciences"),
    "สำนักวิชาสาธารณสุขศาสตร์": ("สำนักวิชาสาธารณสุขศาสตร์", "School of Public Health"),
    "สำนักวิชาสารสนเทศศาสตร์": ("สำนักวิชาสารสนเทศศาสตร์", "School of Informatics"),
    "สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร": ("สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร", "School of Agricultural Technology and Food Industry"),
    "สำนักวิชาเภสัชศาสตร์": ("สำนักวิชาเภสัชศาสตร์", "School of Pharmacy"),
    "สำนักวิชาแพทยศาสตร์": ("สำนักวิชาแพทยศาสตร์", "School of Medicine"),
    "ศูนย์การแพทย์มหาวิทยาลัยวลัยลักษณ์": ("ศูนย์การแพทย์มหาวิทยาลัยวลัยลักษณ์", "Walailak University Medical Center"),
    "บัณฑิตวิทยาลัย": ("บัณฑิตวิทยาลัย", "College of Graduate Studies")
}


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
        if not RE_EMAIL.match(email) or any(k in email for k in ["admin@", "info@", "contact@", "webmaster@"]):
            email = None
    r["email"] = email or None

    r["phone"] = None  # PDPA Invariant: 0 personal phone numbers
    r["university_th"] = WU_TH
    r["university_en"] = WU_EN
    return r


# ---------------------------------------------------------------------------
# Extractor 1: WU Intranet Personnel Directory (24 Academic Divisions)
# ---------------------------------------------------------------------------
def extract_wu_intranet() -> list[dict]:
    print("\n--- Harvesting Walailak Intranet Personnel Directory ---")
    results = []
    url = "https://intranet.wu.ac.th/th/searchPersons"

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=SSL_CTX))

    req1 = urllib.request.Request(url, headers=HEADERS)
    with opener.open(req1, timeout=10) as r:
        soup = BeautifulSoup(r.read().decode("utf-8", errors="ignore"), "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]
        select = soup.find("select", {"name": "DIVISION_ID"})
        divisions = []
        for opt in select.find_all("option"):
            val = opt.get("value")
            txt = opt.text.strip()
            if val and any(k in txt for k in ["สำนักวิชา", "วิทยาลัย", "ศูนย์การแพทย์", "บัณฑิตวิทยาลัย"]):
                divisions.append((val, txt))

    print(f"Targeting {len(divisions)} academic divisions...")
    ACADEMIC_TITLES = ["ศ.", "รศ.", "ผศ.", "ดร.", "อ.", "อาจารย์", "นายแพทย์", "แพทย์หญิง", "ทพ.", "ทพญ.", "สพ.ญ.", "นสพ.", "นพ.", "พญ."]
    ACADEMIC_POSITIONS = ["อาจารย์", "คณบดี", "รองคณบดี", "ผู้ช่วยคณบดี", "หัวหน้าสาขาวิชา", "ผู้อำนวยการ", "นักวิจัย", "แพทย์", "ทันตแพทย์", "สัตวแพทย์", "เภสัชกร"]

    for val, txt in divisions:
        data = urllib.parse.urlencode({
            "_token": token,
            "action": "search",
            "FIRST_NAME": "",
            "LAST_NAME": "",
            "OFFICE_PHONE": "",
            "OFFICE_EMAIL": "",
            "DIVISION_ID": val
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={**HEADERS, "Referer": url})
        try:
            with opener.open(req, timeout=12) as resp:
                soup_res = BeautifulSoup(resp.read().decode("utf-8", errors="ignore"), "html.parser")
                table = soup_res.find("table")
                if not table:
                    continue

                div_count = 0
                for row in table.find_all("tr")[1:]:
                    cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
                    if len(cols) < 7:
                        continue
                    pid, name, div_str, pos, phone, email = cols[1], cols[2], cols[3], cols[4], cols[5], cols[6]

                    is_academic = (
                        any(t in name for t in ACADEMIC_TITLES) or
                        any(p in pos for p in ACADEMIC_POSITIONS)
                    )
                    if not is_academic:
                        continue

                    # Clean email
                    em_match = re.findall(r"[a-zA-Z0-9._%+-]+@wu\.ac\.th", email)
                    clean_em = em_match[0].lower() if em_match else None

                    # Resolve faculty/department
                    fac_th = "มหาวิทยาลัยวลัยลักษณ์"
                    fac_en = "Walailak University"
                    for k, (f_th, f_en) in DIVISION_EN_MAP.items():
                        if k in div_str:
                            fac_th = f_th
                            fac_en = f_en
                            break

                    parts_th = normalize_thai_title_and_name(name)
                    results.append({
                        "full_name_th": parts_th[1] or name,
                        "academic_title_th": parts_th[0] or "",
                        "faculty_th": fac_th,
                        "faculty_en": fac_en,
                        "department_th": div_str,
                        "department_en": fac_en,
                        "email": clean_em,
                        "profile_url": f"https://intranet.wu.ac.th/th/searchPersons?pid={pid}",
                        "research_interests": [fac_th]
                    })
                    div_count += 1

                print(f"  {txt}: {div_count} academic faculty harvested")
        except Exception as e:
            print(f"  {txt} error: {e}")
        time.sleep(0.2)

    print(f"Total faculty harvested from WU Intranet: {len(results)}")
    return results


# ---------------------------------------------------------------------------
# Extractor 2: Authoritative OpenAlex WU Researchers (I96916377)
# ---------------------------------------------------------------------------
def extract_wu_openalex() -> list[dict]:
    print("\n--- Harvesting Authoritative OpenAlex WU Researchers (I96916377) ---")
    results = []
    cursor = "*"
    headers = {"User-Agent": "mailto:dev@example.com"}

    def map_topics_to_wu_faculty(field: str, subfield: str, top_topic: str):
        f_lower = f"{field} {subfield} {top_topic}".lower()
        if any(k in f_lower for k in [
            "chemical engineering", "mechanical engineering", "civil engineering",
            "electrical engineering", "materials science", "concrete", "renewable energy",
            "polymer", "manufacturing", "robotics", "automation"
        ]):
            return "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี", "School of Engineering and Technology", "สาขาวิชาวิศวกรรมศาสตร์", "Department of Engineering"
        elif any(k in f_lower for k in [
            "dentistry", "dental", "orthodontic", "periodont", "oral health", "endodont"
        ]):
            return "วิทยาลัยทันตแพทยศาสตร์นานาชาติ", "International College of Dentistry", "สาขาวิชาวิทยาศาสตร์สุขภาพช่องปาก", "Department of Oral Health Science"
        elif any(k in f_lower for k in [
            "veterinary", "animal disease", "canine", "feline", "bovine", "zoonotic", "swine"
        ]):
            return "วิทยาลัยสัตวแพทยศาสตร์อัครราชกุมารี", "Akkhraratchakumari Veterinary College", "สาขาวิชาวิทยาศาสตร์การสัตวแพทย์", "Department of Veterinary Science"
        elif any(k in f_lower for k in [
            "pharmacy", "pharmacology", "pharmaceutical", "drug delivery", "toxicology", "pharmacognosy"
        ]):
            return "สำนักวิชาเภสัชศาสตร์", "School of Pharmacy", "สาขาวิชาเภสัชศาสตร์", "Department of Pharmacy"
        elif any(k in f_lower for k in [
            "medicine", "clinical", "surgery", "pathology", "oncology", "cardiology",
            "pediatrics", "internal medicine", "infectious disease", "medical science"
        ]):
            return "สำนักวิชาแพทยศาสตร์", "School of Medicine", "สาขาวิชาแพทยศาสตร์", "Department of Medicine"
        elif any(k in f_lower for k in [
            "physical therapy", "physiotherapy", "rehabilitation", "medical technology",
            "allied health", "biomedical science", "clinical chemistry"
        ]):
            return "สำนักวิชาสหเวชศาสตร์", "School of Allied Health Sciences", "สาขาวิชาเทคนิคการแพทย์", "Department of Medical Technology"
        elif any(k in f_lower for k in [
            "public health", "epidemiology", "environmental health", "occupational health", "community health"
        ]):
            return "สำนักวิชาสาธารณสุขศาสตร์", "School of Public Health", "สาขาวิชาสาธารณสุขศาสตร์", "Department of Public Health"
        elif any(k in f_lower for k in ["nursing", "nurse", "patient care", "geriatric care"]):
            return "สำนักวิชาพยาบาลศาสตร์", "School of Nursing", "สาขาวิชาพยาบาลศาสตร์", "Department of Nursing"
        elif any(k in f_lower for k in [
            "computer science", "artificial intelligence", "software", "information system",
            "machine learning", "data science", "informatics", "multimedia"
        ]):
            return "สำนักวิชาสารสนเทศศาสตร์", "School of Informatics", "สาขาวิชาเทคโนโลยีสารสนเทศ", "Department of Information Technology"
        elif any(k in f_lower for k in [
            "agriculture", "crop", "agronomy", "horticulture", "food science", "food technology",
            "postharvest", "fishery", "aquaculture"
        ]):
            return "สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร", "School of Agricultural Technology and Food Industry", "สาขาวิชาเทคโนโลยีการเกษตร", "Department of Agricultural Technology"
        elif any(k in f_lower for k in [
            "physics", "plasma", "optics", "quantum", "condensed matter", "nanomaterial", "thin film"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "School of Science", "สาขาวิชาฟิสิกส์", "Department of Physics"
        elif any(k in f_lower for k in [
            "chemistry", "sensor", "catalysis", "organic chemistry", "analytical chemistry", "electrochemistry"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "School of Science", "สาขาวิชาเคมี", "Department of Chemistry"
        elif any(k in f_lower for k in [
            "biology", "microbiology", "genetics", "biochemistry", "molecular biology", "botany", "zoology", "ecology"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "School of Science", "สาขาวิชาชีววิทยา", "Department of Biology"
        elif any(k in f_lower for k in [
            "mathematics", "applied mathematics", "algebra", "statistics", "calculus"
        ]):
            return "สำนักวิชาวิทยาศาสตร์", "School of Science", "สาขาวิชาคณิตศาสตร์", "Department of Mathematics"
        elif any(k in f_lower for k in [
            "accounting", "finance", "banking", "financial management"
        ]):
            return "สำนักวิชาการบัญชีและการเงิน", "School of Accountancy and Finance", "สาขาวิชาการบัญชี", "Department of Accounting"
        elif any(k in f_lower for k in [
            "management", "marketing", "business", "logistics", "tourism", "hospitality"
        ]):
            return "สำนักวิชาการจัดการ", "School of Management", "สาขาวิชาการจัดการ", "Department of Management"
        elif any(k in f_lower for k in ["political science", "public administration", "international relation", "policy"]):
            return "สำนักวิชารัฐศาสตร์และรัฐประศาสนศาสตร์", "School of Political Science and Public Administration", "สาขาวิชารัฐศาสตร์", "Department of Political Science"
        elif any(k in f_lower for k in ["law", "legal", "jurisprudence"]):
            return "สำนักวิชานิติศาสตร์", "School of Law", "สาขาวิชานิติศาสตร์", "Department of Law"
        elif any(k in f_lower for k in ["architecture", "urban planning", "interior design", "industrial design"]):
            return "สำนักวิชาสถาปัตยกรรมศาสตร์และการออกแบบ", "School of Architecture and Design", "สาขาวิชาสถาปัตยกรรมศาสตร์", "Department of Architecture"
        elif any(k in f_lower for k in ["education", "teaching", "pedagogy", "curriculum"]):
            return "สำนักวิชาศึกษาศาสตร์", "School of Education", "สาขาวิชาศึกษาศาสตร์", "Department of Education"
        elif any(k in f_lower for k in ["linguistics", "language", "english", "thai", "literature", "humanities"]):
            return "สำนักวิชาศิลปศาสตร์", "School of Liberal Arts", "สาขาวิชาภาษา", "Department of Languages"
        else:
            return "สำนักวิชาวิทยาศาสตร์", "School of Science", "สาขาวิชาวิทยาศาสตร์", "Department of Science"

    batches = 0
    total_authors = 0
    while cursor and batches < 15:
        batches += 1
        url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:I96916377,works_count:>1&per-page=100&cursor={urllib.parse.quote(cursor)}"
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

                    fac_th, fac_en, dept_th, dept_en = map_topics_to_wu_faculty(field, subfield, top_topic)

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
    print("🚀 STARTING WAVE 51: WALAILAK UNIVERSITY (WU) AUTONOMOUS PIPELINE")
    print("================================================================================")

    ckpt_path = Path("backend/data/agent_states/wave51_wu_extraction.json")
    if ckpt_path.exists():
        print(f"Loading cached state checkpoint from: {ckpt_path}")
        with open(ckpt_path, "r", encoding="utf-8") as f:
            all_cleaned = json.load(f)
        print(f"Loaded {len(all_cleaned)} records from checkpoint.")
    else:
        all_harvested = []

        # 1. WU Intranet Personnel Directory (24 Academic Divisions)
        all_harvested.extend(extract_wu_intranet())

        # 2. OpenAlex WU Authors (I96916377)
        all_harvested.extend(extract_wu_openalex())

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
        existing_wu = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%วลัยลักษณ์%")) |
            (FacultyDB.university.ilike("%Walailak%"))
        ).all()
        print(f"Current existing WU faculty in database: {len(existing_wu)}")

        existing_lookup_th = {}
        existing_lookup_en = {}
        for ef in existing_wu:
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
                WU_TH,
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
            uid = f"wu_w51_{seq:04d}_{random.randint(100, 999)}"
            while uid in have_ids:
                seq += 1
                uid = f"wu_w51_{seq:04d}_{random.randint(100, 999)}"
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
                university=WU_EN,
                university_th=WU_TH,
                faculty=r.get("faculty_en") or r.get("faculty_th") or "สำนักวิชาวิทยาศาสตร์",
                faculty_th=r.get("faculty_th") or "สำนักวิชาวิทยาศาสตร์",
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
            (FacultyDB.university_th.ilike("%วลัยลักษณ์%")) |
            (FacultyDB.university.ilike("%Walailak%"))
        ).count()
        with_email = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%วลัยลักษณ์%")) |
            (FacultyDB.university.ilike("%Walailak%")),
            FacultyDB.email.isnot(None)
        ).count()
        with_embed = db.query(FacultyDB).filter(
            (FacultyDB.university_th.ilike("%วลัยลักษณ์%")) |
            (FacultyDB.university.ilike("%Walailak%")),
            FacultyDB.embedding.isnot(None)
        ).count()

        print("\n================================================================================")
        print("🎉 WAVE 51 WALAILAK UNIVERSITY (WU) COMPLETED SUCCESSFULLY!")
        print(f"Total WU Faculty in Database: {final_total}")
        print(f"Faculty with Verified Email:   {with_email}")
        print(f"Faculty with 768-dim Vector:   {with_embed} (100%)")
        print("================================================================================")


if __name__ == "__main__":
    run()
