import os
import sys

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from google import genai
import json
import time

def recompute_embeddings():
    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not found!")
        return

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    db = SessionLocal()
    faculties = db.query(FacultyDB).all()
    
    for f in faculties:
        print(f"Updating embedding for: {f.first_name} {f.last_name}")
        
        # 1. Build the new embedding text
        interests = ", ".join(f.research_interests) if f.research_interests else ""
        courses = ", ".join(f.taught_courses) if f.taught_courses else ""
        pubs = " | ".join([p["title"] for p in f.featured_publications]) if f.featured_publications else ""
        
        text = f"{f.academic_title_th or ''} {f.full_name_th or ''} {f.first_name or ''} {f.last_name or ''}. "
        text += f"Department: {f.department or ''} {f.department_th or ''}. "
        text += f"Research Interests: {interests}. "
        text += f"Taught Courses: {courses}. "
        text += f"Publications: {pubs}."
        
        f.embedding_text = text
        
        # 2. Get embedding vector from Gemini
        try:
            response = client.models.embed_content(
                model='gemini-embedding-2',
                contents=text,
                config={'output_dimensionality': 768}
            )
            f.embedding = response.embeddings[0].values
            db.commit()
            print("  -> Success")
        except Exception as e:
            print(f"  -> Error embedding: {e}")
            db.rollback()
            
        time.sleep(1)
        
    db.close()
    print("All embeddings updated!")

if __name__ == "__main__":
    recompute_embeddings()
