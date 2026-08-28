import os, sys, json, time, threading, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), override=True)
from bs4 import BeautifulSoup
from google import genai
from pydantic import BaseModel, Field
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS","").split(",") if k.strip()]
_clients = {}
key_lock = threading.Lock()
idx = 0
def get_client():
    global idx
    with key_lock:
        key = API_KEYS[idx % len(API_KEYS)]
        idx = (idx+1) % len(API_KEYS)
        if key not in _clients:
            _clients[key] = genai.Client(api_key=key)
        return _clients[key]

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

TARGETS = [
    ("King Mongkut's University of Technology Thonburi", "https://www.sit.kmutt.ac.th/bsc/"),
    ("King Mongkut's University of Technology Thonburi", "https://www.sit.kmutt.ac.th/msc/"),
    ("King Mongkut's University of Technology Thonburi", "https://fibo.kmutt.ac.th/prospective-students/undergraduate/curriculum/"),
    ("King Mongkut's University of Technology Thonburi", "https://www.kmutt.ac.th/education/curriculum/faculty-of-science/"),
    ("King Mongkut's Institute of Technology Ladkrabang", "https://www.eng.kmitl.ac.th/"),
    ("King Mongkut's Institute of Technology Ladkrabang", "https://www.kmitl.ac.th/academics/programs"),
    ("King Mongkut's Institute of Technology Ladkrabang", "http://www.math.sci.kmitl.ac.th/"),
    ("King Mongkut's Institute of Technology Ladkrabang", "https://agri.eng.kmitl.ac.th/course/"),
]

def fetch(url):
    try:
        headers={'User-Agent':'Mozilla/5.0'}
        r=requests.get(url, headers=headers, timeout=15, verify=False)
        r.raise_for_status()
        soup=BeautifulSoup(r.content,'html.parser')
        for t in soup(["script","style","nav","footer"]):
            t.decompose()
        txt=soup.get_text(separator=' ', strip=True)
        return txt[:15000]
    except Exception as e:
        print(f"fetch fail {url}: {e}")
        return ""

def extract(txt, url, uni):
    if len(txt)<400:
        print(f"skip short {url} {len(txt)}")
        return []
    prompt = f"""You are a data extraction AI. Extract all academic programs/curricula mentioned in the text.
Target University: {uni}. Use only text provided, DO NOT hallucinate. If tuition/credits not mentioned write "ไม่ระบุ".
Website: {url}

TEXT:
{txt}
"""
    client=get_client()
    try:
        resp=client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config={'response_mime_type':'application/json','response_schema':ExtractedCourses,'temperature':0.1}
        )
        if resp.text:
            data=json.loads(resp.text)
            courses=data.get("courses",[])
            for c in courses:
                c["website_url"]=url
            print(f"  -> extracted {len(courses)} from {url}")
            return courses
    except Exception as e:
        print(f"AI err {url}: {e}")
    return []

def main():
    import urllib3
    urllib3.disable_warnings()
    Base.metadata.create_all(bind=engine)
    all_courses=[]
    for uni, url in TARGETS:
        print(f"--- {uni} : {url}")
        txt=fetch(url)
        print(f"  fetched {len(txt)} chars")
        courses=extract(txt, url, uni)
        all_courses.extend(courses)
        time.sleep(0.8)
    print(f"Total extracted {len(all_courses)}")
    # dedup
    seen={}
    for c in all_courses:
        cid=c.get("id")
        if cid not in seen:
            seen[cid]=c
    unique=list(seen.values())
    print(f"Unique {len(unique)}")
    if not unique:
        return
    session=SessionLocal()
    ins=upd=0
    for c in unique:
        emb_text=f"{c.get('title_th','')} {c.get('title_en','')} {c.get('faculty_th','')} {c.get('description','')} {', '.join(c.get('curriculum_highlights',[]))}"
        vec=embedding_service.get_embedding(emb_text)
        c["embedding_text"]=emb_text
        c["embedding"]=vec if vec and len(vec)==768 else None
        existing=session.query(CourseDB).filter_by(id=c["id"]).first()
        try:
            if existing:
                for k,v in c.items():
                    setattr(existing,k,v)
                upd+=1
            else:
                session.add(CourseDB(**c))
                ins+=1
            session.commit()
            print(f"  committed {c['id']} {'update' if existing else 'insert'}")
        except Exception as e:
            print(f"DB err {c.get('id')}: {e}")
            session.rollback()
    session.close()
    print(f"Done inserted {ins} updated {upd}")

if __name__=="__main__":
    main()
