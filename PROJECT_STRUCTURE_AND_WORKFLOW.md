# Thai EduCenter & Advisor Match: โครงสร้างโปรเจค ขั้นตอนการทำงาน และสารบัญระบบแม่บท (Master Architecture & Runbook)

> **สำหรับ AI Model / Developer ที่เข้ามารับช่วงต่อใน Session ใหม่:**
> เอกสารฉบับนี้คือ **Single Source of Truth** ที่รวบรวมสารบัญไฟล์, สถาปัตยกรรมระบบ, ขั้นตอนการทำงานมาตรฐาน (SOP), กฎเหล็กความปลอดภัย, และข้อควรระวังเพื่อป้องกันข้อผิดพลาด 100% โปรดอ่านและปฏิบัติตามอย่างเคร่งครัด

---

## 1. บทนำและเป้าหมายของโปรเจค (Project Mission)

**Thai EduCenter** (ประกอบด้วยระบบ **Thai Advisor Match**) คือแพลตฟอร์มค้นหาข้อมูลการศึกษาต่อระดับปริญญาโท-เอกในประเทศไทย ช่วยให้นักศึกษาและนักวิจัยสามารถ:
1. **AI Semantic Advisor Matching:** ค้นหาอาจารย์ที่ปรึกษาวิทยานิพนธ์ด้วยหัวข้องานวิจัย/บทคัดย่อ (ทั้งภาษาไทยและอังกฤษ) คำนวณเปอร์เซ็นต์ความเข้ากัน (% Match Score) ผ่าน `pgvector` และเวกเตอร์ 768 มิติของ Gemini
2. **Curriculum & Tuition Discovery:** ค้นหาหลักสูตรการศึกษา ข้อมูลค่าเล่าเรียน ระยะเวลาศึกษา จำนวนหน่วยกิต และสายอาชีพ
3. **Research Labs Interlinking:** สำรวจห้องปฏิบัติการวิจัยชั้นนำระดับชาติ (104 Labs) และเชื่อมโยง 2 ทางกับอาจารย์หัวหน้าห้องแล็บ
4. **RIASEC Career Discovery Quiz:** แบบทดสอบจิตวิทยา 3 ระดับเพื่อจับคู่นักศึกษากับสายงานวิชาการที่เหมาะสม

---

## 2. สารบัญโครงสร้างไฟล์และโฟลเดอร์ (Project Directory Index & TOC)

