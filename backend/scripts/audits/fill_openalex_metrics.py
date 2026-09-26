# -*- coding: utf-8 -*-
"""
Phase 1a helper — fill author-level metrics for rows that hold a canonical OpenAlex ID but
total_publications_count = 0 (2026-09-26). enrich_openalex_works.py skips those rows, so their
featured publications never get fetched.

Authoritative lifetime metrics (AGENTS.md §9.10): works_count / cited_by_count / h_index are read
from the author record and written with GREATEST — never lowered.

Usage (local Docker DB only):
    python scripts/audits/fill_openalex_metrics.py            # dry-run
    python scripts/audits/fill_openalex_metrics.py --apply
"""
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remediate_bare_openalex_ids import DSN, OA_PREFIX, fetch_with_retry  # noqa: E402


def fetch_chunk(chunk: list[str]) -> list[dict]:
    url = ("https://api.openalex.org/authors?per-page=50&filter=openalex:" +
           "|".join(i.rsplit("/", 1)[-1] for i in chunk) +
           "&select=id,works_count,cited_by_count,summary_stats")
    return (fetch_with_retry(url) or {}).get("results", [])


def main(apply: bool) -> None:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("""SELECT openalex_id FROM faculties
                   WHERE openalex_id LIKE %s AND coalesce(total_publications_count,0) = 0""",
                (OA_PREFIX + "A%",))
    ids = sorted({r[0] for r in cur.fetchall()})
    chunks = [ids[i:i + 50] for i in range(0, len(ids), 50)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        authors = [a for res in ex.map(fetch_chunk, chunks) for a in res]
    with_works = [a for a in authors if (a.get("works_count") or 0) > 0]
    print(f"target IDs: {len(ids)} | fetched: {len(authors)} | works_count > 0: {len(with_works)}")
    if not apply:
        print("DRY-RUN only — re-run with --apply to execute.")
        return
    for a in with_works:
        cur.execute("""UPDATE faculties SET
                           total_publications_count = GREATEST(coalesce(total_publications_count,0), %s),
                           total_citations = GREATEST(coalesce(total_citations,0), %s),
                           h_index = GREATEST(coalesce(h_index,0), %s)
                       WHERE openalex_id = %s""",
                    (a["works_count"], a.get("cited_by_count") or 0,
                     (a.get("summary_stats") or {}).get("h_index") or 0, a["id"]))
    conn.commit()
    cur.close(); conn.close()
    print(f"APPLIED to {len(with_works)} author IDs.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fill OpenAlex author metrics for zero-works canonical rows")
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
