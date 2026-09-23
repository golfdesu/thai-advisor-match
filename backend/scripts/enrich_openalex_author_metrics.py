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
  the SURNAME as a whole token AND the first name or its initial. A unique qualifying
  candidate without university corroboration is retained as a low-confidence match
  (`corroborated=False`); several uncorroborated candidates are left ambiguous. A
  wrong-but-confident match is far worse than a miss.

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
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPTS_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR))

from sqlalchemy import and_, or_

from app.core.database import SessionLocal                        # noqa: E402
from app.models.db_models import FacultyDB                        # noqa: E402
from fetch_openalex_publication_metrics import (                  # noqa: E402
    fetch_with_retry, all_keys_exhausted
)

CHECKPOINT_DIR = os.path.join("backend", "data", "agent_states")
SENTINEL_MISS = "not_indexed"
# Deliberately disambiguated homonyms (Phase 5/10 approved repairs): their
# metrics were proven to belong to ANOTHER person (e.g. MFU physician
# mfu_med_komsan_001 vs the MFU/CMU economist of the same name). Never
# re-probe these, even with --include-sentinel — a wrong-but-confident
# match is far worse than a miss. See audits/apply_phase10_metric_repairs.py.
PROTECTED_SENTINEL_IDS = frozenset({
    "mfu_med_komsan_001",
    "chulalongk_facultyofp_fac_036_036",
    "chulalongk_facultyofp_fac_010_010",
    "chulalongk_facultyofa_fac_008_008",
    "khonkaenun_facultyofm_fac_035_035",
    "regionalun_facultymem_fac_050_050",
})
_TOKEN_RE = re.compile(r"[a-z]+")


def strip_accents(s: str) -> str:
    """Normalize Latin diacritics: 'Söhnke' -> 'Sohnke'."""
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))


def tokens(name: str) -> set:
    """Lowercase alphabetic tokens: 'M. Sarikaputi' -> {'m', 'sarikaputi'}."""
    return set(_TOKEN_RE.findall(strip_accents(name or "").lower()))


def inst_frag(u: str) -> str:
    return re.sub(r"[^a-z ]", "", (u or "").lower()).strip()


COMMON_INST_STOP = {
    "university", "institute", "technology", "of", "and", "the", "for",
    "state", "rajabhat", "campus", "college", "school", "king"
}


def corroborates(cand: dict, uni: str) -> bool:
    """True if an author affiliation string shares a meaningful token with the DB university."""
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


TOPIC_STOP = frozenset({
    "and", "the", "of", "for", "with", "using", "based", "under", "from",
    "research", "study", "studies", "analysis", "effects", "effect", "role",
    "among", "between", "through", "their", "into", "over", "more", "general",
})


def topic_tokens(text: str) -> set:
    """English content tokens from a topic/interest string (len>=4, no stop)."""
    return {t for t in _TOKEN_RE.findall(strip_accents(text or "").lower())
            if len(t) >= 4 and t not in TOPIC_STOP}


def candidate_topic_tokens(cand: dict) -> set:
    toks = set()
    for t in cand.get("topics") or []:
        toks |= topic_tokens(t.get("display_name") or "")
        sub = t.get("subfield") or {}
        toks |= topic_tokens(sub.get("display_name") or "")
        fld = t.get("field") or {}
        toks |= topic_tokens(fld.get("display_name") or "")
    return toks


def person_named(cand: dict) -> bool:
    """Reject degenerate OpenAlex author records whose display_name is a
    topic/field, not a person (observed: 'Physical and Colloid Chemistry').
    Every token must be Title-Case or a single initial."""
    toks = (cand.get("display_name") or "").split()
    if len(toks) < 2:
        return False
    return all(bool(re.fullmatch(r"[A-Z][a-z'\-]+|[A-Z]\.?", t)) for t in toks)


def topic_disambiguate(qualifying: list, interests) -> "dict | None":
    """Pick one ambiguous candidate by research-topic overlap with the row's
    own research_interests. Returns winner iff best_score >= 3 AND margin >= 2
    over runner-up; else None (stay ambiguous). Pure function, thread-safe."""
    pool = [c for c in qualifying if person_named(c)]
    if not pool:
        return None
    want = set()
    for item in interests or []:
        want |= topic_tokens(str(item))
    if not want:
        return None
    scored = sorted(
        ((len(want & candidate_topic_tokens(c)), c) for c in pool),
        key=lambda x: x[0], reverse=True)
    if not scored or scored[0][0] < 3:
        return None
    if len(scored) > 1 and scored[0][0] - scored[1][0] < 2:
        return None
    return scored[0][1]