```text
Teacher/
├── CHANGELOG.md                                   # บันทึกประวัติการเปลี่ยนแปลงและการขยายระบบตามวันที่
├── compose.yaml                                   # Docker Compose: PostgreSQL 17 + pgvector + pgAdmin 4
├── PROJECT_STRUCTURE_AND_WORKFLOW.md             # [เอกสารนี้] สารบัญแม่บทและคู่มือการทำงานสำหรับ AI / Dev
├── README.md                                      # เอกสารแนะนำโปรเจคเบื้องต้น
├── AGENTS.md / CLAUDE.md                          # กฎการทำงานและข้อห้ามระดับระบบสำหรับ AI Agents
│
├── docker/
│   └── init.sql                                   # สคริปต์ Init Database (Extensions, ตาราง, HNSW & GIN Indexes)
│
├── frontend/                                      # Next.js 16 Super App UI (Port 3000)
│   ├── package.json                               # Next.js 16, React 19, Lucide React, Tailwind CSS v4
│   ├── next.config.ts                             # Image Domain Whitelisting (ac.th, unsplash, avatars)
│   ├── tsconfig.json                              # Path alias @/* ชี้ไปยัง ./src/*
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                         # Root Layout, Theme Providers, Head Script
│       │   ├── page.tsx                           # หน้าแรก (Hero, Quick Search, Popular Chips)
│       │   ├── globals.css                        # Tailwind v4 Directives (@import "tailwindcss"; @theme)
│       │   ├── advisor/[id]/page.tsx              # หน้ารายละเอียดอาจารย์ (โปรไฟล์, กราฟ, ผลงาน, งานวิจัย)
│       │   ├── labs/[id]/page.tsx                 # หน้ารายละเอียดห้องปฏิบัติการวิจัย (เครื่องมือ, สมาชิก)
│       │   └── career-discovery/page.tsx          # หน้าแบบประเมิน RIASEC Quiz
│       ├── components/
│       │   ├── AdvisorCard.tsx                    # การ์ดแสดงผลอาจารย์ + Synergy Badges + Tier Badges
│       │   ├── CourseCard.tsx                     # การ์ดแสดงผลหลักสูตร
│       │   ├── LabCard.tsx                        # การ์ดแสดงผลห้องวิจัย
│       │   ├── FilterBar.tsx                      # ตัวกรองมหาวิทยาลัย, คณะ, ภูมิภาค, และ Performance Tier
│       │   ├── Header.tsx / Footer.tsx            # ส่วนหัวและส่วนท้ายของเว็บไซต์
│       │   └── ...                                # UI Components อื่นๆ
│       ├── lib/
│       │   ├── config.ts                          # API Base URLs, Helper URLs (Avatar fallback)
│       │   └── dsa.ts                             # Client-side LRU Cache สำหรับแคชผลการค้นหา
│       └── types/
│           └── index.ts                           # Single Source of Truth สำหรับ TypeScript Interfaces ทั้งหมด
│
├── backend/                                       # FastAPI API & Data Engine (Port 8000)
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
│   │       ├── routes_faculty.py                  # API ข้อมูลอาจารย์, รายชื่อ, กรองตามภาควิชา/มหาวิทยาลัย
│   │       ├── routes_courses.py                  # API หลักสูตรและค่าเล่าเรียน
│   │       ├── routes_labs.py                     # API ห้องปฏิบัติการวิจัยและการเชื่อมโยงอาจารย์
│   │       └── routes_career_quiz.py              # API ประมวลผล RIASEC Quiz
│   │
│   ├── data/
│   │   └── agent_states/                          # Checkpointed Extraction State JSONs (Wave 1 to Wave 19)
│   │       ├── wave17_ku_forest_extracted.json
│   │       ├── wave18_ku_forest_regional_extracted.json
│   │       └── wave19_cu_gaps_extracted.json
│   │
│   ├── scripts/                                   # Automation Scripts & Pipelines
│   │   ├── agentic_pipeline/                      # Pipeline ประมวลผลและลดรูปข้อมูล
│   │   │   ├── state_reducer.py                   # ตัดคำนำหน้า (Thai/EN), RapidFuzz Deduplication, Merge Logic
│   │   │   ├── content_pruner.py                  # ตัด HTML Boilerplate (LLMLingua/Trafilatura)
│   │   │   └── cli_runner.py                      # CLI Runner สำหรับรัน Autonomous Pipeline
│   │   ├── crawlers/                              # สคริปต์ Web Crawler แยกตาม Wave
│   │   │   ├── crawl_wave13_flagships.py          # Intania CU, KU Science, PSU Agro
│   │   │   ├── crawl_wave14_flagships.py          # MU Science, KKU Science, KKU Agri, CU Science
│   │   │   ├── crawl_wave15_flagships.py          # CU Dent, CU AHS, PSU Med, KU Agro, KU Vet, KU Forestry
│   │   │   ├── crawl_wave16_flagships.py          # KMITL AAD, KMITL SIET, CU Pharm, KKU Pharm, TSE
│   │   │   ├── crawl_wave17_ku_forest.py          # KU Forest: Social Sci, Humanities, Business, Econ, Environment, Vet Tech
│   │   │   ├── crawl_wave18_ku_forest_regional.py # KU Forest Closeout: remaining Bang Khen + KPS/Sriracha/Sakon Nakhon (20 faculties)
│   │   │   └── crawl_wave19_cu_gaps.py            # CU Gap Closeout: Law, PolSci, Econ, Edu (API), Psy rosters
│   │   ├── audits/                                # เครื่องมือตรวจสอบสุขอนามัยของฐานข้อมูล
│   │   │   ├── verify_db_stats.py                 # ตรวจสอบจำนวนข้อมูลและ Null Embeddings
│   │   │   └── merge_duplicate_faculties.py       # ตรวจสอบและควบรวมข้อมูลซ้ำซ้อน
│   │   ├── migrate_supabase_to_local.py           # สตรีมข้อมูลจาก Supabase ลง Docker Local
│   │   └── sync_local_to_supabase.py              # ซิงค์ข้อมูลที่ผ่านการทดสอบขึ้น Cloud Supabase
│   │
│   └── tests/                                     # Pytest Test Suite (34 Test Cases)
│       ├── test_search.py                         # ทดสอบ API Search, Filters, Lab Interlinking
│       ├── test_agentic_pipeline.py               # ทดสอบ State Reducer, Title Stripping, PDPA Redaction
│       ├── test_audited_bug_regressions.py        # ทดสอบป้องกัน Regression 10 ข้อหลัก
│       ├── test_taxonomy_and_regional_search.py   # ทดสอบระบบจัดหมวดหมู่และค้นหาระดับภูมิภาค
│       └── test_wikiskill.py                      # ทดสอบ WikiSkill Architecture
│
└── .agents/ & memory/                             # ระบบความจำระยะยาว (Persistent Long-term Memory)
    ├── memory/
    │   ├── MEMORY.md                              # สารบัญ Memory ของระบบ
    │   ├── future-data-acquisition-roadmap.md     # Roadmap ความคืบหน้าการขยายข้อมูล (Status 14,015)
    │   ├── hold-supabase-sync-until-local-complete.md # กฎ Local-First Zero-Egress
    │   └── antipatterns-and-bug-prevention.md     # กฎเหล็กป้องกันข้อผิดพลาดที่ผ่านการออดิตแล้ว
    └── .agents/skills/                            # Domain Automation Skills (db-optimization, etc.)
```

