# -*- coding: utf-8 -*-
import sys
from collections import Counter
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
all_facs = db.query(FacultyDB).all()
title_counts = Counter()
title_to_venues = {}

for f in all_facs:
    for p in (f.featured_publications or []):
        if isinstance(p, dict):
            t = p.get('title', '').strip()
            v = p.get('venue', '')
        else:
            t = str(p).strip()
            v = 'string'
        if t:
            title_counts[t] += 1
            if t not in title_to_venues:
                title_to_venues[t] = set()
            title_to_venues[t].add(v)

print('Top 30 most frequent publication titles across DB:')
for t, c in title_counts.most_common(30):
    if c > 1:
        print(f'{c} times: "{t[:80]}" | Venues: {list(title_to_venues[t])}')
db.close()
