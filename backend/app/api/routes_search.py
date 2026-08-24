from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schema import SearchRequest, SearchResponse, ColdEmailRequest, ColdEmailResponse
from app.models.db_models import FacultyDB
from app.api.routes_faculty import db_to_pydantic
from app.core.database import get_db
from app.core.embedding_service import embedding_service

router = APIRouter(prefix="/search", tags=["Semantic Search & Match"])


@router.post("/", response_model=SearchResponse)
def search_and_match_advisors(request: SearchRequest, db: Session = Depends(get_db)):
    """
    AI Semantic Search & Matching endpoint for graduate students.
    Matches prospective thesis topics against faculty research domains using PostgreSQL DB.
    """
    if not request.query or len(request.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must contain at least 2 characters")

    query = db.query(FacultyDB)
    if request.university:
        query = query.filter(FacultyDB.university.ilike(f"%{request.university}%") | FacultyDB.university_th.ilike(f"%{request.university}%"))
    if request.department:
        query = query.filter(FacultyDB.department.ilike(f"%{request.department}%") | FacultyDB.department_th.ilike(f"%{request.department}%"))

    db_faculties = query.all()
    faculty_list = [db_to_pydantic(f) for f in db_faculties]

    # Rank with hybrid semantic embedding / lexical matcher
    ranked_results = embedding_service.rank_faculty(
        query=request.query,
        faculty_list=faculty_list,
        top_k=request.top_k
    )

    return SearchResponse(
        query=request.query,
        total_matched=len(ranked_results),
        results=ranked_results
    )


@router.post("/cold-email", response_model=ColdEmailResponse)
def generate_cold_email(req: ColdEmailRequest, db: Session = Depends(get_db)):
    """
    AI Cold Email Generator: Draft a professional inquiry email for contacting an advisor.
    """
    db_faculty = db.query(FacultyDB).filter(FacultyDB.id == req.faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")
        
    target_faculty = db_to_pydantic(db_faculty)
    
    faculty_name = target_faculty.full_name_th if target_faculty else "อาจารย์ที่ปรึกษา"
    dept_name = target_faculty.department_th if target_faculty else "ภาควิชา"
    
    if req.language == "th":
        subject = f"ขอคำปรึกษาและแสดงความประสงค์เข้าศึกษาต่อระดับ{req.intended_degree} — {req.student_name}"
        body = f"""กราบเรียน {faculty_name} ที่เคารพ

กระผม/ดิฉัน {req.student_name} มีความประสงค์ที่จะเข้าศึกษาต่อในระดับ{req.intended_degree} {dept_name} 

เนื่องจากกระผม/ดิฉันได้ติดตามผลงานวิจัยของอาจารย์ โดยเฉพาะในด้าน {", ".join(target_faculty.research_interests[:2]) if target_faculty.research_interests else 'งานวิจัยของอาจารย์'} และมีความสนใจอย่างยิ่งที่จะทำวิทยานิพนธ์ในหัวข้อ "{req.research_topic}"

ประวัติการศึกษาและพื้นฐานเบื้องต้น:
{req.student_background}

กระผม/ดิฉันจึงใคร่ขออนุญาตเรียนปรึกษาความเป็นไปได้ในการเข้าเป็นนักศึกษาในความดูแลของอาจารย์ รวมถึงขอคำแนะนำเกี่ยวกับแนวทางการเตรียมตัวและการพัฒนาโครงร่างวิทยานิพนธ์ครับ/ค่ะ

ทั้งนี้ กระผม/ดิฉันได้แนบประวัติ (CV) และโครงร่างแนวคิดงานวิจัย (Research Proposal) มาพร้อมกับอีเมลฉบับนี้แล้วครับ/ค่ะ

ขอแสดงความนับถืออย่างสูง
{req.student_name}
"""
        tips = [
            "ควรแนบไฟล์ CV (PDF) และ Transcripts ทางการ",
            "ระบุความสนใจในผลงานวิจัยของอาจารย์อย่างเฉพาะเจาะจง",
            "ใช้อีเมลทางการและใช้ถ้อยคำสุภาพเรียบร้อย"
        ]
    else:
        subject = f"Inquiry regarding {req.intended_degree} Thesis Advising — {req.student_name}"
        body = f"""Dear {faculty_name},

My name is {req.student_name}, and I am writing to express my strong interest in pursuing a {req.intended_degree} under your supervision at {dept_name}.

I have reviewed your published research in {", ".join(target_faculty.research_interests[:2]) if target_faculty.research_interests else 'your research area'}, and I am particularly passionate about conducting research on "{req.research_topic}".

Brief Background:
{req.student_background}

I would be honored to discuss potential advising opportunities and would appreciate any guidance on the application process. I have attached my CV and a brief research concept note for your review.

Thank you very much for your time and consideration.

Sincerely,
{req.student_name}
"""
        tips = [
            "Attach a concise 1-2 page CV (PDF format)",
            "Be clear and specific about why this professor's lab is the best fit for your research goals",
            "Follow up politely after 7-10 business days if no reply"
        ]

    return ColdEmailResponse(
        subject=subject,
        body=body,
        tips=tips
    )
