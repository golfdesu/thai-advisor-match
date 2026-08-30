from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.schema import CourseSchema
import re


class QuizAnswerItem(BaseModel):
    question_id: Any
    dimension: Optional[str] = None  # R, I, A, S, E, C or custom
    category: Optional[str] = None  # Location, Vibe, Budget, etc.
    value: Any  # Likert score (1-5), single string, array of strings
    label: Optional[str] = None  # Text of selected option
    text: Optional[str] = None  # Free text response


class CareerQuizSubmitRequest(BaseModel):
    tier: str = Field("standard", pattern=r"^(quick|standard|deep)$", description="'quick' (12 questions), 'standard' (24 questions), or 'deep' (50 questions)")
    answers: List[QuizAnswerItem] = Field(default_factory=list, max_length=100)
    free_text_answers: Dict[str, str] = Field(default_factory=dict)


class CareerRecommendation(BaseModel):
    title: str
    description: str
    match_percentage: int
    skills: List[str] = Field(default_factory=list)
    growth_outlook: str = "เติบโตสูง"

    @field_validator("match_percentage", mode="before")
    @classmethod
    def parse_match_percentage(cls, v: Any) -> int:
        if isinstance(v, (int, float)):
            return int(round(float(v)))
        if isinstance(v, str):
            clean = re.sub(r"[^\d.]", "", v)
            if clean:
                try:
                    return int(round(float(clean)))
                except ValueError:
                    pass
        return 90


class RiasecBreakdown(BaseModel):
    realistic: float = Field(0.0, description="R score percentage 0-100")
    investigative: float = Field(0.0, description="I score percentage 0-100")
    artistic: float = Field(0.0, description="A score percentage 0-100")
    social: float = Field(0.0, description="S score percentage 0-100")
    enterprising: float = Field(0.0, description="E score percentage 0-100")
    conventional: float = Field(0.0, description="C score percentage 0-100")


class CareerProfileResponse(BaseModel):
    tier: str
    archetype_title: str
    archetype_code: str  # e.g., "IAS (Investigative-Artistic-Social)"
    archetype_description: str
    riasec_scores: RiasecBreakdown
    personality_summary: str
    strengths: List[str] = Field(default_factory=list)
    ideal_work_environment: str
    campus_vibe_match: Optional[str] = None
    learning_style_match: Optional[str] = None
    lifestyle_highlights: List[str] = Field(default_factory=list)
    growth_advice: str
    share_quote: str
    top_careers: List[CareerRecommendation] = Field(default_factory=list)
    recommended_courses: List[CourseSchema] = Field(default_factory=list)
