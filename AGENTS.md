# Thai EduCenter & Advisor Match - Project Guidelines & Architecture

## 1. Project Overview & Vision
**Thai EduCenter** (incorporating **Thai Advisor Match**) is an all-in-one AI-powered educational discovery platform designed for prospective undergraduate and graduate students (Bachelor's, Master's, and Ph.D. candidates) in Thailand.

### Core Features:
1. **University Curriculum & Course Directory:** Comprehensive search and exploration of academic programs across Thai universities (tuition fees, duration, credits, and career paths).
2. **AI Semantic Advisor Matching:** Students input their thesis topics, abstracts, or research proposals. The platform semantically indexes, matches, and ranks faculty members and universities with the highest alignment, displaying a % Match Score.
3. **AI Match Explanation:** Automatically synthesizes concise explanations of why a specific professor is an ideal match for the student's research direction.
4. **Comprehensive Profiles:** Academic background, research interests, supervised courses, publication links, and official contact channels.
5. **AI Cold Email Generator:** An AI assistant that drafts professional inquiry emails and research proposals for contacting prospective advisors in Thai and English.
6. **RIASEC Career Discovery Quiz:** A 3-tier psychological assessment (Quick 12, Standard 24, Deep Dive 50 questions) that matches students to suitable academic paths.

---

## 2. Tech Stack & Architecture (Monorepo)

```text
[ Frontend: Next.js 16 / React / TypeScript / Tailwind CSS (Port 3000) ]
                          ↕ (REST API JSON)
[ Backend: Python FastAPI / Uvicorn (Port 8000) ]
                          ↕
[ AI Layer: Gemini API / Embeddings ] ↔ [ Database: PostgreSQL + pgvector (Supabase) ]
```

* **Frontend (`/frontend`):**
  * **Framework:** Next.js `16.3.2` (App Router, Turbopack, React Server/Client Components).
  * **Core Engine:** React `19.2.8` & React DOM `19.2.8`.
  * **Styling:** Tailwind CSS `v4.x` (`@tailwindcss/postcss` `^4.0.0`) with `@theme` and `@custom-variant dark`.
  * **Language:** TypeScript `^5.0.0` (Strict typing, central types in `frontend/src/types/index.ts`).
  * **Icons:** `lucide-react` `^1.34.0`.
* **Backend (`/backend`):**
  * **Runtime:** Python `3.12+`.
  * **API Framework:** FastAPI `>=0.110.0`, Uvicorn `>=0.28.0`.
  * **Data Validation:** Pydantic `v2.6.0+` (`pydantic-settings` `>=2.2.0`).
  * **ORM & Database:** SQLAlchemy `2.0+`, `psycopg2-binary`, `pgvector`.
  * **AI & NLP:** `google-genai` `>=0.1.1` (Gemini API with `gemini-embedding-2` & `gemini-2.5-flash` / `gemini-3.6-flash`).
  * **Scraping Engine:** `httpx` `>=0.27.0`, `requests` `>=2.31.0`, `beautifulsoup4` `>=4.12.3`, `rapidfuzz`, `scholarly`.
* **Database & Vector Store:**
  * **Production:** PostgreSQL + `pgvector` hosted on **Supabase**.

---

## 2.1 Strict Technology Versions & Syntax Standards (Must Read Before Editing)

All agents and developers MUST strictly follow the exact syntax standards corresponding to these library versions:

### 1. Tailwind CSS v4 Rules:
- **No `tailwind.config.js`:** Tailwind CSS v4 is configured via CSS directives in `frontend/src/app/globals.css`.
- **CSS Import:** Always use `@import "tailwindcss";` at the top.
- **Theme Variables:** Declare variables using `@theme { ... }` blocks.
- **Class-based Dark Mode:** To ensure class-based dark mode toggling (`<html class="dark">`) works with `dark:*` utility classes, `globals.css` MUST always retain:
  ```css
  @custom-variant dark (&:where(.dark, .dark *));
  ```
- **Never downgrade or inject Tailwind v3 configs or plugins** (e.g., do not add `@tailwind base;` or create `tailwind.config.js`).

