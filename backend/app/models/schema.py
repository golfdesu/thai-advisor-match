from typing import List, Optional
import re
from pydantic import BaseModel, Field, model_validator, field_validator

# ---------------------------------------------------------------------------
# Academic-title normalization (display-layer guard)
# ---------------------------------------------------------------------------
# Legacy ingestion rows often store the academic title redundantly inside
# full_name_th (e.g. academic_title_th='ศ.ดร.' + full_name_th='ศ.ดร. สุทธิเขตต์').
# Rendering layers prepend academic_title_th, producing 'ศ.ดร.ศ.ดร. สุทธิเขตต์'.
# These helpers strip duplicated title prefixes at the DTO boundary so every
# API consumer (cards and detail pages) gets a clean display name.
_TITLE_CANON_PATTERNS = [
    # canonical form -> regex variants (longest / most-specific first)
    # Explicit boundary check: Require dot or whitespace so Thai names starting
    # with "ดร" (e.g. ดรุณี, ดรัลพร) are never stripped.
    ("ศ.ดร.", [r"ศาสตราจารย์\s*ดร(\.|\s+|$)", r"ศ\.\s*ดร(\.|\s+|$)", r"Prof(?:\.|\b)\s*Dr(?:\.|\b)"]),
    ("รศ.ดร.", [r"รอง\s*ศาสตราจารย์\s*ดร(\.|\s+|$)", r"รศ\.\s*ดร(\.|\s+|$)", r"Assoc(?:\.|\b)\s*Prof(?:\.|\b)\s*Dr(?:\.|\b)"]),
    ("ผศ.ดร.", [r"ผู้ช่วย\s*ศาสตราจารย์\s*ดร(\.|\s+|$)", r"ผศ\.\s*ดร(\.|\s+|$)", r"Asst(?:\.|\b)\s*Prof(?:\.|\b)\s*Dr(?:\.|\b)"]),
    ("อ.ดร.", [r"อาจารย์\s*ดร(\.|\s+|$)", r"อ\.\s*ดร(\.|\s+|$)", r"Lect(?:\.|\b)\s*Dr(?:\.|\b)"]),
    ("ดร.", [r"ดร\.", r"ดร\s+", r"Dr(?:\.|\b)"]),
    ("ศ.", [r"ศาสตราจารย์(\s+|$)", r"ศ\."]),
    ("รศ.", [r"รอง\s*ศาสตราจารย์(\s+|$)", r"รศ\."]),
    ("ผศ.", [r"ผู้ช่วย\s*ศาสตราจารย์(\s+|$)", r"ผศ\."]),
    ("อ.", [r"อาจารย์(\s+|$)", r"อ\."]),
]
_COMPILED_TITLES = [
    (canon, re.compile(p)) for canon, pats in _TITLE_CANON_PATTERNS for p in pats
]

def _canonical_title(text: str) -> Optional[str]:
    t = text.strip()
    for canon, pat in _COMPILED_TITLES:
        if pat.fullmatch(t):
            return canon
    return None

def _strip_leading_title_tokens(name: str, max_strips: int = 3) -> str:
    """Repeatedly remove academic-title tokens at the start of a name.
    Handles stacked prefixes like 'ศ.ดร.ศ.ดร.' or 'รองศาสตราจารย์ ดร.'."""
    out = name.strip()
    for _ in range(max_strips):
        stripped = None
        for _canon, pat in _COMPILED_TITLES:
            m = pat.match(out)
            if m:
                candidate = out[m.end():].lstrip(" .").strip()
                if candidate:
                    stripped = candidate
                break
        if stripped is None:
            break
        out = stripped
    return out or name.strip()

def _has_duplicate_leading_title(name: str) -> bool:
    first = None
    for canon, pat in _COMPILED_TITLES:
        m = pat.match(name)
        if m:
            first = (canon, m)
            break
    if not first:
        return False
    rest = name[first[1].end():].lstrip(" .")
    for canon, pat in _COMPILED_TITLES:
        m = pat.match(rest)
        if m:
            return canon == first[0]
    return False

