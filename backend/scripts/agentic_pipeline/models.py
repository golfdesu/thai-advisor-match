"""
State & Patch Models for Autonomous Faculty Extraction Pipeline
Based on the SKILL.state Architecture & Evaluation: https://arxiv.org/html/2608.26263v2#S5
"""
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class RawFacultyProfile(BaseModel):
    """
    Compact & Compressed Faculty Profile schema for LLM structured output.
    Static metadata (university, faculty, canonical ID, confidence) are injected
    deterministically by the State Reducer in Python to save 40%+ Output Tokens.
    """
    full_name_th: str = Field(..., description="Full Thai name with title, e.g. 'ศ.ดร. บุญเสริม กิจศิริกุล'")
    academic_title_th: Optional[str] = Field(None, description="Thai title e.g. ศ.ดร., รศ.ดร., ผศ.ดร., อ.ดร.")
    first_name: Optional[str] = Field(None, description="English first name")
    last_name: Optional[str] = Field(None, description="English last name")
    email: Optional[str] = Field(None, description="Official university email")
    department_th: Optional[str] = Field(None, description="Department name in Thai if specified on page")
    image_url: Optional[str] = Field(None, description="Profile photo URL if present")
    profile_url: Optional[str] = Field(None, description="Personal profile URL if present")
    education: List[str] = Field(default_factory=list, description="Degrees and universities")
    research_interests: List[str] = Field(default_factory=list, description="Research areas/keywords")
    featured_publications: List[str] = Field(default_factory=list, description="Notable papers/publications")
    scholar_url: Optional[str] = Field(None, description="Google Scholar URL if present")


class ProfileFieldUpdate(BaseModel):
    scholar_url: Optional[str] = None
    featured_publications: List[str] = Field(default_factory=list)
    research_interests: List[str] = Field(default_factory=list)
    email: Optional[str] = None


class FacultyStatePatch(BaseModel):
    """
    Atomic State Patch emitted by the LLM on each extraction turn.
    Following the SKILL.state paradigm, LLMs output only deltas/patches instead of full state history.
    """
    discovered_urls: List[str] = Field(
        default_factory=list,
        description="Newly discovered faculty directory or detail URLs to explore"
    )
    new_profiles: List[RawFacultyProfile] = Field(
        default_factory=list,
        description="Newly extracted faculty profiles in this chunk"
    )
    updated_profile_fields: List[ProfileFieldUpdate] = Field(
        default_factory=list,
        description="Updates for existing profiles"
    )
    unreachable_or_empty_pages: List[str] = Field(
        default_factory=list,
        description="URLs that failed or contained no valid faculty data"
    )
    next_action_recommendation: Optional[str] = Field(
        None,
        description="Recommended next step, e.g., 'crawl_next_department', 'enrich_scholar', 'finalize'"
    )
    summary_of_changes: str = Field(
        "",
        description="Concise one-line summary of what was extracted in this step"
    )


class ExtractionAgentState(BaseModel):
    """
    Complete state representation of the Faculty Ingestion Agent.
    Maintained in-memory and updated deterministically by the State Reducer.
    """
    session_id: str = Field(..., description="Unique extraction session identifier")
    target_university_th: str = Field(..., description="Target university name in Thai")
    target_university_en: str = Field(..., description="Target university name in English")
    target_faculty_th: Optional[str] = Field(None, description="Target faculty in Thai")
    target_faculty_en: Optional[str] = Field(None, description="Target faculty in English")

    pending_urls: List[str] = Field(default_factory=list, description="FIFO queue of URLs to crawl")
    visited_urls: List[str] = Field(default_factory=list, description="Set/List of already processed URLs")
    failed_urls: List[str] = Field(default_factory=list, description="URLs that errored out")

    # Primary extracted dictionary keyed by normalized Faculty ID
    faculties: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Verified & normalized faculty records ready for database ingestion"
    )

    # Exact and fuzzy dedup indexes
    dedup_thai_names: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of cleaned Thai Name -> Faculty ID"
    )
    dedup_emails: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of lowercase email -> Faculty ID"
    )

    # Runtime & telemetry metrics
    step_count: int = Field(0, description="Number of extraction steps completed")
    total_tokens_used: int = Field(0, description="Cumulative tokens consumed")
    status: str = Field("initialized", description="'initialized', 'in_progress', 'completed', 'failed'")
    last_error: Optional[str] = None
