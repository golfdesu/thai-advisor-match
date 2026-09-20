# Faculty Data Quality Audit & Discovery Runbook
<!-- Reference: WikiSkill - Academic Quality Verification & Discovery Framework -->

Comprehensive operational runbook for data auditing, defect remediation, and discovering unlisted or newly appointed faculty members across all academic ranks (อ., อ.ดร., ผศ., รศ., ศ., and researchers).

---

## 0. Executive Technical Guardrails

1. **Local-First Zero-Egress Invariant**: All data acquisition, cleaning, vector embeddings, and database modifications MUST execute strictly against the local containerized PostgreSQL database (`localhost:5432/advisor_match`). Never stream or sync unverified data directly to remote Supabase.
2. **Universal Console Encoding**: Every CLI and ingestion script must reconfigure stdout to prevent Windows `cp1252` encoding crashes:
   ```python
   import sys
   if hasattr(sys.stdout, "reconfigure"):
       sys.stdout.reconfigure(encoding="utf-8")
   ```
3. **Headless Execution & Checkpointing**: Keep crawling, regex normalization, and deduplication headlessly in Python. Always checkpoint snapshots in `backend/data/agent_states/` before committing changes to PostgreSQL.

---

## Stage 1: Name & Field Hygiene Audit

### 1.1 Completeness, Script Validation & Hidden Unicode
* **Target Defects**:
  - Null or empty names: `first_name IS NULL` or `last_name IS NULL`.
  - Script cross-contamination: Thai characters leaking into English name columns (`[฀-๿]`).
  - Invisible Unicode artifacts: Zero-Width Space (`​`), Byte Order Mark (`﻿`), Non-Breaking Space (`\xa0`) that break exact SQL lookups and drop RapidFuzz matches to 0.
* **Verification Logic**:
  ```python
  # Clean invisible unicode characters
  clean_text = raw_text.replace('​', '').replace('﻿', '').replace('\xa0', ' ').strip()
  # Verify Latin-only script for English name columns
  assert re.match(r"^[a-zA-Z\s\-\.\']+$", clean_en_name)
  ```
* **Remediation**:
  - Transliterate authentic names using Royal Thai General System (RTGS) constrained by institutional email local-part hints (`@university.ac.th`).
  - Enforce canonical dictionary mappings in `backend/scripts/enrichment/update_english_names.py`.

### 1.2 Anonymization & Placeholder Contamination
* **Target Defects**:
  - Automated PDPA redaction artifacts: `first_name='REDACTED'` or `last_name='REDACTED'`.
  - Scraper generic fallback tokens: `Member`, `Faculty`, `Unknown`, `Staff`, `None`.
* **Verification Query**:
  ```sql
  SELECT id, university_th, faculty_th, full_name_th, first_name, last_name, email
  FROM faculties
  WHERE UPPER(first_name) IN ('REDACTED', 'MEMBER', 'FACULTY', 'UNKNOWN', 'STAFF', 'NONE')
     OR UPPER(last_name) IN ('REDACTED', 'MEMBER', 'FACULTY', 'UNKNOWN', 'STAFF', 'NONE');
  ```
* **Remediation**: Re-extract authentic names from `full_name_th` or institutional email addresses (`user@domain.ac.th`), romanize cleanly, and replace placeholders.

### 1.3 Leaked Academic Titles & Organizational Roles
* **Target Defects**:
  - Title prefixes leaking into `first_name`: `Prof.`, `Assoc. Prof.`, `Asst. Prof.`, `Dr.`, `Lect.`, `Mr.`, `Ms.`, `Mrs.`, `Ait En`.
  - Academic roles and degrees trailing in `last_name`: `Academic Expert`, `Professor Emeritus`, `Ph.D.`, `Dba Finance`, `Editnp`.
* **Verification Regex**:
  ```python
  TITLE_PREFIX_PATTERN = re.compile(
      r"^(?:Ait\s+En|Asst\s+Prof|Assoc\s+Prof|Associate\s+Prof|Assistant\s+Prof|Assoc|Asst|Prof|Dr|Mr|Ms|Mrs)\b\.?\s*",
      re.IGNORECASE
  )
  ROLE_SUFFIX_PATTERN = re.compile(
      r"\s+(?:Professor\s+Emeritus|Academic\s+Expert|Emeritus|Expert|Editnp|Ph\.?D?|Dba\s+Finance|Dba).*$",
      re.IGNORECASE
  )
  ```
* **Remediation**: Strip prefixes and suffixes, re-partition tokens into `first_name` and `last_name`, apply `.title()`, and validate against `^[a-zA-Z\s\-\.\']+$`.

