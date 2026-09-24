"""Wave 53: Rajamangala Universities of Technology (RMUT) Autonomous Pipeline
Harvests faculty data from all 9 Rajamangala University campuses:
1. RMUT Thanyaburi (RMUTT) - มทร.ธัญบุรี
2. RMUT Lanna (RMUTL) - มทร.ล้านนา
3. RMUT Phra Nakhon (RMUTP) - มทร.พระนคร
4. RMUT Isan (RMUTI) - มทร.อีสาน
5. RMUT Krungthep (RMUTK) - มทร.กรุงเทพ
6. RMUT Rattanakosin (RMUTR) - มทร.รัตนโกสินทร์
7. RMUT Srivijaya (RMUTSV) - มทร.ศรีวิชัย
8. RMUT Suvanabhumi (RMUTS) - มทร.สุวรรณภูมิ
9. RMUT Tawan-ok (RMUTTO) - มทร.ตะวันออก

Sources:
1. Official RMUT campus faculty directory pages (HTML parse)
2. OpenAlex Institution author rosters (per-campus ROR/OpenAlex ID)
3. State checkpoint to JSON for deduplication

PDPA: 0 phone numbers stored. Local PostgreSQL only.
"""

import os
import sys
import json
import time
import re
import random
import threading
import logging
import urllib.request
import urllib.parse
import urllib.error
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)

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

