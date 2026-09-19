# -*- coding: utf-8 -*-
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB, ResearchLabDB

db = SessionLocal()

print("--- DETAILED ANOMALY INVESTIGATION ---")

# 1. Investigate impossible OpenAlex metrics
facs = db.query(FacultyDB).filter(FacultyDB.h_index > 0).all()
bad_metrics = []
for f in facs:
    cits = f.total_citations if f.total_citations is not None else -1
    pubs = f.total_publications_count if f.total_publications_count is not None else -1
    if f.h_index > cits or f.h_index > pubs:
        bad_metrics.append((f.id, f.full_name_th, f.openalex_id, f.h_index, f.total_citations, f.total_publications_count))

print(f"Total faculty with h_index > citations or h_index > pubs: {len(bad_metrics)}")
for bm in bad_metrics[:15]:
    print(f"  {bm[0]} | {bm[1]} | openalex: {bm[2]} | h={bm[3]}, cits={bm[4]}, pubs={bm[5]}")

# 2. Investigate the 73 English names containing title prefixes
print("\n--- 73 ENGLISH NAMES WITH TITLES ---")
title_tokens_en = ["dr.", "dr", "prof.", "prof", "assoc.", "asst.", "assist.", "ph.d.", "md", "m.d.", "lecturer"]
bad_en_names = []
for f in db.query(FacultyDB).all():
    fn = (f.first_name or "")
    ln = (f.last_name or "")
    combined = f"{fn} {ln}".lower()
    if any(t in combined.split() for t in title_tokens_en) or "," in combined or "ph.d" in combined or "assist" in combined:
        bad_en_names.append((f.id, f.full_name_th, f.first_name, f.last_name))

print(f"Found {len(bad_en_names)} faculties with corrupted English names:")
for ben in bad_en_names[:25]:
    print(f"  {ben[0]} | {ben[1]} -> fn='{ben[2]}', ln='{ben[3]}'")

# 3. Investigate SUT tab character
sut = db.query(FacultyDB).filter(FacultyDB.id == "sut_thanasak_phittayakorn_8728").first()
if sut:
    print(f"\nSUT record: id={sut.id}, full_name_th={repr(sut.full_name_th)}, fn={repr(sut.first_name)}, ln={repr(sut.last_name)}")

# 4. Investigate duplicate CMU faculty
for fid in ["cmu_21646dd5_9077", "cmu_398c4c40_5859", "cmu_6add0253_6499", "cmu-med-021_9d90dd"]:
    rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
    if rec:
        print(f"\nCMU rec {rec.id}:")
        print(f"  name_th: {rec.full_name_th}")
        print(f"  en: {rec.first_name} {rec.last_name}")
        print(f"  email: {rec.email}")
        print(f"  openalex: {rec.openalex_id}, h={rec.h_index}, cits={rec.total_citations}, pubs={rec.total_publications_count}")
        print(f"  featured_pubs count: {len(rec.featured_publications or [])}")

# 5. Investigate course duration and program_type anomalies
print("\n--- COURSE DURATION ANOMALIES ---")
courses = db.query(CourseDB).all()
bad_dur = []
for c in courses:
    dur = (c.duration_years or "").strip()
    if dur and not (dur.endswith("ปี") or dur == "ไม่ระบุ"):
        bad_dur.append((c.id, c.title_th, repr(dur)))
print(f"Found {len(bad_dur)} course duration anomalies:")
for bd in bad_dur:
    print(f"  {bd[0]} | {bd[1]} | {bd[2]}")

print("\n--- COURSE PROGRAM_TYPE WITH CORRUPTED CHARS ---")
for c in courses:
    pt = c.program_type or ""
    if any(c in pt for c in ["�", "\x00", "\r", "\n", "\t"]):
        print(f"  {c.id} | {c.title_th} | {repr(pt)}")

db.close()
