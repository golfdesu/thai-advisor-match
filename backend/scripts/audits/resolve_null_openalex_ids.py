# -*- coding: utf-8 -*-
"""
Phase 1b — find OpenAlex author IDs for faculty rows whose openalex_id is NULL (2026-09-26).

Two-factor verification (AGENTS.md §9.10), reusing remediate_bare_openalex_ids helpers:
  • Candidate search is restricted to authors affiliated with the row's university
    (filter=affiliations.institution.id:<inst>), so affiliation is verified by construction.
  • Name: the row's English first name must match the candidate's first name AND the Thai
    given name / surname initial consonants must be compatible with the candidate's name.
    Rows whose English surname was cleared (last_name NULL) are searched by first name and
    accepted only when the Thai surname's initial matches the candidate's surname.
  • Exactly one candidate must pass; ties / zero → 'not_indexed' (never guessed).
  • A candidate ID already held by another row is never re-assigned.

Accepted rows get the canonical ID, the candidate's surname (if last_name was empty),
citations/h-index/works from the author record; featured publications are then filled by
enrich_openalex_works.py.

Usage (local Docker DB only):
    python scripts/audits/resolve_null_openalex_ids.py            # dry-run → plan JSON
    python scripts/audits/resolve_null_openalex_ids.py --apply
"""
import sys
import json
import argparse
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import psycopg2.extras
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remediate_bare_openalex_ids import (  # noqa: E402
    DSN, STATE_DIR, OA_PREFIX, UNIV_EN_FALLBACK, THAI_RE,
    fetch_with_retry, split_thai_name, initial_ok,
)

PLAN_FILE = STATE_DIR / "phase1b_null_openalex_plan_2026-09-26.json"


def resolve_institution(univ_en: str) -> str | None:
    url = "https://api.openalex.org/institutions?filter=country_code:TH&search=" + urllib.parse.quote(univ_en)
    best, best_score = None, 0
    for inst in (fetch_with_retry(url) or {}).get("results", [])[:5]:
        s = fuzz.token_sort_ratio(univ_en.lower(), (inst.get("display_name") or "").lower())
        if s > best_score:
            best, best_score = inst["id"].rsplit("/", 1)[-1], s
    return best if best_score >= 90 else None


def candidate_passes(row, cand) -> bool:
    th_first, th_last = split_thai_name(row["full_name_th"])
    names = [cand.get("display_name") or ""] + (cand.get("display_name_alternatives") or [])
    first_en = (row["first_name"] or "").strip()
    last_en = (row["last_name"] or "").strip()
    for n in names:
        toks = n.replace(",", " ").split()
        if len(toks) < 2:
            continue
        c_first, c_last = toks[0], toks[-1]
        if THAI_RE.search(n):
            # Thai-script OpenAlex name: compare with the Thai name directly
            if fuzz.token_sort_ratio(f"{th_first} {th_last}", n) >= 90:
                return True
            continue
        if fuzz.ratio(first_en.lower(), c_first.lower()) < 85:
            continue
        if last_en and fuzz.ratio(last_en.lower(), c_last.lower()) < 85:
            continue
        # Thai initials must be compatible (guards against first-name-only collisions)
        if THAI_RE.search(th_first) and not initial_ok(th_first, c_first):
            continue
        if THAI_RE.search(th_last) and not initial_ok(th_last, c_last):
            continue
        if not THAI_RE.search(th_first + th_last) and \
                fuzz.token_sort_ratio(f"{th_first} {th_last}".lower(), n.lower()) < 85:
            continue
        return True
    return False


def search_row(row, inst_id):
    q = f"{row['first_name'] or ''} {row['last_name'] or ''}".strip()
    url = ("https://api.openalex.org/authors?per-page=25&search=" + urllib.parse.quote(q) +
           f"&filter=affiliations.institution.id:{inst_id}"
           "&select=id,display_name,display_name_alternatives,cited_by_count,summary_stats,works_count")
    cands = (fetch_with_retry(url) or {}).get("results", [])
    passing = [c for c in cands if candidate_passes(row, c)]
    return row["id"], passing


def main(apply: bool) -> None:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT id, university, university_th, full_name_th, first_name, last_name
                   FROM faculties WHERE openalex_id IS NULL ORDER BY id""")
    rows = cur.fetchall()
    cur.execute("SELECT openalex_id FROM faculties WHERE openalex_id LIKE %s", (OA_PREFIX + "%",))
    taken = {r["openalex_id"] for r in cur.fetchall()}

    inst_cache = {}
    for r in rows:
        u = r["university"] or UNIV_EN_FALLBACK.get(r["university_th"], "")
        if u and u not in inst_cache:
            inst_cache[u] = resolve_institution(u)
    print("institutions:", inst_cache)

    jobs = []
    plan = []
    for r in rows:
        u = r["university"] or UNIV_EN_FALLBACK.get(r["university_th"], "")
        inst = inst_cache.get(u)
        if not (r["first_name"] or "").strip() or not inst:
            plan.append({"id": r["id"], "action": "SKIP",
                         "reason": "no English first name" if inst else "institution unresolved"})
        else:
            jobs.append((r, inst))

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = dict(ex.map(lambda j: search_row(*j), jobs))

    by_id = {r["id"]: r for r in rows}
    assigned = set()
    for rid, passing in results.items():
        r = by_id[rid]
        entry = {"id": rid, "full_name_th": r["full_name_th"],
                 "en": f"{r['first_name']} {r['last_name'] or ''}".strip()}
        ids = {c["id"] for c in passing}
        if len(ids) != 1:
            entry.update(action="NOT_INDEXED", reason=f"{len(ids)} passing candidates",
                         cands=[c["display_name"] for c in passing][:3])
        else:
            c = passing[0]
            if c["id"] in taken or c["id"] in assigned:
                entry.update(action="NOT_INDEXED", reason="candidate ID already held by another row",
                             cands=[c["display_name"]])
            else:
                assigned.add(c["id"])
                entry.update(action="ASSIGN", oa=c["id"], oa_name=c["display_name"],
                             citations=c.get("cited_by_count") or 0,
                             h_index=(c.get("summary_stats") or {}).get("h_index") or 0,
                             works=c.get("works_count") or 0)
        plan.append(entry)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PLAN_FILE.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {}
    for e in plan:
        counts[e["action"]] = counts.get(e["action"], 0) + 1
    print(f"plan: {counts} → {PLAN_FILE.name}")
    if not apply:
        print("DRY-RUN only — re-run with --apply to execute.")
        return

    for e in plan:
        if e["action"] == "ASSIGN":
            last = e["oa_name"].replace(",", " ").split()[-1]
            cur.execute("""UPDATE faculties SET openalex_id = %s,
                               total_citations = GREATEST(coalesce(total_citations,0), %s),
                               h_index = GREATEST(coalesce(h_index,0), %s),
                               total_publications_count = GREATEST(coalesce(total_publications_count,0), %s),
                               last_name = CASE WHEN coalesce(last_name,'') = '' THEN %s ELSE last_name END
                           WHERE id = %s AND openalex_id IS NULL""",
                        (e["oa"], e["citations"], e["h_index"], e["works"], last, e["id"]))
        elif e["action"] == "NOT_INDEXED":
            cur.execute("UPDATE faculties SET openalex_id = 'not_indexed' WHERE id = %s AND openalex_id IS NULL",
                        (e["id"],))
    conn.commit()
    cur.close(); conn.close()
    print("APPLIED.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Phase 1b: two-factor OpenAlex ID resolution for NULL rows")
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
