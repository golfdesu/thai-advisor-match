"""One-shot hygiene repair for wave21-32 rows to meet audited contracts.
Idempotent, whole-DB: only transforms violating values, never invents content.
1. university := TH_TO_EN_CANONICAL[university_th] where mismatched
2. "" -> None for nullable string columns (contract: NULL, never "")
3. str pubs -> {"title": s} (api shape)
4. freemail-domain + pinned shared-inbox emails -> None
5. case-insensitive dedupe of research_interests within row
"""
import sys, re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
def _log(*a): print(*a, flush=True)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

FREEMAIL = ("@gmail.com", "@yahoo.", "@hotmail.", "@outlook.", "@live.", "@icloud.")
VALID_SUFFIXES = (".ac.th", ".edu", ".or.th", ".go.th", "ku.th", ".ac.kr", ".dk",
    "tggs-bangkok.org", "chulavrc.org", "cern.ch", "chula.md")
SHARED = ["fish@ku.ac.th", "allied@allied.tu.ac.th", "fac-en@silpakorn.edu", "agro@psu.ac.th",
    "engineering@kku.ac.th", "chemy@ku.ac.th", "math@cmu.ac.th", "attm@med.tu.ac.th",
    "biology@cmu.ac.th", "intmed@cmu.ac.th", "ams@cmu.ac.th", "dsc@cmu.ac.th",
    "cpe@ku.ac.th", "chemistry@kmutt.ac.th", "stat@sci.kmutnb.ac.th", "ie@eng.chula.ac.th"]
NULLABLE_STR = ["department", "department_th", "role", "first_name", "last_name",
    "email", "profile_url", "image_url", "scholar_url"]

def bad_email(e):
    e = (e or "").lower().strip()
    if not e or "@" not in e:
        return False
    if e in SHARED:
        return True
    dom = e.split("@")[-1]
    return not any(dom == s or dom.endswith(s) for s in VALID_SUFFIXES)

db = SessionLocal()
try:
    stats = {"uni": 0, "null": 0, "pubs": 0, "email": 0, "dupint": 0}
    q = db.query(FacultyDB).yield_per(500)
    n = 0
    for f in q:
        n += 1
        dirty = False
        canon = TH_TO_EN_CANONICAL.get(f.university_th or "")
        if canon and f.university != canon:
            f.university = canon; stats["uni"] += 1; dirty = True
        for col in NULLABLE_STR:
            if getattr(f, col) == "":
                setattr(f, col, None); stats["null"] += 1; dirty = True
        pubs = f.featured_publications or []
        fixed, converted = [], False
        for p in pubs:
            if isinstance(p, str):
                t = p.strip()
                if t: fixed.append({"title": t[:500]})
                converted = True
            elif isinstance(p, dict) and p.get("title"):
                pruned = {k: v for k, v in p.items()
                          if k in {"title", "year", "venue", "url", "citation_count"}}
                if set(p) - set(pruned):
                    converted = True
                fixed.append(pruned)
            else:
                converted = True
        if converted:
            f.featured_publications = fixed
            stats["pubs"] += 1; dirty = True
        for col in ("profile_url", "image_url"):
            v = getattr(f, col)
            if v and " " in v:
                from urllib.parse import quote
                setattr(f, col, quote(v, safe="/:#?&=%@"))
                dirty = True
        if f.email and bad_email(f.email):
            f.email = None; stats["email"] += 1; dirty = True
        seen, dedup, changed = set(), [], False
        for item in (f.research_interests or []):
            k = str(item).strip().lower()
            if k in seen and k:
                changed = True; continue
            seen.add(k); dedup.append(item)
        if changed:
            f.research_interests = dedup; stats["dupint"] += 1; dirty = True
        if dirty and n % 2000 == 0:
            db.flush()
    db.commit()
    _log(f"scanned {n} | uni-fixed {stats['uni']} | ''->None {stats['null']} | pubs {stats['pubs']} | emails-nulled {stats['email']} | dedup-int {stats['dupint']}")
finally:
    db.close()
