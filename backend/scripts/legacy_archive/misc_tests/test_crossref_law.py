# -*- coding: utf-8 -*-
import sys, urllib.parse, urllib.request, json
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
law_facs = db.query(FacultyDB).filter(
    FacultyDB.faculty_th.like('%นิติ%'),
    (FacultyDB.total_publications_count == 0) | (FacultyDB.openalex_id == None) | (FacultyDB.openalex_id == '')
).limit(10).all()

for f in law_facs:
    en_name = f"{f.first_name or ''} {f.last_name or ''}".strip()
    print(f"Law Faculty: {f.full_name_th} ({en_name}) | Univ: {f.university_th}")
    if en_name:
        url = f"https://api.crossref.org/works?query.author={urllib.parse.quote(en_name)}&rows=2"
        req = urllib.request.Request(url, headers={'User-Agent': 'ThaiEduCenter/1.0 (mailto:admin@thaieducenter.ac.th)'})
        try:
            with urllib.request.urlopen(req, timeout=4) as res:
                data = json.loads(res.read().decode('utf-8'))
                items = data.get('message', {}).get('items', [])
                for it in items:
                    title = it.get('title', [''])[0]
                    journal = it.get('container-title', [''])[0]
                    year = it.get('issued', {}).get('date-parts', [[None]])[0][0]
                    print(f"   Crossref: {title[:70]} | {journal} ({year})")
        except Exception as e:
            print(f"   Error: {e}")
db.close()