### 1.4 International & Foreign Faculty Bilingual Symmetry
* **Target Defects**:
  - Foreign faculty members with valid English names whose `full_name_th` was truncated by scrapers to solitary title prefixes (e.g. `th='อ.'`, `th='ดร.'`, `th='รศ.ดร.'`).
  - Prepending redundant default Thai titles to English names (e.g. `"อ. Dr. James Moran"`).
* **Verification Logic**:
  ```python
  is_truncated = (
      r.full_name_th in ['อ.', 'ดร.', 'ผศ.', 'รศ.', 'ศ.', 'อ.ดร.', 'ผศ.ดร.', 'รศ.ดร.']
      or len((r.full_name_th or "").strip()) <= 2
  ) and (r.first_name and len(r.first_name) > 1)
  ```
* **Remediation**:
  - Format `full_name_th` as a bilingual representation combining title and Latin name (e.g. `อ. Morten Bennedsen`, `ดร. Xuefeng Zhang`).
  - Order title alternations **Longest Match First** (`Assoc. Prof. Dr.` before `Assoc. Prof.`, `Mrs.` before `Mr.`).

---

## Stage 2: Structural Scraper Artifacts Audit

### 2.1 Departmental Header & Breadcrumb Overwrite
* **Target Defects**:
  - Scrapers mistakenly parsing category headers or breadcrumb elements as person names, overwriting dozens of faculty with the same name (e.g. 38 faculty in CMU Pediatrics named `Endocrine Metabolism`).
* **Verification Logic**:
  - Frequency anomaly detection:
    ```sql
    SELECT first_name, last_name, faculty_th, COUNT(*)
    FROM faculties
    GROUP BY first_name, last_name, faculty_th
    HAVING COUNT(*) > 3;
    ```
* **Remediation**:
  - Audit high-frequency identical name clusters within the same faculty.
  - Re-extract authentic names from `full_name_th` and institutional emails using batch RTGS transliteration.

### 2.2 Multi-Person Row Concatenation
* **Target Defects**:
  - Unclosed HTML table cells (`</td>`) or rows (`</tr>`) causing text extractors to merge multiple consecutive personnel into one record (e.g. `อ. พญ. เพ็ญพิชชา ... พญ. วิมลรัฐ ...`).
* **Verification Logic**:
  - Detect embedded title tokens (`พญ.`, `นพ.`, `ดร.`, `ผศ.`, `รศ.`, `Dr.`) occurring after position 10 in personal name columns.
* **Remediation**:
  - Check if individual records already exist for the concatenated persons.
  - Split and quarantine or map cleanly to the primary record without leaving compound entities.

### 2.3 Greedy Boundary-less Thai Title Regex Mutilation
* **Target Defects**:
  - Stripping valid Thai name characters because the regex lacked strict delimiters (Thai has no word boundaries):
    - `นพคุณ` -> `คุณ` (stripped `นพ`)
    - `นพพล` -> `พล` (stripped `นพ`)
    - `ศศินี` -> `ินี` (stripped `ศ`)
    - `ดรุณี` -> `ุณี` (stripped `ดร`)
* **Verification Standard**:
  - Thai title stripping regex MUST require an explicit period or whitespace delimiter:
    ```python
    SAFE_TITLE_REGEX = re.compile(
        r"^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.|"
        r"ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|"
        r"นายแพทย์\s+|แพทย์หญิง\s+|อาจารย์\s+|ผศ\s+|รศ\s+|ศ\s+|ดร\s+|นพ\s+|พญ\s+)\s*",
        re.IGNORECASE
    )
    ```

---

## Stage 3: Advisor Eligibility Verification

Under Ministry of Higher Education, Science, Research and Innovation (MHESI / อว.) regulations, thesis advisors for Master's and Doctoral students must be active faculty members.

### 3.1 Eligibility Audit Checklist
* **Ineligible Groups to Purge / Filter**:
  1. **อาจารย์เกษียณอายุ (Retired Faculty)**: Identified via `role` or `full_name_th` containing `อาจารย์เกษียณอายุ`.
  2. **อดีตคณาจารย์ (Former Faculty)**: Identified via `role` containing `อดีตคณาจารย์` (distinct from "Former Dean/President" who are active professors).
  3. **ศาสตราจารย์เกียรติคุณ (Professor Emeritus)**: Cannot serve as primary thesis advisors (`title` or `full_name_th` containing `ศ.เกียรติคุณ`, `ศาสตราจารย์เกียรติคุณ`, `ศ.คลินิกเกียรติคุณ`, or English role `Professor Emeritus`).
  4. **ผู้ลาศึกษาต่อ (Faculty on Study Leave)**: Personnel on doctoral study leave (`ลาศึกษาต่อ`) who cannot accept graduate students.
  5. **ผู้ถึงแก่อนิจกรรม / เสียชีวิต (Deceased Personnel)**: Verified deceased faculty.
