# -*- coding: utf-8 -*-
"""
Clean the 762 records in en_name_prefixes:
1. Extract authentic English names for the 17 records with English in last_name.
2. Clear misplaced Thai titles/names from first_name and last_name for the 745 records.
3. Rebuild embedding_text for all affected records.
4. Save snapshot checkpoint to backend/data/agent_states/clean_en_prefixes_snapshot.json.
"""
import os
import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b|อ\.|ผศ\.|รศ\.|ศ\.)\s*",
    re.IGNORECASE
)

RE_STRIP_TITLE = re.compile(
    r"^(?:Mr\.?|Mrs\.?|Ms\.?|Miss\.?|Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?)\s*",
    re.IGNORECASE
)

def build_faculty_embedding_text(f: FacultyDB) -> str:
    parts = []
    if f.full_name_th:
        parts.append(f.full_name_th)
    en_name = f"{f.first_name or ''} {f.last_name or ''}".strip()
    if en_name:
        parts.append(en_name)
    if f.university_th:
        parts.append(f.university_th)
    if f.faculty_th:
        parts.append(f.faculty_th)
    if f.department_th:
        parts.append(f.department_th)
    if f.research_interests:
        interests = " ".join(f.research_interests) if isinstance(f.research_interests, list) else str(f.research_interests)
        parts.append(interests)
    if f.featured_publications and isinstance(f.featured_publications, list):
        pub_titles = [p.get("title", "") for p in f.featured_publications if isinstance(p, dict) and p.get("title")]
        if pub_titles:
            parts.append(" ".join(pub_titles[:5]))
    return " | ".join([p for p in parts if p.strip()])

def main():
    db = SessionLocal()
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

    snapshot = []
    fixed_en_count = 0
    cleared_thai_count = 0

    for f in faculties:
        first = (f.first_name or "").strip()
        if first and RE_EN_PREFIX.match(first):
            ln = (f.last_name or "").strip()
            has_thai = bool(re.search(r"[฀-๿]", ln))
            has_en = bool(re.search(r"[a-zA-Z]", ln))

            old_first = f.first_name
            old_last = f.last_name

            if has_en and not has_thai:
                # English name extraction
                clean_ln = RE_STRIP_TITLE.sub("", ln).strip()
                parts = clean_ln.split()
                if len(parts) == 1:
                    new_fn = parts[0].capitalize()
                    new_ln = ""
                elif len(parts) == 2:
                    new_fn = parts[0].capitalize()
                    new_ln = parts[1].capitalize()
                elif len(parts) >= 3 and parts[-2].upper() == "O":
                    # Handle Irish surnames e.g. O Donnell, O Neill
                    new_fn = " ".join(p.capitalize() for p in parts[:-2])
                    new_ln = f"O {parts[-1].capitalize()}"
                else:
                    new_fn = " ".join(p.capitalize() for p in parts[:-1])
                    new_ln = parts[-1].capitalize()

                f.first_name = new_fn
                f.last_name = new_ln
                fixed_en_count += 1

                snapshot.append({
                    "id": f.id,
                    "action": "extract_en_name",
                    "old_first": old_first,
                    "old_last": old_last,
                    "new_first": new_fn,
                    "new_last": new_ln
                })
            else:
                # Thai titles/names misplaced in first_name/last_name
                f.first_name = None
                f.last_name = None
                cleared_thai_count += 1

                snapshot.append({
                    "id": f.id,
                    "action": "clear_misplaced_thai",
                    "old_first": old_first,
                    "old_last": old_last,
                    "new_first": None,
                    "new_last": None
                })

            f.embedding_text = build_faculty_embedding_text(f)

    db.commit()
    print(f"Fixed English names: {fixed_en_count}")
    print(f"Cleared misplaced Thai from first/last: {cleared_thai_count}")
    print(f"Total processed: {len(snapshot)}")

    # Save snapshot
    out_file = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_en_prefixes_snapshot.json")
    with open(out_file, "w", encoding="utf-8") as out:
        json.dump(snapshot, out, ensure_ascii=False, indent=2)
    print(f"Snapshot checkpoint saved to {out_file}.")

    db.close()

if __name__ == "__main__":
    main()
