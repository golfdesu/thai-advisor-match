import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from google import genai

def generate_embedding_text(f):
    interests = ", ".join(f.research_interests) if f.research_interests else ""
    courses = ", ".join(f.taught_courses) if f.taught_courses else ""
    pubs = ", ".join(f.featured_publications) if f.featured_publications else ""
    
    text = f"{f.academic_title_th or ''} {f.full_name_th or ''} {f.first_name or ''} {f.last_name or ''}. "
    text += f"University: {f.university or ''}. "
    text += f"Faculty: {f.faculty or ''}. "
    text += f"Department: {f.department or ''} {f.department_th or ''}. "
    text += f"Research Interests: {interests}. "
    text += f"Taught Courses: {courses}. "
    text += f"Publications: {pubs}."
    return text

def recompute_embeddings_fast():
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    db = SessionLocal()
    faculties = db.query(FacultyDB).filter(FacultyDB.embedding == None).all()
    print(f"Found {len(faculties)} advisors needing embeddings...")
    
    for i, f in enumerate(faculties):
        text = generate_embedding_text(f)
        f.embedding_text = text
        
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
