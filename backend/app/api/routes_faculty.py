import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Response
from sqlalchemy.orm import Session, defer, load_only
from app.models.schema import FacultyMember, FacultyCardSchema
from app.models.db_models import FacultyDB
from app.core.database import get_db

router = APIRouter(prefix="/faculty", tags=["Faculty"])

# Egress budget: list/card payloads must skip heavy columns server-side so
# Supabase never ships education / pubs / embedding_text for card rendering.
_FACULTY_CARD_COLUMNS = (
    FacultyDB.id,
    FacultyDB.university, FacultyDB.university_th,
    FacultyDB.faculty, FacultyDB.faculty_th,
    FacultyDB.department, FacultyDB.department_th,
    FacultyDB.academic_title_th,
    FacultyDB.first_name, FacultyDB.last_name, FacultyDB.full_name_th,
    FacultyDB.role, FacultyDB.image_url,
    FacultyDB.research_interests,
    FacultyDB.total_publications_count,
    FacultyDB.first_author_count, FacultyDB.co_author_count,
    FacultyDB.scholar_url,
)

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
        total_publications_count=getattr(db_model, "total_publications_count", 0) or 0,
        first_author_count=getattr(db_model, "first_author_count", 0) or 0,
        co_author_count=getattr(db_model, "co_author_count", 0) or 0,
        total_citations=getattr(db_model, "total_citations", 0) or 0,
        h_index=getattr(db_model, "h_index", 0) or 0,
        openalex_id=getattr(db_model, "openalex_id", None),
        scholar_url=db_model.scholar_url,
        # embedding_text intentionally NOT read here (perf audit 2026-09-10):
        # every /search candidate row defers that column, so touching it in the
        # converter fired one extra SELECT per result (N+1) and shipped ~1 KB/row
        # of internal index text the UI never renders.
    )


def db_to_card(db_model: FacultyDB) -> FacultyCardSchema:
    """Slim converter — only touches columns in _FACULTY_CARD_COLUMNS (never deferred attrs)."""
    eng_parts = [p for p in [db_model.first_name, db_model.last_name] if p]
    constructed_full_name = " ".join(eng_parts) if eng_parts else None

    return FacultyCardSchema(
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
        image_url=db_model.image_url,
        scholar_url=db_model.scholar_url,
        research_interests=list(db_model.research_interests or [])[:5],
        total_publications_count=db_model.total_publications_count or 0,
        first_author_count=db_model.first_author_count or 0,
        co_author_count=db_model.co_author_count or 0,
    )

@router.get("/", response_model=List[FacultyCardSchema])
def list_faculty(
    university: Optional[str] = Query(None, description="Filter by university"),
    department: Optional[str] = Query(None, description="Filter by department"),
    faculty: Optional[str] = Query(None, description="Filter by faculty/school"),
    limit: int = Query(24, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Retrieve faculty card list (slim payload). Use GET /faculty/{id} for full profile."""
    query = db.query(FacultyDB).options(load_only(*_FACULTY_CARD_COLUMNS))

    if university and university.strip() and university.strip().lower() != "all":
        u_clean = university.strip()
        query = query.filter(FacultyDB.university.ilike(f"%{u_clean}%") | FacultyDB.university_th.ilike(f"%{u_clean}%"))
    if faculty and faculty.strip() and faculty.strip().lower() != "all":
        f_clean = faculty.strip()
        query = query.filter(FacultyDB.faculty.ilike(f"%{f_clean}%") | FacultyDB.faculty_th.ilike(f"%{f_clean}%"))
    if department and department.strip() and department.strip().lower() != "all":
        d_clean = department.strip()
        query = query.filter(FacultyDB.department.ilike(f"%{d_clean}%") | FacultyDB.department_th.ilike(f"%{d_clean}%"))

    db_faculties = query.limit(limit).all()
    return [db_to_card(f) for f in db_faculties]


@router.get("/{faculty_id}", response_model=FacultyMember)
def get_faculty_profile(faculty_id: str, response: Response, db: Session = Depends(get_db)):
    """Retrieve a specific faculty member by ID from PostgreSQL Database."""
    db_faculty = db.query(FacultyDB).options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text)).filter(FacultyDB.id == faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
    response.headers["Cache-Control"] = "public, max-age=600"
    return db_to_pydantic(db_faculty)
