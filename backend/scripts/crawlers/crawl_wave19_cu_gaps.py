"""
Wave 19: Chulalongkorn University gap-closure crawl (approved Plan A, adapted).

No central CU portal exists (KUForest equivalent absent), so this wave targets the
five faculty rosters validated during recon (read-only probes on 2026-09-12):

  1. Law         https://www.law.chula.ac.th/about/faculty-profiles/ (paged, ~7)
                 -> card-profile blocks (rank <p.h4> + name + envelope-svg email + avatar,
                    phone-free) -> /profile/NNN/ detail for วุฒิการศึกษา / รายวิชาที่สอน. ~68.
  2. Political Sci  https://www.polsci.chula.ac.th/content?pid=8
                 -> server-rendered single__program cards (name+title, email, photo). ~70.
  3. Economics   https://www.econ.chula.ac.th/ຄณาจารย์/ (percent-encoded Thai URL, ECON_THAI_URL)
                 -> Thai h4 roster cards (54): rank+Thai name, mailto, uploads photo; 12
                    /portfolio/ detail pages add education/expertise/publications.
  4. Education   https://eduadmin.edu.chula.ac.th/api/v1/staffs/
                 -> clean JSON: name (Thai w/ title), email, image, departments[],
                    staff_positions[]. type==TEACHER only. 129 teachers.
  5. Psychology  https://www.psy.chula.ac.th/th/people-sitemap.xml -> /th/people/<slug>/
                 -> h1 name + role line; keep only academic ranks (filter admin staff);
                    personal email from the Email <li> of people-contact (never Phone). ~35.

Skipped for this round (JS-SPA / legacy, no harvestable path): นิเทศศาสตร์, อักษรศาสตร์,
พยาบาล, ศิลปกรรม, กีฬา.

Pipeline (5-step SOP, same contract as Waves 17/18):
  crawl -> checkpoint (incremental per source) -> RapidFuzz dedup/enrich vs local CU
  -> 768-dim vectorization (rotating Gemini keys) -> local PostgreSQL commit.

PDPA: telephone numbers on these pages (PolSci/Econ/Psy/Edu) are stripped, never persisted.
"""

import re
import sys
import json
import time
import random
import logging
import threading
import urllib.request
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("crawl_wave19_cu_gaps")

CHECKPOINT_PATH = ROOT_DIR / "backend" / "data" / "agent_states" / "wave19_cu_gaps_extracted.json"

WAVE = "wave19"
UNIV = "Chulalongkorn University"
UNIV_TH = "จุฬาลงกรณ์มหาวิทยาลัย"

SOURCES = [
    ("law", "คณะนิติศาสตร์", "Faculty of Law"),
    ("polsci", "คณะรัฐศาสตร์", "Faculty of Political Science"),
    ("econ", "คณะเศรษฐศาสตร์", "Faculty of Economics"),
    ("edu", "คณะครุศาสตร์", "Faculty of Education"),
    ("psy", "คณะจิตวิทยา", "Faculty of Psychology"),
]

ECON_THAI_URL = ("https://www.econ.chula.ac.th/"
                 "%e0%b8%84%e0%b8%93%e0%b8%b2%e0%b8%88%e0%b8%b2%e0%b8%a3%e0%b8%a2%e0%b9%8c/")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

RE_PHONE = re.compile(r'(โทร\.?|Tel\.?|Phone(?: Number)?[:\s]*|0[\d\-\s\.]{6,})', re.IGNORECASE)
RE_EMAIL = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
RE_PERSONAL_HONORIFIC = re.compile(r"^(นาย|นางสาว|นาง)\s+")
RE_EN_NAME = re.compile(r'^[A-Za-z][A-Za-z .\'\-]+$')


