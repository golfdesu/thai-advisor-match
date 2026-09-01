from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, defer
from sqlalchemy import or_, text
from typing import List, Optional
from app.models.schema import (
    ResearchLab,
    LabSearchRequest,
    LabSearchResponse,
    LabInquiryRequest,
    LabInquiryResponse,
    FacultyMember
)
from app.models.db_models import ResearchLabDB, FacultyDB
from app.api.routes_faculty import db_to_pydantic
from app.core.database import get_db
from app.core.embedding_service import embedding_service
from app.core.security import sanitize_for_prompt

router = APIRouter(prefix="/labs", tags=["Research Labs & Centers of Excellence"])


def db_lab_to_pydantic(db_lab: ResearchLabDB, db: Optional[Session] = None, match_score: float = 95.0) -> ResearchLab:
    lead_adv = None
    member_facs = []

    if db and db_lab.lead_advisor_id:
        f_db = db.query(FacultyDB).options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text)).filter_by(id=db_lab.lead_advisor_id).first()
        if f_db:
            lead_adv = db_to_pydantic(f_db)

    if db and db_lab.member_faculty_ids:
        mem_ids = [fid for fid in db_lab.member_faculty_ids if fid != db_lab.lead_advisor_id]
        if mem_ids:
            mem_dbs = db.query(FacultyDB).options(defer(FacultyDB.embedding), defer(FacultyDB.embedding_text)).filter(FacultyDB.id.in_(mem_ids)).all()
            member_facs = [db_to_pydantic(f) for f in mem_dbs]

    synergy_badges = []
    if db_lab.open_positions:
        synergy_badges.append(f"🟢 มีทุนวิจัย/เปิดรับนักศึกษา ({len(db_lab.open_positions)} ตำแหน่ง)")
    if db_lab.flagship_equipment:
        synergy_badges.append("🔬 เครื่องมือวิจัยระดับสากล")
    if db_lab.industry_partners:
        synergy_badges.append("🤝 มีเครือข่ายพันธมิตรภาคอุตสาหกรรม")

    return ResearchLab(
        id=db_lab.id,
        name_th=db_lab.name_th,
        name_en=db_lab.name_en,
        university=db_lab.university,
        university_th=db_lab.university_th,
        faculty=db_lab.faculty,
        faculty_th=db_lab.faculty_th,
        department=db_lab.department,
        department_th=db_lab.department_th,
        lead_advisor_id=db_lab.lead_advisor_id,
        lead_advisor=lead_adv,
        member_faculty_ids=db_lab.member_faculty_ids or [],
        member_faculties=member_facs,
        description=db_lab.description,
        research_domains=db_lab.research_domains or [],
        flagship_equipment=db_lab.flagship_equipment or [],
        industry_partners=db_lab.industry_partners or [],
        open_positions=db_lab.open_positions or [],
        website_url=db_lab.website_url,
        image_url=db_lab.image_url,
        match_score=match_score,
        synergy_badges=synergy_badges
    )


