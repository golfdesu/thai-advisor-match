import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from google import genai

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_faculty_embedding(fac_id, text):
    try:
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=text,
            config={'output_dimensionality': 768}
        )
        return (fac_id, response.embeddings[0].values, None)
    except Exception as e:
        return (fac_id, None, str(e))

def recompute_embeddings():
    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not found!")
        return

    db = SessionLocal()
    # Process only faculties without embeddings
    faculties = db.query(FacultyDB).filter(FacultyDB.embedding == None).all()
    
    if not faculties:
        print("All faculties already have embeddings!")
        db.close()
        return
        
    print(f"Starting embeddings generation for {len(faculties)} missing faculties...")
    
    tasks = []
    for f in faculties:
        interests = ", ".join(f.research_interests) if f.research_interests else ""
        courses = ", ".join(f.taught_courses) if f.taught_courses else ""
        
        # Handle publications depending on if it's a list of dicts or strings
        if f.featured_publications:
            if isinstance(f.featured_publications[0], dict):
                pubs = " | ".join([p.get("title", "") for p in f.featured_publications])
            else:
                pubs = " | ".join(f.featured_publications)
        else:
            pubs = ""
            
        text = f"{f.academic_title_th or ''} {f.full_name_th or ''} {f.first_name or ''} {f.last_name or ''}. "
        text += f"Department: {f.department or ''} {f.department_th or ''}. "
        text += f"Research Interests: {interests}. "
        text += f"Taught Courses: {courses}. "
        text += f"Publications: {pubs}."
        
        text = text[:6000] # Safe limit
        tasks.append((f.id, text))
        
    db.close()
    
    BATCH_SIZE = 15
    completed = 0
    
    for i in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[i:i+BATCH_SIZE]
        db = SessionLocal()
        
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            future_to_id = {executor.submit(generate_faculty_embedding, tid, txt): tid for tid, txt in batch}
            
            for future in as_completed(future_to_id):
                fac_id, vector, err = future.result()
                if vector:
                    f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
                    if f:
                        f.embedding = vector
                        f.embedding_text = [t for i, t in batch if i == fac_id][0]
                        completed += 1
                else:
                    print(f"Failed {fac_id}: {err}")
        
        db.commit()
        db.close()
        print(f"Progress: {completed} / {len(tasks)}")
        time.sleep(1)

    print("All faculty embeddings updated!")

if __name__ == "__main__":
    recompute_embeddings()
