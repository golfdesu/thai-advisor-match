---
name: data-curriculum-tuition-discovery
description: Standardized 3-tier methodology for discovering, auditing, extracting, and reconciling university curriculum structures, tuition fees, and career pathways across any Thai university.
---

# Multi-Tier Curriculum & Tuition Discovery Methodology (TCAS & TQF-2 Cross-University Standardization)

To systematically discover, audit, extract, and reconcile undergraduate and graduate curriculum structures, tuition fees, and career pathways across any Thai university (e.g., CMU, MFU, CU, MU, KU, KKU, TU, KMUTT, KMITL, KMUTNB, PSU, SUT), follow this standardized 3-tier methodology:

## 1. Tier 1: Central Academic Quality & TQF-2 MIS Portals (Comprehensive Program Directory & Structure)
- **Target:** University-wide academic quality assurance / MIS databases (e.g., CMU TQF-2 MIS `mis.cmu.ac.th/TQF`, MFU Programme portal `programme.mfu.ac.th`, CU Central Curriculum Directory `chula.ac.th/academics/programs/`, Mahidol Graduate Sitemap `graduate.mahidol.ac.th`, KKU QA).
- **Data Extracted:** Official curriculum code, degree name (TH/EN), standard Thai degree abbreviation (e.g., วท.บ., วศ.บ., พ.บ., ท.บ., ภ.บ., สพ.บ., ศศ.บ., บธ.บ., น.บ., ศศ.ม., วท.ม., ปร.ด.), full credit breakdown (General Education, Major/Core, Free Electives), duration in years, study plan (Regular vs. Special vs. International), and curriculum philosophy/objectives.
- **Discovery Pattern:** Intercept ASP.NET postbacks, JSON APIs, or multi-tab SPA endpoints. Ensure all faculties (including newly approved curricula and interdisciplinary programs) are cataloged.

## 2. Tier 2: Official TCAS & Central Admission Portals (Real-Time Tuition Fees & Career Opportunities)
- **Target:** University central undergraduate admission and TCAS project discovery systems (e.g., CMU TCAS `admission.reg.cmu.ac.th/tcas/findfaculty.php`, MFU Admission fee tables, mytcas.com university detail endpoints, CU TCAS admission regulations, TU/KU Central Registrar announcements).
- **Data Extracted:** Verified per-semester tuition fees (`tuition_per_semester`), project-specific surcharges (e.g., International programs, Dual-Degree programs, Sandbox tracks like CEDT, Special Programs vs. Regular Programs), target career paths (`career_paths`), and official admission project URLs.
- **Total Tuition Calculation Standard Formulas (`tuition_total`):**
  - **4-Year Bachelor Programs:** `tuition_per_semester * 8`
  - **3.5-Year Sandbox Programs (e.g., CEDT):** `tuition_per_semester * 7`
  - **5-Year Architecture / Education Programs:** `tuition_per_semester * 10`
  - **6-Year Medical / Dental / Pharmacy / Veterinary Programs:** `tuition_per_semester * 12`
  - **2-Year Master's Programs:** `tuition_per_semester * 4` (or trimester/tranche-based total)
  - **3-Year Doctoral Programs:** `tuition_per_semester * 6`

## 3. Tier 3: Automated Fuzzy Reconciler & Zero-Stale Vector Re-Indexing Pipeline
- **Fuzzy Token Matching (`RapidFuzz`):** Reconcile TQF-2 formal program titles against TCAS major names using `fuzz.token_set_ratio` with faculty boost (+15) and international program modifier checks (+20 if both inter, -30 if mismatch). Enforce matching threshold score $\ge 70$.
- **Differential Gap Analysis:** Compare sets between TQF-2 (macro academic registry) and TCAS (active recruitment projects). Flag legacy curricula missing from TCAS and newly launched international tracks missing from TQF-2.
- **Zero-Stale Vector Re-Indexing:** Upon enriching tuition and career paths, re-synthesize `embedding_text` containing:
  ```python
  emb_text = f"{title_th} {title_en} {faculty_th} {faculty} {department_th} {description} {' '.join(career_paths)} {' '.join(tags)}"
  ```
  Immediately calculate 768-dimensional Gemini embeddings (`gemini-embedding-2`) and persist to Supabase PostgreSQL (`CourseDB.embedding`) to ensure real-time semantic discovery alignment.
