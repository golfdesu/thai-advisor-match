"""
Wave 17: Kasetsart University (บางเขน) Faculty Expansion via KU Central Research Directory (KUForest).

Source portal: https://research.ku.ac.th/forest/
  - Department.aspx?CampusId=01&FacultyID=XX          -> lists Sections (departments)
  - Department.aspx?...&SectionID=YY                   -> Persons block: "ดร. NAME, TITLE" + email + avatar
  - Person.aspx?id=NNNNNN                              -> Profile, Education, Expertise Cloud, Interest, h-index

Target faculties (CampusId=01 / บางเขน):
  - 09  คณะสังคมศาสตร์        (Faculty of Social Sciences)
  - 16  คณะมนุษยศาสตร์        (Faculty of Humanities)
  - 28  คณะบริหารธุรกิจ       (Faculty of Business Administration)
  - 08  คณะเศรษฐศาสตร์         (Faculty of Economics)
  - 36  คณะสิ่งแวดล้อม         (Faculty of the Environment)
  - 38  คณะเทคนิคการสัตวแพทย์  (Faculty of Veterinary Technology)

Pipeline (5-step SOP):
  1. Real-time crawl (section list -> person detail) with polite concurrency.
  2. State reduction (normalize_thai_title_and_name) + RapidFuzz dedup vs local KU records.
  3. Disk checkpoint -> backend/data/agent_states/wave17_ku_forest_extracted.json
  4. Multi-client 768-dim vectorization (rotating Gemini keys, retry + fallback model).
  5. Local PostgreSQL commit + verification (pytest + next build run separately).

PDPA: telephone numbers shown on the portal are STRIPPED and never persisted.
"""

import re
import sys
import json
import time
import random
import logging
import threading
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.state_reducer import (
    normalize_thai_title_and_name,
    THAI_TITLES_NORMALIZATION,
)


def is_academic_title(text: str) -> bool:
    """True if the text starts with a recognized Thai/English academic title."""
    text = (text or "").strip()
    if not text:
        return False
    return any(pat.match(text) for pat, _ in THAI_TITLES_NORMALIZATION)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("crawl_wave17_ku_forest")

CHECKPOINT_PATH = ROOT_DIR / "backend" / "data" / "agent_states" / "wave17_ku_forest_extracted.json"

BASE = "https://research.ku.ac.th/forest"
CAMPUS = "01"  # บางเขน

# FacultyID -> (faculty_th, faculty_en, id_code)
TARGET_FACULTIES = {
    "09": ("คณะสังคมศาสตร์", "Faculty of Social Sciences", "soc"),
    "16": ("คณะมนุษยศาสตร์", "Faculty of Humanities", "hum"),
    "28": ("คณะบริหารธุรกิจ", "Faculty of Business Administration", "bus"),
    "08": ("คณะเศรษฐศาสตร์", "Faculty of Economics", "econ"),
    "36": ("คณะสิ่งแวดล้อม", "Faculty of the Environment", "env"),
    "38": ("คณะเทคนิคการสัตวแพทย์", "Faculty of Veterinary Technology", "vettech"),
}

