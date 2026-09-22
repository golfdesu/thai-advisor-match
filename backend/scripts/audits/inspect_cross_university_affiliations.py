# -*- coding: utf-8 -*-
"""
Inspect Cross-University Scholar Affiliations (2026-09-22)

Audits all 2,718 cross-university duplicate scholars to determine their
true authentic current institution using OpenAlex last_known_institutions,
publication affiliation timeline, and active institutional email signals.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Adjust pythonpath to find backend app
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import engine
from app.core.university_canonicalizer import canonicalize_university_th, get_university_dedup_key
from sqlalchemy import text
from scripts.fetch_openalex_publication_metrics import (
    get_next_api_key,
    append_api_key,
    OPENALEX_HEADERS,
    SSL_CTX,
)


def normalize_inst_token(name: str | None) -> set[str]:
    if not name:
        return set()
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", name.lower())
    tokens = set(cleaned.split())
    stopwords = {"university", "of", "technology", "the", "institute", "and", "college", "school", "national", "thailand"}
    return {t for t in tokens if len(t) > 2 and t not in stopwords}


def match_institutions(inst_a: str | None, inst_b: str | None) -> bool:
    if not inst_a or not inst_b:
        return False
    toks_a = normalize_inst_token(inst_a)
    toks_b = normalize_inst_token(inst_b)
    if not toks_a or not toks_b:
        return False
    # If any distinctive university token matches (e.g. 'chulalongkorn', 'mahidol', 'kasetsart', 'chiang', 'mai', 'walailak')
    return bool(toks_a & toks_b)


def run_cross_university_inspection():
    print("=== 🔍 CROSS-UNIVERSITY SCHOLAR AFFILIATION AUDIT ===", flush=True)

    # 1. Extract the 2,718 cross-university authors
    with engine.connect() as conn:
        rows = conn.execute(text("""
            WITH dup_cross AS (
                SELECT openalex_id
                FROM faculties
                WHERE openalex_id LIKE '%/A%'
                  AND first_name IS NOT NULL AND first_name != ''
                  AND last_name IS NOT NULL AND last_name != ''
                GROUP BY openalex_id, LOWER(TRIM(first_name)), LOWER(TRIM(last_name))
                HAVING COUNT(DISTINCT university) > 1
            )
            SELECT f.openalex_id, f.id, f.university, f.university_th, f.full_name_th,
                   f.first_name, f.last_name, f.email, f.faculty_th, f.department_th,
                   f.total_citations, f.h_index
            FROM faculties f
            JOIN dup_cross d ON f.openalex_id = d.openalex_id
            ORDER BY f.openalex_id, f.id;
        """)).fetchall()

    by_oa = defaultdict(list)
    for r in rows:
        by_oa[r[0]].append({
            "id": r[1],
            "university": r[2],
            "university_th": r[3],
            "full_name_th": r[4],
            "first_name": r[5],
            "last_name": r[6],
            "email": r[7],
            "faculty_th": r[8],
            "department_th": r[9],
            "total_citations": r[10],
            "h_index": r[11],
        })

    print(f"Extracted {len(by_oa):,} unique OpenAlex authors across {len(rows):,} database rows.", flush=True)

    # 2. Divide into batches of 50 IDs
    oa_ids = list(by_oa.keys())
    batch_size = 50
    batches = [oa_ids[i:i + batch_size] for i in range(0, len(oa_ids), batch_size)]
    print(f"Divided into {len(batches)} batches of up to {batch_size} IDs. Fetching via 7 multiplexed API keys...", flush=True)

    oa_metadata: dict[str, dict] = {}

    def fetch_batch(batch: list[str]) -> list[dict]:
        short_ids = [x.split("/")[-1] for x in batch]
        id_filter = "|".join(short_ids)
        base_url = f"https://api.openalex.org/authors?filter=openalex_id:{id_filter}&select=id,display_name,last_known_institutions,affiliations&per_page=50"

        for attempt in range(3):
            key = get_next_api_key()
            url = append_api_key(base_url, key)
            try:
                req = urllib.request.Request(url, headers=OPENALEX_HEADERS)
                with urllib.request.urlopen(req, timeout=12, context=SSL_CTX) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("results", [])
            except Exception as e:
                time.sleep(0.5 * (attempt + 1))
        return []

    start_t = time.time()
    completed_batches = 0
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = {pool.submit(fetch_batch, b): b for b in batches}
        for fut in as_completed(futures):
            res_list = fut.result()
            for a in res_list:
                full_id = a.get("id")
                if full_id:
                    if not full_id.startswith("http"):
                        full_id = f"https://openalex.org/{full_id}"
                    oa_metadata[full_id] = {
                        "display_name": a.get("display_name"),
                        "last_known_institutions": [
                            {"id": x.get("id"), "display_name": x.get("display_name"), "country_code": x.get("country_code")}
                            for x in (a.get("last_known_institutions") or [])
                        ],
                        "affiliations": [
                            {
                                "institution": x.get("institution", {}).get("display_name"),
                                "years": x.get("years", [])
                            }
                            for x in (a.get("affiliations") or [])
                        ]
                    }
            completed_batches += 1
            if completed_batches % 10 == 0 or completed_batches == len(batches):
                print(f"  Progress: [{completed_batches}/{len(batches)}] batches ({len(oa_metadata)} authors resolved)", flush=True)

    elapsed = time.time() - start_t
    print(f"OpenAlex fetch completed in {elapsed:.1f}s. Resolved {len(oa_metadata):,} of {len(oa_ids):,} authors.\n", flush=True)

    # 3. Disambiguate Current Authentic Institution for each of the 2,718 scholars
    analysis_report = []

    counts = {
        "total_scholars": len(by_oa),
        "total_db_rows": len(rows),
        "exact_single_email_winner": 0,
        "lki_matched_winner": 0,
        "transferred_career_movement": 0,
        "multiple_emails": 0,
        "no_email_resolved_by_lki": 0,
        "ambiguous_pending_manual": 0,
    }

    university_ghost_counts = defaultdict(int)

    for oa_id, db_records in by_oa.items():
        meta = oa_metadata.get(oa_id) or {}
        lkis = meta.get("last_known_institutions") or []
        lki_names = [x.get("display_name") for x in lkis if x.get("display_name")]
        affs = meta.get("affiliations") or []

        # Map each university to its latest publication year in OpenAlex
        uni_latest_year = defaultdict(int)
        for af in affs:
            inst_name = af.get("institution")
            years = af.get("years") or []
            if inst_name and years:
                max_yr = max(years)
                for rec in db_records:
                    if match_institutions(rec["university"], inst_name):
                        if max_yr > uni_latest_year[rec["university"]]:
                            uni_latest_year[rec["university"]] = max_yr

        # Analyze DB signals
        recs_with_email = [r for r in db_records if r["email"] and "@" in r["email"]]
        recs_with_thai = [r for r in db_records if r["full_name_th"] and any("฀" <= c <= "๿" for c in r["full_name_th"])]

        winner_id = None
        winner_reason = ""
        current_institution = None

        # Case 1: Exactly 1 record has official email
        if len(recs_with_email) == 1:
            winner = recs_with_email[0]
            winner_id = winner["id"]
            current_institution = winner["university"]
            winner_reason = "official_email_tenure"
            counts["exact_single_email_winner"] += 1

            # Check if LKI also confirms
            lki_matches = [name for name in lki_names if match_institutions(winner["university"], name)]
            if lki_matches:
                winner_reason = "email_and_lki_converged"
                counts["lki_matched_winner"] += 1

        # Case 2: No records have email, but OpenAlex LKI matches exactly 1 of the universities
        elif len(recs_with_email) == 0:
            lki_matched_recs = [r for r in db_records if any(match_institutions(r["university"], lki_name) for lki_name in lki_names)]
            if len(lki_matched_recs) == 1:
                winner = lki_matched_recs[0]
                winner_id = winner["id"]
                current_institution = winner["university"]
                winner_reason = "openalex_last_known_institution"
                counts["no_email_resolved_by_lki"] += 1
            elif len(lki_matched_recs) == 0 and uni_latest_year:
                # Pick the university with the most recent publication year
                best_rec = max(db_records, key=lambda r: uni_latest_year[r["university"]])
                if uni_latest_year[best_rec["university"]] > 0:
                    winner_id = best_rec["id"]
                    current_institution = best_rec["university"]
                    winner_reason = f"latest_publication_year_{uni_latest_year[best_rec['university']]}"
                    counts["transferred_career_movement"] += 1
                else:
                    winner_reason = "ambiguous_no_email_no_lki_match"
                    counts["ambiguous_pending_manual"] += 1
            else:
                winner_reason = "ambiguous_multiple_lki_matches"
                counts["ambiguous_pending_manual"] += 1

        # Case 3: Multiple records have email (Career transfer between universities)
        else:
            counts["multiple_emails"] += 1
            # Disambiguate by latest publication year or OpenAlex LKI
            lki_matched_recs = [r for r in recs_with_email if any(match_institutions(r["university"], lki_name) for lki_name in lki_names)]
            if len(lki_matched_recs) == 1:
                winner = lki_matched_recs[0]
                winner_id = winner["id"]
                current_institution = winner["university"]
                winner_reason = "career_transfer_resolved_by_lki"
                counts["transferred_career_movement"] += 1
            elif uni_latest_year:
                best_rec = max(recs_with_email, key=lambda r: uni_latest_year[r["university"]])
                winner_id = best_rec["id"]
                current_institution = best_rec["university"]
                winner_reason = f"career_transfer_resolved_by_year_{uni_latest_year[best_rec['university']]}"
                counts["transferred_career_movement"] += 1
            else:
                winner_id = recs_with_email[0]["id"]
                current_institution = recs_with_email[0]["university"]
                winner_reason = "career_transfer_fallback_primary_email"

        # Record ghost records for deletion/merging
        ghost_ids = []
        if winner_id:
            for r in db_records:
                if r["id"] != winner_id:
                    ghost_ids.append(r["id"])
                    university_ghost_counts[r["university"]] += 1

        analysis_report.append({
            "openalex_id": oa_id,
            "scholar_name": f"{db_records[0]['first_name']} {db_records[0]['last_name']}",
            "winner_id": winner_id,
            "current_institution": current_institution,
            "winner_reason": winner_reason,
            "openalex_last_known_institutions": lki_names,
            "ghost_ids": ghost_ids,
            "db_records": [
                {
                    "id": r["id"],
                    "university": r["university"],
                    "email": r["email"],
                    "full_name_th": r["full_name_th"],
                    "department_th": r["department_th"],
                    "latest_oa_year": uni_latest_year[r["university"]],
                }
                for r in db_records
            ]
        })

    # Save detailed JSON report
    out_path = Path("backend/data/agent_states/cross_university_affiliations_audit.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "counts": counts,
            "top_ghost_universities": dict(sorted(university_ghost_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
            "scholars": analysis_report
        }, f, ensure_ascii=False, indent=2)

    print(f"=== 📊 AFFILIATION DISAMBIGUATION RESULTS ===")
    print(f"Total Cross-University Scholars Audited: {counts['total_scholars']:,}")
    print(f"Total Related Database Rows: {counts['total_db_rows']:,}")
    print(f"1. Single Official Email Winner: {counts['exact_single_email_winner']:,} ({counts['exact_single_email_winner']/counts['total_scholars']*100:.1f}%)")
    print(f"   └─ Both Email & OpenAlex LKI Converged: {counts['lki_matched_winner']:,} scholars (100% verified)")
    print(f"2. Resolved by OpenAlex LKI (when DB had no email): {counts['no_email_resolved_by_lki']:,} scholars")
    print(f"3. Career Movement / Transferred Scholars (timeline resolved): {counts['transferred_career_movement']:,} scholars")
    print(f"4. Multiple Active Emails: {counts['multiple_emails']} scholars")
    print(f"5. Ambiguous / Pending Manual Review: {counts['ambiguous_pending_manual']} scholars")
    print(f"\nTotal Confirmed Current Institutions: {counts['total_scholars'] - counts['ambiguous_pending_manual']:,} / {counts['total_scholars']:,} ({(counts['total_scholars'] - counts['ambiguous_pending_manual'])/counts['total_scholars']*100:.1f}%)")
    print(f"Total Identified Ghost Rows (to be merged/purged): {sum(university_ghost_counts.values()):,} rows")
    print(f"\nTop Universities harboring ghost duplicate rows:")
    for u, cnt in sorted(university_ghost_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {u}: {cnt} ghost rows")
    print(f"\nDetailed report saved to: {out_path}", flush=True)


if __name__ == "__main__":
    run_cross_university_inspection()