@router.get("/", response_model=List[ResearchLab])
def list_labs(
    university: Optional[str] = Query(None, description="Filter by university name"),
    faculty: Optional[str] = Query(None, description="Filter by faculty/school"),
    domain: Optional[str] = Query(None, description="Filter by research domain"),
    search: Optional[str] = Query(None, description="Keyword search in lab name/domains"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all Research Labs with optional filtering."""
    query = db.query(ResearchLabDB).options(defer(ResearchLabDB.embedding), defer(ResearchLabDB.embedding_text))

    if university and university.strip() and university.strip().lower() != "all":
        u_clean = university.strip()
        query = query.filter(or_(
            ResearchLabDB.university.ilike(f"%{u_clean}%"),
            ResearchLabDB.university_th.ilike(f"%{u_clean}%")
        ))
    if faculty and faculty.strip() and faculty.strip().lower() != "all":
        f_clean = faculty.strip()
        query = query.filter(or_(
            ResearchLabDB.faculty.ilike(f"%{f_clean}%"),
            ResearchLabDB.faculty_th.ilike(f"%{f_clean}%")
        ))
    if search and search.strip():
        s_clean = search.strip()
        query = query.filter(or_(
            ResearchLabDB.name_th.ilike(f"%{s_clean}%"),
            ResearchLabDB.name_en.ilike(f"%{s_clean}%"),
            ResearchLabDB.description.ilike(f"%{s_clean}%")
        ))

    db_labs = query.limit(limit).all()
    return [db_lab_to_pydantic(lab, db=db) for lab in db_labs]


@router.get("/{lab_id}", response_model=ResearchLab)
def get_lab_detail(lab_id: str, db: Session = Depends(get_db)):
    """Retrieve single lab detail with resolved PIs and faculty members."""
    db_lab = db.query(ResearchLabDB).options(defer(ResearchLabDB.embedding), defer(ResearchLabDB.embedding_text)).filter(ResearchLabDB.id == lab_id).first()
    if not db_lab:
        raise HTTPException(status_code=404, detail="Research Lab not found")
    return db_lab_to_pydantic(db_lab, db=db)


@router.post("/search", response_model=LabSearchResponse)
def search_labs(req: LabSearchRequest, db: Session = Depends(get_db)):
    """AI Semantic Vector Search for Research Labs matching research proposals."""
    query_text = (req.query or "").strip()

    if not query_text:
        labs = list_labs(university=req.university, faculty=req.faculty, domain=req.domain, limit=req.top_k, db=db)
        return LabSearchResponse(query="", total_matched=len(labs), results=labs)

    # 1. Generate query embedding
    query_vector = embedding_service.get_embedding(query_text)

    # 2. Vector search via pgvector Cosine Distance
    if query_vector:
        try:
            filters = []
            if req.university and req.university.strip() and req.university.strip().lower() != "all":
                u_clean = req.university.strip()
                filters.append(f"(university ILIKE '%{u_clean}%' OR university_th ILIKE '%{u_clean}%')")
            if req.faculty and req.faculty.strip() and req.faculty.strip().lower() != "all":
                f_clean = req.faculty.strip()
                filters.append(f"(faculty ILIKE '%{f_clean}%' OR faculty_th ILIKE '%{f_clean}%')")

            where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

            raw_sql = f"""
                SELECT id, 1 - (embedding <=> :vec) AS similarity
                FROM research_labs
                {where_clause}
                ORDER BY embedding <=> :vec
                LIMIT :limit
            """
            rows = db.execute(text(raw_sql), {"vec": str(query_vector), "limit": req.top_k}).fetchall()

            lab_ids = [r.id for r in rows]
            scores_map = {r.id: round(max(50.0, min(99.0, float(r.similarity) * 100)), 1) for r in rows}

            if lab_ids:
                db_labs = db.query(ResearchLabDB).options(defer(ResearchLabDB.embedding), defer(ResearchLabDB.embedding_text)).filter(ResearchLabDB.id.in_(lab_ids)).all()
                # Maintain rank order
                db_labs_dict = {lab.id: lab for lab in db_labs}
                ordered_labs = [db_labs_dict[lid] for lid in lab_ids if lid in db_labs_dict]

                results = []
                for lab in ordered_labs:
                    score = scores_map.get(lab.id, 85.0)
                    pydantic_lab = db_lab_to_pydantic(lab, db=db, match_score=score)

                    # Generate smart contextual explanation
                    domains_str = ", ".join(pydantic_lab.research_domains[:3])
                    pydantic_lab.ai_explanation = f"ห้องปฏิบัติการนี้มุ่งเน้นงานวิจัยด้าน {domains_str} ซึ่งสอดคล้องกับแนวคิดวิจัย '{query_text[:50]}' พร้อมเครื่องมือวิจัยและทุนสนับสนุน"
                    results.append(pydantic_lab)

                return LabSearchResponse(query=query_text, total_matched=len(results), results=results)
        except Exception as e:
            print("Lab vector search fallback error:", e)

    # Lexical fallback
    search_pattern = f"%{query_text}%"
    db_labs = db.query(ResearchLabDB).options(defer(ResearchLabDB.embedding), defer(ResearchLabDB.embedding_text)).filter(
        or_(
            ResearchLabDB.name_th.ilike(search_pattern),
            ResearchLabDB.name_en.ilike(search_pattern),
            ResearchLabDB.description.ilike(search_pattern)
        )
    ).limit(req.top_k).all()

    results = [db_lab_to_pydantic(lab, db=db, match_score=88.0) for lab in db_labs]
    return LabSearchResponse(query=query_text, total_matched=len(results), results=results)


@router.post("/inquiry", response_model=LabInquiryResponse)
def generate_lab_inquiry(req: LabInquiryRequest, db: Session = Depends(get_db)):
    """Generate a high-impact inquiry letter to join a Research Lab or apply for a Research Assistantship (RA)."""
    db_lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == req.lab_id).first()
    if not db_lab:
        raise HTTPException(status_code=404, detail="Research Lab not found")

    lab_pydantic = db_lab_to_pydantic(db_lab, db=db)
    lead_name = lab_pydantic.lead_advisor.full_name_th if lab_pydantic.lead_advisor else f"ผู้อำนวยการ {lab_pydantic.name_th}"

    student_name = sanitize_for_prompt(req.student_name)
    background = sanitize_for_prompt(req.student_background)
    proposal = sanitize_for_prompt(req.research_proposal)

    if req.language == "th":
        subject = f"ขอแสดงความจำนงสมัครเข้าร่วมวิจัยในห้องปฏิบัติการ {db_lab.name_th} ({req.intended_degree}) - {student_name}"
        body = f"""เรียน {lead_name} และคณาจารย์ประจำห้องปฏิบัติการ {db_lab.name_th}

กระผม/ดิฉัน {student_name} มีความประสงค์จะสมัครเข้าศึกษาต่อในระดับ {req.intended_degree} ณ {db_lab.university_th} และมีความสนใจอย่างยิ่งที่จะขอเข้าร่วมทำวิจัยในห้องปฏิบัติการ {db_lab.name_th} ({db_lab.name_en}) ภายใต้การดูแลของท่าน

จากการติดตามผลงานวิจัยของห้องปฏิบัติการ โดยเฉพาะในด้าน {", ".join(db_lab.research_domains[:3])} กระผม/ดิฉันเล็งเห็นว่าทิศทางวิจัยของห้องปฏิบัติการมีความล้ำสมัยและตรงกับเป้าหมายทางวิชาการของกระผม/ดิฉันอย่างยิ่ง

ประวัติและพื้นฐานการศึกษาโดยย่อ:
{background}

แนวคิดและข้อเสนอโครงการวิจัยที่ประสงค์จะพัฒนา:
{proposal}

ด้วยความพร้อมด้านเครื่องมือวิจัยและบรรยากาศทางวิชาการของห้องปฏิบัติการ กระผม/ดิฉันมีความตั้งใจจริงที่จะทุ่มเทเพื่อสร้างสรรค์ผลงานตีพิมพ์และนวัตกรรมที่มีผลกระทบสูง (High Impact) จึงใคร่ขอความอนุเคราะห์เข้าพบเพื่อขอรับคำปรึกษา แนะนำแนวทางการทำวิจัย หรือสมัครรับทุนผู้ช่วยวิจัย (Research Assistant) ของห้องปฏิบัติการ

ทั้งนี้ กระผม/ดิฉันได้แนบประวัติการศึกษา (CV) และเอกสารแสดงผลการเรียนมาพร้อมกับอีเมลฉบับนี้ด้วยแล้ว

ขอแสดงความนับถืออย่างยิ่ง

{student_name}
อีเมลติดต่อ: [ใส่อีเมลทางการของคุณ]"""
        tips = [
            "แนบไฟล์ CV/Resume และ Transcript ฉบับล่าสุดเป็น PDF",
            "ระบุชัดเจนว่าสามารถเริ่มเข้าแล็บได้ตั้งแต่ช่วงเดือนใด",
            "หากมีผลงานโปรเจกต์เดิม หรือ GitHub/Portfolio ให้แนบลิงก์ไปด้วยเพื่อเพิ่มโอกาสการตอบรับ"
        ]
    else:
        subject = f"Prospective Research Inquiries & RA Application: {db_lab.name_en} ({req.intended_degree}) - {student_name}"
        body = f"""Dear Director & Research Team of {db_lab.name_en},

My name is {student_name}, and I am writing to express my strong interest in joining the {db_lab.name_en} at {db_lab.university} as a prospective {req.intended_degree} student and Research Assistant.

I have been closely following your groundbreaking research in {", ".join(db_lab.research_domains[:3])}. My academic background and research vision align closely with the ongoing projects in your laboratory.

Academic Background:
{background}

Proposed Research Focus:
{proposal}

I am eager to contribute to your laboratory's ongoing initiatives and would be deeply grateful for the opportunity to discuss prospective research projects or research assistantship opportunities.

Please find my Curriculum Vitae (CV) and academic transcripts attached for your review.

Sincerely,

{student_name}
Email: [Your Official Email]"""
        tips = [
            "Attach your latest CV and academic transcripts in PDF format",
            "Highlight prior publications, coding repositories, or hardware prototypes",
            "State your expected enrollment term clearly"
        ]

    return LabInquiryResponse(subject=subject, body=body, tips=tips)
