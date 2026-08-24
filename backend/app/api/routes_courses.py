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
    if degree_level and degree_level != "all":
        query = query.filter(CourseDB.degree_level.ilike(f"%{degree_level}%"))
    
    courses = query.limit(limit).all()
    return [db_course_to_pydantic(c) for c in courses]

@router.post("/search", response_model=CourseSearchResponse)
def search_courses(request: CourseSearchRequest, db: Session = Depends(get_db)):
    query = db.query(CourseDB)
    
    if request.university and request.university != "all":
        query = query.filter(CourseDB.university.ilike(f"%{request.university}%") | CourseDB.university_th.ilike(f"%{request.university}%"))
    
    if request.degree_level and request.degree_level != "all":
        # Map common keys
        level_map = {
            "bachelor": "ปริญญาตรี",
            "master": "ปริญญาโท",
            "doctorate": "ปริญญาเอก",
            "certificate": "ประกาศนียบัตร"
        }
        filter_level = level_map.get(request.degree_level.lower(), request.degree_level)
        query = query.filter(CourseDB.degree_level.ilike(f"%{filter_level}%"))

    if request.query and len(request.query.strip()) > 0:
        q = f"%{request.query.strip()}%"
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
