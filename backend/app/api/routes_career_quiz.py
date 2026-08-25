import os
import json
import logging
import threading
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.config import settings
from app.models.db_models import CourseDB
from app.api.routes_courses import db_course_to_pydantic
from app.models.quiz_schema import (
    CareerQuizSubmitRequest,
    CareerProfileResponse,
    RiasecBreakdown,
    CareerRecommendation
)
from google import genai
from google.genai import types
import time

logger = logging.getLogger("CareerQuizRouter")
router = APIRouter(prefix="/career-quiz", tags=["Career & Faculty Discovery Quiz"])

# --- Key Rotation System (17 keys) ---
API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",")] if os.getenv("GEMINI_API_KEYS") else [os.getenv("GEMINI_API_KEY")]
_key_lock = threading.Lock()
_current_key_idx = 0

def _get_client():
    global _current_key_idx
    with _key_lock:
        return genai.Client(api_key=API_KEYS[_current_key_idx])

def _rotate_key():
    global _current_key_idx
    with _key_lock:
        _current_key_idx = (_current_key_idx + 1) % len(API_KEYS)

def _call_gemini_with_retry(prompt: str, max_retries: int = 10):
    """Call Gemini generate_content with key rotation and retry on 429."""
    for attempt in range(max_retries):
        try:
            client = _get_client()
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.5
                )
            )
            return json.loads(response.text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                _rotate_key()
                time.sleep(0.5)
                continue
            logger.error(f"Gemini call error (attempt {attempt+1}): {e}")
            _rotate_key()
            time.sleep(0.5)
    return None

def _get_embedding_with_retry(text: str, max_retries: int = 10):
    """Get embedding vector with key rotation and retry on 429."""
    for attempt in range(max_retries):
        try:
            client = _get_client()
            response = client.models.embed_content(
                model='gemini-embedding-2',
                contents=text,
                config={'output_dimensionality': 768}
            )
            return response.embeddings[0].values
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                _rotate_key()
                time.sleep(0.5)
                continue
            logger.error(f"Embedding error (attempt {attempt+1}): {e}")
            _rotate_key()
            time.sleep(0.5)
    return None


def calculate_riasec_scores(answers: List[Any]) -> Dict[str, float]:
    """Calculate normalized percentages (0-100) for R, I, A, S, E, C dimensions."""
    raw_scores = {"R": 0.0, "I": 0.0, "A": 0.0, "S": 0.0, "E": 0.0, "C": 0.0}
    counts = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}

    # Map question types and add scores
    for item in answers:
        dim = getattr(item, "dimension", None) or (item.get("dimension") if isinstance(item, dict) else None)
        val = getattr(item, "value", None) if not isinstance(item, dict) else item.get("value")

        if not dim:
            continue

        # Handle compound dimensions like "I+R", "S+E"
        target_dims = [d.strip() for d in dim.split("+") if d.strip() in raw_scores]

        # Numerical score (Likert 1 to 5)
        if isinstance(val, (int, float)):
            score = float(val)  # 1 to 5
            for d in target_dims:
                raw_scores[d] += score
                counts[d] += 1
        elif isinstance(val, list):
            # Multiple choices
            for d in target_dims:
                raw_scores[d] += 4.0
                counts[d] += 1
        elif isinstance(val, str) and val.strip():
            for d in target_dims:
                raw_scores[d] += 4.0
                counts[d] += 1

    # Normalize to 0-100 scale
    normalized = {}
    for d, raw in raw_scores.items():
        cnt = counts[d]
        if cnt > 0:
            avg = raw / cnt  # 1.0 to 5.0
            pct = round(max(10.0, min(100.0, ((avg - 1.0) / 4.0) * 85.0 + 15.0)), 1)
        else:
            pct = 40.0  # default baseline
        normalized[d] = pct

    return normalized


