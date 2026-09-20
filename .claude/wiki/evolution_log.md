# WikiSkill Evolution & Patch Log
<!-- Reference: WikiSkill - Evolution Log (arXiv:2608.27454v1) -->

## [2026-09-01] Initial Wiki Initialization
- **Action:** Compiled foundational knowledge structure for Thai Universities (CMU ME, CPE, EE).
- **Traces Analyzed:** `cmu_robotics_mechatronics_batch` execution traces.
- **Skill Gating Status:** Baseline skills updated to reflect `SKILL.state` runtime and Wiki references.

### [2026-09-06 13:29:41] Wiki Knowledge Compilation
- **Traces Processed:** 34
- **Universities Updated:** leading_thai_universities, thammasat_university, mahidol_university, prince_of_songkla_university, khon_kaen_university, chiang_mai_university, chulalongkorn_university
- **New Verified Endpoints:** 28
- **Dead Links Flagged:** 3

### [2026-09-09] KKU Faculty of Nursing Full Acquisition (Wave 1)
- **Pipeline:** SKILL.state `cli_runner.py` (9 seed URLs, 71 profiles) → `faculty_massive_ingestion_runner.py` Batch 69 → 72 records embedded (768-dim) in local `advisor_match`.
- **Verified Endpoints:** nu.kku.ac.th executives, dept heads, program-coordinator (0 yield — flagged), 7 department pages.
- **Coverage Fix:** KKU Nursing 1 → 72 records; all embedded.

### [2026-09-09] TU Faculty of Engineering Acquisition (Wave 1)
- **Pipeline:** SKILL.state `cli_runner.py` (5 dept seed URLs → 82 profiles) → Batch 70 → 94 records embedded in local `advisor_match` (incl. 13 pre-existing deduped).
- **Verified Endpoints:** ece.engr.tu.ac.th/lecturer, ce/structural, me/professor_rangsit, che/professor; cic /person/ (0 yield — flagged).
- **Blocked Flagged:** sci.tu.ac.th (Incapsula), med.tu.ac.th (PDF-only rosters) — need SPA/PDF strategies per `data-scrape-spa` skill.
- **Coverage Fix:** TU Engineering 13 → 94 records.

### [2026-09-09] PSU Faculty of Science Acquisition (Wave 1)
- **Pipeline:** SKILL.state `cli_runner.py --no-wiki` (4 `personnel-lists` seed URLs → 224 clean profiles, all PSU emails) → Batch 71 → 228 records embedded in local `advisor_match`; 5 transient 503 embedding failures repaired via `embed_missing.py` (missing embeddings now 0).
- **Incident (fixed):** first run auto-seeded cross-faculty wiki URLs (FMS/Law) via `lookup_university_endpoints`, producing contaminated export — deleted before ingestion; restructured PSU wiki into Faculty-Scoped section + added `--no-wiki` flag to `cli_runner.py`.
- **Blocked Flagged:** Medicine (DNS dead; hospital.psu.ac.th → Google Sites org chart), Engineering (SPA, ce.eng JS-redirect only).
- **Coverage Fix:** PSU Science 5 → 228 records.

### [2026-09-09] Canonical Label Hygiene + Wave 2 Acquisition
- **Canonical merge (`enrichment/canonical_faculty_merge.py`):** 179 merged-university strings resolved via email/id-prefix evidence; variant labels unified ((TBS)/(KKBS)/(CBS)/CAMT/SIIT/CMMU/JGSEE/SGtech/สำนักวิชาววิทยาศาสตร์ typo/SUT program suffixes); composite labels split by department evidence (CU+MU allied/medtech → CU Allied Health Sciences (สหเวชศาสตร์) 27 + MU Medical Technology (เทคนิคการแพทย์) 10; KU agro/vet split by id prefix; Siriraj+Rama label retained — rows carry only dept evidence, no university split possible without fabrication; Silpakorn arts split by dept).
- **Source-dataset sync (`canonical_datasets_fix.py`):** 38 dataset files canonicalized so ingestion re-runs don't regress; 317 changed rows re-embedded; SIT/FIBO variants patched in 5 more files.
- **Wave 2 acquisitions:** CMU Public Health `ph.cmu.ac.th/lecturer.php` → 12 records (was 3 incl. variants); MU Nursing `ns.mahidol.ac.th/nurse_th/administrator.html` → 19 (was 3); KKU Science head-dept + env + bio portals → 54 (was 12).
- **Blocked:** KMUTT FIBO staff page & KMITL Medicine staff (JS-rendered, 0 raw HTML), MU Nursing dept pages (intranet), vet.cmu.ac.th / econ.cmu.ac.th / sci.kku.ac.th DNS dead.
- **Final DB state:** 4,347 faculties, 0 merged-university strings, 0 duplicate-variant labels (2 legitimate composite labels remain, evidence-based), 0 missing embeddings.

