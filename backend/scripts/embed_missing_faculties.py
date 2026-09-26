# -*- coding: utf-8 -*-
"""
Generate Vector Embeddings for Faculties with NULL Embedding
Target: Remaining 50 Assumption University faculty records
Model: gemini-embedding-001 (768 dimensions)
"""
import os
import sys
import time
import re
from pathlib import Path
from google import genai

if os.path.exists("/app"):
    BACKEND_DIR = Path("/app")
else:
    BACKEND_DIR = Path(__file__).resolve().parents[1] if "__file__" in locals() and len(Path(__file__).resolve().parents) > 1 else Path("backend").resolve()

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text

def main():
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
    if gemini_key and gemini_key not in keys:
        keys.insert(0, gemini_key)

    if not keys:
        print("ERROR: No GEMINI API key found!")
        return

    print(f"Loaded {len(keys)} Gemini API keys.")
    client_idx = 0
    client = genai.Client(api_key=keys[client_idx])

    db = SessionLocal()

    try:
        targets = db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).all()
        print(f"Total faculty records needing embeddings: {len(targets)}")
        if not targets:
            print("No records need embeddings!")
            return

        batch_size = 25
        total = len(targets)
        updated = 0

        for i in range(0, total, batch_size):
            chunk = targets[i : i + batch_size]
            texts = []
            for fac in chunk:
                txt = build_faculty_embedding_text(fac)
                if not txt.strip():
                    txt = f"{fac.full_name_th or ''} {fac.university_th or ''} {fac.faculty_th or ''}".strip()
                texts.append(txt)

            print(f"[{i + len(chunk)}/{total}] Embedding batch of {len(chunk)} records...", flush=True)

            max_retries = 8
            embeddings = None
            for attempt in range(max_retries):
                try:
                    res = client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=texts,
                        config={"output_dimensionality": 768}
                    )
                    embeddings = res.embeddings
                    break
                except Exception as e:
                    err_msg = str(e)
                    # Check for retryDelay
                    retry_match = re.search(r"retryDelay':\s*'(\d+)s'", err_msg)
                    wait_time = int(retry_match.group(1)) + 2 if retry_match else (attempt + 1) * 5

                    # Rotate key if available
                    if len(keys) > 1:
                        client_idx = (client_idx + 1) % len(keys)
                        client = genai.Client(api_key=keys[client_idx])
                        print(f"  Rotated to Gemini API key {client_idx + 1}/{len(keys)}. Waiting {wait_time}s...", flush=True)
                    else:
                        print(f"  Attempt {attempt+1} failed: {err_msg[:80]}... Waiting {wait_time}s...", flush=True)
                    time.sleep(wait_time)

            if not embeddings or len(embeddings) != len(chunk):
                print(f"ERROR: Failed to embed chunk starting at index {i}!")
                continue

            for fac, txt, emb in zip(chunk, texts, embeddings):
                fac.embedding_text = txt
                fac.embedding = emb.values[:768]
                updated += 1

            db.commit()
            print(f"  Committed batch {i // batch_size + 1}. Total updated: {updated}", flush=True)
            time.sleep(1.0)

        print(f"\nSuccessfully generated and committed {updated} vector embeddings (768-dim)!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
