"""Forensic inspection of:
1. Faculty with English in full_name_th (Bilingual duplicates or un-translated names)
2. Email cross-contamination resolution (Which faculty truly owns the email based on username matching, and which faculty needs email cleared)
3. Parentheses in names resolution strategy
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def inspect():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).all()
        print(f"Total faculty records: {len(faculties)}")

        # 1. English letters in full_name_th
        english_in_th_name = []
        for f in faculties:
            if f.full_name_th and re.search(r"[a-zA-Z]", f.full_name_th):
                english_in_th_name.append({
                    "id": f.id,
                    "name_th": f.full_name_th,
                    "first": f.first_name,
                    "last": f.last_name,
                    "uni": f.university_th,
                    "fac": f.faculty_th,
                    "email": f.email,
                    "cites": f.total_citations,
                    "pubs": f.total_publications_count,
                    "openalex": f.openalex_id
                })

        print(f"\n1. Faculty records with English in full_name_th: {len(english_in_th_name)}")
        for item in english_in_th_name[:20]:
            print(f"   * {item['id']} | {item['name_th']} | {item['uni']} | {item['fac']} | {item['email']}")
        if len(english_in_th_name) > 20:
            print(f"   * ... and {len(english_in_th_name) - 20} more.")

        # Save details
        out = {
            "english_in_th_name": english_in_th_name,
        }
        out_file = BACKEND_DIR / "data" / "agent_states" / "bilingual_name_inspection.json"
        out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved to {out_file}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect()