---

## 3. สถาปัตยกรรมและเทคโนโลยีหลัก (Core Technology Stack & Contracts)

### 3.1 Frontend (Next.js 16 + React 19 + Tailwind CSS v4)
* **Tailwind CSS v4:** กำหนดค่าผ่าน CSS Directives ใน `frontend/src/app/globals.css` (ใช้ `@import "tailwindcss";` และ `@theme`, **ห้ามสร้าง `tailwind.config.js` เด็ดขาด**)
* **App Router & Client Components:** คอมโพเนนต์ที่มีการใช้ React Hooks (`useState`, `useEffect`, `useRouter`, `useSearchParams`) ต้องประกาศ `"use client";` ไว้บนสุดเสมอ
* **Image Optimization (Zero Cumulative Layout Shift - CLS = 0):**
  * ห้ามใช้แท็ก `<img>` ธรรมดา ให้ใช้ `<Image />` จาก `next/image` เท่านั้น
  * กำหนด `width`/`height` ชัดเจน หรือใช้ `fill` ร่วมกับ `relative` container พร้อมระบุ `sizes`
  * มี Fallback เสมอโดยใช้ `getAdvisorAvatarUrl(name)` เมื่อโหลดภาพจริงไม่สำเร็จ
  * อนุญาตโดเมนภาพใน `next.config.ts` เช่น `**.ac.th`, `**.edu`, `images.unsplash.com`, `ui-avatars.com`
* **TypeScript Strictness:** ห้ามเขียน `interface` หรือ `type` ซ้ำซ้อนในแต่ละไฟล์ ให้ import จาก `@/types` เท่านั้น

### 3.2 Backend (FastAPI + SQLAlchemy 2.0 + Pydantic v2)
* **Python 3.12+ Syntax:** ใช้ Type Hints มาตรฐาน (`str | None`, `list[str]`)
* **Pydantic v2:**
  * ใช้ `model.model_dump()` และ `model.model_dump_json()` (ห้ามใช้ `dict()` หรือ `json()`)
  * การ Validate ใช้ `@field_validator("field", mode="before")`
  * การแปลง SQLAlchemy ORM ใช้ `ConfigDict(from_attributes=True)`
* **High Performance DSA:**
  * ใช้ `TopKHeap` (Min-Heap $O(N \log K)$) ในการคัดเลือก Top Candidates แทนการ Sort ทั้งก้อน ($O(N \log N)$)
  * ใช้ `LRUCache` ในการเก็บเวกเตอร์คำค้นหา (0.001ms latency)
  * เปิดใช้ `GZipMiddleware(minimum_size=1000)` เพื่อบีบอัดขนาด Payload ลง 75-85%

