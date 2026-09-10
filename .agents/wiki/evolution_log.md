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
