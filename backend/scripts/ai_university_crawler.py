"""
AI-Powered Universal University Crawler
This script uses Google Search to find official curriculum pages for a list of universities,
extracts the textual content, and uses the Gemini API to parse the unstructured text into
the standardized EduCenter `CourseDB` JSON schema.
"""
import os
import sys
import json
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from google import genai
from pydantic import BaseModel, Field

# Setup path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",")] if os.getenv("GEMINI_API_KEYS") else [os.getenv("GEMINI_API_KEY")]

key_lock = threading.Lock()
current_key_idx = 0

def get_client():
    global current_key_idx
    with key_lock:
        key = API_KEYS[current_key_idx]
        current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    return genai.Client(api_key=key)

UNIVERSITIES = [
    "Prince of Songkla University",
    "Suranaree University of Technology",
    "Walailak University",
    "Maejo University",
    "University of Phayao",
    "Ubon Ratchathani University",
    "Rajamangala University of Technology Thanyaburi",
    "Rajamangala University of Technology Krungthep",
    "Rajamangala University of Technology Phra Nakhon",
    "Suan Sunandha Rajabhat University",
    "Suan Dusit University",
    "Chiang Mai Rajabhat University",
    "Bangkok University",
    "Assumption University",
    "Sripatum University",
    "University of the Thai Chamber of Commerce",
    "Rangsit University",
    "Thaksin University",
    "Ramkhamhaeng University",
    "Sukhothai Thammathirat Open University"
]

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

def fetch_text_from_url(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        # return the first 15000 characters to avoid huge payloads
        return text[:15000]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_courses_with_ai(text: str, url: str, university: str) -> list[dict]:
    if len(text) < 500:
        return []
    
    prompt = f"""
    You are a data extraction AI. Extract all academic programs/curricula mentioned in the following text.
    The text is scraped from a university website. Target University: {university}.
    Extract as many courses as you can find. If tuition fees or credits are not explicitly mentioned, make an educated estimate or write "ไม่ระบุ".
    Website URL for reference: {url}
    
    TEXT:
    {text}
    """
    
    client = get_client()
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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
        print(f"AI Extraction error for {url}: {e}")
    return []

def process_university(uni_name: str):
    print(f"--- Processing {uni_name} ---")
    query = f'"{uni_name}" หลักสูตร ปริญญาตรี ปริญญาโท site:.ac.th OR site:.edu'
    urls_to_scrape = []
    try:
        for url in search(query, num_results=3, sleep_interval=2):
            urls_to_scrape.append(url)
    except Exception as e:
        print(f"Search error for {uni_name}: {e}")
        return

    all_courses = []
    for url in urls_to_scrape:
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
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items(): setattr(existing, k, v)
            else:
                session.add(CourseDB(**c))
                inserted += 1
        session.commit()
        session.close()
        print(f"=== Successfully seeded {inserted} REAL courses for {uni_name} ===")

def main():
    import urllib3
    urllib3.disable_warnings()
    if DB_AVAILABLE:
        Base.metadata.create_all(bind=engine)
    
    # Process with ThreadPool for speed
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_university, uni) for uni in UNIVERSITIES]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in thread: {e}")

if __name__ == "__main__":
    main()
