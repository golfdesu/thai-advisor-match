from datetime import datetime
from sqlalchemy import Column, String, Text, JSON, Float, Integer, DateTime
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class FacultyDB(Base):
    __tablename__ = "faculties"

    id = Column(String, primary_key=True, index=True)
    university = Column(String, index=True)
    university_th = Column(String, index=True)
    faculty = Column(String)
    faculty_th = Column(String)
    department = Column(String)
    department_th = Column(String)
    
    academic_title_th = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    full_name_th = Column(String)
    
    role = Column(String)
    email = Column(String)
    image_url = Column(String)
    profile_url = Column(String)
    
    education = Column(JSON, default=list)
    research_interests = Column(JSON, default=list)
    taught_courses = Column(JSON, default=list)
    featured_publications = Column(JSON, default=list)
    
    scholar_url = Column(String)
    embedding_text = Column(Text)
    
    # Store the 768-dimensional vector from Gemini (text-embedding-004)
    embedding = Column(Vector(768))


class CourseDB(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, index=True)
    title_th = Column(String, index=True)
    title_en = Column(String, index=True)
    degree_level = Column(String, index=True)  # Bachelor, Master, Doctorate, Certificate
    degree_name = Column(String)  # e.g., วท.ม., วศ.ม., MBA, Ph.D.
    university = Column(String, index=True)
    university_th = Column(String, index=True)
    faculty = Column(String, index=True)
    faculty_th = Column(String, index=True)
    department = Column(String)
    department_th = Column(String)
    program_type = Column(String)  # Regular, International, Special, Weekend
    duration_years = Column(String)
    total_credits = Column(String)
    tuition_per_semester = Column(String)
    tuition_total = Column(String)
    description = Column(Text)
    curriculum_highlights = Column(JSON, default=list)
    career_paths = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    website_url = Column(String)
    embedding_text = Column(Text)
    embedding = Column(Vector(768), nullable=True)


class ResearchLabDB(Base):
    __tablename__ = "research_labs"

    id = Column(String, primary_key=True, index=True)
    name_th = Column(String, index=True)
    name_en = Column(String, index=True)
    university = Column(String, index=True)
    university_th = Column(String, index=True)
    faculty = Column(String, index=True)
    faculty_th = Column(String, index=True)
    department = Column(String)
    department_th = Column(String)

    lead_advisor_id = Column(String, index=True)  # Lead PI / Director
    member_faculty_ids = Column(JSON, default=list)  # List of Faculty IDs

    description = Column(Text)
    research_domains = Column(JSON, default=list)
    flagship_equipment = Column(JSON, default=list)
    industry_partners = Column(JSON, default=list)
    open_positions = Column(JSON, default=list)

    website_url = Column(String)
    image_url = Column(String)

    embedding_text = Column(Text)
    embedding = Column(Vector(768), nullable=True)


class SemanticCacheDB(Base):
    """
    Zero-Token & Zero-Latency Semantic Cache Table (pgvector)
    Stores pre-computed AI thesis match insights and cold emails.
    If query vector cosine distance <= 0.05 (similarity >= 0.95), cached payload is returned instantly.
    """
    __tablename__ = "semantic_cache"

    id = Column(String, primary_key=True, index=True)
    cache_type = Column(String, index=True)  # 'advisor_search', 'cold_email', 'synergy_insight'
    query_text = Column(Text, nullable=False)
    cache_payload = Column(JSON, nullable=False)  # Cached structured response
    hit_count = Column(Integer, default=1)

    embedding = Column(Vector(768), nullable=False)  # 768-dim query embedding
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


