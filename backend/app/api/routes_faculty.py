import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.models.schema import FacultyMember
from app.models.db_models import FacultyDB
from app.core.database import get_db

router = APIRouter(prefix="/faculty", tags=["Faculty"])

def db_to_pydantic(db_model: FacultyDB) -> FacultyMember:
    eng_parts = [p for p in [db_model.first_name, db_model.last_name] if p]
    constructed_full_name = " ".join(eng_parts) if eng_parts else None

    return FacultyMember(
        id=db_model.id,
        university=db_model.university,
        university_th=db_model.university_th,
        faculty=db_model.faculty,
        faculty_th=db_model.faculty_th,
        department=db_model.department,
        department_th=db_model.department_th,
        academic_title_th=db_model.academic_title_th,
        first_name=db_model.first_name,
        last_name=db_model.last_name,
        full_name=constructed_full_name,
        full_name_th=db_model.full_name_th,
        role=db_model.role,
        email=db_model.email,
        image_url=db_model.image_url,
        profile_url=db_model.profile_url,
        education=db_model.education,
        research_interests=db_model.research_interests,
        taught_courses=db_model.taught_courses,
        featured_publications=[
            {"title": pub} if isinstance(pub, str) else pub 
            for pub in (db_model.featured_publications or [])
        ],
        scholar_url=db_model.scholar_url,
        embedding_text=db_model.embedding_text
    )

@router.get("/", response_model=List[FacultyMember])
def list_faculty(
    university: Optional[str] = Query(None, description="Filter by university"),
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all faculty members with optional filtering from PostgreSQL Database."""
    query = db.query(FacultyDB)
    
    if university:
        query = query.filter(FacultyDB.university.ilike(f"%{university}%") | FacultyDB.university_th.ilike(f"%{university}%"))
    if department:
        query = query.filter(FacultyDB.department.ilike(f"%{department}%") | FacultyDB.department_th.ilike(f"%{department}%"))
        
    db_faculties = query.limit(limit).all()
    return [db_to_pydantic(f) for f in db_faculties]


@router.get("/{faculty_id}", response_model=FacultyMember)
def get_faculty_profile(faculty_id: str, db: Session = Depends(get_db)):
    """Retrieve a specific faculty member by ID from PostgreSQL Database."""
    db_faculty = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    return db_to_pydantic(db_faculty)
