---
name: db-optimization
description: Specialized Supabase, PostgreSQL, pgvector, and SQLAlchemy optimization guidelines for the Thai EduCenter backend.
---

# Supabase & PostgreSQL Custom Best Practices

This skill defines the exact database interaction standards for the project to ensure <500ms latency when communicating with Supabase PostgreSQL via Python (FastAPI). 
**Do not use standard Supabase JS client instructions; follow these SQLAlchemy specific rules instead.**

## 1. SQLAlchemy 2.0 & pgvector Rules
- **2.0 Style Queries:** Always use `select(Model).where(...)` and execute via session (`session.scalars(query)` / `session.execute(query)`).
- **Vector Cosine Distance:** Execute direct HNSW vector ordering with `order_by(Model.embedding.cosine_distance(query_vector))` and `filter(Model.embedding.isnot(None))`. Never wrap distances in functions that break index scans.
- **Column Deferrals:** Always apply `.options(defer(Model.embedding))` on list and search queries to avoid large vector payload memory overheads.

## 2. Database & pgvector Optimization Rules
- **HNSW Vector Indexes:** Ensure `hnsw (embedding vector_cosine_ops)` indexes exist on `faculties` and `courses` tables.
- **Direct Vector Distance Ordering:** Use direct `ORDER BY embedding.cosine_distance(query_vector)` with `filter(embedding.isnot(None))` to activate PostgreSQL HNSW index scans. Never wrap distances in `func.coalesce()` or other expressions that force Full Table Scans.
- **GIN Trigram Indexing for Text:** Utilize the `pg_trgm` extension with GIN indexes on `title_th`, `faculty_th`, `full_name_th`, and `department_th` to accelerate `ILIKE '%...%'` queries.
- **Heavy Column Deferral:** Always apply `defer(Model.embedding)` and `defer(Model.embedding_text)` on search and list endpoints to avoid transferring 768-float arrays over the network.
- **Supabase Connection Pooling:** Configure SQLAlchemy with `pool_size=10, max_overflow=20, pool_recycle=300, pool_timeout=15, pool_pre_ping=True` to prevent idle connection drops and cold start penalties.