@router.post("/analyze", response_model=CareerProfileResponse)
def analyze_career_quiz(request: CareerQuizSubmitRequest, db: Session = Depends(get_db)):
    """
    AI Career & Course Discovery Engine:
    1. Computes Holland's RIASEC scores.
    2. Synthesizes psychometric profile & ideal career paths using Gemini (with key rotation).
    3. Semantically matches recommended undergraduate courses from the database via pgvector.
    """
    riasec_pct = calculate_riasec_scores(request.answers)

    # Sort RIASEC to get top 3 traits
    sorted_traits = sorted(riasec_pct.items(), key=lambda x: x[1], reverse=True)
    top_code = "".join([t[0] for t in sorted_traits[:3]])

    trait_names = {
        "R": "นักปฏิบัติ (Realistic)",
        "I": "นักสืบค้น (Investigative)",
        "A": "นักสร้างสรรค์ (Artistic)",
        "S": "นักสังคม (Social)",
        "E": "นักบริหาร (Enterprising)",
        "C": "นักจัดระเบียบ (Conventional)"
    }

    free_text_context = "\n".join([f"- {k}: {v}" for k, v in request.free_text_answers.items() if v])

    prompt = f"""
    You are an empathetic, top-tier Thai Educational Psychologist and Career Counselor helping a Thai High School student discover their ideal career path and university major.

    [Student Assessment Data]
    Assessment Depth: {request.tier} mode
    Top Holland Code: {top_code}
    Holland RIASEC Breakdown:
    - Realistic (นักปฏิบัติ): {riasec_pct.get('R')}%
    - Investigative (นักคิดค้น/วิเคราะห์): {riasec_pct.get('I')}%
    - Artistic (นักสร้างสรรค์/ศิลปะ): {riasec_pct.get('A')}%
    - Social (นักสังคม/ช่วยเหลือ): {riasec_pct.get('S')}%
    - Enterprising (นักบริหาร/ผู้นำ): {riasec_pct.get('E')}%
    - Conventional (นักจัดระเบียบ/ระบบ): {riasec_pct.get('C')}%

    Student's Open-Ended Passions & Free-Text Responses:
    {free_text_context or 'ไม่ได้ระบุข้อความเพิ่มเติม'}

    [Task]
    Generate an insightful, encouraging, and highly specific Career & University Profile in Thai.
    The "search_keywords" MUST be highly relevant Thai academic keywords based on the student's RIASEC profile AND their free-text answers. Include faculty names, department names, and field names in Thai that match the student's interests. For example, if a student likes art and nature, suggest "ศิลปกรรมศาสตร์", "จิตรกรรม", "การออกแบบ". If they like business, suggest "บริหารธุรกิจ", "การตลาด", "การจัดการ". If they like medicine, suggest "แพทยศาสตร์", "สาธารณสุข", "เภสัชศาสตร์".
    
    Return a strict JSON object with this exact schema:
    {{
        "archetype_title": "ฉายาตัวตนเท่ๆ เช่น นักคิดค้นนวัตกรรมและเทคโนโลยีเปลี่ยนโลก (The Tech Innovator)",
        "archetype_description": "คำอธิบายตัวตนแบบกระชับ 1 ประโยค",
        "personality_summary": "ย่อหน้าวิเคราะห์เจาะลึกบุคลิกภาพ สไตล์การเรียนรู้ จุดเด่น และสิ่งที่ขับเคลื่อนจิตวิญญาณของน้อง (ความยาว 3-4 ประโยค ภาษาอบอุ่นและสร้างแรงบันดาลใจ)",
        "strengths": ["จุดเด่นที่ 1", "จุดเด่นที่ 2", "จุดเด่นที่ 3", "จุดเด่นที่ 4"],
        "ideal_work_environment": "สภาพแวดล้อมการทำงานที่ทำให้น้องเปล่งประกายที่สุด",
        "growth_advice": "คำแนะนำสั้นๆ ในการเตรียมตัวช่วง ม.ปลาย (เช่น การทำพอร์ต การหาประสบการณ์)",
        "share_quote": "ประโยคคมๆ สั้นๆ 1 ประโยค สำหรับแคปแชร์ลง Instagram Story / Twitter",
        "top_careers": [
            {{
                "title": "ชื่ออาชีพภาษาไทยและอังกฤษ",
                "description": "คำอธิบายว่าอาชีพนี้ทำอะไรและตรงกับตัวตนของน้องอย่างไร",
                "match_percentage": 96,
                "skills": ["ทักษะ 1", "ทักษะ 2", "ทักษะ 3"],
                "growth_outlook": "เติบโตสูงมากในยุค AI"
            }},
            {{
                "title": "อาชีพทางเลือกที่ 2",
                "description": "คำอธิบายความน่าสนใจ",
                "match_percentage": 91,
                "skills": ["ทักษะ 1", "ทักษะ 2"],
                "growth_outlook": "เติบโตต่อเนื่อง"
            }},
            {{
                "title": "อาชีพทางเลือกที่ 3",
                "description": "คำอธิบายความน่าสนใจ",
                "match_percentage": 87,
                "skills": ["ทักษะ 1", "ทักษะ 2"],
                "growth_outlook": "เป็นที่ต้องการสูง"
            }}
        ],
        "search_keywords": ["คีย์เวิร์ดคณะภาษาไทยที่ 1", "คีย์เวิร์ดสาขาวิชาภาษาไทยที่ 2", "คีย์เวิร์ดที่ 3", "คีย์เวิร์ดที่ 4", "คีย์เวิร์ดที่ 5"]
    }}
    """

    # Call Gemini API with key rotation
    gemini_data = _call_gemini_with_retry(prompt)

    # Fallback if Gemini fails completely
    if not gemini_data:
        top_name = trait_names.get(sorted_traits[0][0], "นักคิดค้น")
        # Extract keywords from free_text for smarter fallback
        fallback_keywords = []
        for v in request.free_text_answers.values():
            if v:
                fallback_keywords.extend(v.split()[:5])
        if not fallback_keywords:
            fallback_keywords = ["วิทยาการ", "วิศวกรรม", "เทคโนโลยี", "บริหาร"]
        
        gemini_data = {
            "archetype_title": f"ผู้บุกเบิกสาย {top_name}",
            "archetype_description": f"คุณเป็นคนที่มีความโดดเด่นด้าน {top_name} และมุ่งมั่นที่จะพัฒนาตนเอง",
            "personality_summary": f"คุณมีคะแนนโดดเด่นในกลุ่ม {top_code} ซึ่งสะท้อนถึงความเป็นคนชอบเรียนรู้ ลงมือทำ และมีวิสัยทัศน์ที่ชัดเจนในการแก้ปัญหา เหมาะอย่างยิ่งกับสาขาวิชาที่ได้ใช้ทั้งความคิดเชิงวิเคราะห์และความคิดสร้างสรรค์",
            "strengths": ["การคิดวิเคราะห์อย่างเป็นระบบ", "ความมุ่งมั่นในการเรียนรู้", "ความสามารถในการปรับตัว"],
            "ideal_work_environment": "สภาพแวดล้อมที่เปิดกว้าง มีพื้นที่ให้ได้คิดและสร้างสรรค์สิ่งใหม่",
            "growth_advice": "เริ่มสะสมผลงาน (Portfolio) และหาโอกาสเข้าร่วมค่ายกิจกรรมหรืออบรมทักษะที่เกี่ยวข้อง",
            "share_quote": "ค้นพบตัวตนและเส้นทางที่ใช่ ก้าวสู่อนาคตอย่างมั่นใจ 🌟",
            "top_careers": [
                {
                    "title": f"สายอาชีพที่เหมาะกับ {top_name}",
                    "description": f"อาชีพที่ตรงกับบุคลิกภาพแบบ {top_code}",
                    "match_percentage": 90,
                    "skills": ["ทักษะเฉพาะทาง", "การวิเคราะห์", "การสื่อสาร"],
                    "growth_outlook": "เติบโตสูง"
                }
            ],
            "search_keywords": fallback_keywords
        }

    # --- Query Undergraduate Courses from DB ---
    search_kws = gemini_data.get("search_keywords", [])
    recommended_courses = []

    try:
        base_query = db.query(CourseDB).filter(
            or_(
                CourseDB.degree_level.ilike("%ปริญญาตรี%"),
                CourseDB.degree_level.ilike("%Bachelor%"),
                CourseDB.degree_level.ilike("%ตรี%")
            )
        )

        matched_db = []
        
        # 1. Try pgvector semantic search if there's free text input
        if request.free_text_answers and any(request.free_text_answers.values()):
            # Build a rich query from free text + archetype
            query_parts = list(request.free_text_answers.values())
            query_parts.append(gemini_data.get("archetype_description", ""))
            query_parts.extend(search_kws)
            query_text = " ".join([p for p in query_parts if p])
            
            embedding = _get_embedding_with_retry(query_text)
            if embedding and len(embedding) == 768:
                # Semantic search using pgvector cosine_distance
                matched_db = base_query.order_by(
                    CourseDB.embedding.cosine_distance(embedding)
                ).limit(6).all()
        
        # 2. Fallback to keyword matching if pgvector fails or no free text
        if not matched_db:
            filters = []
            for kw in search_kws:
                pattern = f"%{kw}%"
                filters.append(CourseDB.title_th.ilike(pattern))
                filters.append(CourseDB.faculty_th.ilike(pattern))
                filters.append(CourseDB.description.ilike(pattern))

            if filters:
                matched_db = base_query.filter(or_(*filters)).limit(6).all()
            else:
                matched_db = base_query.limit(6).all()

        # Fallback if no specific matched undergraduate courses
        if not matched_db or len(matched_db) < 3:
            fallback_db = base_query.limit(6).all()
            matched_db = list({c.id: c for c in (matched_db + fallback_db)}.values())[:6]

        for i, c in enumerate(matched_db):
            score = 98.0 - (i * 2.5)
            recommended_courses.append(db_course_to_pydantic(c, match_score=round(score, 1)))

    except Exception as e:
        logger.error(f"Error querying courses for career quiz: {e}")

    # Build response
    return CareerProfileResponse(
        tier=request.tier,
        archetype_title=gemini_data.get("archetype_title", "นักสร้างสรรค์นวัตกรรม"),
        archetype_code=f"{top_code} ({trait_names.get(top_code[0], '')})",
        archetype_description=gemini_data.get("archetype_description", ""),
        riasec_scores=RiasecBreakdown(
            realistic=riasec_pct.get("R", 0.0),
            investigative=riasec_pct.get("I", 0.0),
            artistic=riasec_pct.get("A", 0.0),
            social=riasec_pct.get("S", 0.0),
            enterprising=riasec_pct.get("E", 0.0),
            conventional=riasec_pct.get("C", 0.0)
        ),
        personality_summary=gemini_data.get("personality_summary", ""),
        strengths=gemini_data.get("strengths", []),
        ideal_work_environment=gemini_data.get("ideal_work_environment", ""),
        growth_advice=gemini_data.get("growth_advice", ""),
        share_quote=gemini_data.get("share_quote", ""),
        top_careers=[
            CareerRecommendation(
                title=c.get("title", ""),
                description=c.get("description", ""),
                match_percentage=c.get("match_percentage", 90),
                skills=c.get("skills", []),
                growth_outlook=c.get("growth_outlook", "เติบโตสูง")
            )
            for c in gemini_data.get("top_careers", [])
        ],
        recommended_courses=recommended_courses
    )

