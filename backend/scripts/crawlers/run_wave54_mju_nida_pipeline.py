"""Wave 54: Maejo University (MJU) + NIDA Autonomous Pipeline
- MJU (แม่โจ้): OpenAlex I190734841 — expand from 366 to full roster
- NIDA (นิด้า): OpenAlex I159665162 — expand from 115 to full roster
Sources: OpenAlex author rosters + Official web pages
"""

import sys
import json
import time
import re
import random
import threading
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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
except ImportError:
    from backend.app.core.database import SessionLocal
    from backend.app.models.db_models import FacultyDB
    from backend.app.core.config import settings
    from backend.scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

from google import genai
from google.genai import types
from rapidfuzz import fuzz
import ssl

UNIVERSITIES = [
    {
        "en": "Maejo University",
        "th": "มหาวิทยาลัยแม่โจ้",
        "short": "MJU",
        "prefix": "mju",
        "openalex_id": "I190734841",
        "email_domain": "mju.ac.th",
        "wave": "54",
        "pages": [
            ("Faculty of Agricultural Production", "คณะผลิตกรรมการเกษตร",
             "https://agpro.mju.ac.th/list_staff.php?lang=th"),
            ("Faculty of Business Administration and Liberal Arts", "คณะบริหารธุรกิจและศิลปศาสตร์",
             "https://bala.mju.ac.th/lecturer.php"),
            ("Faculty of Agricultural Business", "คณะเศรษฐศาสตร์",
             "https://econ.mju.ac.th/list_staff.php"),
            ("Faculty of Engineering and Agro-Industry", "คณะวิศวกรรมและอุตสาหกรรมเกษตร",
             "https://en.mju.ac.th/list_staff.php"),
            ("Faculty of Fisheries Technology", "คณะเทคโนโลยีการประมงและทรัพยากรทางน้ำ",
             "https://fishtech.mju.ac.th/list_staff.php"),
            ("Faculty of Animal Science and Technology", "คณะสัตวศาสตร์และเทคโนโลยี",
             "https://ansc.mju.ac.th/list_staff.php"),
            ("Faculty of Science", "คณะวิทยาศาสตร์",
             "https://science.mju.ac.th/list_staff.php"),
            ("Faculty of Natural Resources", "คณะทรัพยากรธรรมชาติ",
             "https://nat.mju.ac.th/list_staff.php"),
            ("Faculty of Arts, Architecture and Design", "คณะศิลปศาสตร์สถาปัตยกรรมศาสตร์และการออกแบบสิ่งแวดล้อม",
             "https://artarch.mju.ac.th/list_staff.php"),
            ("Faculty of Veterinary Medicine", "คณะสัตวแพทยศาสตร์",
             "https://vet.mju.ac.th/list_staff.php"),
            ("Faculty of Education and Communication Arts", "คณะศึกษาศาสตร์และสารสนเทศศาสตร์",
             "https://educate.mju.ac.th/list_staff.php"),
            ("Faculty of Information Technology", "วิทยาลัยนานาชาตินวัตกรรมดิจิทัล",
             "https://www.mju.ac.th/mju_main/lecturer.php?kk=1&id_fac=38"),
        ],
    },
    {
        "en": "National Institute of Development Administration",
        "th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์",
        "short": "NIDA",
        "prefix": "nida",
        "openalex_id": "I159665162",
        "email_domain": "nida.ac.th",
        "wave": "55",
        "pages": [
            ("Graduate School of Applied Statistics", "คณะสถิติประยุกต์",
             "https://as.nida.ac.th/th/about/staff/"),
            ("Graduate School of Business Administration", "คณะบริหารธุรกิจ",
             "https://nida.ac.th/th/faculty/business-administration.html"),
            ("Graduate School of Development Administration", "คณะรัฐประศาสนศาสตร์",
             "https://gspa.nida.ac.th/th/about/personnel/"),
            ("Graduate School of Public Administration", "คณะพัฒนาสังคมและยุทธศาสตร์การบริหาร",
             "https://dpim.nida.ac.th/personnel/"),
            ("Graduate School of Information Technology", "คณะเทคโนโลยีสารสนเทศ",
             "https://sis.nida.ac.th/th/about/personnel/"),
            ("Graduate School of Language and Communication", "คณะภาษาและการสื่อสาร",
             "https://lc.nida.ac.th/th/about/personnel/"),
            ("Graduate School of Environmental Development Administration", "คณะพัฒนาการเศรษฐกิจ",
             "https://econ.nida.ac.th/th/about/personnel/"),
            ("Graduate School of Public and Private Management", "คณะการจัดการการท่องเที่ยว",
             "https://tourism.nida.ac.th/th/about/personnel/"),
        ],
    },
]

