"""
Wave2 targeted crawler for KMUTT & KMITL (fill gaps after first generic crawl)
Queries per faculty/subdomain + Gemini 3.6 Flash extraction + embedding
"""
import os, sys, json, time, re, threading, urllib.parse, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)
load_dotenv(os.path.join(BACKEND_DIR, '.env'), override=True)

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    from app.core.embedding_service import embedding_service
    DB_AVAILABLE = True
except ImportError as e:
    print("DB import failed", e)
    DB_AVAILABLE = False

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip().strip('"').strip("'")
API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
if not API_KEYS:
    single = os.getenv("GEMINI_API_KEY","").strip()
    if single:
        API_KEYS = [single]

key_lock = threading.Lock()
current_key_idx = 0
_clients = {}

def get_client():
    global current_key_idx
    with key_lock:
        key = API_KEYS[current_key_idx % len(API_KEYS)]
        current_key_idx = (current_key_idx + 1) % len(API_KEYS)
        if key not in _clients:
            _clients[key] = genai.Client(api_key=key)
        return _clients[key]

class CourseSchema(BaseModel):
    id: str = Field(description="Unique ID (e.g. kmutt_sit_cs_bsc2)")
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

TARGET_QUERIES = [
    ("King Mongkut's University of Technology Thonburi", "site:sit.kmutt.ac.th หลักสูตร ปริญญาตรี ปริญญาโท"),
    ("King Mongkut's University of Technology Thonburi", "site:fibo.kmutt.ac.th หลักสูตร"),
    ("King Mongkut's University of Technology Thonburi", "site:kmutt.ac.th หลักสูตร คณะวิศวกรรมศาสตร์ คณะวิทยาศาสตร์"),
    ("King Mongkut's Institute of Technology Ladkrabang", "site:eng.kmitl.ac.th หลักสูตร ปริญญาตรี ปริญญาโท"),
    ("King Mongkut's Institute of Technology Ladkrabang", "site:sci.kmitl.ac.th OR site:arch.kmitl.ac.th หลักสูตร"),
    ("King Mongkut's Institute of Technology Ladkrabang", "site:kmitl.ac.th หลักสูตร ปริญญาตรี ปริญญาโท ปริญญาเอก"),
]

def search_serpapi(query: str, num=3):
    if not SERPAPI_KEY:
        return []
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(query)}&api_key={SERPAPI_KEY}&num={num}"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        return [r["link"] for r in data.get("organic_results", []) if "link" in r]
    except Exception as e:
        print(f"SerpAPI error for {query}: {e}")
        return []

def fetch_text(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        for tag in soup(["script","style","nav","footer"]):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text[:15000]
    except Exception as e:
        print(f"fetch err {url}: {e}")
        return ""

def extract(text: str, url: str, uni: str):
    if len(text) < 400:
        return []
    prompt = f"""You are a data extraction AI. Extract all academic programs/curricula mentioned in the text.
Target University: {uni}. Use only text provided, DO NOT hallucinate. If tuition/credits not mentioned write "ไม่ระบุ".
Website: {url}

TEXT:
{text}
"""
    client = get_client()
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': ExtractedCourses,
                'temperature': 0.1
            }
        )
        if response.text:
            data = json.loads(response.text)
            courses = data.get("courses", [])
            for c in courses:
                c["website_url"] = url
            return courses
    except Exception as e:
        print(f"AI err {url}: {e}")
    return []

def process_query(uni, query):
    print(f"--- Query: {uni} | {query[:60]} ---")
    urls = search_serpapi(query, num=3)
    print(f"  URLs: {urls}")
    all_courses = []
    for url in urls:
        print(f"  Scraping {url} ...")
        text = fetch_text(url)
        courses = extract(text, url, uni)
        if courses:
            print(f"    -> {len(courses)} courses")
            all_courses.extend(courses)
        time.sleep(0.5)
    return all_courses

def main():
    import urllib3
    urllib3.disable_warnings()
    if DB_AVAILABLE:
        Base.metadata.create_all(bind=engine)
    all_results = []
    # Sequential to respect rate limits (Gemini + SerpAPI)
    for uni, q in TARGET_QUERIES:
        courses = process_query(uni, q)
        all_results.extend(courses)
        time.sleep(1)

    print(f"\nTotal extracted before dedup: {len(all_results)}")
    # Deduplicate by id
    seen = {}
    for c in all_results:
        cid = c.get("id")
        if cid not in seen:
            seen[cid] = c
        else:
            # keep longer description
            if len(c.get("description","")) > len(seen[cid].get("description","")):
                seen[cid] = c
    unique = list(seen.values())
    print(f"Unique courses: {len(unique)}")

    if not unique or not DB_AVAILABLE:
        print("Nothing to seed")
        return

    # Insert with embeddings
    session = SessionLocal()
    inserted = updated = 0
    for c in unique:
        # Build embedding text
        highlights = ", ".join(c.get("curriculum_highlights",[]))
        careers = ", ".join(c.get("career_paths",[]))
        tags = ", ".join(c.get("tags",[]))
        emb_text = f"{c.get('title_th','')} {c.get('title_en','')} Faculty:{c.get('faculty_th','')} Dept:{c.get('department_th','')} Highlights:{highlights} Careers:{careers} Tags:{tags} Desc:{c.get('description','')}"
        emb_vec = embedding_service.get_embedding(emb_text)
        c["embedding_text"] = emb_text
        c["embedding"] = emb_vec if (emb_vec and len(emb_vec)==768) else None

        existing = session.query(CourseDB).filter_by(id=c["id"]).first()
        try:
            if existing:
                for k,v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
        except Exception as e:
            print(f"DB skip {c.get('id')}: {e}")
            session.rollback()
            continue
        # commit per course to avoid big transaction lock but flush embeddings
        try:
            session.commit()
        except Exception as e:
            print(f"Commit err {c.get('id')}: {e}")
            session.rollback()
    session.close()
    print(f"=== Wave2 done: inserted {inserted} updated {updated} total unique {len(unique)} ===")

if __name__ == "__main__":
    main()
