# -*- coding: utf-8 -*-
import os
import sys
import json
from collections import defaultdict
from sim_unified_dedup import get_name_tokens, are_same_person

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    db = SessionLocal()
    facs = db.query(FacultyDB).all()

    by_univ = defaultdict(list)
    for f in facs:
        if not f.university_th:
            continue
        fn, ln, tokens = get_name_tokens(f)
        if len(tokens) >= 2:
            by_univ[f.university_th].append((f, tokens))

    clusters = []
    seen = set()

    for univ, members in by_univ.items():
        n = len(members)
        for i in range(n):
            f1, tok1 = members[i]
            if f1.id in seen:
                continue
            cluster = [f1]
            for j in range(i + 1, n):
                f2, tok2 = members[j]
                if f2.id in seen:
                    continue
                if are_same_person(tok1, tok2):
                    cluster.append(f2)
            if len(cluster) > 1:
                clusters.append((univ, cluster))
                for m in cluster:
                    seen.add(m.id)

    print(f"Auditing {len(clusters)} clusters...")
    report = []
    for idx, (univ, cluster) in enumerate(clusters, 1):
        entry = {
            "cluster_id": idx,
            "university": univ,
            "members": [
                {
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "first_name": f.first_name,
                    "last_name": f.last_name,
                    "academic_title_th": f.academic_title_th,
                    "department_th": f.department_th,
                    "email": f.email,
                    "openalex_id": f.openalex_id,
                    "total_citations": f.total_citations,
                }
                for f in cluster
            ]
        }
        report.append(entry)

    out_file = os.path.join(BACKEND_DIR, "data", "agent_states", "unified_dedup_audit_clusters.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved audit report to {out_file}")
    db.close()

if __name__ == "__main__":
    main()
