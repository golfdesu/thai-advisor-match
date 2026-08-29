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

API_KEYS=[k.strip() for k in os.getenv("GEMINI_API_KEYS","").split(",") if k.strip()]
_clients={}
lock=threading.Lock()
idx=0
def get_client():
    global idx
    with lock:
        k=API_KEYS[idx % len(API_KEYS)]
        idx=(idx+1)%len(API_KEYS)
        if k not in _clients:
            _clients[k]=genai.Client(api_key=k)
        return _clients[k]

class CourseSchema(BaseModel):
    id: str
    title_th: str
    title_en: str
    degree_level: str
    degree_name: str
    university: str
    university_th: str
    faculty: str
    faculty_th: str
    department: str
    department_th: str
    program_type: str
    duration_years: str
    total_credits: str
    tuition_per_semester: str
    tuition_total: str
    description: str
    curriculum_highlights: list[str]
    career_paths: list[str]
    tags: list[str]
class ExtractedCourses(BaseModel):
    courses: list[CourseSchema]

SERPAPI_KEY=os.getenv("SERPAPI_KEY","").strip().strip('"').strip("'")

QUERIES=[
    ("Mahidol University","Mahidol University Faculty of Medicine programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Dentistry programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Pharmacy programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Engineering programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Nursing programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Public Health programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Tropical Medicine programs site:mahidol.ac.th"),
    ("Mahidol University","Mahidol University Faculty of Veterinary programs site:mahidol.ac.th"),
]

def search(q, num=3):
    url=f"https://serpapi.com/search.json?q={urllib.parse.quote(q)}&api_key={SERPAPI_KEY}&num={num}"
    try:
        r=requests.get(url, timeout=15)
        data=r.json()
        links=[x["link"] for x in data.get("organic_results",[]) if "link" in x]
        return links[:3]
    except Exception as e:
        print(f" serp err {q[:40]}: {e}")
        return []

def fetch(url):
    try:
        h={'User-Agent':'Mozilla/5.0'}
        r=requests.get(url, headers=h, timeout=20, verify=False)
        r.raise_for_status()
        soup=BeautifulSoup(r.content,'html.parser')
        for t in soup(["script","style","nav","footer"]):
            t.decompose()
        return soup.get_text(separator=' ', strip=True)[:15000]
    except Exception as e:
        print(f" fetch fail {url[:60]}: {e}")
        return ""

def extract(txt, url, uni):
    if len(txt)<400:
        return []
    prompt=f"""You are a data extraction AI. Extract all academic programs/curricula mentioned in the text.
Target University: {uni}. Use ONLY text provided, DO NOT hallucinate. If tuition/credits not mentioned write "ไม่ระบุ".
Website: {url}

TEXT:
{txt}
"""
    client=get_client()
    try:
        resp=client.models.generate_content(model='gemini-3.6-flash', contents=prompt, config={'response_mime_type':'application/json','response_schema':ExtractedCourses,'temperature':0.1})
        if resp.text:
            data=json.loads(resp.text)
            courses=data.get("courses",[])
            for c in courses:
                c["website_url"]=url
            return courses
    except Exception as e:
        print(f" AI err {url[:50]}: {e}")
    return []

def main():
    import urllib3
    urllib3.disable_warnings()
    Base.metadata.create_all(bind=engine)
    total_ins=total_upd=0
    for uni, q in QUERIES:
        print(f"\n=== {uni} | {q[:60]} ===")
        urls=search(q, 3)
        print(f" urls: {urls}")
        all_courses=[]
        for url in urls:
            txt=fetch(url)
            print(f"  fetched {len(txt)} from {url[:70]}")
            courses=extract(txt, url, uni)
            print(f"    -> {len(courses)}")
            all_courses.extend(courses)
            time.sleep(4)
        if not all_courses:
            print("  No courses")
            time.sleep(1)
            continue
        seen={}
        for c in all_courses:
            if c["id"] not in seen:
                seen[c["id"]]=c
        unique=list(seen.values())
        print(f"  unique {len(unique)}")
        session=SessionLocal()
        ins=upd=0
        for c in unique:
            emb=f"{c.get('title_th','')} {c.get('title_en','')} {c.get('faculty_th','')}"
            vec=embedding_service.get_embedding(emb)
            c["embedding_text"]=emb
            c["embedding"]=vec if vec and len(vec)==768 else None
            ex=session.query(CourseDB).filter_by(id=c["id"]).first()
            try:
                if ex:
                    for k,v in c.items():
                        setattr(ex,k,v)
                    upd+=1
                else:
                    session.add(CourseDB(**c))
                    ins+=1
                session.commit()
            except Exception as e:
                print(f" DB err {c['id']}: {e}")
                session.rollback()
        session.close()
        print(f"  done ins={ins} upd={upd}")
        total_ins+=ins
        total_upd+=upd
        time.sleep(2)
    print(f"\nDONE total ins={total_ins} upd={total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        q1 = text("SELECT count(*) FROM courses WHERE university='Mahidol University'")
        q2 = text("SELECT count(*) FROM courses")
        print(f"MU total {conn.execute(q1).scalar()}")
        print(f"DB total {conn.execute(q2).scalar()}")

if __name__=="__main__":
    main()
