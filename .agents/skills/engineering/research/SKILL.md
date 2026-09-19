---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, and first-party APIs), not a secondary write-up. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file. Cite the source beside each material claim and separate verified facts from recommendations.
3. Save it under `.agents/wiki/`, matching `.agents/wiki/WIKI_INDEX.md` and the existing directory convention. Use `universities/` for university-specific findings, `patterns/` for reusable crawler or extraction patterns, and `research/` only if that category already exists or the user asks for it. Update the wiki index when the repository convention requires it.

## Thai EduCenter research rules

- For Gemini, verify the active model and embedding identifier against the official Google AI documentation and the implementation in `backend/app/core/embedding_service.py`; do not assume a model name from an old note.
- For pgvector, use the pgvector source/documentation and compare with the local schema and HNSW index definitions.
- For search quality, use synthetic or predefined benchmark queries. Never use production user data.
- For crawler research, record the official institutional URL, access date, extraction pattern, and any unresolved ambiguity in the relevant wiki page.
- Do not turn research into manual data synthesis. Findings may document a source or procedure; actual faculty, course, lab, and embedding changes must go through the project's acquisition pipeline.
- Redact API keys, Thai National IDs, phone numbers, and other sensitive values from notes and captured artifacts.

## Primary sources for common topics

| Topic | Primary source |
|---|---|
| Gemini API models and embeddings | https://ai.google.dev/gemini-api/docs/models |
| pgvector HNSW and distance operators | https://github.com/pgvector/pgvector |
| SQLAlchemy 2.0 | https://docs.sqlalchemy.org/en/20/ |
| Next.js App Router | https://nextjs.org/docs |
| Tailwind CSS v4 | https://tailwindcss.com/docs |
| OpenAlex API | https://docs.openalex.org |
| Pydantic v2 | https://docs.pydantic.dev/latest/ |
| BM25 implementation details | https://github.com/dorianbrown/rank_bm25 |

Before writing, read the relevant local skill as well as the primary source: for example `db-optimization`, `gemini-api-dev`, `qa-evaluate-search`, or `webapp-testing`.
