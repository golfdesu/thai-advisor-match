# -*- coding: utf-8 -*-
"""Wave21 regional sparse famous-faculty headless recovery.
Reuses proven fetch+parse routines (import, no in-chat HTML):
- fetch pattern from crawl_wave2_regional_faculties / crawl_buu_su_mfu_pipeline
- normalize_thai_title_and_name + PHONE_REGEX from agentic_pipeline.state_reducer
Writes raw checkpoint only, NO DB commit.
"""
import os, sys, re, ssl, json, logging, urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))
try:
    from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name, PHONE_REGEX
except Exception:
    from agentic_pipeline.state_reducer import normalize_thai_title_and_name, PHONE_REGEX
from rapidfuzz import fuzz
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("wave21")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
TITLE_RE = re.compile(r"(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ภก\.|ภญ\.|Prof\.|Assoc\.|Assist\.|Dr\.)")
BAD_NAME_HINTS = ("สถานที่ติดต่อ", "คณะ", "ภาควิชา", "สาขาวิชา", "มหาวิทยาลัย", "สำนักงาน", "ฝ่าย",
                  "Computer", "Science Group", "Contact", "Download", "โทรศัพท์", "รายละเอียด")
CHECKPOINT = BACKEND / "data" / "agent_states" / "wave21_regional_sparse_extracted.json"

TARGETS = [
    dict(key="swu_eng", university_th="มหาวิทยาลัยศรีนครินทรวิโรฒ", university_en="Srinakharinwirot University",
         faculty_th="คณะวิศวกรรมศาสตร์", faculty_en="Faculty of Engineering",
         q="site:swu.ac.th คณะวิศวกรรมศาสตร์ บุคลากร อาจารย์", seeds=["https://eng.swu.ac.th/", "https://eng.swu.ac.th/personnel"]),
    dict(key="swu_pharm", university_th="มหาวิทยาลัยศรีนครินทรวิโรฒ", university_en="Srinakharinwirot University",
         faculty_th="คณะเภสัชศาสตร์", faculty_en="Faculty of Pharmacy",
         q="site:swu.ac.th คณะเภสัชศาสตร์ บุคลากร อาจารย์", seeds=["https://pharm.swu.ac.th/", "https://pharmacy.swu.ac.th/"]),
    dict(key="swu_sci", university_th="มหาวิทยาลัยศรีนครินทรวิโรฒ", university_en="Srinakharinwirot University",
         faculty_th="คณะวิทยาศาสตร์", faculty_en="Faculty of Science",
         q="site:swu.ac.th คณะวิทยาศาสตร์ บุคลากร อาจารย์", seeds=["https://sci.swu.ac.th/"]),
    dict(key="swu_dent", university_th="มหาวิทยาลัยศรีนครินทรวิโรฒ", university_en="Srinakharinwirot University",
         faculty_th="คณะทันตแพทยศาสตร์", faculty_en="Faculty of Dentistry",
         q="site:swu.ac.th คณะทันตแพทยศาสตร์ บุคลากร อาจารย์", seeds=["https://dent.swu.ac.th/"]),
    dict(key="buu_pharm", university_th="มหาวิทยาลัยบูรพา", university_en="Burapha University",
         faculty_th="คณะเภสัชศาสตร์", faculty_en="Faculty of Pharmaceutical Sciences",
         q="site:buu.ac.th คณะเภสัชศาสตร์ บุคลากร อาจารย์", seeds=["https://pharm.buu.ac.th/", "https://pharmacy.buu.ac.th/"]),
    dict(key="buu_sci", university_th="มหาวิทยาลัยบูรพา", university_en="Burapha University",
         faculty_th="คณะวิทยาศาสตร์", faculty_en="Faculty of Science",
         q="site:buu.ac.th คณะวิทยาศาสตร์ บุคลากร อาจารย์", seeds=["https://sci.buu.ac.th/", "https://science.buu.ac.th/"]),
    dict(key="up_eng", university_th="มหาวิทยาลัยพะเยา", university_en="University of Phayao",
         faculty_th="คณะวิศวกรรมศาสตร์", faculty_en="School of Engineering",
         q="site:up.ac.th คณะวิศวกรรมศาสตร์ บุคลากร อาจารย์", seeds=["https://eng.up.ac.th/"]),
    dict(key="up_med", university_th="มหาวิทยาลัยพะเยา", university_en="University of Phayao",
         faculty_th="คณะแพทยศาสตร์", faculty_en="School of Medicine",
         q="site:up.ac.th คณะแพทยศาสตร์ บุคลากร อาจารย์", seeds=["https://med.up.ac.th/", "https://medicine.up.ac.th/"]),
    dict(key="up_pub", university_th="มหาวิทยาลัยพะเยา", university_en="University of Phayao",
         faculty_th="คณะสาธารณสุขศาสตร์", faculty_en="School of Public Health",
         q="site:up.ac.th สาธารณสุขศาสตร์ บุคลากร อาจารย์", seeds=["https://ph.up.ac.th/", "https://publichealth.up.ac.th/"]),
    dict(key="ubu_eng", university_th="มหาวิทยาลัยอุบลราชธานี", university_en="Ubon Ratchathani University",
         faculty_th="คณะวิศวกรรมศาสตร์", faculty_en="Faculty of Engineering",
         q="site:ubu.ac.th คณะวิศวกรรมศาสตร์ บุคลากร อาจารย์", seeds=["https://www.eng.ubu.ac.th/"]),
    dict(key="ubu_sci", university_th="มหาวิทยาลัยอุบลราชธานี", university_en="Ubon Ratchathani University",
         faculty_th="คณะวิทยาศาสตร์", faculty_en="Faculty of Science",
         q="site:ubu.ac.th คณะวิทยาศาสตร์ บุคลากร อาจารย์", seeds=["https://www.sci.ubu.ac.th/"]),
    dict(key="nu_dent", university_th="มหาวิทยาลัยนเรศวร", university_en="Naresuan University",
         faculty_th="คณะทันตแพทยศาสตร์", faculty_en="Faculty of Dentistry",
         q="site:nu.ac.th คณะทันตแพทยศาสตร์ บุคลากร อาจารย์", seeds=["https://www.dent.nu.ac.th/"]),
    dict(key="nu_pharm", university_th="มหาวิทยาลัยนเรศวร", university_en="Naresuan University",
         faculty_th="คณะเภสัชศาสตร์", faculty_en="Faculty of Pharmaceutical Sciences",
         q="site:nu.ac.th คณะเภสัชศาสตร์ บุคลากร อาจารย์", seeds=["https://www.pharm.nu.ac.th/", "https://pharmacy.nu.ac.th/"]),
]

