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
- **Canonical merge (`enrichment/canonical_faculty_merge.py`):** 179 merged-university strings resolved via email/id-prefix evidence; variant labels unified ((TBS)/(KKBS)/(CBS)/CAMT/SIIT/CMMU/JGSEE/SGtech/สำนักวิชาววิทยาศาสตร์ typo/SUT program suffixes); composite labels split by department evidence (CU+MU allied/medtech → CU สหเวชศาสตร์ 27 + MU เทคนิคการแพทย์ 10; KU agro/vet split by id prefix; Siriraj+Rama label retained — rows carry only dept evidence, no university split possible without fabrication; Silpakorn arts split by dept).
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
- **TU Pharmacy (1 → 43):** homepage nav reveals `/academicstaff` (42 profiles, emails partially cross-domain: some ภญ. keep mahidol/chula addresses — legit joint appointments).
- **Bug fix (wave1 files):** contamination regex had stripped `@` from emails (sayamon.schula.ac.th); regex extended with `:@`, all 6 sparse datasets regenerated with corrected emails, re-ingested (wave-1 rows updated in-place; no new inserts).
- **Ingestion:** Batches 88–90 → +298 records, 298/298 embedded; 3 residual missing-embedding rows repaired post-run. Final DB: **5,359 faculties, 0 missing embeddings**. Semantic spot-checks: vet-orthopedic query → CMU/CU/KU vets top-5; clinical-pharmacy query → TU Pharmacy top-5.

### [2026-09-10] Sparse-Famous-Faculty Wave 3 (7 faculties across 5 universities, +228)
- **Method:** batch DNS/academic-density probing of 55 candidate subdomains (2 rounds) → SERPAPI key rotation (key[0] exhausted, key[1] live) for exact faculty names → WP REST API enumeration (`wp-json/wp/v2/pages`) to reveal hidden staff pages (KU Sports Sci `?page_id=521/359` → `/lecturer/`, `/staff/`).
- **Acquisitions:** CMU Agriculture `agro.cmu.ac.th/mis2/personnel/personal_new.php` → 80 (was 4); KKU Architecture `arch.kku.ac.th/org-staff-academic` → 59 (was 2); CU Institute of Asian Studies `ias.chula.ac.th/personnel/` → 27 (was 1); KU Sports Sci & Health `sportsscience.kps.ku.ac.th/lecturer/` → 24 (was 1); MU Institute of Nutrition `inmu.mahidol.ac.th/th/advisors/` + `/executive/` → 23 (was 3); KU Veterinary Technology `vettech.ku.ac.th/vettech` + `/vetnurse` → 9 (was 2); CMU Fine Arts → 6 (was 5, partial roster behind Elementor sub-pages).
- **Blocked confirmed:** KU Architecture (roster behind `ku-work.ku.ac.th` login), MU Vet (no roster in DOM/XHR), CU FAA (Incapsula persists), ~20 DNS-dead subdomains logged in `leading_thai_universities.md`.
- **Ingestion:** Batches 91–97 → +228 records, 228/228 embedded; 23 residual rows repaired post-run. Final DB: **5,587 faculties, 0 missing embeddings**. Spot-checks: KKU landscape-arch → KKU Arch top-4; nutrition → INMU top-4; Asian-studies → IAS top-4; agriculture → CMU Agri top-4 (0.80+ similarity).
