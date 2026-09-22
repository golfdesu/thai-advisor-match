# -*- coding: utf-8 -*-
import os
import sys
import json
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SNAPSHOT_FILE = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_civic_titles_and_tggs_images_snapshot.json")

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()

    snapshot = {
        "civic_title_cleanups": [],
        "tggs_image_repairs": [],
        "foreign_faculty_repairs": [],
        "punctuation_and_casing_repairs": []
    }

    # 1. Civic titles following academic titles
    CIVIC_TITLE_PATTERN = re.compile(
        r"^(?P<title>(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)(?:\s*ดร\.)?)\s*(?:นาย\s+|นางสาว\s*|นาง\s+)(?P<name>[a-zA-Z฀-๿].*)$"
    )

    print("\n--- 1. Normalizing Civic Titles Following Academic Titles ---")
    for f in facs:
        nth = f.full_name_th or ""
        m = CIVIC_TITLE_PATTERN.match(nth.strip())
        if m:
            cleaned = f"{m.group('title')} {m.group('name').strip()}"
            if cleaned.endswith(" อาจารย์"):
                cleaned = cleaned[:-8].strip()
            if cleaned != nth:
                f.full_name_th = cleaned
                f.embedding_text = build_faculty_embedding_text(f)
                snapshot["civic_title_cleanups"].append({
                    "id": f.id,
                    "old": nth,
                    "new": cleaned
                })
                print(f"  {f.id}: '{nth}' -> '{cleaned}'")

    # 2. Fix ubu_w49_0085_490 (Thu Thu Aung)
    print("\n--- 2. Fixing Foreign Faculty ubu_w49_0085_490 ---")
    f_thu = db.query(FacultyDB).filter(FacultyDB.id == "ubu_w49_0085_490").first()
    if f_thu:
        f_thu.academic_title_th = "อ."
        f_thu.first_name = "Thu Thu"
        f_thu.last_name = "Aung"
        f_thu.full_name_th = "อ. Thu Thu Aung"
        f_thu.embedding_text = build_faculty_embedding_text(f_thu)
        snapshot["foreign_faculty_repairs"].append({
            "id": f_thu.id,
            "first_name": "Thu Thu",
            "last_name": "Aung",
            "full_name_th": "อ. Thu Thu Aung"
        })
        print(f"  Fixed ubu_w49_0085_490 -> อ. Thu Thu Aung")

    # 3. Fix TGGS relative image URLs
    print("\n--- 3. Fixing TGGS Relative Image URLs ---")
    for f in facs:
        if f.image_url and f.image_url.strip().startswith("../wp-content/"):
            old_url = f.image_url.strip()
            new_url = old_url.replace("../wp-content/", "https://tggs.kmutnb.ac.th/wp-content/")
            f.image_url = new_url
            snapshot["tggs_image_repairs"].append({
                "id": f.id,
                "old_url": old_url,
                "new_url": new_url
            })
            print(f"  {f.id}: '{old_url}' -> '{new_url}'")

    # 4. Clean punctuation (commas, trailing dots) and ALL-CAPS casing in English names
    print("\n--- 4. Cleaning Punctuation and ALL-CAPS in English Names ---")
    for f in facs:
        changed = False
        fn = f.first_name or ""
        ln = f.last_name or ""

        # strip commas
        if "," in fn:
            fn = fn.replace(",", "").strip()
            changed = True
        if "," in ln:
            ln = ln.replace(",", "").strip()
            changed = True

        # title case ALL CAPS names (len > 2 and all uppercase)
        if len(fn) > 2 and fn.isupper():
            fn = fn.title()
            changed = True
        if len(ln) > 2 and ln.isupper():
            # handle hyphenated like NA-BANGCHANG -> Na-Bangchang
            parts = ln.split("-")
            ln = "-".join(p.title() for p in parts)
            changed = True

        if changed:
            f.first_name = fn
            f.last_name = ln
            # also sync full_name_th if it was pure Latin
            if f.full_name_th and not re.search(r"[฀-๿]", f.full_name_th):
                f.full_name_th = f"{fn} {ln}"
            f.embedding_text = build_faculty_embedding_text(f)
            snapshot["punctuation_and_casing_repairs"].append({
                "id": f.id,
                "new_fn": fn,
                "new_ln": ln
            })
            print(f"  {f.id}: fn='{fn}', ln='{ln}'")

    db.commit()
    db.close()

    os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"\nCheckpoint written to: {SNAPSHOT_FILE}")

if __name__ == "__main__":
    main()