def _clean_display_name(title: Optional[str], full_name_th: Optional[str]) -> Optional[str]:
    """Return full_name_th without a duplicated leading academic title.

    - If academic_title_th exists, strip every leading title token from the
      name (the renderer re-adds the single canonical title anyway).
    - If no title is available, collapse duplicated leading title tokens to
      one canonical token (e.g. 'ดร.ดร. พรชัย' -> 'ดร. พรชัย') so the name
      stays self-contained without losing the title information.
    """
    if not full_name_th:
        return full_name_th
    name = full_name_th.strip()
    if (title or "").strip():
        cleaned = _strip_leading_title_tokens(name, 3)
        return cleaned
    # no title available: collapse duplicated title tokens, keep one
    for canon, pat in _COMPILED_TITLES:
        m = pat.match(name)
        if not m:
            continue
        rest_raw = name[m.end():].lstrip(" .")
        if not rest_raw:
            return name
        rest = _strip_leading_title_tokens(rest_raw, 2)
        return f"{canon} {rest}" if rest and rest != rest_raw else name
    return name


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
    total_publications_count: Optional[int] = Field(0, description="Total verified papers authored/co-authored")
    first_author_count: Optional[int] = Field(0, description="Papers authored as first/primary author")
    co_author_count: Optional[int] = Field(0, description="Papers authored as co-author")
    total_citations: Optional[int] = Field(0, description="Total academic citations across works")
    h_index: Optional[int] = Field(0, description="h-index metric")
    openalex_id: Optional[str] = None
    scholar_url: Optional[str] = None
    embedding_text: Optional[str] = None

    @field_validator("education", "research_interests", "taught_courses", "featured_publications", mode="before")
    @classmethod
    def _coerce_none_to_list(cls, v):
        return v if v is not None else []

    @model_validator(mode="after")
    def _dedupe_title_in_name(self) -> "FacultyMember":
        cleaned = _clean_display_name(self.academic_title_th, self.full_name_th)
        if cleaned:
            self.full_name_th = cleaned
        return self


class FacultyCardSchema(BaseModel):
    """
    Egress-optimized slim DTO for list / card / search-result rendering.

    Drops heavy columns (education, taught_courses, featured_publications,
    citations, embedding_text) that list views never display — detail pages
    fetch the full FacultyMember via GET /faculty/{id} instead.
    Converters MUST NOT touch deferred attributes to avoid per-row lazy-load N+1.
    """
    id: str = Field(..., description="Unique ID e.g. cmu_eng_ee_014")
    university: str = Field(..., description="University name in English")
    university_th: str = Field(..., description="University name in Thai")
    faculty: str = Field(..., description="Faculty / School name in English")
    faculty_th: str = Field(..., description="Faculty / School name in Thai")
    department: str = Field(..., description="Department name in English")
    department_th: str = Field(..., description="Department name in Thai")

    academic_title_th: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    full_name_th: str = Field(..., description="Full name in Thai with title")

    role: Optional[str] = None
    image_url: Optional[str] = None
    scholar_url: Optional[str] = None

    research_interests: List[str] = Field(default_factory=list, description="Trimmed to top 5")
    total_publications_count: Optional[int] = Field(0)
    first_author_count: Optional[int] = Field(0)
    co_author_count: Optional[int] = Field(0)

    @field_validator("research_interests", mode="before")
    @classmethod
    def _coerce_interests(cls, v):
        return v if v is not None else []

    @model_validator(mode="after")
    def _dedupe_title_in_name(self) -> "FacultyCardSchema":
        cleaned = _clean_display_name(self.academic_title_th, self.full_name_th)
        if cleaned:
            self.full_name_th = cleaned
        return self


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

    @field_validator("curriculum_highlights", "career_paths", "tags", mode="before")
    @classmethod
    def _coerce_course_lists(cls, v):
        return v if v is not None else []


class CourseCardSchema(BaseModel):
    """
    Egress-optimized slim DTO for course list / card / comparison rendering.

    Drops heavy columns (description, tags, tuition_total, embedding_text) and
    trims long arrays. Detail modal fetches the full CourseSchema via
    GET /courses/{course_id} when the user opens it.
    Converters MUST NOT touch deferred attributes to avoid per-row lazy-load N+1.
    """
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
    curriculum_highlights: List[str] = Field(default_factory=list, description="Trimmed to top 3")
    career_paths: List[str] = Field(default_factory=list, description="Trimmed to top 4")
    website_url: Optional[str] = None
    match_score: Optional[float] = 95.0

    @field_validator("curriculum_highlights", "career_paths", mode="before")
    @classmethod
    def _coerce_course_card_lists(cls, v):
        return v if v is not None else []


class CourseSearchRequest(BaseModel):
    query: Optional[str] = Field("", max_length=500)
    university: Optional[str] = Field(None, max_length=150)
    degree_level: Optional[str] = Field(None, max_length=50)
    faculty: Optional[str] = Field(None, max_length=150)
    top_k: int = Field(20, ge=1, le=50)


class CourseSearchResponse(BaseModel):
    query: str
    total_matched: int
    results: List[CourseCardSchema]


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

    @field_validator(
        "member_faculty_ids",
        "member_faculties",
        "research_domains",
        "flagship_equipment",
        "industry_partners",
        "open_positions",
        "synergy_badges",
        mode="before"
    )
    @classmethod
    def _coerce_lab_lists(cls, v):
        return v if v is not None else []


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

