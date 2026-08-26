from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.schema import CourseSchema, CourseSearchRequest, CourseSearchResponse
from app.models.db_models import CourseDB
from app.core.database import get_db
from app.core.embedding_service import embedding_service

router = APIRouter(prefix="/courses", tags=["University Courses"])

def db_course_to_pydantic(db_course: CourseDB, match_score: float = 95.0) -> CourseSchema:
    return CourseSchema(
        id=db_course.id,
        title_th=db_course.title_th,
        title_en=db_course.title_en,
        degree_level=db_course.degree_level,
        degree_name=db_course.degree_name,
        university=db_course.university,
        university_th=db_course.university_th,
        faculty=db_course.faculty,
        faculty_th=db_course.faculty_th,
        department=db_course.department,
        department_th=db_course.department_th,
        program_type=db_course.program_type or "ภาคปกติ",
        duration_years=db_course.duration_years,
        total_credits=db_course.total_credits,
        tuition_per_semester=db_course.tuition_per_semester,
        tuition_total=db_course.tuition_total,
        description=db_course.description,
        curriculum_highlights=db_course.curriculum_highlights or [],
        career_paths=db_course.career_paths or [],
        tags=db_course.tags or [],
        website_url=db_course.website_url,
        match_score=match_score
    )

from sqlalchemy import or_

def build_degree_level_filter(degree_level: Optional[str]):
    """
    Returns an OR filter condition for degree_level covering Thai and English representations:
    - Bachelor: ปริญญาตรี, Bachelor, Bachelor's Degree, undergrad, etc.
    - Master: ปริญญาโท, Master, Master's Degree, etc.
    - Doctorate: ปริญญาเอก, Doctor, Ph.D, Ph.D., Doctoral, Doctorate, PhD, etc.
    - Certificate: ประกาศนียบัตร, Certificate, Diploma, Graduate Diploma, cert, etc.
    """
    if not degree_level or degree_level.strip().lower() == "all":
        return None
    
    raw = degree_level.strip().lower()
    
    if any(k in raw for k in ["ตรี", "bachelor", "undergrad"]):
        targets = ["ปริญญาตรี", "bachelor"]
    elif any(k in raw for k in ["โท", "master"]):
        targets = ["ปริญญาโท", "master"]
    elif any(k in raw for k in ["เอก", "doctor", "ph.d", "phd", "doctoral", "doctorate"]):
        targets = ["ปริญญาเอก", "doctor", "ph.d", "phd", "doctoral", "doctorate"]
    elif any(k in raw for k in ["ประกาศนียบัตร", "certificate", "diploma", "cert"]):
        targets = ["ประกาศนียบัตร", "certificate", "diploma"]
    else:
        targets = [degree_level.strip()]
        
    return or_(*[CourseDB.degree_level.ilike(f"%{t}%") for t in targets])

