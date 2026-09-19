"""Loose-match unmapped grad groups vs orphan advisor groups (review list)."""
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
    grad = defaultdict(int)
    for u, f, c in db.query(CourseDB.university_th, CourseDB.faculty_th, func.count()).filter(
            CourseDB.degree_level.in_(GRAD)).group_by(
            CourseDB.university_th, CourseDB.faculty_th).all():
        if norm(f): grad[(norm(u), norm(f))] += c
    adv_by_uni = defaultdict(list)
    for (u, f) in adv: adv_by_uni[u].append(f)
    # strict-mapped advisor keys (>=80, as used)
    strict_covered = set()
    for (gu, gf) in grad:
        if (gu, gf) in adv:
            strict_covered.add((gu, gf)); continue
        hit = process.extractOne(gf, adv_by_uni.get(gu, []),
                                 scorer=fuzz.token_set_ratio, score_cutoff=80)
        if hit: strict_covered.add((gu, hit[0]))
    orphans = sorted([(a, u, f) for (u, f), a in adv.items() if (u, f) not in strict_covered],
                     reverse=True)
    _log(f"orphan groups: {len(orphans)}")
    # loose pass 55-79: possible missed aliases
    for a, u, f in orphans[:25]:
        cands = adv_by_uni.get(u, [])
        gnames = [gf for (gu, gf) in grad if gu == u]
        best = process.extractOne(f, gnames, scorer=fuzz.token_set_ratio,
                                  score_cutoff=55) if gnames else None
        if best and best[1] < 80:
            gc = grad[(u, best[0])]
            _log(f"  MAYBE-MISSED adv={a} [{f}]  ~ grad={gc} [{best[0]}] score={best[1]:.0f}")
        elif not best:
            _log(f"  NO-GRAD-AT-ALL adv={a} [{u} :: {f}]")
        else:
            _log(f"  covered-strict adv={a} [{f}] (unexpected)")
finally:
    db.close()
