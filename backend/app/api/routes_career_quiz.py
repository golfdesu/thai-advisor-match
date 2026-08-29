import os
import json
import logging
import threading
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, defer
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
from app.core.embedding_service import embedding_service
from google.genai import types
import time

logger = logging.getLogger("CareerQuizRouter")
router = APIRouter(prefix="/career-quiz", tags=["Career & Faculty Discovery Quiz"])

def _call_gemini_with_retry(prompt: str, max_retries: int = 3):
    """Call Gemini generate_content with key rotation and fast retry on 429."""
    for attempt in range(max_retries):
        try:
            client = embedding_service._get_client()
            if not client:
                logger.error("No Gemini API key available")
                return None
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
                embedding_service._rotate_key()
                time.sleep(0.2)
                continue
            logger.error(f"Gemini call error (attempt {attempt+1}): {e}")
            embedding_service._rotate_key()
            time.sleep(0.2)
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

    # Extract Lifestyle preferences from answers
    lifestyle_items = []
    for item in request.answers:
        cat = getattr(item, "category", None) or (item.get("category") if isinstance(item, dict) else None)
        lbl = getattr(item, "label", None) or (item.get("label") if isinstance(item, dict) else None)
        val = getattr(item, "value", None) if not isinstance(item, dict) else item.get("value")
        txt = getattr(item, "text", None) or (item.get("text") if isinstance(item, dict) else None)

        if cat and not cat.startswith("ความสนใจและกิจกรรม"):
            val_str = lbl or (str(val) if val is not None else "") or (txt if txt else "")
            if val_str and val_str not in ["1", "2", "3", "4", "5"]:
                lifestyle_items.append(f"- {cat}: {val_str}")

    lifestyle_context = "\n".join(lifestyle_items) if lifestyle_items else "ไม่มีข้อมูลไลฟ์สไตล์เพิ่มเติม"

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

    Student's Lifestyle & University Preferences:
    {lifestyle_context}

    Student's Open-Ended Passions & Free-Text Responses:
    {free_text_context or 'ไม่ได้ระบุข้อความเพิ่มเติม'}

    [Task]
    Generate an insightful, encouraging, and highly specific Career & University Profile in Thai.
    The "search_keywords" MUST be highly relevant Thai academic keywords based on the student's RIASEC profile, lifestyle preferences, and free-text answers. Include faculty names, department names, and field names in Thai that match the student's interests.
    
    Return a strict JSON object with this exact schema:
    {{
        "archetype_title": "ฉายาตัวตนเท่ๆ เช่น นักคิดค้นนวัตกรรมและเทคโนโลยีเปลี่ยนโลก (The Tech Innovator)",
        "archetype_description": "คำอธิบายตัวตนแบบกระชับ 1 ประโยค",
        "personality_summary": "ย่อหน้าวิเคราะห์เจาะลึกบุคลิกภาพ สไตล์การเรียนรู้ จุดเด่น และสิ่งที่ขับเคลื่อนจิตวิญญาณของน้อง (ความยาว 3-4 ประโยค ภาษาอบอุ่นและสร้างแรงบันดาลใจ)",
        "strengths": ["จุดเด่นที่ 1", "จุดเด่นที่ 2", "จุดเด่นที่ 3", "จุดเด่นที่ 4"],
        "ideal_work_environment": "สภาพแวดล้อมการทำงานที่ทำให้น้องเปล่งประกายที่สุด",
        "campus_vibe_match": "สไตล์และบรรยากาศมหาวิทยาลัยที่ตรงกับไลฟ์สไตล์และภูมิภาคที่น้องสนใจ (1 ประโยค)",
        "learning_style_match": "สไตล์การเรียนรู้ในรั้วมหาวิทยาลัยที่เข้ากับน้องที่สุด (1 ประโยค)",
        "lifestyle_highlights": ["ไฮไลต์ด้านไลฟ์สไตล์/กิจกรรมที่ 1", "ไฮไลต์ที่ 2", "ไฮไลต์ที่ 3"],
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

    # Compose student profile context for parallel course embedding
    course_query_parts = []
    if request.free_text_answers and any(request.free_text_answers.values()):
        course_query_parts.extend([str(v) for v in request.free_text_answers.values() if v])
    if lifestyle_items:
        course_query_parts.extend(lifestyle_items)
    course_query_parts.append(f"ความสนใจด้าน {trait_names.get(top_code[0], '')}")
    if len(top_code) > 1:
        course_query_parts.append(f"{trait_names.get(top_code[1], '')}")
    initial_course_query_text = " ".join(course_query_parts)

    # 1. Parallel execution: run Gemini psychometric profiling and course embedding concurrently
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_gemini = executor.submit(_call_gemini_with_retry, prompt)
        future_embedding = executor.submit(embedding_service.get_embedding, initial_course_query_text)
        
        gemini_data = future_gemini.result()
        pre_embedding = future_embedding.result()

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
        
        # Rich career mapping per Holland dimension
        dim_careers_map = {
            "R": [
                {"title": "วิศวกรและนักพัฒนานวัตกรรมทางเทคนิค", "description": "ออกแบบและพัฒนาเทคโนโลยี เครื่องจักร หรือระบบคอมพิวเตอร์ที่ใช้งานได้จริง", "match_percentage": 94, "skills": ["การแก้ปัญหาทางเทคนิค", "การลงมือปฏิบัติ", "ทักษะวิศวกรรม"], "growth_outlook": "เติบโตสูงมาก"},
                {"title": "ผู้เชี่ยวชาญด้านระบบอัตโนมัติและหุ่นยนต์", "description": "สร้างและควบคุมระบบปฏิบัติการอัตโนมัติในภาคอุตสาหกรรม", "match_percentage": 90, "skills": ["ระบบสมองกล", "การเขียนโปรแกรมควบคุม", "การวิเคราะห์โครงสร้าง"], "growth_outlook": "เติบโตสูง"},
                {"title": "นักวิเคราะห์และทดสอบระบบ (System & QA Engineer)", "description": "ตรวจสอบความถูกต้องและประสิทธิภาพของระบบเทคโนโลยีและเครื่องมือ", "match_percentage": 86, "skills": ["การทดสอบระบบ", "การแก้ปัญหาเฉพาะหน้า", "ความละเอียดรอบคอบ"], "growth_outlook": "เป็นที่ต้องการสูง"}
            ],
            "I": [
                {"title": "นักวิทยาศาสตร์ข้อมูลและนักวิจัย AI", "description": "วิเคราะห์ข้อมูลเชิงลึกและพัฒนาแบบจำลองปัญญาประดิษฐ์เพื่อแก้ไขปัญหาที่ซับซ้อน", "match_percentage": 95, "skills": ["Machine Learning", "Data Analysis", "Critical Thinking"], "growth_outlook": "เติบโตสูงมาก"},
                {"title": "นักวิจัยและผู้เชี่ยวชาญด้านวิทยาศาสตร์สุขภาพ", "description": "ค้นคว้า วิจัย และพัฒนาองค์ความรู้ทางการแพทย์และสาธารณสุข", "match_percentage": 91, "skills": ["การวิจัยทางวิทยาศาสตร์", "การทดลอง", "การคิดเชิงตรรกะ"], "growth_outlook": "เติบโตสูง"},
                {"title": "นักวิเคราะห์ระบบและกลยุทธ์เชิงปริมาณ", "description": "สร้างแบบจำลองทางคณิตศาสตร์และสถิติเพื่อการคาดการณ์และวางแผน", "match_percentage": 87, "skills": ["สถิติขั้นสูง", "การสร้างแบบจำลอง", "การสืบค้นข้อมูล"], "growth_outlook": "เป็นที่ต้องการสูง"}
            ],
            "A": [
                {"title": "นักออกแบบสื่อดิจิทัลและประสบการณ์ผู้ใช้ (UX/UI Designer)", "description": "สร้างสรรค์งานออกแบบที่ผสานความสวยงามและการใช้งานที่ตอบโจทย์ผู้คน", "match_percentage": 93, "skills": ["UI/UX Design", "Creative Problem Solving", "Visual Storytelling"], "growth_outlook": "เติบโตสูง"},
                {"title": "นักสร้างสรรค์เนื้อหาและผู้กำกับศิลป์ (Creative Director)", "description": "วางแนวคิดและขับเคลื่อนโปรเจกต์เชิงสร้างสรรค์ในอุตสาหกรรมคอนเทนต์", "match_percentage": 89, "skills": ["การเล่าเรื่อง", "การกำกับงานศิลป์", "นวัตกรรมสื่อ"], "growth_outlook": "เติบโตต่อเนื่อง"},
                {"title": "สถาปนิกและนักออกแบบพื้นที่ (Architect & Spatial Designer)", "description": "ออกแบบพื้นที่และสิ่งแวดล้อมที่เชื่อมโยงศิลปะและฟังก์ชันการใช้งาน", "match_percentage": 86, "skills": ["การออกแบบสถาปัตยกรรม", "การมองมิติสัมพันธ์", "การออกแบบเชิงแนวคิด"], "growth_outlook": "เติบโตมั่นคง"}
            ],
            "S": [
                {"title": "ผู้เชี่ยวชาญด้านจิตวิทยาและการให้คำปรึกษา", "description": "ให้คำปรึกษาและส่งเสริมสุขภาวะทางจิตใจแก่บุคคลและองค์กร", "match_percentage": 94, "skills": ["จิตวิทยาการปรึกษา", "Empathy", "Active Listening"], "growth_outlook": "เติบโตสูงมาก"},
                {"title": "บุคลากรทางการแพทย์และสาธารณสุขชุมชน", "description": "ดูแลรักษา ฟื้นฟู และยกระดับคุณภาพชีวิตของผู้คนในสังคม", "match_percentage": 90, "skills": ["การดูแลผู้ป่วย", "การสื่อสารเพื่อการบำบัด", "การทำงานเป็นทีม"], "growth_outlook": "เป็นที่ต้องการสูง"},
                {"title": "นักพัฒนาทรัพยากรมนุษย์และการศึกษา (HR Specialist)", "description": "ออกแบบโปรแกรมการเรียนรู้และพัฒนาศักยภาพของคนในองค์กร", "match_percentage": 86, "skills": ["การฝึกอบรม", "การโค้ช", "การสื่อสารระหว่างบุคคล"], "growth_outlook": "เติบโตต่อเนื่อง"}
            ],
            "E": [
                {"title": "ผู้ประกอบการสตาร์ทอัพและผู้นำธุรกิจดิจิทัล (Startup Founder)", "description": "สร้างและขยายธุรกิจนวัตกรรมเพื่อตอบสนองโอกาสใหม่ในตลาด", "match_percentage": 95, "skills": ["ภาวะผู้นำ", "Business Strategy", "การระดมทุนและการเจรจา"], "growth_outlook": "เติบโตสูงมาก"},
                {"title": "ผู้จัดการฝ่ายกลยุทธ์และการตลาดดิจิทัล (Growth Marketer)", "description": "ขับเคลื่อนยอดขายและการเติบโตของแบรนด์ผ่านช่องทางดิจิทัล", "match_percentage": 91, "skills": ["Digital Marketing", "Data-Driven Strategy", "การตลาดเชิงรุก"], "growth_outlook": "เติบโตสูง"},
                {"title": "ที่ปรึกษาด้านการจัดการและการลงทุน (Management Consultant)", "description": "ให้คำปรึกษาเชิงกลยุทธ์เพื่อเพิ่มประสิทธิภาพและผลกำไรขององค์กร", "match_percentage": 87, "skills": ["การวิเคราะห์ธุรกิจ", "การนำเสนอ", "การตัดสินใจเชิงกลยุทธ์"], "growth_outlook": "เป็นที่ต้องการสูง"}
            ],
            "C": [
                {"title": "นักวิเคราะห์การเงินและการลงทุน (Financial Analyst)", "description": "วิเคราะห์ข้อมูลทางการเงิน ประเมินความเสี่ยง และวางแผนการลงทุน", "match_percentage": 94, "skills": ["Financial Modeling", "Risk Management", "การวิเคราะห์งบการเงิน"], "growth_outlook": "เติบโตสูง"},
                {"title": "ผู้ตรวจสอบบัญชีและนักวางระบบการเงิน (Auditor & FinTech)", "description": "ตรวจสอบและจัดระเบียบระบบบัญชีและการเงินให้มีความโปร่งใสและถูกต้อง", "match_percentage": 90, "skills": ["การสอบบัญชี", "กฎหมายภาษี", "ความละเอียดแม่นยำ"], "growth_outlook": "มั่นคงสูง"},
                {"title": "ผู้จัดการข้อมูลและกระบวนการทางธุรกิจ (Business Process Analyst)", "description": "ออกแบบและปรับปรุงขั้นตอนการดำเนินงานในองค์กรให้มีประสิทธิภาพสูงสุด", "match_percentage": 86, "skills": ["Data Governance", "Process Optimization", "การจัดการฐานข้อมูล"], "growth_outlook": "เติบโตต่อเนื่อง"}
            ]
        }

        top_dim = sorted_traits[0][0]
        second_dim = sorted_traits[1][0] if len(sorted_traits) > 1 else top_dim
        fallback_careers = list(dim_careers_map.get(top_dim, dim_careers_map["I"])[:2])
        if len(fallback_careers) < 3:
            second_career = dim_careers_map.get(second_dim, dim_careers_map["E"])[0]
            fallback_careers.append(second_career)

        gemini_data = {
            "archetype_title": f"ผู้บุกเบิกสาย {top_name}",
            "archetype_description": f"คุณเป็นคนที่มีความโดดเด่นด้าน {top_name} และมุ่งมั่นที่จะพัฒนาตนเอง",
            "personality_summary": f"คุณมีคะแนนโดดเด่นในกลุ่ม {top_code} ซึ่งสะท้อนถึงความเป็นคนชอบเรียนรู้ ลงมือทำ และมีวิสัยทัศน์ที่ชัดเจนในการแก้ปัญหา เหมาะอย่างยิ่งกับสาขาวิชาที่ได้ใช้ทั้งความคิดเชิงวิเคราะห์และความคิดสร้างสรรค์",
            "strengths": ["การคิดวิเคราะห์อย่างเป็นระบบ", "ความมุ่งมั่นในการเรียนรู้", "ความสามารถในการปรับตัว"],
            "ideal_work_environment": "สภาพแวดล้อมที่เปิดกว้าง มีพื้นที่ให้ได้คิดและสร้างสรรค์สิ่งใหม่",
            "campus_vibe_match": "มหาวิทยาลัยที่มีบรรยากาศส่งเสริมการเรียนรู้และมีสิ่งอำนวยความสะดวกครบครัน",
            "learning_style_match": "การเรียนที่ผสมผสานทฤษฎีกับการลงมือทำโครงงานจริง",
            "lifestyle_highlights": ["ชอบบรรยากาศที่เปิดกว้าง", "ให้ความสำคัญกับสมดุลการเรียนและการใช้ชีวิต"],
            "growth_advice": "เริ่มสะสมผลงาน (Portfolio) และหาโอกาสเข้าร่วมค่ายกิจกรรมหรืออบรมทักษะที่เกี่ยวข้อง",
            "share_quote": "ค้นพบตัวตนและเส้นทางที่ใช่ ก้าวสู่อนาคตอย่างมั่นใจ 🌟",
            "top_careers": fallback_careers,
            "search_keywords": fallback_keywords
        }

    # --- Query Undergraduate Courses from DB ---
    search_kws = gemini_data.get("search_keywords", [])
    recommended_courses = []

    try:
        from app.api.routes_courses import build_degree_level_filter
        degree_filter = build_degree_level_filter("ปริญญาตรี")
        base_query = db.query(CourseDB).options(
            defer(CourseDB.embedding), defer(CourseDB.embedding_text)
        )
        if degree_filter is not None:
            base_query = base_query.filter(degree_filter)

        matched_db = []
        
        # Use pre-computed embedding from parallel executor or compute on expanded search_kws
        embedding = pre_embedding
        if (not embedding or len(embedding) != 768) and search_kws:
            combined_text = f"{initial_course_query_text} {' '.join(search_kws)}"
            embedding = embedding_service.get_embedding(combined_text)

        if embedding and len(embedding) == 768:
            matched_db = base_query.filter(CourseDB.embedding.isnot(None)).order_by(
                CourseDB.embedding.cosine_distance(embedding)
            ).limit(6).all()
        
        # 2. Fallback to keyword matching if pgvector fails or returns empty
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
        campus_vibe_match=gemini_data.get("campus_vibe_match", "มหาวิทยาลัยที่มีบรรยากาศส่งเสริมการเรียนรู้และมีสิ่งอำนวยความสะดวกครบครัน"),
        learning_style_match=gemini_data.get("learning_style_match", "การเรียนที่ผสมผสานทฤษฎีกับการลงมือทำโครงงานจริง"),
        lifestyle_highlights=gemini_data.get("lifestyle_highlights", ["เปิดรับสิ่งใหม่", "มุ่งมั่นพัฒนาตนเอง"]),
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