@router.get("/", response_model=List[CourseSchema])
def list_courses(
    university: Optional[str] = None,
    degree_level: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(CourseDB)
    if university and university != "all":
        query = query.filter(CourseDB.university.ilike(f"%{university}%") | CourseDB.university_th.ilike(f"%{university}%"))
    
    degree_filter = build_degree_level_filter(degree_level)
    if degree_filter is not None:
        query = query.filter(degree_filter)
    
    courses = query.limit(limit).all()
    return [db_course_to_pydantic(c) for c in courses]

@router.post("/search", response_model=CourseSearchResponse)
def search_courses(request: CourseSearchRequest, db: Session = Depends(get_db)):
    query = db.query(CourseDB)
    
    if request.university and request.university != "all":
        query = query.filter(CourseDB.university.ilike(f"%{request.university}%") | CourseDB.university_th.ilike(f"%{request.university}%"))
    
    degree_filter = build_degree_level_filter(request.degree_level)
    if degree_filter is not None:
        query = query.filter(degree_filter)

    if request.query and len(request.query.strip()) > 0:
        query_str = request.query.strip()
        
        # Thai academic slang / abbreviation / misspelling mapping
        # Longest keys first to prevent partial replacements overlapping incorrectly
        th_slang_map = {
            "หมอฟัน": "ทันตแพทยศาสตร์",
            "ทันตแพทย์": "ทันตแพทยศาสตร์",
            "ทันตะ": "ทันตแพทยศาสตร์",
            "หมอสัตว์": "สัตวแพทยศาสตร์",
            "หมอหมา": "สัตวแพทยศาสตร์",
            "หมอแมว": "สัตวแพทยศาสตร์",
            "สัตวแพทย์": "สัตวแพทยศาสตร์",
            "สัตวแพทย์ศาสตร์": "สัตวแพทยศาสตร์",
            "หมอตา": "ทัศนมาตรศาสตร์",
            "หมอ": "แพทยศาสตร์",
            "แพทย์": "แพทยศาสตร์",
            "แพทศาสตร์": "แพทยศาสตร์",
            "พยาบาล": "พยาบาลศาสตร์",
            "เภสัช": "เภสัชศาสตร์",
            "เปสัช": "เภสัชศาสตร์",
            "สาสุข": "สาธารณสุข",
            "สถาปัตย์": "สถาปัตยกรรม",
            "ถาปัตย์": "สถาปัตยกรรม",
            "สถาปัต": "สถาปัตยกรรม",
            "วิศวะ": "วิศวกรรม",
            "วิดวะ": "วิศวกรรม",
            "วิศว": "วิศวกรรม",
            "วิทย์กีฬา": "วิทยาศาสตร์การกีฬา",
            "วิดยา": "วิทยาศาสตร์",
            "วิทย์": "วิทยาศาสตร์",
            "วิทยา": "วิทยาศาสตร์",
            "คุรุศาสตร์": "ครุศาสตร์",
            "ครู": "ครุศาสตร์",
            "ศึกษา": "ศึกษาศาสตร์",
            "บริหาร": "บริหารธุรกิจ",
            "บันชี": "บัญชี",
            "เสดสาด": "เศรษฐศาสตร์",
            "เศรษฐ": "เศรษฐศาสตร์",
            "มนุษย์": "มนุษยศาสตร์",
            "มนุษ": "มนุษยศาสตร์",
            "มนุส": "มนุษยศาสตร์",
            "นิติ": "นิติศาสตร์",
            "กฎหมาย": "นิติศาสตร์",
            "ศิลปกรรม": "ศิลปกรรมศาสตร์",
            "สินกำ": "ศิลปกรรมศาสตร์",
            "นิเทศ": "นิเทศศาสตร์",
            "แมสคอม": "สื่อสารมวลชน",
            "ไอที": "เทคโนโลยีสารสนเทศ",
            "it": "เทคโนโลยีสารสนเทศ"
        }
        
        # We must sort by length descending to ensure longer words are replaced first
        sorted_slang = sorted(th_slang_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for slang, formal in sorted_slang:
            # For short English words like 'it', ensure we match exactly or case-insensitive without replacing inside words like 'architecture'
            if slang == 'it':
                if 'it' in query_str.lower().split():
                    query_str = query_str.lower().replace('it', formal)
            elif slang in query_str and formal not in query_str:
                query_str = query_str.replace(slang, formal)

        # 1. AI Vector Search (Semantic)
        query_vector = embedding_service.get_embedding(query_str)
        
        if query_vector:
            # Use pgvector cosine_distance. COALESCE to handle courses that don't have embeddings yet (push to bottom)
            from sqlalchemy.sql.expression import func
            distance_expr = func.coalesce(CourseDB.embedding.cosine_distance(query_vector), 2.0)
            
            # Hybrid approach: We still want to prioritize exact matches slightly.
            # However, for pure AI semantic search, ordering by distance is enough!
            query = query.order_by(distance_expr)
        else:
            # Fallback if Gemini vector embedding is unavailable
            tokens = [t.strip() for t in query_str.split() if len(t.strip()) >= 2]
            if tokens:
                token_filters = [
                    CourseDB.title_th.ilike(f"%{t}%") |
                    CourseDB.title_en.ilike(f"%{t}%") |
                    CourseDB.faculty_th.ilike(f"%{t}%") |
                    CourseDB.description.ilike(f"%{t}%")
                    for t in tokens
                ]
                query = query.filter(or_(*token_filters))
            else:
                q = f"%{query_str}%"
                query = query.filter(
                    CourseDB.title_th.ilike(q) |
                    CourseDB.title_en.ilike(q) |
                    CourseDB.faculty_th.ilike(q) |
                    CourseDB.description.ilike(q)
                )

    matched_courses = query.limit(request.top_k).all()
    results = [db_course_to_pydantic(c) for c in matched_courses]

    return CourseSearchResponse(
        query=request.query or "",
        total_matched=len(results),
        results=results
    )

@router.get("/{course_id}", response_model=CourseSchema)
def get_course_detail(course_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return db_course_to_pydantic(course)
