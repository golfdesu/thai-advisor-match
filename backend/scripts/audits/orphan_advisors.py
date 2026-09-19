"""Inverse mismatch: advisor groups with ZERO grad courses mapped."""
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
    grad_keys = set()
    for u, f, _ in db.query(CourseDB.university_th, CourseDB.faculty_th, func.count()).filter(
            CourseDB.degree_level.in_(GRAD)).group_by(
            CourseDB.university_th, CourseDB.faculty_th).all():
        grad_keys.add((norm(u), norm(f)))
    adv_by_uni = defaultdict(list)
    for (u, f) in adv: adv_by_uni[u].append(f)
    # fuzzy map grad->adv (same as reconcile)
    grad_covered_adv = set()
    for (gu, gf) in grad_keys:
        if not gf: continue
        if (gu, gf) in adv:
            grad_covered_adv.add((gu, gf)); continue
        cands = adv_by_uni.get(gu, [])
        hit = process.extractOne(gf, cands, scorer=fuzz.token_set_ratio, score_cutoff=80) if cands else None
        if hit: grad_covered_adv.add((gu, hit[0]))
    orphans = sorted(((a, u, f) for (u, f), a in adv.items() if (u, f) not in grad_covered_adv),
                     reverse=True)
    _log(f"advisor groups total {len(adv)} | with grad {len(grad_covered_adv)} | WITHOUT grad {len(orphans)}")
    _log(f"advisors sitting in no-grad groups: {sum(a for a, _, _ in orphans)}")
    _log("=== top 40 no-grad advisor groups ===")
    for a, u, f in orphans[:40]:
        _log(f"  adv={a:4d} | {u} :: {f}")
finally:
    db.close()