### 3.3 Database & Vector Search (Local PostgreSQL 17 + pgvector)
* **Local-First Zero-Egress Invariant:** การทำ Crawling, State Reduction, Deduplication, Vector Embedding และ Commit **ต้องทำกับ Local Docker PostgreSQL (`localhost:5432/advisor_match`) เท่านั้น** ห้ามสตรีมข้อมูลขึ้น Supabase Cloud โดยไม่ได้รับคำสั่งอนุมัติ เพื่อป้องกันโควตา Egress รั่วไหล
* **Vector Embeddings:** เวกเตอร์ขนาด **768 มิติ** สร้างด้วยโมเดล Google Gemini (`gemini-embedding-2` หรือ fallback `gemini-embedding-001`)
* **Database Indexes:**
  * HNSW Cosine Index สำหรับเวกเตอร์: `ix_faculties_embedding_hnsw`
  * GIN Trigram Index สำหรับค้นหาชื่อภาษาไทย: `idx_faculties_name_th_trgm`

---

## 4. ขั้นตอนการทำงานมาตรฐานในการขยายข้อมูล (Data Acquisition SOP Lifecycle)

เมื่อได้รับมอบหมายให้ดึงข้อมูลคณาจารย์ใน Wave ถัดไป (เช่น Wave 17, 18, ...) ต้องปฏิบัติตาม **วงจร 5 ขั้นตอน (5-Step Lifecycle)** อย่างเคร่งครัด **ห้ามข้ามขั้นตอนหรือสร้างข้อมูลขึ้นมาเองโดยไม่ได้ Crawl เด็ดขาด**:

```text
[Step 1: Real-time Web Crawl] 
           ↓ (HTML/JSON Extraction)
[Step 2: State Reduction & RapidFuzz Dedup] 
           ↓ (Normalized, Cleaned, Deduplicated)
[Step 3: Disk Checkpointing] -> backend/data/agent_states/waveXX_extracted.json
           ↓ (Immutable Recovery Point)
[Step 4: Multi-Client 768-dim Vectorization] -> Gemini API Key Rotation (Backoff on 429)
           ↓ (768-dim Float Arrays)
[Step 5: Local DB Commit & Verification] -> PostgreSQL 17 (34/34 Tests + Next.js Build)
```

### รายละเอียดในแต่ละขั้นตอน:
1. **Step 1: Reverse-Engineering & Crawling:**
   * ตรวจสอบ Endpoint ของมหาวิทยาลัย/คณะเป้าหมาย (สังเกต AJAX API, WordPress REST API, หรือ HTML Directory)
   * สกัดข้อมูล: ชื่อไทย-อังกฤษ, คำนำหน้า, คณะ, ภาควิชา, อีเมลทางการ, รูปภาพ, ความเชี่ยวชาญ/งานวิจัย
2. **Step 2: State Reduction & Thai Title Normalization:**
   * ใช้ฟังก์ชัน `strip_all_titles(name)` และ `normalize_thai_title_and_name(raw_name)`
   * นำรายชื่อไปทำ RapidFuzz Deduplication กับฐานข้อมูล Local (`fuzz.token_set_ratio >= 90`)
   * หากพบว่ามีอยู่แล้ว: ทำการ **Enrich** ข้อมูล (เติมอีเมล, เติมรูปภาพ, รวม research interests) โดยไม่สร้างแถวซ้ำ
   * หากเป็นคนใหม่: จัดเข้ากลุ่ม **New Members** เพื่อสร้างเวกเตอร์
3. **Step 3: Disk Checkpointing:**
   * บันทึก Raw Extracted JSON ลงใน `backend/data/agent_states/waveXX_flagships_extracted.json` ทันที เพื่อรองรับกรณีเน็ตหลุดหรือเครื่องดับ สามารถ resume ได้โดยไม่ต้อง crawl ใหม่
4. **Step 4: Multi-Client Thread-Safe Vectorization:**
   * ดึง API Keys จาก `settings.GEMINI_API_KEYS` นำมาสร้าง Pool ของ `genai.Client`
   * ใช้ ThreadPoolExecutor ร่วมกับ Key Rotation และ Exponential Backoff (เมื่อเจอ HTTP 429 ให้ sleep และลองโมเดล fallback `gemini-embedding-001`)
   * ผลลัพธ์ต้องได้เวกเตอร์ 768 มิติจำนวนครบถ้วน 100% (Null Embeddings = 0)
