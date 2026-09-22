# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHECKPOINT_FILE = os.path.join(BACKEND_DIR, "data", "agent_states", "enrich_single_char_names_checkpoint.json")

def fetch_openalex_author(oaid):
    short_id = oaid.split("/")[-1]
    url = f"https://api.openalex.org/authors/{short_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "mailto:advisor-match@edu.th"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
            else:
                return None
        except Exception:
            return None
    return None

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).filter(
        FacultyDB.first_name.isnot(None),
        FacultyDB.openalex_id.isnot(None),
        FacultyDB.openalex_id != "not_indexed"
    ).all()

    targets = [
        f for f in facs
        if len(f.first_name.strip()) == 1 and f.last_name and len(f.last_name.strip()) > 1
    ]
    print(f"Total faculty with single-character first_name: {len(targets)}")

    enriched = []

    def process_faculty(f_id, fn, ln, oaid, full_th):
        data = fetch_openalex_author(oaid)
        if not data:
            return None
        alts = data.get("display_name_alternatives") or []
        disp = data.get("display_name") or ""
        all_names = [disp] + alts

        initial = fn.strip().upper()
        target_ln = ln.strip().lower()

        best_match = None
        for name in all_names:
            if not isinstance(name, str):
                continue
            parts = name.strip().split()
            if len(parts) >= 2:
                # Case 1: "First Last"
                if parts[-1].lower() == target_ln and len(parts[0]) > 1 and parts[0][0].upper() == initial and not parts[0].endswith("."):
                    best_match = (parts[0], " ".join(parts[1:]))
                    break
                # Case 2: "Last, First" or "Last First"
                elif parts[0].rstrip(",").lower() == target_ln and len(parts[-1]) > 1 and parts[-1][0].upper() == initial and not parts[-1].endswith("."):
                    best_match = (parts[-1], parts[0].rstrip(","))
                    break

        if best_match:
            return {
                "id": f_id,
                "old_fn": fn,
                "old_ln": ln,
                "new_fn": best_match[0],
                "new_ln": best_match[1],
                "full_th": full_th,
                "oaid": oaid
            }
        return None

    print("Querying OpenAlex concurrently (workers=5)...")
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_faculty, f.id, f.first_name, f.last_name, f.openalex_id, f.full_name_th): f.id
            for f in targets
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    print(f"\nSuccessfully identified full names for {len(results)}/{len(targets)} faculty records!")

    # Apply updates to database
    for r in results:
        f = db.query(FacultyDB).filter(FacultyDB.id == r["id"]).first()
        if f:
            f.first_name = r["new_fn"]
            f.last_name = r["new_ln"]
            # If full_name_th was just the English initial + surname, update it to full English name
            if f.full_name_th and re.match(r"^[A-Z]\.?\s+[A-Za-z\-]+$", f.full_name_th.strip()):
                f.full_name_th = f"{r['new_fn']} {r['new_ln']}"
            f.embedding_text = build_faculty_embedding_text(f)
            enriched.append(r)
            print(f"  {f.id}: '{r['old_fn']} {r['old_ln']}' -> '{r['new_fn']} {r['new_ln']}'")

    db.commit()
    db.close()

    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    print(f"\nCheckpoint written to: {CHECKPOINT_FILE}")

if __name__ == "__main__":
    main()
