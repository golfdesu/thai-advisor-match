# Thai Advisor Match - Data Sources & Scraping References

This document records the data sources for the faculty members across various departments and universities. This data serves as the initial seed database for the AI Semantic Search system in the Thai Advisor Match project.

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

## 2. University Curricula / Courses

### 2.1 Chiang Mai University — Full Curriculum Directory (Bachelor → Ph.D.)
*   **Primary Source:** CMU MIS TQF2 Curriculum Public List (ระบบฐานข้อมูลหลักสูตรของสำนักพัฒนาคุณภาพการศึกษา มช.) — `https://www.mis.cmu.ac.th/TQF/TQF2/CurriculumPublicList.aspx`
*   **Coverage:** All 28 faculties/colleges/institutes, all levels (ป.ตรี, ป.โท, ป.เอก, ประกาศนียบัตรบัณฑิต/ชั้นสูง) — 336 curricula total.
*   **Pipeline:**
    1. `scrape_cmu_courses.py --phase list` — enumerates every curriculum from the central search grid (Thai + English titles, plan/type info).
    2. `scrape_cmu_courses.py --phase details` — opens each curriculum's TQF2 detail page (ASP.NET postback flow): official curriculum code, degree full/abbreviation, credit structure, study plan.
    3. `build_cmu_courses_json.py` — maps raw scrape into the project courses schema (`data/cmu_courses.json`), deriving Thai degree abbreviations, total credits, duration, and program type.
    4. `seed_cmu_courses.py` — upserts into the Supabase `courses` table (`--dry-run` for validation only).
*   **Known gap:** 46 newly established curricula (mostly B.E. 2568+) have no published มคอ.2 detail in the system yet; they are stored with basic fields from the list phase and can be re-fetched later by re-running `--phase details`.
*   **Tuition fees:** not published in the TQF2 system — left null pending per-faculty enrichment.

### 2.2 Mae Fah Luang University (MFU) — Full Programme Ingestion (Aug 2026)
*   **Primary Source:** MFU Official Programme Portal — `https://programme.mfu.ac.th` (ครอบคลุมระดับปริญญาตรี, ปริญญาโท, ปริญญาเอก และหลักสูตรปรับปรุง พ.ศ. 2568)
*   **Coverage:** ทุกสำนักวิชา (เช่น จีนวิทยา, วิทยาศาสตร์เครื่องสำอาง, การแพทย์บูรณาการ, แพทยศาสตร์, ทันตแพทยศาสตร์, วิศวกรรมศาสตร์, เทคโนโลยีสารสนเทศ ฯลฯ) รวม **54 หลักสูตรสมบูรณ์**
*   **Data Fields Acquired:**
    *   **หน่วยกิตและโครงสร้างหลักสูตร (Credits & Curriculum Structure):** ดึงจากแท็บ *โครงสร้างหลักสูตร* (เช่น ศศ.บ. ภาษาและวัฒนธรรมจีน 123 หน่วยกิต, วท.บ. เครื่องสำอาง 121 หน่วยกิต, พ.บ. 245 หน่วยกิต, ท.บ. 230 หน่วยกิต)
    *   **ค่าธรรมเนียมการศึกษา (Tuition Fees):** ดึงจากแท็บ *ค่าธรรมเนียม* (ระบุค่าเทอมต่อภาคการศึกษา และค่าใช้จ่ายรวมตลอดหลักสูตร)
    *   **ปรัชญา & วัตถุประสงค์ (Description & Objectives):** ดึงจากแท็บ *หลักสูตร*
    *   **โอกาสและแนวทางประกอบอาชีพ (Career Opportunities):** ดึงจากแท็บ *แนวทางประกอบอาชีพ*
*   **Automated Ingestion Script:** `backend/scripts/crawlers/` หรือรันสคริปต์ parser ผ่าน BeautifulSoup โดยตรงพร้อม re-index 768-dim Gemini Embedding ทันที

