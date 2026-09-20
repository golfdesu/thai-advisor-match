# Task 5: Elite Researcher Discovery & Gap Remediation

> **Priority:** 🔥 Tier 1–2 (Directly linked to Tasks 2 and 3)  
> **Recorded:** September 10, 2026  
> **Audit Database:** Local Docker PostgreSQL (`localhost:5432 / advisor_match`) — 5,587 faculty records at task opening; **currently 5,685 records** post-Batches 98–101 and deduplication.  
> **Audit Scripts Available:**
> - `backend/scripts/audits/field_coverage_gap_analysis.py` (sparse discipline analysis)
> - `backend/scripts/audits/field_taxonomy.py` (shared 57-discipline taxonomy)
> - `backend/scripts/audits/elite_researcher_gap.py` (elite scholar gap detection)

---

## 1. Baseline Research Data Summary (Updated Post-Dedup Sep 10)

| Metric | Value |
| :--- | :---: |
| Total Faculty | Initial: **5,497** → Current: **5,685 records** (Batches 98–101 added +322 academics; `--by-name` dedup purged 283 duplicate rows) |
| Faculty with `h_index` > 0 | **2,030 records (35.7%)** — Wave 1 added +227, name dedup consolidated donor records (2,050 → 2,030); OpenAlex Wave 2 queued for quota reset |
| Faculty with `total_citations` | ~2,000 records |
| Faculty with `featured_publications` | 1,750 → **2,413 records (42.4%)** — ThaiJO Waves 1–4 (+~900) and TU Law curated citations (+188 records) |
| **Unindexed Research Profiles** | `openalex_id IS NULL` stands at **2,093 rows** (unattempted — resumable) |
| Mean h-index (among indexed) | 14.1 |
| Maximum h-index | 121 (Michael Doyle, CU Chemistry) |

**Key Bias:** OpenAlex indexing primarily matches STEM and Health Sciences (due to Latin publication names). Social Sciences and Humanities scholars publishing in Thai journals (ThaiJO) require separate bibliographic harvesting via `enrich_thaijo_publications.py`.

---

## 2. 🏆 Top Scholars Baseline (Ready for "Distinguished Advisors" Feature)

| Scholar | University | h-index | Citations | Discipline |
| :--- | :--- | ---: | ---: | :--- |
| Michael Doyle | Chulalongkorn University | 121 | 88,361 | Chemistry / Pharmacy |
| Prof. Dr. Soottawat Benjakul | Prince of Songkla University | 117 | 61,450 | Biochemistry / Food Science |
| Asst. Prof. Dr. Chayanist Asvatanakuldee | Chulalongkorn University | 108 | 41,864 | Pharmacy |
| Asst. Prof. Jenni | Chulalongkorn University | 102 | 37,089 | Pharmacy |
| Prof. Dr. Somchai Wongwises | KMUTT | 101 | 42,309 | Energy / Thermal Engineering |
| Asst. Prof. Warit Mitrthamsiri | Mahidol University | 98 | 39,130 | Medicine |
| Prof. Dr. Prinya Chindaprasirt | Khon Kaen University | 92 | 32,737 | Civil Engineering / Materials |
| Prof. Dr. Philip Hallinger | Mahidol University | 86 | 31,192 | Education (rare high citation in Social Sciences) |
| Prof. Dr. Metha Wanapat | Khon Kaen University | 49 | 9,558 | Veterinary Science / Animal Nutrition |

---

## 3. 🚨 High-Demand Disciplines vs. Elite Faculty Gaps (Priority Matrix)

