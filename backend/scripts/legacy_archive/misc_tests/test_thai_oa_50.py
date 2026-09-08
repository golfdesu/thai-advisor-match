# -*- coding: utf-8 -*-
import sys, urllib.parse
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry
from scripts.agentic_pipeline.state_reducer import TITLE_STRIP_REGEX

db = SessionLocal()
unindexed = db.query(FacultyDB).filter(
    (FacultyDB.total_publications_count == 0) | (FacultyDB.openalex_id == None) | (FacultyDB.openalex_id == '')
).all()
zero_pubs = [f for f in unindexed if not f.featured_publications or len(f.featured_publications) == 0]

print(f"Testing Thai name search in OpenAlex across 50 zero-pub profiles...")

matched = 0
found_list = []
for f in zero_pubs[:50]:
    clean_th = TITLE_STRIP_REGEX.sub("", f.full_name_th).strip()
    clean_th = clean_th.replace("นาย ", "").replace("นาง ", "").replace("นางสาว ", "").strip()
    if len(clean_th) < 4:
        continue

    enc_th = urllib.parse.quote(clean_th)
    data = fetch_with_retry(f"https://api.openalex.org/authors?search={enc_th}&per_page=2")
    res = data.get("results", [])
    if res:
        # Check display name
        top = res[0]
        dname = top.get("display_name", "")
        # If Thai characters match closely
        if any(part in dname for part in clean_th.split() if len(part) >= 3):
            matched += 1
            found_list.append((f.id, f.full_name_th, dname, top.get("id"), top.get("works_count", 0)))

print(f"Matched {matched}/50 ({matched*100/50:.1f}%)!")
for fid, th, oa_name, oaid, wc in found_list[:10]:
    print(f"  {th} -> {oa_name} (Works: {wc}) [{oaid}]")

db.close()
