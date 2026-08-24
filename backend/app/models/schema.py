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
    query: str = Field(..., description="Research topic, abstract, or keywords from prospective student")
    university: Optional[str] = Field(None, description="Filter by university name (TH or EN)")
    faculty: Optional[str] = Field(None, description="Filter by faculty name (TH or EN)")
    department: Optional[str] = Field(None, description="Filter by department name (TH or EN)")
    top_k: int = Field(10, ge=1, le=50, description="Number of results to return")


class SearchMatchResult(BaseModel):
    faculty: FacultyMember
    match_score: float = Field(..., description="Match percentage score between 0 and 100")
    ai_explanation: Optional[str] = Field(None, description="AI-generated explanation of why this advisor matches")
    matched_keywords: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    total_matched: int
    results: List[SearchMatchResult]


class ColdEmailRequest(BaseModel):
    faculty_id: str
    student_name: str
    student_background: str
    research_topic: str
    intended_degree: str = Field("Master's Degree", description="Master's Degree or Ph.D.")
    language: str = Field("th", description="'th' for Thai or 'en' for English")


class ColdEmailResponse(BaseModel):
    subject: str
    body: str
    tips: List[str] = Field(default_factory=list)