def load_serp_keys():
    keys = []
    envp = BACKEND / ".env"
    if envp.exists():
        for line in envp.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("SERPAPI_KEYS"):
                keys += [k.strip() for k in line.split("=", 1)[1].strip().strip("\"'").split(",") if k.strip()]
            elif line.strip().startswith("SERPAPI_KEY") and "KEYS" not in line:
                v = line.split("=", 1)[1].strip().strip("\"'")
                if v: keys.append(v)
    keys += [v for v in [os.getenv("SERPAPI_KEYS"), os.getenv("SERPAPI_KEY")] if v]
    seen, out = set(), []
    for k in keys:
        for part in k.split(","):
            part = part.strip()
            if part and part not in seen:
                seen.add(part); out.append(part)
    return out

def serp_resolve(query, api_key, timeout=12):
    try:
        url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(
            {"engine": "google", "q": query, "num": 5, "hl": "th", "api_key": api_key})
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        urls = []
        for item in (data.get("organic_results") or [])[:5]:
            link = item.get("link", "")
            if link: urls.append(link)
        return urls
    except Exception as e:
        log.warning(f"SERP fail [{query[:40]}]: {e}")
        return []

def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
            raw = r.read()
            final = r.geturl()
        try: html = raw.decode("utf-8", errors="ignore")
        except Exception: html = raw.decode("tis-620", errors="ignore")
        return html, final
    except Exception as e:
        log.warning(f"fetch fail {url}: {e}")
        return "", url