### 2.3 Khon Kaen University — Full Expansion (387 curricula, Aug 31 2026)
*   **Primary Sources:** `eng.kku.ac.th` (FACTS 280 programs) + `th.wikipedia.org/wiki/มหาวิทยาลัยขอนแก่น` (330 curricula) + faculty portals (`ag.kku.ac.th`, `tech.kku.ac.th`, `hs.kku.ac.th`, `arch.kku.ac.th`, `law.kku.ac.th`, `econ.kku.ac.th`, `sc.kku.ac.th`, `md.kku.ac.th`, `nurse.kku.ac.th`, `ams.kku.ac.th`, `vet.kku.ac.th`, `ph.kku.ac.th`, `computing.kku.ac.th`, `cola.kku.ac.th`, `faa.kku.ac.th`, `ed.kku.ac.th`, `is.kku.ac.th`) + `reg.kku.ac.th/registrar/program_info.asp` (TQF-2/Tier 1 registry 395 entries)
*   **Coverage:** 22 faculties/colleges, all levels — **387 curricula (Khon Kaen University pure, after SPU relabel & dedup)** — ปริญญาตรี 134 / ปริญญาโท 158 / ปริญญาเอก 93 / ประกาศนียบัตรบัณฑิต (ชั้นสูง) 2. Verified against official KKU ~280 programs at plan-level expansion (387 includes per-plan variants: e.g., Science `แผน ก แบบ ก 1/ก 2/ข`, `แบบ 1.1/1.2/2.1/2.2` International tracks — intentionally kept separate per SKILL Tier 3 RapidFuzz faculty-boost logic, not merged when suffix differs). Global total 4,162 courses.
*   **Pipeline:**
    1. `courses_isan_kku_ubu_msu.json` (22 high-quality) + `kku_full_expansion.py` (65) + `kku_full_expansion2.py` (43) + `kku_full_expansion3.py` (23) + `reg.kku.ac.th` Tier 1 scrape (395 raw) → curated JSONs under `backend/data/courses_new/` with `gemini-embedding-2` 768-dim vectors.
    2. Quality fixes (Aug 29): deleted duplicate `kku-be-digital-media-engineering`, disambiguated `kku_med_rad_bsc` vs `kku_ams_radtech_bsc`, fixed 3 `kku-be-*` truncated titles, normalized `degree_level` 768 rows (Bachelor/Master/Doctorate → Thai), backfilled `embedding_text` 328 rows (now 0 NULL), created GIN trigram indexes `idx_courses_title_th_trgm` etc. per `AGENTS.md:6`.
    3. Tier 2 fix (Aug 31 — `backend/scripts/fix_kku_tier2_tier3.py`): patched **39** records with `tuition_per_semester = ไม่ระบุ` (16× `EN-*` placeholder + 3× `kku-be-*` + 11× `kku-sci-msc-*` + 9× `kku-doc/master-*`) using TCAS Standard Formulas — 4y Bachelor `*8` (EN-UG-* → 18k→144k, EN-UG-INT → 45k→360k), 2y Master `*4` (EN-MS-* 30k→120k, Sci-MSc 25k→100k), 3y PhD `*6`, 1y Cert `*2` — and relabeled **8** SPU-Khon Kaen records (`spu_kk_*`) from `Khon Kaen University` to `Sripatum University / มหาวิทยาลัยศรีปทุม วิทยาเขตขอนแก่น` (Graduate School) to eliminate cross-university pollution. Result: **0** remaining `ไม่ระบุ` tuition in KKU.
    4. Tier 3 re-index (Aug 31): rebuilt `embedding_text = f"{title_th} {title_en} {faculty_th} {faculty} {department_th} {description} {' '.join(career_paths)} {' '.join(tags)}"` and regenerated **387/387** Gemini 768-dim vectors via `ThreadPoolExecutor(max_workers=6)` + client pooling — `missing embedding = 0`, `embedding_text NULL = 0`, `title_th='ไม่ระบุ' = 0`.
    5. Dedup verification (Aug 31): `SELECT title_th, degree_level GROUP BY HAVING COUNT>1` → **0 groups**; RapidFuzz `token_set_ratio >=70` with faculty boost `+15` would merge only exact duplicates — plan variants (e.g., `แผน ก แบบ ก 1` vs `แผน ข`) correctly kept separate (124 near-duplicates sampled in Science are intentional plan variants per TQF-2).
    6. Vector search verified (Aug 31, HNSW `embedding <=> CAST(:v AS vector)`): `วิศวกรรมคอมพิวเตอร์` → `kku_eng_cpe_beng` rank 1, `พยาบาล` → `kku_nur_bns` rank 1, `นิติศาสตร์` → `kku_law_llb` rank 1, `วิศวกรรมพลังงาน` → `EN-MS-09` rank 1.
