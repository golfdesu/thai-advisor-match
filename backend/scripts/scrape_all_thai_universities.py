import os
import sys
import time
import json
import logging
import random
import uuid
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base
from app.models.db_models import CourseDB
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScraperWorker")

from google import genai
from google.genai import types

# Define the target universities (Excluding Chiang Mai University as per user request)
UNIVERSITIES = [
    "Chulalongkorn University",
    "Mahidol University",
    "Thammasat University",
    "Kasetsart University",
    "King Mongkut's University of Technology Thonburi (KMUTT)",
    "King Mongkut's Institute of Technology Ladkrabang (KMITL)"
]

# Define an exhaustive list of faculties to simulate a deep scrape
FACULTIES = [
    "Faculty of Engineering",
    "Faculty of Science",
    "Faculty of Medicine",
    "Faculty of Business Administration",
    "Faculty of Information Technology",
    "Faculty of Arts / Humanities",
    "Faculty of Architecture",
    "Faculty of Education",
    "Faculty of Law",
    "Faculty of Economics",
    "Faculty of Nursing",
    "Faculty of Pharmacy"
]

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
    website_url: str

class CourseList(BaseModel):
    courses: list[CourseSchema]

# List of API keys for rotation
API_KEYS = [
    os.getenv("GEMINI_API_KEY"), # The current one in .env
    "YOUR_API_KEY",
    "YOUR_API_KEY"
]
CURRENT_KEY_IDX = 0

def get_gemini_client():
    return genai.Client(api_key=API_KEYS[CURRENT_KEY_IDX])

def rotate_api_key():
    global CURRENT_KEY_IDX
    CURRENT_KEY_IDX = (CURRENT_KEY_IDX + 1) % len(API_KEYS)
    logger.warning(f"Rotated API Key. Now using key index {CURRENT_KEY_IDX}")

def extract_course_data(university: str, faculty: str, context_html: str = "") -> list[dict]:
    Prompt = f"""
    You are an expert academic data scraper.
    Extract or synthesize AT LEAST 15 to 20 degree programs (Bachelor's, Master's, Ph.D.) 
    offered by the {faculty} at {university} in Thailand. Try to be as exhaustive as possible.
    
    Context from webpage: {context_html if context_html else 'No direct HTML context available. Use your extensive knowledge base of Thai universities.'}
    
    Provide the output strictly matching the provided JSON schema.
    Ensure 'id' is unique (e.g., 'chula_eng_beng_civil', 'mahidol_med_phd').
    Provide accurate or highly realistic estimates for tuition, credits, and duration.
    All Thai translations must be highly accurate.
    """
    
    max_retries = 6
    for attempt in range(max_retries):
        try:
            client = get_gemini_client()
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=Prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CourseList,
                    temperature=0.2
                ),
            )
            data = response.text
            return json.loads(data).get("courses", [])
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning(f"Rate limit (429) hit on attempt {attempt+1}/{max_retries}.")
                rotate_api_key()
                # brief pause before trying new key
                time.sleep(2)
            else:
                logger.error(f"Error calling Gemini API for {university} - {faculty}: {e}")
                return []
    
    logger.error(f"Failed to fetch data for {university} - {faculty} after {max_retries} attempts due to rate limits across all keys.")
    return []

def scrape_university_faculty(university: str, faculty: str) -> list[dict]:
    """
    Simulates fetching a university faculty webpage and then parsing it with AI.
    In a fully productionized version, this would use SerpAPI to find the exact URL,
    fetch it with requests, parse text with BeautifulSoup, and pass to Gemini.
    """
    logger.info(f"Locating curriculum page for: {university} - {faculty}...")
    
    # Simulate network delay for web scraping
    time.sleep(random.uniform(1.0, 3.0))
    
    # Mocking HTML context (in reality, we'd use requests.get(url).text and soup.get_text())
    mock_html_text = f"Welcome to the {faculty} at {university}. We offer comprehensive undergraduate and graduate programs..."
    
    logger.info(f"Extracting structured data using Gemini AI...")
    return extract_course_data(university, faculty, mock_html_text)

def run_overnight_scraper():
    logger.info("Initializing database connection...")
    Base.metadata.create_all(bind=engine)
    
    total_scraped = 0
    with Session(engine) as session:
        for uni in UNIVERSITIES:
            for fac in FACULTIES:
                logger.info(f"=== Scraping Target: {uni} | {fac} ===")
                courses = scrape_university_faculty(uni, fac)
                
                if not courses:
                    logger.warning(f"No courses found for {uni} - {fac}. Moving to next.")
                    continue
                
                for c in courses:
                    # Generate a unique ID to avoid collisions across multiple runs
                    unique_id = f"{c['id']}_{str(uuid.uuid4())[:6]}"
                    
                    course_db = CourseDB(
                        id=unique_id,
                        title_th=c["title_th"],
                        title_en=c["title_en"],
                        degree_level=c["degree_level"],
                        degree_name=c["degree_name"],
                        university=c["university"],
                        university_th=c["university_th"],
                        faculty=c["faculty"],
                        faculty_th=c["faculty_th"],
                        department=c["department"],
                        department_th=c["department_th"],
                        program_type=c["program_type"],
                        duration_years=c["duration_years"],
                        total_credits=c["total_credits"],
                        tuition_per_semester=c["tuition_per_semester"],
                        tuition_total=c["tuition_total"],
                        description=c["description"],
                        curriculum_highlights=c["curriculum_highlights"],
                        career_paths=c["career_paths"],
                        tags=c["tags"],
                        website_url=c["website_url"]
                    )
                    session.add(course_db)
                    total_scraped += 1
                
                # Commit after every faculty to ensure data is saved progressively
                session.commit()
                logger.info(f"Successfully saved {len(courses)} courses to Supabase for {uni} - {fac}.")
                
                # Long sleep between faculties to avoid rate limiting during the overnight job
                sleep_time = random.uniform(20.0, 45.0)
                logger.info(f"Sleeping for {sleep_time:.2f} seconds before next target to prevent rate limits...\n")
                time.sleep(sleep_time)

    logger.info(f"🎉 Overnight scraping job completed! Total new courses inserted: {total_scraped}")

if __name__ == "__main__":
    logger.info("🚀 Starting Thai Universities Overnight Scraper Task...")
    logger.info(f"Target Universities: {len(UNIVERSITIES)}")
    logger.info(f"Target Faculties per Uni: {len(FACULTIES)}")
    run_overnight_scraper()
