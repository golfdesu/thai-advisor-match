from sqlalchemy import Column, String, Text, JSON, Integer
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

    total_publications_count = Column(Integer, default=0)
    first_author_count = Column(Integer, default=0)
    co_author_count = Column(Integer, default=0)
    total_citations = Column(Integer, default=0)
    h_index = Column(Integer, default=0)
    openalex_id = Column(String)

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
