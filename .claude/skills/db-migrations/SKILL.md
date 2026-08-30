---
name: db-migrations
description: Runbook for safely generating, reviewing, and applying database schema migrations using Alembic and Supabase PostgreSQL.
---

# Database Migration Management (Alembic)

This skill provides the operational runbook for executing database schema changes safely. Do NOT mix this with query optimization; this is strictly for altering tables.

## Pre-Flight Checklist
Before generating a migration:
1. Ensure the SQLAlchemy models in `backend/app/models/db_models.py` reflect the desired state.
2. Verify that vectors and embeddings still utilize `pgvector` specifically.

## Migration Generation Workflow
1. **Autogenerate:** Run `alembic revision --autogenerate -m "description_of_change"` to create the migration script.
2. **Review Script:** Open the newly generated revision file in `alembic/versions/` and manually inspect `upgrade()` and `downgrade()`.
   - Ensure vector indexes (like HNSW) are properly defined if adding a new table.
   - Alembic may not auto-detect specific `pgvector` or `pg_trgm` index additions natively without specific setup. Manually inject `execute()` statements for these if needed.
3. **Verify Downgrade:** Ensure the `downgrade()` function accurately reverses the changes WITHOUT data loss (unless explicitly destructive).

## Applying Migrations
- Apply locally first: `alembic upgrade head`
- If a migration fails, NEVER manually delete rows in the `alembic_version` table. Fix the script and re-run, or use `alembic downgrade -1`.