Benchmarked against MHESI demand data (Academic Year 2568 Term 1 new Master's intake = 40,029 students/year; source: `info.mhesi.go.th/stat_std_new.php`):

| Academic Field | Annual Master's Demand | DB Faculty Count | Faculty with h ≥ 20 | Status (Sep 10 Post-Stage 3) |
| :--- | ---: | ---: | ---: | :--- |
| **Education & Pedagogy** | ~7,254 | 206 → **340** | 0 (max h=18) | 🟡 Roster expanded (SWU + SSRU + CU); Thai scholars sparsely indexed in OpenAlex; 205 with publications |
| **Public Administration (M.P.A.)** | ~2,830 | 70 → 67* | **1** (max h=77) | 🟡 *Post-dedup; 1 top scholar established |
| **Law** | ~1,622 | 282 → **328** | 0 (max h=7) | 🟡 **188 curated publications** added (TU Law); primary citations reside in ThaiJO |
| **Nursing** | ~1,534 | 250 | 6 | 🟡 Deficit in top-tier scholars |
| **Public Health** | ~1,428 | 233 | 6 | 🟡 Deficit in top-tier scholars |
| **Political Science** | ~1,331 | 199 | 1 | 🟡 |
| **Tourism & Hospitality** | High ongoing | 77 | 0 | ⚫ **Skipped** — Tourism directory sources unreachable (ConnectError) |
| **Business Administration / Marketing** | High (National Association) | 95 → **149** | 0 → **4** (max h=37) | ✅ **Gap Closed** — TBS 102 scholars (Batch 101) established first cohort with h ≥ 20 |
| **Cybersecurity** | Very high labor demand | 85 | 2 | ⚫ **Skipped** — Network sources unreachable; existing entries ingested |
| **HCI / UX** | High labor demand | 39 | 0 | ⚫ **Skipped** — No reachable directories |
| **Educational Technology** | High labor demand | 20 | 0 | 🔴 Critical gap |
| **Logistics & Supply Chain** | High labor demand | 85 | 0 | 🔴 Critical gap |
| **Architecture** | ~202 | 82 | 0 | 🔴 Max h = 4 |
| **Psychology** | — | 166 | 0 | 🔴 Max h = 6 |
| **History & Archaeology** | — | 60 | 0 | 🔴 Critical gap |

*Well-covered disciplines with high citation density:* Biotechnology/Biochemistry (26 scholars h ≥ 40), Medicine (18), Energy (13), Civil Engineering (9), Chemistry (3), Materials (2).

---

## 4. 🐛 Data Quality Anomalies Identified During Audit

1. **Duplicate Titles in Names (5,409 rows = 97%):** `full_name_th` redundant with `academic_title_th` (e.g. `academic_title_th='ศ.ดร.'` and `full_name_th='ศ.ดร. สุทธิเขตต์...'`), resulting in doubled UI rendering ("ศ.ดร.ศ.ดร. สุทธิเขตต์...").
   - **Fix:** Strip titles in Pydantic presentation DTOs or normalize column data directly.
2. **Cross-University Duplicates:** Discovered cross-institution duplicates (e.g. "Bin Zhao", h=87, citations=22,690, duplicated under TU and CU with distinct IDs).
   - **Fix:** Canonical deduplication via OpenAlex ID and RapidFuzz token matching.
3. **Unclassifiable Faculty (750 rows):** Lacking research interests or possessing ambiguous department descriptors.

---

## 5. 🐛 Backend Fix: `_fetch_distinguished_advisors` Ranking
File: `backend/app/api/routes_universities.py` (`_fetch_distinguished_advisors`).
Previously fetched the first 25 records with `research_interests` without sorting by `h_index` or `total_citations`.
- **Quick Win Fix:**
  ```python
  .order_by(FacultyDB.h_index.desc().nullslast(), FacultyDB.total_citations.desc().nullslast())
  ```
  Preserves existing department distribution (`seen_departments`).

---

## 6. Action Plan & Implementation Stages

### Stage 1 — Quick Wins (Code Changes Without Scraping) ✅ Completed Sep 10, 2026
- [x] Updated `_fetch_distinguished_advisors` to `ORDER BY h_index DESC NULLS LAST` in `routes_universities.py`.
- [x] Resolved duplicate title rendering in Pydantic DTOs (`schema.py` `_clean_display_name` + model validators across `FacultyMember` and `FacultyCardSchema`).
- [x] Deduplicated via `openalex_id`: Created `scripts/audits/merge_duplicate_faculties.py` (purged 90 duplicate rows, preserved 12 dual-affiliation groups, re-pointed lab references).
- [x] Re-pointed 5 orphan research lab references (`ku_agro_001` etc.) to authentic top-ranked faculty in matching disciplines.

### Stage 2 — Research Data Enrichment (Zero-Bypass Policy) ✅ Completed Sep 10, 2026
- [x] Deployed `backend/scripts/enrich_openalex_author_metrics.py` (OpenAlex author search → `h_index`, `citations`, `works`).
  - **Homonym Gate:** Full surname token match + given name match + institutional verification.
  - 100% exact-id recovery on ground-truth evaluation.
  - Idempotent and resumable: Checkpoints written to `backend/data/agent_states/openalex_author_metrics_apply.json`.
- [x] **Wave 1 Execution:** 2,036 targets → resolved +227 scholars with h-index (1,823 → 2,050 = 37.3%).
  - Added canary health-gate to prevent writing corrupted sentinels during API outages.
  - Resumable command: `python backend/scripts/enrich_openalex_author_metrics.py --apply --workers 4`.
- [x] Checkpointing enforced via `backend/data/agent_states/`.

### Stage 3 — Targeted Acquisition for Deficit Disciplines (`data-acquire-faculty-elites`) ✅ Completed Sep 10, 2026
Completed 4 new batches through the full SKILL.state Reducer lifecycle:

| Batch | Pipeline / Source | Yield | Highlights |
| :--- | :--- | ---: | :--- |
| 98 | `crawlers/swu_edu_api_pipeline.py` — SWU Education WordPress API | **107** | Filtered administrative staff via courtesy prefix filtering |
| 99 | `crawlers/ssru_edu_api_pipeline.py` — SSRU Education Accordion + DLP | **53** | 100% email, photo, and degree coverage across 9 departments |
| 100 | `crawlers/tu_law_api_pipeline.py` — TU Law WordPress API (102 posts) | **32** | **188 curated publications (dict shape + DOI)** |
| 101 | `crawlers/tbs_staff_api_pipeline.py` — TBS Staff Sitemap (195 candidates) | **102** | 78 emails, 90 degrees, 570×570 photos, 17 non-academics filtered |

**Impact on Priority Gaps:**
- Education: 206 → **340 faculty** (205 with publications).
- Law: 282 → **328 faculty** (182 with publications, primarily from TU Law curated records).
- Business & Marketing (TBS): 95 → **149 faculty, 4 scholars with h ≥ 20 (max 37)** — first closed gap in Stage 3.
- Resolved legacy rows lacking emails using `merge_duplicate_faculties.py --by-name` (5,872 → **5,685**).

---

## 7. Task 5 Summary Table

| Metric | Before | After |
| :--- | ---: | ---: |
| Total Faculty | 5,497 | **5,685** |
| Faculty with `featured_publications` | ~1,750 (31.8%) | **2,413 (42.4%)** |
| ThaiJO-Credited Scholars | 551 | **656** (Waves 1–4, +105) |
| Faculty with `h_index` > 0 | 2,050 (37.3%) | **2,030 (35.7%)** |
| Missing Vector Embeddings | 0 | **0** |
| Disciplines with Closed Elite Gap (h ≥ 20) | — | **Business / Marketing (TBS: 4 scholars, max h=37)** |

**Permanent Tooling Added to Repository:**
1. `enrich_openalex_author_metrics.py` — OpenAlex metrics harvester with homonym and canary gates.
2. `enrich_thaijo_publications.py` — OJS3 crawler for Thai academic journals across social sciences.
3. `merge_duplicate_faculties.py --by-name` — Title-normalized deduplication with metric inheritance and re-embedding.
4. `backfill_embeddings.py` — Vector embedding backfill utility.
5. Standardized acquisition pipelines (SWU, SSRU, TU Law, TBS) serving as blueprints for future faculty waves.