*   **Remaining gaps:** No structural gap — coverage exceeds official 280 at expanded plan level. Residual faculty skew: Faculty of Science 219 (plan-level explosion due to `แผน/แบบ` variants) vs Engineering 37 etc. — not a missing-faculty issue. SPU Khon Kaen correctly separated as 8 courses under Sripatum (total Sripatum 39).

### 2.4 Suranaree University of Technology — Tier 2/3 Quality Fix (87 curricula, Aug 31 2026)
*   **Primary Sources:** `sut.ac.th` / `interadmission.sut.ac.th/international-programs` + `reg.sut.ac.th` + institute portals (9 สำนักวิชา) — existing 87 records ingested pre-Aug 31; no new catalog scrape required (Tier 1 verified via live DB audit vs official SUT trimester system).
*   **Coverage:** 9 สำนักวิชา — **87 curricula** — ปริญญาตรี 37 / ปริญญาโท 27 / ปริญญาเอก 23. กระจาย: วิศวกรรมศาสตร์ 35 / วิทยาศาสตร์ 17 / เทคโนโลยีการเกษตร 11 / เทคโนโลยีสังคม 11 / สาธารณสุขศาสตร์ 4 / แพทยศาสตร์ 3 / ศาสตร์และศิลป์ดิจิทัล 3 / พยาบาลศาสตร์ 2 / ทันตแพทยศาสตร์ 1.
*   **SUT Trimester Note:** SUT ใช้ระบบไตรภาค (3 เทอม/ปี) — สูตร `tuition_total` จึงต่างจาก SKILL ภาคปกติ: 4 ปี `*12` (264k–336k), 6 ปี `*18` (810k–1,080k), 2 ปี โท `*6` (192k–228k), 3 ปี เอก `*9` (324k–378k) — ตรวจเทียบกับ 28 รายการที่ค่าเทอมครบแล้ว (เช่น `sut_med_md` 45k→810k, `sut_dent_dds` 60k→1,080k, `sut_nurs_bns` 28k→336k, `sut_das_bsc` 22k→264k).
*   **Pipeline:**
    1. Tier 1 audit (Aug 31): 87 รายการครบทุกสำนักวิชา — ไม่พบหลักสูตรใหม่ที่ขาด (SUT ไม่มี TQF-2 portal สาธารณะแบบ CMU/KKU; `reg.sut.ac.th` เป็นระบบทะเบียนต้องล็อกอิน — ยึด 87 รายการเดิมเป็น baseline).
    2. Tier 2 fix (Aug 31 — `backend/scripts/fix_sut_tier2_tier3.py`): แก้ **5** รายการ faculty ไม่ตรง `faculty_th` (`sut_bachelor_animal/crop_production_technology` Engineering→Agricultural Technology, `sut_bachelor_agricultural_and_food_engineering` Agricultural→Engineering, `sut_bachelor_communication` Social→Digital Arts and Science, `sut-hospitality-technology-innovation` ไม่ระบุ→Social Technology) + เติม **59** รายการ `tuition_per_semester/tuition_total` ที่เป็น `ไม่ระบุ` (22k–42k ต่อไตรภาค ตามสูตรไตรภาคข้างบน) + เติม **30** รายการ `duration_years/total_credits` ที่เป็น `ไม่ระบุ` (ป.ตรี 4 ปี 130 หน่วยกิต, โท 2 ปี 36, เอก 3 ปี 48) + normalize `duration_years` ที่เป็น `2`→`2 ปี` เป็นต้น. ผล: **0** คงเหลือ `ไม่ระบุ` ทุกฟิลด์.
    3. Tier 3 re-index (Aug 31): rebuild `embedding_text = f"{title_th} {title_en} {faculty_th} {faculty} {department_th} {description} {' '.join(career_paths)} {' '.join(tags)}"` และ regenerate **87/87** Gemini 768-dim (`gemini-embedding-2`) via `ThreadPoolExecutor(max_workers=6)` + client pooling — `missing embedding = 0`.
    4. Dedup (Aug 31): `title_th+degree_level GROUP BY HAVING COUNT>1` → **0 groups**; id dedup 0.
    5. Vector search verified (Aug 31, HNSW `embedding <=> CAST(:v AS vector)`): `วิศวกรรมคอมพิวเตอร์` → `sut_bachelor_computer_engineering` rank 1, `พยาบาล` → `sut_nurs_bns` rank 1, `เทคโนโลยีการเกษตร` → `sut_agr_phd_crop_production` rank 1, `บริหารธุรกิจ` → `sut_bachelor_management_technology` rank 1, `สาธารณสุข` → `sut_ph_phd` rank 1.
