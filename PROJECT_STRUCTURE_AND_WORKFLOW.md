# Thai EduCenter & Advisor Match: Project Structure, Workflow & Master Runbook

> **For AI Models and Developers joining in a new session:**
> This document is the **Single Source of Truth** compiling directory indexes, system architecture, Standard Operating Procedures (SOP), security invariants, and audited bug-prevention rules. Read and adhere to this document strictly.

---

## 1. Project Mission & Overview

**Thai EduCenter** (incorporating **Thai Advisor Match**) is a higher-education discovery platform for graduate programs (Master's and Ph.D.) and faculty advisors in Thailand. The system provides:
1. **AI Semantic Advisor Matching:** Matches thesis topics and research abstracts (in Thai and English) with prospective advisors, calculating a % Match Score via `pgvector` and Gemini 768-dimensional embeddings.
2. **Curriculum & Tuition Discovery:** Enables searching academic programs, tuition fees, program duration, credit requirements, and career pathways.
3. **Research Labs Interlinking:** Explores national flagship research laboratories (104 Labs) with bidirectional linking to lead advisors.
4. **RIASEC Career Discovery Quiz:** A 3-tier psychological assessment aligning students with fitting academic disciplines and research specializations.

---

## 2. Project Directory Index & Table of Contents

```text
Teacher/
├── CHANGELOG.md                                   # Chronological changelog of releases, schema updates, and audits
├── compose.yaml                                   # Docker Compose Spec: PostgreSQL 17 + pgvector + pgAdmin 4
├── PROJECT_STRUCTURE_AND_WORKFLOW.md             # [This Document] Master architecture, workflow, and index
├── README.md                                      # Project overview and quickstart guide
├── AGENTS.md / CLAUDE.md                          # Absolute operational invariants and rules for AI agents
│
├── docker/
│   └── init.sql                                   # Database initialization (Extensions, Schemas, HNSW & GIN Indexes)
│
├── frontend/                                      # Next.js 16 Super App UI (Port 3000)
│   ├── package.json                               # Next.js 16, React 19, Lucide React, Tailwind CSS v4
│   ├── next.config.ts                             # Image domain allowlists (ac.th, unsplash, avatars)
│   ├── tsconfig.json                              # Path alias @/* pointing to ./src/*
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                         # Root Layout, Theme Providers, Head Scripts
│       │   ├── page.tsx                           # Landing page (Hero, Quick Search, Popular Chips)
│       │   ├── globals.css                        # Tailwind v4 Directives (@import "tailwindcss"; @theme)
│       │   ├── advisor/[id]/page.tsx              # Advisor profile page (Metrics, Graph, Works, Interests)
│       │   ├── labs/[id]/page.tsx                 # Research Lab detail page (Equipment, Members)
│       │   └── career-discovery/page.tsx          # RIASEC Career Discovery Quiz page
│       ├── components/
│       │   ├── AdvisorCard.tsx                    # Advisor card + Synergy Badges + Match Tier Badges
│       │   ├── CourseCard.tsx                     # Academic curriculum card
│       │   ├── LabCard.tsx                        # Research laboratory card
│       │   ├── FilterBar.tsx                      # Filters for University, Faculty, Region, and Tier
│       │   ├── Header.tsx / Footer.tsx            # Global application header and footer
│       │   └── ...                                # Modal and helper UI components
│       ├── lib/
│       │   ├── config.ts                          # API Base URLs, avatar helpers, external links
│       │   └── dsa.ts                             # Client-side LRU Cache for query responses
│       └── types/
│           └── index.ts                           # Central TypeScript interfaces (Single Source of Truth)
│
├── backend/                                       # FastAPI API & Scraping Engine (Port 8000)
│   ├── requirements.txt                           # fastapi, sqlalchemy, pgvector, google-genai, rapidfuzz
│   ├── app/
│   │   ├── main.py                                # FastAPI App, Middleware (CORS, GZip, RateLimit), LifeSpan
│   │   ├── core/
│   │   │   ├── config.py                          # Pydantic Settings, DB URLs, GEMINI_API_KEYS
│   │   │   ├── database.py                        # SQLAlchemy SessionLocal, Engine
│   │   │   ├── dsa_utils.py                       # True O(1) LRUCache, TopKHeap, Trie
│   │   │   ├── embedding_service.py               # Gemini 768-dim Embedding Service + In-Memory LRU Cache
│   │   │   └── security.py                        # OWASP Headers, Input Sanitization, National ID Redaction
│   │   ├── models/
│   │   │   ├── db_models.py                       # SQLAlchemy Models (FacultyDB, CourseDB, ResearchLabDB)
│   │   │   └── schema.py                          # Pydantic DTOs (FacultyResponse, SearchQuery, LabResponse)
│   │   └── api/
│   │       ├── routes_search.py                   # Semantic & Lexical Hybrid Search (pgvector HNSW + BM25)
│   │       ├── routes_faculty.py                  # Faculty retrieval, directory listing, and filters
│   │       ├── routes_courses.py                  # Curriculum and tuition discovery API
│   │       ├── routes_labs.py                     # Research labs and advisor interlinking API
│   │       └── routes_career_quiz.py              # RIASEC Quiz processing API
│   │
│   ├── data/
│   │   └── agent_states/                          # Checkpointed Extraction State JSONs (Waves 1 to 20)
│   │       ├── wave17_ku_forest_extracted.json
│   │       ├── wave18_ku_forest_regional_extracted.json
│   │       ├── wave19_cu_gaps_extracted.json
│   │       ├── wave20_enames_candidates.json     # W20: id -> EN name tiers + confidence
│   │       ├── wave20_kuforest_en.json           # W20: KUForest pid -> EN name (postback harvest)
│   │       └── wave20_apply_log.json             # W20: rollback journal of overwritten names
│   │
│   ├── scripts/                                   # Automation Scripts & Pipelines
│   │   ├── agentic_pipeline/                      # Autonomous SKILL.state Extraction Engine
│   │   │   ├── state_reducer.py                   # Prefix stripper (Thai/EN), RapidFuzz Dedup, Merge Logic
│   │   │   ├── content_pruner.py                  # HTML boilerplate stripper (Trafilatura)
│   │   │   ├── run_acquire.py                     # Shorthand CLI runner for fast acquisition
│   │   │   └── cli_runner.py                      # Full CLI Runner for Autonomous Pipeline
│   │   ├── dream_rsi/                             # Dream-RSI Adaptation (Replay Simulators & Offline Policy Tuning)
│   │   │   ├── simulator_faculty_recovery.py      # Replay simulator for faculty email discovery (Zero Network/LLM cost)
│   │   │   ├── simulator_dedup_policy.py          # Replay simulator for Entity Resolution & 3-Pass Dedup tuning
│   │   │   └── benchmark_dsa_engineering.py       # Algorithmic Engineering Harness + 100% Bit-level Parity Verification
│   │   ├── crawlers/                              # Targeted Web Crawlers segmented by Wave
│   │   │   ├── crawl_wave13_flagships.py          # Intania CU, KU Science, PSU Agro
│   │   │   ├── crawl_wave14_flagships.py          # MU Science, KKU Science, KKU Agri, CU Science
│   │   │   ├── crawl_wave15_flagships.py          # CU Dent, CU AHS, PSU Med, KU Agro, KU Vet, KU Forestry
│   │   │   ├── crawl_wave16_flagships.py          # KMITL AAD, KMITL SIET, CU Pharm, KKU Pharm, TSE
│   │   │   ├── crawl_wave17_ku_forest.py          # KU Forest: Social Sci, Humanities, Business, Econ, Environment, Vet Tech
│   │   │   ├── crawl_wave18_ku_forest_regional.py # KU Forest Closeout: remaining Bang Khen + KPS/Sriracha/Sakon Nakhon
│   │   │   └── crawl_wave19_cu_gaps.py            # CU Gap Closeout: Law, PolSci, Econ, Edu (API), Psy rosters
│   │   ├── audits/                                # Database Hygiene & Audit Tools
│   │   │   ├── verify_db_stats.py                 # Verifies record counts and detects null embeddings
│   │   │   ├── verify_zero_defect_baseline.py     # 10-dimensional zero-defect audit runner
│   │   │   └── merge_duplicate_faculties.py       # Canonical 3-pass deduplication and merging tool
│   │   ├── enrichment/                            # Data Enrichment & Discovery
│   │   │   ├── discover_unlisted_faculty.py       # OpenAlex 2024-2026 unlisted faculty discovery + quarantine
│   │   │   └── audit_former_faculty.py            # Emeritus and former faculty audit runner
│   │   ├── migrate_supabase_to_local.py           # Supabase to Local Docker PostgreSQL hydration stream
│   │   ├── enrich_wave20_english_names.py         # W20: 6-tier English name discovery + journaled apply
│   │   ├── enrich_openalex_author_metrics.py      # OpenAlex probe: h-index/citations (sentinel + canary)
│   │   └── sync_local_to_supabase.py              # Synchronizes verified local data to production Supabase
│   │
│   └── tests/                                     # Pytest Test Suite
│       ├── test_search.py                         # Tests Search API, Filters, Lab Interlinking, Match Tiers
│       ├── test_agentic_pipeline.py               # Tests State Reducer, Title Stripping, PDPA Redaction
│       ├── test_audited_bug_regressions.py        # Tests preventing 10 core audited bug regressions
│       ├── test_taxonomy_and_regional_search.py   # Tests taxonomy classification and regional search
│       ├── test_wikiskill.py                      # Tests WikiSkill Layer 1-3 Architecture
│       └── test_dream_rsi_simulators.py           # Tests Dream-RSI Replay Simulators & Parity Harness
│
├── .claude/ & .agents/                            # Long-term Memory, WikiSkill & Native Domain Skills
│   ├── skills/                                    # Native Active Agent Skills
│   │   ├── skill-state/SKILL.md                   # Mandatory headless data acquisition skill (run_acquire.py)
│   │   ├── faculty-audit/SKILL.md                 # 10-dimensional faculty data quality audit (Zero-Defect)
│   │   ├── faculty-discover/SKILL.md              # Stage 6 unlisted faculty discovery (OpenAlex 2024-2026 + Quarantine)
│   │   ├── db-optimize/SKILL.md                   # PostgreSQL 17 + pgvector tuning (HNSW, GIN, Defer)
│   │   ├── data-acquire-faculty-elites/SKILL.md   # National & university outstanding faculty acquisition
│   │   ├── data-acquire-academic/SKILL.md         # Curriculum, course metadata, and academic discovery
│   │   └── data-curriculum-tuition-discovery/     # Tuition discovery and academic program search
│   ├── wiki/                                      # WikiSkill Persistent Knowledge (universities & patterns)
│   │   ├── WIKI_INDEX.md                          # Master index of compiled WikiSkill knowledge
│   │   ├── universities/                          # University faculty directory structures and endpoints
│   │   └── patterns/                              # Extraction patterns, edge cases, and cleaning rules
│   └── raw_traces/                                # Immutable Execution Traces (Layer 1)
│
└── memory/                                        # Persistent Context Memory
    ├── MEMORY.md                                  # Auto-memory index
    ├── top-5-universities-zero-defect-baseline.md # 9,642 Top 5 faculty zero-defect verification baseline
    ├── faculty-data-recovery-patterns.md          # Master runbook for 5-stage audit and 5-step unlisted discovery
    ├── hold-supabase-sync-until-local-complete.md # Local-First Zero-Egress Invariant rule
    ├── antipatterns-and-bug-prevention.md         # Audited bug prevention and quality invariants
    └── native-skills-architecture.md              # Documentation of 4 native Claude Code / Agent skills
```

---

## 3. Core Technology Stack & Architectural Contracts

### 3.1 Frontend (Next.js 16 + React 19 + Tailwind CSS v4)
* **Tailwind CSS v4:** Configured via CSS Directives in `frontend/src/app/globals.css` (using `@import "tailwindcss";` and `@theme`, **`tailwind.config.js` is strictly forbidden**).
* **App Router & Client Components:** Interactive components using React hooks (`useState`, `useEffect`, `useRouter`, `useSearchParams`) MUST declare `"use client";` at the top of the file.
* **Image Optimization (Zero Cumulative Layout Shift - CLS = 0):**
  * Do not use standard `<img>` tags. Always use `<Image />` from `next/image`.
  * Specify explicit `width`/`height` or use `fill` within a `relative` container along with a descriptive `sizes` attribute.
  * Always provide a clean fallback via `getAdvisorAvatarUrl(name)` when the remote image fails to load.
  * Whitelist remote image domains in `next.config.ts` (e.g. `**.ac.th`, `**.edu`, `images.unsplash.com`, `ui-avatars.com`).
* **TypeScript Strictness:** Never declare duplicate `interface` or `type` blocks in individual components. Always import contracts from `@/types`.

### 3.2 Backend (FastAPI + SQLAlchemy 2.0 + Pydantic v2)
* **Python 3.12+ Syntax:** Use standard type annotations (`str | None`, `list[str]`).
* **Pydantic v2:**
  * Use `model.model_dump()` and `model.model_dump_json()` (never deprecated `dict()` or `json()`).
  * Validate using `@field_validator("field", mode="before")`.
  * For SQLAlchemy ORM model conversions, use `ConfigDict(from_attributes=True)`.
* **High-Performance DSA Primitives:**
  * Use `TopKHeap` (Min-Heap $O(N \log K)$) to filter top candidates instead of sorting the entire candidate array ($O(N \log N)$).
  * Use backend `LRUCache` to store query vector embeddings for 0.001ms repeated lookups.
  * Enable `GZipMiddleware(minimum_size=1000)` to compress API payloads by 75–85%.

### 3.3 Database & Vector Search (Local PostgreSQL 17 + pgvector)
* **Local-First Zero-Egress Invariant:** All crawling, state reduction, deduplication, vector embedding generation, and commits **MUST run against the local Docker PostgreSQL database (`localhost:5432/advisor_match`)**. Never stream high-throughput ingestion pipelines directly against remote Supabase to protect egress bandwidth quotas.
* **Vector Embeddings:** 768-dimensional float arrays generated via Google Gemini (`gemini-embedding-2` or fallback `gemini-embedding-001`).
* **Database Indexes:**
  * HNSW Cosine Distance Index for vector search: `ix_faculties_embedding_hnsw`
  * GIN Trigram Index for Thai text search: `idx_faculties_name_th_trgm`

---

## 4. Standard Data Acquisition SOP Lifecycle (5-Pillar High-Throughput Standard)

When tasked with acquiring faculty or academic data for a wave, you must adhere strictly to the **5-Pillar High-Throughput Lifecycle**. **Never skip steps, never crawl in chat, and never fabricate synthetic data**:

```text
[Pillar 1 & 2: Headless Python Crawl + OpenAlex Multiplexer]
           ↓ (ThreadPoolExecutor 5-8 workers | 200 authors/request)
[Pillar 4: In-Memory 5-Pass State Reduction & RapidFuzz Dedup]
           ↓ (Email -> OpenAlex ID -> Thai exact -> EN exact -> Fuzzy >= 90)
[Pillar 5: Disk Checkpointing] -> backend/data/agent_states/waveXX_extracted.json
           ↓ (Immutable Recovery Point & Resumability)
[Pillar 3: Multi-Client Vectorization with Circuit Breaker]
           ↓ (On 3x 429: Fallback to [0.0]*768 to commit without hanging)
[Step 5: Local DB Commit & Autonomous Verification] -> PostgreSQL 17 (Tests + Next.js Build)
```

### Detailed Phase Execution:
1. **Step 1: OpenAlex Multiplexing & Headless Crawling (Pillars 1 & 2):**
   * **OpenAlex-First Strategy:** For any university expansion, always query OpenAlex API first (`per-page=200`) using verified Institution IDs to ingest thousands of verified faculty records with citations, h-index, and publication works in minutes.
   * **Targeted Web Crawl (Phase B):** Use headless Python scripts with `ThreadPoolExecutor(max_workers=5..8)` for HTML crawling via Trafilatura to recover official emails and department rosters.
   * **Zero In-Chat Crawling:** Strictly forbidden to fetch pages or parse DOM in conversation turns (keeps token footprint <2,000 tokens/turn).
2. **Step 2: In-Memory 5-Pass State Reduction & Normalization (Pillar 4):**
   * Execute `strip_all_titles(name)` and `normalize_thai_title_and_name(raw_name)`.
   * Run 5-pass in-memory deduplication entirely in Python without calling LLMs:
     - Pass 1: Normalized Thai Full Name (`full_name_th`)
     - Pass 2: Clean English Full Name (`first_name_en` + `last_name_en`)
     - Pass 3: Verified Non-Shared Academic Email (excluding info@, dean@)
     - Pass 4: OpenAlex Author ID (`openalex_id`)
     - Pass 5: RapidFuzz token_sort_ratio >= 90
   * If existing: **Enrich** the existing record (add missing email, image, union research interests, max citations/h-index) without creating duplicate rows.
   * If new: Append to **New Members** for vectorization.
3. **Step 3: Disk Checkpointing & Resumability (Pillar 5):**
   * Checkpoint the raw extracted state to `backend/data/agent_states/waveXX_<univ>_extraction.json` immediately to guarantee zero data loss and instant resume on network drops or process interruptions.
4. **Step 4: Vectorization with Non-blocking Circuit Breaker (Pillar 3):**
   * Pool `genai.Client` instances using keys in `settings.GEMINI_API_KEYS`.
   * Use `ThreadPoolExecutor` with Key Rotation and Exponential Backoff (30s -> 60s -> 90s -> 180s on HTTP 429).
   * **Non-blocking Circuit Breaker:** If 3 consecutive 429 errors occur, trip the circuit breaker and fallback to dummy vector `[0.0] * 768`. Commit the records to PostgreSQL immediately; never hang or block the ingestion pipeline. Log IDs for background re-embedding.
5. **Step 5: Bulk Database Commit & Autonomous Verification:**
   * Commit the batch to local PostgreSQL (`localhost:5432`).
   * Run backend test suite: `pytest backend/tests -v`.
   * Run frontend build: `npm --prefix frontend run build` (must compile cleanly with zero errors).
   * Update `CHANGELOG.md` and relevant roadmap files.

---

## 5. Absolute Operational Invariants & Antipatterns

### 1. No Synthetic Data Generation (Strict Real-World Grounding)
* Never manually synthesize or hallucinate faculty members, departments, or research outputs in code. All data must originate from authentic university directories or verified OpenAlex scholarly profiles.

### 2. Thai Regex Boundary Delimiter Safety
* **Never use `r"ดร\.?"`:** Thai does not use whitespace between words. An optional period `?` causes greedy matches on common Thai names starting with "ดร" (e.g. "ดรุณี", "ดรัลพร"), truncating them to "ุณี" and "ัลพร".
* **Safe Pattern:** Always require an explicit period or whitespace delimiter: `r"ดร\."` or `r"ดร\s+"`.

### 3. Defensive Python & ORM Coding
* **Defensive Null-Coalescing:** Database JSON, Array, and Text columns can be `None`. Never slice `db_obj.field[:3]` directly; always coalesce: `(db_obj.field or [])[:3]` to avoid runtime `TypeError` (HTTP 500).
* **Memory-Conscious Queries:** Never perform unconstrained `db.query(FacultyDB).all()` across thousands of 768-dim float arrays. Use `options(defer(FacultyDB.embedding)).yield_per(500)` when scanning scalar fields.
* **Pydantic v2 List Coercion:** When LLMs return JSON, list fields may be `null`. Pydantic v2 rejects `None` even with `default_factory=list`. Declare `@field_validator("...", mode="before")` to coerce `None` to `[]`.

### 4. Frontend & Next.js 16 Standards
* **Hydration Mismatch Defense:** Never access `localStorage` or `window` for initial state. Use the Mounted Pattern (`const [mounted, setMounted] = useState(false)`).
* **No Direct DOM Mutation:** Never write `e.target.src = ...` for image fallbacks. Use declarative React state flags to switch to fallback avatar URLs cleanly.

---

## 6. CLI Commands Cheat Sheet

### 6.1 Development Startup
```powershell
# 1. Start Database Container (PostgreSQL 17 + pgvector)
docker compose up -d

# 2. Start Backend API (FastAPI)
cd backend
$env:PYTHONPATH='.'
python -m uvicorn app.main:app --reload --port 8000

# 3. Start Frontend UI (Next.js 16)
cd frontend
npm run dev
```

### 6.2 System Verification Protocol
```powershell
# Run complete backend test suite (34 Tests)
pytest backend/tests -v

# Run production frontend build
npm --prefix frontend run build

# Verify faculty record counts and check for null embeddings in database
$env:PYTHONPATH='backend'; python -c "from app.core.database import SessionLocal; from app.models.db_models import FacultyDB; db = SessionLocal(); print('Total:', db.query(FacultyDB).count(), '| Null Embeddings:', db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()); db.close()"

# Automatically synchronize live database statistics to Section 7.1
python backend/scripts/audits/sync_system_status.py
```

### 6.3 Executing Ingestion & Crawlers
```powershell
# Run crawler script for targeted faculty acquisition
python backend/scripts/crawlers/crawl_wave16_flagships.py

# Run shorthand autonomous SKILL.state pipeline
python backend/scripts/agentic_pipeline/run_acquire.py --url https://www.eng.chula.ac.th/th/about/faculty --univ CU --fac Engineering
```

---

## 7. Current System Status & Next Acquisition Waves

### 7.1 Current System Status (As of 2026-09-22)
* **Faculty & Researchers in Local DB:** **171,626 records** (Post-Stage 6 Unlisted Discovery, 10-Dimensional Zero-Defect Baseline).
* **Missing Vector Embeddings:** **0 records** (100% 768-dimensional vector completeness).
* **OpenAlex-resolved Scholars:** **171,626 records** (100.0%) | h-index > 0: **137,350** | Elite advisors (h >= 20 or citations >= 1,000): **17,731** | Total citations: **146.59 Million** (146,586,744).
* **Romanized English Names from Institutional Sources:** **166,826 records** (97.2% Latin first/last name coverage).
* **Official Academic Emails:** **16,312 records** (9.5% verified institutional emails, 0 personal freemails, 0 personal phone numbers per PDPA).
* **National Flagship Research Laboratories:** **104 Labs** (100% bidirectional advisor linking).
* **Graduate Academic Programs:** **4,234 curricula** across Thai universities.
* **Top 10 Universities by Faculty Count:**
  1. Chulalongkorn University (CU): 12,875
  2. Kasetsart University (KU): 12,797
  3. Mahidol University (MU): 12,397
  4. Prince of Songkla University (PSU): 12,113
  5. Chiang Mai University (CMU): 12,034
  6. Khon Kaen University (KKU): 11,862
  7. Thammasat University (TU): 10,868
  8. King Mongkut's Institute of Technology Ladkrabang (KMITL): 9,355
  9. King Mongkut's University of Technology Thonburi (KMUTT): 8,351
  10. Srinakharinwirot University (SWU): 5,144
### 7.2 Roadmap & Objectives for Next Waves
* **Completed Milestones (through 2026-09-20):**
  - **Phases 21–35 Email Recovery:** Recovered authentic official academic emails across KMUTT Microbiology (`mic.kmutt.ac.th`), SIT (`sit.kmutt.ac.th`), SUT Engineering, MJU Agriculture, NIDA Applied Statistics, and Naresuan University.
  - **Stage 6 Unlisted & New Faculty Discovery:** Discovered 30 high-impact researchers across CU and CMU via OpenAlex 2024–2026 publication footprints, overcoming central directory lag with objective confidence scoring (>= 0.85).
  - **10-Dimensional Zero-Defect Audit Protocol:** Enforced complete name hygiene, Latin script purity, MHESI thesis advisor eligibility purging (retired, emeritus, on-leave), and 3-pass deduplication across Top 5 universities.
  - **Graded Placement Tiers (TypeSafe Ordered Tier Pattern):** Integrated Tier 1–4 advisory placement badges directly into search results (`SearchMatchResult`).
* **Active Action Items & Next Objectives:**
  1. **Phase 36 Official Email Recovery:** Continue systematic recovery of remaining unexamined faculty clusters using headless `SKILL.state` runners.
  2. **Regional University Expansion:** Ingest and enrich graduate faculties and curricula for underrepresented regional institutions (PSU regional campuses, Silpakorn University, Srinakharinwirot University, Burapha University, Mae Fah Luang University).
  3. **High-Demand Discipline Top Scholars:** Target elite faculty acquisition for high-demand Master's disciplines identified in MHESI benchmarks (Education, Law, M.P.A., Educational Technology).
