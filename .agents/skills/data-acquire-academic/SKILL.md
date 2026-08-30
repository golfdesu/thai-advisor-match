---
name: data-acquire-academic
description: Methodology for systematically scaling and enriching high-depth faculty advisor datasets across Thailand's leading research universities without bottlenecks or hallucination.
---

# Massive Academic Data Acquisition & Faculty Enrichment Methodology

To systematically scale and enrich high-depth faculty advisor datasets across Thailand's leading research universities (CU, MU, CMU, TU, KU, KKU, KMITL, KMUTT) without bottlenecks or hallucination, follow this 5-pillar methodology:

- **Direct Directory & Research Center Reverse-Engineering:** Target institutional faculty registries and designated Centers of Excellence (e.g., SIIT, BART LAB, CERT Center, SiSCR, TropMed MVRC) rather than generic university landing pages.
- **Domain-Specific Strategic Taxonomy Clustering:** Cluster data acquisition around core international research pillars:
  1. *AI, Robotics & Cyber-Physical Systems* (Computer Vision, NLP, BCI, Medical AI).
  2. *Precision Medicine, Genomics & Cellular Therapy* (CAR-T, CRISPR, Pharmacogenomics, Hematology).
  3. *Clean Energy, Smart Grids & Advanced Materials* (Perovskite PV, Power Electronics, Biodegradable Polymers).
  4. *Law, Economics & Public Policy* (Constitutional Law, Macroeconomic DSGE, Supply Chain Resilience).
  5. *Food Science, Biotechnology & One Health* (Alternative Proteins, Zoonoses, Transdermal Nanomedicine).
- **Multi-Evidence Profile Synthesis:** Maintain zero-missing-field profiles containing structured `education`, 4–7 specific `research_interests`, `taught_courses`, 3–5 high-impact `featured_publications`, and verified Google Scholar profiles.
- **Immediate 768-dim Vector Embeddings with Key Pool Rotation:** Always compute synthesized `embedding_text` and generate real 768-dimensional vectors (`gemini-embedding-2`) immediately upon ingestion. Use multi-key rotation with thread locks to eliminate HTTP 429 rate-limiting during batch operations.
- **Strict PDPA & Contact Channel Hygiene:** Whitelist only official institutional email domains (`@tu.ac.th`, `@mahidol.ac.th`, `@cmu.ac.th`, `@chula.ac.th`, `@ku.th`). Strictly enforce 0 phone numbers stored.

