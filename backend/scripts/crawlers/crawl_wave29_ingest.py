"""Wave29 ingest: CMU social + NIDA econ (dept-guard) + KKU huso (scrubbed)."""
import sys, re, time, random, threading
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz, process

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
def _log(*a): print(*a, flush=True)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles

RE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
JUNK = ["ยินดี", "แสดงความ", "โปรดเกล้า", "องครักษ์", "หมู่",
    "ออกหน่วย", "ข่าว", "ประกาศ", "รับสมัคร", "ติดต่อ", "kingsteruni"]
RE_BADSCRIPT = re.compile(r"[^\u0E00-\u0E7FA-Za-z\s\.\(\)\-]")

EXPECT = {
 "wave29_cmu_social_export.py": ("เชียงใหม่", {}),
 "wave29_nida_econ_export.py": ("บัณฑิตพัฒนบริหารศาสตร์", {"dept_guard": "econ"}),
 "wave29_kku_huso_export.py": ("ขอนแก่น", {"scrub_lists": True}),
}
CANON = {"บัณฑิตพัฒนบริหารศาสตร์": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)"}

def real_person(s):
    s = (s or "").strip()
    if not s or len(s) < 6 or re.search(r'\d{2,}', s): return False
    if RE_BADSCRIPT.search(s): return False
    if any(m in s for m in JUNK): return False
    try: _, _, base = normalize_thai_title_and_name(s)
    except Exception: return False
    if not base or len(base) < 4 or len(base) > 60: return False
    if len(base.split()) < 2: return False
    return bool(re.search(r'[ก-๙]{2,}', base))

def clean_email(e):
    e = (e or "").strip().lower()
    return e if e and RE_EMAIL.match(e) else ""

def load_export(p):
    ns = {}
    try:
        exec(p.read_text(encoding="utf-8"), {}, ns)
        return ns.get("EXTRACTED_FACULTIES", [])
    except Exception as ex:
        _log(f"skip {p.name}: {ex}"); return []

