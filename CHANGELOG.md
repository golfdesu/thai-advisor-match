# Changelog

## 2026-09-11

### Removed

- Removed the Cold Email feature from the frontend and backend.
- Removed the Cold Email modal, API endpoint, request/response schemas, AI generator, rate limiter, tests, migration entry, and semantic-cache implementation.
- Removed the Cold Email table from fresh database initialization.

### Updated

- Kept official advisor contact links (`mailto:`) in advisor profiles.
- Applied the `no-ai-slop` writing principles to user-facing copy and project guidance: shorter headings, concrete claims, and fewer generic marketing phrases.
- Updated README, project guidance, career-discovery copy, homepage metadata, and footer text.
- Synced project guidance and API metadata with the current PostgreSQL-only development setup, active Gemini model order, `*DB` model class names, and the new changelog workflow.

### Verification

- `npm run lint` passed.
- `npm run build` passed.
- `python -m compileall -q backend` passed.
- `git diff --check` passed.
- Backend pytest was not available in the current environment (`No module named pytest`).

> Existing Docker volumes are not modified automatically. If an old `semantic_cache` table exists in a volume, it is no longer read or created by the application.
