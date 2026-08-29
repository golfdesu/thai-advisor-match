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

MODEL="gemini-3.6-flash"

QUERIES=[
    ("Chiang Mai University","site:eng.cmu.ac.th หลักสูตร"),
    ("Chiang Mai University","site:science.cmu.ac.th หลักสูตร"),
    ("Chiang Mai University","site:med.cmu.ac.th หลักสูตร"),
    ("Chulalongkorn University","site:eng.chula.ac.th หลักสูตร"),
    ("Chulalongkorn University","site:science.chula.ac.th หลักสูตร"),
    ("Chulalongkorn University","site:commerce.chula.ac.th หลักสูตร OR site:account.chula.ac.th หลักสูตร"),
    ("Chulalongkorn University","site:med.chula.ac.th หลักสูตร"),
    ("Chulalongkorn University","site:law.chula.ac.th หลักสูตร"),
    ("Mahidol University","site:med.mahidol.ac.th หลักสูตร OR site:si.mahidol.ac.th หลักสูตร"),
    ("Mahidol University","site:sc.mahidol.ac.th หลักสูตร"),
    ("Mahidol University","site:eng.mahidol.ac.th หลักสูตร"),
    ("Mahidol University","site:ph.mahidol.ac.th หลักสูตร"),
    ("Mahidol University","site:graduate.mahidol.ac.th หลักสูตร ปริญญาโท ปริญญาเอก"),
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
        resp=client.models.generate_content(model=MODEL, contents=prompt, config={'response_mime_type':'application/json','response_schema':ExtractedCourses,'temperature':0.1})
        if resp.text:
            data=json.loads(resp.text)
            courses=data.get("courses",[])
            for c in courses:
                c["website_url"]=url
            return courses
    except Exception as e:
        print(f" AI err {url[:50]}: {e}")
    return []

def process_query(uni, q):
    print(f"\n=== {uni} | {q[:60]} ===")
    urls=search(q, 3)
    print(f" urls: {urls}")
    all_courses=[]
    for url in urls:
        txt=fetch(url)
        print(f"  fetched {len(txt)} from {url[:70]}")
        courses=extract(txt, url, uni)
        print(f"    -> {len(courses)} courses")
        all_courses.extend(courses)
        time.sleep(0.5)
    if not all_courses:
        print("  No courses")
        return 0,0
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
    return ins, upd

def main():
    import urllib3
    urllib3.disable_warnings()
    Base.metadata.create_all(bind=engine)
    total_ins=total_upd=0
    for uni, q in QUERIES:
        ins,upd=process_query(uni, q)
        total_ins+=ins
        total_upd+=upd
        time.sleep(1)
    print(f"\nDONE total ins={total_ins} upd={total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        for uni in ["Chiang Mai University","Chulalongkorn University","Mahidol University"]:
            cnt=conn.execute(text(f"SELECT count(*) FROM courses WHERE university='{uni}'")).scalar()
            print(f" {uni[:30]:30} {cnt}")
        print("total", conn.execute(text("SELECT count(*) FROM courses")).scalar())

if __name__=="__main__":
    main()
