# -*- coding: utf-8 -*-
"""Elite-researcher coverage audit: which fields lack strong advisors with good research output."""
import sys, io, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import psycopg2, re
from collections import defaultdict

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
cur = conn.cursor()
cur.execute("""SELECT id, university_th, faculty_th, department_th, research_interests::text,
               h_index, total_citations, total_publications_count
               FROM faculties""")
rows = cur.fetchall()

# Reuse the 57-field taxonomy from the coverage audit and safe title stripping
from pathlib import Path
audit_dir = Path(__file__).resolve().parent
backend_dir = Path(__file__).resolve().parents[2]
if str(audit_dir) not in sys.path:
    sys.path.insert(0, str(audit_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from field_taxonomy import FIELDS, compiled  # noqa
from app.models.schema import _strip_leading_title_tokens

def score(h, cit, pub):
    """Research strength score (lightweight proxy for 'เก่ง')."""
    return (h or 0) * 3 + min(cit or 0, 5000) / 100 + min(pub or 0, 200) * 0.5

def tier(h):
    if h is None or h <= 0: return 'no_data'
    if h >= 40: return 'elite_h40'
    if h >= 20: return 'strong_h20'
    if h >= 10: return 'mid_h10'
    return 'early'

field_people = defaultdict(list)
for fid, uni, fac, dep, ri, h, cit, pub in rows:
    try:
        interests = json.loads(ri) if ri else []
    except Exception:
        interests = []
    text = " || ".join([str(x) for x in interests] + [str(fac or ''), str(dep or '')])
    for field, pats in compiled.items():
        if any(p.search(text) for p in pats):
            field_people[field].append({
                'id': fid, 'uni': uni, 'name': None, 'h': h or 0, 'cit': cit or 0,
                'pub': pub or 0, 'score': score(h, cit, pub), 'tier': tier(h)})
            break  # first-match wins (same as coverage audit)

# need names for top lists — full_name_th often embeds the rank; strip it, then
# re-prefix the canonical academic_title_th (mirrors schema.py _clean_display_name)
name_map = {}
cur.execute("SELECT id, full_name_th, academic_title_th FROM faculties")
for i, n, t in cur.fetchall():
    bare = _strip_leading_title_tokens(n or "", max_strips=3)
    name_map[i] = f"{t or ''} {bare}".strip()

print(f"{'สาขา':<38}{'คน':>6}{'มีh':>6}{'h>=20':>7}{'h>=40':>7}{'top h':>7}")
print("-" * 74)
for f in sorted(field_people, key=lambda f: len(field_people[f])):
    ppl = field_people[f]
    n = len(ppl)
    nh = sum(1 for p in ppl if p['h'] > 0)
    n20 = sum(1 for p in ppl if p['h'] >= 20)
    n40 = sum(1 for p in ppl if p['h'] >= 40)
    mx = max((p['h'] for p in ppl), default=0)
    print(f"{f:<38}{n:>6}{nh:>6}{n20:>7}{n40:>7}{mx:>7}")

print("\n===== 🏆 Top 5 'อาจารย์เก่ง' ต่อสาขาที่ขาดแคลน =====")
weak_fields = [f for f in field_people if len(field_people[f]) < 110]
for f in sorted(weak_fields, key=lambda f: len(field_people[f])):
    ppl = sorted(field_people[f], key=lambda p: -p['score'])[:5]
    print(f"\n  ▸ {f} ({len(field_people[f])} คนใน DB)")
    for p in ppl:
        print(f"     - {name_map.get(p['id'],'?')[:40]:<42} h={p['h']:<4} cit={p['cit']:<7,} {p['uni']}")

print("\n===== 🚨 สาขาที่ไม่มีอาจารย์ h>=20 เลย =====")
for f in sorted(field_people, key=lambda f: len(field_people[f])):
    ppl = field_people[f]
    if not any(p['h'] >= 20 for p in ppl):
        best = max((p['h'] for p in ppl), default=0)
        print(f"  {f:<42} {len(ppl):>3} คน | h สูงสุดแค่ {best}")

cur.close(); conn.close()
