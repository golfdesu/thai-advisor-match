import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from app.core.embedding_text import build_faculty_embedding_text
from google import genai
from sqlalchemy import or_

def generate_embedding_text(f):
    return build_faculty_embedding_text(f)


def _stringify_items(items, key=None):
    """Return non-empty text values from legacy strings or structured objects."""
    values = []
    for item in items or []:
        value = item.get(key) if key and isinstance(item, dict) else item
        if value:
            values.append(str(value).strip())
    return values



def recompute_embeddings_fast():
    db = SessionLocal()
    faculties = db.query(FacultyDB).filter(
        or_(FacultyDB.embedding.is_(None), FacultyDB.embedding_text.is_(None))
    ).all()
    print(f"Found {len(faculties)} advisors needing embeddings or embedding_text...")
    needs_embedding = any(f.embedding is None for f in faculties)
    if needs_embedding and not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not found; cannot generate missing vectors.")
        db.close()
        return
    client = genai.Client(api_key=settings.GEMINI_API_KEY) if needs_embedding else None
    
    for i, f in enumerate(faculties):
        text = generate_embedding_text(f)
        f.embedding_text = text

        if f.embedding is not None:
            if i % 100 == 0:
                db.commit()
            continue
        
        success = False
        while not success:
            try:
                response = client.models.embed_content(
                    model='text-embedding-004',
                    contents=text,
                    config={'output_dimensionality': 768}
                )
                f.embedding = response.embeddings[0].values
                success = True
            except Exception as e:
                error_str = str(e)
                if "429" in error_str:
                    time.sleep(2)
                else:
                    print(f"Failed {f.id}: {e}")
                    break
                    
        if i % 100 == 0 and i > 0:
            print(f"Embedded {i}/{len(faculties)}")
            db.commit()
            
    db.commit()
    db.close()
    print("All embeddings updated!")

if __name__ == "__main__":
    recompute_embeddings_fast()