### 2. Next.js 16 & React 19 Rules:
- **App Router:** Use App Router conventions under `frontend/src/app/`.
- **Client Components:** Any interactive component using React hooks (`useState`, `useEffect`, `useRouter`, `useSearchParams`) MUST have `"use client";` at the very top.
- **React 19 Compatibility:** Ensure hooks and component trees adhere to React 19 standards. Never use deprecated legacy lifecycles or legacy context patterns.

### 3. Pydantic v2 & FastAPI Rules:
- **Pydantic v2 Syntax:** Always use Pydantic v2 methods:
  - Use `model.model_dump()` and `model.model_dump_json()` instead of deprecated `dict()` / `json()`.
  - Use `@field_validator("field_name", mode="before")` and `@model_validator(mode="after")` instead of deprecated `@validator` / `@root_validator`.
  - Use `ConfigDict(from_attributes=True)` instead of `class Config: orm_mode = True`.
- **FastAPI Type Annotations:** Utilize standard Python 3.12 type union syntax (`str | None`, `list[str]`) for models and route parameters.

### 4. SQLAlchemy 2.0 & pgvector Rules:
- **2.0 Style Queries:** Always use `select(Model).where(...)` and execute via session (`session.scalars(query)` / `session.execute(query)`).
- **Vector Cosine Distance:** Execute direct HNSW vector ordering with `order_by(Model.embedding.cosine_distance(query_vector))` and `filter(Model.embedding.isnot(None))`. Never wrap distances in functions that break index scans.
- **Column Deferrals:** Always apply `.options(defer(Model.embedding))` on list and search queries to avoid large vector payload memory overheads.

---

## 3. Data Schema Standards

### Faculty Member Schema (`faculties` Table):
```json
{
  "id": "cmu_eng_ee_014",
  "university": "Chiang Mai University",
  "university_th": "มหาวิทยาลัยเชียงใหม่",
  "faculty": "Faculty of Engineering",
  "faculty_th": "คณะวิศวกรรมศาสตร์",
  "department": "Department of Electrical Engineering",
  "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
  "academic_title": "Asst. Prof. Dr.",
  "academic_title_th": "ผศ.ดร.",
  "first_name": "Watcharin",
  "last_name": "Srirattanawichaikul",
  "full_name": "Asst. Prof. Dr. Watcharin Srirattanawichaikul",
  "full_name_th": "ผศ.ดร. วัชริน ศรีรัตนาวิชัยกุล",
  "role": "Head of the Department of Electrical Engineering",
  "email": "watcharin.s@cmu.ac.th",
  "image_url": "https://ee.eng.cmu.ac.th/images/gallerys_content/b_20221129114143.png",
  "profile_url": "https://ee.eng.cmu.ac.th/web/personnel_detail.php?id=14",
  "education": [
    "D.Eng. (Electrical Engineering), Chiang Mai University",
    "M.Eng. (Electrical Engineering), Chiang Mai University"
  ],
  "research_interests": [
    "Power Electronics",
    "Microgrids and Renewable Energy"
  ],
  "featured_publications": [],
  "scholar_url": "http://apps2.lib.cmu.ac.th/scholars/profile/35305627600",
  "embedding_text": "Asst. Prof. Dr. Watcharin Srirattanawichaikul...",
  "embedding": [0.012, -0.045]
}
```

### Course / Curriculum Schema (`courses` Table):
```json
{
  "id": "cmu_ds_msc",
  "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูล",
  "title_en": "Master of Science Program in Data Science",
  "degree_level": "Master's Degree",
  "degree_name": "M.Sc. (Data Science)",
  "university": "Chiang Mai University",
  "university_th": "มหาวิทยาลัยเชียงใหม่",
  "faculty": "Faculty of Science",
  "faculty_th": "คณะวิทยาศาสตร์",
  "department": "Department of Computer Science",
  "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
  "program_type": "Regular / Special Program",
  "duration_years": "2 Years",
  "total_credits": "36 Credits",
  "tuition_per_semester": "45,000 THB",
  "tuition_total": "180,000 THB",
  "description": "Focuses on producing graduates specialized in Big Data Analytics, Machine Learning, and Cloud Computing...",
  "curriculum_highlights": [
    "Advanced Machine Learning & AI",
    "Big Data Infrastructure & Cloud Computing"
  ],
  "career_paths": ["Data Scientist", "ML Engineer"],
  "tags": ["Data Science", "AI & Machine Learning"],
  "website_url": "https://cs.science.cmu.ac.th"
}
```

