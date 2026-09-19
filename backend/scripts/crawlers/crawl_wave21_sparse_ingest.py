"""Wave21 sparse-faculty ingest: SPA exports (CU/MU/CMU) + sanitized regional sparse.
SOP: checkpoint already on disk -> RapidFuzz dedup vs local -> 768-dim vectorize -> local commit.
Invariant 9: regional news/address crumbs are REJECTED, never ingested as person names.
"""
import sys, re, json, time, random, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from scripts.agentic_pipeline.state_reducer import normalize_thai_title_and_name

RE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
RE_PHONE = re.compile(r'(โทร\.?|Tel\.?|Phone|0\d[\d\-\s\.]{6,})', re.I)
JUNK_MARKERS = ["ยินดี", "แสดงความ", "โปรดเกล้า", "ศาสตราจารย์ ได้รับ", "องครักษ์", "นครนายก",
    "หมู่", "ต.แม่", "อ.เมือง", "จ.พะเยา", "56000", "26120", "ออกหน่วย", "ทันตกรรม", "ทันกรรม",
    "พระราชทาน", "สัมภาษณ์", "ศิษย์เก่า", "EP ", "ข่าว", "ประกาศ", "รับสมัคร", "19/1",
    "ติดต่อ", "สถานที่", "ภาควิชา", "คณะ", "มหาวิทยาลัย", "สายด่วน", "โทรศัพท์"]

def is_real_person(th_name: str) -> bool:
    s = (th_name or "").strip()
    if not s or len(s) < 6:
        return False
    if any(m in s for m in JUNK_MARKERS):
        return False
    if re.search(r'\d{2,}', s):
        return False
    try:
        _, _, base = normalize_thai_title_and_name(s)
    except Exception:
        return False
    if not base or len(base) < 4:
        return False
    parts = base.split()
    if len(parts) < 2:
        return False
    if not re.search(r'[ก-๙]{2,}', base):
        return False
    if len(base) > 60:
        return False
    return True

def clean_email(e):
    e = (e or "").strip().lower()
    if not e or not RE_EMAIL.match(e):
        return ""
    return e

def load_spa(path: Path):
    try:
        ns = {}
        exec(path.read_text(encoding="utf-8"), {}, ns)
        return ns.get("EXTRACTED_FACULTIES", [])
    except Exception as ex:
        print(f"  skip {path.name}: {ex}")
        return []

