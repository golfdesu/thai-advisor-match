import os
import sys
import json
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base
from app.models.db_models import FacultyDB
from sqlalchemy import text
from app.core.config import settings

# Attempt to load genai for embeddings
try:
    from google import genai
    import numpy as np
    if settings.GEMINI_API_KEY:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    else:
        client = None
except ImportError:
    client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_embedding(text_content: str):
    if not client or not text_content:
        return np.zeros(768).tolist()
    
    try:
        response = client.models.embed_content(
            model='text-embedding-004',
            contents=text_content,
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return np.zeros(768).tolist()

def init_db():
    logger.info("Initializing database...")
    
    # Create pgvector & pg_trgm extensions
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        if not str(engine.url).startswith("sqlite"):
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            except Exception as e:
                logger.warning(f"Could not create pg_trgm extension: {e}")
        conn.commit()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

    # Create HNSW vector & GIN Trigram indexes for ultra-fast vector & ILIKE text search
    if not str(engine.url).startswith("sqlite"):
        with engine.connect() as conn:
            try:
                # Vector HNSW Indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_faculties_embedding_hnsw ON faculties USING hnsw (embedding vector_cosine_ops);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_courses_embedding_hnsw ON courses USING hnsw (embedding vector_cosine_ops);"))
                
                # Trigram GIN Indexes for fast ILIKE substring searches
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_courses_title_th_trgm ON courses USING gin (title_th gin_trgm_ops);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_courses_faculty_th_trgm ON courses USING gin (faculty_th gin_trgm_ops);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_faculties_name_th_trgm ON faculties USING gin (full_name_th gin_trgm_ops);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_faculties_dept_th_trgm ON faculties USING gin (department_th gin_trgm_ops);"))
                
                conn.commit()
                logger.info("HNSW Vector & GIN Trigram Indexes verified/created successfully.")
            except Exception as ex:
                logger.warning(f"Could not create advanced indexes (may already exist or not supported): {ex}")

    # Seed data
    data_file = Path(__file__).resolve().parent.parent.parent / "cmu_ee_faculty.json"
    if data_file.exists():
        logger.info(f"Loading data from {data_file}")
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        with engine.connect() as conn:
            from sqlalchemy.orm import Session
            with Session(engine) as session:
                members = data.get("members", [])
                
                for m in members:
                    # Check if already exists
                    existing = session.query(FacultyDB).filter_by(id=m['id']).first()
                    if existing:
                        logger.info(f"Skipping {m['full_name_th']} (already exists)")
                        continue
                    
                    logger.info(f"Processing {m['full_name_th']}...")
                    embedding_text = m.get('embedding_text', '')
                    vector = generate_embedding(embedding_text)
                    
                    db_member = FacultyDB(
                        id=m['id'],
                        university=m.get('university'),
                        university_th=m.get('university_th'),
                        faculty=m.get('faculty'),
                        faculty_th=m.get('faculty_th'),
                        department=m.get('department'),
                        department_th=m.get('department_th'),
                        academic_title_th=m.get('academic_title_th'),
                        first_name=m.get('first_name'),
                        last_name=m.get('last_name'),
                        full_name_th=m.get('full_name_th'),
                        role=m.get('role'),
                        email=m.get('email'),
                        image_url=m.get('image_url'),
                        profile_url=m.get('profile_url'),
                        education=m.get('education', []),
                        research_interests=m.get('research_interests', []),
                        taught_courses=m.get('taught_courses', []),
                        featured_publications=m.get('featured_publications', []),
                        scholar_url=m.get('scholar_url'),
                        embedding_text=embedding_text,
                        embedding=vector
                    )
                    session.add(db_member)
                
                session.commit()
                logger.info("Data seeding completed!")
    else:
        logger.error(f"Data file not found at {data_file}")

if __name__ == "__main__":
    init_db()
