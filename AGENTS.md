# Thai EduCenter & Advisor Match - Project Guidelines & Architecture

## ⚠️ ABSOLUTE OPERATIONAL INVARIANTS (ZERO-DEVIATION RULES)
> [!IMPORTANT]
> **Strict Process Compliance & Zero-Bypass Policy:**
> 1. **No Direct Data Synthesis / Manual Shortcuts:** When instructed to acquire, scrape, or enrich faculty, curriculum, or laboratory data, NEVER manually author/synthesize data directly into files or bypass pipelines to save time. You MUST strictly execute the designated Autonomous Pipeline CLI Runners (e.g., `python backend/scripts/agentic_pipeline/cli_runner.py` for `SKILL.state` or established crawlers).
> 2. **Process Integrity Over Speed:** Always follow the full lifecycle: Real-time Extraction/Crawl → State Reducer (RapidFuzz Dedup & Title Normalization) → Disk Checkpointing (`data/agent_states/`) → Multi-Threaded Vectorization → Database Commit.
> 3. **Adhere to Defined Skills & Protocols:** If a specialized agent skill exists (e.g., `data-acquire-faculty-elites`, `data-acquire-academic`, `db-optimization`), you MUST execute according to that skill's documented CLI tools and architectural contracts.

---

## 1. Project Overview & Architecture
**Thai EduCenter** (incorporating **Thai Advisor Match**) is an all-in-one AI-powered educational discovery & academic advisor matching platform for undergraduate and graduate candidates in Thailand.

### Core Features:
1. **Curriculum & Tuition Discovery:** Search academic programs across Thai universities (tuition fees, duration, credits, career paths).
2. **AI Semantic Advisor Matching:** Thesis topic/abstract matching with % Match Score via `pgvector` & Gemini embeddings.
3. **Zero-Latency Synergy Badges & Insights:** Instant synthesis of thesis alignment & relevant publication highlights.
4. **AI Cold Email Generator:** Drafts inquiry emails and research proposals for contacting prospective advisors.
5. **RIASEC Career Discovery Quiz:** 3-tier psychological assessment matching students to academic paths.

### Tech Stack:
```text
[ Frontend: Next.js 16 / React 19 / TypeScript / Tailwind CSS v4 (Port 3000) ]
                                  ↕ (REST API JSON)
[ Backend: Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Uvicorn (Port 8000) ]
                                  ↕
[ AI Layer: Gemini API / Embeddings ] ↔ [ Database: PostgreSQL + pgvector (Supabase) ]
```

---

## 2. Strict Technology Versions & Syntax Standards

### 1. Tailwind CSS v4 Rules:
- **No `tailwind.config.js`:** Configured via CSS directives in `frontend/src/app/globals.css`.
- **CSS Directives:** Always start with `@import "tailwindcss";` and declare theme variables via `@theme { ... }`.
- **Class-based Dark Mode:** Must retain the custom variant in `globals.css`:
  ```css
  @custom-variant dark (&:where(.dark, .dark *));
  ```
- **Never inject Tailwind v3 legacy configs or plugins** (no `@tailwind base;` or `tailwind.config.js`).

### 2. Next.js 16 & React 19 Rules:
- **App Router & Client Components:** Interactive components using hooks (`useState`, `useEffect`, `useRouter`, `useSearchParams`) MUST declare `"use client";` at the top.
- **No Synchronous `setState` in Effects:** Do not call `setState` synchronously within the top-level body of `useEffect` on state/prop changes to prevent cascading re-renders.
- **Strict Hydration & Theme Scripts:** 
  - Never read `window` or `localStorage` for initial state. Always use the "Mounted Pattern" (`const [mounted, setMounted] = useState(false)`) to prevent SSR hydration mismatches.
  - Place raw initialization scripts (e.g., `dangerouslySetInnerHTML`) directly inside `<head>` and use `suppressHydrationWarning` on `<html>` to avoid React 19 "Encountered a script tag..." errors.
- **Next.js Image Optimization & Zero-CLS Rules:**
  - **No `<img>` Tags:** Always use `<Image />` from `next/image` to eliminate Cumulative Layout Shift (CLS = 0) and satisfy `@next/next/no-img-element`. Never bypass with `eslint-disable`.
  - **Explicit Sizing:** Provide explicit `width`/`height` or use `fill` inside a `relative` container with a descriptive `sizes` attribute (e.g. `sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"`).
  - **Declarative Fallback:** Never mutate DOM directly (`(e.target as HTMLElement).src = ...`). Use React state flags to cleanly fallback to `getAdvisorAvatarUrl(name)`.
  - **Domain Whitelisting:** Declare external sources in `frontend/next.config.ts` (`**.ac.th`, `**.edu`, `images.unsplash.com`, `ui-avatars.com`). Use `unoptimized` on dynamic university URLs when edge caching is unnecessary.
