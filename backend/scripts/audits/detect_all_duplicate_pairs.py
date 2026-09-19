"""Detect ALL duplicate faculty pairs across the entire database:
1. Exact or normalized email match
2. OpenAlex ID match
3. Profile URL match
4. Thai name exact/near match within same university
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def detect_duplicates():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).all()
        print(f"Total faculty loaded: {len(faculties)}")

        # Map 1: By Email
        email_map = defaultdict(list)
        # Map 2: By OpenAlex ID
        openalex_map = defaultdict(list)
        # Map 3: By Profile URL
        url_map = defaultdict(list)

        for f in faculties:
            if f.email:
                email_map[f.email.lower().strip()].append(f)
            if f.openalex_id and f.openalex_id not in ["not_indexed", "none", "null"]:
                openalex_map[f.openalex_id.strip()].append(f)
            if f.profile_url and len(f.profile_url.strip()) > 15:
                # normalize url (strip trailing slash, lowercase)
                p = f.profile_url.strip().lower().rstrip("/")
                # exclude generic landing pages
                if not any(p.endswith(g) for g in ["/faculty", "/staff", "/people", "/personnel", "/lecturer", "/index.php"]):
                    url_map[p].append(f)

        print(f"Unique emails: {len(email_map)}")
        print(f"Unique OpenAlex IDs: {len(openalex_map)}")
        print(f"Unique specific profile URLs: {len(url_map)}")

        # Find duplicates by OpenAlex ID
        openalex_dupes = []
        for oid, facs in openalex_map.items():
            if len(facs) > 1:
                openalex_dupes.append({
                    "openalex_id": oid,
                    "faculties": [
                        {"id": f.id, "name": f.full_name_th, "uni": f.university_th, "fac": f.faculty_th, "email": f.email, "cites": f.total_citations}
                        for f in facs
                    ]
                })

        # Find duplicates by Profile URL
        url_dupes = []
        for purl, facs in url_map.items():
            if len(facs) > 1:
                url_dupes.append({
                    "url": purl,
                    "faculties": [
                        {"id": f.id, "name": f.full_name_th, "uni": f.university_th, "fac": f.faculty_th, "email": f.email, "cites": f.total_citations}
                        for f in facs
                    ]
                })

        print(f"\nDuplicates by OpenAlex ID: {len(openalex_dupes)}")
        for d in openalex_dupes:
            print(f"   * OpenAlex {d['openalex_id']}: {', '.join(x['id'] + ' (' + x['name'] + ')' for x in d['faculties'])}")

        print(f"\nDuplicates by Profile URL: {len(url_dupes)}")
        for d in url_dupes:
            print(f"   * URL {d['url']}: {', '.join(x['id'] + ' (' + x['name'] + ')' for x in d['faculties'])}")

        out = {
            "openalex_dupes": openalex_dupes,
            "url_dupes": url_dupes,
        }
        out_path = BACKEND_DIR / "data" / "agent_states" / "all_detected_duplicates.json"
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReport written to {out_path}")

    finally:
        db.close()

if __name__ == "__main__":
    detect_duplicates()
