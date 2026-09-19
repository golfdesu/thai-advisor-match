"""Reconcile courses(faculty_th) vs faculties(faculty_th) for grad-backed priority."""
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
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

db = SessionLocal()
try:
    # advisor counts per (uni, fac)
    adv = defaultdict(int)
    for u, f, c in db.query(FacultyDB.university_th, FacultyDB.faculty_th, func.count()).group_by(FacultyDB.university_th, FacultyDB.faculty_th).all():
        adv[(norm(u), norm(f))] = c
    # grad course counts per (uni, fac)
    grad = defaultdict(int)
    grad_rows = db.query(CourseDB.university_th, CourseDB.faculty_th, func.count()).filter(
        CourseDB.degree_level.in_(GRAD)).group_by(CourseDB.university_th, CourseDB.faculty_th).all()
    for u, f, c in grad_rows:
        grad[(norm(u), norm(f))] += c
    _log(f"advisor groups: {len(adv)} | grad groups: {len(grad)}")
    # exact matches
    exact = {k: v for k, v in grad.items() if k in adv}
    _log(f"exact uni+fac match: {len(exact)}/{len(grad)}")
    # empty faculty in courses
    empty = sum(c for (u, f), c in grad.items() if not f)
    _log(f"grad courses with EMPTY faculty_th: {empty}")
    # fuzzy pass for leftovers within same university
    adv_by_uni = defaultdict(list)
    for (u, f) in adv: adv_by_uni[u].append(f)
    mapped, unmapped = {}, []
    for (u, f), c in grad.items():
        if not f or (u, f) in adv: continue
        cands = adv_by_uni.get(u, [])
        hit = process.extractOne(f, cands, scorer=fuzz.token_set_ratio, score_cutoff=80) if cands else None
        if hit: mapped[(u, f)] = (hit[0], hit[1])
        else: unmapped.append((u, f, c))
    _log(f"fuzzy mapped: {len(mapped)} | unmapped: {len(unmapped)}")
    for u, f, c in sorted(unmapped, key=lambda x: -x[2])[:30]:
        _log(f"  UNMAPPED grad={c} | {u} :: {f}")
    # priority: grad>0 sorted by advisors asc (merge fuzzy into canonical)
    prio = defaultdict(lambda: [0, set()])
    for (u, f), c in grad.items():
        if not f: continue
        key = (u, f)
        if key in adv:
            prio[key][0] += c
        elif key in mapped:
            ck = (u, mapped[key][0])
            prio[ck][0] += c
            prio[ck][1].add(f)
    _log("\n=== PRIORITY: grad programs with thinnest advisors (top 40) ===")
    rows = sorted(prio.items(), key=lambda kv: adv.get(kv[0], 0))
    for (u, f), (g, aliases) in rows[:40]:
        a = adv.get((u, f), 0)
        al = f" aliases={sorted(aliases)}" if aliases else ""
        _log(f"  adv={a:4d} grad={g:3d} | {u} :: {f}{al}")
    _log("\n=== grad-backed groups already healthy (adv>=30, top 15 by grad) ===")
    healthy = sorted([kv for kv in prio.items() if adv.get(kv[0], 0) >= 30],
                     key=lambda kv: -kv[1][0])[:15]
    for (u, f), (g, _) in healthy:
        _log(f"  adv={adv[(u,f)]:4d} grad={g:3d} | {u} :: {f}")
finally:
    db.close()