def extract_records(html, page_url, t):
    """Generic proven-pattern parser: title-prefixed human names + adjacent official emails."""
    recs = []
    if not html: return recs
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style", "nav", "footer"]): s.decompose()
    text = soup.get_text("\n")
    text = PHONE_REGEX.sub("", text)  # PDPA strip
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # candidate name lines with academic title + Thai/EN human name
    for i, line in enumerate(lines):
        if len(line) > 120 or len(line) < 6: continue
        if not TITLE_RE.search(line): continue
        if any(b in line for b in BAD_NAME_HINTS): continue
        # find email within ±4 lines
        window = "\n".join(lines[max(0, i-4):i+5])
        em = EMAIL_RE.search(window)
        email = em.group(0).lower() if em else None
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email): email = None
        try:
            title_th, full_th, base = normalize_thai_title_and_name(line)
        except Exception: continue
        if not base or len(base.split()) < 2: continue
        if any(b in base for b in BAD_NAME_HINTS): continue
        if "@" in base or "http" in base: continue
        # profile url: nearest anchor with personnel/staff/member/person/teacher
        profile_url = page_url
        recs.append({"university_th": t["university_th"], "university_en": t["university_en"],
                     "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
                     "full_name_th": full_th, "academic_title_th": title_th,
                     "email": email, "profile_url": profile_url, "source_page": page_url})
    # also harvest mailto anchors with name context
    try:
        for a in soup.find_all("a", href=re.compile(r"mailto:", re.I)):
            email = EMAIL_RE.search(a.get("href", "") or "")
            if not email: continue
            em = email.group(0).lower()
            ctx = a.parent.get_text(" ", strip=True) if a.parent else ""
            if len(ctx) > 200: ctx = ctx[:200]
            if not TITLE_RE.search(ctx): continue
            try: title_th, full_th, base = normalize_thai_title_and_name(ctx)
            except Exception: continue
            if not base or len(base.split()) < 2: continue
            recs.append({"university_th": t["university_th"], "university_en": t["university_en"],
                         "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
                         "full_name_th": full_th, "academic_title_th": title_th,
                         "email": em, "profile_url": page_url, "source_page": page_url})
    except Exception: pass
    return recs

def dedupe(recs):
    out, seen_exact = [], set()
    for r in recs:
        k = (r["university_th"], r["faculty_th"], (r["full_name_th"] or "").strip())
        if k in seen_exact: continue
        dup = False
        for o in out:
            if o["university_th"] == r["university_th"] and o["faculty_th"] == r["faculty_th"]:
                try:
                    if fuzz.token_set_ratio(o["full_name_th"], r["full_name_th"]) >= 90: dup = True; break
                except Exception: pass
        if dup: continue
        # merge email if existing entry lacks it
        seen_exact.add(k); out.append(r)
    return out

def run():
    keys = load_serp_keys()
    log.info(f"SERP keys available: {len(keys)} (queries capped at {len(TARGETS)})")
    all_recs, failed, per_target_seeds = [], [], {}
    # 1. resolve seeds via SERP (minimal: 1 query/target, first key only)
    for t in TARGETS:
        seeds = list(t["seeds"])
        if keys:
            urls = serp_resolve(t["q"], keys[0])
            for u in urls:
                if u not in seeds: seeds.append(u)
            seeds = seeds[:4]  # cap fetches per target
        per_target_seeds[t["key"]] = seeds
    # 2. headless fetch+parse (threaded)
    jobs = [(t, s) for t in TARGETS for s in per_target_seeds[t["key"]]]
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_url, s): (t, s) for t, s in jobs}
        pages = {}
        for f in as_completed(futs):
            t, s = futs[f]
            try: html, final = f.result()
            except Exception: html, final = "", s
            pages.setdefault(t["key"], []).append((t, s, html, final))
            if not html: log.warning(f"empty: {t['key']} <- {s}")
    for t in TARGETS:
        trecs = []
        for tt, s, html, final in pages.get(t["key"], []):
            trecs.extend(extract_records(html, final or s, t))
        trecs = dedupe(trecs)
        log.info(f"{t['key']}: {len(trecs)} candidates from {len(pages.get(t['key'], []))} pages")
        if not trecs: failed.append(t["key"])
        all_recs.extend(trecs)
    all_recs = dedupe(all_recs)
    # 3. checkpoint (required minimal schema + extras)
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    slim = [{"university_th": r["university_th"], "faculty_th": r["faculty_th"],
             "full_name_th": r["full_name_th"], "email": r.get("email"),
             "profile_url": r.get("profile_url")} for r in all_recs]
    CHECKPOINT.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Checkpoint: {CHECKPOINT} ({len(slim)} records). NO DB commit.")
    # per-faculty breakdown to stdout (concise)
    from collections import Counter
    c = Counter((r["university_th"], r["faculty_th"]) for r in slim)
    for t in TARGETS:
        log.info(f"  {t['key']}: {(t['university_th'], t['faculty_th'])} -> {c.get((t['university_th'], t['faculty_th']), 0)}")
    log.info(f"FAILED: {failed if failed else 'none'}")

if __name__ == "__main__":
    run()
