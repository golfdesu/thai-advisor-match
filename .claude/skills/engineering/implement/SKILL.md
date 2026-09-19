---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use `/tdd` where possible, at pre-agreed seams. Keep one vertical slice small: failing test, minimal implementation, then the next slice.

## Typechecking and focused verification

Run focused checks after every significant change:

**Backend:**

```bash
cd backend && python -m mypy app/ --ignore-missing-imports
```

If mypy is not installed in the environment, record that limitation and still run the relevant pytest checks.

**Frontend:**

```bash
npm --prefix frontend run build
```

The Next.js build is the frontend TypeScript and App Router verification command.

**Single backend test file during the TDD loop:**

```bash
pytest backend/tests/<test_file>.py -v
```

**Full backend suite once at the end:**

```bash
pytest backend/tests -v
```

## Thai EduCenter invariants

Before calling the implementation done, verify:

- [ ] Local-first work uses the Docker PostgreSQL database at `localhost:5432`; no ingestion or embedding pipeline targets Supabase.
- [ ] Vector list/search queries defer `Model.embedding` and use SQL-level filtering and limits.
- [ ] User-controlled text sent to Gemini passes through `sanitize_for_prompt`; Thai 13-digit IDs and other sensitive data are redacted.
- [ ] Nullable ORM JSON/array fields use `(field or [])` before iteration or slicing.
- [ ] BM25 indexing and scoring use the same `tokenize_mixed` tokenizer.
- [ ] New Thai title regexes require a delimiter such as `ดร\.` or `ดร\s+`; compound alternatives precede shorter ones.
- [ ] Frontend interactive components declare `"use client"`, use the mounted pattern where browser state is involved, and render images with `next/image` rather than `<img>`.
- [ ] External links with `target="_blank"` include `rel="noopener noreferrer"`.

Once done, use `/code-review` to review the work. Commit the work to the current branch only when the user has explicitly requested a commit.
