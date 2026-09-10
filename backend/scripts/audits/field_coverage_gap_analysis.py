# -*- coding: utf-8 -*-
"""Field coverage gap analysis: analyzes researcher density across 57 academic disciplines."""
import sys, io, json
from pathlib import Path
from collections import defaultdict
import psycopg2, re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

audit_dir = Path(__file__).resolve().parent
if str(audit_dir) not in sys.path:
    sys.path.insert(0, str(audit_dir))

from field_taxonomy import FIELDS, compiled

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
cur = conn.cursor()
cur.execute("SELECT id, university_th, faculty_th, department_th, research_interests::text FROM faculties")
rows = cur.fetchall()

field_advisors = defaultdict(set)
field_unis = defaultdict(set)
zero_text = 0
unmatched_ids = []

for fid, uni, fac, dep, ri in rows:
    try:
        interests = json.loads(ri) if ri else []
    except Exception:
        interests = []
    text = " || ".join([str(x) for x in interests] + [str(fac or ''), str(dep or '')])
    if not text.strip():
        zero_text += 1
        continue
    hit = False
    for field, pats in compiled.items():
        if any(p.search(text) for p in pats):
            field_advisors[field].add(fid)
            field_unis[field].add(uni)
            hit = True
    if not hit:
        unmatched_ids.append((fid, uni, fac, dep))

print(f"Total advisors scanned: {len(rows)}   (no text at all: {zero_text})")
print(f"Advisors not matching any field: {len(unmatched_ids)}\n")

print(f"{'สาขา':<40}{'อาจารย์':>8}{'มหาลัย':>8}")
print("-" * 58)
for field in sorted(field_advisors, key=lambda f: len(field_advisors[f])):
    print(f"{field:<40}{len(field_advisors[field]):>8}{len(field_unis[field]):>8}")

print("\n===== 🚨 BOTTOM 20 — สาขาที่อาจารย์ใน DB น้อยที่สุด =====")
for field in sorted(field_advisors, key=lambda f: len(field_advisors[f]))[:20]:
    print(f"  {field:<42} {len(field_advisors[field]):>4} คน | {len(field_unis[field]):>2} มหาลัย")

output_file = audit_dir / "field_advisors.json"
with open(output_file, 'w', encoding="utf-8") as f:
    json.dump({k: sorted(v) for k, v in field_advisors.items()}, f, ensure_ascii=False)
print(f"\nSaved field advisors mapping to: {output_file}")

cur.close(); conn.close()
