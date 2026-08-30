---
name: build-scraper
description: Guidelines and standards for building scrapers to extract course and faculty data (Reverse-Engineering, Multi-threaded, Vector Embedding).
---

# University Data Scraper Guidelines

When the user triggers `/build-scraper [University Name]` or requests a new university scraper, strictly follow these 4 standards:

## 1. Direct Portal Reverse-Engineering
- **DO NOT** use generic HTML parsing if it can be avoided.
- Inspect the Network tab to find Internal APIs, REST APIs (e.g., WordPress `wp-json`), GraphQL, or XML Sitemaps.
- Examples:
  - Chulalongkorn (CU): Direct via WordPress REST/AJAX.
  - Mahidol (MU): Extracted via Graduate XML Sitemaps (`program-sitemap.php`).
  - Chiang Mai (CMU): Reverse-engineered via the central portal and TQF2 system.

## 2. Multi-threaded & Resilient Pipeline
- Use `ThreadPoolExecutor` from `concurrent.futures` to run requests concurrently (prevent bottlenecks).
- Implement Retry mechanisms (e.g., `tenacity`) and Fallbacks if the target API imposes Rate Limiting.
- The process must complete scraping hundreds of courses within seconds.

## 3. Immediate Enrichment + 768-dim Embeddings
- As soon as raw data is retrieved, map it to the system's standard Pydantic Schema (department, faculty, career paths, tuition).
- **Must generate Vector Embeddings** (768-dim) using the Gemini API immediately before inserting into the database.
- This ensures that data entering Supabase (pgvector) is instantly ready for Real-time Semantic Search without requiring subsequent Batch Processing.

## 4. PDPA Compliance and Data Hygiene
- **NEVER** save the personal phone numbers of faculty members.
- Contact information must be restricted to official university channels or Google Scholar.
- After completing the scraper, remind the user to run `/audit-db` or `/check-coverage` to ensure the data in the database is complete and non-redundant.