* **Verification Query**:
  ```python
  ineligible = db.query(FacultyDB).filter(
      (FacultyDB.role.like("%อาจารย์เกษียณอายุ%")) |
      (FacultyDB.role.like("%อดีตคณาจารย์%")) |
      (FacultyDB.role.like("%ลาศึกษาต่อ%")) |
      (FacultyDB.full_name_th.like("%ศ.เกียรติคุณ%")) |
      (FacultyDB.full_name_th.like("%ศาสตราจารย์เกียรติคุณ%")) |
      (FacultyDB.academic_title_th == "ศ.เกียรติคุณ") |
      (FacultyDB.academic_title_th == "ศาสตราจารย์เกียรติคุณ")
  ).all()
  ```
* **Remediation Procedure**:
  - Save full snapshot to `backend/data/agent_states/skill_state_purged_former_faculty.json`.
  - Unlink any foreign key references (`research_labs.lead_advisor_id = None`).
  - Purge records from `faculties` table.

---

## Stage 4: Deduplication & Disambiguation Audit

### 4.1 Three-Pass Academic Deduplication (Section 9 Invariant 10)
Execute deduplication across three distinct, ordered passes:
1. **Pass 1: Normalized Thai Name**: Match `full_name_th` (stripped of titles and spaces).
2. **Pass 2: Clean English Name**: Match `(first_name, last_name)` with university match.
3. **Pass 3: Verified Academic Email**: Match unique personal institutional email (excluding shared departmental inboxes like `sci@ku.ac.th`, `dent@cmu.ac.th`).

### 4.2 Lifetime Research Metric Preservation Invariant
In every deduplication merge:
* `survivor.total_citations = max(survivor.total_citations or 0, donor.total_citations or 0)`
* `survivor.h_index = max(survivor.h_index or 0, donor.h_index or 0)`
* `survivor.research_interests = union_lists(survivor.research_interests, donor.research_interests)`
* `survivor.featured_publications = union_lists(survivor.featured_publications, donor.featured_publications)`
* Re-point all `ResearchLabDB.lead_advisor_id` referencing donor to survivor.
* Recompute 768-dimensional Gemini vector embedding for survivor.
* Cleanly delete donor record.

### 4.3 Orthographic & Surname Disambiguation Hazards
* **Prohibit Last-Name-Only Fallbacks**: Thai academic families frequently have multiple relatives in the same faculty (e.g. Dr. Kanes Chattipakorn vs. Prof. Nipon Chattipakorn). Never match on family name alone.
* **Phonetic & Consonantal Verification**: Distinct consonants produce distinct persons (e.g. `ผศ.ดร. ศศิธร ตรงจิตภักดี` in Agro-Industry vs. `ดร. สศิธร ทองจิตร์ภักดี` in IFRPD). Transliterate faithfully (`Trongchitpakdee` vs. `Thongjitpakdi`) and never merge.
* **Dictionary Key Collisions**: Never declare duplicate keys in static mapping dictionaries. Use composite keys `(first_th, last_th)` for common first names.

---

## Stage 5: Metrics, Vector & Relational Integrity Audit

### 5.1 Author Metric Recovery & Maiden Name Resolution
* **Defect**: Faculty member has `h_index = 0` despite an active international publishing record.
* **Causes**:
  - OpenAlex author ID fragmentation across institutions.
  - Maiden vs. Married surname divergence (e.g. publishing under maiden name while institutional HR lists married surname).
* **Remediation**:
  - Check institutional email local-part for alternate surname spellings.
  - Query Crossref API with polite headers (`mailto:...`) using both maiden and married surnames.
  - Re-aggregate authentic lifetime metrics.

### 5.2 Vector Embedding Completeness & Symmetry
* **Defect**: Null or stale vector embeddings, or vector text out of sync with updated names.
* **Remediation**:
  - Generate canonical embedding text via `build_faculty_embedding_text(faculty)`:
    `"{academic_title_th} {full_name_th} ({first_name} {last_name}), {department_th}, {faculty_th}, {university_th}. Research: {interests}. Publications: {publications}"`
  - Compute 768-dimensional vector via `EmbeddingService`.
  - Verify `embedding IS NOT NULL` and vector dimension = 768.

---

## Stage 6: Unlisted & New Faculty Discovery Workflow

