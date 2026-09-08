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

print(f"Testing two-tier OpenAlex author resolution on 20 zero-pub profiles:")

def resolve_author_fuzzy(f):
    clean_th = TITLE_STRIP_REGEX.sub("", f.full_name_th).strip()
    u_lower = (f.university or "").lower()
    u_th = f.university_th or ""

    # 1. Try search by Thai name
    enc_th = urllib.parse.quote(clean_th)
    data = fetch_with_retry(f"https://api.openalex.org/authors?search={enc_th}&per_page=3")
    res = data.get("results", [])
    if res:
        for a in res:
            insts = [i.get("display_name", "").lower() for i in (a.get("last_known_institutions") or [])]
            if not insts or any(u_part in " ".join(insts) for u_part in u_lower.split() if len(u_part) > 3):
                return a, "thai_name_match"

    # 2. Try search by English Last Name + Affiliation Match
    ln = (f.last_name or "").strip()
    if ln and len(ln) >= 4:
        enc_ln = urllib.parse.quote(ln)
        data = fetch_with_retry(f"https://api.openalex.org/authors?search={enc_ln}&per_page=5")
        for a in data.get("results", []):
            insts = [i.get("display_name", "").lower() for i in (a.get("last_known_institutions") or [])]
            # Match university
            if any(u_part in " ".join(insts) for u_part in u_lower.split() if len(u_part) > 3):
                # check first name initial or similarity
                fn = (f.first_name or "").strip().lower()
                dname = (a.get("display_name") or "").lower()
                if fn[:3] in dname or dname.split()[-1] == ln.lower():
                    return a, "last_name_affil_match"

    return None, None

matched = 0
for f in zero_pubs[:20]:
    a, method = resolve_author_fuzzy(f)
    if a:
        matched += 1
        print(f"✅ MATCH ({method}): {f.full_name_th} -> {a.get('display_name')} ({a.get('works_count')} works, {a.get('cited_by_count')} cites) | ID: {a.get('id')}")
    else:
        print(f"❌ Not found: {f.full_name_th} ({f.first_name} {f.last_name})")

print(f"\nTotal matched: {matched}/20 ({matched*100/20:.1f}%)")
db.close()
