# -*- coding: utf-8 -*-
"""
OpenAlex Thai Name Enricher

Queries OpenAlex Authors API using clean Thai names for faculty records
where openalex_id IS NULL. Matches only when OpenAlex display_name or
display_name_alternatives explicitly contains the authentic Thai name.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("backend/scripts"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from fetch_openalex_publication_metrics import fetch_with_retry, all_keys_exhausted
from scripts.agentic_pipeline.state_reducer import TITLE_STRIP_REGEX

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
COMMON_INST_STOP = {
    "university", "institute", "technology", "of", "and", "the", "for",
    "state", "rajabhat", "campus", "college", "school", "king"
}


def inst_frag(u: str) -> str:
    return re.sub(r"[^a-z ]", "", (u or "").lower()).strip()


def corroborates(cand: dict, uni: str) -> bool:
    if not uni:
        return False
    utok = {t for t in inst_frag(uni).split() if len(t) >= 4 and t not in COMMON_INST_STOP}
    if not utok:
        return False
    for a in cand.get("affiliations") or []:
        disp_toks = set(inst_frag((a.get("institution") or {}).get("display_name", "")).split())
        if bool(utok & disp_toks):
            return True
    return False


def clean_thai_name(name_th: str) -> str:
    if not name_th:
        return ""
    # Strip titles and honorifics
    cleaned = TITLE_STRIP_REGEX.sub("", name_th).strip()
    for p in ["นาย ", "นาง ", "นางสาว ", "น.ส. "]:
        cleaned = cleaned.replace(p, "")
    # Remove Latin characters and punctuation attached
    cleaned = re.sub(r"[A-Za-z0-9().\-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def search_authors(name: str, per_page: int = 5) -> list:
    q = urllib.parse.quote(name)
    d = fetch_with_retry(
        f"https://api.openalex.org/authors?search={q}&per-page={per_page}",
        max_retries=4
    )
    return (d or {}).get("results", []) or []


def resolve_thai(clean_th: str, uni: str):
    """
    Return (author_dict | None, verdict).
    Matches only if the authentic Thai name is explicitly confirmed
    in display_name or display_name_alternatives.
    """
    cands = search_authors(clean_th)
    if not cands:
        return None, "no_hit"

    th_parts = clean_th.split()
    if len(th_parts) < 2:
        return None, "no_hit"

    fn_th, ln_th = th_parts[0], th_parts[-1]

    qualifying = []
    for c in cands:
        dname = (c.get("display_name") or "").strip()
        alts = [(a or "").strip() for a in c.get("display_name_alternatives", [])]
        names_to_check = [dname] + alts

        exact_match = False
        for n in names_to_check:
            if clean_th == n:
                exact_match = True
                break
            if fn_th in n and ln_th in n:
                exact_match = True
                break

        if exact_match:
            qualifying.append(c)

    if not qualifying:
        return None, "no_hit"

    # Prioritize candidates with institutional corroboration
    corr = [c for c in qualifying if corroborates(c, uni)]
    pool = corr if corr else qualifying

    # Pick candidate with highest h-index, then citations, then works
    pool.sort(
        key=lambda c: (
            (c.get("summary_stats") or {}).get("h_index") or 0,
            c.get("cited_by_count") or 0,
            c.get("works_count") or 0
        ),
        reverse=True
    )

    best = pool[0]
    return best, "match"


def probe_worker(item):
    rid, name_th, uni = item
    clean_th = clean_thai_name(name_th)
    if len(clean_th.split()) < 2 or len(clean_th) < 5:
        return rid, None, "skip", ""

    try:
        author, verdict = resolve_thai(clean_th, uni or "")
    except Exception as e:
        return rid, None, "error", str(e)[:160]

    if verdict != "match" or not author:
        return rid, None, verdict, ""

    ss = author.get("summary_stats") or {}
    payload = {
        "openalex_id": author.get("id"),
        "matched_author_name": author.get("display_name"),
        "h_index": ss.get("h_index") or 0,
        "total_citations": author.get("cited_by_count") or 0,
        "total_publications_count": author.get("works_count") or 0,
        "corroborated": corroborates(author, uni),
    }
    return rid, payload, "match", ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Commit to DB")
    parser.add_argument("--limit", type=int, default=0, help="Limit count")
    parser.add_argument("--workers", type=int, default=8, help="Worker threads")
    parser.add_argument("--batch", type=int, default=50, help="Commit batch size")
    args = parser.parse_args()

    db = SessionLocal()
    rows = (
        db.query(FacultyDB.id, FacultyDB.full_name_th, FacultyDB.university)
        .filter(FacultyDB.openalex_id.is_(None))
        .all()
    )
    db.close()

    items = [(r.id, r.full_name_th, r.university) for r in rows if r.full_name_th]
    if args.limit:
        items = items[: args.limit]

    total = len(items)
    print(f"🚀 Probing {total} Thai-named faculties against OpenAlex (workers={args.workers})...", flush=True)
    if total == 0:
        return

    counts = {"match": 0, "no_hit": 0, "skip": 0, "error": 0}
    matches_to_apply = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(probe_worker, item): item for item in items}
        done = 0
        for f in as_completed(futures):
            rid, payload, verdict, _ = f.result()
            counts[verdict] = counts.get(verdict, 0) + 1
            if verdict == "match" and payload:
                matches_to_apply.append((rid, payload))

            done += 1
            if done % 100 == 0 or done == total:
                elapsed = time.time() - start_time
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (total - done) / rate if rate > 0 else 0
                print(
                    f"  [{done}/{total}] Matches: {counts.get('match', 0)} | "
                    f"No-hit: {counts.get('no_hit', 0)} | Rate: {rate:.1f}/s (ETA: {remaining/60:.1f}m)",
                    flush=True
                )

            if all_keys_exhausted():
                print("\n🛑 All API keys have exhausted daily quota! Halting probe gracefully as requested...", flush=True)
                for pending in futures:
                    pending.cancel()
                break

    print("\n" + "=" * 60)
    print(f"📊 PROBE COMPLETE in {time.time() - start_time:.1f}s")
    print(f"   Matches: {counts.get('match', 0)}")
    print(f"   No-hit: {counts.get('no_hit', 0)}")
    print(f"   Skip: {counts.get('skip', 0)}")
    print("=" * 60)

    if not args.apply:
        print("  (Dry-run mode — nothing committed to DB. Run with --apply to commit.)")
        return

    if not matches_to_apply:
        print("  No matches to apply.")
        return

    print(f"\n💾 Committing {len(matches_to_apply)} matches to database...")
    db = SessionLocal()
    applied_count = 0
    checkpoint_records = []
    try:
        for idx, (rid, payload) in enumerate(matches_to_apply):
            fac = db.get(FacultyDB, rid)
            if not fac:
                continue
            if fac.openalex_id is not None and fac.openalex_id != "not_indexed":
                continue

            fac.openalex_id = payload["openalex_id"]
            fac.h_index = payload["h_index"]
            fac.total_citations = payload["total_citations"]
            fac.total_publications_count = max(
                fac.total_publications_count or 0,
                payload["total_publications_count"]
            )
            checkpoint_records.append({"id": rid, **payload})
            applied_count += 1

            if applied_count % args.batch == 0:
                db.commit()

        db.commit()
    finally:
        db.close()

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    cp_path = os.path.join(CHECKPOINT_DIR, "openalex_thai_matches.json")
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint_records, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully committed {applied_count} Thai-matched faculties to database!")
    print(f"   Checkpoint saved to {cp_path}")


if __name__ == "__main__":
    main()