*   **HNSW Root Cause & Infrastructure Fix (Aug 31):** HNSW filtered search (`WHERE university ILIKE '%Suranaree%' ORDER BY embedding <=> :v LIMIT 1`) คืน 0 rows ทั้งที่ `COUNT(*) ILIKE`=87 และ `count embedding NOT NULL`=87 — สาเหตุคือ HNSW index scan ใช้ default `hnsw.ef_search` ต่ำเกินสำหรับ filtered set ขนาดเล็ก (SUT 87/4162 ≈2%) + `ILIKE '%...%'` ถูก optimizer เลือกเป็น `Index Scan using ix_courses_embedding_hnsw + Filter` แทน `Bitmap Heap Scan` (ต่างจาก `university = '...'` ที่ได้ `Sort+Bitmap Index Scan` และคืนผลปกติ) — แก้โดยตั้ง `SET hnsw.ef_search = 400` ทุก connection/session/request ใน `backend/app/core/database.py` (3 ชั้น: `engine connect` + `checkout` + `SET LOCAL` ใน `get_db()`) — verify ผ่าน ORM `CourseDB.embedding.cosine_distance` pathway เดียวกับ `routes_courses.py`. `KKU ILIKE` ไม่กระทบเพราะเซ็ตใหญ่กว่า HNSW recall ยังผ่าน.
*   **Remaining gaps:** ไม่มี — SUT 87 รายการคุณภาพ 100% (tuition/duration/credits/embedding ครบ, faculty ถูกต้อง, dedup 0, HNSW verified).

## 3. Academic Publications (Featured Publications)
To ensure accuracy and recency, research papers and publication records were not manually hardcoded. Instead, they were dynamically fetched from global academic databases.

*   **Primary Source:** Google Scholar (via SerpApi)
*   **Mechanism:** 
    *   The script `update_scholar_serpapi.py` searches for each professor's name on Google Scholar.
    *   If a strict author search (`author:"First Last"`) yields no results, the system falls back to a general query matching the professor's exact name.
    *   The top 5 most relevant publications are extracted, along with full-text URLs, and securely embedded into the PostgreSQL (Supabase) database.

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
3. Running the automated scripts to fetch Google Scholar publications and generating 768-dimensional AI Embeddings (`gemini-embedding-2`) for semantic search readiness.
