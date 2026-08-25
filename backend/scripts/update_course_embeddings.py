import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.config import settings
from google import genai

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_embedding_for_course(course_id, text):
    try:
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=text,
            config={'output_dimensionality': 768}
        )
        return (course_id, response.embeddings[0].values, None)
    except Exception as e:
        return (course_id, None, str(e))

def main():
    db = SessionLocal()
    courses = db.query(CourseDB).filter(CourseDB.embedding == None).all()
    
    if not courses:
        print("All courses already have embeddings!")
        return

    print(f"Starting embeddings generation for {len(courses)} courses...")
    
    tasks = []
    for c in courses:
        highlights = ", ".join(c.curriculum_highlights) if c.curriculum_highlights else ""
        careers = ", ".join(c.career_paths) if c.career_paths else ""
        tags = ", ".join(c.tags) if c.tags else ""
        
        text = f"{c.title_th} {c.title_en or ''} "
        text += f"คณะ: {c.faculty_th or ''} สาขา: {c.department_th or ''} "
        text += f"มหาวิทยาลัย: {c.university_th or ''} "
        text += f"จุดเด่น: {highlights} "
        text += f"อาชีพ: {careers} "
        text += f"แท็ก: {tags} "
        text += f"รายละเอียด: {c.description or ''}"
        
        text = text[:6000]
        tasks.append((c.id, text))
        
    db.close()

    BATCH_SIZE = 15
    completed = 0
    
    for i in range(0, len(tasks), BATCH_SIZE):
        batch = tasks[i:i+BATCH_SIZE]
        db = SessionLocal()
        
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            future_to_id = {executor.submit(generate_embedding_for_course, tid, txt): tid for tid, txt in batch}
            
            for future in as_completed(future_to_id):
                course_id, vector, err = future.result()
                if vector:
                    c = db.query(CourseDB).filter(CourseDB.id == course_id).first()
                    if c:
                        c.embedding = vector
                        c.embedding_text = [t for cid, t in batch if cid == course_id][0]
                        completed += 1
                else:
                    print(f"Failed {course_id}: {err}")
        
        db.commit()
        db.close()
        print(f"Progress: {completed} / {len(tasks)}")
        
        # Sleep slightly to avoid 1500 RPM / rate limits
        time.sleep(1)

    print("Embedding generation complete!")

if __name__ == '__main__':
    main()
