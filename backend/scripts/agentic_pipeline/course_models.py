"""
Course & Curriculum Models for SKILL.state Extraction Pipeline
Based on arXiv:2608.26263v2 & Tier-3 TCAS/TQF-2 Standardization
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RawCourseProfile(BaseModel):
    """
    Compact Course schema for LLM state patch generation.
    Static university/faculty metadata is populated deterministically by the CourseStateReducer.
    """
    title_th: str = Field(..., description="Full program name in Thai (e.g. 'วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์')")
    title_en: Optional[str] = Field(None, description="Full program name in English")
    degree_level: str = Field(..., description="ปริญญาตรี, ปริญญาโท, or ปริญญาเอก")
    degree_name: Optional[str] = Field(None, description="Official degree abbreviation e.g. วศ.บ., วท.บ., วศ.ม., ปร.ด.")
    department_th: Optional[str] = Field(None, description="Department name in Thai")
    department_en: Optional[str] = Field(None, description="Department name in English")
    program_type: Optional[str] = Field("ภาคปกติ", description="ภาคปกติ, ภาคพิเศษ, หรือ นานาชาติ")
    duration_years: Optional[str] = Field("4 ปี", description="Study duration e.g. 4 ปี, 2 ปี, 3 ปี")
    total_credits: Optional[str] = Field(None, description="Total credits required e.g. 136 หน่วยกิต")
    tuition_per_semester: Optional[str] = Field(None, description="Tuition fee per semester e.g. 21,000 บาท")
    tuition_total: Optional[str] = Field(None, description="Total estimated tuition fee")
    description: Optional[str] = Field(None, description="Curriculum description & learning objectives")
    curriculum_highlights: List[str] = Field(default_factory=list, description="Core topics, specialized tracks or highlights")
    career_paths: List[str] = Field(default_factory=list, description="Target career occupations")
    tags: List[str] = Field(default_factory=list, description="Subject taxonomy tags e.g. AI, CyberSecurity, IoT")
    website_url: Optional[str] = Field(None, description="Official curriculum URL")


class CourseStatePatch(BaseModel):
    """
    Atomic State Patch emitted by LLM for Course extraction turns.
    Following SKILL.state, only new items and discovered URLs are emitted.
    """
    discovered_urls: List[str] = Field(default_factory=list, description="Newly discovered curriculum links")
    new_courses: List[RawCourseProfile] = Field(default_factory=list, description="Extracted course programs")
    unreachable_or_empty_pages: List[str] = Field(default_factory=list, description="Failed URLs")
    summary_of_changes: str = Field("", description="Summary of extracted programs")


class CourseAgentState(BaseModel):
    """
    Full in-memory state of the Course Extraction session.
    Persisted to disk checkpointing after every turn.
    """
    session_id: str = Field(..., description="Unique extraction session identifier")
    target_university_th: str = Field(...)
    target_university_en: str = Field(...)
    target_faculty_th: Optional[str] = None
    target_faculty_en: Optional[str] = None

    pending_urls: List[str] = Field(default_factory=list)
    visited_urls: List[str] = Field(default_factory=list)
    failed_urls: List[str] = Field(default_factory=list)

    courses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    dedup_title_keys: Dict[str, str] = Field(default_factory=dict)

    step_count: int = Field(0)
    total_tokens_used: int = Field(0)
    status: str = Field("initialized")
    last_error: Optional[str] = None