### [2026-09-10] Sparse-Famous-Faculty Wave 1 (CU CommArts/Arts, MU PT/Music)
- **Trigger:** coverage query flagged famous faculties with ≤5 advisors (66 rows across 7 flagship universities).
- **Tooling added:** `scripts/crawlers/discover_sparse_faculty_seeds.py` (SERPAPI seed discovery, results checkpointed to `data/agent_states/seed_discovery_results.json`), `scripts/crawlers/spa_skill_state_runner.py` (static fetch first, Selenium `app/scrapers/browser_scraper.py` fallback when academic density < 5 — implements `data-scrape-spa` skill contract), `scripts/crawlers/clean_sparse_wave1.py` (deterministic mojibake/transliteration cleaner: strips Cyrillic/Arabic contamination from EN→TH transliterations, EN-fallback names, dedup by email/name).
- **Acquisitions:** CU CommArts `units-personnel` + `department-jr` → 26 (was 2); CU Arts `arts.chula.ac.th/th/team` → 26 (was 21, fills roster; domain = Faculty of ARTS, NOT Fine & Applied Arts — relabeled); MU Physical Therapy `staff_lecturer` → 74 (was 3); MU College of Music `/people/` + `/yamp/faculty-list/` → 203 (was 3; EN-name pages, 5 kept EN-fallback).
- **Blocked flagged:** CU FAA `faa.chula.ac.th` (Incapsula, Selenium bypass failed), CU Vet lecturer roster (XHR-only), CMU Vet vmcmu personnel tabs (XHR-only), CMU Pharmacy `menu/208` (admin-only), TU Pharmacy/Liberal Arts (DNS dead for la/pharmacy subdomains — pharmacy lives at `pharm.tu.ac.th`).
- **Ingestion:** `faculty_massive_ingestion_runner.py` Batches 84–87 → +329 records, 329/329 embedded 768-dim (22 empty-text rebuilds repaired post-run). Final DB: 5,061 faculties, 0 missing embeddings. Semantic spot-check (pgvector HNSW): CommArts/Music queries return expected new faculty in top-5.

### [2026-09-10] Sparse-Famous-Faculty Wave 2 (XHR API breakthroughs: CU Vet, CMU Vet, TU Pharmacy)
- **Tooling added:** `app/scrapers/network_capture.py` (Selenium CDP `Network.responseReceived` + `Network.getResponseBody` capture; optional click-through of tabs) — the breakthrough tool: reveals hidden XHR endpoints and static fallbacks invisible to raw-HTML probing.
- **CMU Vet (3 → 83):** discovered `vmcmu.vet.cmu.ac.th/pages/person/api/fetchDataPerson_api.php?typeData[type]=vet_subject-{1,2}` returning structured JSON (name TH/EN, email, research, branch, scopus/scholar/orcid). Full category switch map extracted from `/pages/person/js/person.js`. Pipeline: `scripts/crawlers/cmu_vet_api_pipeline.py` (API → RawFacultyProfile → FacultyStateReducer) → 82 verified.
- **CU Vet (4 → 178):** new-site XHR dead-ended, but **legacy site `www.vet.chula.ac.th/department/<slug>`** renders full rosters statically — 11 dept slugs crawled → 174 profiles with @chula.ac.th emails (Facebook/500-slug auto-discovered URLs correctly failed).
- **TU Pharmacy (1 → 43):** homepage nav reveals `/academicstaff` (42 profiles, emails partially cross-domain: some pharmacists (ภญ.) keep mahidol/chula addresses — legit joint appointments).
- **Bug fix (wave1 files):** contamination regex had stripped `@` from emails (sayamon.schula.ac.th); regex extended with `:@`, all 6 sparse datasets regenerated with corrected emails, re-ingested (wave-1 rows updated in-place; no new inserts).
- **Ingestion:** Batches 88–90 → +298 records, 298/298 embedded; 3 residual missing-embedding rows repaired post-run. Final DB: **5,359 faculties, 0 missing embeddings**. Semantic spot-checks: vet-orthopedic query → CMU/CU/KU vets top-5; clinical-pharmacy query → TU Pharmacy top-5.

