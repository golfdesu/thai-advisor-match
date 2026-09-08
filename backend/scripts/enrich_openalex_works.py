# -*- coding: utf-8 -*-
"""
Enrich Missing Faculty Publications from OpenAlex Works API (Track 1)
Fetches top 5 cited works for faculties with verified OpenAlex IDs
and updates featured_publications with rich metadata (title, year, venue, citation_count).
"""

import sys
import os
import time
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.abspath("backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

MAX_WORKERS = 8
PRINT_LOCK = threading.Lock()

def fetch_top_works_for_author(openalex_id_raw: str, max_works: int = 5) -> list:
    """Fetch top cited works for a single OpenAlex author ID"""
    m = re.search(r'(A\d+)', openalex_id_raw)
    if not m:
        return []
    aid = m.group(1)

    url = f"https://api.openalex.org/works?filter=author.id:{aid}&sort=cited_by_count:desc&per_page={max_works}"
    data = fetch_with_retry(url)
    results = data.get("results", [])

    formatted_pubs = []
    for r in results:
        title = (r.get("title") or "").strip()
        if not title:
            continue
        year = r.get("publication_year")
        citations = r.get("cited_by_count") or 0
        primary_loc = r.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        venue = source.get("display_name")
        doi = r.get("doi")

        pub_dict = {
            "title": title,
            "year": year,
            "venue": venue,
            "url": doi or (f"https://openalex.org/{r.get('id', '').split('/')[-1]}" if r.get("id") else ""),
            "citation_count": citations
        }
        formatted_pubs.append(pub_dict)

    return formatted_pubs


def run_openalex_publication_enrichment():
    db = SessionLocal()

    # Query faculties with verified OpenAlex IDs and pub count > 0 who need enrichment (< 3 publications)
    candidates = db.query(FacultyDB).filter(
        FacultyDB.total_publications_count > 0,
        FacultyDB.openalex_id.like('%openalex.org%')
    ).all()

    target_faculties = []
    for f in candidates:
        pubs = f.featured_publications or []
        if len(pubs) < 3:
            target_faculties.append((f.id, f.openalex_id, f.full_name_th, pubs))

    db.close()

    total = len(target_faculties)
    print("=" * 65)
    print(f"🚀 STARTING OPENALEX WORKS ENRICHMENT FOR {total} FACULTIES")
    print("=" * 65)

    if total == 0:
        print("✅ No faculties need OpenAlex works enrichment!")
        return

    enriched_results = {}
    completed = 0
    start_time = time.time()

    def worker_task(item):
        fid, oaid, name_th, existing_pubs = item
        works = fetch_top_works_for_author(oaid, max_works=5)
        return fid, name_th, works, existing_pubs

    # Process in batches of 50 to frequently commit to DB
    batch_size = 50
    for i in range(0, total, batch_size):
        chunk = target_faculties[i:i + batch_size]
        chunk_results = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(worker_task, item) for item in chunk]
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    chunk_results.append(res)
                except Exception as e:
                    pass

        # Batch write to DB
        db_write = SessionLocal()
        saved_count = 0
        for fid, name_th, works, existing_pubs in chunk_results:
            if not works:
                continue
            fac_rec = db_write.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if not fac_rec:
                continue

            # Merge: Keep existing publications if unique, append fetched OpenAlex works
            existing_titles = set()
            merged_pubs = []
            for ep in (fac_rec.featured_publications or []):
                t = ep.get("title") if isinstance(ep, dict) else str(ep)
                if t and t.lower() not in existing_titles:
                    existing_titles.add(t.lower())
                    merged_pubs.append(ep)

            for nw in works:
                nt = nw["title"]
                if nt.lower() not in existing_titles:
                    existing_titles.add(nt.lower())
                    merged_pubs.append(nw)

            fac_rec.featured_publications = merged_pubs
            saved_count += 1

        db_write.commit()
        db_write.close()

        completed += len(chunk)
        elapsed = time.time() - start_time
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = (total - completed) / rate if rate > 0 else 0
        print(f"[{completed}/{total}] Enriched {saved_count} in chunk | Overall progress: {completed*100/total:.1f}% (ETA: {remaining/60:.1f}m)")

    print("=" * 65)
    print(f"✅ COMPLETED OPENALEX PUBLICATION ENRICHMENT IN {time.time() - start_time:.1f}s")
    print("=" * 65)


if __name__ == "__main__":
    run_openalex_publication_enrichment()
