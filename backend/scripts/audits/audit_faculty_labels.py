"""Audit near-duplicate faculty_th labels within each university (no writes)."""
import sys, re
from pathlib import Path
from collections import defaultdict
from itertools import combinations
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
def _log(*a): print(*a, flush=True)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy import func

CAMPUS_MARKERS = ["ศรีราชา", "กำแพงแสน", "สกลนคร", "บางเขน", "ภูเก็ต", "ปัตตานี",
                  "ขอนแก่น", "วิทยาเขต", "สมุทรปราการ", "ชุมพร", "ระยอง", "ตรัง"]

db = SessionLocal()
try:
    rows = db.query(FacultyDB.university_th, FacultyDB.faculty_th, func.count()).group_by(
        FacultyDB.university_th, FacultyDB.faculty_th).all()
    by_uni = defaultdict(list)
    for u, f, c in rows:
        by_uni[u or "?"].append((f or "?", c))
    _log(f"universities: {len(by_uni)}")
    for u in sorted(by_uni):
        facs = by_uni[u]
        if len(facs) < 2: continue
        pairs = []
        for (f1, c1), (f2, c2) in combinations(sorted(facs), 2):
            s = fuzz.token_set_ratio(f1, f2)
            if s >= 80:
                camp = any(m in f1 or m in f2 for m in CAMPUS_MARKERS)
                pairs.append((s, f1, c1, f2, c2, camp))
        if pairs:
            _log(f"\n== {u} ({len(facs)} labels) ==")
            for s, f1, c1, f2, c2, camp in sorted(pairs, reverse=True):
                flag = "CAMPUS-KEEP" if camp else "merge?"
                _log(f"  [{s}] ({c1}) {f1}  <>  ({c2}) {f2}  -> {flag}")
finally:
    db.close()
