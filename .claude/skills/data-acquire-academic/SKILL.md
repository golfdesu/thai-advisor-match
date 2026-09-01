---
name: data-acquire-academic
description: Methodology for systematically scaling and enriching high-depth faculty advisor datasets across Thailand's leading research universities without bottlenecks or hallucination.
---

<!-- Reference: SKILL.state Architecture & Evaluation (arXiv:2608.26263v2) - https://arxiv.org/html/2608.26263v2#S5 -->

# Massive Academic Data Acquisition & Faculty Enrichment Methodology (SKILL.state Paradigm)

To systematically scale and enrich high-depth faculty advisor datasets across Thailand's leading research universities (CU, MU, CMU, TU, KU, KKU, KMITL, KMUTT) without bottlenecks or hallucination, follow this 5-pillar methodology powered by the `SKILL.state` architecture (`backend/scripts/agentic_pipeline/`):

- **SKILL.state Deterministic Execution:** Use `FacultyExtractionAgent` or `cli_runner.py` to maintain a flat token footprint (<2,000 tokens/turn), eliminate conversational history accumulation, and perform deterministic RapidFuzz deduplication and deep merging ([Reference: arXiv:2608.26263v2](https://arxiv.org/html/2608.26263v2#S5)).
- **Direct Directory & Research Center Reverse-Engineering:** Target institutional faculty registries and designated Centers of Excellence (e.g., SIIT, BART LAB, CERT Center, SiSCR, TropMed MVRC) rather than generic university landing pages.
- **Domain-Specific Strategic Taxonomy Clustering:** Cluster data acquisition around core international research pillars:
  1. *AI, Robotics & Cyber-Physical Systems* (Computer Vision, NLP, BCI, Medical AI).
  2. *Precision Medicine, Genomics & Cellular Therapy* (CAR-T, CRISPR, Pharmacogenomics, Hematology).
  3. *Clean Energy, Smart Grids & Advanced Materials* (Perovskite PV, Power Electronics, Biodegradable Polymers).
  4. *Law, Economics & Public Policy* (Constitutional Law, Macroeconomic DSGE, Supply Chain Resilience).
  5. *Food Science, Biotechnology & One Health* (Alternative Proteins, Zoonoses, Transdermal Nanomedicine).
- **Multi-Evidence Profile Synthesis & Checkpointing:** Maintain zero-missing-field profiles containing structured `education`, 4–7 specific `research_interests`, `taught_courses`, 3–5 high-impact `featured_publications`, and verified Google Scholar profiles. All state checkpoints auto-save to `backend/data/agent_states/`.
- **Immediate 768-dim Vector Embeddings with Key Pool Rotation:** Always compute synthesized `embedding_text` and generate real 768-dimensional vectors (`gemini-embedding-2`) immediately upon ingestion via `faculty_massive_ingestion_runner.py`.
- **Strict PDPA & Contact Channel Hygiene:** Whitelist only official institutional email domains (`@tu.ac.th`, `@mahidol.ac.th`, `@cmu.ac.th`, `@chula.ac.th`, `@ku.th`). Automatically redact phone numbers (`[REDACTED_PHONE]`).

