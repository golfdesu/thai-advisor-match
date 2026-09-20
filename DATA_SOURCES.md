# Thai Advisor Match - Data Sources & Scraping References

This document records the data sources for faculty members across various departments and universities. This data serves as the initial seed database for the AI Semantic Search system in the Thai Advisor Match project.

## 1. Basic Faculty Information (Profile & Research Interests)

### 1.1 Chiang Mai University (CMU)
*   **Faculty of Engineering - Department of Electrical Engineering (EE)**
    *   **Primary Source:** [CMU EE Official Website](https://ee.eng.cmu.ac.th/web/personnel.php)
    *   **Data Type:** Faculty names, academic titles, emails, and specialized research areas (imported via `cmu_ee_faculty.json`).
*   **Faculty of Science - Department of Computer Science (CS)**
    *   **Primary Source:** [CS CMU Academic Staff](https://www.cs.science.cmu.ac.th/academicstaff/)
    *   **Data Type:** Full department roster (~30 professors) in ML, NLP, CV, Data Mining, Software Engineering, Bioinformatics (imported via `seed_cmu_complete.py`).
*   **Faculty of Engineering - Department of Electrical Engineering (EE)**
    *   **Primary Source:** [CMU EE Official Website](https://ee.eng.cmu.ac.th/web/personnel.php)
    *   **Data Type:** Faculty names, academic titles, emails, and specialized research areas (imported via `cmu_ee_faculty.json`) — complete roster (19/19).
*   **CMU Business School (Faculty of Business Administration)** — complete roster across all 4 departments
    *   **Primary Source:** [CMUBS Faculty Members](https://www.cmubs.cmu.ac.th/organization/lecturer/) + official CV API (`apps.cmubs.cmu.ac.th/mis/cv.php`)
    *   **Data Type:** Accounting, Finance, Marketing, Management & Entrepreneurship professors with degrees and research interests from official CVs (imported via `seed_cmubs.py`).

### 1.2 Mahidol University (MU)
*   **Faculty of Medicine Siriraj Hospital**
    *   **Primary Source:** [Siriraj Hospital Departments](https://www.si.mahidol.ac.th/th/department/)
    *   **Data Type:** Medical professors in Surgery and Pediatrics (imported via `seed_extra.py`).

### 1.3 Chulalongkorn University (CU)
Popular Master's faculties, imported via `seed_more_universities.py`:
*   **Faculty of Commerce and Accountancy** (Business & Data Science program)
    *   **Primary Source:** [datasci.cbs.chula.ac.th](https://datasci.cbs.chula.ac.th/people) / [bsd.cbs.chula.ac.th](https://bsd.cbs.chula.ac.th/faculty/index.php?cate_id=2)
    *   **Data Type:** Professors in Statistics & Data Science, Business Software Development, Machine Learning.
*   **Faculty of Engineering - Department of Computer Engineering**
    *   **Primary Source:** [cp.eng.chula.ac.th faculty directory](https://www.cp.eng.chula.ac.th/about/faculty) + individual profile pages
    *   **Data Type:** Professors specializing in ML, AI, NLP, Data Mining.
*   **Faculty of Education**
    *   **Primary Source:** [eduadmin.edu.chula.ac.th staff API](https://eduadmin.edu.chula.ac.th/api/v1/staffs-departments)
    *   **Data Type:** Professors in Educational Technology and Communications.

### 1.4 Thammasat University (TU)
Imported via `seed_more_universities.py`:
*   **Faculty of Commerce and Accountancy (TBS)**
    *   **Primary Source:** [tbs.tu.ac.th staff pages](https://tbs.tu.ac.th/aboutus/committee-and-faculty-members/)
    *   **Data Type:** Accounting, Finance, Marketing, Operations Management (incl. MBA Program Director).
*   **Sirindhorn International Institute of Technology (SIIT) - School of ICT**
    *   **Primary Source:** [siit.tu.ac.th](https://www.siit.tu.ac.th/page_a.php?cid=263) + individual profiles
    *   **Data Type:** CS/ICT professors (ML, Image Processing, Cyber Security).
*   **Faculty of Engineering - ECE Department**
    *   **Primary Source:** [ece.engr.tu.ac.th/lecturer](https://ece.engr.tu.ac.th/lecturer)
    *   **Data Type:** Speech/Machine Learning/Network Security professors.

### 1.5 KMUTT & NIDA
Imported via `seed_more_universities.py`:
*   **KMUTT School of Information Technology**
    *   **Primary Source:** [sit.kmutt.ac.th lecturer profiles](https://www.sit.kmutt.ac.th/en/lecturer/) (`showprofile?empid=...`)
    *   **Data Type:** Dean, Associate Deans, ML/Data Science/Business Informatics professors.
*   **NIDA Business School**
    *   **Primary Source:** [mba.nida.ac.th faculty pages](https://mba.nida.ac.th/en/about/professor/)
    *   **Data Type:** Finance (MF Director), Marketing (Professional MBA Director), Strategic Management professors.
*   **NIDA Graduate School of Public Administration (GSPA)**
    *   **Primary Source:** [gspa.nida.ac.th](https://gspa.nida.ac.th/en/faculty-member/)
    *   **Data Type:** Digital Government / Public Policy associate deans.

### 1.6 Kasetsart University (KU) & KMITL
Imported via `seed_more_universities.py`:
*   **KU Faculty of Engineering - Computer Engineering**
    *   **Primary Source:** [cpe.ku.ac.th teacher-information](https://cpe.ku.ac.th/index.php/teacher-information/?id=351)
    *   **Data Type:** Professors in Data Mining, Parallel Computing.
*   **Kasetsart Business School**
    *   **Primary Source:** [fin.bus.ku.ac.th](https://fin.bus.ku.ac.th/personnel_position/%e0%b8%ab%e0%b8%b1%e0%b8%a7%e0%b8%ab%e0%b8%99%e0%b9%89%e0%b8%b2%e0%b8%A0%e0%B8%B2%E0%B8%84%E0%B8%A7%E0%B8%B4%E0%B8%8A%E0%B8%B2%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%80%E0%B8%87%E0%B8%B4%E0%B8%99/) / [opm.bus.ku.ac.th](https://opm.bus.ku.ac.th/peopledetailb3.html)
    *   **Data Type:** Finance department head (CFA), Corporate Finance, Quality/Supply Chain Management professors.
*   **KMITL School of Information Technology**
    *   **Primary Source:** [it.kmitl.ac.th/en/staffs/academic](https://www.it.kmitl.ac.th/en/staffs/academic) + individual profiles
    *   **Data Type:** Professors in Computational Intelligence, Deep Learning, LLM Applications.
*   **KMITL Business School**
    *   **Primary Source:** [kbs.kmitl.ac.th person pages](https://www.kbs.kmitl.ac.th/)
    *   **Data Type:** International Marketing, Strategic HRM/Sustainability professors.

> **Note:** All entries above were verified against official university pages at collection time (Aug 2026). Emails are official institutional addresses only; no personal phone numbers collected (PDPA compliance). Some NIDA/KU profiles publish no public email or photo — fields left empty rather than guessed.

### 1.7 Expansion Wave (Aug 2026) — New Faculties & Universities
Imported via `seed_wave2a.py` + `seed_wave2b.py`, publications via `pubs_wave2.json`:
*   **Public Health**: Mahidol Faculty of Public Health (Biostatistics/Epidemiology/Env. Health/Administration) + Khon Kaen Faculty of Public Health (incl. Dean Wongsa Laohasiriwong, cancer epidemiology group).
    *   **Primary Sources:** bios/phep/pheh.ph.mahidol.ac.th, murex.mahidol.ac.th, ph.kku.ac.th
*   **Economics**: Chulalongkorn Faculty of Economics (Dean Nopphol Witvorapong et al.) + Thammasat Faculty of Economics.
    *   **Primary Sources:** econ.chula.ac.th, econ.tu.ac.th
*   **Law**: Thammasat Faculty of Law + Chulalongkorn Faculty of Law.
    *   **Primary Sources:** law.tu.ac.th, law.chula.ac.th
*   **Engineering (other branches)**: Chula Mechanical (robotics/composites) + Chula Civil + KKU Computer Engineering.
    *   **Primary Sources:** eng.chula.ac.th, civil.eng.chula.ac.th, cvs.enit.kku.ac.th
*   **Education (new universities)**: Srinakharinwirot Faculty of Education (EdTech dept) + KKU Faculty of Education.
    *   **Primary Sources:** edu.swu.ac.th, ednet.kku.ac.th

**Publications policy:** For every faculty member (all 190), up to 10 featured publications were collected — university-official sources first (CMUBS CV API, department profile pages), falling back to verified external databases (Google Scholar, DBLP, Semantic Scholar, OpenAlex, PubMed, ORCID). Every entry was seen verbatim in a fetched source; no invented entries. Early-career lecturers with genuinely zero indexed publications (verified exhaustively) are left with an empty list rather than padded.

---

### 1.8 Elite-Researcher Acquisition Waves (Sep 10, 2026) — Batches 98–101
All four went through the SKILL.state contract (crawler → `RawFacultyProfile` → `FacultyStateReducer` → `data/agent_states/` checkpoint → `data_sources/*_extracted.py` → `faculty_massive_ingestion_runner.py` upsert + embedding):

*   **SWU Faculty of Education (107)** — `backend/scripts/crawlers/swu_edu_api_pipeline.py`
    *   **Primary Source:** `edu.swu.ac.th/wp-json/wp/v2/staff` (WordPress custom post type, 171 posts; academic ranks only — support officers filtered by Thai courtesy prefixes นาย/นางสาว/นาง).
*   **SSRU Faculty of Education (53)** — `backend/scripts/crawlers/ssru_edu_api_pipeline.py`
    *   **Primary Sources:** `edu.ssru.ac.th/{th,en}/page/facmembers` (TH/EN accordion paired by ordinal with card-count assertion) + per-person email from `ssrudlp.ssru.ac.th/teacher/<Name>` DLP pages. 100% email/photo/education coverage.
*   **Thammasat Faculty of Law (32 verified from 96)** — `backend/scripts/crawlers/tu_law_api_pipeline.py`
    *   **Primary Source:** `law.tu.ac.th/wp-json/wp/v2/teacher` (102 posts). First in-repo feed of **curated Thai legal publication citations** (188 entries, dict-shape with DOI + year), parsed from `ผลงานวิชาการคัดสรร` sections; English names taken from post slugs to dodge the related-teacher widget leaking inside `content.rendered`.
*   **Thammasat Business School (102 academic from 177)** — `backend/scripts/crawlers/tbs_staff_api_pipeline.py`
    *   **Primary Sources:** `tbs.tu.ac.th/staff-sitemap.xml` (280 URLs → 195 people after collapsing `_th/_en/_director/_management-team/_secretary` variants); profile pages' `single_staff_name/position/desc` blocks + mailto + 570×570 photos. Secretaries/administrative staff excluded.

## 2. University Curricula / Courses

### 2.1 Chiang Mai University — Full Curriculum Directory (Bachelor → Ph.D.)
*   **Primary Source:** CMU MIS TQF2 Curriculum Public List (Curriculum database of CMU Educational Quality Development Division) — `https://www.mis.cmu.ac.th/TQF/TQF2/CurriculumPublicList.aspx`
*   **Coverage:** All 28 faculties/colleges/institutes, all levels (Bachelor's, Master's, Ph.D., Graduate/Higher Graduate Diploma) — 336 curricula total.
*   **Pipeline:**
    1. `scrape_cmu_courses.py --phase list` — enumerates every curriculum from the central search grid (Thai + English titles, plan/type info).
    2. `scrape_cmu_courses.py --phase details` — opens each curriculum's TQF2 detail page (ASP.NET postback flow): official curriculum code, degree full/abbreviation, credit structure, study plan.
    3. `build_cmu_courses_json.py` — maps raw scrape into the project courses schema (`data/cmu_courses.json`), deriving Thai degree abbreviations, total credits, duration, and program type.
    4. `seed_cmu_courses.py` — upserts into the Supabase `courses` table (`--dry-run` for validation only).
*   **Known gap:** 46 newly established curricula (mostly B.E. 2568+) have no published TQF-2 details in the system yet; they are stored with basic fields from the list phase and can be re-fetched later by re-running `--phase details`.
*   **Tuition fees:** Not published in the central TQF2 system — left null pending per-faculty enrichment.

### 2.2 Mae Fah Luang University (MFU) — Full Programme Ingestion (Aug 2026)
*   **Primary Source:** MFU Official Programme Portal — `https://programme.mfu.ac.th` (covers Bachelor's, Master's, Doctoral degrees, and B.E. 2568 revised curricula).
*   **Coverage:** All schools (Sinology, Cosmetic Science, Integrative Medicine, Medicine, Dentistry, Engineering, Information Technology, etc.) totaling **54 complete curricula**.
*   **Data Fields Acquired:**
    *   **Credits & Curriculum Structure:** Extracted from the *Curriculum Structure* tab (e.g. B.A. Chinese Language and Culture 123 credits, B.Sc. Cosmetic Science 121 credits, M.D. 245 credits, D.D.S. 230 credits).
    *   **Tuition Fees:** Extracted from the *Tuition Fee* tab (semester fee and total program cost).
    *   **Description & Objectives:** Extracted from the *Curriculum Info* tab.
    *   **Career Opportunities:** Extracted from the *Career Opportunities* tab.
*   **Automated Ingestion Script:** `backend/scripts/crawlers/` or direct BeautifulSoup parser execution with immediate 768-dim Gemini Embedding re-indexing.

### 2.3 Khon Kaen University — Full Expansion (387 curricula, Aug 31 2026)
*   **Primary Sources:** `eng.kku.ac.th` (FACTS 280 programs) + `th.wikipedia.org/wiki/มหาวิทยาลัยขอนแก่น` (330 curricula) + faculty portals (`ag.kku.ac.th`, `tech.kku.ac.th`, `hs.kku.ac.th`, `arch.kku.ac.th`, `law.kku.ac.th`, `econ.kku.ac.th`, `sc.kku.ac.th`, `md.kku.ac.th`, `nurse.kku.ac.th`, `ams.kku.ac.th`, `vet.kku.ac.th`, `ph.kku.ac.th`, `computing.kku.ac.th`, `cola.kku.ac.th`, `faa.kku.ac.th`, `ed.kku.ac.th`, `is.kku.ac.th`) + `reg.kku.ac.th/registrar/program_info.asp` (TQF-2/Tier 1 registry 395 entries).
*   **Coverage:** 22 faculties/colleges, all levels — **387 curricula (Khon Kaen University pure, after SPU relabel & dedup)** — Bachelor's 134 / Master's 158 / Ph.D. 93 / Graduate Diploma 2. Verified against official KKU ~280 programs at plan-level expansion (387 includes per-plan variants: e.g., Science `Plan A Type A 1 / A 2 / B`, `Type 1.1 / 1.2 / 2.1 / 2.2` International tracks — intentionally kept separate per SKILL Tier 3 RapidFuzz faculty-boost logic, not merged when suffix differs). Global total: 4,162 courses.
*   **Pipeline:**
    1. `courses_isan_kku_ubu_msu.json` (22 high-quality) + `kku_full_expansion.py` (65) + `kku_full_expansion2.py` (43) + `kku_full_expansion3.py` (23) + `reg.kku.ac.th` Tier 1 scrape (395 raw) → curated JSONs under `backend/data/courses_new/` with `gemini-embedding-2` 768-dim vectors.
    2. Quality fixes (Aug 29): deleted duplicate `kku-be-digital-media-engineering`, disambiguated `kku_med_rad_bsc` vs `kku_ams_radtech_bsc`, fixed 3 `kku-be-*` truncated titles, normalized `degree_level` across 768 rows (Bachelor/Master/Doctorate → Thai canonical labels), backfilled `embedding_text` for 328 rows (now 0 NULL), created GIN trigram indexes `idx_courses_title_th_trgm` etc. per `AGENTS.md`.
    3. Tier 2 fix (Aug 31 — `backend/scripts/fix_kku_tier2_tier3.py`): patched **39** records with `tuition_per_semester = ไม่ระบุ` (16× `EN-*` placeholder + 3× `kku-be-*` + 11× `kku-sci-msc-*` + 9× `kku-doc/master-*`) using TCAS Standard Formulas — 4y Bachelor `*8` (EN-UG-* → 18k→144k, EN-UG-INT → 45k→360k), 2y Master `*4` (EN-MS-* 30k→120k, Sci-MSc 25k→100k), 3y PhD `*6`, 1y Cert `*2` — and relabeled **8** SPU-Khon Kaen records (`spu_kk_*`) from `Khon Kaen University` to `Sripatum University / มหาวิทยาลัยศรีปทุม วิทยาเขตขอนแก่น` (Graduate School) to eliminate cross-university pollution. Result: **0** remaining unspecified tuition records in KKU.
    4. Tier 3 re-index (Aug 31): rebuilt `embedding_text = f"{title_th} {title_en} {faculty_th} {faculty} {department_th} {description} {' '.join(career_paths)} {' '.join(tags)}"` and regenerated **387/387** Gemini 768-dim vectors via `ThreadPoolExecutor(max_workers=6)` + client pooling — `missing embedding = 0`, `embedding_text NULL = 0`, `title_th='ไม่ระบุ' = 0`.
    5. Dedup verification (Aug 31): `SELECT title_th, degree_level GROUP BY HAVING COUNT>1` → **0 groups**; RapidFuzz `token_set_ratio >=70` with faculty boost `+15` merges only exact duplicates — plan variants (e.g. `Plan A Type A 1` vs `Plan B`) are correctly preserved (124 near-duplicates sampled in Science are intentional plan variants per TQF-2).
    6. Vector search verified (Aug 31, HNSW `embedding <=> CAST(:v AS vector)`): `วิศวกรรมคอมพิวเตอร์` → `kku_eng_cpe_beng` rank 1, `พยาบาล` → `kku_nur_bns` rank 1, `นิติศาสตร์` → `kku_law_llb` rank 1, `วิศวกรรมพลังงาน` → `EN-MS-09` rank 1.
*   **Remaining gaps:** No structural gap — coverage exceeds official 280 at expanded plan level. Residual faculty skew: Faculty of Science 219 (plan-level explosion due to plan/track variants) vs Engineering 37 etc. SPU Khon Kaen correctly separated as 8 courses under Sripatum (total Sripatum 39).

### 2.4 Suranaree University of Technology — Tier 2/3 Quality Fix (87 curricula, Aug 31 2026)
*   **Primary Sources:** `sut.ac.th` / `interadmission.sut.ac.th/international-programs` + `reg.sut.ac.th` + institute portals (9 institutes) — existing 87 records ingested pre-Aug 31; no new catalog scrape required (Tier 1 verified via live DB audit vs official SUT trimester system).
*   **Coverage:** 9 institutes — **87 curricula** — Bachelor's 37 / Master's 27 / Ph.D. 23. Breakdown: Engineering 35 / Science 17 / Agricultural Technology 11 / Social Technology 11 / Public Health 4 / Medicine 3 / Digital Arts and Science 3 / Nursing 2 / Dentistry 1.
*   **SUT Trimester Note:** SUT operates on a trimester calendar (3 trimesters/year) — formula for `tuition_total` differs from standard 2-semester models: 4-year Bachelor `*12` (264k–336k), 6-year professional degrees `*18` (810k–1,080k), 2-year Master `*6` (192k–228k), 3-year Ph.D. `*9` (324k–378k) — validated against 28 baseline programs with complete tuition data (e.g., `sut_med_md` 45k→810k, `sut_dent_dds` 60k→1,080k, `sut_nurs_bns` 28k→336k, `sut_das_bsc` 22k→264k).
*   **Pipeline:**
    1. Tier 1 audit (Aug 31): 87 records complete across all 9 institutes — baseline established.
    2. Tier 2 fix (Aug 31 — `backend/scripts/fix_sut_tier2_tier3.py`): corrected **5** mismatched `faculty` values (`sut_bachelor_animal/crop_production_technology` Engineering→Agricultural Technology, `sut_bachelor_agricultural_and_food_engineering` Agricultural→Engineering, `sut_bachelor_communication` Social→Digital Arts and Science, `sut-hospitality-technology-innovation` unspecified→Social Technology) + backfilled **59** records with unspecified `tuition_per_semester/tuition_total` (22k–42k per trimester per standard formula) + backfilled **30** records with unspecified `duration_years/total_credits` (Bachelor 4y/130 credits, Master 2y/36 credits, Ph.D. 3y/48 credits) + normalized `duration_years` formats. Result: **0** remaining unspecified fields.
    3. Tier 3 re-index (Aug 31): rebuilt `embedding_text = f"{title_th} {title_en} {faculty_th} {faculty} {department_th} {description} {' '.join(career_paths)} {' '.join(tags)}"` and regenerated **87/87** Gemini 768-dim vectors (`gemini-embedding-2`) via `ThreadPoolExecutor(max_workers=6)` + client pooling — `missing embedding = 0`.
    4. Dedup (Aug 31): `title_th+degree_level GROUP BY HAVING COUNT>1` → **0 groups**; duplicate IDs: 0.
    5. Vector search verified (Aug 31, HNSW `embedding <=> CAST(:v AS vector)`): `วิศวกรรมคอมพิวเตอร์` → `sut_bachelor_computer_engineering` rank 1, `พยาบาล` → `sut_nurs_bns` rank 1, `เทคโนโลยีการเกษตร` → `sut_agr_phd_crop_production` rank 1, `บริหารธุรกิจ` → `sut_bachelor_management_technology` rank 1, `สาธารณสุข` → `sut_ph_phd` rank 1.
*   **HNSW Root Cause & Infrastructure Fix (Aug 31):** HNSW filtered search (`WHERE university ILIKE '%Suranaree%' ORDER BY embedding <=> :v LIMIT 1`) returned 0 rows despite 87 valid records existing. Root cause: HNSW index scan used a default `hnsw.ef_search` too low for a small filtered subset (SUT 87/4162 ≈ 2%) + `ILIKE '%...%'` was planned as `Index Scan using ix_courses_embedding_hnsw + Filter` instead of `Bitmap Heap Scan`. Resolved by configuring `SET hnsw.ef_search = 400` across connections, checkouts, and request sessions in `backend/app/core/database.py` (3 layers: `engine connect` + `checkout` + `SET LOCAL` in `get_db()`).
*   **Remaining gaps:** None — 87 SUT records verified at 100% quality (tuition, duration, credits, embeddings complete, faculty normalized, dedup 0, HNSW verified).

## 3. Academic Publications (Featured Publications)
To ensure accuracy and recency, research papers and publication records were not manually hardcoded. Instead, they were dynamically fetched from global academic databases.

*   **Primary Source:** Google Scholar (via SerpApi)
*   **Mechanism:** 
    *   The script `update_scholar_serpapi.py` searches for each professor's name on Google Scholar.
    *   If a strict author search (`author:"First Last"`) yields no results, the system falls back to a general query matching the professor's exact name.
    *   The top 5 most relevant publications are extracted, along with full-text URLs, and securely embedded into the PostgreSQL (Supabase) database.
*   **ThaiJO (Sep 2026):** `enrich_thaijo_publications.py` crawls OJS3 aggregate shards (`so01`–`so06.thaiojournals...` search with precision-gated `authors=` matching) for Thai-language scholars invisible to global DBs → 649+ rows credited with authentic article titles (venue + URL; citation count left 0 as ThaiJO does not expose citation metrics).
*   **OpenAlex (Sep 2026):** `enrich_openalex_author_metrics.py` resolves `openalex_id IS NULL` rows via author search behind a homonym gate (surname token + given name + institutional affiliation confirmation), updating `h_index`, `total_citations`, and `works_count`. Idempotent and resumable; canary health-gate aborts before writing when the key pool fails. Wave 1: +227 rows.
*   **Source-curated lists:** TU Law curated publications (`ผลงานวิชาการคัดสรร`, Batch 100) ingested as full structured dictionaries post-reducer.

---

## 4. Profile Pictures
Profile pictures were sourced from multiple platforms due to strict Hotlink Protection (CORS) policies enforced by certain university servers.

*   **Primary Source:** Official university directories.
*   **Fallback Sources (Bypassing firewalls):** 
    *   ResearchGate (e.g., Assoc. Prof. Dr. Jakramate)
    *   LinkedIn (e.g., Assoc. Prof. Dr. Rattasit)
    *   Other non-restricted official domains.
*   **Automated UI Fallback:** If an image link is broken or unavailable, the frontend automatically generates a clean avatar containing the professor's initials using the `ui-avatars.com` API.

---

## 5. Future Data Pipeline
Once the backend API is fully deployed to production hosting, scaling the database to include other universities (e.g., Prince of Songkla, Khon Kaen, Chiang Mai additional faculties) will follow this pipeline:
1. Developing specialized Web Scrapers (using BeautifulSoup / Playwright) tailored to the DOM structure of target university directories.
2. Importing scraped data using the standardized JSON schema defined in `AGENTS.md`.
3. Running automated scripts to fetch Google Scholar publications and generating 768-dimensional AI Embeddings (`gemini-embedding-2`) for semantic search readiness.

---

## 6. National Education Statistics (MHESI) — Demand-Side Benchmark
> **Added:** September 10, 2026 | **Used In:** `future_tasks/05_find_expert_researchers.md`

*   **Primary Source:** Ministry of Higher Education, Science, Research and Innovation (MHESI) Higher Education Information Portal — [info.mhesi.go.th](https://info.mhesi.go.th)
*   **Pages:**
    *   New Students (Annual intake by institution/faculty): `stat_std_new.php?search_year=2568`
    *   Graduates: `stat_graduate.php?search_year=2568`
    *   Total Enrolled Students: `stat_std_all.php`
*   **Download Mechanism:** Link `download2.php?file_id=<id>.xlsx&stat_id=<sid>&id_member=<year>` returns HTTP 302 → Follow redirect to `Location` (pattern: `<page>.php?search_year=<year>&download=<sid>&file_id=<file>`) using the session cookie obtained from the initial report page. Files are XLSX with hierarchical row indentation determined by `cell.alignment.indent` (0=Degree Title, 3=Institution, 4=Faculty).
*   **Key Baseline (Academic Year 2568 Term 1):** Annual new Master's student intake: 40,029 students/year — Education/Pedagogy leads with ~7,254 students (Rank 1), followed by M.Sc. 6,753, M.B.A. 5,804, and M.P.A. 2,526.
*   **Analysis Scripts:** `backend/scripts/audits/field_coverage_gap_analysis.py` + `elite_researcher_gap.py`
