# -*- coding: utf-8 -*-
"""
Audit OpenAlex Affiliations Across All Faculty Records
======================================================
Queries OpenAlex author metadata in 50-ID batches across 7 multiplexed API keys
to verify whether faculty institutional affiliations match their database assignments.

Detects:
1. Perfect match: last_known_institutions matches assigned university_th.
2. Cross-university transfers / crawler mismatches: last_known_institutions
   points to a different Thai university.
3. Foreign / Unlisted institutions: Ph.D. institutions, international labs, etc.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
SCRIPTS_DIR = BACKEND_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.db_models import FacultyDB
from scripts.fetch_openalex_publication_metrics import (
    get_next_api_key,
    append_api_key,
    OPENALEX_HEADERS,
    SSL_CTX,
)
from scripts.audits.clean_prototype_synthetic_faculties import INST_TO_THAI_UNIV

CACHE_FILE = BACKEND_DIR / "data" / "agent_states" / "openalex_affiliations_cache.json"


def normalize_inst_token(name: str | None) -> set[str]:
    if not name:
        return set()
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", name.lower())
    tokens = set(cleaned.split())
    stopwords = {"university", "of", "technology", "the", "institute", "and", "college", "school", "national", "thailand"}
    return {t for t in tokens if len(t) > 2 and t not in stopwords}


def match_thai_univ(inst_name: str | None) -> tuple[str, str] | None:
    """Matches an OpenAlex institution display_name to (univ_th, univ_en)."""
    if not inst_name:
        return None
    for eng_name, (th_u, en_u) in INST_TO_THAI_UNIV.items():
        if eng_name.lower() in inst_name.lower():
            return th_u, en_u
    return None


def run_audit(limit: int = 0, batch_size: int = 50, workers: int = 7):
    print("=================================================================", flush=True)
    print("🔍 AUDITING OPENALEX AFFILIATIONS ACROSS ALL FACULTY", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    try:
        query = db.query(
            FacultyDB.id,
            FacultyDB.full_name_th,
            FacultyDB.first_name,
            FacultyDB.last_name,
            FacultyDB.university_th,
            FacultyDB.university,
            FacultyDB.faculty_th,
            FacultyDB.department_th,
            FacultyDB.email,
            FacultyDB.openalex_id
        ).filter(FacultyDB.openalex_id.like("%/A%"))

        if limit > 0:
            query = query.limit(limit)

        records = query.all()
        print(f"Total faculty records to audit: {len(records):,}", flush=True)

        # Load existing cache
        cache: dict[str, dict] = {}
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                print(f"Loaded {len(cache):,} existing author metadata entries from cache.", flush=True)
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}", flush=True)

        # Identify missing IDs to fetch
        missing_ids = [r.openalex_id for r in records if r.openalex_id not in cache]
        print(f"Missing OpenAlex metadata to fetch: {len(missing_ids):,}", flush=True)

        if missing_ids:
            batches = [missing_ids[i:i + batch_size] for i in range(0, len(missing_ids), batch_size)]
            print(f"Fetching {len(missing_ids):,} authors in {len(batches)} batches using {workers} workers...", flush=True)

            def fetch_oa_batch(b: list[str]) -> list[dict]:
                short_ids = [x.split("/")[-1] for x in b]
                id_filter = "|".join(short_ids)
                base_url = f"https://api.openalex.org/authors?filter=openalex_id:{id_filter}&select=id,display_name,last_known_institutions,affiliations&per_page=50"
                for attempt in range(4):
                    key = get_next_api_key()
                    url = append_api_key(base_url, key)
                    try:
                        req = urllib.request.Request(url, headers=OPENALEX_HEADERS)
                        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
                            data = json.loads(resp.read().decode("utf-8"))
                            return data.get("results", []) or []
                    except Exception as e:
                        time.sleep(0.5 * (attempt + 1))
                return []

            t0 = time.time()
            done_batches = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(fetch_oa_batch, b): b for b in batches}
                for fut in as_completed(futures):
                    res_list = fut.result()
                    for item in res_list:
                        raw_id = item.get("id")
                        if not raw_id:
                            continue
                        full_id = raw_id if raw_id.startswith("http") else f"https://openalex.org/{raw_id}"
                        cache[full_id] = {
                            "display_name": item.get("display_name"),
                            "last_known_institutions": [
                                {
                                    "id": x.get("id"),
                                    "display_name": x.get("display_name"),
                                    "country_code": x.get("country_code"),
                                }
                                for x in (item.get("last_known_institutions") or [])
                                if x
                            ],
                            "affiliations": [
                                {
                                    "institution": (x.get("institution") or {}).get("display_name"),
                                    "years": x.get("years") or [],
                                }
                                for x in (item.get("affiliations") or [])
                                if x
                            ]
                        }
                    done_batches += 1
                    if done_batches % 20 == 0 or done_batches == len(batches):
                        elapsed = time.time() - t0
                        pct = (done_batches / len(batches)) * 100
                        print(f"  [{done_batches}/{len(batches)}] ({pct:.1f}%) - Cached: {len(cache):,} ({elapsed:.1f}s)", flush=True)

            # Save updated cache to disk
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved updated cache with {len(cache):,} authors to {CACHE_FILE}", flush=True)

        # -------------------------------------------------------------
        # 3. Analyze Affiliation Alignment
        # -------------------------------------------------------------
        print("\n--- Cross-University Affiliation Analysis ---", flush=True)
        exact_matches = 0
        international_only = 0
        no_institution = 0
        conflicts = []

        for r in records:
            meta = cache.get(r.openalex_id)
            if not meta:
                no_institution += 1
                continue

            lkis = meta.get("last_known_institutions") or []
            if not lkis:
                no_institution += 1
                continue

            # Check if any last known institution matches assigned university
            matched_assigned = False
            thai_institutions_found = []

            for inst in lkis:
                disp = inst.get("display_name")
                m = match_thai_univ(disp)
                if m:
                    th_u, en_u = m
                    thai_institutions_found.append((th_u, en_u, disp))
                    if th_u == r.university_th:
                        matched_assigned = True

            if matched_assigned:
                exact_matches += 1
            elif thai_institutions_found:
                # OpenAlex lists Thai institutions, but NONE match the assigned university!
                conflicts.append({
                    "id": r.id,
                    "name": r.full_name_th,
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "assigned_univ": r.university_th,
                    "faculty": r.faculty_th,
                    "department": r.department_th,
                    "email": r.email,
                    "openalex_id": r.openalex_id,
                    "oa_thai_institutions": thai_institutions_found,
                    "all_oa_institutions": [i.get("display_name") for i in lkis],
                })
            else:
                # Only foreign / non-Thai institutions found
                international_only += 1

        print(f"\nResults across {len(records):,} records:", flush=True)
        print(f"  ✅ Exact Matches (Assigned University = OpenAlex): {exact_matches:,}", flush=True)
        print(f"  🌐 International / Foreign Institutions Only:     {international_only:,}", flush=True)
        print(f"  ❓ No Institutional Affiliation in OpenAlex:      {no_institution:,}", flush=True)
        print(f"  ⚠️ Cross-University Institutional Conflicts:      {len(conflicts):,}", flush=True)

        if conflicts:
            conflict_file = BACKEND_DIR / "data" / "agent_states" / "openalex_affiliation_conflicts.json"
            with open(conflict_file, "w", encoding="utf-8") as f:
                json.dump(conflicts, f, ensure_ascii=False, indent=2)
            print(f"\nSaved {len(conflicts)} conflicts to: {conflict_file}", flush=True)

            print("\nSample conflicts (first 10):", flush=True)
            for c in conflicts[:10]:
                print(f"  - [{c['id']}] {c['name']} (Assigned: {c['assigned_univ']}) -> OpenAlex Thai Inst: {[x[0] for x in c['oa_thai_institutions']]} | Email: {c['email']}", flush=True)

        return conflicts

    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    run_audit(limit=args.limit)
