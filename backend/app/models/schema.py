from typing import List, Optional
from pydantic import BaseModel, Field


class Publication(BaseModel):
    title: str
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    citation_count: Optional[int] = 0


class FacultyMember(BaseModel):
    id: str = Field(..., description="Unique ID e.g. cmu_eng_ee_014")
    university: str = Field(..., description="University name in English")
    university_th: str = Field(..., description="University name in Thai")
    faculty: str = Field(..., description="Faculty / School name in English")
    faculty_th: str = Field(..., description="Faculty / School name in Thai")
    department: str = Field(..., description="Department name in English")
    department_th: str = Field(..., description="Department name in Thai")
    
    academic_title: Optional[str] = None
    academic_title_th: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    full_name_th: str = Field(..., description="Full name in Thai with title")
    
    role: Optional[str] = None
    email: Optional[str] = None
    image_url: Optional[str] = None
    profile_url: Optional[str] = None
    
    education: List[str] = Field(default_factory=list)
    research_interests: List[str] = Field(default_factory=list)
    taught_courses: List[str] = Field(default_factory=list)
    featured_publications: List[Publication] = Field(default_factory=list)
    scholar_url: Optional[str] = None
    embedding_text: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Research topic, abstract, or keywords from prospective student")
    university: Optional[str] = Field(None, max_length=150, description="Filter by university name (TH or EN)")
    faculty: Optional[str] = Field(None, max_length=150, description="Filter by faculty name (TH or EN)")
    department: Optional[str] = Field(None, max_length=150, description="Filter by department name (TH or EN)")
    top_k: int = Field(10, ge=1, le=50, description="Number of results to return")


class SearchMatchResult(BaseModel):
    faculty: FacultyMember
    match_score: float = Field(..., ge=0.0, le=100.0, description="Match percentage score between 0 and 100")
    ai_explanation: Optional[str] = Field(None, max_length=1000, description="AI-generated explanation of why this advisor matches")
    matched_keywords: List[str] = Field(default_factory=list)
    matching_publications: List[str] = Field(default_factory=list, description="Specific publication titles matching the query")
    synergy_badges: List[str] = Field(default_factory=list, description="Badges indicating match strength e.g. Direct Focus, Active Papers")
    suggested_thesis_angles: List[str] = Field(default_factory=list, description="Suggested research angles connecting student & advisor")


class SearchResponse(BaseModel):
    query: str
    total_matched: int
    results: List[SearchMatchResult]


class ColdEmailRequest(BaseModel):
    faculty_id: str = Field(..., min_length=2, max_length=100)
    student_name: str = Field(..., min_length=1, max_length=100)
    student_background: str = Field(..., min_length=2, max_length=1500)
    research_topic: str = Field(..., min_length=2, max_length=1500)
    intended_degree: str = Field("Master's Degree", max_length=50, description="Master's Degree or Ph.D.")
    language: str = Field("th", pattern=r"^(th|en)$", description="'th' for Thai or 'en' for English")


class ColdEmailResponse(BaseModel):
    subject: str
    body: str
    tips: List[str] = Field(default_factory=list)


class CourseSchema(BaseModel):
    id: str
    title_th: str
    title_en: Optional[str] = None
    degree_level: str
    degree_name: Optional[str] = None
    university: str
    university_th: str
    faculty: str
    faculty_th: str
    department: Optional[str] = None
    department_th: Optional[str] = None
    program_type: Optional[str] = "ภาคปกติ"
    duration_years: Optional[str] = None
    total_credits: Optional[str] = None
    tuition_per_semester: Optional[str] = None
    tuition_total: Optional[str] = None
    description: Optional[str] = None
    curriculum_highlights: List[str] = Field(default_factory=list)
    career_paths: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    website_url: Optional[str] = None
    match_score: Optional[float] = 95.0


class CourseSearchRequest(BaseModel):
    query: Optional[str] = Field("", max_length=500)
    university: Optional[str] = Field(None, max_length=150)
    degree_level: Optional[str] = Field(None, max_length=50)
    faculty: Optional[str] = Field(None, max_length=150)
    top_k: int = Field(20, ge=1, le=50)


class CourseSearchResponse(BaseModel):
    query: str
    total_matched: int
    results: List[CourseSchema]


class ResearchLab(BaseModel):
    id: str = Field(..., description="Unique Lab ID e.g. kmutt_fibo_robotics_lab")
    name_th: str
    name_en: str
    university: str
    university_th: str
    faculty: str
    faculty_th: str
    department: Optional[str] = None
    department_th: Optional[str] = None

    lead_advisor_id: Optional[str] = None
    lead_advisor: Optional[FacultyMember] = None
    member_faculty_ids: List[str] = Field(default_factory=list)
    member_faculties: List[FacultyMember] = Field(default_factory=list)

    description: Optional[str] = None
    research_domains: List[str] = Field(default_factory=list)
    flagship_equipment: List[str] = Field(default_factory=list)
    industry_partners: List[str] = Field(default_factory=list)
    open_positions: List[str] = Field(default_factory=list)

    website_url: Optional[str] = None
    image_url: Optional[str] = None
    match_score: Optional[float] = 95.0
    ai_explanation: Optional[str] = None
    synergy_badges: List[str] = Field(default_factory=list)


class LabSearchRequest(BaseModel):
    query: Optional[str] = Field("", max_length=500)
    university: Optional[str] = Field(None, max_length=150)
    faculty: Optional[str] = Field(None, max_length=150)
    domain: Optional[str] = Field(None, max_length=150)
    top_k: int = Field(20, ge=1, le=50)


class LabSearchResponse(BaseModel):
    query: str
    total_matched: int
    results: List[ResearchLab]


class LabInquiryRequest(BaseModel):
    lab_id: str = Field(..., min_length=2, max_length=100)
    student_name: str = Field(..., min_length=1, max_length=100)
    student_background: str = Field(..., min_length=2, max_length=1500)
    research_proposal: str = Field(..., min_length=2, max_length=1500)
    intended_degree: str = Field("Master's Degree", max_length=50)
    inquiry_type: str = Field("ra_assistantship", description="ra_assistantship, lab_visit, or joint_project")
    language: str = Field("th", pattern=r"^(th|en)$")


class LabInquiryResponse(BaseModel):
    subject: str
    body: str
    tips: List[str] = Field(default_factory=list)

