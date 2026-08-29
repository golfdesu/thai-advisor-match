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
if not API_KEYS:
    API_KEYS=[os.getenv("GEMINI_API_KEY","").strip()]
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

TARGETS=[
    ("Mahidol University", 629),
    ("Chulalongkorn University", 456),
    ("Chiang Mai University", 334),
    ("Thammasat University", 200),
    ("Kasetsart University", 200),
    ("Khon Kaen University", 200),
    ("Srinakharinwirot University", 200),
    ("Prince of Songkla University", 150),
    ("Burapha University", 150),
    ("Silpakorn University", 150),
    ("Suranaree University of Technology", 100),
    ("National Institute of Development Administration", 45),
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
        h={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r=requests.get(url, headers=h, timeout=20, verify=False)
        r.raise_for_status()
        soup=BeautifulSoup(r.content,'html.parser')
        for t in soup(["script","style","nav","footer"]):
            t.decompose()
        txt=soup.get_text(separator=' ', strip=True)
        return txt[:15000]
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

def process_uni(uni, target):
    print(f"\n=== {uni} (target {target}) ===")
    q=f'"{uni}" หลักสูตร ปริญญาตรี ปริญญาโท site:.ac.th'
    urls=search(q, 3)
    print(f" urls: {urls}")
    all_courses=[]
    for url in urls:
        txt=fetch(url)
        print(f"  fetched {len(txt)} from {url[:70]}")
        courses=extract(txt, url, uni)
        print(f"    -> {len(courses)} courses")
        all_courses.extend(courses)
        time.sleep(0.7)
    if not all_courses:
        print(f"  No courses for {uni}")
        return 0,0
    # dedup by id
    seen={}
    for c in all_courses:
        if c["id"] not in seen:
            seen[c["id"]]=c
    unique=list(seen.values())
    print(f"  unique {len(unique)} for {uni}")
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
    print(f"  {uni} done ins={ins} upd={upd}")
    return ins, upd

def main():
    import urllib3
    urllib3.disable_warnings()
    Base.metadata.create_all(bind=engine)
    total_ins=total_upd=0
    for uni, target in TARGETS:
        ins,upd=process_uni(uni, target)
        total_ins+=ins
        total_upd+=upd
        time.sleep(1)
    print(f"\nDONE total ins={total_ins} upd={total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        print(f"DB total {conn.execute(text('SELECT count(*) FROM courses')).scalar()}")
        for uni,_ in TARGETS:
            cnt=conn.execute(text(f"SELECT count(*) FROM courses WHERE university='{uni}'")).scalar()
            print(f" {uni[:32]:32} {cnt}")

if __name__=="__main__":
    main()
