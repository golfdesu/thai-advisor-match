# -*- coding: utf-8 -*-
"""
OpenAlex Author-Metrics Enricher  (h-index / citations / works for un-attempted faculty)

Populates research-impact metrics for faculties that were never run through OpenAlex
enrichment (openalex_id IS NULL). This is the missing tool the earlier pipeline lacked:
every previous script copied h_index from Supabase or wrote only publication titles —
none resolved a *new* author and pulled their h-index.

HOMONYM SAFETY (critical — this feeds the university "distinguished advisor" ranking):
  OpenAlex `search=` can match a stranger (observed live: empty-surname "Pi" →
  "Ileana Heredia-Pi", h=31). We only adopt a candidate when its display_name carries
  the SURNAME as a whole token AND the first name or its initial. When several
  candidates qualify and none is corroborated by the faculty's own university, we
  refuse to guess and leave the row untouched. A wrong-but-confident match is far
  worse than a miss.

Writes (only on a confident match): openalex_id, h_index, total_citations,
total_publications_count. Genuine no-hits get openalex_id='not_indexed' so re-runs
skip them. h_index is NOT part of embedding_text (see canonical_faculty_merge
build_embedding_text) → no embedding refresh needed, no semantic drift.

Concurrency: ThreadPool workers perform HTTP ONLY and return plain data. Every DB
read/write happens on the main thread (SQLAlchemy sessions are not thread-safe).

Run from the REPO ROOT. Default dry-run; pass --apply to commit. Idempotent: the
selection query is openalex_id IS NULL, and applied rows leave that set, so a
re-run resumes exactly where it stopped. Each batch also mirrors to a JSON
checkpoint under backend/data/agent_states/ for manual reversal.

  python backend/scripts/enrich_openalex_author_metrics.py                # dry-run
  python backend/scripts/enrich_openalex_author_metrics.py --apply
  python backend/scripts/enrich_openalex_author_metrics.py --apply --limit 200
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

from sqlalchemy import and_, or_

from app.core.database import SessionLocal                        # noqa: E402
from app.models.db_models import FacultyDB                        # noqa: E402
from fetch_openalex_publication_metrics import fetch_with_retry   # noqa: E402

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
SENTINEL_MISS = "not_indexed"
_TOKEN_RE = re.compile(r"[a-z]+")


def tokens(name: str) -> set:
    """Lowercase alphabetic tokens: 'M. Sarikaputi' -> {'m', 'sarikaputi'}."""
    return set(_TOKEN_RE.findall((name or "").lower()))


def inst_frag(u: str) -> str:
    return re.sub(r"[^a-z ]", "", (u or "").lower()).strip()


def corroborates(cand: dict, uni: str) -> bool:
    """True if an author affiliation string shares a meaningful token with the DB university."""
    if not uni:
        return False
    utok = {t for t in inst_frag(uni).split() if len(t) > 4 and t not in ("university", "institute")}
    if not utok:
        return False
    for a in cand.get("affiliations") or []:
        disp = inst_frag((a.get("institution") or {}).get("display_name", ""))
        if any(t in disp for t in utok):
            return True
    return False


CANARY = "Sutkhet Nakasathien"   # definitely in OpenAlex; empty here => rate-limited, not "no authors"


def api_healthy() -> bool:
    """Distinguish throttle from genuine empties. When keys are exhausted AND the polite
    pool 429s, every lookup returns [] — a health-gated run must abort instead of
    stamping 'not_indexed' onto rate-limit blinks."""
    return bool(search_authors(CANARY, per_page=1))


def search_authors(name: str, per_page: int = 10) -> list:
    q = urllib.parse.quote(name)
    d = fetch_with_retry(f"https://api.openalex.org/authors?search={q}&per-page={per_page}",
                         max_retries=4)
    return (d or {}).get("results", []) or []


def resolve(first: str, last: str, uni: str):
    """Return (author_dict|None, verdict). verdict ∈ {'match','no_hit','ambiguous'}."""
    cands = search_authors(f"{first} {last}")
    if not cands:
        return None, "no_hit"
    last_tok, first_tok = last.lower(), first.lower()
    qualifying = [c for c in cands
                  if last_tok in tokens(c.get("display_name"))
                  and (first_tok in tokens(c.get("display_name")) or first_tok[:1] in tokens(c.get("display_name")))]
    if not qualifying:
        return None, "no_hit"
    corr = [c for c in qualifying if corroborates(c, uni)]
    if len(qualifying) == 1 or corr:
        pool = corr or qualifying
        pool.sort(key=lambda c: ((c.get("summary_stats") or {}).get("h_index") or 0), reverse=True)
        return pool[0], "match"
    return None, "ambiguous"   # several uncorroborated people → don't guess


def probe(row):
    """NETWORK ONLY — no DB access (runs in worker threads). row is a plain tuple."""
    rid, fn, ln, uni = row
    try:
        author, verdict = resolve(fn.strip(), ln.strip(), uni or "")
    except Exception as e:
        return rid, None, f"error", str(e)[:160]
    if verdict != "match":
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to DB (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="max faculty this invocation (0 = all)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--batch", type=int, default=40, help="commit interval")
    ap.add_argument("--include-sentinel", action="store_true",
                    help="also re-probe rows marked 'not_indexed' with h_index=0 "
                         "(use after a rate-limited run; quota resets daily)")
    args = ap.parse_args()

    db = SessionLocal()
    # Plain column query: no ORM objects cross thread boundaries, ever.
    # --include-sentinel: re-probe rows previously marked 'not_indexed' that still
    # have h_index=0. Needed when a run was rate-limited and misses were recorded
    # against exhausted keys — quota resets daily, so yesterday's no_hit may be today's match.
    id_filter = (FacultyDB.openalex_id.is_(None)
                 if not args.include_sentinel
                 else (or_(FacultyDB.openalex_id.is_(None),
                           and_(FacultyDB.openalex_id == SENTINEL_MISS, FacultyDB.h_index == 0))))
    rows = (db.query(FacultyDB.id, FacultyDB.first_name, FacultyDB.last_name, FacultyDB.university)
            .filter(id_filter,
                    FacultyDB.first_name.isnot(None),
                    FacultyDB.last_name.isnot(None))
            .all())
    # romanized-only: OpenAlex keys on latin names; require a real surname (>=3 chars)
    rows = [r for r in rows if r.first_name.isascii() and r.last_name.isascii()
            and len(r.last_name.strip()) >= 3]
    if args.limit:
        rows = rows[: args.limit]
    print(f"Targets (openalex_id IS NULL, romanized, surname>=3): {len(rows)}", flush=True)
    if not rows:
        db.close()
        return
    if not api_healthy():
        print("✋ OpenAlex unreachable right now (keys exhausted AND polite pool throttled). "
              "Aborting before any writes so misses aren't mislabeled. Retry later — "
              "key quotas reset daily.", flush=True)
        db.close()
        return

    counts = {"match": 0, "no_hit": 0, "ambiguous": 0, "error": 0, "metric_gain": 0}
    changes = []
    done = 0

    def apply_one(rid, payload, verdict):
        fac = db.get(FacultyDB, rid)
        if fac is None:
            return False
        if fac.openalex_id is not None and fac.openalex_id != SENTINEL_MISS:
            return False                      # already resolved — never clobber
        if fac.openalex_id == SENTINEL_MISS and verdict == "no_hit":
            return False                      # still a miss → leave sentinel, no churn
        if verdict == "match":
            before = {"h": fac.h_index, "cit": fac.total_citations}
            gained = payload["h_index"] != (fac.h_index or 0)
            fac.openalex_id = payload["openalex_id"]
            fac.h_index = payload["h_index"]
            fac.total_citations = payload["total_citations"]
            fac.total_publications_count = payload["total_publications_count"]
            rec = {"id": rid, "verdict": "match", "corroborated": payload["corroborated"],
                   "openalex_id": payload["openalex_id"],
                   "matched_author_name": payload["matched_author_name"],
                   "h_index": payload["h_index"], "total_citations": payload["total_citations"],
                   "total_publications_count": payload["total_publications_count"],
                   "before": before}
            if gained:
                counts["metric_gain"] += 1
            changes.append(rec)
        elif verdict == "no_hit":
            fac.openalex_id = SENTINEL_MISS    # stop re-querying a confirmed miss
            changes.append({"id": rid, "verdict": verdict})
        else:
            changes.append({"id": rid, "verdict": verdict})   # leave NULL → retried later

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(probe, r) for r in rows]
        for fut in as_completed(futures):
            rid, payload, verdict, err = fut.result()
            done += 1
            counts[verdict if verdict in counts else "error"] += 1
            if err:
                print(f"  ! {rid} {err}", flush=True)
            if args.apply:
                apply_one(rid, payload, verdict)
                if done % args.batch == 0:
                    db.commit()
                    write_checkpoint(args.apply, counts, changes)
                    # keys can expire MID-run (observed: quota burned after ~500 queries).
                    # If the API goes dark, give the polite pool a minute, then stop cleanly
                    # rather than stamping 'not_indexed' onto throttle blinks.
                    if not api_healthy():
                        print(f"  ⏸ API degraded at {done}/{len(rows)} — waiting 60s…", flush=True)
                        time.sleep(60)
                        if not api_healthy():
                            print("  ✋ still degraded — stopping this wave (resumable).", flush=True)
                            break
            elif verdict == "match":
                changes.append({"id": rid, "verdict": "match", "corroborated": payload["corroborated"],
                                "matched_author_name": payload["matched_author_name"],
                                "openalex_id": payload["openalex_id"], "h_index": payload["h_index"]})
            if done % 100 == 0:
                print(f"  ...{done}/{len(rows)} {counts}", flush=True)

    if args.apply:
        db.commit()
    write_checkpoint(args.apply, counts, changes)
    print("\n==== SUMMARY ====")
    for k, v in counts.items():
        print(f"  {k:<12} {v}")
    if not args.apply:
        print("\n  (dry-run — nothing written. Re-run with --apply.)")
    db.close()


def write_checkpoint(apply_mode, counts, changes):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    cp = os.path.join(CHECKPOINT_DIR, f"openalex_author_metrics_{'apply' if apply_mode else 'dryrun'}.json")
    with open(cp, "w", encoding="utf-8") as f:
        json.dump({"mode": "apply" if apply_mode else "dry-run", "counts": counts,
                   "changes": changes, "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                  f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