### [2026-09-10] Sparse-Famous-Faculty Wave 3 (7 faculties across 5 universities, +228)
- **Method:** batch DNS/academic-density probing of 55 candidate subdomains (2 rounds) → SERPAPI key rotation (key[0] exhausted, key[1] live) for exact faculty names → WP REST API enumeration (`wp-json/wp/v2/pages`) to reveal hidden staff pages (KU Sports Sci `?page_id=521/359` → `/lecturer/`, `/staff/`).
- **Acquisitions:** CMU Agriculture `agro.cmu.ac.th/mis2/personnel/personal_new.php` → 80 (was 4); KKU Architecture `arch.kku.ac.th/org-staff-academic` → 59 (was 2); CU Institute of Asian Studies `ias.chula.ac.th/personnel/` → 27 (was 1); KU Sports Sci & Health `sportsscience.kps.ku.ac.th/lecturer/` → 24 (was 1); MU Institute of Nutrition `inmu.mahidol.ac.th/th/advisors/` + `/executive/` → 23 (was 3); KU Veterinary Technology `vettech.ku.ac.th/vettech` + `/vetnurse` → 9 (was 2); CMU Fine Arts → 6 (was 5, partial roster behind Elementor sub-pages).
- **Blocked confirmed:** KU Architecture (roster behind `ku-work.ku.ac.th` login), MU Vet (no roster in DOM/XHR), CU FAA (Incapsula persists), ~20 DNS-dead subdomains logged in `leading_thai_universities.md`.
- **Ingestion:** Batches 91–97 → +228 records, 228/228 embedded; 23 residual rows repaired post-run. Final DB: **5,587 faculties, 0 missing embeddings**. Spot-checks: KKU landscape-arch → KKU Arch top-4; nutrition → INMU top-4; Asian-studies → IAS top-4; agriculture → CMU Agri top-4 (0.80+ similarity).

