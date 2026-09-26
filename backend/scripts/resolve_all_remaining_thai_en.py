# -*- coding: utf-8 -*-
"""
Resolve All Remaining Thai in EN Fields
Truth-seeking pipeline:
1. For records with openalex_id (A...), fetch author from OpenAlex API.
2. For records needing transliteration, use gemini-3.5-flash-lite with RTGS rules to extract clean Latin first_name and last_name.
3. Update faculties table and persist in thai_romanization_cache.json.
"""
import os
import sys
import json
import time
import re
import urllib.request
from pathlib import Path
from google import genai

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

def clean_ascii_name(text: str) -> str:
    """Strips any non-ascii character except hyphen and space."""
    cleaned = re.sub(r"[^a-zA-Z\s\-]", "", str(text)).strip()
    return " ".join(cleaned.split()).title()

def main():
    # Load .env if present
    env_paths = [Path("/app/.env"), BACKEND_DIR / ".env"]
    for p in env_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ or not os.environ[k]:
                            os.environ[k] = v

    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
    if gemini_key and gemini_key not in keys:
        keys.insert(0, gemini_key)

    if not keys:
        print("ERROR: No GEMINI API key found!")
        return

    print(f"Loaded {len(keys)} Gemini API keys.")
    client_idx = 0
    client = genai.Client(api_key=keys[client_idx])

    db = SessionLocal()

    # Load cache
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    print(f"Loaded existing cache with {len(cache)} entries.")

    try:
        targets = db.query(FacultyDB).filter(
            (FacultyDB.first_name.op("~")("[ก-๙]")) | (FacultyDB.last_name.op("~")("[ก-๙]"))
        ).all()

        total = len(targets)
        print(f"Total faculty records needing Latin names: {total}")
        if total == 0:
            print("No records need resolution!")
            return

        batch_size = 50
        updated_total = 0

        for i in range(0, total, batch_size):
            chunk = targets[i : i + batch_size]
            items_to_send = []
            for fac in chunk:
                items_to_send.append({
                    "id": fac.id,
                    "full_name_th": fac.full_name_th or "",
                    "current_fn": fac.first_name or "",
                    "current_ln": fac.last_name or "",
                    "university_th": fac.university_th or ""
                })

            prompt = f"""You are an expert academic Thai-to-English transliterator adhering strictly to the Royal Thai General System of Transcription (RTGS) and Thai academic publication conventions.
Given the following list of Thai university faculty members:
1. Strip all academic titles, royal decorations, and prefixes (e.g. ศ., รศ., ผศ., อ., ดร., ดร, พญ., นพ., สพ.ญ., น.สพ., อ.ดร., ท่านผู้หญิง, นาย, นาง, นางสาว).
2. Transliterate the given name into first_name and surname into last_name in Latin English characters.
3. If current_fn or current_ln already contains a valid English name, preserve and clean it into ASCII.
4. STRICT INVARIANT: All output values for first_name and last_name MUST be 100% pure ASCII Latin letters [a-zA-Z -]. ZERO Thai characters allowed.
5. Return a strict JSON array of objects with keys: "id", "first_name", "last_name".

Input Data:
{json.dumps(items_to_send, ensure_ascii=False)}
"""
            max_retries = 5
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
                    err_msg = str(e)
                    print(f"  Attempt {attempt+1} failed: {err_msg[:80]}")
                    if len(keys) > 1:
                        client_idx = (client_idx + 1) % len(keys)
                        client = genai.Client(api_key=keys[client_idx])
                        print(f"  Rotated to Gemini API key {client_idx+1}/{len(keys)}")
                    time.sleep(2)

            if not data or not isinstance(data, list):
                print(f"ERROR: Could not parse response for batch {i}..{i+len(chunk)}")
                continue

            batch_updated = 0
            for item in data:
                fid = item.get("id")
                fn = clean_ascii_name(item.get("first_name", ""))
                ln = clean_ascii_name(item.get("last_name", ""))

                if fn and ln and fn.isascii() and ln.isascii():
                    fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
                    if fac:
                        fac.first_name = fn
                        fac.last_name = ln
                        cache[fid] = {"first_name": fn, "last_name": ln}
                        batch_updated += 1
                        updated_total += 1

            db.commit()
            print(f"[{min(i + batch_size, total)}/{total}] Successfully updated {batch_updated} records. (Total updated: {updated_total})", flush=True)

            # Persist cache incrementally
            if CACHE_PATH.exists():
                try:
                    with open(CACHE_PATH, "w", encoding="utf-8") as f:
                        json.dump(cache, f, ensure_ascii=False, indent=2)
                except Exception as ex:
                    print(f"Warning writing cache: {ex}")

            time.sleep(0.5)

        print(f"\nFinished processing! Total records updated: {updated_total}")
        print(f"Cache size: {len(cache)}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