---

## 4. Project Directory Structure

```text
Teacher/
├── AGENTS.md                     # Single authoritative guidelines & architecture (this file)
├── CLAUDE.md                     # Points to @AGENTS.md
├── DATA_SOURCES.md               # Documentation of data sources and scraping references
├── README.md                     # Project overview and setup instructions
├── render.yaml                   # Render deployment configuration
├── .gitignore
│
├── frontend/                     # Next.js 16 Super App UI
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx          # Dual Search (Courses & Advisors), Cold Email Modal
│   │   │   ├── advisor/[id]/     # Dynamic Advisor Profile page
│   │   │   │   └── page.tsx
│   │   │   ├── career-discovery/ # RIASEC AI Quiz page
│   │   │   │   └── page.tsx
│   │   │   └── globals.css
│   │   ├── components/           # Modular UI Components (Header, Footer, Cards, Modals)
│   │   ├── lib/
│   │   │   ├── config.ts         # Shared API configuration & global helpers
│   │   │   └── dsa.ts            # Client-side Data Structures & LRU Cache Engine
│   │   └── types/
│   │       └── index.ts          # Centralized TypeScript interfaces (Faculty, Course, Quiz)
│   ├── package.json
│   └── .env.local
│
├── backend/                      # Python FastAPI API & Scraping Engine
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_search.py  # AI Semantic Search & Cold Email API
│   │   │   ├── routes_faculty.py # Faculty directory API
│   │   │   ├── routes_courses.py # University course search & directory API
│   │   │   └── routes_career_quiz.py # Career discovery RIASEC quiz API
│   │   ├── core/
│   │   │   ├── config.py         # Application settings & environment variables
│   │   │   ├── database.py       # Supabase PostgreSQL connection
│   │   │   ├── dsa_utils.py      # Core Data Structures & Algorithms Library
│   │   │   ├── security.py       # Rate Limiter, Security Headers, Prompt Sanitizer
│   │   │   └── embedding_service.py # Gemini embeddings & query expansion
│   │   ├── models/
│   │   │   ├── schema.py         # Pydantic models for Search, Faculty, Course
│   │   │   ├── quiz_schema.py    # Pydantic models for RIASEC Quiz & Recommendations
│   │   │   └── db_models.py      # SQLAlchemy & PgVector models
│   │   └── main.py               # FastAPI entrypoint
│   │
│   ├── scripts/                  # Automation & Data Seeding
│   │   ├── seed_courses.py       # Seeds course curricula into Supabase
│   │   ├── init_db.py            # Initializes database tables & vectors
│   │   ├── update_scholar_serpapi.py
│   │   └── update_embeddings.py
│   ├── requirements.txt
│   └── .env
```

---

## 5. Development Guidelines & Best Practices

1. **Scraping Ethics & PDPA Compliance:**
   * Collect only publicly disclosed academic information and official institutional contact channels (e.g., official university email addresses).
   * **Never collect or store personal phone numbers.**
2. **Semantic Matching Quality:**
   * Utilize `text-embedding-004` / `gemini-embedding-2` with `pgvector` for calculating Cosine Similarity.
   * Implement Query Expansion (translating Thai terms to English academic equivalents) before generating embeddings to ensure cross-language semantic accuracy.
3. **Clean Architecture:**
   * Keep frontend UI logic in `frontend/src/app` and API/database logic in `backend/app`.

---

## 6. High-Performance & Anti-Bottleneck Architecture Standards

To ensure sub-second response times (< 500ms for searches, < 1.5s for AI generation) and zero bottlenecks across the stack, all agents and developers MUST strictly follow these design patterns:

### 1. AI & LLM Performance Rules
- **No Sequential LLM Loops:** NEVER call LLM APIs (Gemini) inside a loop across search candidate lists. Use intelligent contextual template generators (0ms latency), single-batch prompts, or on-demand loading.
- **In-Memory Embedding Caching:** Always cache query vector embeddings in an in-memory LRU cache (`_embedding_cache`) to achieve 0.001ms response times on frequent/repeated queries.
- **Client Pooling & Reuse:** Cache `genai.Client` instances by API key in a pool rather than instantiating new clients per HTTP request.
- **Fast Model Hierarchy:** Default to `gemini-3.6-flash` or `gemini-2.5-flash` for user-facing interactive endpoints (e.g., Cold Email, Quiz). Reserve Pro models strictly for offline batch tasks.
- **Parallel AI Execution:** In multi-step pipelines (such as the Career Discovery Quiz), execute LLM psychometric generation and course embedding concurrently using `ThreadPoolExecutor`.

### 2. Database & pgvector Optimization Rules
- **HNSW Vector Indexes:** Ensure `hnsw (embedding vector_cosine_ops)` indexes exist on `faculties` and `courses` tables.
- **Direct Vector Distance Ordering:** Use direct `ORDER BY embedding.cosine_distance(query_vector)` with `filter(embedding.isnot(None))` to activate PostgreSQL HNSW index scans. Never wrap distances in `func.coalesce()` or other expressions that force Full Table Scans.
- **GIN Trigram Indexing for Text:** Utilize the `pg_trgm` extension with GIN indexes on `title_th`, `faculty_th`, `full_name_th`, and `department_th` to accelerate `ILIKE '%...%'` queries.
- **Heavy Column Deferral:** Always apply `defer(Model.embedding)` and `defer(Model.embedding_text)` on search and list endpoints to avoid transferring 768-float arrays over the network.
- **Supabase Connection Pooling:** Configure SQLAlchemy with `pool_size=10, max_overflow=20, pool_recycle=300, pool_timeout=15, pool_pre_ping=True` to prevent idle connection drops and cold start penalties.

### 3. Backend & API Rules
- **Response Compression:** Always enable `GZipMiddleware(minimum_size=1000)` on FastAPI to compress JSON payloads by 70–85%.
- **Pre-compiled Regex:** Compile dictionary transformations and slang replacements (`re.compile`) once at module level for single-pass processing.
- **Concurrency Safety:** Define database/blocking endpoints as standard `def` to allow FastAPI/AnyIO to dispatch them to worker thread pools without blocking the main event loop.

### 4. Frontend & UI Performance Rules
- **Environment-based URLs:** Always reference `process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"`. Never hardcode `http://localhost:8000`.
- **Image Resilience:** Always add `loading="lazy"`, `decoding="async"`, and `onError` fallback handlers (e.g., UI-Avatars) to external university images to prevent layout shifts and broken states.
- **Instant Search on Interaction:** Clicking popular chips or quick tags must immediately trigger the search action rather than requiring an extra click.
- **Enforce Query Limits:** Always apply reasonable default pagination limits (`limit=24..50`) on list queries to keep frontend DOM node counts and memory lightweight.

### 5. Data Ingestion, Scraping & Batch Processing Rules
- **Multi-threaded Scraping:** Always use `ThreadPoolExecutor(max_workers=6..8)` when fetching faculty detail pages over HTTP instead of sequential blocking requests.
- **Immediate Embedding on Seeding:** Always compute and persist `embedding_text` and `embedding` vector (768-dim) directly during course seeding scripts so new records are instantly searchable via pgvector.
- **Batch Database Updates:** In automation scripts, use `Model.id.in_(batch_ids)` and commit once per batch to eliminate N+1 roundtrips to the database.
- **Targeted Scholar Enrichment:** Only process records missing publication data (`featured_publications == None | []`) and commit in chunks to avoid redundant SerpApi queries.

### 6. Fallback Search & Query Protection Rules
- **SQL Pre-filtering for Fallbacks:** In lexical/keyword fallback algorithms, always apply `filter(or_(*filters)).limit(...)` at the SQL level. NEVER call `.all()` on an unconstrained table to loop over in Python memory.