5. **Step 5: Bulk Database Commit & Autonomous Verification:**
   * บันทึกข้อมูลลงฐานข้อมูล Local PostgreSQL
   * รันชุดทดสอบ Backend: `pytest backend/tests -v` (ต้องผ่านครบ 34 ข้อ)
   * รันบิลด์ Frontend: `npm --prefix frontend run build` (ต้องผ่านปราศจากข้อผิดพลาด)
   * อัปเดตเอกสาร `CHANGELOG.md` และ `memory/future-data-acquisition-roadmap.md`

---

## 5. กฎเหล็กและข้อควรระวังเพื่อป้องกันข้อผิดพลาด (Absolute Invariants & Antipatterns)

### 1. กฎห้ามสร้างข้อมูลสังเคราะห์เอง (No Direct Synthesis / Manual Shortcuts)
* ห้ามเขียนข้อมูลชื่ออาจารย์หรือข้อมูลคณะขึ้นมาเองในไฟล์โค้ดเพื่อความรวดเร็ว ต้องมาจากการรันสคริปต์ Crawl ข้อมูลจริงจากเว็บไซต์ของมหาวิทยาลัยเท่านั้น

### 2. ข้อห้ามเรื่อง Regex คำนำหน้าภาษาไทย (Thai Regex Boundary Safety)
* **ห้ามใช้ `r"ดร\.?"` เด็ดขาด:** ภาษาไทยไม่มีการเว้นวรรคคำ การใช้เครื่องหมาย `?` หลังจุด จะทำให้ Regex ตัดชื่อคนไทยที่ขึ้นต้นด้วย "ดร" เช่น "ดรุณี", "ดรัลพร" กลายเป็น "ุณี", "ัลพร" ซึ่งทำให้ชื่อเสียหายถาวร
* **สิ่งที่ต้องใช้:** ต้องบังคับให้มีจุดเสมอ เช่น `r"ดร\."` หรือ `r"ดร\s+"` เท่านั้น

### 3. การป้องกันความผิดพลาดในภาษา Python และ ORM
* **Defensive Null-Coalescing:** ข้อมูลในฐานข้อมูล (JSON, List, Text) สามารถเป็น `None` ได้ ห้ามเขียน `db_obj.field[:3]` ตรงๆ โดยเด็ดขาด ให้เขียน `(db_obj.field or [])[:3]` เสมอ เพื่อป้องกัน runtime `TypeError` (HTTP 500)
* **Memory-Conscious Queries:** ห้ามรัน `db.query(FacultyDB).all()` ในจุดที่มีการดึงเวกเตอร์ขนาด 768 มิติของคนหลายพันคนพร้อมกัน ให้ใช้ `options(defer(FacultyDB.embedding)).yield_per(500)` เมื่อต้องการสแกนเฉพาะฟิลด์ข้อความ
* **Pydantic v2 Coercion:** เมื่อ Gemini ส่งผลลัพธ์เป็น JSON ค่า Array อาจเป็น `null` ซึ่ง Pydantic v2 จะ reject ทันทีแม้จะใส่ `default_factory=list` ให้ใส่ `@field_validator("...", mode="before")` เพื่อแปลง `None` เป็น `[]` เสมอ

### 4. การจัดการ Frontend และ Next.js 16
* **Hydration Mismatch Defense:** ห้ามอ่าน `localStorage` หรือ `window` ในช่วง Initial State ให้ใช้ "Mounted Pattern" (`const [mounted, setMounted] = useState(false)`)
* **No Direct DOM Mutation:** ห้ามเขียน `e.target.src = ...` ในการจัดการรูปภาพ fallback ให้ใช้ State Flag ของ React ในการสลับไปใช้รูป Avatar สำรอง

---

## 6. คู่มือคำสั่งสำหรับใช้งานระบบ (CLI Commands Cheat Sheet)

