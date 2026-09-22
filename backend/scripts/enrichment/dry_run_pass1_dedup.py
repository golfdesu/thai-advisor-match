# -*- coding: utf-8 -*-
"""
Dry-run of Pass 1 Deduplication:
Same University + Normalized Thai Full Name (>= 2 Thai words)
"""
import os
import sys
import re
import json
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_TITLE = re.compile(
    r"^(ศ\.เชี่ยวชาญพิเศษ\s+ดร\.\s+นพ\.|ศ\.คลินิก\s+ดร\.\s+สพ\.ญ\.|ศ\.คลินิก\s+ทพญ\.|"
    r"ศ\.ดร\.นพ\.|ศ\.ดร\.พญ\.|ศ\.ดร\.ภก\.|ศ\.ดร\.ภญ\.|ศ\.ดร\.น\.สพ\.|ศ\.ดร\.สพ\.ญ\.|"
    r"รศ\.ดร\.นพ\.|รศ\.ดร\.พญ\.|รศ\.ดร\.ภก\.|รศ\.ดร\.ภญ\.|รศ\.ดร\.น\.สพ\.|รศ\.ดร\.สพ\.ญ\.|รศ\.ดร\.ทพ\.|รศ\.ดร\.ทพญ\.|"
    r"ผศ\.ดร\.นพ\.|ผศ\.ดร\.พญ\.|ผศ\.ดร\.ภก\.|ผศ\.ดร\.ภญ\.|ผศ\.ดร\.น\.สพ\.|ผศ\.ดร\.สพ\.ญ\.|ผศ\.ดร\.ทพ\.|ผศ\.ดร\.ทพญ\.|"
    r"ศ\.นพ\.|ศ\.พญ\.|ศ\.ภก\.|ศ\.ภญ\.|ศ\.น\.สพ\.|ศ\.สพ\.ญ\.|ศ\.ทพ\.|ศ\.ทพญ\.|"
    r"รศ\.นพ\.|รศ\.พญ\.|รศ\.ภก\.|รศ\.ภญ\.|รศ\.น\.สพ\.|รศ\.สพ\.ญ\.|รศ\.ทพ\.|รศ\.ทพญ\.|"
    r"ผศ\.นพ\.|ผศ\.พญ\.|ผศ\.ภก\.|ผศ\.ภญ\.|ผศ\.น\.สพ\.|ผศ\.สพ\.ญ\.|ผศ\.ทพ\.|ผศ\.ทพญ\.|"
    r"อ\.นพ\.|อ\.พญ\.|อ\.ภก\.|อ\.ภญ\.|อ\.น\.สพ\.|อ\.สพ\.ญ\.|อ\.ทพ\.|อ\.ทพญ\.|"
    r"ศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+นพ\.|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|"
    r"ศ\.คลินิก|รศ\.คลินิก|ผศ\.คลินิก|ศ\.\(พิเศษ\)|รศ\.\(พิเศษ\)|ผศ\.\(พิเศษ\)|"
    r"ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.)\s*"
)

db = SessionLocal()
faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()

groups = defaultdict(list)
for f in faculties:
    name_th = (f.full_name_th or "").strip()
    if re.search(r"[฀-๿]", name_th):
        m = RE_TITLE.match(name_th)
        bare_th = name_th[m.end():].strip() if m else name_th
        bare_th = re.sub(r"\s+", " ", bare_th)
        words = bare_th.split()
        if len(words) >= 2 and len(bare_th) >= 6:
            groups[(f.university_th, bare_th)].append(f)

dup_clusters = {k: v for k, v in groups.items() if len(v) > 1}
print(f"Total duplicate clusters found: {len(dup_clusters)}")
donor_count = sum(len(v) - 1 for v in dup_clusters.values())
print(f"Total donor records to be merged into primary: {donor_count}")

# Check scoring logic for choosing primary
sample_merges = []
for (univ, bare_name), cluster in list(dup_clusters.items())[:10]:
    # Score function
    def score_fac(fac):
        s = 0
        if fac.email and len(fac.email) > 5: s += 100
        if fac.openalex_id and fac.openalex_id != "not_indexed": s += 50
        if fac.academic_title_th: s += 20
        if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 15
        if fac.total_citations: s += min(fac.total_citations, 50)
        if fac.featured_publications: s += len(fac.featured_publications) * 2
        return s

    sorted_cluster = sorted(cluster, key=score_fac, reverse=True)
    primary = sorted_cluster[0]
    donors = sorted_cluster[1:]
    sample_merges.append({
        "univ": univ,
        "name": bare_name,
        "primary": f"{primary.id} | {primary.full_name_th} | email: {primary.email} | openalex: {primary.openalex_id} | cites: {primary.total_citations}",
        "donors": [f"{d.id} | {d.full_name_th} | email: {d.email} | openalex: {d.openalex_id} | cites: {d.total_citations}" for d in donors]
    })

for s in sample_merges[:5]:
    print(f"\nCluster: {s['univ']} | '{s['name']}'")
    print(f"  Primary: {s['primary']}")
    for d in s['donors']:
        print(f"  Donor:   {d}")

db.close()
