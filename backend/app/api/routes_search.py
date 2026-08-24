from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schema import SearchRequest, SearchResponse, ColdEmailRequest, ColdEmailResponse, SearchMatchResult
from app.models.db_models import FacultyDB
from app.api.routes_faculty import db_to_pydantic
from app.core.database import get_db
from app.core.embedding_service import embedding_service
import math

router = APIRouter(prefix="/search", tags=["Semantic Search & Match"])

@router.post("/", response_model=SearchResponse)
def search_and_match_advisors(request: SearchRequest, db: Session = Depends(get_db)):
    """
    AI Semantic Search & Matching endpoint for graduate students.
    Matches prospective thesis topics against faculty research domains using PostgreSQL pgvector.
    """
    if not request.query or len(request.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must contain at least 2 characters")

    # 1. Get query embedding
    query_vector = embedding_service.get_embedding(request.query)

    query_db = db.query(FacultyDB)
    if request.university:
        query_db = query_db.filter(FacultyDB.university.ilike(f"%{request.university}%") | FacultyDB.university_th.ilike(f"%{request.university}%"))
    if request.department:
        query_db = query_db.filter(FacultyDB.department.ilike(f"%{request.department}%") | FacultyDB.department_th.ilike(f"%{request.department}%"))

    ranked_results = []

    if query_vector:
        # 2. Use pgvector to calculate cosine distance
        # distance = 0 (identical) to 2 (opposite). Similarity = 1 - distance
        faculties = query_db.all() # Fetch all matching filters
        
        # Calculate scores in python since sqlite fallback might be used if pgvector fails in local dev, 
        # but the db schema uses Vector(768). Let's use sqlalchemy!
        
        # We can use order_by(FacultyDB.embedding.cosine_distance(query_vector))
        # But for compatibility across DBs in testing, we can do python dot product if we fetched them.
        # Since we use Supabase production, let's use the DB!
        try:
            results = db.query(
                FacultyDB,
                FacultyDB.embedding.cosine_distance(query_vector).label("distance")
            ).filter(FacultyDB.id.in_([f.id for f in query_db.all()])).order_by("distance").limit(request.top_k).all()
            
            for db_fac, dist in results:
                # 1. Lexical Keyword Boost
                # Expand the query first to catch English equivalents of Thai words
                expanded_query = embedding_service.expand_query(request.query).lower()
                query_tokens = expanded_query.split()
                
                corpus = " ".join((db_fac.research_interests or []) + (db_fac.taught_courses or [])).lower()
                
                final_dist = dist
                lexical_matched = False
                
                # Check if any significant word from expanded query is exactly in corpus
                for token in query_tokens:
                    if len(token) >= 2 and token in corpus:
                        lexical_matched = True
                        break
                        
                if lexical_matched:
                    final_dist -= 0.04  # Strong boost for exact keyword match
                
                # 2. Stretch the cosine distance (typically 0.33 to 0.52 for Gemini) into 0-100%
                normalized = max(0.0, min(1.0, (0.52 - final_dist) / (0.52 - 0.32)))
                ux_score = normalized * 100.0
                
                fac_model = db_to_pydantic(db_fac)
                explanation = embedding_service._generate_explanation(request.query, fac_model, ux_score)
                
                # Highlight keyword if there was a lexical match
                matched_kws = [request.query] if lexical_matched else []
                
                ranked_results.append(SearchMatchResult(
                    faculty=fac_model,
                    match_score=round(ux_score, 1),
                    ai_explanation=explanation,
                    matched_keywords=matched_kws
                ))
        except Exception as e:
            print(f"Vector search failed: {e}")
            # Fallback if DB vector search fails
            db_faculties = query_db.limit(request.top_k).all()
            for db_fac in db_faculties:
                fac_model = db_to_pydantic(db_fac)
                ranked_results.append(SearchMatchResult(
                    faculty=fac_model,
                    match_score=50.0,
                    ai_explanation="Fallback match",
                    matched_keywords=[]
                ))
    else:
        # Fallback if Gemini fails
        db_faculties = query_db.limit(request.top_k).all()
        for db_fac in db_faculties:
            fac_model = db_to_pydantic(db_fac)
            ranked_results.append(SearchMatchResult(
                faculty=fac_model,
                match_score=50.0,
                ai_explanation="ระบบ AI ไม่สามารถประมวลผลได้ในขณะนี้",
                matched_keywords=[]
            ))

    return SearchResponse(
        query=request.query,
        total_matched=len(ranked_results),
        results=ranked_results
    )


@router.post("/cold-email", response_model=ColdEmailResponse)
def generate_cold_email(req: ColdEmailRequest, db: Session = Depends(get_db)):
    # ... keep existing cold email logic ...
    db_faculty = db.query(FacultyDB).filter(FacultyDB.id == req.faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
        
    target_faculty = db_to_pydantic(db_faculty)
    
    faculty_name = target_faculty.full_name_th if target_faculty else "อาจารย์"
    dept_name = target_faculty.department_th if target_faculty else "ภาควิชา"
    
    if req.language == "th":
        subject = f"ขอรับคำปรึกษาและสอบถามโอกาสในการทำวิทยานิพนธ์ระดับ{req.intended_degree} - {req.student_name}"
        body = f"""เรียน {faculty_name} ที่เคารพ\n\nผม/ดิฉัน {req.student_name} มีความสนใจอย่างยิ่งที่จะศึกษาต่อระดับ{req.intended_degree} ใน{dept_name}\n\nจากการศึกษาผลงานวิชาการของอาจารย์พบว่ามีความสอดคล้องกับความสนใจของผม/ดิฉัน โดยเฉพาะในด้าน {", ".join(target_faculty.research_interests[:2]) if target_faculty.research_interests else 'งานวิจัยของท่าน'} ผม/ดิฉันจึงอยากขอคำปรึกษาเกี่ยวกับการทำวิจัยในหัวข้อ "{req.research_topic}"\n\nประวัติโดยย่อ:\n{req.student_background}\n\nผม/ดิฉันได้แนบประวัติการศึกษา (CV) และโครงร่างงานวิจัยเบื้องต้น (Research Proposal) มาพร้อมกับอีเมลฉบับนี้\n\nขอแสดงความนับถือ\n{req.student_name}\n"""
        tips = ["แนบไฟล์ CV (PDF) และ Transcripts", "ปรับแก้เนื้อหาให้ตรงกับสไตล์ของตนเอง", "ตรวจสอบความถูกต้องของชื่ออาจารย์ก่อนส่ง"]
    else:
        subject = f"Inquiry regarding {req.intended_degree} Thesis Advising - {req.student_name}"
        body = f"""Dear {faculty_name},\n\nMy name is {req.student_name}, and I am writing to express my strong interest in pursuing a {req.intended_degree} under your supervision at {dept_name}.\n\nI have reviewed your published research in {", ".join(target_faculty.research_interests[:2]) if target_faculty.research_interests else 'your research area'}, and I am particularly passionate about conducting research on "{req.research_topic}".\n\nBrief Background:\n{req.student_background}\n\nI have attached my CV and a brief research concept note for your review. I would be honored to discuss potential advising opportunities.\n\nThank you very much for your time and consideration.\n\nSincerely,\n{req.student_name}\n"""
        tips = ["Attach a concise 1-2 page CV (PDF format)", "Be clear and specific about why this professor's lab is the best fit", "Follow up politely after 7-10 business days if no reply"]

    return ColdEmailResponse(subject=subject, body=body, tips=tips)
