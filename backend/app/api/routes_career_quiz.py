import json
import logging
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

logger = logging.getLogger("CareerQuizRouter")
router = APIRouter(prefix="/career-quiz", tags=["Career & Faculty Discovery Quiz"])


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
    2. Synthesizes psychometric profile & ideal career paths using Gemini.
    3. Semantically matches recommended undergraduate courses from the database.
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
        "search_keywords": ["คีย์เวิร์ดคณะที่ 1 เช่น วิศวกรรมคอมพิวเตอร์", "วิทยาการข้อมูล", "เทคโนโลยีสารสนเทศ", "นิเทศศาสตร์", "บริหารธุรกิจ"]
    }}
    """

    # Call Gemini API
    gemini_data = None
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4
                )
            )
            gemini_data = json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini career analysis failed: {e}")

    # Fallback if Gemini fails
    if not gemini_data:
        top_name = trait_names.get(sorted_traits[0][0], "นักคิดค้น")
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
                    "title": "Data Scientist & AI Specialist",
                    "description": "ผู้นำข้อมูลและเทคโนโลยีมาแก้ปัญหาเชิงลึกและสร้างนวัตกรรมใหม่",
                    "match_percentage": 95,
                    "skills": ["Python", "Machine Learning", "Critical Thinking"],
                    "growth_outlook": "เติบโตสูงมาก"
                },
                {
                    "title": "Software & System Engineer",
                    "description": "ออกแบบและพัฒนาโครงสร้างระบบดิจิทัลแห่งอนาคต",
                    "match_percentage": 90,
                    "skills": ["Coding", "System Design", "Problem Solving"],
                    "growth_outlook": "เป็นที่ต้องการสูง"
                }
            ],
            "search_keywords": ["คอมพิวเตอร์", "ข้อมูล", "วิศวกรรม", "วิทยาการ", "เทคโนโลยี"]
        }

    # Query Undergraduate Courses from DB based on search keywords
    search_kws = gemini_data.get("search_keywords", ["วิทยาการ", "วิศวกรรม", "เทคโนโลยี", "บริหาร"])
    recommended_courses = []

    try:
        query = db.query(CourseDB).filter(
            or_(
                CourseDB.degree_level.ilike("%ปริญญาตรี%"),
                CourseDB.degree_level.ilike("%Bachelor%"),
                CourseDB.degree_level.ilike("%ตรี%")
            )
        )

        filters = []
        for kw in search_kws:
            pattern = f"%{kw}%"
            filters.append(CourseDB.title_th.ilike(pattern))
            filters.append(CourseDB.faculty_th.ilike(pattern))
            filters.append(CourseDB.description.ilike(pattern))

        if filters:
            matched_db = query.filter(or_(*filters)).limit(6).all()
        else:
            matched_db = query.limit(6).all()

        # Fallback if no specific matched undergraduate courses
        if not matched_db or len(matched_db) < 3:
            fallback_db = query.limit(6).all()
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
