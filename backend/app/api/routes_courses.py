import re
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from sqlalchemy.orm import Session, defer, load_only
from sqlalchemy import or_
from typing import List, Optional
from app.models.schema import CourseSchema, CourseCardSchema, CourseSearchRequest, CourseSearchResponse
from app.models.db_models import CourseDB
from app.core.database import get_db
from app.core.embedding_service import embedding_service

# Egress budget: list/card payloads must skip heavy columns server-side so
# Supabase never ships description / tags / tuition_total / embedding_text.
_COURSE_CARD_COLUMNS = (
    CourseDB.id,
    CourseDB.title_th, CourseDB.title_en,
    CourseDB.degree_level, CourseDB.degree_name,
    CourseDB.university, CourseDB.university_th,
    CourseDB.faculty, CourseDB.faculty_th,
    CourseDB.department, CourseDB.department_th,
    CourseDB.program_type,
    CourseDB.duration_years, CourseDB.total_credits,
    CourseDB.tuition_per_semester,
    CourseDB.curriculum_highlights, CourseDB.career_paths,
    CourseDB.website_url,
)

router = APIRouter(prefix="/courses", tags=["University Courses"])

TH_SLANG_MAP = {
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

_SORTED_SLANG_KEYS = sorted([k for k in TH_SLANG_MAP.keys() if k != "it"], key=len, reverse=True)
_SLANG_REGEX = re.compile("|".join(re.escape(k) for k in _SORTED_SLANG_KEYS))
# DSA audit 2026-09-10 (#7): precompiled alongside _SLANG_REGEX (AGENTS.md §5.3).
_IT_WORD_RE = re.compile(r"\b[iI][tT]\b")

def normalize_query_slang(query_str: str) -> str:
    """Fast single-pass normalization of Thai slang and abbreviations."""
    result = query_str
    # Replace whole-word 'it' case-insensitively
    result = _IT_WORD_RE.sub("เทคโนโลยีสารสนเทศ", result)
    # Replace other Thai slang terms in one pass
    return _SLANG_REGEX.sub(lambda m: TH_SLANG_MAP.get(m.group(0), m.group(0)), result)

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


def db_course_to_card(db_course: CourseDB, match_score: float = 95.0) -> CourseCardSchema:
    """Slim converter — only touches columns in _COURSE_CARD_COLUMNS (never deferred attrs)."""
    return CourseCardSchema(
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
        curriculum_highlights=list(db_course.curriculum_highlights or [])[:3],
        career_paths=list(db_course.career_paths or [])[:4],
        website_url=db_course.website_url,
        match_score=match_score
    )

def build_degree_level_filter(degree_level: Optional[str]):
    """
    Returns an index-accelerated filter condition for degree_level utilizing B-Tree index.
    """
    if not degree_level or degree_level.strip().lower() == "all":
        return None
    
    raw = degree_level.strip().lower()
    
    if any(k in raw for k in ["ตรี", "bachelor", "undergrad"]):
        targets = ["ปริญญาตรี", "Bachelor", "bachelor", "Bachelor's Degree"]
    elif any(k in raw for k in ["โท", "master"]):
        targets = ["ปริญญาโท", "Master", "master", "Master's Degree", "วท.ม.", "วศ.ม.", "บธ.ม."]
    elif any(k in raw for k in ["เอก", "doctor", "ph.d", "phd", "doctoral", "doctorate"]):
        targets = ["ปริญญาเอก", "Doctorate", "Ph.D.", "doctoral", "doctorate"]
    elif any(k in raw for k in ["ประกาศนียบัตร", "certificate", "diploma", "cert"]):
        targets = ["ประกาศนียบัตร", "Certificate", "Diploma"]
    else:
        targets = [degree_level.strip()]
        
    return CourseDB.degree_level.in_(targets) | or_(*[CourseDB.degree_level.startswith(t) for t in targets])

@router.get("/", response_model=List[CourseCardSchema])
def list_courses(
    university: Optional[str] = None,
    degree_level: Optional[str] = None,
    limit: int = 24,
    db: Session = Depends(get_db)
):
    limit = max(1, min(limit, 50))
    query = db.query(CourseDB).options(load_only(*_COURSE_CARD_COLUMNS))
    if university and university != "all":
        query = query.filter(CourseDB.university.ilike(f"%{university}%") | CourseDB.university_th.ilike(f"%{university}%"))

    degree_filter = build_degree_level_filter(degree_level)
    if degree_filter is not None:
        query = query.filter(degree_filter)

    courses = query.limit(limit).all()
    return [db_course_to_card(c) for c in courses]

@router.post("/search", response_model=CourseSearchResponse)
def search_courses(request: CourseSearchRequest, db: Session = Depends(get_db)):
    query = db.query(CourseDB).options(load_only(*_COURSE_CARD_COLUMNS))

    if request.university and request.university.strip() and request.university.strip().lower() != "all":
        query = query.filter(CourseDB.university.ilike(f"%{request.university.strip()}%") | CourseDB.university_th.ilike(f"%{request.university.strip()}%"))

    if request.faculty and request.faculty.strip() and request.faculty.strip().lower() != "all":
        query = query.filter(CourseDB.faculty.ilike(f"%{request.faculty.strip()}%") | CourseDB.faculty_th.ilike(f"%{request.faculty.strip()}%"))

    degree_filter = build_degree_level_filter(request.degree_level)
    if degree_filter is not None:
        query = query.filter(degree_filter)

    if request.query and len(request.query.strip()) > 0:
        query_str = normalize_query_slang(request.query.strip())

        # 1. AI Vector Search (Semantic)
        query_vector = embedding_service.get_embedding(query_str)
        
        if query_vector:
            # Slim-select IDs by vector rank first, then fetch slim columns.
            # (load_only + ORDER BY vector expression forces Postgres to ship
            #  the 768-dim vector per row; two-step avoids that egress.)
            vector_query = db.query(CourseDB.id).filter(CourseDB.embedding.isnot(None))
            if request.university and request.university.strip() and request.university.strip().lower() != "all":
                u_clean = request.university.strip()
                vector_query = vector_query.filter(CourseDB.university.ilike(f"%{u_clean}%") | CourseDB.university_th.ilike(f"%{u_clean}%"))
            if request.faculty and request.faculty.strip() and request.faculty.strip().lower() != "all":
                f_clean = request.faculty.strip()
                vector_query = vector_query.filter(CourseDB.faculty.ilike(f"%{f_clean}%") | CourseDB.faculty_th.ilike(f"%{f_clean}%"))
            if degree_filter is not None:
                vector_query = vector_query.filter(degree_filter)

            id_rows = (
                vector_query
                .order_by(CourseDB.embedding.cosine_distance(query_vector))
                .limit(request.top_k)
                .all()
            )
            ranked_ids = [r.id for r in id_rows]
            if not ranked_ids:
                return CourseSearchResponse(query=request.query or "", total_matched=0, results=[])
            matched_courses = (
                db.query(CourseDB)
                .options(load_only(*_COURSE_CARD_COLUMNS))
                .filter(CourseDB.id.in_(ranked_ids))
                .all()
            )
            order = {cid: i for i, cid in enumerate(ranked_ids)}
            matched_courses.sort(key=lambda c: order.get(c.id, 1 << 30))
            return CourseSearchResponse(
                query=request.query or "",
                total_matched=len(matched_courses),
                results=[db_course_to_card(c) for c in matched_courses],
            )
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
    results = [db_course_to_card(c) for c in matched_courses]

    return CourseSearchResponse(
        query=request.query or "",
        total_matched=len(results),
        results=results
    )

@router.get("/{course_id}", response_model=CourseSchema)
def get_course_detail(course_id: str, response: Response, db: Session = Depends(get_db)):
    course = db.query(CourseDB).options(defer(CourseDB.embedding), defer(CourseDB.embedding_text)).filter(CourseDB.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    response.headers["Cache-Control"] = "public, max-age=600"
    return db_course_to_pydantic(course)
