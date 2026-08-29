import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re, requests, json, time, threading, urllib.parse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup
from google import genai
from pydantic import BaseModel, Field
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from dotenv import load_dotenv

load_dotenv()
API_KEYS=[k.strip() for k in os.getenv("GEMINI_API_KEYS","").split(",") if k.strip()]
_clients={}
lock=threading.Lock()
idx=0

def get_client():
    global idx
    with lock:
        k=API_KEYS[idx % len(API_KEYS)]
        idx+=1
        if k not in _clients:
            _clients[k]=genai.Client(api_key=k)
        return _clients[k]

class CourseList(BaseModel):
    courses: list[dict] = Field(description="List of courses extracted.")

def search_google(query):
    print(f"Searching: {query}")
    h = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get("https://html.duckduckgo.com/html/?q="+urllib.parse.quote(query), headers=h, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        res = soup.find_all('a', class_='result__snippet')
        return " ".join([x.text for x in res])[:2500]
    except Exception as e:
        print("Search error:", e)
        return ""

def extract_courses(faculty):
    queries = [
        f"หลักสูตรปริญญาโท {faculty} มหาวิทยาลัยเกษตรศาสตร์",
        f"หลักสูตรปริญญาเอก {faculty} มหาวิทยาลัยเกษตรศาสตร์"
    ]
    all_text = ""
    for q in queries:
        all_text += search_google(q) + "\n"
        time.sleep(1)
        
    if len(all_text.strip()) < 50:
        return []
        
    client = get_client()
    prompt = f"""
    คุณคือนักสกัดข้อมูลหลักสูตรปริญญาโทและเอก จากข้อความค้นหาด้านล่าง
    สกัดเฉพาะหลักสูตรที่เป็นของมหาวิทยาลัยเกษตรศาสตร์ (Kasetsart University) คณะ: {faculty} เท่านั้น
    
    ส่งกลับเป็น JSON list of objects:
    [
      {{
        "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชา...", 
        "title_en": "Master of Science in ...", 
        "degree_level": "Master" or "Doctorate"
      }}
    ]
    ถ้าไม่มี ให้ส่ง []
    
    ข้อความ:
    {all_text}
    """
    
    try:
        resp = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        data = json.loads(resp.text)
        if isinstance(data, dict) and "courses" in data:
            return data["courses"]
        elif isinstance(data, list):
            return data
        return []
    except Exception as e:
        print("LLM Error:", e)
        return []

def run():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    faculties = [
        "คณะเกษตร", "คณะวิทยาศาสตร์", "คณะวิศวกรรมศาสตร์", "คณะบริหารธุรกิจ",
        "คณะเศรษฐศาสตร์", "คณะมนุษยศาสตร์", "คณะสังคมศาสตร์", "คณะศึกษาศาสตร์",
        "คณะสัตวแพทยศาสตร์", "คณะอุตสาหกรรมเกษตร", "คณะสิ่งแวดล้อม", "คณะประมง",
        "คณะวนศาสตร์", "คณะสถาปัตยกรรมศาสตร์", "คณะเทคนิคการสัตวแพทย์"
    ]
    
    print("Starting KU Grad AI Extraction...")
    total_ins = 0
    total_upd = 0
    for f in faculties:
        courses = extract_courses(f)
        for c in courses:
            title_th = c.get("title_th", "")
            title_en = c.get("title_en", "")
            if not title_th and not title_en: continue
            if "title_th" not in c: c["title_th"] = "ไม่ระบุ"
            if "title_en" not in c: c["title_en"] = "ไม่ระบุ"
            
            # Avoid inserting non-grad stuff
            if "ปริญญาตรี" in title_th or "Bachelor" in title_en: continue
            
            c["university"] = "Kasetsart University"
            c["university_th"] = "มหาวิทยาลัยเกษตรศาสตร์"
            c["faculty"] = f
            c["faculty_th"] = f
            
            import hashlib
            raw_id = f"ku-grad-{f}-{title_th}-{title_en}"
            c["id"] = hashlib.md5(raw_id.encode('utf-8')).hexdigest()
            
            c["degree_level"] = c.get("degree_level", "Master")
            c["degree_name"] = "M.Sc./M.A." if c["degree_level"] == "Master" else "Ph.D."
            c["program_type"] = "Graduate"
            c["department"] = "ไม่ระบุ"
            c["department_th"] = "ไม่ระบุ"
            c["duration_years"] = "2" if c["degree_level"] == "Master" else "3"
            c["tuition_per_semester"] = "ไม่ระบุ"
            c["tuition_total"] = "ไม่ระบุ"
            c["description"] = "Graduate program at Kasetsart University."
            c["website_url"] = "https://www.grad.ku.ac.th/"
            
            emb_text = f"{c['title_th']} {c['title_en']} {c['faculty_th']} Kasetsart University"
            c["embedding_text"] = emb_text
            
            ex = session.query(CourseDB).filter_by(id=c["id"]).first()
            if ex:
                total_upd += 1
            else:
                vec = embedding_service.get_embedding(emb_text)
                c["embedding"] = vec if vec and len(vec) == 768 else None
                session.add(CourseDB(**c))
                total_ins += 1
        session.commit()
        print(f" - {f}: Inserted {len(courses)} courses.")
        
    print(f"\nDone! Inserted: {total_ins}, Updated: {total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        q = text("SELECT count(*) FROM courses WHERE university='Kasetsart University'")
        print(f"KU total: {conn.execute(q).scalar()}")

if __name__ == "__main__":
    run()