### 6.1 การเริ่มต้นระบบ (Development Startup)
```powershell
# 1. รัน Database Container (PostgreSQL 17 + pgvector)
docker compose up -d

# 2. รัน Backend API (FastAPI)
cd backend
$env:PYTHONPATH='.'
python -m uvicorn app.main:app --reload --port 8000

# 3. รัน Frontend UI (Next.js 16)
cd frontend
npm run dev
```

### 6.2 การตรวจสอบและทดสอบระบบ (Verification Protocol)
```powershell
# รันชุดทดสอบ Backend ทั้งหมด (34 Tests)
pytest backend/tests -v

# รัน Production Build ของ Frontend
npm --prefix frontend run build

# ตรวจสอบจำนวนข้อมูลอาจารย์และเช็คความสมบูรณ์ของ Embeddings ในฐานข้อมูล
$env:PYTHONPATH='backend'; python -c "from app.core.database import SessionLocal; from app.models.db_models import FacultyDB; db = SessionLocal(); print('Total:', db.query(FacultyDB).count(), '| Null Embeddings:', db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()); db.close()"
```

### 6.3 การรัน Ingestion / Crawlers
```powershell
# ตัวอย่างการรัน Crawler ขยายข้อมูลคณาจารย์
python backend/scripts/crawlers/crawl_wave16_flagships.py
```

---

## 7. สถานะระบบปัจจุบันและ Roadmap การขยายข้อมูล (Status & Next Waves)

### 7.1 สถานะปัจจุบัน (ณ วันที่ 2026-09-12)
* **อาจารย์และนักวิจัยในระบบ Local DB:** **14,015 ท่าน** (ผ่านการประมวลผล Wave 1 ถึง Wave 19)
* **เวกเตอร์ Embedding ขาดหาย:** **0 รายการ** (ความสมบูรณ์ 100%)
* **ห้องปฏิบัติการวิจัยชั้นนำระดับชาติ:** **104 ห้องแล็บ** (เชื่อมโยงอาจารย์หัวหน้าแล็บ 100%)
* **หลักสูตรระดับบัณฑิตศึกษา:** **4,185 หลักสูตร**
* **สถิติมหาวิทยาลัย 8 อันดับแรก:**
  1. มหาวิทยาลัยเกษตรศาสตร์: 3,272 ท่าน
  2. จุฬาลงกรณ์มหาวิทยาลัย: 2,446 ท่าน
  3. มหาวิทยาลัยเชียงใหม่: 1,780 ท่าน
  4. มหาวิทยาลัยมหิดล: 1,296 ท่าน
  5. มหาวิทยาลัยขอนแก่น: 770 ท่าน
  6. มหาวิทยาลัยธรรมศาสตร์: 742 ท่าน
  7. มหาวิทยาลัยสงขลานครินทร์: 608 ท่าน
  8. สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง: 568 ท่าน

### 7.2 Roadmap เป้าหมาย Wave ถัดไป (Wave 20)
* **สถานะ Wave 19 (เสร็จสิ้น 2026-09-12):** ปิดช่องว่างคณะของ จุฬาฯ — ตรวจพบว่าจะไม่มีพอร์ทัลกลาง CU (togethher/research.chula DNS ตาย) จึงใช้แผนสำรองที่อนุมัติแล้ว: 5 รายชื่อคณะที่เข้าถึงได้ (นิติศาสตร์ 53, รัฐศาสตร์ 66, เศรษฐศาสตร์ 54 + portfolio 12 หน้า, ครุศาสตร์ 129 ผ่าน eduadmin JSON API, จิตวิทยา 35) = 337 raw → Insert 184 + Enrich 153, ฐานรวมข้ามหลัก **14,015 ท่าน**, CU จาก 2,262 → 2,446 (อันดับ 2 ตามเดิม, KU 3,272)
* **เป้าหมาย:** คณะ CU ที่เหลือซึ่งเป็น JS-SPA/legacy (นิเทศศาสตร์, อักษรศาสตร์, พยาบาล, ศิลปกรรม, กีฬา) — ต้องใช้ headed browser/Playwright หรือหา JSON endpoint, Thammasat SciTech (Rangsit), มหาลัยภูมิภาคที่ยังบาง (PSU วิทยาเขตอื่นๆ, NU, UBU), หรือ enrichment รอบ OpenAlex ต่อ
