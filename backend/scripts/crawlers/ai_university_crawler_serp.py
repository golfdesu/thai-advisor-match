"""
AI-Powered Universal University Crawler (SerpApi Version)
"""
import os, sys, json, time, re, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BACKEND_DIR)
sys.path.append(SCRIPTS_DIR)
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",")] if os.getenv("GEMINI_API_KEYS") else [os.getenv("GEMINI_API_KEY")]

key_lock = threading.Lock()
current_key_idx = 0

def get_client():
    global current_key_idx
    with key_lock:
        key = API_KEYS[current_key_idx]
        current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    return genai.Client(api_key=key)

UNIVERSITIES = sys.argv[1:]
if not UNIVERSITIES:
    print("Please provide university names as arguments.")
    sys.exit(1)

class CourseSchema(BaseModel):
    id: str = Field(description="Unique ID for the course (e.g. psu_sci_bio)")
    title_th: str = Field(description="Full program name in Thai")
    title_en: str = Field(description="Full program name in English")
    degree_level: str = Field(description="ปริญญาตรี, ปริญญาโท, or ปริญญาเอก")
    degree_name: str = Field(description="Official degree abbreviation (e.g. วท.บ.)")
    university: str = Field(description="University name in English")
    university_th: str = Field(description="University name in Thai")
    faculty: str = Field(description="Faculty name in English")
    faculty_th: str = Field(description="Faculty name in Thai")
    department: str = Field(description="Department name in English")
    department_th: str = Field(description="Department name in Thai")
    program_type: str = Field(description="ภาคปกติ, ภาคพิเศษ, or นานาชาติ")
    duration_years: str = Field(description="e.g. 4 ปี")
    total_credits: str = Field(description="e.g. 130 หน่วยกิต")
    tuition_per_semester: str = Field(description="e.g. 15,000 บาท")
    tuition_total: str = Field(description="e.g. 120,000 บาท")
    description: str = Field(description="Brief summary of the program")
    curriculum_highlights: list[str] = Field(description="2-4 key subjects or highlights")
    career_paths: list[str] = Field(description="2-4 potential careers")
    tags: list[str] = Field(description="2-5 relevant tags")

class ExtractedCourses(BaseModel):
    courses: list[CourseSchema]

def search_serpapi(query: str) -> list[str]:
    if not SERPAPI_KEY:
        return []
    url = f"https://serpapi.com/search.json?q={query}&api_key={SERPAPI_KEY}&num=3"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        results = data.get("organic_results", [])
        return [r["link"] for r in results if "link" in r]
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return []

def fetch_text_from_url(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text[:15000]
    except Exception as e:
        return ""

def extract_courses_with_ai(text: str, url: str, university: str) -> list[dict]:
    if len(text) < 500: return []
    prompt = f"""
    You are a data extraction AI. Extract all academic programs/curricula (Bachelor's, Master's, Ph.D.) mentioned in the following text.
    The text is scraped from a university website. Target University: {university}.
    Extract as many courses as you can find. DO NOT hallucinate. Use only the text provided.
    If tuition fees or credits are not explicitly mentioned, write "ไม่ระบุ".
    Website URL for reference: {url}
    
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
        print(f"AI Extraction error: {e}")
    return []

def process_university(uni_name: str):
    print(f"--- Processing {uni_name} ---")
    
    # Check for dedicated scraper
    scraper_map = {
        "ubon ratchathani university": "scrape_ubu",
        "ubu": "scrape_ubu",
        "มหาวิทยาลัยอุบลราชธานี": "scrape_ubu",
        "chiang mai rajabhat university": "scrape_cmru",
        "cmru": "scrape_cmru",
        "suan dusit university": "scrape_sdu",
        "sdu": "scrape_sdu",
        "suan sunandha rajabhat university": "scrape_ssru",
        "ssru": "scrape_ssru",
        "thaksin university": "scrape_tsu",
        "tsu": "scrape_tsu",
        "thammasat university": "scrape_tu",
        "tu": "scrape_tu",
        "rajamangala university of technology thanyaburi": "scrape_rmutt",
        "rmutt": "scrape_rmutt",
        "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี": "scrape_rmutt",
    }
    
    norm_name = uni_name.lower().strip()
    if norm_name in scraper_map:
        module_name = scraper_map[norm_name]
        try:
            mod = __import__(module_name)
            if hasattr(mod, "seed_db"):
                print(f"Running dedicated high-precision pipeline from {module_name}...")
                mod.seed_db()
                return
        except Exception as e:
            print(f"Dedicated scraper fallback to SERP crawl due to: {e}")

    query = f'"{uni_name}" หลักสูตร ปริญญาตรี ปริญญาโท site:.ac.th OR site:.edu'
    urls = search_serpapi(query)
    
    all_courses = []
    for url in urls:
        print(f"Scraping {url} ...")
        text = fetch_text_from_url(url)
        courses = extract_courses_with_ai(text, url, uni_name)
        if courses:
            all_courses.extend(courses)
            print(f"  -> Found {len(courses)} courses from {url}")
            
    if all_courses and DB_AVAILABLE:
        session = SessionLocal()
        inserted = 0
        for c in all_courses:
            try:
                existing = session.query(CourseDB).filter_by(id=c["id"]).first()
                if existing:
                    for k, v in c.items(): setattr(existing, k, v)
                else:
                    session.add(CourseDB(**c))
                    inserted += 1
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Skipping {c['id']} due to DB error: {e}")
        session.close()
        print(f"=== Successfully seeded {inserted} REAL courses for {uni_name} ===")

def main():
    import urllib3
    urllib3.disable_warnings()
    if DB_AVAILABLE: Base.metadata.create_all(bind=engine)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_university, uni) for uni in UNIVERSITIES]
        for future in as_completed(futures):
            future.result()

if __name__ == "__main__":
    main()
