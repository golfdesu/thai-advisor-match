# -*- coding: utf-8 -*-
import os
import sys
import re
from collections import defaultdict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()

    univ_token_groups = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn = (f.first_name or "").lower().strip()
        ln = (f.last_name or "").lower().strip()
        if fn and ln and len(fn) > 1 and len(ln) > 1:
            tokens = frozenset(re.findall(r'[a-z]+', f"{fn} {ln}"))
            if len(tokens) >= 2:
                univ_token_groups[(f.university_th, tokens)].append(f)

    dups = {k: v for k, v in univ_token_groups.items() if len(v) > 1}

    multi_email = []
    for (univ, tokens), cluster in dups.items():
        emails = set(f.email for f in cluster if f.email)
        if len(emails) > 1:
            multi_email.append((univ, tokens, cluster))

    print(f"Total token-set clusters: {len(dups)}")
    print(f"Clusters with >1 distinct email: {len(multi_email)}")
    for univ, tokens, cluster in multi_email:
        print(f"\n{univ} - tokens: {tokens}")
        for f in cluster:
            print(f"   {f.id} | fn: '{f.first_name}' | ln: '{f.last_name}' | email: {f.email}")
    db.close()

if __name__ == "__main__":
    main()
