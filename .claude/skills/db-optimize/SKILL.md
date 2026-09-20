---
name: db-optimize
description: Database tuning, indexing, and query optimization for PostgreSQL 17 + pgvector (HNSW cosine indexes, GIN trigram indexes, heavy column deferrals, and zero-egress invariants).
---

# Database Tuning & pgvector Optimization Skill

This skill defines the operational standards and commands for tuning PostgreSQL 17 + pgvector in the Thai EduCenter & Advisor Match project.

## Operational Invariants
1. **Local-First Zero-Egress Invariant:** High-throughput queries, bulk ingestions, and testing MUST run on local Docker container (`localhost:5432/advisor_match`). Zero unverified streaming to remote Supabase.
2. **PostgreSQL 17 + pgvector 0.8 Parity:** Binary parity between local Docker (`pgvector/pgvector:pg17`) and production Supabase.
3. **Column Deferral Standard:** Heavy columns (`embedding` 768-dim float arrays, `embedding_text`) must ALWAYS be deferred (`options(defer(Model.embedding))`) on list and search queries to prevent multi-gigabyte memory bloat and network payload latency.

---

## Indexing Architecture

### 1. HNSW Vector Cosine Distance Index (`pgvector`)
- **Table:** `faculties`, `courses`, `research_labs`
- **Definition:**
  ```sql
  CREATE INDEX IF NOT EXISTS ix_faculties_embedding_hnsw
  ON faculties USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```
- **Query Standard:**
  Use direct `order_by(FacultyDB.embedding.cosine_distance(query_vector))` with `filter(FacultyDB.embedding.isnot(None))`.
  *Strict Anti-Pattern:* Never wrap vector distances in `func.coalesce()` or mathematical expressions that break HNSW index scan activation.

### 2. GIN Trigram Indexing (`pg_trgm`)
- **Table:** `faculties`, `courses`, `research_labs`
- **Definition:**
  ```sql
  CREATE INDEX IF NOT EXISTS idx_faculties_name_th_trgm
  ON faculties USING gin (full_name_th gin_trgm_ops);

  CREATE INDEX IF NOT EXISTS idx_faculties_dept_th_trgm
  ON faculties USING gin (department_th gin_trgm_ops);

  CREATE INDEX IF NOT EXISTS idx_faculties_fac_th_trgm
  ON faculties USING gin (faculty_th gin_trgm_ops);
  ```
- **Query Standard:**
  Accelerates lexical Thai text search (`ILIKE '%...%'`) with sub-millisecond execution.

### 3. SQLAlchemy 2.0 Connection Pool Tuning
- Local/production engine pool parameters:
  ```python
  engine = create_engine(
      settings.DATABASE_URL,
      pool_size=10,
      max_overflow=20,
      pool_recycle=300,
      pool_timeout=15,
      pool_pre_ping=True
  )
  ```

---

## Maintenance & Verification Commands

Inspect active indexes and table sizes:
```bash
python -c "
from backend.app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
res = db.execute(text('''
    SELECT tablename, indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public' AND tablename IN ('faculties', 'courses', 'research_labs')
    ORDER BY tablename, indexname;
''')).fetchall()

for row in res:
    print(f'{row[0]} -> {row[1]}')
db.close()
"
```

Reindex and analyze tables:
```bash
python -c "
from backend.app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
db.execute(text('VACUUM ANALYZE faculties;'))
db.execute(text('VACUUM ANALYZE courses;'))
db.execute(text('VACUUM ANALYZE research_labs;'))
print('VACUUM ANALYZE completed successfully.')
db.close()
"
```