def main():
    spa_files = [
        ROOT / "data/agent_states/spa_cu_commarts_export.py",
        ROOT / "data/agent_states/spa_cu_arts_export.py",
        ROOT / "data/agent_states/spa_cmu_agro_export.py",
        ROOT / "data/agent_states/spa_mu_vet_export.py",
    ]
    cands = []
    for p in spa_files:
        if p.exists():
            rows = load_spa(p)
            print(f"{p.name}: {len(rows)} raw")
            cands.extend(rows)
    reg_path = ROOT / "backend/data/agent_states/wave21_regional_sparse_extracted.json"
    reg_raw = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else []
    print(f"regional raw: {len(reg_raw)}")
    reg_ok, reg_rej = [], 0
    for r in reg_raw:
        if is_real_person(r.get("full_name_th", "")):
            reg_ok.append(r)
        else:
            reg_rej += 1
    print(f"regional kept: {len(reg_ok)} rejected crumbs: {reg_rej}")
    # normalize regional dicts to faculty schema (no fake names/emails)
    for r in reg_ok:
        try:
            th_title, th_name, base = normalize_thai_title_and_name(r.get("full_name_th", ""))
        except Exception:
            continue
        cands.append({
            "university_th": r.get("university_th", ""), "university": "",
            "faculty_th": r.get("faculty_th", ""), "faculty": "",
            "department_th": "", "department": "",
            "academic_title_th": th_title, "full_name_th": th_name,
            "first_name": base.split(" ")[0] if " " in base else base,
            "last_name": " ".join(base.split(" ")[1:]) if " " in base else "",
            "email": clean_email(r.get("email")), "image_url": "",
            "profile_url": r.get("profile_url", ""), "role": th_title,
            "research_interests": [], "featured_publications": [],
            "education": [], "taught_courses": [],
        })
    print(f"total candidates pre-dedup: {len(cands)}")

    db = SessionLocal()
    try:
        unis = list({c.get("university_th", "") for c in cands if c.get("university_th")})
        existing = db.query(FacultyDB).filter(FacultyDB.university_th.in_(unis)).all()
        print(f"existing in scope {len(unis)} unis: {len(existing)}")
        from scripts.crawlers.crawl_wave19_cu_gaps import strip_all_titles
        new_members, seen = [], set()
        enriched = 0
        for m in cands:
            fn = (m.get("full_name_th") or "").strip()
            if not fn:
                continue
            mc = strip_all_titles(fn)
            if mc in seen:
                continue
            best, match = 0, None
            for ex in existing:
                s = fuzz.token_set_ratio(mc, strip_all_titles(ex.full_name_th or ""))
                if s >= 90 and s > best:
                    best, match = s, ex
            if match:
                ch = False
                em = clean_email(m.get("email", ""))
                if em and not (match.email or ""):
                    match.email = em; ch = True
                if m.get("profile_url") and not (match.profile_url or ""):
                    match.profile_url = m["profile_url"]; ch = True
                if ch:
                    enriched += 1
                continue
            seen.add(mc)
            new_members.append(m)
        print(f"enriched: {enriched} | net new: {len(new_members)}")
        # vectorize + insert
        raw_keys = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        if new_members and not api_keys:
            raise ValueError("No Gemini keys")
        def emb_text(m):
            return (f"อาจารย์และนักวิจัย: {m.get('full_name_th','')} ({m.get('academic_title_th','')})\n"
                    f"สังกัด: {m.get('department_th','')}, {m.get('faculty_th','')}, {m.get('university_th','')}")
        if new_members:
            from google import genai
            from google.genai import types
            clients = [genai.Client(api_key=k) for k in api_keys]
            lock = threading.Lock(); box = [0]
            def get_vec(t):
                for a in range(6):
                    with lock:
                        c = clients[box[0] % len(clients)]; box[0] += 1
                    for model in ["gemini-embedding-2", "gemini-embedding-001"]:
                        try:
                            r = c.models.embed_content(model=model, contents=t,
                                config=types.EmbedContentConfig(output_dimensionality=768))
                            v = r.embeddings[0].values
                            if v and len(v) == 768:
                                return v
                        except Exception as e:
                            if "429" in str(e) or "Quota" in str(e):
                                time.sleep(1.0*(a+1))
                    time.sleep(1.2*(a+1))
                raise RuntimeError("embed fail")
            texts = [emb_text(m) for m in new_members]
            vecs = [None]*len(new_members)
            with ThreadPoolExecutor(max_workers=4) as ex:
                fm = {ex.submit(get_vec, t): i for i, t in enumerate(texts)}
                done = 0
                for f in as_completed(fm):
                    vecs[fm[f]] = f.result(); done += 1
                    if done % 50 == 0:
                        print(f"  embedded {done}/{len(vecs)}")
            # unique ids
            have = {r[0] for r in db.query(FacultyDB.id).all()}
            n = 0
            for m, v in zip(new_members, vecs):
                n += 1
                base = re.sub(r'[^a-z0-9]+', '', (m.get("university_th") or "uni")[:2].lower()) or "wave21"
                uid = f"wave21_{n:04d}_{random.randint(100,999)}"
                while uid in have:
                    n += 1; uid = f"wave21_{n:04d}_{random.randint(100,999)}"
                have.add(uid)
                db.add(FacultyDB(id=uid, university=m.get("university") or "", university_th=m.get("university_th") or "",
                    faculty=m.get("faculty") or "", faculty_th=m.get("faculty_th") or "",
                    department=m.get("department") or "", department_th=m.get("department_th") or "",
                    academic_title_th=m.get("academic_title_th") or "", full_name_th=m.get("full_name_th") or "",
                    first_name=m.get("first_name") or "", last_name=m.get("last_name") or "",
                    email=clean_email(m.get("email")), image_url=m.get("image_url") or "",
                    profile_url=m.get("profile_url") or "", role=m.get("role") or "",
                    research_interests=(m.get("research_interests") or []),
                    featured_publications=(m.get("featured_publications") or []),
                    education=(m.get("education") or []), taught_courses=(m.get("taught_courses") or []),
                    embedding=v))
            db.commit()
        else:
            db.commit()
        total = db.query(FacultyDB).count()
        nulls = db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()
        print(f"GRAND TOTAL: {total} null_emb: {nulls}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