SSL_CTX = ssl._create_unverified_context()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th,en-US;q=0.7,en;q=0.3",
}

RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
RE_PHONE = re.compile(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b")
RE_BAD_NAME = re.compile(
    r"(?:ภาควิชา|สาขาวิชา|หน่วยงาน|คณะ|สาขา|โทร|เบอร์|ห้อง|center|department|faculty"
    r"|งาน|ดาวน์โหลด|ข่าวสาร|กิจกรรม|ประกาศ|รายละเอียด)",
    re.I,
)

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def setup_clients():
    keys_raw = getattr(settings, "GEMINI_API_KEYS", None) or getattr(settings, "GEMINI_API_KEY", None)
    if isinstance(keys_raw, str):
        keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    elif isinstance(keys_raw, list):
        keys = [k.strip() for k in keys_raw if k and k.strip()]
    else:
        keys = []
    return [genai.Client(api_key=k) for k in keys]


clients = setup_clients()
key_box = [0]
key_lock = threading.Lock()
quota_available = len(clients) > 0
consecutive_429 = [0]


def get_embedding(text: str) -> list[float]:
    global quota_available
    if not quota_available or not clients:
        return [0.0] * 768
    for _ in range(2):
        with key_lock:
            if not quota_available:
                return [0.0] * 768
            c = clients[key_box[0] % len(clients)]
            key_box[0] += 1
        try:
            res = c.models.embed_content(
                model="gemini-embedding-001",
                contents=text[:2000],
                config=types.EmbedContentConfig(output_dimensionality=768),
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
                        print("  WARN: Gemini quota exhausted. Baseline embeddings.")
                return [0.0] * 768
            time.sleep(0.3)
    return [0.0] * 768


def clean_raw_name(raw: str) -> str:
    for token in ["ตำแหน่ง", "โทรศัพท์", "อีเมล", "โทร.", "โทร ", "ห้องทำงาน",
                  "ติดต่อ", "E-mail", "Tel", "Email", "Office", "CV", "คณบดี"]:
        if token in raw:
            raw = raw.split(token)[0]
    raw = re.sub(r"[,;].*$", "", raw)
    return re.sub(r"\s+", " ", raw).strip()


def clean_record(r: dict, univ: dict) -> dict | None:
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
                first_name, last_name = parts[0], " ".join(parts[1:])
            elif parts:
                first_name = parts[0]

    if not raw_th and not raw_en and not first_name:
        return None

    email = (r.get("email") or "").strip().lower()
    if email and not RE_EMAIL.match(email):
        email = ""

    interests = [RE_PHONE.sub("", i).strip() for i in (r.get("research_interests") or [])]
    interests = [i for i in interests if i and len(i) > 2]

    fn_th = raw_th or f"{first_name} {last_name}".strip() or raw_en or "อาจารย์"

    return {
        "full_name_th": fn_th,
        "full_name_en": raw_en or f"{first_name} {last_name}".strip(),
        "first_name": first_name,
        "last_name": last_name,
        "academic_title_th": title_th,
        "academic_title_en": title_en,
        "university": univ["en"],
        "university_th": univ["th"],
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
    }


def fetch_openalex(univ: dict) -> list[dict]:
    """Fetch authors from OpenAlex for this university."""
    inst_id = univ["openalex_id"]
    print(f"  [OpenAlex] {univ['short']} ({inst_id}): fetching...")
    results = []
    cursor = "*"
    pages = 0

    while cursor:
        try:
            params = urllib.parse.urlencode({
                "filter": f"affiliations.institution.id:{inst_id}",
                "select": "id,display_name,last_known_institutions,topics,cited_by_count,works_count,summary_stats",
                "per-page": "200",
                "cursor": cursor,
                "mailto": "research@example.com",
            })
            url = f"https://api.openalex.org/authors?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "AdvisorMatchBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            authors = data.get("results", [])
            cursor = data.get("meta", {}).get("next_cursor")
            pages += 1

            for a in authors:
                display_name = (a.get("display_name") or "").strip()
                if not display_name:
                    continue

                # Verify affiliation to this university
                last_insts = a.get("last_known_institutions") or []
                is_likely_member = any(
                    univ["en"].lower() in (i.get("display_name") or "").lower() or
                    univ["th"] in (i.get("display_name") or "")
                    for i in last_insts
                ) if last_insts else True  # include all if no filter

                topics = [(t.get("display_name") or "") for t in (a.get("topics") or [])[:8]
                          if (t.get("display_name") or "")]
                h_index = (a.get("summary_stats") or {}).get("h_index", 0) or 0
                has_thai = any("฀" <= c <= "๿" for c in display_name)

                results.append({
                    "full_name_th": display_name if has_thai else "",
                    "full_name_en": "" if has_thai else display_name,
                    "first_name": "", "last_name": "",
                    "academic_title_th": "", "academic_title_en": "",
                    "faculty": "", "faculty_th": "",
                    "department": "", "department_th": "",
                    "email": "",
                    "image_url": "",
                    "profile_url": f"https://openalex.org/{(a.get('id') or '').split('/')[-1]}",
                    "research_interests": topics,
                    "featured_publications": [],
                    "total_citations": a.get("cited_by_count", 0) or 0,
                    "h_index": h_index,
                    "works_count": a.get("works_count", 0) or 0,
                    "openalex_id": (a.get("id") or "").split("/")[-1],
                })

            if pages >= 50 or not cursor:
                break
            time.sleep(0.15)

        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5)
            else:
                print(f"    HTTP {e.code}")
                break
        except Exception as e:
            print(f"    Error: {e}")
            break

    print(f"    -> {univ['short']}: {len(results)} authors ({pages} pages)")
    return results


def fetch_html_pages(univ: dict) -> list[dict]:
    """Fetch faculty from official HTML pages."""
    print(f"  [HTML] {univ['short']}: Fetching {len(univ['pages'])} pages...")
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

            # Strategy: Find email anchors → walk up to name
            email_anchors = soup.find_all("a", href=re.compile(r"mailto:"))
            for anchor in email_anchors:
                email = anchor.get("href", "").replace("mailto:", "").strip().lower()
                if not RE_EMAIL.match(email):
                    continue

                card = anchor.parent
                for _ in range(8):
                    text = card.get_text(" ", strip=True)
                    if 10 < len(text) < 800:
                        break
                    if card.parent:
                        card = card.parent
                    else:
                        break

                lines = [l.strip() for l in card.get_text("\n").split("\n") if l.strip()]
                img = card.find("img")
                img_src = urllib.parse.urljoin(url, img["src"]) if img and img.get("src") else ""

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

            # Fallback: named patterns
            if not page_results:
                for m_th in re.finditer(
                    r"((?:ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ศ\.|รศ\.|ผศ\.|อ\.)(?:\s*ดร\.)?[\s฀-๿]{5,40})",
                    html,
                ):
                    name_line = m_th.group(1).strip()
                    if RE_BAD_NAME.search(name_line):
                        continue
                    m_email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                                        html[max(0, m_th.start()-300):m_th.end()+300])
                    email = m_email.group(0).lower() if m_email else ""
                    page_results.append({
                        "full_name_th": name_line,
                        "full_name_en": "",
                        "faculty": fac_en,
                        "faculty_th": fac_th,
                        "email": email,
                        "image_url": "",
                        "profile_url": url,
                        "research_interests": [fac_th],
                        "total_citations": 0,
                        "h_index": 0,
                        "works_count": 0,
                    })

        except Exception as e:
            print(f"    Failed {url[:60]}: {type(e).__name__}: {e}")
        return page_results

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(fetch_page, p) for p in univ["pages"]]
        for fut in as_completed(futures):
            results.extend(fut.result())

    print(f"    -> {univ['short']} HTML: {len(results)} raw records")
    return results


