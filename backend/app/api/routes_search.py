from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schema import SearchRequest, SearchResponse, ColdEmailRequest, ColdEmailResponse, SearchMatchResult
from app.models.db_models import FacultyDB
from app.api.routes_faculty import db_to_pydantic
from app.core.database import get_db
from app.core.embedding_service import embedding_service
import math

router = APIRouter(prefix="/search", tags=["Semantic Search & Match"])

def keyword_fallback_search(query_str: str, query_db, top_k: int) -> list[SearchMatchResult]:
    """Fallback ranking algorithm based on lexical keyword matching when AI embedding is unavailable."""
    expanded_query = embedding_service.expand_query(query_str).lower()
    raw_tokens = [t.strip() for t in expanded_query.split() if len(t.strip()) >= 2]
    
    faculties = query_db.all()
    scored_list = []
    
    for db_fac in faculties:
        corpus_list = (db_fac.research_interests or []) + (db_fac.taught_courses or [])
        corpus_text = " ".join(corpus_list).lower()
        full_text = f"{corpus_text} {(db_fac.department_th or '').lower()} {(db_fac.full_name_th or '').lower()} {(db_fac.embedding_text or '').lower()}"
        
        hit_count = 0
        matched_kws = []
        for token in raw_tokens:
            if token in full_text:
                hit_count += 1
                if token not in matched_kws:
                    matched_kws.append(token)
                    
        # Calculate dynamic score between 50% and 92% based on matches
        if hit_count > 0:
            score = min(92.0, 65.0 + (hit_count * 7.0))
        else:
            score = 45.0
            
        scored_list.append((db_fac, score, matched_kws))
        
    # Sort by score descending
    scored_list.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for db_fac, score, matched_kws in scored_list[:top_k]:
        fac_model = db_to_pydantic(db_fac)
        if matched_kws:
            interests_matched = [i for i in (fac_model.research_interests or []) if any(k in i.lower() for k in matched_kws)]
            int_str = ", ".join(interests_matched[:2]) if interests_matched else (fac_model.research_interests[0] if fac_model.research_interests else "หัวข้อที่เกี่ยวข้อง")
            explanation = f"อาจารย์มีความเชี่ยวชาญด้าน {int_str} ซึ่งตรงกับคำค้นหาของคุณ"
        else:
            explanation = "อาจารย์ในสาขาวิชาที่เกี่ยวข้องกับหัวข้อที่คุณค้นหา"
            
        results.append(SearchMatchResult(
            faculty=fac_model,
            match_score=round(score, 1),
            ai_explanation=explanation,
            matched_keywords=matched_kws[:3]
        ))
    return results

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
        try:
            results = db.query(
                FacultyDB,
                FacultyDB.embedding.cosine_distance(query_vector).label("distance")
            ).filter(FacultyDB.id.in_([f.id for f in query_db.all()])).order_by("distance").limit(request.top_k).all()
            
            for db_fac, dist in results:
                # 1. Lexical Keyword Boost
                expanded_query = embedding_service.expand_query(request.query).lower()
                query_tokens = expanded_query.split()
                
                corpus = " ".join((db_fac.research_interests or []) + (db_fac.taught_courses or [])).lower()
                
                final_dist = dist
                lexical_matched = False
                
                for token in query_tokens:
                    if len(token) >= 2 and token in corpus:
                        lexical_matched = True
                        break
                    if len(token) >= 5:
                        stem = token.removesuffix('s').removesuffix('ing').removesuffix('ation').removesuffix('e')
                        if len(stem) >= 4 and stem in corpus:
                            lexical_matched = True
                            break
                        
                if lexical_matched:
                    final_dist -= 0.04  # Strong boost for exact keyword match
                
                # 2. Stretch the cosine distance (typically 0.33 to 0.52 for Gemini) into 0-100%
                normalized = max(0.0, min(1.0, (0.52 - final_dist) / (0.52 - 0.32)))
                ux_score = normalized * 100.0
                
                fac_model = db_to_pydantic(db_fac)
                explanation = embedding_service._generate_explanation(request.query, fac_model, ux_score)
                
                matched_kws = [request.query] if lexical_matched else []
                
                ranked_results.append(SearchMatchResult(
                    faculty=fac_model,
                    match_score=round(ux_score, 1),
                    ai_explanation=explanation,
                    matched_keywords=matched_kws
                ))
        except Exception as e:
            print(f"Vector search failed, using smart keyword fallback: {e}")
            ranked_results = keyword_fallback_search(request.query, query_db, request.top_k)
    else:
        # Fallback if Gemini vector embedding is rate-limited or unavailable
        ranked_results = keyword_fallback_search(request.query, query_db, request.top_k)

    return SearchResponse(
        query=request.query,
        total_matched=len(ranked_results),
        results=ranked_results
    )


@router.post("/cold-email", response_model=ColdEmailResponse)
def generate_cold_email(req: ColdEmailRequest, db: Session = Depends(get_db)):
    db_faculty = db.query(FacultyDB).filter(FacultyDB.id == req.faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
        
    target_faculty = db_to_pydantic(db_faculty)
    
    subject, body, tips = embedding_service.generate_cold_email_ai(req.model_dump(), target_faculty)

    return ColdEmailResponse(subject=subject, body=body, tips=tips)
