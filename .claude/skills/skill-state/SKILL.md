---
name: skill-state
description: MANDATORY TOOL for any web scraping, crawling, faculty data acquisition, or email/profile enrichment. MUST be invoked whenever asked to scrape, crawl, harvest, search faculty, or collect academic data. Enforces headless execution via cli_runner.py with zero in-chat token bloat.
---

<!-- Reference: SKILL.state Architecture & Evaluation (arXiv:2608.26263v2) - https://arxiv.org/html/2608.26263v2#S5 -->

# SKILL.state Autonomous Pipeline Execution Standard

When instructed to acquire, scrape, harvest, search, or enrich faculty, curriculum, or laboratory data (including missing emails/profiles), you MUST strictly execute the designated Autonomous Pipeline CLI Runners (`python backend/scripts/agentic_pipeline/run_acquire.py` or `cli_runner.py`).

## ⚠️ ABSOLUTE OPERATIONAL INVARIANT
**STRICTLY FORBIDDEN to run ad-hoc multi-turn scrapers in chat, parse raw HTML/DOM in conversation turns, or write one-off `temp_scrape.py` scripts.**
All crawling, Trafilatura boilerplate pruning, LLMLingua compression, and RapidFuzz deduplication MUST run headlessly in Python to maintain a flat token footprint (<2,000 tokens/turn).

---

## 1. Fast CLI Execution (Shorthand Wrapper)

Use the shorthand wrapper with built-in university/faculty normalization:
```bash
python backend/scripts/agentic_pipeline/run_acquire.py \
  --url "https://target-faculty-page.ac.th/staff" \
  --univ "CU" \
  --fac "Engineering" \
  --max-steps 20
```

Supported university shortcuts:
- `CU` -> จุฬาลงกรณ์มหาวิทยาลัย (Chulalongkorn University)
- `CMU` -> มหาวิทยาลัยเชียงใหม่ (Chiang Mai University)
- `KU` -> มหาวิทยาลัยเกษตรศาสตร์ (Kasetsart University)
- `MU` -> มหาวิทยาลัยมหิดล (Mahidol University)
- `KKU` -> มหาวิทยาลัยขอนแก่น (Khon Kaen University)
- `KMITL` -> สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL)
- `KMUTT` -> มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี (KMUTT)
- `TU` -> มหาวิทยาลัยธรรมศาสตร์ (Thammasat University)
- `PSU` -> มหาวิทยาลัยสงขลานครินทร์ (Prince of Songkla University)

---

## 2. Direct CLI Runner Execution (`cli_runner.py`)

For custom or full-named invocations:
```bash
python backend/scripts/agentic_pipeline/cli_runner.py \
  --univ-th "มหาวิทยาลัยเชียงใหม่" \
  --univ-en "Chiang Mai University" \
  --faculty-th "คณะวิศวกรรมศาสตร์" \
  --faculty-en "Faculty of Engineering" \
  --url "https://me.eng.cmu.ac.th/staff/professor" \
  --export-file "backend/scripts/data_sources/cmu_me_extracted.py" \
  --max-steps 20
```

---

## 3. Workflow & Checkpoints

1. **Extraction:** `FacultyExtractionAgent` fetches pages, extracts records via structured LLM schema (`FacultyStatePatch`).
2. **Pruning:** Boilerplate is stripped via Trafilatura before calling LLMs (80%+ token reduction).
3. **State Reducer:** Titles are normalized (`ศ.ดร.`, `รศ.ดร.`, etc.), phone numbers redacted (PDPA), and RapidFuzz dedup (threshold > 88) executes in Python.
4. **Checkpointing:** State auto-saves to `backend/data/agent_states/extract_{timestamp}_{hash}.json`.
5. **Reporting:** Return ONLY high-level summary counts (number of verified faculty, new vs updated) to the user.
