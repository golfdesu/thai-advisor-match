# -*- coding: utf-8 -*-
"""
Rebuild embedding_text for all faculties and re-generate 768-dim vectors
only where the deterministic text actually changed (post canonical-merge hygiene).
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from scripts.faculty_massive_ingestion_runner import build_faculty_embedding_text


def main():
    db = SessionLocal()
    stale = []
    for f in db.query(FacultyDB).all():
        rebuilt = build_faculty_embedding_text(f)
        if rebuilt != (f.embedding_text or ""):
            stale.append(f.id)
    print(f"🔎 Rows with changed embedding_text (need re-embed): {len(stale)}")
    db.close()
    if not stale:
        return

    def embed_one(fid):
        with SessionLocal() as s:
            rec = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if not rec:
                return fid, None, None
            txt = build_faculty_embedding_text(rec)
            for attempt in range(3):
                try:
                    vec = embedding_service.get_embedding(txt)
                    if vec:
                        return fid, txt, vec
                except Exception:
                    time.sleep(1.5 * (attempt + 1))
            return fid, txt, None

    done = 0
    failed = []
    t0 = time.time()
    for i in range(0, len(stale), 20):
        batch = stale[i:i + 20]
        vec_map = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(embed_one, fid) for fid in batch]
            for fut in as_completed(futs):
                fid, txt, vec = fut.result()
                if vec and txt:
                    vec_map[fid] = (txt, vec)
                elif txt:
                    failed.append(fid)
        with SessionLocal() as sw:
            for fid, (txt, vec) in vec_map.items():
                obj = sw.query(FacultyDB).filter(FacultyDB.id == fid).first()
                if obj:
                    obj.embedding_text = txt
                    obj.embedding = vec
            sw.commit()
        done += len(batch)
        print(f"   -> {done}/{len(stale)} processed ({done / (time.time() - t0):.1f} rec/s)")

    print(f"✅ Refresh complete. Failed (retry embed_missing): {len(failed)}")
    if failed:
        with open(os.path.join(BACKEND_DIR, "data", "agent_states", "refresh_failed_ids.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(failed))


if __name__ == "__main__":
    main()
