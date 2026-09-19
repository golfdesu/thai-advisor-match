"""Depth check: advisors vs grad-course volume per group."""
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
    # map each grad group -> advisor group (exact then fuzzy)
    cover = {}  # adv_key -> grad count
    for (gu, gf), gc in grad.items():
        if (gu, gf) in adv:
            cover[(gu, gf)] = cover.get((gu, gf), 0) + gc
        else:
            cands = adv_by_uni.get(gu, [])
            hit = process.extractOne(gf, cands, scorer=fuzz.token_set_ratio, score_cutoff=80) if cands else None
            if hit: cover[(gu, hit[0])] = cover.get((gu, hit[0]), 0) + gc
    # shortage: grad courses > advisors
    short = [(g - adv[k], adv[k], g, k) for k, g in cover.items() if g > adv[k]]
    short.sort(reverse=True)
    _log(f"covered groups: {len(cover)} | SHORTAGE groups (grad>adv): {len(short)}")
    _log(f"advisors in shortage groups: {sum(a for _, a, _, _ in short)}")
    _log("=== top 25 shortage (need>have) ===")
    for need, a, g, (u, f) in short[:25]:
        _log(f"  short={need:3d} adv={a:3d} grad={g:3d} | {u} :: {f}")
    # depth buckets for covered groups
    import math
    buckets = defaultdict(lambda: [0, 0])  # ratio bucket -> [groups, advisors]
    for k, g in cover.items():
        a = adv[k]
        r = a / g if g else 0
        b = "adv<grad" if r < 1 else ("1-3 adv/grad" if r < 3 else ("3-10" if r < 10 else "10+"))
        buckets[b][0] += 1; buckets[b][1] += a
    _log("=== depth buckets (covered groups) ===")
    for b in ["adv<grad", "1-3 adv/grad", "3-10", "10+"]:
        _log(f"  {b}: groups={buckets[b][0]} advisors={buckets[b][1]}")
finally:
    db.close()
