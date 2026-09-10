# -*- coding: utf-8 -*-
"""
Backfill missing faculty embeddings using the SAME embedding_service and the SAME
canonical embedding_text the ingestion pipeline wrote — so new vectors are directly
comparable to the existing corpus (a different text-builder or model would put these
rows in a different vector space and silently corrupt semantic matching).

The massive ingestion runner swallows transient per-row API failures (it prints
progress regardless of success), leaving rows with embedding_text but no vector.
This closes that gap; it is idempotent (selection is embedding IS NULL) and
resumable. Run from repo root:  python backend/scripts/backfill_embeddings.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("backend"))
sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service


def main():
    db = SessionLocal()
    rows = (db.query(FacultyDB.id, FacultyDB.embedding_text)
              .filter(FacultyDB.embedding.is_(None))
              .order_by(FacultyDB.id)
              .all())
    print(f"Rows missing embedding: {len(rows)}", flush=True)
    ok = empty_text = failed = 0
    still_missing = []
    for i, (rid, text) in enumerate(rows, 1):
        if not text or not text.strip():
            empty_text += 1
            continue
        vec = None
        for attempt in range(4):
            try:
                v = embedding_service.get_embedding(text)
                if v:
                    vec = v
                    break
            except Exception as e:
                if attempt == 3:
                    print(f"  ! {rid}: {str(e)[:120]}", flush=True)
                time.sleep(1.5 * (attempt + 1))
        if vec:
            obj = db.get(FacultyDB, rid)
            obj.embedding = vec
            ok += 1
        else:
            failed += 1
            still_missing.append(rid)
        if i % 25 == 0:
            db.commit()
            print(f"  ...{i}/{len(rows)} ok={ok} fail={failed}", flush=True)
    db.commit()
    db.close()
    print(f"\n==== SUMMARY ====\n  embedded  {ok}\n  empty_text {empty_text}\n  failed    {failed}")
    if still_missing:
        print("  still missing:", still_missing[:20], "..." if len(still_missing) > 20 else "")


if __name__ == "__main__":
    main()