### 7. DRY (Don't Repeat Yourself) & Code Redundancy Elimination Standards
- **Centralized Frontend Contracts:** NEVER define duplicate TypeScript `interface` or `type` blocks in individual page components. Always import from `@/types` (`frontend/src/types/index.ts`).
- **Single Source for API URLs & Asset Helpers:** Always import `API_BASE_URL` and avatar/image fallback helpers from `@/lib/config` instead of re-declaring environment variables or fallback templates in multiple files.
- **No Dead Backend Endpoints:** Maintain zero dead routes in FastAPI `main.py` (e.g., static template mountings when the frontend is decoupled as Next.js).
- **No Redundant Wrapper Methods:** Avoid pass-through wrapper functions with zero added logic (e.g., `_generate_explanation` calling `generate_smart_explanation`). Direct callers straight to the canonical implementation.

### 8. AI Semantic Advisor & Academic Matching Standards
To deliver enterprise-grade academic matching without hallucination or slow response times, follow these standards:
- **Cross-Disciplinary Academic Ontology:** Maintain a single-pass regex compiled ontology (`THAI_EN_SYNONYMS` + `_SYNONYM_REGEX`) in `embedding_service.py` to translate Thai research inquiries into global academic taxonomy (AI/NLP, Energy/Microgrid, Biomedical/Genomics, Quant Finance, Robotics) before vector embedding.
- **Hybrid Multi-Evidence Re-ranking:** Do NOT rely purely on cosine distance. Always apply a 4-tier composite score:
  1. *Dense Semantic Similarity:* Gemini 768-dimensional vector cosine distance with `pgvector` HNSW index scans.
  2. *Core Research Interests Match:* Explicit alignment with listed research domains.
  3. *Publication Synergy:* Scan past paper titles (`featured_publications`) to detect actual published track records.
  4. *Academic Track Record & Credentials:* Reward verified Google Scholar profiles and doctoral advisory qualifications.
- **Contextual Synergy Badges & Thesis Angles:**
  - Auto-generate *Synergy Badges* (e.g., `⭐ Direct Research Focus`, `📄 Relevant Publications`, `🏆 International Scholar`, `🎓 Doctoral Advisor`).
  - Provide actionable *Suggested Thesis Angles* showing how the student's proposal integrates with the advisor's methodology.
- **Zero-Latency Rationale Generation:** Synthesize explanations locally using contextual multi-evidence templates citing actual publication titles without making synchronous LLM API roundtrips during candidate ranking.
- **Decoupled Tab State & Dual Catalog Hydration:** Switching tabs between Curricula and Advisors must NEVER trigger unintended automatic searches. Hydrate initial catalog data concurrently via `Promise.allSettled`.

---

## 7. Data Structures & Algorithms (DSA) Standards

To ensure optimal computational time and space complexity across both backend and frontend systems, all developers and agents MUST follow these DSA architectural patterns:

### 1. True $O(1)$ LRU Caching (Doubly Linked List + Hash Map)
- **Backend Vector Cache (`backend/app/core/dsa_utils.py`):** Use `LRUCache[K, V]` with sentinel pseudo-head and pseudo-tail nodes combined with a hash map. Guarantees true $O(1)$ time complexity for `.get()`, `.put()`, and least-recently-used node evictions without resizing or linear scan overheads.
- **Frontend Client-side Cache (`frontend/src/lib/dsa.ts`):** Maintain `ClientLRUCache` to instantly return previously executed search queries and faculty profile detail pages in $0\text{ms}$ ($O(1)$), preventing redundant network roundtrips.

### 2. $O(N \log K)$ Top-K Bounded Min-Heap Re-Ranking
- **Top-K Element Collector (`TopKHeap`):** When ranking search results, advisors, or courses, NEVER sort the entire candidate pool of size $N$ in $O(N \log N)$.
- **Heap Maintenance:** Maintain a Min-Heap of fixed size $K$. For each incoming candidate score, perform a comparison with the minimum element in $O(1)$ and `heapreplace` in $O(\log K)$ time. Space complexity is strictly bounded to $O(K)$.

### 3. $O(L)$ Trie (Prefix Tree) & Multi-Pattern Keyword Matching
- **Keyword & Prefix Indexing (`Trie`):** Index academic terminology, faculty interests, and taxonomy into a Trie to achieve $O(L)$ search and prefix lookup time (where $L$ is word length), eliminating $O(M \cdot L)$ linear scanning overheads across large dictionaries.
- **Set-based $O(1)$ De-duplication:** Always use hash sets (`set()`) for matching interests, publication hits, and synergy badges during scoring loops to prevent $O(N^2)$ nested lookups.

