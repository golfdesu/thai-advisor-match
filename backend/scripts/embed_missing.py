import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from google import genai

def embed_missing():
    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not found!")
        return

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    db = SessionLocal()
    missing = db.query(FacultyDB).filter(FacultyDB.embedding == None).all()

    if not missing:
        print("All records already have embeddings.")
        db.close()
        return

    print(f"{len(missing)} records missing embedding")
    for f in missing:
        interests = ", ".join(f.research_interests) if f.research_interests else ""
        courses = ", ".join(f.taught_courses) if f.taught_courses else ""
        pubs = " | ".join([p["title"] for p in f.featured_publications]) if f.featured_publications else ""

        text = f"{f.academic_title_th or ''} {f.full_name_th or ''} {f.first_name or ''} {f.last_name or ''}. "
        text += f"Department: {f.department or ''} {f.department_th or ''}. "
        text += f"Research Interests: {interests}. "
        text += f"Taught Courses: {courses}. "
        text += f"Publications: {pubs}."

        f.embedding_text = text
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
    db.close()

if __name__ == "__main__":
    embed_missing()