def resolve(first: str, last: str, uni: str):
    """Return (author_dict|None, verdict). verdict ∈ {'match','no_hit','ambiguous'}."""
    cands = search_authors(f"{strip_accents(first).strip()} {strip_accents(last).strip()}")
    qualifying = qualify_candidates(first, last, cands)
    if not qualifying:
        return None, "no_hit"
    corr = [c for c in qualifying if corroborates(c, uni)]
    if corr:
        pool = corr
        pool.sort(key=lambda c: ((c.get("summary_stats") or {}).get("h_index") or 0), reverse=True)
        return pool[0], "match"
    if len(qualifying) == 1:
        # Keep a lone candidate as a low-confidence match. The payload records
        # corroborated=False so callers can review it separately from verified matches.
        return qualifying[0], "match"
    return None, "ambiguous"   # several uncorroborated people → don't guess


def qualify_candidates(first: str, last: str, cands: list) -> list:
    """Name-gate filter shared by resolve() and topic disambiguation."""
    first_clean = strip_accents(first).strip()
    last_clean = strip_accents(last).strip()
    last_toks = tokens(last_clean)
    first_toks = tokens(first_clean)
    first_collapsed = "".join(c for c in first_clean.lower() if c.isalpha())
    qualifying = []
    for c in cands or []:
        cand_toks = tokens(c.get("display_name"))
        # Must match surname token
        if not bool(last_toks & cand_toks):
            continue
        cand_given_toks = cand_toks - last_toks
        cand_given_collapsed = "".join(c for c in (c.get("display_name") or "").lower() if c.isalpha() and c not in "".join(last_toks))

        # Must match given name token, initial, or compound/hyphenated prefix
        given_match = (
            bool(first_toks & cand_toks) or
            any(t[:1] in cand_toks for t in first_toks if t) or
            any(ct[:1] in first_toks for ct in cand_given_toks if ct) or
            (first_collapsed and first_collapsed in cand_given_collapsed) or
            (cand_given_collapsed and cand_given_collapsed in first_collapsed) or
            any(ct.startswith(t) or t.startswith(ct) for ct in cand_given_toks for t in first_toks if len(ct) >= 2 and len(t) >= 2)
        )
        if given_match:
            qualifying.append(c)
    return qualifying


DISAMBIGUATE = False  # set from --disambiguate flag (module-level for worker threads)