### 4. Fast Inverted Indexing (`FastInvertedIndex`)
- **Token Posting Lists:** For lexical keyword fallbacks, maintain an in-memory token posting list with term frequency (TF) and inverse document frequency (IDF) weighting for sub-millisecond document scoring.

---

## 8. Cybersecurity & System Hardening Standards

To protect against OWASP Top 10 vulnerabilities, API abuse, and LLM-specific threats (OWASP Top 10 for LLM Applications), all developers and agents MUST strictly adhere to these cybersecurity standards:

### 1. API Protection & Rate Limiting (DoS Mitigation)
- **Sliding-Window Rate Limiting (`RateLimitMiddleware`):** All public API endpoints MUST be protected by IP-based rate limiting (`RateLimiter`, 180 req/min per client IP).
- **HTTP 429 & Retry-After:** Rejected excessive traffic MUST return HTTP `429 Too Many Requests` with a valid `Retry-After: 60` header and structured JSON error response.

### 2. Strict Cross-Origin Resource Sharing (CORS) Policy
- **No Wildcard with Credentials:** NEVER use wildcard `allow_origins=["*"]` or open regex `r"^https?://.*"` on endpoints that handle user data.
- **Whitelisted Origins:** Explicitly declare authorized origins (e.g., `http://localhost:3000`, `https://*.vercel.app`, `https://*.render.com`). Restrict allowed HTTP methods strictly to `GET`, `POST`, and `OPTIONS`.

### 3. OWASP Security Response Headers (`SecurityHeadersMiddleware`)
All HTTP responses MUST inject the following security headers:
- `X-Content-Type-Options: nosniff` (Mitigates MIME sniffing attacks).
- `X-Frame-Options: DENY` (Mitigates UI redressing and Clickjacking).
- `X-XSS-Protection: 1; mode=block` (Legacy cross-site scripting filter).
- `Referrer-Policy: strict-origin-when-cross-origin` (Protects user referral privacy).
- `Permissions-Policy: camera=(), microphone=(), geolocation=()` (Restricts browser device access).

### 4. AI & LLM Prompt Injection Defense (OWASP LLM01)
- **Prompt Sanitization Engine (`sanitize_for_prompt`):** User inputs (e.g., student name, thesis proposal, background) injected into LLM prompts MUST be sanitized:
  - Detect and neutralize instruction overrides (e.g., `ignore previous instructions`, `system: you are`, `DAN mode`, `reveal system prompt`).
  - Strip null bytes (`\x00`) and malicious ASCII control characters.
- **System Prompt Boundary Isolation:** System instructions MUST contain explicit defense boundaries instructing the model to treat user fields strictly as data, ignoring embedded commands.

### 5. PDPA & Privacy Protection (PII Redaction)
- **Automated PII Masking:** Automatically redact sensitive identifiers (e.g., Thai 13-digit National ID `\b[1-9]\d{12}\b`, credit card patterns, and API keys) before passing text to third-party LLM APIs.
- **Public Data Compliance:** Never collect or persist personal phone numbers or private non-academic contact details.

### 6. Strict Input Validation & Schema Constraints
- **Pydantic v2 DTO Hardening:** Every incoming request field MUST declare explicit validation boundaries:
  - `min_length` and `max_length` to prevent payload inflation and buffer exhaustion.
  - Regex `pattern` enforcement on enumeration fields (e.g., `tier: pattern=r"^(quick|standard|deep)$"`).
  - Numeric boundary constraints (`ge`, `le`) on pagination and scoring values.

### 7. Frontend Web Security & Reverse Tabnabbing Prevention
- **Safe External Anchors:** Every external link opening in a new tab (`target="_blank"`) MUST include `rel="noopener noreferrer"` to prevent window opener hijacking (Reverse Tabnabbing).
- **Layout Security Headers:** Declare Content Security Policy and security metadata at the Root Layout level (`frontend/src/app/layout.tsx`).
