# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from collections import Counter

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()

print("--- 1. INVESTIGATING THE 135 IMPOSSIBLE METRICS ---")
bad_metrics = []
for f in db.query(FacultyDB).filter(FacultyDB.h_index > 0).all():
    cits = f.total_citations if f.total_citations is not None else 0
    pubs = f.total_publications_count if f.total_publications_count is not None else 0
    if f.h_index > cits or f.h_index > pubs:
        bad_metrics.append(f)

print(f"Total: {len(bad_metrics)}")
# Group by openalex_id status and university
status_counter = Counter(
    "not_indexed" if f.openalex_id == "not_indexed"
    else ("none" if not f.openalex_id else "has_openalex")
    for f in bad_metrics
)
print("Breakdown by openalex_id:", dict(status_counter))

uni_counter = Counter(f.university_th for f in bad_metrics)
print("Breakdown by university:", dict(uni_counter))

for f in bad_metrics[:10]:
    print(f"ID: {f.id} | Name: {f.full_name_th} | Uni: {f.university_th}")
    print(f"  openalex: {f.openalex_id} | h: {f.h_index} | cits: {f.total_citations} | pubs: {f.total_publications_count}")
    print(f"  featured_pubs count: {len(f.featured_publications or [])}")
    if f.featured_publications:
        for p in f.featured_publications[:2]:
            print(f"    - {p.get('title')} (cits: {p.get('citations')})")

print("\n--- 2. INVESTIGATING MAHIDOL PHARMACY mu_pharm_wave12_* ---")
mu_pharm = db.query(FacultyDB).filter(FacultyDB.id.like("mu_pharm_wave12_%")).all()
print(f"Found {len(mu_pharm)} mu_pharm_wave12 records:")
for m in mu_pharm[:15]:
    print(f"ID: {m.id} | full_name_th: {repr(m.full_name_th)} | title: {repr(m.academic_title_th)} | fn: {repr(m.first_name)} | ln: {repr(m.last_name)}")

db.close()
