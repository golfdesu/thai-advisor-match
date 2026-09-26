# -*- coding: utf-8 -*-
"""
Phase 3 — verify scholars_unassigned candidates for promotion into faculties (2026-09-26, DRY-RUN).

scholars_unassigned holds OpenAlex co-authors bucketed by a university name, which is noisy
(e.g. the US 'NIDA' — National Institute on Drug Abuse — collides with Thailand's NIDA).
A candidate is marked PROMOTABLE only when, on the live OpenAlex author record:
  • last_known_institutions contains the resolved Thai institution ID (country_code TH), and
    every last-known institution is in Thailand (excludes foreign co-authors with a past visit)
  • h_index >= 3 and works_count >= 8
  • its OpenAlex ID is not already held by a faculties row
Everything else → QUARANTINE with a reason. Writes a plan JSON only; nothing is inserted.

Usage:
    python scripts/audits/verify_unassigned_promotion.py
"""
import sys
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import psycopg2.extras

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remediate_bare_openalex_ids import DSN, STATE_DIR, OA_PREFIX, fetch_with_retry  # noqa: E402
from resolve_null_openalex_ids import resolve_institution  # noqa: E402

TARGET_RE = "(ราชภัฏ|รามคำแหง|บัณฑิตพัฒนบริหาร|ราชมงคลพระนคร|ราชมงคลกรุงเทพ|สวนดุสิต|รังสิต|หอการค้า|ศรีปทุม|กรุงเทพ)"
PLAN_FILE = STATE_DIR / "phase3_unassigned_promotion_plan_2026-09-26.json"


def fetch_chunk(ids):
    url = ("https://api.openalex.org/authors?per-page=50&filter=openalex:" +
           "|".join(i.rsplit("/", 1)[-1] for i in ids) +
           "&select=id,display_name,last_known_institutions,summary_stats,works_count")
    return (fetch_with_retry(url) or {}).get("results", [])


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT id, university, university_th, openalex_id, full_name_th
                   FROM scholars_unassigned
                   WHERE university_th ~ %s AND openalex_id LIKE 'https://openalex.org/A%%'
                     AND h_index >= 3 AND total_publications_count >= 8""", (TARGET_RE,))
    rows = cur.fetchall()
    cur.execute("SELECT openalex_id FROM faculties WHERE openalex_id LIKE %s", (OA_PREFIX + "%",))
    taken = {r["openalex_id"] for r in cur.fetchall()}

    inst = {}
    for u in sorted({r["university"] for r in rows if r["university"]}):
        inst[u] = resolve_institution(u)
    ids = sorted({r["openalex_id"] for r in rows})
    with ThreadPoolExecutor(max_workers=6) as ex:
        authors = {a["id"]: a for res in ex.map(fetch_chunk, [ids[i:i + 50] for i in range(0, len(ids), 50)])
                   for a in res}

    plan, stats = [], Counter()
    for r in rows:
        a = authors.get(r["openalex_id"])
        target = inst.get(r["university"])
        e = {"id": r["id"], "university_th": r["university_th"], "oa": r["openalex_id"]}
        if not target:
            e.update(action="QUARANTINE", reason="institution unresolved")
        elif not a:
            e.update(action="QUARANTINE", reason="author not found")
        elif r["openalex_id"] in taken:
            e.update(action="QUARANTINE", reason="OpenAlex ID already in faculties")
        else:
            lki = a.get("last_known_institutions") or []
            lk_ids = {i["id"].rsplit("/", 1)[-1] for i in lki}
            all_th = bool(lki) and all(i.get("country_code") == "TH" for i in lki)
            h = (a.get("summary_stats") or {}).get("h_index") or 0
            if target not in lk_ids:
                e.update(action="QUARANTINE", reason="target not in last_known_institutions")
            elif not all_th:
                e.update(action="QUARANTINE", reason="has non-Thai last-known institution")
            elif h < 3 or (a.get("works_count") or 0) < 8:
                e.update(action="QUARANTINE", reason="below h/works threshold")
            else:
                e.update(action="PROMOTABLE", oa_name=a["display_name"])
        stats[(e["action"], e.get("reason", ""))] += 1
        plan.append(e)

    PLAN_FILE.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print("institutions:", {k: v for k, v in inst.items()})
    for k, v in stats.most_common():
        print(k, v)
    by_u = Counter(e["university_th"] for e in plan if e["action"] == "PROMOTABLE")
    print("promotable by university:", dict(by_u.most_common()))


if __name__ == "__main__":
    main()
