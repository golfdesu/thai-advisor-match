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
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("backend/scripts"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
try:
    from scripts.fetch_openalex_publication_metrics import fetch_with_retry, all_keys_exhausted
except ImportError:
    from fetch_openalex_publication_metrics import fetch_with_retry, all_keys_exhausted

MAX_WORKERS = 8
PRINT_LOCK = threading.Lock()


def is_real_publication(p) -> bool:
    """Check if a publication entry has authentic OpenAlex or DOI metadata."""
    if not isinstance(p, dict):
        return False
    url = (p.get("url") or "").lower()
    if "openalex.org" in url or "doi.org" in url:
        return True
    if (p.get("citation_count") or 0) > 0 and (p.get("venue") or p.get("year")):
        return True
    # If it has year and venue and title doesn't look like an architectural boilerplate header
    if p.get("year") and p.get("venue"):
        return True
    return False

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


def run_openalex_publication_enrichment(limit: int = 0, workers: int = MAX_WORKERS, batch_size: int = 50):
    db = SessionLocal()
    try:
        # Query only needed columns (id, openalex_id, full_name_th, featured_publications)
        # to avoid ballooning 768-dim vector embeddings into memory
        candidates = db.query(
            FacultyDB.id,
            FacultyDB.openalex_id,
            FacultyDB.full_name_th,
            FacultyDB.featured_publications,
            FacultyDB.total_publications_count
        ).filter(
            FacultyDB.total_publications_count > 0,
            FacultyDB.openalex_id.like('%openalex.org%')
        ).all()

        target_faculties = []
        for f in candidates:
            pubs = f.featured_publications or []
            real_pubs = [p for p in pubs if is_real_publication(p)]
            expected_count = min(5, f.total_publications_count or 5)
            if len(real_pubs) < expected_count:
                target_faculties.append((f.id, f.openalex_id, f.full_name_th, pubs))
    finally:
        db.close()

    if limit and limit > 0:
        target_faculties = target_faculties[:limit]

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

    # Process in batches to frequently commit to DB
    for i in range(0, total, batch_size):
        chunk = target_faculties[i:i + batch_size]
        chunk_results = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task, item) for item in chunk]
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    chunk_results.append(res)
                except Exception:
                    pass

        # Batch write to DB with exception-safe rollback and close
        db_write = SessionLocal()
        try:
            saved_count = 0
            for fid, name_th, works, existing_pubs in chunk_results:
                if not works:
                    continue
                fac_rec = db_write.query(FacultyDB).filter(FacultyDB.id == fid).first()
                if not fac_rec:
                    continue

                # Keep authentic publications, filter out placeholder dummy strings
                existing_real = [ep for ep in (fac_rec.featured_publications or []) if is_real_publication(ep)]
                existing_titles = set()
                merged_pubs = []
                for ep in existing_real:
                    t = ep.get("title") if isinstance(ep, dict) else str(ep)
                    if t and t.lower() not in existing_titles:
                        existing_titles.add(t.lower())
                        merged_pubs.append(ep)

                for nw in works:
                    nt = nw["title"]
                    if nt.lower() not in existing_titles:
                        existing_titles.add(nt.lower())
                        merged_pubs.append(nw)

                # Prioritize highest cited authentic publications and take top 5
                merged_pubs.sort(key=lambda p: (p.get("citation_count") or 0) if isinstance(p, dict) else 0, reverse=True)
                fac_rec.featured_publications = merged_pubs[:5]
                saved_count += 1

            db_write.commit()
        except Exception:
            db_write.rollback()
            raise
        finally:
            db_write.close()

        completed += len(chunk)
        elapsed = time.time() - start_time
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = (total - completed) / rate if rate > 0 else 0
        print(f"[{completed}/{total}] Enriched {saved_count} in chunk | Overall progress: {completed*100/total:.1f}% (ETA: {remaining/60:.1f}m)")

        if all_keys_exhausted():
            print("\n⚠️ Daily quota reached across all OpenAlex API keys! Pausing works enrichment cleanly.")
            break

    print("=" * 65)
    print(f"✅ COMPLETED OPENALEX PUBLICATION ENRICHMENT IN {time.time() - start_time:.1f}s")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Enrich faculty publications using OpenAlex Works API")
    parser.add_argument("--limit", type=int, default=0, help="Maximum faculties to process (0 = all)")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Worker threads for HTTP fetching")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch commit size")
    args = parser.parse_args()

    run_openalex_publication_enrichment(limit=args.limit, workers=args.workers, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