UNIV = "Kasetsart University"
UNIV_TH = "มหาวิทยาลัยเกษตรศาสตร์"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Pre-compiled module-level regexes (performance invariant)
RE_SECTION_LINK = re.compile(
    r'Department\.aspx\?CampusID=' + CAMPUS + r'&FacultyID=(\d+)&SectionID=(\d+)"[^>]*>([^<]+)<',
    re.IGNORECASE,
)
RE_PERSON_CARD = re.compile(
    r'Person\.aspx\?id=(\d+)"[^>]*>\s*<span>\s*<img[^>]*src="([^"]+)"[^>]*/?>\s*</span>\s*<p>(.*?)</p>\s*</a>\s*<p>(.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)
RE_EMAIL = re.compile(r'[a-zA-Z0-9._%+\-]+@ku\.ac\.th', re.IGNORECASE)
RE_PHONE = re.compile(r'(โทร\.?|Tel\.?|0[\d\-\s\.]{6,})', re.IGNORECASE)
RE_NAME_TITLE = re.compile(r'^(.*?),\s*([^,]*?(?:ศาสตราจารย์|อาจารย์|นักวิชาการ|นักวิจัย)[^,]*)$', re.DOTALL)

RE_DETAIL_NAME = re.compile(r'<h2\s+class="name"[^>]*>\s*<a[^>]*>(.*?)</a>\s*</h2>', re.IGNORECASE | re.DOTALL)
RE_DETAIL_ACPOS = re.compile(r'<h3\s+class="acPos"[^>]*>(.*?)</h3>', re.IGNORECASE | re.DOTALL)
RE_DETAIL_MAILTO = re.compile(r'href="mailto:([^"]+)"', re.IGNORECASE)
RE_EDU_BLOCK = re.compile(r'<h3>\s*Education\s*</h3>\s*<ul>(.*?)</ul>', re.IGNORECASE | re.DOTALL)
RE_LI = re.compile(r'<li>(.*?)</li>', re.IGNORECASE | re.DOTALL)
RE_EXPERTISE_BOX = re.compile(r'<div\s+class="tagCloudBox"[^>]*>(.*?)</div>', re.IGNORECASE | re.DOTALL)
RE_CLOUD_TAG = re.compile(r'<a\s+class="cloud"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
RE_INTEREST_BLOCK = re.compile(r'id="Interest"\s*>\s*<div\s+class="itemList">\s*<h3>Interest</h3>(.*?)</div>', re.IGNORECASE | re.DOTALL)
RE_HINDEX = re.compile(r'<em>h</em>\-index:\s*([\d]+|N/A)', re.IGNORECASE)


def strip_tags(s: str) -> str:
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = (
        s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
        .replace('&#39;', "'").replace('&lt;', '<').replace('&gt;', '>')
    )
    return re.sub(r'\s+', ' ', s).strip()


def fetch_url(url: str, timeout: int = 20, retries: int = 3) -> str:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as err:  # noqa: BLE001
            last_err = err
            time.sleep(0.8 * (attempt + 1) + random.uniform(0, 0.4))
    logger.warning(f"Fetch failed after {retries} tries: {url} ({last_err})")
    return ""


def strip_all_titles(name: str) -> str:
    """Strip academic/professional prefixes for robust fuzzy dedup matching."""
    prefixes = [
        r"ศาสตราจารย์\s*เกียรติคุณ", r"ศาสตราจารย์\s*ดร\.", r"รองศาสตราจารย์\s*ดร\.",
        r"ผู้ช่วยศาสตราจารย์\s*ดร\.", r"อาจารย์\s*ดร\.",
        r"ศาสตราจารย์", r"รองศาสตราจารย์", r"ผู้ช่วยศาสตราจารย์", r"อาจารย์",
        r"ดร\.", r"ศ\.ดร\.", r"รศ\.ดร\.", r"ผศ\.ดร\.", r"อ\.ดร\.",
        r"ศ\.", r"รศ\.", r"ผศ\.", r"อ\.",
        r"นาย", r"นาง", r"นางสาว", r"ดร\.",
        r"Prof\. Dr\.", r"Assoc\. Prof\. Dr\.", r"Asst\. Prof\. Dr\.", r"Dr\.",
        r"Prof\.", r"Assoc\. Prof\.", r"Asst\. Prof\.", r"Lecturer", r"Mr\.", r"Ms\.", r"Mrs\.",
    ]
    cleaned = (name or "").strip()
    for pat in prefixes:
        cleaned = re.sub(r"^\s*" + pat + r"\s*", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


# ------------------------------------------------------------------------------
# Step 1a: enumerate sections (departments) for a faculty
# ------------------------------------------------------------------------------
def crawl_sections(faculty_id: str) -> list[tuple[str, str]]:
    url = f"{BASE}/Department.aspx?CampusId={CAMPUS}&FacultyID={faculty_id}"
    html = fetch_url(url)
    sections: list[tuple[str, str]] = []
    seen: set[str] = set()
    for _fid, sid, name in RE_SECTION_LINK.findall(html):
        name = strip_tags(name)
        if sid in seen or "(ยกเลิก)" in name:  # skip cancelled sections
            continue
        seen.add(sid)
        sections.append((sid, name))
    logger.info(f"FacultyID={faculty_id}: {len(sections)} active sections.")
    return sections


# ------------------------------------------------------------------------------
# Step 1b: parse Persons block from a section page -> list of person stubs
# ------------------------------------------------------------------------------
def crawl_section_persons(faculty_id: str, section_id: str, section_name: str) -> list[dict]:
    url = f"{BASE}/Department.aspx?CampusId={CAMPUS}&FacultyID={faculty_id}&SectionID={section_id}"
    html = fetch_url(url)
    persons: list[dict] = []
    for pid, img_src, name_block, contact_block in RE_PERSON_CARD.findall(html):
        raw_name = strip_tags(name_block)      # e.g. "ดร. บารมี อริยะเลิศเมตตา, ผู้ช่วยศาสตราจารย์"
        contact = strip_tags(contact_block)     # e.g. "fhumskn@ku.ac.th, โทร. 0-2579-..."
        email_m = RE_EMAIL.search(contact)
        email = email_m.group(0).lower() if email_m else ""
        img = img_src if img_src.startswith("http") else f"{BASE}/{img_src.lstrip('/')}"
        persons.append({
            "person_id": pid,
            "raw_name": raw_name,
            "email": email,
            "image_url": img,
            "department_th": section_name,
        })
    return persons


# ------------------------------------------------------------------------------
# Step 1c: enrich from Person.aspx detail (education, expertise, interest, h-index)
# ------------------------------------------------------------------------------
def crawl_person_detail(person_id: str) -> dict:
    url = f"{BASE}/Person.aspx?id={person_id}"
    html = fetch_url(url)
    detail = {"education": [], "expertise": [], "interest": [], "h_index": None, "acpos": "", "name": "", "email": ""}
    if not html:
        return detail

    m = RE_DETAIL_NAME.search(html)
    if m:
        detail["name"] = strip_tags(m.group(1))
    m = RE_DETAIL_ACPOS.search(html)
    if m:
        detail["acpos"] = strip_tags(m.group(1))
    m = RE_DETAIL_MAILTO.search(html)
    if m and RE_EMAIL.search(m.group(1)):
        detail["email"] = m.group(1).strip().lower()

    m = RE_EDU_BLOCK.search(html)
    if m:
        detail["education"] = [strip_tags(x) for x in RE_LI.findall(m.group(1)) if strip_tags(x)][:8]

    # Expertise Cloud tags (dedup, cap)
    box = RE_EXPERTISE_BOX.search(html)
    if box:
        tags = [strip_tags(t) for t in RE_CLOUD_TAG.findall(box.group(1))]
        clean: list[str] = []
        for t in tags:
            t = t.lstrip(": ").strip()
            if t and t not in clean:
                clean.append(t)
        detail["expertise"] = clean[:25]

    m = RE_INTEREST_BLOCK.search(html)
    if m:
        raw = strip_tags(m.group(1))
        detail["interest"] = [x.strip() for x in raw.split(",") if x.strip()][:12]

    m = RE_HINDEX.search(html)
    if m and m.group(1).isdigit():
        detail["h_index"] = int(m.group(1))

    return detail


def build_record(person: dict, detail: dict, faculty_th: str, faculty_en: str) -> dict | None:
    raw_name = person["raw_name"]  # list format: "NAME, ROLE_OR_TITLE" (e.g. "ดร. สมชาย..., ผู้ช่วยศาสตราจารย์")
    mt = RE_NAME_TITLE.match(raw_name)
    list_name_part = (mt.group(1) if mt else raw_name).strip()
    list_title_part = (mt.group(2) if mt else "").strip()

    title_src = detail.get("acpos") or ""
    name_src = (detail.get("name") or "").strip()  # detail h2.name is honorific-free

    # Prepend only genuine academic ranks; job titles like "นักวิจัย ปฏิบัติการ" are role, not title.
    if is_academic_title(list_title_part):
        title_for_norm = list_title_part
    elif is_academic_title(title_src):
        title_for_norm = title_src
    else:
        title_for_norm = ""

    # List name part keeps "ดร." (detail h2 omits it); only strip personal honorifics.
    name_clean = re.sub(r"^(นาย|นางสาว|นาง)\s+", "", list_name_part).strip() or name_src
    combined = f"{title_for_norm} {name_clean}".strip()

    th_title, th_name, base_name = normalize_thai_title_and_name(combined)
    if not base_name or len(base_name) < 3:
        return None

    # Research interests: real expertise cloud + interest, dept-level fallback only if empty
    interests = list(dict.fromkeys((detail.get("expertise") or []) + (detail.get("interest") or [])))
    dept_th = person["department_th"]
    if not interests:
        interests = [f"{dept_th} {faculty_th}", f"งานวิจัยและวิชาการด้าน{dept_th.replace('ภาควิชา', '').strip()}"]

    email = detail.get("email") or person.get("email") or ""
    # Defensive: never persist phone numbers (PDPA)
    email = RE_PHONE.sub("", email).strip()

    return {
        "university": UNIV,
        "university_th": UNIV_TH,
        "faculty": faculty_en,
        "faculty_th": faculty_th,
        "department": dept_th,
        "department_th": dept_th,
        "academic_title_th": th_title,
        "full_name_th": th_name,
        "first_name": base_name.split(" ")[0] if " " in base_name else base_name,
        "last_name": " ".join(base_name.split(" ")[1:]) if " " in base_name else "",
        "email": email,
        "image_url": person.get("image_url", ""),
        "profile_url": f"{BASE}/Person.aspx?id={person['person_id']}",
        "role": title_src or th_title,
        "research_interests": interests,
        "featured_publications": [],
        "education": detail.get("education", []),
        "taught_courses": [],
        "h_index": detail.get("h_index"),
        "person_id": person["person_id"],
    }


def crawl_faculty(faculty_id: str) -> list[dict]:
    faculty_th, faculty_en, _code = TARGET_FACULTIES[faculty_id]
    logger.info(f"=== Crawling {faculty_th} (FacultyID={faculty_id}) ===")
    sections = crawl_sections(faculty_id)
    records: list[dict] = []
    seen_pid: set[str] = set()

    for sid, sname in sections:
        persons = crawl_section_persons(faculty_id, sid, sname)
        time.sleep(0.3)
        for p in persons:
            if p["person_id"] in seen_pid:
                continue
            seen_pid.add(p["person_id"])
            detail = crawl_person_detail(p["person_id"])
            rec = build_record(p, detail, faculty_th, faculty_en)
            if rec:
                records.append(rec)
            time.sleep(0.15)
        logger.info(f"  {sname}: {len(persons)} persons.")

    logger.info(f"{faculty_th}: extracted {len(records)} faculty records.")
    return records


def run_crawl() -> list[dict]:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    for fid in TARGET_FACULTIES:
        recs = crawl_faculty(fid)
        all_records.extend(recs)
        # Incremental checkpoint after each faculty so a mid-run crash can resume.
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
            json.dump(all_records, fp, ensure_ascii=False, indent=2)
        logger.info(f"Incremental checkpoint: {len(all_records)} records -> {CHECKPOINT_PATH.name}")
    logger.info(f"Checkpoint saved: {len(all_records)} raw records -> {CHECKPOINT_PATH.name}")
    return all_records


def build_embedding_text(f: dict) -> str:
    interests = ", ".join((f.get("research_interests") or [])[:20])
    edu = " | ".join((f.get("education") or [])[:4])
    return (
        f"อาจารย์และนักวิจัย: {f.get('full_name_th', '')} ({f.get('academic_title_th', '')})\n"
        f"สังกัด: {f.get('department_th', '')}, {f.get('faculty_th', '')}, {f.get('university_th', '')}\n"
        f"วุฒิการศึกษา: {edu}\n"
        f"ความเชี่ยวชาญและงานวิจัย: {interests}"
    )


def run_pipeline(force_recrawl: bool = False):
    logger.info("=" * 50)
    logger.info("Wave 17 KU Forest Pipeline")
    logger.info("=" * 50)

    if not force_recrawl and CHECKPOINT_PATH.exists():
        logger.info(f"Loading cached extraction from {CHECKPOINT_PATH.name}")
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as fp:
            all_faculties = json.load(fp)
    else:
        all_faculties = run_crawl()

    logger.info(f"Total raw candidates: {len(all_faculties)}")

    db = SessionLocal()
    try:
        existing = db.query(FacultyDB).filter(FacultyDB.university_th == UNIV_TH).all()
        logger.info(f"Existing KU records in DB: {len(existing)}")

        new_members: list[dict] = []
        updated_count = 0
        for member in all_faculties:
            m_clean = strip_all_titles(member["full_name_th"])
            matched = None
            best = 0
            for ex in existing:
                ex_clean = strip_all_titles(ex.full_name_th or "")
                score = fuzz.token_set_ratio(m_clean, ex_clean)
                if score >= 90 and score > best:
                    best = score
                    matched = ex
            if matched:
                changed = False
                if (not matched.email or "@" not in (matched.email or "")) and member.get("email"):
                    matched.email = member["email"]; changed = True
                if (not matched.image_url or "ui-avatars" in (matched.image_url or "")) and member.get("image_url"):
                    matched.image_url = member["image_url"]; changed = True
                if member.get("department_th") and not (matched.department_th or "").strip():
                    matched.department_th = member["department_th"]
                    matched.department = member["department"]; changed = True
                cur = matched.research_interests or []
                merged = list(dict.fromkeys(cur + (member.get("research_interests") or [])))
                if len(merged) > len(cur):
                    matched.research_interests = merged; changed = True
                if changed:
                    updated_count += 1
            else:
                new_members.append(member)

        logger.info(f"Enriched existing: {updated_count} | Net new to insert: {len(new_members)}")

        if new_members:
            from google import genai
            from google.genai import types

            raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
            api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
            if not api_keys:
                raise ValueError("No Gemini API keys configured!")
            clients = [genai.Client(api_key=k) for k in api_keys]
            lock = threading.Lock()
            idx_box = [0]

            def get_embedding(text: str, max_retries: int = 6) -> list[float]:
                for attempt in range(max_retries):
                    with lock:
                        client = clients[idx_box[0] % len(clients)]
                        idx_box[0] += 1
                    for model in ["gemini-embedding-2", "gemini-embedding-001"]:
                        try:
                            res = client.models.embed_content(
                                model=model, contents=text,
                                config=types.EmbedContentConfig(output_dimensionality=768),
                            )
                            vals = res.embeddings[0].values
                            if vals and len(vals) == 768:
                                return vals
                        except Exception as err:  # noqa: BLE001
                            es = str(err)
                            if any(x in es for x in ["429", "RESOURCE_EXHAUSTED", "Quota"]):
                                time.sleep(1.0 * (attempt + 1))
                            else:
                                time.sleep(0.3)
                    time.sleep(1.5 * (attempt + 1))
                raise RuntimeError(f"Embedding failed after {max_retries} attempts: {text[:50]}")

            logger.info(f"Vectorizing {len(new_members)} new members across {len(clients)} rotating clients...")
            texts = [build_embedding_text(m) for m in new_members]
            embeddings: list = [None] * len(new_members)
            with ThreadPoolExecutor(max_workers=4) as ex:
                fut_map = {ex.submit(get_embedding, t): i for i, t in enumerate(texts)}
                done = 0
                for fut in as_completed(fut_map):
                    i = fut_map[fut]
                    embeddings[i] = fut.result()
                    done += 1
                    if done % 50 == 0:
                        logger.info(f"  embedded {done}/{len(new_members)}")

            id_counts: dict[str, int] = {}
            fac_code_by_th = {ft: code for (ft, _en, code) in TARGET_FACULTIES.values()}
            for i, m in enumerate(new_members):
                code = fac_code_by_th.get(m["faculty_th"], "gen")
                prefix = f"ku_wave17_{code}"
                id_counts[prefix] = id_counts.get(prefix, 0) + 1
                uid = f"{prefix}_{id_counts[prefix]:04d}"
                db.add(FacultyDB(
                    id=uid,
                    university=m["university"], university_th=m["university_th"],
                    faculty=m["faculty"], faculty_th=m["faculty_th"],
                    department=m["department"], department_th=m["department_th"],
                    academic_title_th=m["academic_title_th"], full_name_th=m["full_name_th"],
                    first_name=m["first_name"], last_name=m["last_name"],
                    email=m["email"], image_url=m["image_url"], profile_url=m["profile_url"],
                    role=m["role"], research_interests=m["research_interests"],
                    featured_publications=m["featured_publications"], education=m["education"],
                    taught_courses=m["taught_courses"], h_index=m.get("h_index") or 0,
                    embedding=embeddings[i],
                ))

        db.commit()
        total = db.query(FacultyDB).count()
        ku_total = db.query(FacultyDB).filter(FacultyDB.university_th == UNIV_TH).count()
        nulls = db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()
        logger.info(f"Committed: {updated_count} enriched, {len(new_members)} inserted.")
        logger.info(f"GRAND TOTAL faculties: {total:,} | KU total: {ku_total:,} | Null embeddings: {nulls}")
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force-recrawl" in sys.argv
    run_pipeline(force_recrawl=force)
