# Task 3: Faculty Profile Enrichment

> **Priority:** ⚡ Tier 3 (Data Quality & UX Enhancement)  
> **Target:** Repair and enrich critical missing profile fields across existing baseline faculty records.

---

## 1. Problem Statement & Missing Field Statistics

Audit of the baseline `faculties` table (3,901 records):

| Missing Field | Missing Count | Percentage | System Impact |
| :--- | :---: | :---: | :--- |
| **Image URL (`image_url`)** | **2,482 records** | **63.6%** | UI displays initials fallback avatars instead of authentic photos, impacting perceived credibility. |
| **Research Interests (`research_interests`)** | **1,670 records** | **42.8%** | Limits Synergy Badge computation and reduces semantic thesis matching precision. |
| **Publications (`featured_publications`)** | **745 records** | **19.1%** | Missing recent research citations and impact metrics. |

---

## 2. Enrichment Strategies

### Strategy 1: Enrich Image URLs from Verified Institutional Hubs
- Target English names (`full_name_en`) and institutional affiliations via official university profile slugs.
- Scrape profile photos directly from faculty directories using preserved `profile_url` endpoints.
- Validate that all acquired image URLs return HTTP 200 and are not hotlink-protected or broken.

### Strategy 2: Derive Research Interests from Verified Publications
For faculty members possessing publications (`featured_publications`) but lacking structured `research_interests` (~900+ records):
- Extract specialized research keywords from verified paper titles using TF-IDF / KeyBERT or LLM summarization.
- Populate `research_interests` (JSON Array of strings).
- Synthesize updated embedding text and recalculate 768-dim Gemini embeddings to refresh `pgvector` HNSW indexes.

---

## 3. Implementation Pattern for Local Execution
Enrichment scripts execute under the local-first invariant (`localhost:5432`):
```python
# 1. Query faculties where research_interests is null or image_url is null
# 2. Enrich via official directory scrapes / OpenAlex metrics
# 3. Update local PostgreSQL in chunks of 100 with atomic commits
```
*Requirement: Must run against local Docker (`localhost:5432`) to satisfy the Zero-Egress Invariant.*
