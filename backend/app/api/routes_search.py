from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, defer
from sqlalchemy import or_
from app.models.schema import SearchRequest, SearchResponse, ColdEmailRequest, ColdEmailResponse, SearchMatchResult, FacultyMember
from app.models.db_models import FacultyDB
from app.api.routes_faculty import db_to_pydantic
from app.core.database import get_db
from app.core.embedding_service import embedding_service
from app.core.dsa_utils import TopKHeap, Trie
from typing import List, Tuple, Dict, Any
import math

router = APIRouter(prefix="/search", tags=["Semantic Search & Match"])

def analyze_advisor_synergy(
    query_tokens: List[str],
    raw_query: str,
    faculty: FacultyMember
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Multi-faceted academic synergy analyzer using Set lookups & Trie token scanning:
    1. Extracts matching core research interests in O(1) set complexity
    2. Identifies specific publication titles matching the query
    3. Generates high-confidence synergy badges
    4. Formulates concrete thesis exploration angles
    """
    matched_interests_set = set()
    matched_interests = []
    matching_pubs_set = set()
    matching_pubs = []
    matched_kws_set = set()
    matched_kws = []
    synergy_badges = []
    suggested_angles = []

    interests = faculty.research_interests or []
    courses = faculty.taught_courses or []
    pubs = faculty.featured_publications or []

    # 1. Match Interests
    for interest in interests:
        int_lower = interest.lower()
        for token in query_tokens:
            if token in int_lower:
                if interest not in matched_interests_set:
                    matched_interests_set.add(interest)
                    matched_interests.append(interest)
                if token not in matched_kws_set:
                    matched_kws_set.add(token)
                    matched_kws.append(token)

    # 2. Match Publications
    for pub in pubs:
        pub_title = pub.title if hasattr(pub, "title") else (pub.get("title") if isinstance(pub, dict) else str(pub))
        if not pub_title:
            continue
        pub_lower = pub_title.lower()
        for token in query_tokens:
            if token in pub_lower:
                if pub_title not in matching_pubs_set:
                    matching_pubs_set.add(pub_title)
                    matching_pubs.append(pub_title)
                if token not in matched_kws_set:
                    matched_kws_set.add(token)
                    matched_kws.append(token)

    # 3. Match Taught Courses
    matched_courses_set = set()
    for c in courses:
        c_lower = c.lower()
        for token in query_tokens:
            if token in c_lower:
                if c not in matched_courses_set:
                    matched_courses_set.add(c)
                if token not in matched_kws_set:
                    matched_kws_set.add(token)
                    matched_kws.append(token)

    # Generate Badges based on academic evidence
    if matched_interests:
        synergy_badges.append("⭐ ตรงสายงานวิจัยหลัก (Direct Research Focus)")
    if matching_pubs:
        synergy_badges.append(f"📄 มีผลงานตีพิมพ์ตรงหัวข้อ ({len(matching_pubs)} เรื่อง)")
    if matched_courses_set:
        synergy_badges.append("📚 รับผิดชอบรายวิชาที่เกี่ยวข้อง")
    if faculty.scholar_url or (pubs and len(pubs) >= 3):
        synergy_badges.append("🏆 งานวิจัยตีพิมพ์ระดับนานาชาติ")
    if faculty.academic_title_th in ["ศ.ดร.", "รศ.ดร.", "ผศ.ดร."]:
        synergy_badges.append("🎓 ผู้เชี่ยวชาญระดับดุษฎีบัณฑิต")

    # Generate Contextual Thesis Exploration Angles
    focus_topic = matched_interests[0] if matched_interests else (interests[0] if interests else raw_query)
    clean_query = raw_query.strip()

    if "ai" in clean_query.lower() or "ปัญญาประดิษฐ์" in clean_query or "machine learning" in clean_query.lower():
        suggested_angles.append(f"การประยุกต์ใช้ AI & Data-driven Models ในการพัฒนา {focus_topic}")
        suggested_angles.append(f"การพัฒนาแบบจำลองการทำนายขั้นสูงเพื่อยกระดับ {focus_topic}")
    elif "พลังงาน" in clean_query or "energy" in clean_query.lower() or "solar" in clean_query.lower():
        suggested_angles.append(f"การเพิ่มประสิทธิภาพระบบพลังงานและความยั่งยืนในบริบท {focus_topic}")
        suggested_angles.append(f"การบูรณาการระบบควบคุมอัจฉริยะและการจัดการพลังงาน {focus_topic}")
    elif "แพทย์" in clean_query or "สุขภาพ" in clean_query or "biomedical" in clean_query.lower() or "health" in clean_query.lower():
        suggested_angles.append(f"การวิจัยเชิงลึกด้านนวัตกรรมและเทคโนโลยีทางสุขภาพใน {focus_topic}")
        suggested_angles.append(f"การศึกษาเชิงทดลองและการประเมินประสิทธิผลสำหรับ {focus_topic}")
    elif "บริหาร" in clean_query or "การตลาด" in clean_query or "การเงิน" in clean_query or "finance" in clean_query.lower():
        suggested_angles.append(f"การวิเคราะห์เชิงประจักษ์และการวางกลยุทธ์การเติบโตด้าน {focus_topic}")
        suggested_angles.append(f"ผลกระทบของการเปลี่ยนแปลงทางดิจิทัลต่อการบริหารจัดการ {focus_topic}")
    else:
        suggested_angles.append(f"การศึกษาและพัฒนาระเบียบวิธีวิจัยขั้นสูงสำหรับ {focus_topic}")
        suggested_angles.append(f"การประยุกต์ใช้เทคโนโลยีสมัยใหม่เพื่อแก้ปัญหา {clean_query} ร่วมกับ {focus_topic}")

    return matched_kws, matching_pubs, synergy_badges, suggested_angles


def keyword_fallback_search(query_str: str, query_db, top_k: int) -> list[SearchMatchResult]:
    """Fallback ranking algorithm based on rich multi-tier matching when AI embedding is unavailable."""
    expanded_query = embedding_service.expand_query(query_str).lower()
    raw_tokens = [t.strip() for t in expanded_query.split() if len(t.strip()) >= 2]

    # 1. SQL-level candidate pre-filtering
    candidate_query = query_db.options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text))
    if raw_tokens:
        filters = []
        for token in raw_tokens[:6]:
            pattern = f"%{token}%"
            filters.append(FacultyDB.full_name_th.ilike(pattern))
            filters.append(FacultyDB.first_name.ilike(pattern))
            filters.append(FacultyDB.last_name.ilike(pattern))
            filters.append(FacultyDB.department_th.ilike(pattern))
            filters.append(FacultyDB.department.ilike(pattern))
            filters.append(FacultyDB.faculty_th.ilike(pattern))
            filters.append(FacultyDB.faculty.ilike(pattern))
            filters.append(FacultyDB.embedding_text.ilike(pattern))

        faculties = candidate_query.filter(or_(*filters)).limit(max(top_k * 4, 35)).all()
        if not faculties:
            faculties = candidate_query.limit(max(top_k * 2, 20)).all()
    else:
        faculties = candidate_query.limit(top_k).all()

    # 2. DSA Optimization: Use TopKHeap for O(N log K) selection
    heap = TopKHeap[Tuple[FacultyMember, float, List[str], List[str], List[str], List[str]]](k=top_k)

    for db_fac in faculties:
        fac_model = db_to_pydantic(db_fac)
        matched_kws, matching_pubs, badges, angles = analyze_advisor_synergy(raw_tokens, query_str, fac_model)

        # Multi-factor score computation
        base_score = 50.0
        hit_bonus = len(matched_kws) * 8.0
        pub_bonus = min(len(matching_pubs) * 5.0, 10.0)
        scholar_bonus = 3.0 if fac_model.scholar_url else 0.0

        total_score = min(96.0, base_score + hit_bonus + pub_bonus + scholar_bonus)
        if len(matched_kws) == 0:
            total_score = 48.0

        heap.push(total_score, (fac_model, total_score, matched_kws, matching_pubs, badges, angles))

    top_candidates = heap.get_top_k_descending()

    results = []
    for fac_model, score, matched_kws, matching_pubs, badges, angles in top_candidates:
        explanation = embedding_service.generate_smart_explanation(
            query_str, fac_model, score, matched_kws, matching_pubs
        )
        results.append(SearchMatchResult(
            faculty=fac_model,
            match_score=round(score, 1),
            ai_explanation=explanation,
            matched_keywords=matched_kws[:4],
            matching_publications=matching_pubs[:2],
            synergy_badges=badges,
            suggested_thesis_angles=angles
        ))
    return results

@router.post("/", response_model=SearchResponse)
def search_and_match_advisors(request: SearchRequest, db: Session = Depends(get_db)):
    """
    AI Semantic Search & Hybrid Multi-Evidence Matching endpoint for prospective graduate students.
    Matches thesis proposals against faculty research corpus, publications, and supervised domains with pgvector.
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

            # Fetch candidates using HNSW index
            candidates_limit = max(request.top_k * 2, 25)
            results = vector_query.order_by(distance_col).limit(candidates_limit).all()

            expanded_query = embedding_service.expand_query(request.query).lower()
            query_tokens = [t for t in expanded_query.split() if len(t) >= 2]

            # DSA Optimization: Min-Heap for Top-K extraction in O(N log K)
            heap = TopKHeap[SearchMatchResult](k=request.top_k)

            for db_fac, dist in results:
                fac_model = db_to_pydantic(db_fac)
                matched_kws, matching_pubs, badges, angles = analyze_advisor_synergy(query_tokens, request.query, fac_model)

                # 1. Semantic vector similarity (calibrated 0.0 - 1.0)
                # Gemini cosine distance range typically 0.28 (identical) to 0.54 (unrelated)
                sim_base = max(0.0, min(1.0, (0.54 - dist) / (0.54 - 0.28)))

                # 2. Multi-Evidence Hybrid Weighting
                # Exact / Substring Keyword synergy bonus
                keyword_bonus = min(len(matched_kws) * 0.04, 0.12)
                # Publication synergy bonus
                pub_bonus = min(len(matching_pubs) * 0.03, 0.08)
                # Scholar / Active Research Profile bonus
                scholar_bonus = 0.02 if fac_model.scholar_url else 0.0

                composite_score = min(0.99, sim_base + keyword_bonus + pub_bonus + scholar_bonus)
                ux_score = round(composite_score * 100.0, 1)

                explanation = embedding_service.generate_smart_explanation(
                    request.query, fac_model, ux_score, matched_kws, matching_pubs
                )

                candidate_item = SearchMatchResult(
                    faculty=fac_model,
                    match_score=ux_score,
                    ai_explanation=explanation,
                    matched_keywords=matched_kws[:4] if matched_kws else [request.query],
                    matching_publications=matching_pubs[:2],
                    synergy_badges=badges,
                    suggested_thesis_angles=angles
                )
                heap.push(ux_score, candidate_item)

            ranked_results = heap.get_top_k_descending()

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