def process_university(univ: dict, db) -> tuple[int, int]:
    """Full pipeline for one university. Returns (inserted, enriched)."""
    print(f"\n{'='*70}")
    print(f"  University: {univ['en']}")
    print(f"{'='*70}")

    # Source 1: HTML
    html_records = fetch_html_pages(univ)
    # Source 2: OpenAlex
    openalex_records = fetch_openalex(univ)

    # Clean all records
    all_raw = []
    for r in html_records + openalex_records:
        cleaned = clean_record(r, univ)
        if cleaned:
            all_raw.append(cleaned)

    print(f"  Total cleaned: {len(all_raw)}")

    # Checkpoint
    ckpt = CHECKPOINT_DIR / f"wave{univ['wave']}_{univ['prefix']}_extraction.json"
    with open(ckpt, "w", encoding="utf-8") as f:
        json.dump(all_raw, f, ensure_ascii=False, indent=2)
    print(f"  Checkpoint: {ckpt.name}")

    # Load existing from DB
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
    ).filter(FacultyDB.university == univ["en"]).all()

    existing_by_email: dict[str, str] = {}
    existing_by_openalex: dict[str, str] = {}
    existing_by_name_th: dict[str, str] = {}
    existing_by_name_en: dict[str, str] = {}
    existing_metrics: dict[str, dict] = {}

    for row in existing:
        eid, nth, fn, ln, email, opx, cit, h, pubs = row
        name_en = f"{fn} {ln}".strip()
        if email and "@" in email:
            existing_by_email[email.lower()] = eid
        if opx:
            existing_by_openalex[opx] = eid
        if nth and len(nth) > 2:
            existing_by_name_th[nth.lower()] = eid
        if name_en and len(name_en) > 2:
            existing_by_name_en[name_en.lower()] = eid
        existing_metrics[eid] = {"c": cit or 0, "h": h or 0, "w": pubs or 0}

    print(f"  Existing in DB: {len(existing)}")

    to_insert = []
    enrichment = []
    seen_batch: set[str] = set()

    for rec in all_raw:
        email = (rec.get("email") or "").strip().lower()
        name_th = (rec.get("full_name_th") or "").strip()
        fn = (rec.get("first_name") or "").strip()
        ln = (rec.get("last_name") or "").strip()
        name_en = (rec.get("full_name_en") or f"{fn} {ln}").strip()
        opx = (rec.get("openalex_id") or "").strip()

        matched = None
        if email and email in existing_by_email:
            matched = existing_by_email[email]
        if not matched and opx and opx in existing_by_openalex:
            matched = existing_by_openalex[opx]
        if not matched and name_th and name_th.lower() in existing_by_name_th:
            matched = existing_by_name_th[name_th.lower()]
        if not matched and name_en and name_en.lower() in existing_by_name_en:
            matched = existing_by_name_en[name_en.lower()]
        if not matched and name_th and len(name_th) > 3:
            for en, eid in existing_by_name_th.items():
                if fuzz.token_set_ratio(name_th.lower(), en) >= 90:
                    matched = eid
                    break
        if not matched and name_en and len(name_en) > 3:
            for en, eid in existing_by_name_en.items():
                if fuzz.token_set_ratio(name_en.lower(), en) >= 90:
                    matched = eid
                    break

        if matched:
            old = existing_metrics.get(matched, {})
            if (rec.get("total_citations", 0) or 0) > old.get("c", 0):
                enrichment.append({
                    "id": matched,
                    "total_citations": rec["total_citations"],
                    "h_index": rec["h_index"],
                    "total_publications_count": rec["works_count"],
                    "openalex_id": opx,
                    "research_interests": rec.get("research_interests") or [],
                    "email": email if email and not db.query(FacultyDB.email).filter(
                        FacultyDB.id == matched).scalar() else "",
                })
        else:
            dedup_key = (opx or (name_th or name_en).lower() or email or "").strip()
            if dedup_key in seen_batch:
                continue
            seen_batch.add(dedup_key)
            to_insert.append(rec)

    # Enrichment updates
    for upd in enrichment:
        fac = db.query(FacultyDB).filter(FacultyDB.id == upd["id"]).first()
        if not fac:
            continue
        if (upd["total_citations"] or 0) > (fac.total_citations or 0):
            fac.total_citations = upd["total_citations"]
            fac.h_index = max(fac.h_index or 0, upd["h_index"] or 0)
            fac.total_publications_count = max(
                fac.total_publications_count or 0, upd["total_publications_count"] or 0
            )
        if upd["openalex_id"] and not fac.openalex_id:
            fac.openalex_id = upd["openalex_id"]
        if upd["email"] and not fac.email:
            fac.email = upd["email"]
        if upd["research_interests"]:
            merged = list(set(fac.research_interests or []) | set(upd["research_interests"]))
            fac.research_interests = merged
    if enrichment:
        db.commit()

    print(f"  New: {len(to_insert)}, Enrich: {len(enrichment)}")

    if not to_insert:
        return 0, len(enrichment)

    # Generate embeddings
    print(f"  Generating {len(to_insert)} embeddings...")
    embed_texts = []
    for r in to_insert:
        name = (r.get("full_name_th") or r.get("full_name_en") or "").strip()
        interests = " | ".join((r.get("research_interests") or [])[:5])
        fac_th = r.get("faculty_th") or r.get("faculty") or ""
        embed_texts.append(f"{name} {fac_th} {univ['th']} {interests}".strip())

    with ThreadPoolExecutor(max_workers=min(4, len(clients) or 1)) as ex:
        embs = list(ex.map(get_embedding, embed_texts))

    # DB commit
    have_ids = {r[0] for r in db.query(FacultyDB.id).all()}
    seq = 0
    new_objs = []
    wave_prefix = f"{univ['prefix']}_w{univ['wave']}"

    for i, r in enumerate(to_insert):
        seq += 1
        uid = f"{wave_prefix}_{seq:04d}_{random.randint(100, 999)}"
        while uid in have_ids:
            seq += 1
            uid = f"{wave_prefix}_{seq:04d}_{random.randint(100, 999)}"
        have_ids.add(uid)

        emb = embs[i] if i < len(embs) else [0.0] * 768
        fn_th = r.get("full_name_th") or r.get("full_name_en") or "อาจารย์"

        new_objs.append(FacultyDB(
            id=uid,
            first_name=r.get("first_name") or "",
            last_name=r.get("last_name") or "",
            full_name_th=fn_th,
            academic_title_th=r.get("academic_title_th") or "",
            university=univ["en"],
            university_th=univ["th"],
            faculty=r.get("faculty") or "",
            faculty_th=r.get("faculty_th") or "",
            department=r.get("department") or "",
            department_th=r.get("department_th") or "",
            email=r.get("email") or "",
            image_url=r.get("image_url") or "",
            profile_url=r.get("profile_url") or "",
            research_interests=r.get("research_interests") or [],
            featured_publications=[],
            total_citations=r.get("total_citations") or 0,
            h_index=r.get("h_index") or 0,
            total_publications_count=r.get("works_count") or 0,
            openalex_id=r.get("openalex_id") or "",
            embedding=emb,
        ))

    batch_size = 300
    for i in range(0, len(new_objs), batch_size):
        db.add_all(new_objs[i:i + batch_size])
        db.commit()
        print(f"    Batch committed: {len(new_objs[i:i+batch_size])}")

    print(f"  {univ['short']}: +{len(new_objs)} inserted, {len(enrichment)} enriched")
    return len(new_objs), len(enrichment)