def main():
    d = ROOT / "backend/data/agent_states"
    cands = []
    for fname, (uni_key, opts) in EXPECT.items():
        rows = load_export(d / fname)
        kept, xuni, xname, xdept = 0, 0, 0, 0
        for r in rows:
            u = (r.get("university_th") or "") + (r.get("university") or "")
            if uni_key not in u: xuni += 1; continue
            if not real_person(r.get("full_name_th", "")): xname += 1; continue
            if opts.get("dept_guard") == "econ":
                blob = ((r.get("department_th") or "") + (r.get("department") or "") +
                        (r.get("profile_url") or "") + (r.get("faculty_th") or "")).lower()
                central = (r.get("department_th") or "").strip() in (
                    "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)")
                if central and "econ" not in blob and "เศรษฐ" not in blob:
                    xdept += 1; continue
            if opts.get("scrub_lists"):
                r["research_interests"] = []
                r["featured_publications"] = []
                r["taught_courses"] = []
            for k, canon in CANON.items():
                if k in (r.get("university_th") or ""):
                    r["university_th"] = canon
            r["email"] = clean_email(r.get("email"))
            cands.append(r); kept += 1
        _log(f"{fname}: raw {len(rows)} kept {kept} xuni {xuni} xname {xname} xdept {xdept}")
    _log(f"TOTAL kept pre-dedup: {len(cands)}")
    db = SessionLocal()
    try:
        unis = list({c.get("university_th","") for c in cands if c.get("university_th")})
        existing = db.query(FacultyDB).filter(FacultyDB.university_th.in_(unis)).all() if unis else []
        _log(f"existing in scope {unis}: {len(existing)}")
        ex_by_uni = defaultdict(list)
        for ex in existing: ex_by_uni[ex.university_th or ""].append(ex)
        cache = {}
        def clean_of(ex):
            v = cache.get(ex.id)
            if v is None: v = strip_all_titles(ex.full_name_th or ""); cache[ex.id] = v
            return v
        for lst in ex_by_uni.values():
            for ex in lst: clean_of(ex)
        new_members, seen, enriched = [], set(), 0
        for m in cands:
            fn = (m.get("full_name_th") or "").strip()
            if not fn: continue
            mc = strip_all_titles(fn)
            if mc in seen: continue
            pool = ex_by_uni.get(m.get("university_th") or "", [])
            match = None
            if pool:
                choices = {ex.id: clean_of(ex) for ex in pool}
                hit = process.extractOne(mc, choices, scorer=fuzz.token_set_ratio, score_cutoff=90)
                if hit: match = next((e for e in pool if e.id == hit[2]), None)
            if match:
                ch = False
                if m.get("email") and not (match.email or ""): match.email = m["email"]; ch = True
                if m.get("profile_url") and not (match.profile_url or ""): match.profile_url = m["profile_url"]; ch = True
                if ch: enriched += 1
                continue
            seen.add(mc); new_members.append(m)
        _log(f"enriched {enriched} net new {len(new_members)}")
        raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        if new_members:
            from google import genai
            from google.genai import types
            clients = [genai.Client(api_key=k) for k in api_keys]
            lock = threading.Lock(); box = [0]
            def get_vec(t):
                for a in range(6):
                    with lock: c = clients[box[0] % len(clients)]; box[0] += 1
                    for model in ["gemini-embedding-2", "gemini-embedding-001"]:
                        try:
                            r = c.models.embed_content(model=model, contents=t,
                                config=types.EmbedContentConfig(output_dimensionality=768))
                            v = r.embeddings[0].values
                            if v and len(v) == 768: return v
                        except Exception as e:
                            if "429" in str(e) or "Quota" in str(e): time.sleep(1.0*(a+1))
                    time.sleep(1.2*(a+1))
                raise RuntimeError("embed fail")
            def et(m):
                return (f"อาจารย์และนักวิจัย: {m.get('full_name_th','')} ({m.get('academic_title_th','')})\n"
                        f"สังกัด: {m.get('department_th','')}, {m.get('faculty_th','')}, {m.get('university_th','')}")
            texts = [et(m) for m in new_members]
            vecs = [None]*len(new_members)
            with ThreadPoolExecutor(max_workers=4) as ex:
                fm = {ex.submit(get_vec, t): i for i, t in enumerate(texts)}
                for f in as_completed(fm): vecs[fm[f]] = f.result()
            _log(f" embedded {len(vecs)}/{len(vecs)}")
            have = {r[0] for r in db.query(FacultyDB.id).all()}
            n = 0
            for m, v in zip(new_members, vecs):
                n += 1
                uid = f"wave29_{n:04d}_{random.randint(100,999)}"
                while uid in have:
                    n += 1; uid = f"wave29_{n:04d}_{random.randint(100,999)}"
                have.add(uid)
                db.add(FacultyDB(id=uid, university=m.get("university") or "", university_th=m.get("university_th") or "",
                    faculty=m.get("faculty") or "", faculty_th=m.get("faculty_th") or "",
                    department=m.get("department") or "", department_th=m.get("department_th") or "",
                    academic_title_th=m.get("academic_title_th") or "", full_name_th=m.get("full_name_th") or "",
                    first_name=m.get("first_name") or "", last_name=m.get("last_name") or "",
                    email=m.get("email") or "", image_url=m.get("image_url") or "",
                    profile_url=m.get("profile_url") or "", role=m.get("role") or "",
                    research_interests=(m.get("research_interests") or []),
                    featured_publications=(m.get("featured_publications") or []),
                    education=(m.get("education") or []), taught_courses=(m.get("taught_courses") or []),
                    embedding=v))
            db.commit()
        else: db.commit()
        _log(f"GRAND TOTAL {db.query(FacultyDB).count()} null {db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()}")
    finally: db.close()

if __name__ == "__main__": main()
