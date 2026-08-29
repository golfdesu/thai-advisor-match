# Thai EduCenter & Advisor Match - Project Guidelines & Architecture

## 1. Project Overview & Vision
**Thai EduCenter** (incorporating **Thai Advisor Match**) is an all-in-one AI-powered educational discovery platform designed for prospective undergraduate and graduate students (Bachelor's, Master's, and Ph.D. candidates) in Thailand.

### Core Features:
1. **University Curriculum & Course Directory:** Comprehensive search and exploration of academic programs across Thai universities (tuition fees, duration, credits, and career paths).
2. **AI Semantic Advisor Matching:** Students input their thesis topics, abstracts, or ideas. The platform semantically indexes, matches, and ranks faculty members and universities with the highest alignment, displaying a % Match Score.
3. **AI Match Explanation:** Automatically synthesizes concise explanations of why a specific professor is an ideal match for the student's research direction.
4. **Comprehensive Profiles:** Academic background, research interests, supervised courses, publication links, and official contact channels.
5. **AI Cold Email Generator:** An AI assistant that drafts professional inquiry emails and research proposals for contacting prospective advisors in Thai and English.

---

## 2. Tech Stack & Architecture (Monorepo)

```
[ Frontend: Next.js 16 / React / TypeScript / Tailwind CSS (Port 3000) ]
                          ↕ (REST API JSON)
[ Backend: Python FastAPI / Uvicorn (Port 8000) ]
                          ↕
[ AI Layer: Gemini API / Embeddings ] ↔ [ Database: PostgreSQL + pgvector (Supabase) ]
```

* **Frontend (`/frontend`):**
  * **Framework:** Next.js (App Router, TypeScript, React 19).
  * **Styling & UI:** Tailwind CSS, Lucide React Icons.
* **Backend (`/backend`):**
  * **Framework:** Python 3.12 (FastAPI, Uvicorn, SQLAlchemy, Pydantic v2).
  * **AI & NLP:** Google Gemini API (`text-embedding-004`), PgVector Cosine Similarity, Query Expansion.
  * **Scraping Engine:** `requests`, `beautifulsoup4`, SerpApi (Google Scholar).
* **Database & Vector Store:**
  * **Production:** PostgreSQL + `pgvector` hosted on **Supabase**.

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
  "embedding": [0.012, -0.045, ...]
}
```

### Course / Curriculum Schema (`courses` Table):
```json
{
  "id": "cmu_ds_msc",
  "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูล",
  "title_en": "Master of Science Program in Data Science",
  "degree_level": "ปริญญาโท",
  "degree_name": "วท.ม. (วิทยาการข้อมูล)",
  "university": "Chiang Mai University",
  "university_th": "มหาวิทยาลัยเชียงใหม่",
  "faculty": "Faculty of Science",
  "faculty_th": "คณะวิทยาศาสตร์",
  "department": "Department of Computer Science",
  "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
  "program_type": "ภาคปกติ / ภาคพิเศษ",
  "duration_years": "2 ปี",
  "total_credits": "36 หน่วยกิต",
  "tuition_per_semester": "45,000 บาท",
  "tuition_total": "180,000 บาท",
  "description": "เน้นการผลิตบัณฑิตที่มีความรู้ความเชี่ยวชาญด้าน Big Data Analytics, Machine Learning...",
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
├── AGENTS.md                     # Authoritative guidelines & architecture for AI agents
├── CLAUDE.md                     # Identical guidelines for Claude Code & Anthropic models
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
│   │   ├── lib/
│   │   │   └── config.ts         # Shared API configuration & global helpers
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
│   │   │   └── routes_courses.py # University course search & directory API
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py       # Supabase PostgreSQL connection
│   │   │   └── embedding_service.py # Gemini embeddings & query expansion
│   │   ├── models/
│   │   │   ├── schema.py         # Pydantic models
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
- **Fast Model Hierarchy:** Default to `gemini-3.6-flash` or `gemini-2.5-flash` for user-facing interactive endpoints (e.g. Cold Email, Quiz). Reserve Pro models strictly for offline tasks.
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
- **Image Resilience:** Always add `loading="lazy"`, `decoding="async"`, and `onError` fallback handlers (e.g. UI-Avatars) to external university images to prevent layout shifts and broken states.
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
- **No Dead Backend Endpoints:** Maintain zero dead routes in FastAPI `main.py` (e.g. static template mountings when the frontend is decoupled as Next.js).
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



