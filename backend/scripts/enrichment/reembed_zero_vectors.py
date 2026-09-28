# -*- coding: utf-8 -*-
"""
Re-embed rows whose embedding is the all-zero circuit-breaker placeholder ([0.0] * 768).

Zero vectors produce NaN cosine distances, which pgvector sorts last, so these rows
are invisible to semantic search even though audit "missing embedding" checks
(IS NULL) pass. Targets faculties and courses with vector_norm(embedding) = 0.

5-pillar contract:
  1. Headless ThreadPoolExecutor (4 workers), batched embed_content calls (20 texts/call)
  3. Per-key circuit breaker: 429 -> rotate key + backoff (15s..90s, up to 60 attempts);
     a batch that fails on every key is skipped (row keeps its zero vector) and logged
  5. Checkpoint of done IDs in backend/data/agent_states/reembed_zero_vectors.json,
     DB commit per batch, so reruns resume without re-calling the API

Model: gemini-embedding-2 @ 768 dims (verified cos >= 0.95 against stored vectors,
vs ~0.03 for gemini-embedding-001).

Usage (inside backend container):  python scripts/enrichment/reembed_zero_vectors.py [--dry-run]
"""
import json
import re
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from google import genai
from google.genai import types
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.embedding_service import load_all_gemini_keys

MODEL = "gemini-embedding-2"
DIM = 768
# Free-tier quota is 100 embed requests/min per project and each text counts,
# so keep batches small and retry 429s patiently instead of failing the batch.
BATCH = 20
WORKERS = 4
MAX_ATTEMPTS = 60
MAX_TEXT = 6000
CHECKPOINT = Path(os.getenv("AGENT_STATE_DIR", BACKEND_DIR / "data" / "agent_states")) / "reembed_zero_vectors.json"

TABLES = {
    "faculties": "SELECT id, embedding_text FROM faculties WHERE vector_norm(embedding) = 0",
    "courses": "SELECT id, embedding_text FROM courses WHERE vector_norm(embedding) = 0",
}


class KeyPool:
    """Round-robin Gemini clients with per-key cooldown after 429s."""

    def __init__(self, keys: list[str]):
        self.clients = [genai.Client(api_key=k) for k in keys]
        self.cool_until = [0.0] * len(keys)
        self.idx = 0
        self.lock = threading.Lock()

    def acquire(self) -> tuple[int, genai.Client]:
        with self.lock:
            now = time.monotonic()
            for _ in range(len(self.clients)):
                i = self.idx
                self.idx = (self.idx + 1) % len(self.clients)
                if self.cool_until[i] <= now:
                    return i, self.clients[i]
            i = min(range(len(self.clients)), key=lambda j: self.cool_until[j])
        time.sleep(max(0.0, self.cool_until[i] - time.monotonic()))
        return i, self.clients[i]

    def cool(self, i: int, seconds: float):
        with self.lock:
            self.cool_until[i] = time.monotonic() + seconds


def embed_batch(pool: KeyPool, texts: list[str]) -> list[list[float]] | None:
    backoff = 15.0
    for _ in range(MAX_ATTEMPTS):
        i, client = pool.acquire()
        try:
            # A bare list[str] is aggregated into ONE embedding by gemini-embedding-2;
            # one Content per text yields one vector per text.
            contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
            res = client.models.embed_content(model=MODEL, contents=contents, config={"output_dimensionality": DIM})
            vecs = [e.values for e in res.embeddings]
            if len(vecs) == len(texts) and all(len(v) == DIM and any(v) for v in vecs):
                return vecs
            print(f"  invalid response: {len(vecs)} vectors for {len(texts)} texts", flush=True)
            return None
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                pool.cool(i, backoff)
                quota = re.findall(r"quotaId': '([^']+)", err)
                print(f"  429 key#{i} {quota[:1]} cooling {backoff:.0f}s", flush=True)
                backoff = min(backoff + 15.0, 90.0)
            elif any(c in err for c in ("401", "403", "UNAUTHENTICATED", "PERMISSION_DENIED")):
                pool.cool(i, 3600.0)
            else:
                print(f"  batch error: {err[:120]}", flush=True)
                return None
    return None


def load_checkpoint() -> dict[str, list[str]]:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    return {t: [] for t in TABLES}


def save_checkpoint(state: dict[str, list[str]]):
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CHECKPOINT)


def main():
    dry_run = "--dry-run" in sys.argv
    keys = load_all_gemini_keys()
    if not keys:
        print("ERROR: no Gemini keys available")
        return
    pool = KeyPool(keys)
    state = load_checkpoint()
    lock = threading.Lock()
    failed: list[str] = []

    for table, sql in TABLES.items():
        db = SessionLocal()
        rows = [(rid, (txt or "").strip()[:MAX_TEXT]) for rid, txt in db.execute(text(sql)).all()]
        db.close()
        done = set(state.get(table, []))
        rows = [r for r in rows if r[0] not in done and r[1]]
        print(f"{table}: {len(rows)} zero-vector rows to embed ({len(done)} already checkpointed)", flush=True)
        if dry_run or not rows:
            continue

        batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
        committed = 0

        def work(batch):
            vecs = embed_batch(pool, [t for _, t in batch])
            if vecs is None:
                return batch, 0
            db = SessionLocal()
            try:
                for (rid, _), v in zip(batch, vecs):
                    db.execute(
                        text(f"UPDATE {table} SET embedding = CAST(:v AS vector) WHERE id = :id"),
                        {"v": "[" + ",".join(f"{x:.8f}" for x in v) + "]", "id": rid},
                    )
                db.commit()
            finally:
                db.close()
            return batch, len(batch)

        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = [ex.submit(work, b) for b in batches]
            for n, fut in enumerate(as_completed(futures), 1):
                batch, ok = fut.result()
                with lock:
                    if ok:
                        committed += ok
                        state.setdefault(table, []).extend(rid for rid, _ in batch)
                        save_checkpoint(state)
                    else:
                        failed.extend(f"{table}:{rid}" for rid, _ in batch)
                if n % 10 == 0 or n == len(batches):
                    print(f"  {table}: {n}/{len(batches)} batches, {committed} rows committed", flush=True)

    print(f"DONE. failed rows: {len(failed)}", flush=True)
    if failed:
        out = CHECKPOINT.with_name("reembed_zero_vectors_failed.json")
        out.write_text(json.dumps(failed, ensure_ascii=False), encoding="utf-8")
        print(f"failed ids logged to {out}", flush=True)


if __name__ == "__main__":
    main()