## 2026-09-10 — Elite Researcher & Field-Coverage Audit (Task 05 Created)
- **Trigger:** User requirement to identify high-impact faculty with strong research outputs and identify sparse academic disciplines.
- **Method:** SQL audit + 57-field regex taxonomy (created `backend/scripts/audits/field_taxonomy.py`, `field_coverage_gap_analysis.py`, `elite_researcher_gap.py`) + MHESI national demand data (40,029 new Master's students in Academic Year 2568).
- **Key Findings:**
  - Only 1,912/5,587 (34%) had an h-index; ~3,675 lacked research metrics (skewed toward STEM).
  - High-demand disciplines with zero top scholars (h ≥ 20 = 0): Education & Pedagogy (demand #1: ~7,254/year), M.P.A. (~2,830), Law (282 faculty, max h=6), Tourism, Marketing, HCI/UX, EdTech, Cybersecurity, Architecture, Psychology.
  - Data quality: Duplicate titles in `full_name_th` across 5,409 rows (97%), cross-university duplicates (Bin Zhao, h=87, under both TU and CU).
  - `_fetch_distinguished_advisors` (`routes_universities.py`) did not rank by h_index/citations.
- **Artifacts:** `future_tasks/05_find_expert_researchers.md` + updated `future_tasks/README.md` + `DATA_SOURCES.md` (MHESI source patterns).
- **Next Steps:** Execute Stages 1–4 in `05_find_expert_researchers.md` (quick wins first, then enrichment of 3,675 faculty via OpenAlex/ThaiJO).

## 2026-09-10 (Evening) — Task 05 Quick Wins EXECUTED ✅
- **Fix 1:** `_fetch_distinguished_advisors` (`routes_universities.py`) — `ORDER BY h_index DESC NULLS LAST, citations, publications` (limit 25 → 40). Verified: CU signature displays Doyle (h=121) → Chayanist (h=108) → Jenni (h=102).
- **Fix 2:** Duplicate titles across 5,409 rows → stripped at Pydantic DTO layer (`schema.py`: `_TITLE_CANON_PATTERNS` + `_clean_display_name` + `model_validator` on `FacultyMember` and `FacultyCardSchema`). Sample-500 audit: raw duplicates 433 → post-clean 0. Handles stacked prefixes (`ศ.ดร.ศ.ดร.`), long-form/abbreviation equivalence, and duplicate titles.
- **Fix 3:** Deduplication by `openalex_id` — `scripts/audits/merge_duplicate_faculties.py` (dry-run and `--apply`; merges same-university records only, preserves cross-university records as dual affiliations, unions list fields, inherits scalar values, re-points lab references). Result: 5,587 → 5,497 (-90 rows), 0 orphan embeddings, remaining duplicates = 12 cross-university groups.
- **Fix 4 (Latent Bug):** `/search/cold-email` runtime crash — `req.degree_level` and `req.thesis_topic` did not exist on `ColdEmailRequest` → renamed to `intended_degree` and `research_topic`. Verified HTTP 200 with authentic generation.
- **Fix 5:** 5 orphan labs (`lead_advisor_id` referencing non-existent IDs like `ku_agro_001`) re-pointed to highest h-index faculty in matching disciplines (cassava → Sarote h=48; smart-agri → Peerasak h=39; MFU cosmetic → Mayuree h=27; MFU fungal → Orawan h=32; SUT quantum → Sukhit h=42). Orphan count = 0.
- **Test Status:** 11 passed; 1 pre-existing failure (`test_agentic_pipeline` expects legacy ID scheme `cmu_eng_ee_001` vs reducer's `chiangmaiu_...`).

## 2026-09-10 (Night) — Task 05 Stages 2–3 EXECUTED: OpenAlex Wave 1 + ThaiJO OJS3 Fix + 4 Acquisition Batches ✅
- **OpenAlex (`enrich_openalex_author_metrics.py`):** Wave 1 `--apply` → **+227 h-index** (1,823 → 2,050, 37.3%); homonym gate precision 100% vs ground-truth; 501 rows mistakenly stamped `not_indexed` during key pool outage cleared back to NULL + added **canary health-gate** (known-good probe before stamping sentinels; aborts cleanly with 0 writes if API fails). Wave 2 (1,964 targets) hit quota limits across all 3 keys; canary aborted cleanly with 0 writes.
- **ThaiJO Rewrite:** `enrich_thaijo_publications.py` rewritten to target **OJS3 aggregate shards so01–so06** + precision-gated `authors=` matching; Waves 1–4 → **656 rows credited with authentic ThaiJO publications** (Wave 3: 3,753 targets +352; Wave 4 post-Batch 101: 3,617 targets +274 covering TBS — 48 TBS scholars with publications).
- **Acquisition of 4 Faculties (SKILL.state Complete Lifecycle, Batches 98–101):**
  - Batch 98: `swu_edu_api_pipeline.py` — SWU Education WordPress API → **107 records** (filtered administrative staff via courtesy prefixes).
  - Batch 99: `ssru_edu_api_pipeline.py` — SSRU Education TH/EN accordion + DLP email pages → **53 records** (100% email, photo, degrees, DLP; stripped glued honorifics; delimited soft-wrapped degree lines with `<br>`).
  - Batch 100: `tu_law_api_pipeline.py` — TU Law WordPress API (102 posts) → **32 verified records, 188 curated publications in dict shape + DOI** (first curated legal citations in database; stripped inline jQuery widgets; formatted output via `pprint.pformat`).
  - Batch 101: `tbs_staff_api_pipeline.py` — TBS Staff Sitemap (280 → 195 candidates) → **102 academics** (78 emails, 90 degrees, 570×570 photos; anchored photo regex to avoid site logo).
- **Deduplication Gap Closed:** Reducer pre-check missed legacy rows lacking emails → resolved via **`merge_duplicate_faculties.py --by-name`** (normalizes names, strips titles, merges within university/faculty, unions lists, re-embeds). First pass: 98 groups (5,776 → 5,677); second pass post-Batch 101: 185 groups (5,872 → **5,685**).
- **Impact on Priority Gaps:** Business/Marketing **closed** (TBS: 95 → 149, h ≥ 20 = 0 → 4, max h=37); Education: 206 → 340 (205 with publications); Law: 282 → 328 (182 with publications); Cyber/HCI/Tourism skipped with verified network connection errors.
- **Database Status:** **5,685 faculty, 0 missing embeddings, h > 0: 2,030 (35.7%), publications: 2,413 (42.4%), emails: 3,903 (68.7%)**.

## 2026-09-10 (Late Night) — System Health + Bottleneck Hunt EXECUTED ✅
- **pgvector HNSW Optimization:** `SET hnsw.ef_search=400` previously forced the planner to discard `ix_faculties_embedding_hnsw` → Seq Scan + Sort (15–39ms on unfiltered semantic search). Configured `ef=40 + hnsw.iterative_scan=strict_order` in `core/database.py` `_HNSW_TUNE` (connect + checkout listeners) and removed redundant `SET LOCAL` from `get_db`. Result: Index Scan 2.4ms, verified index usage across courses and labs paths.
- **Cold-Email Generation Optimization (13–36s → 3.4–4.6s):** Switched chain to `gemini-3.5-flash-lite` first with `max_output_tokens=1500`, pruned dead model calls (`gemini-2.5-flash`), and configured `HttpOptions(timeout=60000)` in `genai.Client`. Cached responses return in 28ms.
- **Search N+1 Query Resolution:** Removed unused `embedding_text` from Pydantic conversion, reducing 21 SELECT queries to 1 SELECT query per search request.
- **Missing Indexes Added:** Added GIN trigram indexes on `university_th`, `university`, and `faculty_th`; HNSW indexes on `research_labs.embedding` and `semantic_cache.embedding`; btree index on `ix_faculties_h_index DESC NULLS LAST`; tuned autovacuum scale factors on `faculties`.
- **Signature Programs Query Optimization (653ms → 416ms cold, 17ms warm):** Replaced 32 round-trip queries with batched `GROUP BY (university_th, university)` aggregation and in-memory matching.
- **Semantic Cache Deduplication:** Prevented appending duplicate rows within cosine distance ≤ 0.10. Captured label before `db.commit()` to avoid attribute expiration issues.
- **Frontend Hydration Mismatch Fixes:** Restored Mounted Pattern across 3 hydration mismatch points (`app/page.tsx`, `advisor/[id]`, `labs/[id]`); added sequence-ref to `executeSearch` and cancellation flags to detail effects to guard against stale render races; verified clean `tsc --noEmit` and dev server responses.

## 2026-09-10 (Late Night Part 2) — DSA, Hybrid Search & Cybersecurity Implementation ✅
- **Search Quality Benchmark:** Deployed `scripts/audits/search_quality_benchmark.py` testing 10 bilingual query pairs against quality floors (`th best >= 40 / recall >= 10%`, `en best >= 85 / recall >= 20%`).
- **Score Calibration & Lexicon Expansion:** Rank on unclamped composite scores and apply clamp strictly at display; expanded `THAI_EN_SYNONYMS` from 94 to 139 domain keys, narrowing TH-EN score gap from +23.3 to **+2.4** and raising Thai mean score to 93.1.
- **Hybrid Dense + Lexical Search (Okapi BM25):** Upgraded `dsa_utils.FastInvertedIndex` to standard Okapi BM25 ($k_1=1.2, b=0.75$); added `ThreadSafeInvertedIndex` and `core/corpus_index.py` using ASCII whitespace and Thai character bigrams over 5,685 documents. Thai mean score reached **96.5** with 20/20 top-1 recall.
- **Cybersecurity & Hygiene Hardening:**
  - Modernized OWASP headers (`X-XSS-Protection: 0` per current browser standards, HSTS production-only, disabled `/docs` and `/redoc` in production).
  - Added stale-IP key eviction to `RateLimiter` (amortized sweep every 512 mutations).
  - Deployed tiered rate limiting for AI endpoints (cold-email: 10/min, career-quiz: 15/min, labs-inquiry: 15/min, search: 40/min) with longest-prefix matching.
  - Parameterized SQL queries in `routes_labs.py` and batch operations in `fuzzy_dedup.py`.
  - Removed dead code (`ClientTrie`, unused `Trie` imports) and precompiled regex patterns.
- **Verification:** Verified 11/12 passing tests, benchmark floors satisfied, and clean TypeScript compilation.
