import os, sys, json, time, threading, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), override=True)
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
        k=API_KEYS[idx%len(API_KEYS)]
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

TARGETS=[
    ("Chulalongkorn University","https://www.arts.chula.ac.th/th/master-education/"),
    ("Chulalongkorn University","https://www.arts.chula.ac.th/th/phd-education/"),
    ("Chulalongkorn University","https://www.arts.chula.ac.th/th/"),
    ("Mahidol University","https://apply.cm.mahidol.ac.th/web/programs/master-degree/th"),
    ("Mahidol University","https://la.mahidol.ac.th/th/prospective-students/"),
    ("Mahidol University","https://graduate.mahidol.ac.th/Admission/announce/cur_open_list.php?Level=M"),
    ("Mahidol University","https://www.mahidol.ac.th/Academics/Curriculum"),
]

def fetch(url):
    try:
        h={'User-Agent':'Mozilla/5.0'}
        r=requests.get(url, headers=h, timeout=15, verify=False)
        r.raise_for_status()
        soup=BeautifulSoup(r.content,'html.parser')
        for t in soup(["script","style","nav","footer"]):
            t.decompose()
        return soup.get_text(separator=' ', strip=True)[:15000]
    except Exception as e:
        print(f"fetch fail {url}: {e}")
        return ""

def extract(txt, url, uni):
    if len(txt)<400:
        print(f"skip {url} len {len(txt)}")
        return []
    prompt=f"""You are a data extraction AI. Extract all academic programs/curricula mentioned in the text.
Target University: {uni}. Use only text provided, DO NOT hallucinate. If tuition/credits not mentioned write "ไม่ระบุ".
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
            print(f" -> {len(courses)} from {url[:70]}")
            return courses
    except Exception as e:
        print(f"AI err {url[:50]}: {e}")
    return []

def main():
    import urllib3
    urllib3.disable_warnings()
    Base.metadata.create_all(bind=engine)
    all_courses=[]
    for uni,url in TARGETS:
        print(f"--- {uni} {url}")
        txt=fetch(url)
        print(f" fetched {len(txt)}")
        courses=extract(txt, url, uni)
        all_courses.extend(courses)
        time.sleep(0.7)
    print(f"total {len(all_courses)}")
    seen={}
    for c in all_courses:
        if c["id"] not in seen:
            seen[c["id"]]=c
    unique=list(seen.values())
    print(f"unique {len(unique)}")
    session=SessionLocal()
    ins=upd=0
    for c in unique:
        emb=f"{c.get('title_th','')} {c.get('title_en','')} {c.get('faculty_th','')} {c.get('description','')}"
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
            print(f" {c['id']} {'upd' if ex else 'ins'}")
        except Exception as e:
            print(f"DB err {c['id']}: {e}")
            session.rollback()
    session.close()
    print(f"done ins={ins} upd={upd}")

if __name__=="__main__":
    main()