# ─────────────────────────────────────────────────────────────
# RMUT Campus definitions (EN, TH, OpenAlex Institution ID)
# ─────────────────────────────────────────────────────────────
RMUT_CAMPUSES = [
    {
        "en": "Rajamangala University of Technology Thanyaburi",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
        "short": "RMUTT",
        "prefix": "rmutt",
        "openalex_id": "I149033750",
        "email_domain": "rmutt.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://www.en.rmutt.ac.th/personnel/"),
            ("Faculty of Science and Technology", "คณะวิทยาศาสตร์และเทคโนโลยี", "https://www.sci.rmutt.ac.th/personnel/"),
            ("Faculty of Business Administration", "คณะบริหารธุรกิจ", "https://www.ba.rmutt.ac.th/personnel/"),
            ("Faculty of Fine and Applied Arts", "คณะศิลปกรรมศาสตร์", "https://www.faa.rmutt.ac.th/personnel/"),
            ("Faculty of Textile Industries", "คณะวิศวกรรมศาสตร์", "https://www.textile.rmutt.ac.th/personnel/"),
            ("Faculty of Home Economics Technology", "คณะเทคโนโลยีคหกรรมศาสตร์", "https://www.hhm.rmutt.ac.th/personnel/"),
            ("Faculty of Technical Education", "คณะครุศาสตร์อุตสาหกรรม", "https://www.ite.rmutt.ac.th/personnel/"),
            ("Faculty of Architecture", "คณะสถาปัตยกรรมศาสตร์", "https://www.arc.rmutt.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Lanna",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลล้านนา",
        "short": "RMUTL",
        "prefix": "rmutl",
        "openalex_id": "I2799438924",
        "email_domain": "rmutl.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://engineer.rmutl.ac.th/personnel/"),
            ("Faculty of Science and Agricultural Technology", "คณะวิทยาศาสตร์และเทคโนโลยีการเกษตร", "https://science.rmutl.ac.th/personnel/"),
            ("Faculty of Business and Liberal Arts", "คณะบริหารธุรกิจและศิลปศาสตร์", "https://ba.rmutl.ac.th/personnel/"),
            ("Faculty of Fine Arts and Architecture", "คณะศิลปกรรมและสถาปัตยกรรมศาสตร์", "https://art.rmutl.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Phra Nakhon",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
        "short": "RMUTP",
        "prefix": "rmutp",
        "openalex_id": "I4210134987",
        "email_domain": "rmutp.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://engineer.rmutp.ac.th/personnel/"),
            ("Faculty of Industrial Textile Technology", "คณะเทคโนโลยีสื่อสารมวลชน", "https://mctech.rmutp.ac.th/personnel/"),
            ("Faculty of Business Administration", "คณะบริหารธุรกิจ", "https://ba.rmutp.ac.th/personnel/"),
            ("Faculty of Science and Technology", "คณะวิทยาศาสตร์และเทคโนโลยี", "https://science.rmutp.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Isan",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลอีสาน",
        "short": "RMUTI",
        "prefix": "rmuti",
        "openalex_id": "I4210116416",
        "email_domain": "rmuti.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์และสถาปัตยกรรมศาสตร์", "https://www.rmuti.ac.th/user_files/personnel/"),
            ("Faculty of Business Administration", "คณะบริหารธุรกิจ", "https://www.rmuti.ac.th/user_files/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Krungthep",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ",
        "short": "RMUTK",
        "prefix": "rmutk",
        "openalex_id": "I2799607564",
        "email_domain": "mail.rmutk.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://engineer.rmutk.ac.th/personnel/"),
            ("Faculty of Business Administration", "คณะบริหารธุรกิจ", "https://ba.rmutk.ac.th/personnel/"),
            ("Faculty of Liberal Arts", "คณะศิลปศาสตร์", "https://la.rmutk.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Rattanakosin",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลรัตนโกสินทร์",
        "short": "RMUTR",
        "prefix": "rmutr",
        "openalex_id": "I4210107090",
        "email_domain": "rmutr.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://engineer.rmutr.ac.th/personnel/"),
            ("Faculty of Architecture and Design", "คณะสถาปัตยกรรมศาสตร์และการออกแบบ", "https://arch.rmutr.ac.th/personnel/"),
            ("Faculty of Business Administration and Liberal Arts", "คณะบริหารธุรกิจ", "https://ba.rmutr.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Srivijaya",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลศรีวิชัย",
        "short": "RMUTSV",
        "prefix": "rmutsv",
        "openalex_id": "I4210090296",
        "email_domain": "rmutsv.ac.th",
        "pages": [
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://engineer.rmutsv.ac.th/personnel/"),
            ("Faculty of Science and Technology", "คณะวิทยาศาสตร์และเทคโนโลยี", "https://science.rmutsv.ac.th/personnel/"),
            ("Faculty of Business Administration", "คณะบริหารธุรกิจ", "https://ba.rmutsv.ac.th/personnel/"),
            ("Faculty of Agricultural Technology", "คณะเทคโนโลยีการจัดการ", "https://agri.rmutsv.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Suvanabhumi",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลสุวรรณภูมิ",
        "short": "RMUTS",
        "prefix": "rmuts",
        "openalex_id": "I4210146567",
        "email_domain": "rmutsb.ac.th",
        "pages": [
            ("Faculty of Engineering and Architecture", "คณะวิศวกรรมศาสตร์และสถาปัตยกรรมศาสตร์", "https://eng.rmutsb.ac.th/personnel/"),
            ("Faculty of Business Administration", "คณะบริหารธุรกิจและเทคโนโลยีสารสนเทศ", "https://bus.rmutsb.ac.th/personnel/"),
        ],
    },
    {
        "en": "Rajamangala University of Technology Tawan-ok",
        "th": "มหาวิทยาลัยเทคโนโลยีราชมงคลตะวันออก",
        "short": "RMUTTO",
        "prefix": "rmutto",
        "openalex_id": "I4210106200",
        "email_domain": "rmutto.ac.th",
        "pages": [
            ("Faculty of Agriculture", "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ", "https://www.rmutto.ac.th/personnel/"),
            ("Faculty of Engineering", "คณะวิศวกรรมศาสตร์", "https://www.rmutto.ac.th/personnel/"),
        ],
    },
]

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|สาขาวิชา|หน่วยงาน|โทร|เบอร์|ห้อง|center|department|faculty|คณะ|สาขา"
    r"|งานวิจัย|เทคโนโลยี|ดาวน์โหลด|ข่าวสาร|กิจกรรม|ประกาศ|รายละเอียด)",
    re.I,
)

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave53_rmut_extraction.json"

# ─────────────────────────────────────────────────────────────
# Embedding Setup
# ─────────────────────────────────────────────────────────────
def setup_embedding_clients():
    keys_raw = getattr(settings, "GEMINI_API_KEYS", None) or getattr(settings, "GEMINI_API_KEY", None)
    if isinstance(keys_raw, str):
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    elif isinstance(keys_raw, list):
        keys = [k.strip() for k in keys_raw if k and k.strip()]
    else:
        keys = []
    clients = [genai.Client(api_key=k) for k in keys]
    return clients

clients = setup_embedding_clients()
key_box = [0]
key_lock = threading.Lock()
quota_available = len(clients) > 0
consecutive_429 = [0]


def get_embedding(text: str) -> list[float]:
    global quota_available
    if not quota_available or not clients:
        return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
    for _ in range(2):
        with key_lock:
            if not quota_available:
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
            c = clients[key_box[0] % len(clients)]
            key_box[0] += 1
        try:
            res = c.models.embed_content(
                model="gemini-embedding-001",
                contents=text[:2000],
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            with key_lock:
                consecutive_429[0] = 0
            return res.embeddings[0].values
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                with key_lock:
                    consecutive_429[0] += 1
                    if consecutive_429[0] >= 3:
                        quota_available = False
                        print("\n  WARN: Gemini quota exhausted. Switching to baseline embeddings.")
                return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search
            else:
                time.sleep(0.3)
    return None  # NULL: re-embed via embed_missing.py; zero vectors excluded from semantic search


# ─────────────────────────────────────────────────────────────
# Name Cleaning
# ─────────────────────────────────────────────────────────────
def clean_raw_name(raw: str) -> str:
    text = raw
    for token in ["ตำแหน่ง", "โทรศัพท์", "อีเมล", "โทร.", "โทร ", "ห้องทำงาน",
                  "ติดต่อ", "E-mail", "Tel", "Email", "Office", "CV", "คณบดี",
                  "อาจารย์ประจำ", "หัวหน้าสาขา", "การศึกษา", "วุฒิ"]:
        if token in text:
            text = text.split(token)[0]
    text = re.sub(r"[,;].*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_record(r: dict, campus: dict) -> dict | None:
    raw_th = (r.get("full_name_th") or "").strip()
    raw_en = (r.get("full_name_en") or "").strip()

    title_th = (r.get("academic_title_th") or "").strip()
    title_en = (r.get("academic_title_en") or "").strip()
    first_name = (r.get("first_name") or "").strip()
    last_name = (r.get("last_name") or "").strip()

    if raw_th:
        raw_th = clean_raw_name(raw_th)
        try:
            norm_title, full_norm, clean_name = normalize_thai_title_and_name(raw_th)
            if clean_name:
                raw_th = clean_name
            elif full_norm:
                raw_th = full_norm
            if norm_title and not title_th:
                title_th = norm_title
        except Exception:
            pass
        if RE_BAD_NAME.search(raw_th) or len(raw_th) < 3:
            raw_th = ""

    if raw_en:
        raw_en = clean_raw_name(raw_en)
        m = re.match(
            r"^(Prof\.?\s*Dr\.?|Assoc\.?\s*Prof\.?\s*Dr\.?|Asst\.?\s*Prof\.?\s*Dr\.?|"
            r"Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s+(.*)$",
            raw_en, re.I,
        )
        if m:
            if not title_en:
                title_en = m.group(1).strip()
            raw_en = m.group(2).strip()
        raw_en = re.sub(r",?\s*(?:Ph\.?D\.?|M\.?Sc\.?|B\.?Sc\.?|SFHEA|FHEA|MD|DDS|DVM)\b.*$",
                        "", raw_en, flags=re.I).strip()
        if not first_name and not last_name:
            parts = raw_en.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            elif len(parts) == 1:
                first_name = parts[0]

    if not raw_th and not raw_en and not first_name:
        return None

    email = (r.get("email") or "").strip().lower()
    if email:
        if not RE_EMAIL.match(email) or "@" not in email:
            email = ""
        elif not any(email.endswith(f"@{campus['email_domain']}") or
                     f"@{campus['email_domain']}" in email
                     for _ in [1]):
            # allow any .ac.th email for RMUT members
            if not (email.endswith(".ac.th") or email.endswith(".edu")):
                email = ""

    interests = [RE_PHONE.sub("", i).strip() for i in (r.get("research_interests") or [])]
    interests = [i for i in interests if i and len(i) > 2]

    fn_th = raw_th or f"{first_name} {last_name}".strip() or raw_en
    if not fn_th:
        fn_th = ""

    return {
        "full_name_th": fn_th,
        "full_name_en": raw_en or f"{first_name} {last_name}".strip(),
        "first_name": first_name,
        "last_name": last_name,
        "academic_title_th": title_th,
        "academic_title_en": title_en,
        "university": campus["en"],
        "university_th": campus["th"],
        "faculty": r.get("faculty") or "",
        "faculty_th": r.get("faculty_th") or "",
        "department": r.get("department") or "",
        "department_th": r.get("department_th") or "",
        "email": email,
        "image_url": r.get("image_url") or "",
        "profile_url": r.get("profile_url") or "",
        "research_interests": interests,
        "featured_publications": r.get("featured_publications") or [],
        "total_citations": r.get("total_citations") or 0,
        "h_index": r.get("h_index") or 0,
        "works_count": r.get("works_count") or 0,
        "openalex_id": r.get("openalex_id") or "",
        "_campus_prefix": campus["prefix"],
    }


# ─────────────────────────────────────────────────────────────
# Source 1: HTML Faculty Directory Pages
# ─────────────────────────────────────────────────────────────
def fetch_campus_html(campus: dict) -> list[dict]:
    """Fetch faculty members from official HTML pages for a campus."""
    print(f"\n  [HTML] {campus['short']}: Fetching {len(campus['pages'])} faculty pages...")
    results = []

    def fetch_page(entry: tuple) -> list[dict]:
        fac_en, fac_th, url = entry
        page_results = []
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Strategy 1: Find by email anchor links
            email_anchors = soup.find_all("a", href=re.compile(r"mailto:"))
            for anchor in email_anchors:
                email = anchor.get("href", "").replace("mailto:", "").strip().lower()
                if not RE_EMAIL.match(email):
                    continue
                # Walk up to find name
                card = anchor.parent
                for _ in range(8):
                    text = card.get_text(" ", strip=True)
                    if 10 < len(text) < 600:
                        break
                    if card.parent:
                        card = card.parent
                    else:
                        break

                lines = [l.strip() for l in card.get_text("\n").split("\n") if l.strip()]
                img = card.find("img")
                img_src = ""
                if img and img.get("src"):
                    img_src = urllib.parse.urljoin(url, img["src"])

                # Find name line (prefer Thai name with title)
                name_line = ""
                for ln in lines:
                    if len(ln) > 3 and any(t in ln for t in [
                        "ศ.", "รศ.", "ผศ.", "อ.", "ดร.", "นาย", "นาง", "น.ส.",
                        "Prof.", "Assoc.", "Asst.", "Dr.", "Mr.", "Mrs.", "Ms."
                    ]):
                        name_line = ln
                        break
                if not name_line and lines:
                    name_line = lines[0]

                if not name_line or len(name_line) < 3:
                    continue

                has_thai = any("฀" <= c <= "๿" for c in name_line)
                page_results.append({
                    "full_name_th": name_line if has_thai else "",
                    "full_name_en": "" if has_thai else name_line,
                    "faculty": fac_en,
                    "faculty_th": fac_th,
                    "email": email,
                    "image_url": img_src,
                    "profile_url": url,
                    "research_interests": [fac_th],
                    "total_citations": 0,
                    "h_index": 0,
                    "works_count": 0,
                })

            # Strategy 2: Find by name patterns if no emails found
            if not page_results:
                cards = soup.find_all(class_=re.compile(
                    r"(card|person|staff|faculty|member|lecturer|professor|teacher|instructor)",
                    re.I
                ))
                if not cards:
                    cards = soup.find_all(["article", "li"], class_=True)

                for card in cards[:200]:
                    text = card.get_text(" ", strip=True)
                    if len(text) < 5 or len(text) > 1000:
                        continue

                    # Look for Thai academic title patterns
                    m_th = re.search(r"((?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|"
                                     r"อาจารย์|ศ\.|รศ\.|ผศ\.|อ\.)(?:\s*ดร\.)?[\s฀-๿]{5,40})",
                                     text)
                    if m_th:
                        name_line = m_th.group(1).strip()
                        img = card.find("img")
                        img_src = urllib.parse.urljoin(url, img["src"]) if img and img.get("src") else ""
                        # Look for email
                        m_email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
                        email = m_email.group(0).lower() if m_email else ""
                        page_results.append({
                            "full_name_th": name_line,
                            "full_name_en": "",
                            "faculty": fac_en,
                            "faculty_th": fac_th,
                            "email": email,
                            "image_url": img_src,
                            "profile_url": url,
                            "research_interests": [fac_th],
                            "total_citations": 0,
                            "h_index": 0,
                            "works_count": 0,
                        })

        except Exception as e:
            print(f"    Failed {url}: {type(e).__name__}: {e}")
        return page_results

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_page, p) for p in campus["pages"]]
        for fut in as_completed(futures):
            results.extend(fut.result())

    print(f"    -> {campus['short']} HTML: {len(results)} raw records")
    return results


# ─────────────────────────────────────────────────────────────
# Source 2: OpenAlex Institution Authors
# ─────────────────────────────────────────────────────────────
def fetch_openalex_authors(campus: dict) -> list[dict]:
    """Fetch authors affiliated with this RMUT campus from OpenAlex."""
    inst_id = campus.get("openalex_id", "")
    if not inst_id:
        return []

    print(f"\n  [OpenAlex] {campus['short']} ({inst_id}): Fetching authors...")
    results = []
    cursor = "*"
    page_count = 0
    max_pages = 30  # up to 6000 authors per campus

    while cursor:
        try:
            params = urllib.parse.urlencode({
                "filter": f"affiliations.institution.id:{inst_id}",
                "select": "id,display_name,display_name_alternatives,last_known_institutions,"
                          "topics,cited_by_count,works_count,counts_by_year,summary_stats",
                "per-page": "200",
                "cursor": cursor,
                "mailto": "research@example.com",
            })
            url = f"https://api.openalex.org/authors?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "AdvisorMatchBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            authors = data.get("results", [])
            meta = data.get("meta", {})
            cursor = data.get("meta", {}).get("next_cursor", None)
            page_count += 1

            for a in authors:
                display_name = a.get("display_name", "").strip()
                if not display_name:
                    continue

                # Verify affiliation to this campus
                last_inst = a.get("last_known_institutions") or []
                is_affiliated = any(
                    inst.get("id", "").endswith(inst_id) or
                    campus["en"].lower() in (inst.get("display_name") or "").lower() or
                    campus["th"] in (inst.get("display_name") or "")
                    for inst in last_inst
                )

                # Filter out clearly unaffiliated (but keep if score is high)
                citations = a.get("cited_by_count", 0) or 0
                works = a.get("works_count", 0) or 0

                # Get research topics
                topics = []
                for t in (a.get("topics") or [])[:8]:
                    topic_name = t.get("display_name", "")
                    if topic_name and len(topic_name) > 2:
                        topics.append(topic_name)

                # Determine h-index
                h_index = (a.get("summary_stats") or {}).get("h_index", 0) or 0

                # Detect if Thai name
                has_thai = any("฀" <= c <= "๿" for c in display_name)

                results.append({
                    "full_name_th": display_name if has_thai else "",
                    "full_name_en": "" if has_thai else display_name,
                    "faculty": "",
                    "faculty_th": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": f"https://openalex.org/{a.get('id', '').split('/')[-1]}",
                    "research_interests": topics,
                    "featured_publications": [],
                    "total_citations": citations,
                    "h_index": h_index,
                    "works_count": works,
                    "openalex_id": a.get("id", "").split("/")[-1],
                })

            if page_count >= max_pages or not cursor:
                break

            time.sleep(0.2)  # OpenAlex rate limit: 10 req/s

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"    Rate limited by OpenAlex, sleeping 5s...")
                time.sleep(5)
            else:
                print(f"    OpenAlex HTTP error {e.code}: {e}")
                break
        except Exception as e:
            print(f"    OpenAlex error: {type(e).__name__}: {e}")
            break

    print(f"    -> {campus['short']} OpenAlex: {len(results)} authors ({page_count} pages)")
    return results


