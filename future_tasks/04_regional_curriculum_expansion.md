# Task 4: Regional Curriculum Expansion

> **Priority:** 📌 Tier 4 (Coverage Optimization)  
> **Target:** Expand graduate academic programs (Master's and Ph.D.) across regional universities.

---

## 1. Baseline Status
In the `courses` dataset (4,162 curricula):
- CMU, KKU, KU, CU, and MU collectively account for >2,800 curricula (providing extensive baseline coverage).
- Regional research universities and comprehensive institutions have relatively sparse representation:
  - Prince of Songkla University (PSU): 74 curricula
  - Sukhothai Thammathirat Open University (STOU): 70 curricula
  - Silpakorn University (SU): 61 curricula
  - Srinakharinwirot University (SWU): 56 curricula
  - University of Phayao (UP): 54 curricula
  - Mae Fah Luang University (MFU): 54 curricula
  - Naresuan University (NU): 53 curricula
  - Burapha University (BUU): 41 curricula
  - Thaksin University (TSU): 36 curricula
  - Ubon Ratchathani University (UBU): 74 curricula
  - Walailak University (WU): minimal representation

---

## 2. Methodology via `data-curriculum-tuition-discovery` Skill
Execute the 3-Tier Discovery protocol documented in `.agents/skills/data-curriculum-tuition-discovery/SKILL.md`:
1. **Tier 1 (TQF-2 MIS):** Harvest curriculum catalogs from university MIS or Graduate School portals to capture degree titles, total credits, and program structure.
2. **Tier 2 (TCAS & Registrar Fees):** Ingest tuition fees per semester (`tuition_per_semester`) and associated career opportunities (`career_paths`).
3. **Tier 3 (Fuzzy Reconciliation & Embedding):** Deduplicate via RapidFuzz and generate 768-dim Gemini embeddings before committing to local PostgreSQL.

### CLI Execution Command:
```bash
python backend/scripts/agentic_pipeline/course_cli_runner.py \
  --univ-th "มหาวิทยาลัยสงขลานครินทร์" \
  --univ-en "Prince of Songkla University" \
  --faculty-th "บัณฑิตวิทยาลัย" \
  --faculty-en "Graduate School" \
  --url "https://grad.psu.ac.th/curriculum" \
  --export-file "backend/scripts/data_sources/psu_grad_courses.py"
```
