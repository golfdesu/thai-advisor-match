# -*- coding: utf-8 -*-
"""
Resolve Missing Surnames for 486 Faculty Records
Uses gemini-3.5-flash-lite to transliterate Thai surnames based on authentic full_name_th.
Saves to thai_romanization_cache.json and updates faculties table.
"""
import os
import sys
import json
import time
import re
from pathlib import Path
from google import genai
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

CACHE_PATH = Path("/app/data/agent_states/thai_romanization_cache.json")
if not CACHE_PATH.exists():
    CACHE_PATH = Path("backend/data/agent_states/thai_romanization_cache.json")

def main():
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("ERROR: GEMINI_API_KEY is not set!")
        return

    client = genai.Client(api_key=gemini_key)
    db = SessionLocal()

    try:
        # Load cache
        cache = {}
        if CACHE_PATH.exists():
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
        print(f"Loaded existing cache with {len(cache)} entries.")

        # Find targets with missing last_name
        targets = db.query(FacultyDB).filter(
            (FacultyDB.last_name.is_(None)) | (FacultyDB.last_name == "")
        ).all()
        print(f"Total targets with missing last_name: {len(targets)}")

        needed = []
        for t in targets:
            fn = (t.first_name or "").strip()
            needed.append({
                "id": t.id,
                "full_name_th": t.full_name_th or "",
                "existing_first_name": fn
            })

        batch_size = 50
        updated_count = 0

        for i in range(0, len(needed), batch_size):
            chunk = needed[i : i + batch_size]
            print(f"[{i + len(chunk)}/{len(needed)}] Transliterating surnames with gemini-3.5-flash-lite...", flush=True)

            prompt = f"""Transliterate the following Thai scholar names into English Latin alphabet (first_name, last_name).
Rules:
1. Retain existing_first_name as first_name and transliterate the Thai surname from full_name_th as last_name.
2. Strip all titles (ผศ., รศ., ศ., อ., ดร., etc.).
3. Ensure outputs contain ONLY pure ASCII characters [a-zA-Z -]. No Thai characters.
4. Return JSON array of objects with keys: "id", "first_name", "last_name".

Input:
{json.dumps(chunk, ensure_ascii=False)}
"""
            max_retries = 3
            data = None
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=prompt,
                        config={"response_mime_type": "application/json"}
                    )
                    data = json.loads(response.text)
                    break
                except Exception as e:
                    print(f"  Attempt {attempt+1} failed: {e}. Retrying in 2s...")
                    time.sleep(2)

            if not data:
                print(f"  ERROR: Failed to transliterate chunk {i}..{i+len(chunk)}")
                continue

            for item in data:
                fid = item.get("id")
                fn = re.sub(r"[^a-zA-Z\s\-]", "", str(item.get("first_name", ""))).strip().title()
                ln = re.sub(r"[^a-zA-Z\s\-]", "", str(item.get("last_name", ""))).strip().title()
                if fn and ln:
                    cache[fid] = {"first_name": fn, "last_name": ln}
                    fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
                    if fac:
                        fac.first_name = fn
                        fac.last_name = ln
                        updated_count += 1

            # Commit batch
            db.commit()
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            time.sleep(0.5)

        print(f"Successfully updated {updated_count} records with verified surnames!")
        print(f"Cache now has {len(cache)} entries.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