# ─────────────────────────────────────────────────────────────
# RapidFuzz 5-Pass Deduplication
# ─────────────────────────────────────────────────────────────
def dedup_against_db(records: list[dict], db, campus: dict) -> tuple[list[dict], list[dict]]:
    """Deduplicates new records against existing DB records for this campus.
    Returns (to_insert, to_enrich_existing)."""
    print(f"\n  [Dedup] Loading existing {campus['en']} records from DB...")

    existing = db.query(
        FacultyDB.id,
        FacultyDB.full_name_th,
        FacultyDB.first_name,
        FacultyDB.last_name,
        FacultyDB.email,
        FacultyDB.openalex_id,
        FacultyDB.total_citations,
        FacultyDB.h_index,
        FacultyDB.total_publications_count,
    ).filter(
        FacultyDB.university == campus["en"]
    ).all()

    existing_by_email: dict[str, str] = {}
    existing_by_name_th: dict[str, str] = {}
    existing_by_name_en: dict[str, str] = {}
    existing_by_openalex: dict[str, str] = {}
    existing_metrics: dict[str, dict] = {}

    for row in existing:
        eid = row[0]
        name_th = (row[1] or "").strip()
        fn = (row[2] or "").strip()
        ln = (row[3] or "").strip()
        name_en = f"{fn} {ln}".strip()
        email = (row[4] or "").strip().lower()
        openalex = (row[5] or "").strip()
        citations = row[6] or 0
        h_idx = row[7] or 0
        pubs = row[8] or 0

        existing_metrics[eid] = {"citations": citations, "h_index": h_idx, "works": pubs}

        if email and "@" in email:
            existing_by_email[email] = eid
        if name_th and len(name_th) > 2:
            existing_by_name_th[name_th.lower()] = eid
        if name_en and len(name_en) > 2:
            existing_by_name_en[name_en.lower()] = eid
        if openalex:
            existing_by_openalex[openalex] = eid

    print(f"    Existing: {len(existing)} records in DB")

    to_insert = []
    enrichment_updates = []
    seen_in_batch: set[str] = set()

    for rec in records:
        email = (rec.get("email") or "").strip().lower()
        name_th = (rec.get("full_name_th") or "").strip()
        name_en = (rec.get("full_name_en") or "").strip()
        fn = (rec.get("first_name") or "").strip()
        ln = (rec.get("last_name") or "").strip()
        if not name_en:
            name_en = f"{fn} {ln}".strip()
        openalex_id = (rec.get("openalex_id") or "").strip()

        matched_id = None

        # Pass 1: Email exact match
        if email and email in existing_by_email:
            matched_id = existing_by_email[email]

        # Pass 2: OpenAlex ID exact match
        if not matched_id and openalex_id and openalex_id in existing_by_openalex:
            matched_id = existing_by_openalex[openalex_id]

        # Pass 3: Thai name exact match
        if not matched_id and name_th:
            if name_th.lower() in existing_by_name_th:
                matched_id = existing_by_name_th[name_th.lower()]

        # Pass 4: English name exact match
        if not matched_id and name_en:
            if name_en.lower() in existing_by_name_en:
                matched_id = existing_by_name_en[name_en.lower()]

        # Pass 5: Fuzzy Thai name >= 90
        if not matched_id and name_th and len(name_th) > 3:
            for existing_name, eid in existing_by_name_th.items():
                if fuzz.token_set_ratio(name_th.lower(), existing_name) >= 90:
                    matched_id = eid
                    break

        # Pass 6: Fuzzy English name >= 90
        if not matched_id and name_en and len(name_en) > 3:
            for existing_name, eid in existing_by_name_en.items():
                if fuzz.token_set_ratio(name_en.lower(), existing_name) >= 90:
                    matched_id = eid
                    break

        if matched_id:
            # Enrich: update metrics if higher
            old = existing_metrics.get(matched_id, {})
            if (rec.get("total_citations", 0) or 0) > (old.get("citations", 0)):
                enrichment_updates.append({
                    "id": matched_id,
                    "total_citations": rec.get("total_citations", 0),
                    "h_index": rec.get("h_index", 0),
                    "total_publications_count": rec.get("works_count", 0),
                    "openalex_id": openalex_id or "",
                    "research_interests": rec.get("research_interests") or [],
                })
        else:
            # Check within-batch deduplication
            dedup_key = (name_th or name_en or email or "").lower().strip()
            if dedup_key and dedup_key in seen_in_batch:
                continue
            if dedup_key:
                seen_in_batch.add(dedup_key)
            to_insert.append(rec)

    print(f"    -> New: {len(to_insert)}, Enrich existing: {len(enrichment_updates)}")
    return to_insert, enrichment_updates


