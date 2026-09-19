import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from app.core.embedding_text import build_faculty_embedding_text
from google import genai
from sqlalchemy import or_

def embed_missing():
    db = SessionLocal()
    missing = db.query(FacultyDB).filter(
        or_(FacultyDB.embedding.is_(None), FacultyDB.embedding_text.is_(None))
    ).all()

    if not missing:
        print("All records already have embeddings.")
        db.close()
        return

    needs_embedding = any(f.embedding is None for f in missing)
    if needs_embedding and not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not found; cannot generate missing vectors.")
        db.close()
        return

    client = genai.Client(api_key=settings.GEMINI_API_KEY) if needs_embedding else None
    print(f"{len(missing)} records missing embedding or embedding_text")
    for f in missing:
        text = build_faculty_embedding_text(f)

        if not text:
            print(f"  SKIPPED: {f.id} has no usable source fields")
            continue

        f.embedding_text = text
        if f.embedding is not None:
            print(f"  TEXT ONLY: {f.id}")
            continue
        try:
            response = client.models.embed_content(
                model='gemini-embedding-2',
                contents=text,
                config={'output_dimensionality': 768}
            )
            f.embedding = response.embeddings[0].values
            db.commit()
            print(f"  OK: {f.first_name} {f.last_name}")
        except Exception as e:
            print(f"  FAILED: {f.first_name} {f.last_name}: {e}")
            db.rollback()
            break
    db.commit()
    db.close()

if __name__ == "__main__":
    embed_missing()
