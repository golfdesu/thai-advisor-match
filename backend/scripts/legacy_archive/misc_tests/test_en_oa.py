# -*- coding: utf-8 -*-
import sys, urllib.parse
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

db = SessionLocal()
zeros = [f for f in db.query(FacultyDB).all() if not f.featured_publications or len(f.featured_publications) == 0]

print(f"Testing English name search in OpenAlex for 25 zero-pub profiles (out of {len(zeros)})...")
found = 0
for f in zeros[:25]:
    fname = f.first_name or ""
    lname = f.last_name or ""
    en_name = f"{fname} {lname}".strip()
    if not en_name or len(en_name) < 5:
        continue
    enc = urllib.parse.quote(en_name)
    data = fetch_with_retry(f"https://api.openalex.org/authors?search={enc}&per_page=3")
    results = data.get("results", [])
    for a in results:
        dname = a.get("display_name", "")
        # Check if last name matches
        if lname.lower() and lname.lower() in dname.lower():
            aid = a.get("id", "").split("/")[-1]
            wc = a.get("works_count", 0)
            print(f"MATCH: {f.full_name_th} ({en_name}) -> {dname} (Works: {wc}) [{aid}]")
            found += 1
            break

print(f"Total matched: {found}/25 ({found*100/25:.1f}%)")
db.close()
