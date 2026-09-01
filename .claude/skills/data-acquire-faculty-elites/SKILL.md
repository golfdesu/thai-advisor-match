---
name: data-acquire-faculty-elites
description: Methodology for discovering, verifying, and ingesting both National Elite Researchers (award winners) and university-specific faculty members, ensuring strict zero-duplication and deep canonical merging.
---

<!-- Reference: SKILL.state Architecture & Evaluation (arXiv:2608.26263v2) - https://arxiv.org/html/2608.26263v2#S5 -->

# Faculty Elite & University-Wide Acquisition Methodology (SKILL.state Engine)

When instructed to discover, scrape, or acquire new faculty members—whether targeting National Outstanding Researchers (นักวิจัยดีเด่นแห่งชาติ) or expanding coverage for specific universities (e.g., CMU, MFU, PSU, SWU, KMITL)—you MUST strictly use the **`SKILL.state` Autonomous Pipeline Engine (`backend/scripts/agentic_pipeline/`)** to ensure flat token consumption (<2,000 tokens/turn), zero context corruption, and deterministic deduplication.

---

## 1. Core Execution Engine: SKILL.state Architecture

Always run or interface with `backend/scripts/agentic_pipeline/` which implements the state-driven paradigm ([arXiv:2608.26263v2](https://arxiv.org/html/2608.26263v2#S5)):

1. **State-Patch Generator (`llm_client.py`):** Uses Gemini with Structured Outputs (`FacultyStatePatch`). Prompts contain ONLY minimal state context + target HTML chunk (never accumulated conversation history).
2. **Deterministic State Reducer (`state_reducer.py`):**
   - Automatically normalizes Thai titles (`ศ.ดร.`, `รศ.ดร.`, `ผศ.ดร.`, `อ.ดร.`) and eliminates duplicate title prefixes.
   - Runs **RapidFuzz deduplication** (threshold > 88–90) against both the in-memory state and the live database.
   - Performs **Deep Merge** of publications, research interests, and Google Scholar URLs into existing records.
   - Enforces **PDPA compliance** by redacting phone numbers (`[REDACTED_PHONE]`).
3. **Resumable State Checkpoints:** Automatically writes and restores session states in `backend/data/agent_states/{session_id}.json`.

---

## 2. CLI Execution Standard

Execute the extraction agent via CLI:
```bash
python scripts/agentic_pipeline/cli_runner.py \
  --univ-th "มหาวิทยาลัยเชียงใหม่" \
  --univ-en "Chiang Mai University" \
  --faculty-th "คณะวิศวกรรมศาสตร์" \
  --faculty-en "Faculty of Engineering" \
  --url "https://me.eng.cmu.ac.th/staff/professor" \
  --export-file "scripts/data_sources/cmu_me_extracted.py" \
  --max-steps 20
```

---

## 3. Discovery & Verification Strategy

### A. National Elite & Breakthrough Researchers Discovery
When asked to "find outstanding professors" or "world-class researchers":
- **Target Recognized Awardees:** Prioritize researchers who have received the National Outstanding Researcher Award (นักวิจัยดีเด่นแห่งชาติ), Senior Research Scholar grants (เมธีวิจัยอาวุโส วช.), Outstanding Scientist of Thailand awards (นักวิทยาศาสตร์ดีเด่นแห่งชาติ), or are recognized as Highly Cited Researchers.
- **Multi-Disciplinary Coverage:** Ensure candidates span diverse fields: Engineering, Medicine, Science, Agriculture, Law, Economics, and Business Administration.
- **Accredited Universities ONLY:** Verify that the researcher is actively affiliated with an accredited Thai Higher Education Institution. DO NOT include researchers from private non-university research institutes (e.g., VISTEC, NSTDA, BIOTEC) unless they hold a joint professorship at a university.

### B. University-Wide Comprehensive Scrapes
When asked to "expand a specific university" (e.g., MFU, KU, CMU):
- **All Major Schools:** Cover all major faculties, especially specialized ones (e.g., Cosmetic Science at MFU, Forestry at KU).
- **Direct Directory Reverse-Engineering:** Extract from official faculty directories (`staff` or `personnel` pages).

---

## 4. Data Structure & Profile Synthesis

Every newly acquired faculty profile MUST follow this precise schema:
```json
{
    "id": "univ_faculty_name_001",
    "university": "English Name",
    "university_th": "Thai Name",
    "faculty": "Faculty in English",
    "faculty_th": "Faculty in Thai",
    "department": "Department in English",
    "department_th": "Department in Thai",
    "academic_title": "Prof. Dr.",
    "academic_title_th": "ศ.ดร.",
    "first_name": "English First",
    "last_name": "English Last",
    "full_name_th": "ศ.ดร. ชื่อ นามสกุล",
    "role": "Outstanding National Researcher / Title",
    "email": "official@univ.ac.th",
    "profile_url": "https://...",
    "education": ["Ph.D. (...)", "M.Sc. (...)", "B.Sc. (...)"],
    "research_interests": ["Domain 1", "Domain 2", "Domain 3"],
    "featured_publications": ["Title 1", "Title 2"],
    "scholar_url": "https://scholar.google.com/..."
}
```

---

## 5. Seamless Ingestion & Vectorization

After extracting via the `SKILL.state` agent, ingest and vectorize using the established runner:
```bash
python scripts/faculty_massive_ingestion_runner.py
```
This guarantees:
1. **Upsert Logic:** Inserts new and updates existing without crashing.
2. **Multi-Threaded Vectorization:** Instantly computes 768-dim `gemini-embedding-2` vectors using thread pools.
3. **Database Commit:** Saves vectors directly to Supabase `pgvector`.