def probe(row):
    """NETWORK ONLY — no DB access (runs in worker threads). row is a plain tuple."""
    rid, fn, ln, uni = row[:4]
    interests = row[4] if len(row) > 4 else None
    via_topic = False
    try:
        if DISAMBIGUATE:
            cands = search_authors(f"{strip_accents(fn).strip()} {strip_accents(ln).strip()}")
            qualifying = qualify_candidates(fn.strip(), ln.strip(), cands)
            if not qualifying:
                return rid, None, "no_hit", ""
            corr = [c for c in qualifying if corroborates(c, uni or "")]
            if corr:
                corr.sort(key=lambda c: ((c.get("summary_stats") or {}).get("h_index") or 0), reverse=True)
                author, verdict = corr[0], "match"
            elif len(qualifying) == 1:
                author, verdict = qualifying[0], "match"
            else:
                winner = topic_disambiguate(qualifying, interests)
                if winner is None:
                    return rid, None, "ambiguous", ""
                author, verdict, via_topic = winner, "match", True
        else:
            author, verdict = resolve(fn.strip(), ln.strip(), uni or "")
            via_topic = False
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
        "disambiguated_via_topic": via_topic,
        "first_name": fn,
        "last_name": ln,
    }
    return rid, payload, "match", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to DB (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="max faculty this invocation (0 = all)")
    ap.add_argument("--workers", type=int, default=21, help="worker threads (saturates 7 OpenAlex keys)")
    ap.add_argument("--batch", type=int, default=100, help="commit interval")
    ap.add_argument("--include-sentinel", action="store_true",
                    help="also re-probe rows marked 'not_indexed' with h_index=0 "
                         "(use after a rate-limited run; quota resets daily)")
    ap.add_argument("--disambiguate", action="store_true",
                    help="for ambiguous verdicts, pick a winner by research-topic "
                         "overlap with the row's own research_interests "
                         "(score>=3, margin>=2; else stays ambiguous)")
    args = ap.parse_args()
    global DISAMBIGUATE
    DISAMBIGUATE = args.disambiguate

    db = SessionLocal()
    # Plain column query: no ORM objects cross thread boundaries, ever.
    # --include-sentinel: re-probe rows previously marked 'not_indexed' that still
    # have h_index=0. Needed when a run was rate-limited and misses were recorded
    # against exhausted keys — quota resets daily, so yesterday's no_hit may be today's match.
    id_filter = (FacultyDB.openalex_id.is_(None)
                 if not args.include_sentinel
                 else (or_(FacultyDB.openalex_id.is_(None),
                           and_(FacultyDB.openalex_id == SENTINEL_MISS, FacultyDB.h_index == 0))))
    rows = (db.query(FacultyDB.id, FacultyDB.first_name, FacultyDB.last_name, FacultyDB.university, FacultyDB.profile_url, FacultyDB.email, FacultyDB.research_interests)
            .filter(id_filter)
            .filter(~FacultyDB.id.in_(PROTECTED_SENTINEL_IDS))
            .all())

    SLUG_PATTERN = re.compile(r"/(?:academic-staff|people|faculty|staff|teams|profile|person)/([a-zA-Z0-9_\-]+)/?", re.I)
    NOISE_SLUGS = {"index", "detail", "profile", "people", "staff", "faculty", "team", "academic-staff"}

    # romanized-only: OpenAlex keys on latin names; require surname >= 2 chars
    norm_rows = []
    for r in rows:
        fn_norm = strip_accents(r.first_name).strip() if r.first_name else ""
        ln_norm = strip_accents(r.last_name).strip() if r.last_name else ""
        if fn_norm.isascii() and ln_norm.isascii() and len(ln_norm) >= 2 and fn_norm and ln_norm:
            norm_rows.append((r.id, fn_norm, ln_norm, r.university, r.research_interests))
            continue

        extracted = None
        if r.profile_url:
            m = SLUG_PATTERN.search(r.profile_url)
            if m:
                raw_slug = m.group(1).strip().lower()
                raw_slug = re.sub(r"-(?:th|en)$", "", raw_slug)
                parts = [p for p in raw_slug.split("-") if p.isalpha() and len(p) >= 2 and p not in NOISE_SLUGS]
                if len(parts) >= 2:
                    extracted = (parts[0].title(), " ".join(parts[1:]).title())
        if not extracted and r.email and "@" in r.email:
            local = r.email.split("@")[0].lower()
            parts = [p for p in re.split(r"[\._]", local) if p.isalpha() and len(p) >= 3]
            if len(parts) >= 2:
                extracted = (parts[0].title(), " ".join(parts[1:]).title())
        if extracted:
            norm_rows.append((r.id, extracted[0], extracted[1], r.university, r.research_interests))
    rows = norm_rows
    if args.limit:
        rows = rows[: args.limit]
    print(f"Targets (openalex_id IS NULL, romanized, surname>=2): {len(rows)}", flush=True)
    if not rows:
        db.close()
        return
    if not api_healthy():
        print("✋ OpenAlex unreachable right now (keys exhausted AND polite pool throttled). "
              "Aborting before any writes so misses aren't mislabeled. Retry later — "
              "key quotas reset daily.", flush=True)
        db.close()
        return

    counts = {"match": 0, "no_hit": 0, "ambiguous": 0, "error": 0, "metric_gain": 0, "topic_pick": 0}
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
            applied_publications = max(
                fac.total_publications_count or 0,
                payload["total_publications_count"],
            )
            if (fac.first_author_count or 0) > 0 or (fac.co_author_count or 0) > 0:
                current_sum = (fac.first_author_count or 0) + (fac.co_author_count or 0)
                diff = applied_publications - current_sum
                if diff > 0:
                    fac.co_author_count = (fac.co_author_count or 0) + diff
                else:
                    applied_publications = current_sum
            fac.total_publications_count = applied_publications
            if payload.get("first_name") and payload.get("last_name"):
                if not (fac.first_name and fac.first_name.isascii()):
                    fac.first_name = payload["first_name"]
                if not (fac.last_name and fac.last_name.isascii()):
                    fac.last_name = payload["last_name"]
            rec = {"id": rid, "verdict": "match", "corroborated": payload["corroborated"],
                   "openalex_id": payload["openalex_id"],
                   "matched_author_name": payload["matched_author_name"],
                   "h_index": payload["h_index"], "total_citations": payload["total_citations"],
                   "total_publications_count": applied_publications,
                   "before": before}
            if gained:
                counts["metric_gain"] += 1
            if payload.get("disambiguated_via_topic"):
                counts["topic_pick"] += 1
                rec["disambiguated_via_topic"] = True
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
                    # keys can expire MID-run.
                    # If all keys exhausted or the API goes dark, give polite pool a minute, then stop cleanly
                    # rather than stamping 'not_indexed' onto throttle blinks.
                    if all_keys_exhausted() or not api_healthy():
                        print(f"  ⏸ API degraded or keys exhausted at {done}/{len(rows)} — waiting 60s…", flush=True)
                        time.sleep(60)
                        if not api_healthy():
                            print("  ✋ still degraded or quota exhausted — stopping this wave (resumable).", flush=True)
                            break
            else:
                # Dry-run checkpoints must preserve every verdict for review,
                # not only matches.
                entry = {"id": rid, "verdict": verdict}
                if verdict == "match":
                    entry.update({
                        "corroborated": payload["corroborated"],
                        "disambiguated_via_topic": payload.get("disambiguated_via_topic", False),
                        "matched_author_name": payload["matched_author_name"],
                        "openalex_id": payload["openalex_id"],
                        "h_index": payload["h_index"],
                    })
                    if payload.get("disambiguated_via_topic"):
                        counts["topic_pick"] += 1
                changes.append(entry)

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
