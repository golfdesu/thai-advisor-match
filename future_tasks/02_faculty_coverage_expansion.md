# Task 2: Faculty Coverage Expansion

> **Priority:** 🔥 Tier 2 (High Priority)  
> **Target:** Expand faculty coverage across leading universities currently having fewer than 50–100 records.

---

## 1. Problem Statement & Baseline Status
In the baseline `faculties` dataset (3,901 members), over 70% of records were concentrated across 5 major universities:
- Chulalongkorn University (CU): 879
- Mahidol University (MU): 592
- Chiang Mai University (CMU): 555
- Thammasat University (TU): 361
- Kasetsart University (KU): 333
- Khon Kaen University (KKU): 253

Conversely, several prominent research institutions with substantial graduate student bodies were significantly underrepresented:

| University | Baseline Count | Target Count | High-Priority Target Faculties |
| :--- | :---: | :---: | :--- |
| **Srinakharinwirot University (SWU)** | **13** | **150+** | Medicine, Engineering, Science, Nursing, Pharmacy |
| **Burapha University (BUU)** | **14** | **150+** | Informatics, Engineering, Medicine, Public Health |
| **Mae Fah Luang University (MFU)** | **25** | **100+** | Information Technology, Health Sciences, Sinology, Integrative Medicine |
| **Silpakorn University (SU)** | **29** | **120+** | Engineering & Industrial Technology, Pharmacy, Science, ICT |
| **Naresuan University (NU)** | **78** | **150+** | Medicine, Engineering, Medical Sciences |
| **Prince of Songkla University (PSU)** | **129** | **300+** | Medicine (Hat Yai), Engineering, Science, Pharmacy |
| **KMUTT** | **116** | **250+** | Engineering (all depts), School of Information Technology (SIT), FIBO |
| **KMITL** | **148** | **300+** | School of Engineering (all depts), IT, Science |

---

## 2. Standard Acquisition Protocol (`AGENTS.md` Zero-Bypass Policy)

All faculty data acquisition must execute through the headless Autonomous Pipeline. Manually synthesized or mocked data is strictly prohibited.

### CLI Runner Invocation:
```bash
python backend/scripts/agentic_pipeline/run_acquire.py \
  --url "https://eng.swu.ac.th/personnel" \
  --univ SWU \
  --fac Engineering \
  --max-steps 25
```
Or via the full `cli_runner.py`:
```bash
python backend/scripts/agentic_pipeline/cli_runner.py \
  --univ-th "มหาวิทยาลัยศรีนครินทรวิโรฒ" \
  --univ-en "Srinakharinwirot University" \
  --faculty-th "คณะวิศวกรรมศาสตร์" \
  --faculty-en "Faculty of Engineering" \
  --url "https://eng.swu.ac.th/personnel" \
  --export-file "backend/scripts/data_sources/swu_eng_faculties.py"
```

### Ingestion Lifecycle:
1. **Real-time Extraction:** Fetch directory HTML via Playwright or requests.
2. **Content Pruning:** Strip boilerplate and navigation headers using `ContentPruner` (<2,000 tokens).
3. **State Reducer:** Extract structured fields and execute RapidFuzz deduplication (`fuzz.token_set_ratio >= 85`) against existing records.
4. **Checkpointing:** Checkpoint structured state to `backend/data/agent_states/`.
5. **Multi-Threaded Vectorization:** Generate 768-dim embeddings via Google Gemini API key pool.
6. **Local Database Commit:** Commit verified records to local PostgreSQL 17.

---

## 3. Domain Quality & Hygiene Invariants
1. **Academic Title Separation:** Normalize academic titles (Prof., Assoc. Prof., Asst. Prof., Dr., M.D., D.D.S., Pharm.) out of `full_name_th` so the name field contains only the authentic human name, storing titles in `academic_title_th`.
2. **Egress Protection:** Verify `DATABASE_URL` connects to `localhost:5432` prior to running batch ingestions.