- **Type-only Imports:** Use `import type { ... } from "@/types"` for interfaces and types.

### 3. Pydantic v2 & FastAPI Rules:
- **Pydantic v2 Syntax:**
  - Use `model.model_dump()` and `model.model_dump_json()` (never deprecated `dict()` / `json()`).
  - Use `@field_validator("field_name", mode="before")` and `@model_validator(mode="after")`.
  - Use `ConfigDict(from_attributes=True)` (never `class Config: orm_mode = True`).
- **Python 3.12+ Annotations:** Use standard type unions (`str | None`, `list[str]`) for models and route parameters.

### 4. Database, pgvector & Skills:
> [!NOTE]
> Database tuning rules reside in `.agents/skills/db-optimization/SKILL.md`.

---

## 3. Data Schema & Core Models

| Entity | Storage | Key Attributes | Schema Source |
| :--- | :--- | :--- | :--- |
| **Faculty Member** | `faculties` table | `id`, `full_name_th`, `university_th`, `faculty_th`, `department_th`, `academic_title_th`, `email`, `image_url`, `research_interests`, `featured_publications`, `embedding` (768-dim) | `backend/app/models/db_models.py` (`Faculty`) & `frontend/src/types/index.ts` (`FacultyMember`) |
| **Course / Curriculum** | `courses` table | `id`, `title_th`, `title_en`, `degree_level`, `university_th`, `faculty_th`, `tuition_per_semester`, `total_credits`, `curriculum_highlights`, `career_paths`, `embedding` | `backend/app/models/db_models.py` (`Course`) & `frontend/src/types/index.ts` (`Course`) |
| **Research Lab** | `research_labs` table | `id`, `name_th`, `name_en`, `university_th`, `faculty_th`, `lead_advisor_id`, `research_domains`, `flagship_equipment`, `open_positions`, `embedding` | `backend/app/models/db_models.py` (`ResearchLab`) & `frontend/src/types/index.ts` (`ResearchLab`) |

---

## 4. Key Directory Structure

```text
Teacher/
├── frontend/                     # Next.js 16 Super App UI (App Router)
│   ├── src/
│   │   ├── app/                  # Routes: /, /advisor/[id], /labs/[id], /career-discovery
│   │   ├── components/           # UI Components (AdvisorCard, CourseCard, LabCard, Header, Footer)
│   │   ├── lib/                  # config.ts (API URLs & Avatar helpers), dsa.ts (Client LRU Cache)
│   │   └── types/index.ts        # Central TypeScript interfaces (Single Source of Truth)
│   └── next.config.ts            # Image domain allowlists & Next.js config
│
├── backend/                      # Python FastAPI API & Scraping Engine
│   ├── app/
│   │   ├── api/                  # Routes: routes_search, routes_faculty, routes_courses, routes_labs, routes_career_quiz
│   │   ├── core/                 # config, database, dsa_utils (LRUCache, TopKHeap, Trie), embedding_service
│   │   └── models/               # db_models (SQLAlchemy + pgvector), schema (Pydantic DTOs)
│   └── scripts/                  # Data Ingestion, Crawlers & Canonical Merging Pipelines
└── .agents/skills/               # Domain-specific automation skills (db-optimization, data-acquire-*, etc.)
```

---

## 5. High-Performance, Anti-Bottleneck & DSA Standards

### 1. AI & LLM Performance:
- **No Sequential LLM Loops:** NEVER call LLM APIs (Gemini) inside loops across search candidate lists. Use pre-compiled contextual template generators (0ms latency).
- **Two-Tier Semantic Caching (`pgvector` + L1 Memory):** Cache query responses & cold email drafts in `SemanticCacheDB` (Cosine Distance $\le 0.10$ / Similarity $\ge 0.90$) and `L1_MEMORY_CACHE` for **0-token, 0ms** instant repeated lookups.
- **Deterministic Content Pruning (LLMLingua-2 & Trafilatura):** Always strip boilerplate navbars/footers via `ContentPruner` before calling LLMs (80%+ input token reduction).
- **Output Schema Compression:** Keep JSON output schemas strictly compact by letting the State Reducer inject static university/faculty metadata in Python (40%+ output token reduction).
- **In-Memory Embedding Caching:** Cache query vector embeddings in backend `LRUCache` (`_embedding_cache`) for 0.001ms instant repeated lookups.
- **Client Pooling:** Cache and reuse `genai.Client` instances by API key instead of re-instantiating per request.
- **Fast Model Hierarchy:** Default to `gemini-3.6-flash` or `gemini-2.5-flash` for user-facing interactive endpoints.

