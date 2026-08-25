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
from app.models.db_models import CourseDB
from sqlalchemy.orm import Session
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CMU_Agent3")

from google import genai
from google.genai import types

UNIVERSITIES = ["Chiang Mai University"]
FACULTIES = [
    "Faculty of Nursing",
    "Faculty of Pharmacy",
    "Faculty of Dentistry",
    "Faculty of Associated Medical Sciences",
    "Faculty of Agriculture"
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

API_KEYS = [
    "YOUR_API_KEY",
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

def extract_course_data(university: str, faculty: str) -> list[dict]:
    Prompt = f"""
    You are an expert academic data scraper.
    Extract or synthesize AT LEAST 15 to 20 degree programs (Bachelor's, Master's, Ph.D.) 
    offered by the {faculty} at {university} in Thailand. Try to be as exhaustive as possible.
    If exact real data is unavailable, generate highly realistic, strictly plausible academic programs that match the typical offerings of {university} in Thailand.
    The response MUST be a valid JSON array matching the provided schema.
    All Thai translations must be highly accurate.
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
                logger.info(f"=== CMU Agent 3 Target: {fac} ===")
                courses = extract_course_data(uni, fac)
                if not courses: continue
                for c in courses:
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
                session.commit()
                logger.info(f"Saved {len(courses)} courses for {uni} - {fac}.")
                time.sleep(random.uniform(25.0, 45.0))
    logger.info(f"Agent 3 completed! Total: {total_scraped}")

if __name__ == "__main__":
    run_scraper()
