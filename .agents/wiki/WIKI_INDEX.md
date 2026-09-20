# WikiSkill Knowledge Index
<!-- Reference: WikiSkill - Compiling Agent Experience into Persistent Knowledge (arXiv:2608.27454v1) -->

Master index of compiled agent experience, verified university directory patterns, and scraping/cleaning strategies across Thai Higher Education.

---

## 🏛️ Universities Directory Knowledge (`wiki/universities/`)
- [Chiang Mai University (CMU)](universities/chiang_mai_university.md) — Public Health, Education, Law, Political Science, and Engineering endpoints.
- [Chulalongkorn University (CU)](universities/chulalongkorn_university.md) — Faculty of Arts, Communication Arts, Veterinary Science, and Asian Studies directory structures.
- [Khon Kaen University (KKU)](universities/khon_kaen_university.md) — Architecture, Law, Computing, Nursing, and Science endpoints.
- [Mahidol University (MU)](universities/mahidol_university.md) — Physical Therapy, Music, and Nutrition directory structures.
- [Prince of Songkla University (PSU)](universities/prince_of_songkla_university.md) — Science, Computing, and Management Sciences endpoints.
- [Thammasat University (TU)](universities/thammasat_university.md) — Law, Pharmacy, and Engineering directory structures.
- [Leading Thai Universities Directory](universities/leading_thai_universities.md) — Comprehensive verified endpoint roster across all major Thai institutions.

---

## 🧩 Extraction & Cleaning Patterns (`wiki/patterns/`)
- [Faculty Data Quality Audit & Discovery Runbook](patterns/faculty_data_recovery_patterns.md) — 5-stage quality audit framework, defect remediation, and 5-step unlisted faculty discovery workflow.
- [Thai Academic Title Edge Cases](patterns/thai_title_rules.md) — Normalization rules for complex/double titles (`ศ.(พิเศษ)`, `รศ.ดร.`, `พญ.ดร.`).
- [SPA & Dynamic Page Scraping](patterns/spa_scraping.md) — Client-side rendered university directory bypass strategies.
- [Anti-Bot & Rate-Limit Policies](patterns/rate_limiting.md) — Request intervals and retry mechanisms.

---

## 🛠️ Layer 3: Active Domain Skills (`skills/`)
- [SKILL.state Autonomous Pipeline (`skill-state`)](../skills/skill-state/SKILL.md) — Mandatory headless web scraping & faculty data acquisition engine enforcing zero in-chat token bloat (<2,000 tokens/turn), Trafilatura pruning, and RapidFuzz deduplication.
- [Faculty Data Quality & Zero-Defect Audit (`faculty-audit`)](../skills/faculty-audit/SKILL.md) — 10-dimensional zero-defect audit automating name hygiene, scraper artifact detection, MHESI thesis advisor eligibility, deduplication, and vector embeddings.
- [Stage 6 Unlisted Faculty Discovery (`faculty-discover`)](../skills/faculty-discover/SKILL.md) — Harvests recent 2024–2026 OpenAlex publication footprints, resolves authentic Thai nomenclature, evaluates confidence, and quarantines ambiguous records (< 0.85).
- [Database Tuning & pgvector Optimization (`db-optimize`)](../skills/db-optimize/SKILL.md) — HNSW vector cosine distance indexing, GIN trigram text indexing, heavy column deferral (`defer(Model.embedding)`), and SQLAlchemy connection pool tuning.
- [Faculty Elites & University-Wide Acquisition (`data-acquire-faculty-elites`)](../skills/data-acquire-faculty-elites/SKILL.md) — Autonomous SKILL.state pipeline for national outstanding scholars and university faculty directories.
- [Academic Curriculum & Discovery (`data-acquire-academic`)](../skills/data-acquire-academic/SKILL.md) — Academic program, course metadata, and curriculum extraction workflows.

## 📜 Evolution Log (`wiki/evolution_log.md`)
- [Evolution History](evolution_log.md) — Audit trail of compiled traces and proposed/accepted skill patches.

## 🔎 Data Provenance
- [Faculty Data Provenance — Waves 1–3](data_provenance.md) — Exact source URLs, discovery methods (SERPAPI/DNS probe/CDP capture/WP REST), extraction pipeline, data-quality fixes, and confirmed dead ends for the 855-record sparse-faculty acquisition (2026-09-10).
