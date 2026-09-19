"""Wave22 ingest: quarantine + university-enforced merge + sanitize + vectorize + local commit."""
import sys, re, time, random, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz, process
import sys as _sys
def _log(*a):
    print(*a, flush=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name
from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles

RE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
JUNK = ["ยินดี", "แสดงความ", "โปรดเกล้า", "องครักษ์", "หมู่", "ต.แม่", "อ.เมือง",
    "ออกหน่วย", "ทันตกรรม", "ทันกรรม", "พระราชทาน", "สัมภาษณ์", "ศิษย์เก่า",
    "ข่าว", "ประกาศ", "รับสมัคร", "ติดต่อ", "สถานที่", "สายด่วน", "facebook",
    "bangkokpost", "mgronline", "naewna", "siamrath"]

# file -> expected university substring (None = skip file entirely)
EXPECT = {
 "wave22_cmu_pharmacy_export.py": "เชียงใหม่",
 "wave22_cmu_agro_export.py": "เชียงใหม่",
 "wave22_up_med_export.py": "พะเยา",
 "wave22_nu_dent_export.py": "นเรศวร",
 "wave22_nu_ahs_export.py": "นเรศวร",
 "wave22_nu_medsci_export.py": "นเรศวร",
 "wave22_nu_sgtech_export.py": "นเรศวร",
 "wave22_kku_dent_export.py": "ขอนแก่น",
 "wave22_kku_medtech_export.py": "ขอนแก่น",
 "wave22_psu_pharmacy_export.py": "สงขลานครินทร์",
 "wave22_sut_med_export.py": "สุรนารี",
 "wave22_sut_nursing_export.py": "สุรนารี",
 "wave22_mu_vet_export.py": "มหิดล",
 "wave22_mu_medtech_export.py": "มหิดล",
 "wave22_tu_journalism_export.py": "ธรรมศาสตร์",
 "wave22_tu_liberalarts_export.py": "ธรรมศาสตร์",
 "wave22_cu_finearts_export.py": "จุฬาลงกรณ์",
 "wave22_su_arts_export.py": "ศิลปากร",
 "wave22_su_ict_export.py": "ศิลปากร",
 "wave22_su_pharmacy_export.py": "ศิลปากร",
 "wave22_swu_pharmacy_export.py": "ศรีนครินทรวิโรฒ",
 "wave22_buu_allied_export.py": "บูรพา",
 "wave22_buu_edu_export.py": "บูรพา",
 "wave22_buu_logistics_export.py": "บูรพา",
 "wave22_ru_law_export.py": "รามคำแหง",
 "wave22_tsu_sci_export.py": "ทักษิณ",
 "wave22_ubu_edu_export.py": "อุบล",
 "wave22_msu_sci_export.py": "มหาสารคาม",
 "wave22_mju_sci_export.py": "แม่โจ้",
 "wave22_mju_vet_export.py": "แม่โจ้",
 "wave22_mfu_med_export.py": "แม่ฟ้าหลวง",
 "wave22_mfu_healthsci_export.py": "แม่ฟ้าหลวง",
 "wave22_kmitl_bus_export.py": "ลาดกระบัง",
 "wave22_kmitl_agritech_export.py": "ลาดกระบัง",
 "wave22_kmutt_biores_export.py": "ธนบุรี",
}
# quarantined / structural-zero files are simply absent from EXPECT

def real_person(s):
    s = (s or "").strip()
    if not s or len(s) < 6 or re.search(r'\d{2,}', s): return False
    if any(m in s for m in JUNK): return False
    try:
        _, _, base = normalize_thai_title_and_name(s)
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
        print(f"skip {p.name}: {ex}"); return []

def main():
    d = ROOT / "backend/data/agent_states"
    cands, stats = [], {}
    for fname, uni_key in EXPECT.items():
        p = d / fname
        if not p.exists():
            _log(f"missing {fname}"); continue
        rows = load_export(p)
        kept, drop_uni, drop_name = 0, 0, 0
        for r in rows:
            u = (r.get("university_th") or "") + (r.get("university") or "")
            if uni_key not in u:
                drop_uni += 1; continue
            if not real_person(r.get("full_name_th", "")):
                drop_name += 1; continue
            r["email"] = clean_email(r.get("email"))
            cands.append(r); kept += 1
        stats[fname] = (len(rows), kept, drop_uni, drop_name)
        _log(f"{fname}: raw {len(rows)} kept {kept} xuni {drop_uni} xname {drop_name}")
    _log(f"TOTAL kept pre-dedup: {len(cands)}")
    db = SessionLocal()
    try:
        unis = list({c.get("university_th","") for c in cands if c.get("university_th")})
        existing = db.query(FacultyDB).filter(FacultyDB.university_th.in_(unis)).all()
        _log(f"existing in scope {len(unis)}: {len(existing)}")
        # group existing by university for O(n*m/nu) instead of O(N*M)
        from collections import defaultdict
        ex_by_uni = defaultdict(list)
        for ex in existing:
            ex_by_uni[ex.university_th or ""].append(ex)
        clean_cache = {}
        def clean_of(ex):
            k = ex.id
            v = clean_cache.get(k)
            if v is None:
                v = strip_all_titles(ex.full_name_th or "")
                clean_cache[k] = v
            return v
        for uni, lst in ex_by_uni.items():
            for ex in lst: clean_of(ex)
            _log(f"  indexed {uni}: {len(lst)}")
        new_members, seen, enriched = [], set(), 0
        for idx, m in enumerate(cands):
            if idx % 200 == 0: _log(f"  dedup {idx}/{len(cands)} new={len(new_members)} enr={enriched}")
            fn = (m.get("full_name_th") or "").strip()
            if not fn: continue
            mc = strip_all_titles(fn)
            if mc in seen: continue
            pool = ex_by_uni.get(m.get("university_th") or "", [])
            match = None
            if pool:
                choices = {ex.id: clean_of(ex) for ex in pool}
                hit = process.extractOne(mc, choices, scorer=fuzz.token_set_ratio, score_cutoff=90)
                if hit:
                    mid = hit[2]
                    match = next((e for e in pool if e.id == mid), None)
            if match:
                ch = False
                if m.get("email") and not (match.email or ""):
                    match.email = m["email"]; ch = True
                if m.get("profile_url") and not (match.profile_url or ""):
                    match.profile_url = m["profile_url"]; ch = True
                if ch: enriched += 1
                continue
            seen.add(mc); new_members.append(m)
        _log(f"enriched {enriched} net new {len(new_members)}")
        raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        if new_members and not api_keys: raise ValueError("no gemini keys")
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
                done = 0
                for f in as_completed(fm):
                    vecs[fm[f]] = f.result(); done += 1
                    if done % 50 == 0: _log(f" embedded {done}/{len(vecs)}")
            have = {r[0] for r in db.query(FacultyDB.id).all()}
            n = 0
            for m, v in zip(new_members, vecs):
                n += 1
                uid = f"wave22_{n:04d}_{random.randint(100,999)}"
                while uid in have:
                    n += 1; uid = f"wave22_{n:04d}_{random.randint(100,999)}"
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
