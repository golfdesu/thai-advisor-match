# Future Data Acquisition & Expansion Roadmap

> **Recorded:** September 8, 2026  
> **Current Primary Database:** Local Docker PostgreSQL 17 (`localhost:5432 / advisor_match`)

This directory documents data gaps, strategic priorities, methodology, and operational scripts for ongoing database expansion. It is structured into **5 core tasks** ranked by priority:

> **Update Sep 10, 2026:** Added Task 5 (Elite Researchers & High-Impact Faculty) as database scale expanded from 3,901 to **5,587 faculty members** across 24 universities.  
> **Task 5 Progress (Sep 10, 2026):** Completed Stages 2–3 of Task 5 — acquired 4 new faculties (SWU Education 107, SSRU Education 53, TU Law 32 with 188 curated publications, TBS Business 102) + ThaiJO OJS3 multi-wave enrichment + deployed canonical deduplication via `merge_duplicate_faculties.py --by-name` → **5,685 faculty records, 42.4% with verified publications, 35.7% with h > 0** (details in `05_find_expert_researchers.md`).

---

## Overview & Database Audit Baseline

| Data Entity | Current Count | Data Completeness | Expansion Priority |
| :--- | :---: | :--- | :---: |
| **1. Research Labs (`research_labs`)** | **30 labs** | Complete fields, but sparse distribution (avg 2-4 labs/university) | 🔥 **Tier 1 (Critical)** |
| **2. Faculty Coverage (`faculties`)** | **3,901 records** | Clustered in Top 5 universities; sparse in SWU, Burapha, MFU, Silpakorn | 🔥 **Tier 2 (High)** |
| **3. Faculty Enrichment (`faculties`)** | **3,901 records** | Missing Email (29.9%), Avatar (63.6%), Research Interests (42.8%) | ⚡ **Tier 3 (Medium)** |
| **4. Regional Courses (`courses`)** | **4,162 curricula** | 100% field completeness; concentrated in Top 6 universities, gaps in regional graduate programs | 📌 **Tier 4 (Normal)** |
| **5. Elite Researchers (`faculties`)** | **2,030/5,685 with h-index** | h > 0: 35.7%, verified publications: 42.4%; Business/Marketing gaps closed (TBS h ≥ 20 = 4); Education & Law rosters expanded | 🏆 **Tier 1–2 (High Impact)** |

---

## Task Breakdown & Roadmap Index

1. **[`01_research_labs_expansion.md`](./01_research_labs_expansion.md)**
   - **Target:** Expand national flagship research laboratories from 30 to 70–100 labs.
   - **Focus Domains:** AI, Robotics, Smart Energy, BioMed, HealthTech, Advanced Materials.
   - **Target Institutions:** CU, MU (Siriraj/Ramathibodi), CMU, KMUTT (FIBO), KMITL, NSTDA (NECTEC/MTEC/BIOTEC/NANOTEC).

2. **[`02_faculty_coverage_expansion.md`](./02_faculty_coverage_expansion.md)**
   - **Target:** Scale faculty coverage in sparse universities (< 30 members).
   - **Focus Institutions:** Srinakharinwirot University (13), Burapha University (14), Mae Fah Luang University (25), Silpakorn University (29), Prince of Songkla University (129).
   - **Methodology:** Headless Autonomous Pipeline Runner (`run_acquire.py`) + WikiSkill directory patterns.

3. **[`03_faculty_profile_enrichment.md`](./03_faculty_profile_enrichment.md)**
   - **Target:** Enrich profile completeness for baseline faculty members.
   - **Focus Areas:**
     - Populate missing profile images across 2,482 records (reduces UI avatar fallback reliance).
     - Populate missing research interests across 1,670 records (improves semantic match accuracy).

4. **[`04_regional_curriculum_expansion.md`](./04_regional_curriculum_expansion.md)**
   - **Target:** Expand graduate curricula (Master's and Ph.D.) in regional universities.
   - **Focus Institutions:** Prince of Songkla University, Naresuan University, Ubon Ratchathani University, University of Phayao, Thaksin University.

5. **[`05_find_expert_researchers.md`](./05_find_expert_researchers.md)** ⭐ (High Impact)
   - **Target:** Acquire high-impact researchers across all academic disciplines and ensure data quality hygiene.
   - **Focus Areas:** Enrich h-index and citation metrics for remaining unindexed faculty; capture top scholars in Education, Law, Public Administration, Tourism, and Cybersecurity; update `_fetch_distinguished_advisors` to rank by h-index; strip duplicate titles across 5,409 rows; execute cross-university deduplication.
   - **Audit Scripts:** `backend/scripts/audits/field_taxonomy.py`, `field_coverage_gap_analysis.py`, `elite_researcher_gap.py`.

---

## Operating Invariants for Resumption (Zero-Bypass & Local-First)
1. **Always Run Against Local Database:** Verify Docker Postgres is running (`docker compose up -d`). All commands must connect to `localhost:5432` to avoid Supabase egress quotas.
2. **Zero Synthetic Data:** Execute only via the Autonomous Pipeline / established crawlers per `AGENTS.md`. Never hallucinate or hardcode mock records.
3. **Verified Production Synchronization:** Use `python backend/scripts/sync_local_to_supabase.py` only when staged local data is fully verified and ready for cloud release.