def is_academic_title(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    return any(pat.match(text) for pat, _ in THAI_TITLES_NORMALIZATION)


def strip_tags(s: str) -> str:
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = (
        s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
        .replace('&#39;', "'").replace('&lt;', '<').replace('&gt;', '>')
        .replace('&#038;', '&')
    )
    return re.sub(r'\s+', ' ', s).strip()


def fetch_url(url: str, timeout: int = 25, retries: int = 3) -> str:
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
    prefixes = [
        r"ศาสตราจารย์\s*พิเศษ", r"ศาสตราจารย์\s*เกียรติคุณ", r"ศาสตราจารย์\s*ดร\.", r"รองศาสตราจารย์\s*ดร\.",
        r"ผู้ช่วยศาสตราจารย์\s*ดร\.", r"อาจารย์\s*ดร\.",
        r"ศาสตราจารย์", r"รองศาสตราจารย์", r"ผู้ช่วยศาสตราจารย์", r"อาจารย์",
        r"ดร\.", r"ศ\.ดร\.", r"รศ\.ดร\.", r"ผศ\.ดร\.", r"อ\.ดร\.",
        r"ศ\.", r"รศ\.", r"ผศ\.", r"อ\.",
        r"นาย", r"นาง", r"นางสาว",
        r"Prof\. Dr\.", r"Assoc\. Prof\. Dr\.", r"Asst\. Prof\. Dr\.", r"Dr\.",
        r"Prof\.", r"Assoc\. Prof\.", r"Asst\. Prof\.", r"Lecturer", r"Mr\.", r"Ms\.", r"Mrs\.",
    ]
    cleaned = (name or "").strip()
    for pat in prefixes:
        cleaned = re.sub(r"^\s*" + pat + r"\s*", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


PSY_ACADEMIC_RANKS = re.compile(r'^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)\b')

# Rank tokens only — roles like "อ. ประจำสาขาวิชาศิลปศึกษา" must yield "อ.", never the tail text.
RE_RANK_TOKEN = re.compile(
    r'^\s*(ศาสตราจารย์(?:พิเศษ|เกียรติคุณ)?|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)'
    r'(?:\s*(ดร\.))?\s*$'
)


def rank_token(text: str) -> str:
    """Return the pure academic-rank prefix of `text` ('' if not rank-led)."""
    text = (text or "").strip()
    m = re.match(
        r'^(ศาสตราจารย์(?:พิเศษ|เกียรติคุณ)?|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)'
        r'(?:\s*(ดร\.))?(?=[\s฀-๿]|$)', text)
    if not m:
        m2 = re.match(r'^((?:ศ|รศ|ผศ|อ)\.(?:\s*ดร\.)?)(?=[\s]|$)', text)
        if m2:
            return re.sub(r'\s+', '', m2.group(1))
        return ""
    full_rank = m.group(1)
    short = {"ศาสตราจารย์": "ศ.", "รองศาสตราจารย์": "รศ.", "ผู้ช่วยศาสตราจารย์": "ผศ.", "อาจารย์": "อ."}
    out = short.get(full_rank, "")
    if m.group(2) and out:
        out = out[:-1] + ".ดร."
    return out


def make_record(source: str, faculty_th: str, faculty_en: str, raw_name: str, role_or_title: str,
                email: str, image_url: str, profile_url: str, department_th: str,
                education: list[str], courses: list[str], interests: list[str],
                publications: list[str] | None = None) -> dict | None:
    """Shared name-builder discipline from Wave 17: prepend ONLY recognized academic
    ranks; job titles / admin positions go to `role`, never into the name.
    Personal honorifics (นาย/นาง/นางสาว) are stripped; 'ดร.' inside the name part stays."""
    raw_name = strip_tags(raw_name)
    role_or_title = strip_tags(role_or_title)
    email = (email or "").strip().lower()
    email = RE_PHONE.sub("", email).strip()
    if email and "@" not in email:
        email = ""

    # Split leading rank off the name itself when present ("ศ.ดร.ชื่อ", "รองศาสตราจารย์ ดร.ชื่อ",
    # abbreviated "ผศ. ดร.ชื่อ" too). Name rank wins over role rank (Edu staff_positions
    # often carry a generic "อ." even when the person is ผศ.).
    m = re.match(
        r'^(ศาสตราจารย์(?:พิเศษ|เกียรติคุณ)?|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์'
        r'|ศ\.|รศ\.|ผศ\.|อ\.)\s*(ดร\.)?\s*', raw_name)
    rank_part = (m.group(0).strip() if m else "")
    name_part = (raw_name[m.end():].strip() if m else raw_name)
    # Titles come from RANK TOKENS ONLY ("อ. ประจำสาขาวิชา..." -> "อ.", never the tail),
    # the Wave 17 contamination lesson.
    title_src = rank_part + (" " + (m.group(2) or "") if m and m.group(2) else "")
    if not is_academic_title(title_src.strip()) and is_academic_title(role_or_title):
        title_src = rank_token(role_or_title)

    name_clean = RE_PERSONAL_HONORIFIC.sub("", name_part).strip() or name_part
    combined = f"{title_src.strip()} {name_clean}".strip()
    th_title, th_name, base_name = normalize_thai_title_and_name(combined)
    if not base_name or len(base_name) < 2:
        return None

    interests = list(dict.fromkeys([t for t in interests if t]))
    if not interests:
        dept_core = (department_th or faculty_th).replace("ภาควิชา", "").replace("สาขาวิชา", "").strip()
        interests = [f"{dept_core} {faculty_th}", f"งานวิจัยและวิชาการด้าน{dept_core}"]

    is_en = bool(RE_EN_NAME.match(base_name))
    return {
        "university": UNIV,
        "university_th": UNIV_TH,
        "faculty": faculty_en,
        "faculty_th": faculty_th,
        "department": department_th,
        "department_th": department_th,
        "academic_title_th": th_title,
        "full_name_th": th_name,
        "first_name": base_name.split(" ")[0] if " " in base_name else base_name,
        "last_name": " ".join(base_name.split(" ")[1:]) if " " in base_name else "",
        "email": email,
        "image_url": image_url or "",
        "profile_url": profile_url,
        "role": role_or_title if role_or_title != title_src.strip() else (title_src.strip() or th_title),
        "research_interests": interests,
        "featured_publications": [p for p in (publications or [])][:8],
        "education": education or [],
        "taught_courses": courses or [],
        "h_index": 0,
        "person_id": f"{source}-en" if is_en else f"{source}-th",  # marker only, not persisted as id
    }


# ------------------------------------------------------------------ sources --

RE_LAW_CARD = re.compile(
    r'<div class="col-8 col-xl-7">.*?<p class="h4 mb-0">(.*?)</p>\s*<h3[^>]*><a href="(https://www\.law\.chula\.ac\.th/profile/\d+/)"><span>(.*?)</span></a></h3>',
    re.IGNORECASE | re.DOTALL,
)
RE_LAW_EMAIL = re.compile(r'</svg>\s*([\w.%+\-]+@[\w.\-]+\.[a-z]{2,})\s*</(?:span|a|div|p)>', re.IGNORECASE)
RE_LAW_SECTION = re.compile(
    r'<strong>(วุฒิการศึกษา|รายวิชาที่สอน|ความสนใจ)\s*[:&nbsp;]*</strong>(.*?)(?=<strong>|</div>\s*</div>|$)',
    re.IGNORECASE | re.DOTALL,
)
RE_LI_ANY = re.compile(r'<(?:li|p)[^>]*>(.*?)</(?:li|p)>', re.IGNORECASE | re.DOTALL)


def crawl_law() -> list[dict]:
    faculty_th, faculty_en = "คณะนิติศาสตร์", "Faculty of Law"
    cards: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    listing = "https://www.law.chula.ac.th/about/faculty-profiles/"
    for page in range(1, 8):
        url = listing if page == 1 else f"{listing}page/{page}/"
        html = fetch_url(url)
        if not html:
            break
        found = RE_LAW_CARD.findall(html)
        new = 0
        for title, prof_url, name in found:
            if prof_url in seen:
                continue
            seen.add(prof_url)
            cards.append((title, prof_url, name))
            new += 1
        logger.info(f"  Law page {page}: {len(found)} cards ({new} new).")
        if new == 0:
            break
    records: list[dict] = []
    for title, prof_url, name in cards:
        html = fetch_url(prof_url)
        time.sleep(0.15)
        email_m = RE_LAW_EMAIL.search(html or "")
        education, courses, interests = [], [], []
        if html:
            # scope to the article body — head og:description otherwise leaks section names
            art = re.search(r'<article.*?</article>', html, re.S)
            body = re.sub(r'<script.*?</script>|<style.*?</style>', '', art.group(0) if art else html, flags=re.S)
            txt_lines = [strip_tags(x) for x in re.split(r'</(?:li|p|h2|h3)>', body)]
            grab = False
            for ln in txt_lines:
                if not ln:
                    continue
                if ln.startswith("วุฒิการศึกษา"):
                    grab = "edu"; continue
                if ln.startswith("รายวิชาที่สอน"):
                    grab = "crs"; continue
                if grab == "edu" and re.match(r'^([฀-๿]|Diplome|DIPLOME|Master|Doctor|LL\.?M|LL\.?B|S\.?J\.?D)', ln) and len(ln) > 4:
                    education.append(ln)
                if grab == "crs" and len(ln) > 3 and not ln.startswith(("รู้จัก", "ประวัติ", "ผู้บริหาร", "คณาจารย์", "บุคลากร")):
                    courses.append(ln)
            education = education[:8]; courses = courses[:8]
        interests = courses[:6]
        img_m = re.search(r'<img[^>]+src="(https://www\.law\.chula\.ac\.th/wp-content/uploads/[^"]+)"', html or "")
        rec = make_record("law", faculty_th, faculty_en, f"{title} {name}".strip(), title,
                          email_m.group(1) if email_m else "", img_m.group(1) if img_m else "",
                          prof_url, "", education, courses, interests)
        if rec:
            records.append(rec)
    return records


RE_POLSCI_CARD = re.compile(
    r'<div class="single__program">.*?<img src="(https://www\.polsci\.chula\.ac\.th/[^"]+)"[^>]*>.*?<a href="([^"]+)">\s*([฀-๿][^<]*?)\s*</a>\s*</h4>\s*<div>\s*อีเมล\s*:\s*([^<]+?)\s*</div>',
    re.IGNORECASE | re.DOTALL,
)

RE_POLSCI_DEPT = re.compile(r'<h[23][^>]*>([^<]*(?:ภาควิชา|สาขาวิชา)[^<]*)</h[23]>', re.IGNORECASE)


def crawl_polsci() -> list[dict]:
    faculty_th, faculty_en = "คณะรัฐศาสตร์", "Faculty of Political Science"
    html = fetch_url("https://www.polsci.chula.ac.th/content?pid=8")
    if not html:
        return []
    # map card positions to department headings
    dept_spans = [(m.start(), strip_tags(m.group(1))) for m in RE_POLSCI_DEPT.finditer(html)]

    def dept_for(pos: int) -> str:
        best = ""
        for s, name in dept_spans:
            if s < pos:
                best = name
            else:
                break
        return best

    records: list[dict] = []
    for img_url, prof_url, name, email in RE_POLSCI_CARD.findall(html):
        name = strip_tags(name)
        email = RE_EMAIL.search(email or "")
        prof_url = prof_url.replace("&amp;", "&")
        if not prof_url.startswith("http"):
            prof_url = f"https://www.polsci.chula.ac.th{prof_url}"
        if not name or not is_academic_title(re.sub(r'^\S*?[\.\s]', '', name) if False else name):
            # name includes its rank inline ("ศ.ดร.สิริพรรณ ...") -> make_record splits it
            pass
        pos = html.find(name[:8])
        rec = make_record("polsci", faculty_th, faculty_en, name, "",
                          email.group(0) if email else "",
                          img_url if img_url.startswith("http") else f"https://www.polsci.chula.ac.th/{img_url.lstrip('/')}",
                          prof_url, dept_for(pos if pos > 0 else 0), [], [], [])
        if rec:
            records.append(rec)
    return records


RE_ECON_NAME = re.compile(r'<h4[^>]*>\s*(.*?)\s*</h4>', re.IGNORECASE | re.DOTALL)
RE_ECON_MAILTO = re.compile(r'mailto:([^"<>@]+@[^"<>]+)', re.IGNORECASE)
RE_ECON_CARD_IMG = re.compile(r'data-lazy-src="(https://www\.econ\.chula\.ac\.th/wp-content/uploads/[^"]+?\.(?:jpg|png))"', re.IGNORECASE)
RE_ECON_PORT = re.compile(r'<a href="(https://www\.econ\.chula\.ac\.th/[^"]*portfolio/[^"]+)"')
RE_ECON_PORT_H1 = re.compile(r'<h1[^>]*tag_line_title[^>]*>\s*(.*?)\s*</h1>', re.IGNORECASE | re.DOTALL)
RE_ECON_PORT_SEC = re.compile(
    r'<h3>\s*(การศึกษา|ความเชี่ยวชาญ|ผลงานวิจัยที่น่าสนใจ)\s*</h3>\s*<ul>(.*?)</ul>',
    re.IGNORECASE | re.DOTALL,
)
RE_ECON_PORT_LI = re.compile(r'<li>(.*?)</li>', re.IGNORECASE | re.DOTALL)


def econ_portfolio_enrich() -> dict:
    """Fetch the 12 faculty portfolio pages; map Thai name -> (education, expertise, pubs)."""
    th = fetch_url(ECON_THAI_URL)
    if not th:
        return {}
    links = sorted(set(RE_ECON_PORT.findall(th)))
    enrich: dict[str, dict] = {}
    for url in links:
        html = fetch_url(url.replace("&amp;", "&"))
        time.sleep(0.15)
        if not html:
            continue
        m_h1 = RE_ECON_PORT_H1.search(html)
        if not m_h1:
            continue
        key = strip_tags(m_h1.group(1)).lower().replace(" ", "")
        sections = {}
        for head, block in RE_ECON_PORT_SEC.findall(html):
            items = [strip_tags(x) for x in RE_ECON_PORT_LI.findall(block)]
            sections[head] = [i for i in items if i and not RE_PHONE.search(i)][:8]
        if key:
            enrich[key] = sections
    logger.info(f"  Econ portfolio enrichment pages: {len(enrich)}/{len(links)}")
    return enrich


def crawl_econ() -> list[dict]:
    """Thai คณาจารย์ roster page: 54 h4 cards (Thai rank + name, mailto, photo). Phone stripped."""
    faculty_th, faculty_en = "คณะเศรษฐศาสตร์", "Faculty of Economics"
    html = fetch_url(ECON_THAI_URL)
    if not html:
        return []
    enrich = econ_portfolio_enrich()
    records: list[dict] = []
    seen_email: set[str] = set()
    parts = html.split('class="team-image">')
    for part in parts[1:]:
        nm = RE_ECON_NAME.search(part)
        if not nm:
            continue
        raw_name = strip_tags(nm.group(1))
        if not raw_name or "@" in raw_name or len(raw_name) < 3:
            continue
        em = RE_ECON_MAILTO.search(part)
        email = strip_tags(em.group(1)) if em else ""
        if not email or not RE_EMAIL.search(email):
            continue
        email = RE_EMAIL.search(email).group(0)
        if email.lower() in seen_email:
            continue
        seen_email.add(email.lower())
        im = RE_ECON_CARD_IMG.search(part)
        img = im.group(1) if im else ""
        img = re.sub(r'-\d+x\d+\.(jpg|png)$', r'.\1', img)
        sec = enrich.get(raw_name.lower().replace(" ", ""), {})
        education = sec.get("การศึกษา", [])
        pubs = sec.get("ผลงานวิจัยที่น่าสนใจ", [])
        interests = sec.get("ความเชี่ยวชาญ", [])
        rec = make_record("econ", faculty_th, faculty_en, raw_name, "", email, img,
                          ECON_THAI_URL, "", education, [], interests, pubs)
        if rec:
            records.append(rec)
    return records


def crawl_edu() -> list[dict]:
    faculty_th, faculty_en = "คณะครุศาสตร์", "Faculty of Education"
    raw = fetch_url("https://eduadmin.edu.chula.ac.th/api/v1/staffs/")
    try:
        payload = json.loads(raw)
        staffs = payload["data"]["staffs"]
    except Exception as err:  # noqa: BLE001
        logger.warning(f"Edu API parse failed: {err}")
        return []
    records: list[dict] = []
    for s in staffs:
        if (s.get("type") or "").upper() != "TEACHER":
            continue
        name = s.get("name") or ""
        dept = ", ".join(d["name"] for d in (s.get("departments") or []))
        div = ", ".join(d["name"] for d in (s.get("divisions") or []))
        dept_th = " ".join(x for x in [dept, div] if x)
        pos = (s.get("staff_positions") or [{}])[0].get("name", "")
        experts = [e.get("name", "") for e in (s.get("staff_experts") or []) if e.get("name")]
        email = (s.get("email") or "").strip()
        rec = make_record("edu", faculty_th, faculty_en, name, pos, email,
                          s.get("image") or "", f"https://www.edu.chula.ac.th/th/faculty-member",
                          dept_th, [], [], experts)
        if rec:
            records.append(rec)
    return records


RE_PSY_SLUG = re.compile(r'<loc>(https://www\.psy\.chula\.ac\.th/th/people/[\w\-]+/)</loc>', re.IGNORECASE)
RE_PSY_H1 = re.compile(r'<h1[^>]*>\s*(.*?)\s*</h1>', re.IGNORECASE | re.DOTALL)
RE_PSY_ROLE = re.compile(r'</h1>\s*<[^>]+>([^<]{3,90})<', re.IGNORECASE)
RE_PSY_MAILTO = re.compile(r'mailto:([^"<>]+@[\w.\-]+\.[a-z]{2,})', re.IGNORECASE)
# personal email sits in the Email <li> of people-contact; Phone/Office <li>s must never leak.
RE_PSY_CONTACT_MAIL = re.compile(
    r'<h6>Email</h6>\s*</div>\s*<div[^>]*>\s*<h6[^>]*>\s*([^<@]+@[\w.\-]+\.[a-z]{2,})\s*</h6>',
    re.IGNORECASE,
)
RE_PSY_IMG = re.compile(r'<img[^>]+src="(https://[^"]+digitaloceanspaces[^"]+)"[^>]*>')
RE_PSY_DEG = re.compile(r'(?:ปริญญ[a-zก-๙\s\.\(\)]*(?:ตรี|โท|เอก|บัณฑิต|มหาบัณฑิต)|Ph\.?\s?D|Ed\.?\s?D|EdM|M\.?S\.?c|B\.?S\.?c|Dr\.)[^<\n]{0,110}', re.IGNORECASE)


def crawl_psy() -> list[dict]:
    faculty_th, faculty_en = "คณะจิตวิทยา", "Faculty of Psychology"
    xml = fetch_url("https://www.psy.chula.ac.th/th/people-sitemap.xml")
    slugs = sorted(set(RE_PSY_SLUG.findall(xml)))
    logger.info(f"  Psy people slugs: {len(slugs)}")
    records: list[dict] = []
    for url in slugs:
        html = fetch_url(url)
        time.sleep(0.1)
        if not html:
            continue
        m_h1 = RE_PSY_H1.search(html)
        if not m_h1:
            continue
        name = strip_tags(m_h1.group(1))
        if not name or len(name) < 3 or "@" in name:
            continue
        m_role = RE_PSY_ROLE.search(html)
        role = strip_tags(m_role.group(1)) if m_role else ""
        # academic only: role line must start with a recognized academic rank
        # (admin staff also carry 'ดร.' inside their names, so name markers are unreliable).
        rank_in_name = re.match(r'^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์)', name)
        if not (PSY_ACADEMIC_RANKS.match(role) or rank_in_name):
            continue
        m_mail = RE_PSY_CONTACT_MAIL.search(html)
        if not m_mail:
            m_mail = RE_PSY_MAILTO.search(html)
            if m_mail and m_mail.group(1).strip().lower() == "psy@chula.ac.th":
                m_mail = None  # generic faculty address is not personal contact
        m_img = RE_PSY_IMG.search(html)
        body = re.sub(r'<script.*?</script>|<style.*?</style>', '', html, flags=re.S)
        edu = [strip_tags(x)[:140] for x in RE_PSY_DEG.findall(body)][:6]
        rec = make_record("psy", faculty_th, faculty_en, name if rank_in_name else f"{role} {name}",
                          role, m_mail.group(1) if m_mail else "",
                          m_img.group(1) if m_img else "", url, "", edu, [], [])
        if rec:
            records.append(rec)
    return records


CRAWLERS = {
    "law": crawl_law,
    "polsci": crawl_polsci,
    "econ": crawl_econ,
    "edu": crawl_edu,
    "psy": crawl_psy,
}


def run_crawl() -> list[dict]:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_records: list[dict] = []
    seen_key: set[str] = set()
    for code, faculty_th, _faculty_en in SOURCES:
        logger.info(f"=== Crawling {faculty_th} ({code}) ===")
        try:
            records = CRAWLERS[code]()
        except Exception as err:  # noqa: BLE001
            logger.error(f"Source {code} failed: {err}")
            records = []
        fresh = 0
        for r in records:
            key = (r["faculty_th"] + "|" + r["full_name_th"]).lower()
            if key in seen_key:
                continue
            seen_key.add(key)
            all_records.append(r)
            fresh += 1
        logger.info(f"{faculty_th}: {fresh} records (cumulative {len(all_records)}).")
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fp:
            json.dump(all_records, fp, ensure_ascii=False, indent=2)
    logger.info(f"Checkpoint saved: {len(all_records)} raw records -> {CHECKPOINT_PATH.name}")
    return all_records


def build_embedding_text(f: dict) -> str:
    interests = ", ".join((f.get("research_interests") or [])[:20])
    edu = " | ".join((f.get("education") or [])[:4])
    courses = ", ".join((f.get("taught_courses") or [])[:6])
    return (
        f"อาจารย์และนักวิจัย: {f.get('full_name_th', '')} ({f.get('academic_title_th', '')})\n"
        f"สังกัด: {f.get('department_th', '')}, {f.get('faculty_th', '')}, {f.get('university_th', '')}\n"
        f"วุฒิการศึกษา: {edu}\n"
        f"รายวิชาที่สอน: {courses}\n"
        f"ความเชี่ยวชาญและงานวิจัย: {interests}"
    )


def run_pipeline(force_recrawl: bool = False):
    logger.info("=" * 50)
    logger.info("Wave 19 CU Gaps Pipeline")
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
        logger.info(f"Existing CU records in DB: {len(existing)}")

        new_members: list[dict] = []
        new_clean_keys: set[str] = set()
        updated_count = 0
        for member in all_faculties:
            m_clean = strip_all_titles(member["full_name_th"])
            if m_clean in new_clean_keys:
                continue
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
                if member.get("education") and not (matched.education or []):
                    matched.education = member["education"]; changed = True
                if member.get("taught_courses") and not (matched.taught_courses or []):
                    matched.taught_courses = member["taught_courses"]; changed = True
                cur = matched.research_interests or []
                merged = list(dict.fromkeys(cur + (member.get("research_interests") or [])))
                if len(merged) > len(cur):
                    matched.research_interests = merged; changed = True
                if changed:
                    updated_count += 1
            else:
                new_clean_keys.add(m_clean)
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
            for i, m in enumerate(new_members):
                prefix = f"cu_{WAVE}_{m['person_id'].split('-')[0]}"
                if not prefix.startswith("cu_wave19_"):
                    prefix = f"cu_{WAVE}_gen"
                # source code is carried in faculty mapping:
                src = next((c for c, ft, _e in SOURCES if ft == m["faculty_th"]), "gen")
                prefix = f"cu_{WAVE}_{src}"
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
        cu_total = db.query(FacultyDB).filter(FacultyDB.university_th == UNIV_TH).count()
        nulls = db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()
        logger.info(f"Committed: {updated_count} enriched, {len(new_members)} inserted.")
        logger.info(f"GRAND TOTAL faculties: {total:,} | CU total: {cu_total:,} | Null embeddings: {nulls}")
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force-recrawl" in sys.argv
    run_pipeline(force_recrawl=force)