def main():
    print("=" * 70)
    print("Wave 54+55: MJU + NIDA Autonomous Acquisition Pipeline")
    print("=" * 70)

    db = SessionLocal()
    try:
        total_inserted = 0
        total_enriched = 0

        for univ in UNIVERSITIES:
            inserted, enriched = process_university(univ, db)
            total_inserted += inserted
            total_enriched += enriched

        # Final verification
        from sqlalchemy import text
        total_all = db.execute(text("SELECT COUNT(*) FROM faculties")).scalar()

        for univ in UNIVERSITIES:
            cnt = db.execute(text(
                f"SELECT COUNT(*) FROM faculties WHERE university = '{univ['en']}'"
            )).scalar()
            email_cnt = db.execute(text(
                f"SELECT COUNT(*) FROM faculties WHERE university = '{univ['en']}' "
                f"AND email != '' AND email IS NOT NULL"
            )).scalar()
            opx_cnt = db.execute(text(
                f"SELECT COUNT(*) FROM faculties WHERE university = '{univ['en']}' "
                f"AND openalex_id != '' AND openalex_id IS NOT NULL"
            )).scalar()
            print(f"\n  {univ['short']}: total={cnt}, email={email_cnt}/{cnt}, "
                  f"openalex={opx_cnt}/{cnt}")

        print(f"\n  Grand Total: {total_all:,}")
        print(f"  Wave 54+55 Summary: +{total_inserted} new, {total_enriched} enriched")

    finally:
        db.close()

    print("\nWave 54+55 Pipeline Complete!")


if __name__ == "__main__":
    main()