### 2. Data Structures & Algorithms (DSA):
- **True $O(1)$ LRU Caching:** Sentinel DLL + Hash Map implementation in `backend/app/core/dsa_utils.py` and `frontend/src/lib/dsa.ts`.
- **$O(N \log K)$ Top-K Min-Heap:** Collect top-K ranked candidates via `TopKHeap` (`heapreplace`) instead of sorting the entire candidate array ($O(N \log N)$).
- **$O(L)$ Trie & Set Lookups:** Index taxonomy in `Trie` for $O(L)$ prefix lookup. Use Python `set()` for interest/synergy matching to prevent $O(N^2)$ nested scans.
- **Fast Inverted Index:** Maintain token posting lists with TF-IDF weighting for sub-millisecond lexical fallback searches.

### 3. API & Database Hygiene:
- **Response Compression:** Enable `GZipMiddleware(minimum_size=1000)` on FastAPI (70–85% payload reduction).
- **Pre-compiled Regex:** Compile dictionary transformations (`re.compile`) once at module level.
- **SQL Pre-filtering:** Enforce `filter(...).limit(...)` at SQL level. Never execute unconstrained `.all()` into Python memory.
- **Batch Processing:** Use `Model.id.in_(batch_ids)` and commit once per batch in ingestion pipelines. Delete temporary/one-off ingestion scripts after verification.

---

## 6. DRY & Frontend Contracts
- **Centralized Frontend Contracts:** Never define duplicate TypeScript `interface` or `type` blocks in individual page components. Always import from `@/types`.
- **Single Source for Helpers:** Always import `API_BASE_URL` and `getAdvisorAvatarUrl` from `@/lib/config`.
- **Instant Search on Interaction:** Popular chips and quick filter tags must trigger immediate search execution.
- **Enforce Query Limits:** Always apply reasonable default pagination limits (`limit=24..50`) to keep DOM node counts and memory lightweight.

---

## 7. Cybersecurity, PDPA & System Hardening

1. **API Protection & Rate Limiting:** Public endpoints protected by IP sliding-window rate limiting (`RateLimiter`, 180 req/min per IP with HTTP `429` & `Retry-After: 60`).
2. **Strict CORS Policy:** Whitelist specific origins (`http://localhost:3000`, production domains). Never use wildcard `allow_origins=["*"]` with credentials.
3. **OWASP Security Response Headers:** Inject `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Permissions-Policy`.
4. **LLM Prompt Injection Defense (OWASP LLM01):** User inputs passed to prompts MUST be sanitized via `sanitize_for_prompt` (neutralize instruction overrides and strip null bytes `\x00`).
5. **PDPA & Privacy Protection:**
   - Automatically redact Thai 13-digit National IDs (`\b[1-9]\d{12}\b`) and sensitive PII before calling external AI APIs.
   - **Never collect or store personal phone numbers.** Collect only official academic contact channels.
6. **Input Validation:** Enforce strict Pydantic constraints (`min_length`, `max_length`, regex `pattern`, `ge`/`le` numeric bounds) on all DTOs.
7. **Safe External Links:** Every external anchor (`target="_blank"`) MUST include `rel="noopener noreferrer"`.

---

## 8. Specialized Domain Skills Reference & WikiSkill Architecture
<!-- Reference: SKILL.state (arXiv:2608.26263v2) & WikiSkill (arXiv:2608.27454v1) -->

The project implements the 3-Layer **WikiSkill Architecture** for autonomous data acquisition, self-evolving procedural knowledge, and lifelong web directory memory:
- **Layer 1 (Raw Traces):** `Teacher/.agents/raw_traces/` (Immutable execution logs).
- **Layer 2 (Persistent Wiki):** `Teacher/.agents/wiki/` (`WIKI_INDEX.md`, `universities/`, `patterns/`, `evolution_log.md`).
- **Layer 3 (Active Skills):** `Teacher/.claude/skills/` and `Teacher/.agents/skills/`.

### Specialized Skills:
- **Database Tuning:** `.agents/skills/db-optimization/SKILL.md`
- **Academic Faculty Acquisition (SKILL.state & WikiSkill):** `.agents/skills/data-acquire-academic/SKILL.md` & `data-acquire-faculty-elites/SKILL.md`
- **Curriculum & Tuition Discovery:** `.agents/skills/data-curriculum-tuition-discovery/SKILL.md`
- **Scraper & SPA Builders:** `.agents/skills/data-build-scraper/SKILL.md` & `data-scrape-spa/SKILL.md`
