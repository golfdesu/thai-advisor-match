from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, defer
from sqlalchemy import or_
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

    # 1. SQL-level candidate pre-filtering to prevent loading entire database into RAM
    candidate_query = query_db.options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text))
    if raw_tokens:
        filters = []
        for token in raw_tokens[:5]:
            pattern = f"%{token}%"
            filters.append(FacultyDB.full_name_th.ilike(pattern))
            filters.append(FacultyDB.department_th.ilike(pattern))
            filters.append(FacultyDB.faculty_th.ilike(pattern))

        faculties = candidate_query.filter(or_(*filters)).limit(max(top_k * 4, 30)).all()
        if not faculties:
            faculties = candidate_query.limit(max(top_k * 2, 20)).all()
    else:
        faculties = candidate_query.limit(top_k).all()
    scored_list = []

    for db_fac in faculties:
        corpus_list = (db_fac.research_interests or []) + (db_fac.taught_courses or [])
        corpus_text = " ".join(corpus_list).lower()
        full_text = f"{corpus_text} {(db_fac.department_th or '').lower()} {(db_fac.full_name_th or '').lower()}"

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
        explanation = embedding_service.generate_smart_explanation(query_str, fac_model, score, matched_kws)
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

    # 1. Base query with optional filters
    query_db = db.query(FacultyDB).options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text))
    if request.university and request.university.strip() and request.university.strip().lower() != "all":
        query_db = query_db.filter(
            FacultyDB.university.ilike(f"%{request.university.strip()}%") |
            FacultyDB.university_th.ilike(f"%{request.university.strip()}%")
        )
    if request.faculty and request.faculty.strip() and request.faculty.strip().lower() != "all":
        query_db = query_db.filter(
            FacultyDB.faculty.ilike(f"%{request.faculty.strip()}%") |
            FacultyDB.faculty_th.ilike(f"%{request.faculty.strip()}%")
        )
    if request.department and request.department.strip() and request.department.strip().lower() != "all":
        query_db = query_db.filter(
            FacultyDB.department.ilike(f"%{request.department.strip()}%") |
            FacultyDB.department_th.ilike(f"%{request.department.strip()}%")
        )

    # 2. Get query embedding
    query_vector = embedding_service.get_embedding(request.query)

    ranked_results = []

    if query_vector:
        try:
            distance_col = FacultyDB.embedding.cosine_distance(query_vector).label("distance")
            vector_query = (
                db.query(FacultyDB, distance_col)
                .options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text))
                .filter(FacultyDB.embedding.isnot(None))
            )
            if request.university and request.university.strip() and request.university.strip().lower() != "all":
                vector_query = vector_query.filter(
                    FacultyDB.university.ilike(f"%{request.university.strip()}%") |
                    FacultyDB.university_th.ilike(f"%{request.university.strip()}%")
                )
            if request.faculty and request.faculty.strip() and request.faculty.strip().lower() != "all":
                vector_query = vector_query.filter(
                    FacultyDB.faculty.ilike(f"%{request.faculty.strip()}%") |
                    FacultyDB.faculty_th.ilike(f"%{request.faculty.strip()}%")
                )
            if request.department and request.department.strip() and request.department.strip().lower() != "all":
                vector_query = vector_query.filter(
                    FacultyDB.department.ilike(f"%{request.department.strip()}%") |
                    FacultyDB.department_th.ilike(f"%{request.department.strip()}%")
                )

            results = vector_query.order_by(distance_col).limit(request.top_k).all()
            
            expanded_query = embedding_service.expand_query(request.query).lower()
            query_tokens = [t for t in expanded_query.split() if len(t) >= 2]
            
            for db_fac, dist in results:
                # 1. Lexical Keyword Boost
                corpus = " ".join((db_fac.research_interests or []) + (db_fac.taught_courses or [])).lower()
                
                final_dist = dist
                lexical_matched = False
                matched_kws = []
                
                for token in query_tokens:
                    if token in corpus:
                        lexical_matched = True
                        if token not in matched_kws:
                            matched_kws.append(token)
                    elif len(token) >= 5:
                        stem = token.removesuffix('s').removesuffix('ing').removesuffix('ation').removesuffix('e')
                        if len(stem) >= 4 and stem in corpus:
                            lexical_matched = True
                            if token not in matched_kws:
                                matched_kws.append(token)
                        
                if lexical_matched:
                    final_dist -= 0.04  # Strong boost for exact keyword match
                
                # 2. Stretch the cosine distance (typically 0.33 to 0.52 for Gemini) into 0-100%
                normalized = max(0.0, min(1.0, (0.52 - final_dist) / (0.52 - 0.32)))
                ux_score = normalized * 100.0
                
                fac_model = db_to_pydantic(db_fac)
                explanation = embedding_service.generate_smart_explanation(
                    request.query, fac_model, ux_score, matched_kws
                )
                
                ranked_results.append(SearchMatchResult(
                    faculty=fac_model,
                    match_score=round(ux_score, 1),
                    ai_explanation=explanation,
                    matched_keywords=matched_kws[:3] if matched_kws else ([request.query] if lexical_matched else [])
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
