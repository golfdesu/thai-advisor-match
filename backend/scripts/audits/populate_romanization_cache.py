# -*- coding: utf-8 -*-
"""
Populate Romanization Cache for all remaining Thai faculty names.
Uses Gemini Flash to Romanize names into first_name and last_name.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from google import genai
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.enrich_thai_faculty_openalex import (
    load_romanization_cache,
    save_romanization_cache,
    generate_romanization_batch,
    PROTECTED_SENTINEL_IDS
)

def main():
    cache = load_romanization_cache()
    print(f"Loaded existing cache with {len(cache)} entries.")

    db = SessionLocal()
    try:
        targets = (
            db.query(
                FacultyDB.id,
                FacultyDB.full_name_th,
                FacultyDB.first_name,
                FacultyDB.last_name
            )
            .filter((FacultyDB.openalex_id.is_(None)) | (FacultyDB.openalex_id == "not_indexed"))
            .filter(~FacultyDB.id.in_(PROTECTED_SENTINEL_IDS))
            .all()
        )

        needed = []
        for r in targets:
            rid = r.id
            if rid in cache:
                continue
            fn = (r.first_name or "").strip()
            ln = (r.last_name or "").strip()
            if fn.isascii() and len(fn) >= 2 and ln.isascii() and len(ln) >= 2:
                cache[rid] = {"first_name": fn, "last_name": ln}
                continue

            existing_first = fn if (fn.isascii() and len(fn) >= 2) else None
            needed.append({
                "id": rid,
                "full_name_th": r.full_name_th or "",
                "existing_first_name": existing_first
            })

        print(f"Total needed transliterations: {len(needed)}")
        if not needed:
            print("All records already transliterated!")
            save_romanization_cache(cache)
            return

        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEYS", "").split(",")[0]
        if not gemini_key:
            print("ERROR: GEMINI_API_KEY not found!")
            return

        client = genai.Client(api_key=gemini_key)
        chunk_size = 50

        for i in range(0, len(needed), chunk_size):
            chunk = needed[i : i + chunk_size]
            pct = ((i + len(chunk)) / len(needed)) * 100
            print(f"[{i + len(chunk)}/{len(needed)}] ({pct:.1f}%) Transliterating...", flush=True)
            results = generate_romanization_batch(chunk, client)
            for res in results:
                fid = res["id"]
                cache[fid] = {
                    "first_name": res.get("first_name", ""),
                    "last_name": res.get("last_name", "")
                }
            save_romanization_cache(cache)
            time.sleep(0.3)

        print(f"✅ Finished! Cache now has {len(cache)} entries.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