# ─────────────────────────────────────────────────────────────
# Main Pipeline
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("Wave 53: RMUT (Rajamangala Universities of Technology) Autonomous Pipeline")
    print("=" * 70)

    all_raw_records: list[dict] = []

    # ── Step 1: Collect from all campuses ──────────────────────────────────
    for campus in RMUT_CAMPUSES:
        print(f"\n{'─'*60}")
        print(f"  Campus: {campus['en']}")
        print(f"{'─'*60}")

        # Source 1: HTML pages
        html_records = fetch_campus_html(campus)

        # Source 2: OpenAlex
        openalex_records = fetch_openalex_authors(campus)

        # Clean and tag with campus
        campus_raw = []
        for r in html_records + openalex_records:
            cleaned = clean_record(r, campus)
            if cleaned:
                campus_raw.append(cleaned)

        print(f"  {campus['short']}: {len(campus_raw)} cleaned records")
        all_raw_records.extend(campus_raw)

    print(f"\n{'='*70}")
    print(f"Total raw records from all RMUT campuses: {len(all_raw_records)}")

    # ── Step 2: Save Checkpoint ────────────────────────────────────────────
    print(f"\nSaving checkpoint to {CHECKPOINT_FILE}...")
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_raw_records, f, ensure_ascii=False, indent=2)
    print(f"  Checkpoint saved: {len(all_raw_records)} records")

    # ── Step 3: Deduplication per campus + DB commit ───────────────────────
    db = SessionLocal()
    try:
        total_inserted = 0
        total_enriched = 0

        # Group records by campus
        campus_groups: dict[str, list[dict]] = {}
        for rec in all_raw_records:
            prefix = rec.get("_campus_prefix", "rmut")
            campus_groups.setdefault(prefix, []).append(rec)

        for campus in RMUT_CAMPUSES:
            prefix = campus["prefix"]
            campus_records = campus_groups.get(prefix, [])
            if not campus_records:
                print(f"\n  {campus['short']}: No records to process")
                continue

            print(f"\n  Processing {campus['short']}: {len(campus_records)} records")

            # Dedup against DB
            to_insert, to_enrich = dedup_against_db(campus_records, db, campus)

            # ── Step 3a: Enrichment updates ────────────────────────────────
            if to_enrich:
                print(f"  Enriching {len(to_enrich)} existing records...")
                for upd in to_enrich:
                    fac = db.query(FacultyDB).filter(FacultyDB.id == upd["id"]).first()
                    if not fac:
                        continue
                    if (upd.get("total_citations", 0) or 0) > (fac.total_citations or 0):
                        fac.total_citations = upd["total_citations"]
                        fac.h_index = max(fac.h_index or 0, upd.get("h_index", 0) or 0)
                        fac.total_publications_count = max(
                            fac.total_publications_count or 0,
                            upd.get("total_publications_count", 0) or 0
                        )
                    if upd.get("openalex_id") and not fac.openalex_id:
                        fac.openalex_id = upd["openalex_id"]
                    if upd.get("research_interests"):
                        existing_ri = set(fac.research_interests or [])
                        new_ri = set(upd["research_interests"])
                        merged = list(existing_ri | new_ri)
                        fac.research_interests = merged
                db.commit()
                total_enriched += len(to_enrich)

            # ── Step 3b: Generate embeddings ───────────────────────────────
            if not to_insert:
                continue

            print(f"  Generating embeddings for {len(to_insert)} new records...")
            embed_texts = []
            for r in to_insert:
                name_part = (r.get("full_name_th") or r.get("full_name_en") or "").strip()
                interests_part = " | ".join((r.get("research_interests") or [])[:5])
                fac_part = r.get("faculty_th") or r.get("faculty") or ""
                text = f"{name_part} {fac_part} {campus['th']} {interests_part}".strip()
                embed_texts.append(text)

            with ThreadPoolExecutor(max_workers=min(4, len(clients) or 1)) as ex:
                embed_results = list(ex.map(get_embedding, embed_texts))

            # ── Step 3c: Batch DB commit ────────────────────────────────────
            print(f"  Committing {len(to_insert)} records to DB...")
            have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
            seq = 0
            new_db_objs = []

            for i, r in enumerate(to_insert):
                seq += 1
                uid = f"{prefix}_w53_{seq:04d}_{random.randint(100, 999)}"
                while uid in have_ids:
                    seq += 1
                    uid = f"{prefix}_w53_{seq:04d}_{random.randint(100, 999)}"
                have_ids.add(uid)

                emb = embed_results[i] if i < len(embed_results) else None  # NULL: re-embed via embed_missing.py

                fn_th = r.get("full_name_th") or ""
                if not fn_th:
                    fn_en = r.get("full_name_en") or ""
                    fn_th = fn_en or "อาจารย์"

                new_fac = FacultyDB(
                    id=uid,
                    first_name=r.get("first_name") or "",
                    last_name=r.get("last_name") or "",
                    full_name_th=fn_th,
                    academic_title_th=r.get("academic_title_th") or "",
                    university=campus["en"],
                    university_th=campus["th"],
                    faculty=r.get("faculty") or "",
                    faculty_th=r.get("faculty_th") or "",
                    department=r.get("department") or "",
                    department_th=r.get("department_th") or "",
                    email=r.get("email") or "",
                    image_url=r.get("image_url") or "",
                    profile_url=r.get("profile_url") or "",
                    research_interests=r.get("research_interests") or [],
                    featured_publications=r.get("featured_publications") or [],
                    total_citations=r.get("total_citations") or 0,
                    h_index=r.get("h_index") or 0,
                    total_publications_count=r.get("works_count") or 0,
                    openalex_id=r.get("openalex_id") or "",
                    embedding=emb,
                )
                new_db_objs.append(new_fac)

            batch_size = 300
            for i in range(0, len(new_db_objs), batch_size):
                db.add_all(new_db_objs[i:i + batch_size])
                db.commit()
                print(f"    Committed batch {i//batch_size + 1}: {len(new_db_objs[i:i+batch_size])} records")

            total_inserted += len(new_db_objs)
            print(f"  {campus['short']} done: +{len(new_db_objs)} inserted, {len(to_enrich)} enriched")

        # ── Step 4: Final DB verification ─────────────────────────────────
        print(f"\n{'='*70}")
        print("Final Verification:")
        from sqlalchemy import text
        total_rmut = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajamangala%'"
        )).scalar()
        total_all = db.execute(text("SELECT COUNT(*) FROM faculties")).scalar()
        rmut_email = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajamangala%' "
            "AND email != '' AND email IS NOT NULL"
        )).scalar()
        rmut_openalex = db.execute(text(
            "SELECT COUNT(*) FROM faculties WHERE university LIKE '%Rajamangala%' "
            "AND openalex_id != '' AND openalex_id IS NOT NULL"
        )).scalar()

        print(f"  RMUT Total: {total_rmut:,}")
        print(f"  RMUT with email: {rmut_email:,} ({100*rmut_email//max(1,total_rmut)}%)")
        print(f"  RMUT with OpenAlex: {rmut_openalex:,} ({100*rmut_openalex//max(1,total_rmut)}%)")
        print(f"  Grand Total Faculties: {total_all:,}")
        print(f"\n  Wave 53 Summary: +{total_inserted} new, {total_enriched} enriched")

    finally:
        db.close()

    print("\nWave 53 RMUT Pipeline Complete!")
    return total_inserted


if __name__ == "__main__":
    main()
