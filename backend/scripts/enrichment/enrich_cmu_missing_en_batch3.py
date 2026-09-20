# -*- coding: utf-8 -*-
"""
Enrichment Script for CMU Faculty of Medicine (252 Faculty Members - Batch 3)
Updates authentic English names, institutional academic emails, Scopus/Crossref bibliometrics,
recomputes 768-dimensional Gemini embeddings, and commits to local PostgreSQL.
"""
import sys
import os
import json
import ssl
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import psycopg2
from app.core.embedding_service import embedding_service

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('med_batch3_compiled.json', 'r', encoding='utf-8') as f:
    BATCH3_FACULTIES = json.load(f)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) mailto:admin@advisor-match.th'
}


def harvest_crossref_metrics(first_name, last_name):
    """
    Query Crossref API for author works and calculate H-index and total citations politely.
    """
    query = f"{first_name} {last_name}"
    url = f"https://api.crossref.org/works?query.author={urllib.parse.quote(query)}&rows=50"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            cdata = json.loads(resp.read().decode('utf-8'))
        items = cdata.get('message', {}).get('items', [])
        cites = []
        matching_pubs = 0
        for it in items:
            authors = it.get('author', [])
            matched_author = False
            for a in authors:
                fam = a.get('family', '').lower()
                giv = a.get('given', '').lower()
                if last_name.lower() in fam or (first_name.lower() in giv and len(first_name) > 3):
                    matched_author = True
                    break
            if matched_author:
                matching_pubs += 1
                cites.append(it.get('is-referenced-by-count', 0))

        cites.sort(reverse=True)
        h_index = 0
        for rank, c in enumerate(cites, 1):
            if c >= rank:
                h_index = rank
            else:
                break

        total_cites = sum(cites)
        return h_index, total_cites, matching_pubs
    except Exception:
        return 0, 0, 0


def run_enrichment():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
    cur = conn.cursor()

    total = len(BATCH3_FACULTIES)
    print(f"=== Starting Batch 3 Enrichment for {total} Medicine Faculty Members ===", flush=True)

    updated_count = 0
    start_time = time.time()

    for i, fac in enumerate(BATCH3_FACULTIES, 1):
        fac_id = fac["id"]
        cur.execute("""
            SELECT full_name_th, department_th, department, faculty_th, university_th,
                   research_interests, education, featured_publications,
                   h_index, total_citations, total_publications_count
            FROM faculties
            WHERE id = %s;
        """, (fac_id,))
        row = cur.fetchone()
        if not row:
            print(f"[{i}/{total}] Record not found: {fac_id}", flush=True)
            continue

        fn_th, dept_th, dept_en, fac_th, uni_th, interests, edu, pubs, cur_h, cur_cites, cur_pubs = row

        scopus_h = fac.get("h_index") or 0
        scopus_cites = fac.get("citations") or 0

        # Only query Crossref if both existing and Scopus metrics are missing
        if (cur_h or 0) == 0 and scopus_h == 0:
            h_idx, cites, works = harvest_crossref_metrics(fac["first_name"], fac["last_name"])
            time.sleep(0.05)
        else:
            h_idx, cites, works = 0, 0, 0

        # Metric Preservation Invariant (Section 9 Invariant 10)
        final_h = max(cur_h or 0, scopus_h, h_idx)
        final_cites = max(cur_cites or 0, scopus_cites, cites)
        final_pubs = max(cur_pubs or 0, works)

        # Parse text fields for embedding
        interests_str = " ".join(interests) if isinstance(interests, list) else (str(interests or ""))
        edu_str = " ".join(edu) if isinstance(edu, list) else (str(edu or ""))
        pubs_str = ""
        if isinstance(pubs, list):
            pubs_str = " ".join(p.get("title", "") for p in pubs if isinstance(p, dict))

        new_embedding_text = (
            f"{fac['first_name']} {fac['last_name']} {fn_th} "
            f"{dept_th or ''} {dept_en or ''} {fac_th or ''} {uni_th or ''} "
            f"{interests_str} {edu_str} {pubs_str}"
        ).strip()

        if i % 10 == 0 or i == total:
            print(f"[{i}/{total}] Embedding: {fac['first_name']} {fac['last_name']} ({fn_th}) | H={final_h}, Cites={final_cites}...", flush=True)

        vec = embedding_service.get_embedding(new_embedding_text)
        if not vec or len(vec) != 768:
            vec = [0.0] * 768

        vec_str = str(vec)

        update_sql = """
            UPDATE faculties SET
                first_name = %(first_name)s,
                last_name = %(last_name)s,
                email = COALESCE(NULLIF(%(email)s, ''), email),
                h_index = %(h_index)s,
                total_citations = %(total_citations)s,
                total_publications_count = %(total_publications_count)s,
                embedding_text = %(embedding_text)s,
                embedding = %(embedding)s::vector
            WHERE id = %(id)s;
        """

        cur.execute(update_sql, {
            "id": fac_id,
            "first_name": fac["first_name"],
            "last_name": fac["last_name"],
            "email": fac["email"],
            "h_index": final_h,
            "total_citations": final_cites,
            "total_publications_count": final_pubs,
            "embedding_text": new_embedding_text,
            "embedding": vec_str
        })

        updated_count += 1

        # Commit every 25 records
        if updated_count % 25 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    elapsed = time.time() - start_time
    print(f"\nSuccessfully enriched and committed {updated_count}/{total} Faculty of Medicine members in {elapsed:.1f}s!", flush=True)


if __name__ == "__main__":
    run_enrichment()
