-- ====================================================================
-- Thai EduCenter / Thai Advisor Match Database Initialization Script
-- Local PostgreSQL with pgvector & pg_trgm extensions
-- ====================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Create Table: faculties
CREATE TABLE IF NOT EXISTS public.faculties (
    id VARCHAR PRIMARY KEY,
    university VARCHAR,
    university_th VARCHAR,
    faculty VARCHAR,
    faculty_th VARCHAR,
    department VARCHAR,
    department_th VARCHAR,
    academic_title_th VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    full_name_th VARCHAR,
    role VARCHAR,
    email VARCHAR,
    image_url VARCHAR,
    profile_url VARCHAR,
    education JSON DEFAULT '[]'::json,
    research_interests JSON DEFAULT '[]'::json,
    taught_courses JSON DEFAULT '[]'::json,
    featured_publications JSON DEFAULT '[]'::json,
    scholar_url VARCHAR,
    embedding_text TEXT,
    embedding vector(768),
    total_publications_count INTEGER DEFAULT 0,
    first_author_count INTEGER DEFAULT 0,
    co_author_count INTEGER DEFAULT 0,
    total_citations INTEGER DEFAULT 0,
    h_index INTEGER DEFAULT 0,
    openalex_id VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_faculties_id ON public.faculties (id);
CREATE INDEX IF NOT EXISTS ix_faculties_university ON public.faculties (university);
CREATE INDEX IF NOT EXISTS ix_faculties_university_th ON public.faculties (university_th);
CREATE INDEX IF NOT EXISTS idx_faculties_name_th_trgm ON public.faculties USING gin (full_name_th gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_dept_th_trgm ON public.faculties USING gin (department_th gin_trgm_ops);
-- perf audit 2026-09-10: ILIKE '%..%' filters on the search hot path were seq-scanning
CREATE INDEX IF NOT EXISTS idx_faculties_university_th_trgm ON public.faculties USING gin (university_th gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_university_trgm ON public.faculties USING gin (university gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_faculty_th_trgm ON public.faculties USING gin (faculty_th gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_faculty_trgm ON public.faculties USING gin (faculty gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_first_name_trgm ON public.faculties USING gin (first_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_last_name_trgm ON public.faculties USING gin (last_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculties_department_trgm ON public.faculties USING gin (department gin_trgm_ops);
-- keyword_fallback_search ORs across 8 columns; Postgres only BitmapOrs (vs seq scan)
-- when EVERY branch is indexed. embedding_text trgm: 73ms -> 0.5ms on selective Thai terms.
CREATE INDEX IF NOT EXISTS idx_faculties_emb_text_trgm ON public.faculties USING gin (embedding_text gin_trgm_ops);
-- distinguished-advisor ordering (ORDER BY h_index DESC NULLS LAST)
CREATE INDEX IF NOT EXISTS ix_faculties_h_index ON public.faculties (h_index DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS ix_faculties_embedding_hnsw ON public.faculties USING hnsw (embedding vector_cosine_ops);

-- 3. Create Table: courses
CREATE TABLE IF NOT EXISTS public.courses (
    id VARCHAR PRIMARY KEY,
    title_th VARCHAR,
    title_en VARCHAR,
    degree_level VARCHAR,
    degree_name VARCHAR,
    university VARCHAR,
    university_th VARCHAR,
    faculty VARCHAR,
    faculty_th VARCHAR,
    department VARCHAR,
    department_th VARCHAR,
    program_type VARCHAR,
    duration_years VARCHAR,
    total_credits VARCHAR,
    tuition_per_semester VARCHAR,
    tuition_total VARCHAR,
    description TEXT,
    curriculum_highlights JSON DEFAULT '[]'::json,
    career_paths JSON DEFAULT '[]'::json,
    tags JSON DEFAULT '[]'::json,
    website_url VARCHAR,
    embedding_text TEXT,
    embedding vector(768)
);

CREATE INDEX IF NOT EXISTS ix_courses_id ON public.courses (id);
CREATE INDEX IF NOT EXISTS ix_courses_university ON public.courses (university);
CREATE INDEX IF NOT EXISTS ix_courses_university_th ON public.courses (university_th);
CREATE INDEX IF NOT EXISTS ix_courses_faculty ON public.courses (faculty);
CREATE INDEX IF NOT EXISTS ix_courses_faculty_th ON public.courses (faculty_th);
CREATE INDEX IF NOT EXISTS ix_courses_title_th ON public.courses (title_th);
CREATE INDEX IF NOT EXISTS ix_courses_title_en ON public.courses (title_en);
CREATE INDEX IF NOT EXISTS ix_courses_degree_level ON public.courses (degree_level);
CREATE INDEX IF NOT EXISTS idx_courses_title_th_trgm ON public.courses USING gin (title_th gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_courses_title_en_trgm ON public.courses USING gin (title_en gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_courses_faculty_th_trgm ON public.courses USING gin (faculty_th gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_courses_embedding_hnsw ON public.courses USING hnsw (embedding vector_cosine_ops);

-- 4. Create Table: research_labs
CREATE TABLE IF NOT EXISTS public.research_labs (
    id VARCHAR PRIMARY KEY,
    name_th VARCHAR,
    name_en VARCHAR,
    university VARCHAR,
    university_th VARCHAR,
    faculty VARCHAR,
    faculty_th VARCHAR,
    department VARCHAR,
    department_th VARCHAR,
    lead_advisor_id VARCHAR,
    member_faculty_ids JSON DEFAULT '[]'::json,
    description TEXT,
    research_domains JSON DEFAULT '[]'::json,
    flagship_equipment JSON DEFAULT '[]'::json,
    industry_partners JSON DEFAULT '[]'::json,
    open_positions JSON DEFAULT '[]'::json,
    website_url VARCHAR,
    image_url VARCHAR,
    embedding_text TEXT,
    embedding vector(768)
);

CREATE INDEX IF NOT EXISTS ix_research_labs_id ON public.research_labs (id);
CREATE INDEX IF NOT EXISTS ix_research_labs_university ON public.research_labs (university);
CREATE INDEX IF NOT EXISTS ix_research_labs_university_th ON public.research_labs (university_th);
CREATE INDEX IF NOT EXISTS ix_research_labs_faculty ON public.research_labs (faculty);
CREATE INDEX IF NOT EXISTS ix_research_labs_faculty_th ON public.research_labs (faculty_th);
CREATE INDEX IF NOT EXISTS ix_research_labs_name_th ON public.research_labs (name_th);
CREATE INDEX IF NOT EXISTS ix_research_labs_name_en ON public.research_labs (name_en);
CREATE INDEX IF NOT EXISTS ix_research_labs_lead_advisor_id ON public.research_labs (lead_advisor_id);
-- ANN index for /labs/search (created live 2026-09-10 perf audit; init.sql synced so fresh containers match)
CREATE INDEX IF NOT EXISTS ix_research_labs_embedding_hnsw ON public.research_labs USING hnsw (embedding vector_cosine_ops);

-- 5. Create Table: semantic_cache
CREATE TABLE IF NOT EXISTS public.semantic_cache (
    id VARCHAR PRIMARY KEY,
    cache_type VARCHAR,
    query_text TEXT NOT NULL,
    cache_payload JSON NOT NULL,
    hit_count INTEGER DEFAULT 1,
    embedding vector(768) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_semantic_cache_id ON public.semantic_cache (id);
CREATE INDEX IF NOT EXISTS ix_semantic_cache_cache_type ON public.semantic_cache (cache_type);
-- perf audit 2026-09-10: L2 lookup ORDER BY embedding <=> was a full sort (no index)
CREATE INDEX IF NOT EXISTS ix_semantic_cache_embedding_hnsw ON public.semantic_cache USING hnsw (embedding vector_cosine_ops);

-- 6. Create Table: quiz_questions
CREATE TABLE IF NOT EXISTS public.quiz_questions (
    id VARCHAR PRIMARY KEY,
    category VARCHAR,
    question TEXT,
    choices JSON,
    answer INTEGER,
    explanation TEXT,
    level VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_quiz_questions_id ON public.quiz_questions (id);
CREATE INDEX IF NOT EXISTS ix_quiz_questions_category ON public.quiz_questions (category);

-- 7. Create Table: quiz_attempts
CREATE TABLE IF NOT EXISTS public.quiz_attempts (
    id SERIAL PRIMARY KEY,
    category VARCHAR,
    score INTEGER,
    total INTEGER,
    answers JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_quiz_attempts_category ON public.quiz_attempts (category);
CREATE INDEX IF NOT EXISTS ix_quiz_attempts_created_at ON public.quiz_attempts (created_at);
