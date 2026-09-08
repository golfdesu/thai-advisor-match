# -*- coding: utf-8 -*-
"""
High-Speed Asynchronous Vector Re-embedding Worker for Updated Faculties
Embeds newly enriched research publications into 768-dimensional AI vectors
using batching and connection pooling for maximum throughput.
"""

import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath("backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from scripts.faculty_massive_ingestion_runner import build_faculty_embedding_text

def run_reembedding():
    db = SessionLocal()
    all_facs = db.query(FacultyDB).all()
    targets = []
    for f in all_facs:
        pubs = f.featured_publications or []
        if not pubs:
            continue
        pub_titles = [p.get('title', '') if isinstance(p, dict) else str(p) for p in pubs]
        txt = f.embedding_text or ''
        if not any(pt and pt[:25].lower() in txt.lower() for pt in pub_titles):
            targets.append(f.id)
    db.close()

    total = len(targets)
    print("=" * 65)
    print(f"🧠 FAST VECTOR RE-EMBEDDING FOR {total} FACULTY MEMBERS")
    print("=" * 65)

    def embed_single(fid):
        with SessionLocal() as s:
            rec = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if not rec:
                return fid, None, None
            new_text = build_faculty_embedding_text(rec)
            vec = embedding_service.get_embedding(new_text)
            return fid, new_text, vec

    chunk_size = 40
    total_embedded = 0
    t0 = time.time()

    for i in range(0, total, chunk_size):
        chunk = targets[i:i + chunk_size]
        vec_map = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(embed_single, fid) for fid in chunk]
            for fut in as_completed(futs):
                try:
                    fid, new_txt, vec = fut.result()
                    if vec:
                        vec_map[fid] = (new_txt, vec)
                except Exception as e:
                    pass

        # Commit chunk
        with SessionLocal() as s_write:
            for fid, (txt, vec) in vec_map.items():
                obj = s_write.query(FacultyDB).filter(FacultyDB.id == fid).first()
                if obj:
                    obj.embedding_text = txt
                    obj.embedding = vec
                    total_embedded += 1
            s_write.commit()

        done = min(i + chunk_size, total)
        pct = (done * 100.0) / total
        print(f"[{done:4d}/{total}] Re-embedded: {total_embedded:4d} faculties ({pct:5.1f}%) | Speed: {total_embedded / (time.time() - t0):.1f} fac/s")

    print("=" * 65)
    print(f"✅ VECTOR RE-EMBEDDING COMPLETED IN {time.time() - t0:.1f}s | Total: {total_embedded}")
    print("=" * 65)

if __name__ == "__main__":
    run_reembedding()