University central faculty directories often suffer from **6 to 24 months of Directory Lag**, failing to reflect newly appointed lecturers ("อ.ดร.") and recently transferred researchers. Use these 5 footprint vectors to discover unlisted faculty:

```text
[ Footprint 1: Deep Subdomains & Program Curricula (TQF 2 / มคอ.2) ]
                                    ↓
[ Footprint 2: University Registrar & Course Schedule Footprints ]
                                    ↓
[ Footprint 3: Recent Affiliated Publication Mining (Crossref / OpenAlex) ]
                                    ↓
[ Footprint 4: New Faculty Research Grants & Seed Funding Footprints ]
                                    ↓
[ Footprint 5: Graduate School Thesis Examination Committee Announcements ]
```

### 1. Deep Subdomain & Program Curriculum Mining (มคอ.2)
* **Mechanism**: Departmental subdomains (`cpe.eng.cmu.ac.th`, `civil.eng.chula.ac.th`) and graduate curriculum handbooks (มคอ.2) update faster than university-level portals.
* **Action**:
  - Crawl isolated departmental subdomains directly at `/people`, `/faculty`, `/staff`.
  - Extract the list of "อาจารย์ผู้รับผิดชอบหลักสูตร" (Program Responsible Faculty) from Master's and Doctoral TQF 2 program documents submitted to MHESI.

### 2. Registrar & Course Syllabus Footprint
* **Mechanism**: Newly appointed faculty must teach courses immediately upon joining, creating active records in the university registrar system months before web profiles exist.
* **Action**:
  - Query university schedule and registrar search portals (`reg.cmu.ac.th`, `mycourseville.chula.ac.th`, `registrar.ku.ac.th`).
  - Extract instructor names for graduate courses (500–800 level), special problems, and seminars.
  - Execute Symmetric Set Difference ($S_{\text{reg}} \setminus S_{\text{db}}$) against the database to isolate unlisted instructors.

### 3. Recent Affiliated Publication Mining
* **Mechanism**: New researchers immediately list their new university affiliation on journal and conference papers upon arrival.
* **Action**:
  - Query OpenAlex / Crossref APIs for papers published in the last 12–24 months filtered by institution:
    `affiliation.institution.id` or `affiliation: "Department of Computer Engineering, Chulalongkorn University"`.
  - Harvest all unique author names.
  - Perform fuzzy matching against `faculties`. Authors with confirmed department affiliations who are absent from `faculties` represent new hires.

### 4. New Faculty Research Grant & Seed Funding Footprints
* **Mechanism**: Almost all newly appointed doctoral lecturers apply for institutional new-researcher grants ("ทุนพัฒนานักวิจัยรุ่นใหม่ / ทุนอาจารย์ใหม่") within their first 12 months.
* **Action**:
  - Download funding announcement PDFs from University Research Administration Divisions (e.g. Ratchadapisek Somphot Endowment Fund at CU, CMU Research Administration).
  - Extract: *Faculty Name, Department, Faculty, Approved Research Title*.
  - This provides verified, authoritative research interests and departmental appointments directly from official administrative decrees.

### 5. Graduate School Thesis Examination Committee Announcements
* **Mechanism**: Master's and Ph.D. thesis defense appointments are published by Graduate Schools and require active academic credentials.
* **Action**:
  - Harvest thesis defense notices and committee appointments from Graduate School portals.
  - Cross-reference committee members serving as "อาจารย์ที่ปรึกษาร่วม" (Co-Advisor) or "กรรมการผู้ทรงคุณวุฒิภายใน" (Internal Committee Member).
  - Ingest new doctoral faculty who are already actively guiding student theses.

---

## 7. Execution Checklist Summary

When completing an audit or new acquisition wave, confirm all 10 checkpoints:

| # | Audit Item | Expected Metric |
|---|---|---|
| 1 | Missing English First Name | **0** |
| 2 | Missing English Last Name | **0** |
| 3 | Thai Characters in English Fields | **0** |
| 4 | Placeholder / Redacted Names (`REDACTED`, `Member`) | **0** |
| 5 | Leaked Titles & Roles in Names (`Asst Prof`, `Expert`) | **0** |
| 6 | Truncated Foreign Names (`th='อ.'`, `th='ดร.'`) | **0** |
| 7 | Ineligible Personnel (Retired, Emeritus, On-Leave) | **0** |
| 8 | Duplicate Faculty Clusters (Thai, English, Email) | **0** |
| 9 | Missing or Invalid 768-dim Vector Embeddings | **0** |
| 10 | Dangling Research Lab Foreign Keys (`lead_advisor_id`) | **0** |
