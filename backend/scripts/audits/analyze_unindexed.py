# -*- coding: utf-8 -*-
import sys, os, re
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()
unindexed = db.query(FacultyDB).filter(
    (FacultyDB.total_publications_count == 0) | (FacultyDB.openalex_id == None) | (FacultyDB.openalex_id == '')
).all()

low_unindexed = [f for f in unindexed if not f.featured_publications or len(f.featured_publications) < 3]
print(f"Total low unindexed faculties: {len(low_unindexed)}")

# Check how many have 0, 1, 2 pubs
c0 = [f for f in low_unindexed if not f.featured_publications or len(f.featured_publications) == 0]
c1 = [f for f in low_unindexed if f.featured_publications and len(f.featured_publications) == 1]
c2 = [f for f in low_unindexed if f.featured_publications and len(f.featured_publications) == 2]
print(f"0 pubs: {len(c0)} | 1 pub: {len(c1)} | 2 pubs: {len(c2)}")

# Let's inspect which data sources or IDs they have
from collections import Counter
id_prefixes = [f.id.split('_')[0] if '_' in f.id else f.id[:10] for f in c0]
print("Top ID prefixes for 0-pub unindexed:", Counter(id_prefixes).most_common(15))

db.close()
