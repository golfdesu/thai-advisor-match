import os, sys, json, time, threading, urllib.parse, requests
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
from scripts.agentic_pipeline.content_pruner import ContentPruner

SERPAPI_KEYS = [k.strip().strip('"').strip("'") for k in os.getenv("SERPAPI_KEYS", "").split(",") if k.strip()]
if not SERPAPI_KEYS and os.getenv("SERPAPI_KEY"):
    single_serp = os.getenv("SERPAPI_KEY", "").strip().strip('"').strip("'")
    if single_serp:
        SERPAPI_KEYS = [single_serp]

serp_lock = threading.Lock()
current_serp_idx = 0

def get_serpapi_key():
    global current_serp_idx
    if not SERPAPI_KEYS:
        return ""
    with serp_lock:
        key = SERPAPI_KEYS[current_serp_idx % len(SERPAPI_KEYS)]
        current_serp_idx = (current_serp_idx + 1) % len(SERPAPI_KEYS)
        return key

API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS","").split(",") if k.strip()]
if not API_KEYS:
    API_KEYS = [os.getenv("GEMINI_API_KEY","").strip()]
_clients={}
lock=threading.Lock()
idx=0
def get_client():
    global idx
    with lock:
        key=API_KEYS[idx % len(API_KEYS)]
        idx=(idx+1)%len(API_KEYS)
        if key not in _clients:
            _clients[key]=genai.Client(api_key=key)
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

def search(q, num=3):
    api_key = get_serpapi_key()
    if not api_key:
        return []
    url=f"https://serpapi.com/search.json?q={urllib.parse.quote(q)}&api_key={api_key}&num={num}"
    try:
        r=requests.get(url, timeout=15)
        data=r.json()
        links=[x["link"] for x in data.get("organic_results",[]) if "link" in x]
        return links[:3]  # strict limit to 3
    except Exception as e:
        print(f"serp err {q}: {e}")
        return []

def fetch(url):
    try:
        h = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        r = requests.get(url, headers=h, timeout=15, verify=False)
        r.raise_for_status()
        # Apply SKILL.state ContentPruner to eliminate boilerplate nav/footer noise (80%+ token reduction)
        return ContentPruner.prune_html(r.text, max_output_chars=25000)
    except Exception as e:
        print(f"fetch fail {url}: {e}")
        return ""

def extract(txt, url, uni):
    if len(txt)<400:
        return []
    prompt=f"""You are a data extraction AI. Extract all academic programs/curricula mentioned in the text.
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
            return courses
    except Exception as e:
        print(f"AI err {url[:60]}: {e}")
    return []

def process_and_commit(uni, q):
    print(f"--- {uni} | {q} ---")
    urls=search(q)
    print(f"  urls: {urls}")
    all_courses=[]
    for url in urls:
        txt=fetch(url)
        print(f"  fetched {len(txt)} from {url[:70]}")
        courses=extract(txt, url, uni)
        print(f"    -> {len(courses)} courses")
        all_courses.extend(courses)
        time.sleep(0.6)
    if not all_courses:
        print("  no courses for this query")
        return 0,0
    # dedup within query
    seen={}
    for c in all_courses:
        if c["id"] not in seen:
            seen[c["id"]]=c
    unique=list(seen.values())
    print(f"  unique {len(unique)} for query")
    session=SessionLocal()
    ins=upd=0
    # Egress guard: one batched IN query for existence check (id-only — no
    # full rows shipped) instead of N per-course .first() round trips.
    unique_ids=[c["id"] for c in unique]
    existing_ids={r.id for r in session.query(CourseDB.id).filter(CourseDB.id.in_(unique_ids)).all()}
    for c in unique:
        emb_text=f"{c.get('title_th','')} {c.get('title_en','')} {c.get('faculty_th','')} {c.get('description','')} {', '.join(c.get('curriculum_highlights',[]))}"
        vec=embedding_service.get_embedding(emb_text)
        c["embedding_text"]=emb_text
        c["embedding"]=vec if vec and len(vec)==768 else None
        # Re-attach only on update path; inserts need no prior read at all.
        existing=session.get(CourseDB, c["id"]) if c["id"] in existing_ids else None
        try:
            if existing:
                for k,v in c.items():
                    setattr(existing,k,v)
                upd+=1
            else:
                session.add(CourseDB(**c))
                ins+=1
            session.commit()
        except Exception as e:
            print(f"DB err {c['id']}: {e}")
            session.rollback()
    session.close()
    print(f"  committed ins={ins} upd={upd}")
    return ins,upd

def main():
    import urllib3
    urllib3.disable_warnings()
    Base.metadata.create_all(bind=engine)
    total_ins=total_upd=0
    for uni,q in QUERIES:
        ins,upd=process_and_commit(uni,q)
        total_ins+=ins
        total_upd+=upd
        time.sleep(1)
    print(f"DONE total ins={total_ins} upd={total_upd}")

if __name__=="__main__":
    main()
