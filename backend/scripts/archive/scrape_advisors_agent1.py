import os
import sys
import time
import json
import logging
import random
import uuid
from pydantic import BaseModel
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.core.database import engine, Base
from app.models.db_models import FacultyDB
from sqlalchemy.orm import Session
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Advisor_Agent1")

from google import genai
from google.genai import types

UNIVERSITIES = ["Chulalongkorn University"]
FACULTIES = [
    "Faculty of Engineering",
    "Faculty of Science",
    "Faculty of Medicine",
    "Faculty of Commerce and Accountancy",
    "Faculty of Arts",
    "Faculty of Architecture",
    "Faculty of Education",
    "Faculty of Law",
    "Faculty of Economics",
    "Faculty of Communication Arts"
]

class FacultySchema(BaseModel):
    id: str
    university: str
    university_th: str
    faculty: str
    faculty_th: str
    department: str
    department_th: str
    academic_title_th: str
    first_name: str
    last_name: str
    full_name_th: str
    role: str
    email: str
    image_url: str
    profile_url: str
    education: list[str]
    research_interests: list[str]
    taught_courses: list[str]
    featured_publications: list[str]
    scholar_url: str

class FacultyList(BaseModel):
    faculties: list[FacultySchema]

API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    "YOUR_API_KEY",
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

def extract_advisor_data(university: str, faculty: str) -> list[dict]:
    Prompt = f"""
    You are an expert academic data scraper and researcher.
    Extract or synthesize highly realistic profiles for AT LEAST 20 to 25 faculty members 
    (Professors, Assoc. Prof, Asst. Prof, Lecturers) who act as thesis advisors for Master's and Ph.D. students
    in the {faculty} at {university} in Thailand. Try to be as exhaustive as possible.
    Ensure their 'research_interests' are highly detailed and specific to graduate-level research.
    If exact real data is unavailable, generate highly realistic, strictly plausible profiles that match typical professors at {university}.
    The response MUST be a valid JSON array matching the provided schema.
    All Thai translations must be highly accurate. Provide placeholder URLs (e.g. https://www.eng.chula.ac.th/profile/name) if needed.
    """
    max_retries = 8
    for attempt in range(max_retries):
        try:
            client = get_gemini_client()
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=Prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FacultyList,
                    temperature=0.3
                ),
            )
            data = response.text
            return json.loads(data).get("faculties", [])
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning(f"Rate limit (429) hit on attempt {attempt+1}/{max_retries}.")
                rotate_api_key()
                time.sleep(2)
            elif "401" in error_str or "UNAUTHENTICATED" in error_str or "invalid" in error_str.lower():
                logger.warning(f"Invalid API Key (401) on attempt {attempt+1}/{max_retries}.")
                rotate_api_key()
            else:
                logger.error(f"Error for {university} - {faculty}: {e}")
                return []
    logger.error(f"Failed {university} - {faculty} after {max_retries} attempts.")
    return []

def run_scraper():
    Base.metadata.create_all(bind=engine)
    total_scraped = 0
    with Session(engine) as session:
        for uni in UNIVERSITIES:
            for fac in FACULTIES:
                logger.info(f"=== Advisor Agent 1 Target: {uni} | {fac} ===")
                advisors = extract_advisor_data(uni, fac)
                if not advisors: continue
                for f in advisors:
                    unique_id = f"{f['id']}_{str(uuid.uuid4())[:6]}"
                    faculty_db = FacultyDB(
                        id=unique_id,
                        university=f["university"],
                        university_th=f["university_th"],
                        faculty=f["faculty"],
                        faculty_th=f["faculty_th"],
                        department=f["department"],
                        department_th=f["department_th"],
                        academic_title_th=f["academic_title_th"],
                        first_name=f["first_name"],
                        last_name=f["last_name"],
                        full_name_th=f["full_name_th"],
                        role=f["role"],
                        email=f["email"],
                        image_url=f["image_url"],
                        profile_url=f["profile_url"],
                        education=f["education"],
                        research_interests=f["research_interests"],
                        taught_courses=f["taught_courses"],
                        featured_publications=f["featured_publications"],
                        scholar_url=f["scholar_url"],
                        embedding_text=None
                    )
                    session.add(faculty_db)
                    total_scraped += 1
                session.commit()
                logger.info(f"Saved {len(advisors)} advisors for {uni} - {fac}.")
                time.sleep(random.uniform(25.0, 45.0))
    logger.info(f"Advisor Agent 1 completed! Total: {total_scraped}")

if __name__ == "__main__":
    run_scraper()
