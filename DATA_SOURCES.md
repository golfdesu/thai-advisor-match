# Thai Advisor Match - Data Sources & Scraping References

This document records the data sources for the faculty members across various departments and universities. This data serves as the initial seed database for the AI Semantic Search system in the Thai Advisor Match project.

## 1. Basic Faculty Information (Profile & Research Interests)

### 1.1 Chiang Mai University (CMU)
*   **Faculty of Engineering - Department of Electrical Engineering (EE)**
    *   **Primary Source:** [CMU EE Official Website](https://ee.eng.cmu.ac.th/web/personnel.php)
    *   **Data Type:** Faculty names, academic titles, emails, and specialized research areas (imported via `cmu_ee_faculty.json`).
*   **Faculty of Science - Department of Computer Science (CS)**
    *   **Primary Source:** [CMU CS Official Website](https://www.cs.science.cmu.ac.th/personnel/)
    *   **Data Type:** Professors specializing in Machine Learning, NLP, Software Engineering, and Network Security (imported via `seed_cs.py`).
*   **CMU Business School (Faculty of Business Administration)**
    *   **Primary Source:** [CMU Business School Website](https://www.ba.cmu.ac.th/)
    *   **Data Type:** Professors specializing in Finance, Marketing, and Management (imported via `seed_extra.py`).

### 1.2 Mahidol University (MU)
*   **Faculty of Medicine Siriraj Hospital**
    *   **Primary Source:** [Siriraj Hospital Departments](https://www.si.mahidol.ac.th/th/department/)
    *   **Data Type:** Medical professors in Surgery and Pediatrics (imported via `seed_extra.py`).

---

## 2. Academic Publications (Featured Publications)
To ensure accuracy and recency, research papers and publication records were not manually hardcoded. Instead, they were dynamically fetched from global academic databases.

*   **Primary Source:** Google Scholar (via SerpApi)
*   **Mechanism:** 
    *   The script `update_scholar_serpapi.py` searches for each professor's name on Google Scholar.
    *   If a strict author search (`author:"First Last"`) yields no results, the system falls back to a general query matching the professor's exact name.
    *   The top 5 most relevant publications are extracted, along with full-text URLs, and securely embedded into the PostgreSQL (Supabase) database.

---

## 3. Profile Pictures
Profile pictures were sourced from multiple platforms due to strict Hotlink Protection (CORS) policies enforced by certain university servers.

*   **Primary Source:** Official university directories.
*   **Fallback Sources (Bypassing firewalls):** 
    *   ResearchGate (e.g., Assoc. Prof. Dr. Jakramate)
    *   LinkedIn (e.g., Assoc. Prof. Dr. Rattasit)
    *   Other non-restricted official domains.
*   **Automated UI Fallback:** If an image link is broken or unavailable, the frontend automatically generates a clean avatar containing the professor's initials using the `ui-avatars.com` API.

---

## 4. Future Data Pipeline
Once the backend API is fully deployed to production hosting, scaling the database to include other universities (e.g., Chulalongkorn, Thammasat, KMITL) will follow this pipeline:
1. Developing specialized Web Scrapers (using BeautifulSoup / Playwright) tailored to the DOM structure of target university directories.
2. Importing scraped data using the standardized JSON schema defined in `AGENTS.md`.
3. Running the automated scripts to fetch Google Scholar publications and generating 768-dimensional AI Embeddings (`gemini-embedding-2`) for semantic search readiness.
