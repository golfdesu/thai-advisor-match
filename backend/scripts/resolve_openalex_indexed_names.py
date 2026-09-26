# -*- coding: utf-8 -*-
"""
Resolve Official Latin Names for OpenAlex-Indexed Faculty
Queries OpenAlex API using batch author IDs to retrieve authoritative display_name.
Updates first_name, last_name, and caches in thai_romanization_cache.json.
"""
import sys
import os
import json
import urllib.request
import urllib.parse
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

CACHE_PATH = Path("/app/data/agent_states/thai_romanization_cache.json")
if not CACHE_PATH.exists():
    CACHE_PATH = BACKEND_DIR / "data" / "agent_states" / "thai_romanization_cache.json"

def fetch_openalex_authors_batch(author_ids: list[str]) -> dict:
    """
    Fetches up to 50 authors in one batch from OpenAlex API.
    Returns mapping from full ID (or short ID) -> (first_name, last_name)
    """
    short_ids = [aid.split("/")[-1] for aid in author_ids]
    pipe_filter = "|".join(short_ids)
    url = f"https://api.openalex.org/authors?filter=openalex:{pipe_filter}&per-page=50"
    req = urllib.request.Request(url, headers={"User-Agent": "ThaiEduCenter/1.0 (mailto:admin@thaieducenter.org)"})

    results = {}
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("results", []):
                full_id = item.get("id")
                short_id = full_id.split("/")[-1] if full_id else ""
                disp = item.get("display_name", "").strip()
                # Check display_name or alternatives for Latin name
                latin_name = None
                if disp and disp.isascii() and " " in disp:
                    latin_name = disp
                else:
                    for alt in item.get("display_name_alternatives", []):
                        if alt and alt.isascii() and " " in alt:
                            # if format "Last, First"
                            if "," in alt:
                                parts = [p.strip() for p in alt.split(",", 1)]
                                latin_name = f"{parts[1]} {parts[0]}"
                            else:
                                latin_name = alt
                            break

                if latin_name:
                    parts = latin_name.split()
                    fn = parts[0].title()
                    ln = " ".join(parts[1:]).title()
                    results[full_id] = (fn, ln)
                    results[short_id] = (fn, ln)
    except Exception as e:
        print(f"Error fetching batch: {e}")

    return results

def main():
    db = SessionLocal()
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)

    try:
        targets = db.query(FacultyDB).filter(
            ((FacultyDB.first_name.op("~")("[ก-๙]")) | (FacultyDB.last_name.op("~")("[ก-๙]"))),
            FacultyDB.openalex_id.isnot(None),
            (FacultyDB.openalex_id.like("http%") | FacultyDB.openalex_id.like("A%"))
        ).all()

        print(f"Found {len(targets)} OpenAlex-indexed faculty records with Thai in EN fields.")

        aids = [t.openalex_id for t in targets]
        chunk_size = 40
        resolved_count = 0

        for i in range(0, len(targets), chunk_size):
            chunk = targets[i : i + chunk_size]
            chunk_aids = [t.openalex_id for t in chunk]
            name_map = fetch_openalex_authors_batch(chunk_aids)

            for fac in chunk:
                short_id = fac.openalex_id.split("/")[-1]
                if fac.openalex_id in name_map or short_id in name_map:
                    fn, ln = name_map.get(fac.openalex_id) or name_map.get(short_id)
                    fac.first_name = fn
                    fac.last_name = ln
                    cache[fac.id] = {"first_name": fn, "last_name": ln}
                    resolved_count += 1
                    print(f"  [{fac.id}] Grounded via OpenAlex: {fn} {ln} ({fac.full_name_th})")

            db.commit()

        if CACHE_PATH.exists():
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

        print(f"Successfully grounded {resolved_count}/{len(targets)} faculty names from OpenAlex official records!")

    finally:
        db.close()

if __name__ == "__main__":
    main()
