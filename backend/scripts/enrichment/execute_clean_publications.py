# -*- coding: utf-8 -*-
"""
Harmonize featured_publications across the database:
1. Strip 977 placeholder strings ('OpenAlex h-index: ...') from featured_publications -> set to []
2. Standardize 117 plain string lists ['Title 1', 'Title 2'] -> [{'title': 'Title 1', ...}, ...]
3. Rebuild embedding_text where affected.
4. Save snapshot checkpoints to backend/data/agent_states/.
"""
import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer

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

    cleared_summary_snapshot = []
    standardized_plain_snapshot = []

    summary_count = 0
    plain_count = 0

    for f in faculties:
        pubs = f.featured_publications
        if not pubs or not isinstance(pubs, list):
            continue

        has_summary = any(isinstance(p, str) and p.startswith("OpenAlex h-index:") for p in pubs)
        has_plain_str = any(isinstance(p, str) and not p.startswith("OpenAlex h-index:") for p in pubs)
        has_dict = any(isinstance(p, dict) for p in pubs)

        if has_summary and not has_plain_str and not has_dict:
            # 977 records where the only item was a summary string
            cleared_summary_snapshot.append({
                "id": f.id,
                "full_name_th": f.full_name_th,
                "old_pubs": pubs
            })
            f.featured_publications = []
            f.embedding_text = build_faculty_embedding_text(f)
            summary_count += 1

        elif has_plain_str:
            # Records with plain strings
            new_pubs = []
            for p in pubs:
                if isinstance(p, dict):
                    if p.get("title"):
                        new_pubs.append(p)
                elif isinstance(p, str):
                    clean_title = p.strip()
                    if clean_title and not clean_title.startswith("OpenAlex h-index:"):
                        new_pubs.append({
                            "title": clean_title,
                            "year": None,
                            "venue": None,
                            "url": None,
                            "citation_count": 0
                        })
            standardized_plain_snapshot.append({
                "id": f.id,
                "full_name_th": f.full_name_th,
                "old_pubs": pubs,
                "new_pubs_count": len(new_pubs)
            })
            f.featured_publications = new_pubs
            f.embedding_text = build_faculty_embedding_text(f)
            plain_count += 1

    db.commit()
    print(f"Summary strings cleared to []: {summary_count}")
    print(f"Plain string lists standardized to dicts: {plain_count}")

    # Save snapshots
    f1 = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_pubs_summary_snapshot.json")
    with open(f1, "w", encoding="utf-8") as out:
        json.dump(cleared_summary_snapshot, out, ensure_ascii=False, indent=2)

    f2 = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_pubs_plain_strings_snapshot.json")
    with open(f2, "w", encoding="utf-8") as out:
        json.dump(standardized_plain_snapshot, out, ensure_ascii=False, indent=2)

    print(f"Checkpoints saved to {f1} and {f2}.")
    db.close()

if __name__ == "__main__":
    main()
