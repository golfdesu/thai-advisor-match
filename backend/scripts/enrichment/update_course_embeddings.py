import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",")] if os.getenv("GEMINI_API_KEYS") else [os.getenv("GEMINI_API_KEY")]
from google import genai
import threading
key_lock = threading.Lock()
current_key_idx = 0

def get_client():
    global current_key_idx
    with key_lock:
        return genai.Client(api_key=API_KEYS[current_key_idx])

def rotate_key():
    global current_key_idx
    with key_lock:
        current_key_idx = (current_key_idx + 1) % len(API_KEYS)
        print(f"Rotated to API Key {current_key_idx+1}/{len(API_KEYS)}")

def generate_embedding_for_course(course_id, text):
    max_retries = 25
    for attempt in range(max_retries):
        try:
            client = get_client()
            response = client.models.embed_content(
                model='gemini-embedding-2',
                contents=text,
                config={'output_dimensionality': 768}
            )
            return (course_id, response.embeddings[0].values, None)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "401" in error_str or "UNAUTHENTICATED" in error_str:
                rotate_key()
                time.sleep(1)
            else:
                return (course_id, None, error_str)
    return (course_id, None, "Max retries exceeded across keys")

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

    from concurrent.futures import ThreadPoolExecutor, as_completed
    completed = 0
    total = len(tasks)
    
    # Use 50 concurrent workers to blast through the requests using all 17 keys
    # When a key hits 429 (100 RPM limit), it instantly rotates to the next key.
    # 17 keys * 100 RPM = 1,700 RPM capacity!
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_id = {executor.submit(generate_embedding_for_course, tid, txt): tid for tid, txt in tasks}
        
        db = SessionLocal()
        for future in as_completed(future_to_id):
            course_id, vector, err = future.result()
            if vector:
                c = db.query(CourseDB).filter(CourseDB.id == course_id).first()
                if c:
                    c.embedding = vector
                    c.embedding_text = [t for cid, t in tasks if cid == course_id][0]
                    completed += 1
                    
                    # Commit every 50 records to not lock the DB too long
                    if completed % 50 == 0:
                        db.commit()
                        print(f"Progress: {completed} / {total}", flush=True)
            else:
                print(f"Failed {course_id}: {err}", flush=True)
                
        db.commit()
        db.close()

    print(f"Final Progress: {completed} / {total}", flush=True)
    print("Embedding generation complete!", flush=True)

if __name__ == '__main__':
    main()
