"""List grad PROGRAMS whose faculty group has fewer advisors than grad courses."""
import sys, re
from pathlib import Path
from collections import defaultdict
from rapidfuzz import fuzz, process

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
def _log(*a): print(*a, flush=True)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB
from sqlalchemy import func

GRAD = ["ปริญญาโท", "ปริญญาเอก"]
def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())

db = SessionLocal()
try:
    adv = {}
    for u, f, c in db.query(FacultyDB.university_th, FacultyDB.faculty_th, func.count()).group_by(
            FacultyDB.university_th, FacultyDB.faculty_th).all():
        adv[(norm(u), norm(f))] = c
    grad_courses = db.query(CourseDB).filter(CourseDB.degree_level.in_(GRAD)).all()
    grad_by_key = defaultdict(list)
    for c in grad_courses:
        grad_by_key[(norm(c.university_th), norm(c.faculty_th))].append(c)
    adv_by_uni = defaultdict(list)
    for (u, f) in adv: adv_by_uni[u].append(f)
    # map grad key -> adv key
    cover_grad = defaultdict(int)
    keymap = {}
    for (gu, gf) in grad_by_key:
        if not gf: continue
        if (gu, gf) in adv:
            keymap[(gu, gf)] = (gu, gf); cover_grad[(gu, gf)] += len(grad_by_key[(gu, gf)])
        else:
            cands = adv_by_uni.get(gu, [])
            hit = process.extractOne(gf, cands, scorer=fuzz.token_set_ratio, score_cutoff=80) if cands else None
            if hit:
                keymap[(gu, gf)] = (gu, hit[0]); cover_grad[(gu, hit[0])] += len(grad_by_key[(gu, gf)])
    _log("=== grad PROGRAMS in groups where advisors < grad courses ===")
    total = 0
    for ak, g in sorted(cover_grad.items(), key=lambda kv: adv.get(kv[0], 0) - kv[1]):
        a = adv.get(ak, 0)
        if a >= g: continue
        _log(f"\n[{a} adv vs {g} courses] {ak[0]} :: {ak[1]}")
        for gk, lst in grad_by_key.items():
            if keymap.get(gk) == ak:
                for c in sorted(lst, key=lambda x: x.degree_level or ""):
                    t = (c.title_th or c.title_en or "?")[:70]
                    _log(f"    [{c.degree_level}] {t}")
                    total += 1
    _log(f"\nTOTAL shortage programs listed: {total}")
finally:
    db.close()
