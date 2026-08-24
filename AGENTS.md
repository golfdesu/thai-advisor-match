# Thai Advisor Match - Project Guidelines & Architecture

## 1. Project Overview & Vision
**Thai Advisor Match** is an AI-powered thesis advisor matching platform designed for prospective graduate students (Master's and Ph.D. candidates) in Thailand. It solves the critical problem where aspiring researchers struggle to identify suitable thesis advisors and find universities actively conducting research in their fields of interest.

### Core Features:
1. **AI Semantic Search & Matching:** Students input their research topics, abstracts, or ideas. The platform semantically indexes, matches, and ranks faculty members and universities with the highest alignment, displaying a percentage match score (% Match Score).
2. **AI Match Explanation:** Automatically synthesizes concise explanations of why a specific professor is an ideal match for the student's research direction.
3. **Faculty & University Directory:** Structured browsing and filtering by university, faculty/school, department, and research domains.
4. **Advisor Profile View:** Comprehensive profile pages displaying academic background, research interests, supervised courses, publication links, and official contact information.
5. **AI Cold Email Generator:** An AI assistant that drafts professional inquiry emails and research proposals for contacting prospective advisors.

---

## 2. Tech Stack & Architecture

```
[ Frontend: Native HTML / Vanilla JS / Tailwind CDN (MVP Prototype) ]
                          ↕ (REST API)
[ Backend: Python FastAPI (Semantic Search & Scraper Engine) ]
                          ↕
[ AI Layer: Gemini Embeddings / NLP ] ↔ [ Database: PostgreSQL + pgvector / Supabase ]
```

* **Frontend:**
  * **Current (MVP):** Native HTML, Vanilla JavaScript, Tailwind CSS (CDN), Lucide Icons, served statically via FastAPI `FileResponse`.
  * **Future Scale:** Next.js (React, TypeScript, App Router).
* **Backend:**
  * **Framework:** Python (FastAPI, Uvicorn, Pydantic v2).
  * **AI & NLP:** Google Gemini API (`gemini-embedding-2`), Vector Cosine Similarity.
  * **Scraping Engine:** `requests`, `beautifulsoup4`, SerpApi (Google Scholar).
* **Database & Vector Store:**
  * **Production:** PostgreSQL + `pgvector` (Supabase).

---

## 3. Data Schema Standards

### Faculty Member Schema:
```json
{
  "id": "cmu_eng_ee_014",
  "university": "Chiang Mai University",
  "university_th": "มหาวิทยาลัยเชียงใหม่",
  "faculty": "Faculty of Engineering",
  "faculty_th": "คณะวิศวกรรมศาสตร์",
  "department": "Department of Electrical Engineering",
  "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
  "academic_title": "Asst. Prof. Dr.",
  "academic_title_th": "ผศ.ดร.",
  "first_name": "Watcharin",
  "last_name": "Srirattanawichaikul",
  "full_name": "Asst. Prof. Dr. Watcharin Srirattanawichaikul",
  "full_name_th": "ผศ.ดร. วัชริน ศรีรัตนาวิชัยกุล",
  "role": "Head of the Department of Electrical Engineering",
  "email": "watcharin.s@cmu.ac.th",
  "image_url": "https://ee.eng.cmu.ac.th/images/gallerys_content/b_20221129114143.png",
  "profile_url": "https://ee.eng.cmu.ac.th/web/personnel_detail.php?id=14",
  "education": [
    "D.Eng. (Electrical Engineering), Chiang Mai University",
    "M.Eng. (Electrical Engineering), Chiang Mai University"
  ],
  "research_interests": [
    "Power Electronics",
    "Microgrids and Renewable Energy"
  ],
  "featured_publications": [],
  "scholar_url": "http://apps2.lib.cmu.ac.th/scholars/profile/35305627600",
  "embedding_text": "Asst. Prof. Dr. Watcharin Srirattanawichaikul..."
}
```

---

## 4. Project Directory Structure

```text
Teacher/
├── AGENTS.md                     # Project guidelines, architecture & roadmap (this file)
├── DATA_SOURCES.md               # Documentation of data sources and scraping references
├── README.md                     # Project overview and setup instructions
├── .gitignore                    # Git ignore file (excludes .env, .venv)
│
├── backend/
│   ├── app/
│   │   ├── api/                  # API Endpoints
│   │   │   ├── routes_search.py  # PgVector search logic
│   │   │   └── routes_faculty.py
│   │   ├── core/                 # Config & AI Services
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── embedding_service.py # Gemini embedding & Query Expansion
│   │   ├── models/               # Pydantic & SQLAlchemy Models
│   │   │   ├── schema.py
│   │   │   └── db_models.py      # Contains FacultyDB with pgvector
│   │   ├── static/               # Frontend MVP UI
│   │   │   ├── index.html        # Home & Search UI
│   │   │   └── profile.html      # Individual Professor Profile
│   │   └── main.py               # FastAPI Entrypoint
│   │
│   ├── scripts/                  # Data Automation Scripts
│   │   ├── update_scholar_serpapi.py # Fetches publications from SerpApi
│   │   └── update_embeddings.py      # Generates vectors using gemini-embedding-2
│   ├── import_cs.py              # Script to seed CS faculty
│   ├── seed_extra.py             # Script to seed Medicine & Business faculty
│   ├── requirements.txt
│   └── .env                      # Contains DATABASE_URL, GEMINI_API_KEY, SERPAPI_KEY
```

---

## 5. Development Guidelines & Best Practices

1. **Scraping Ethics & PDPA Compliance:**
   * Collect only publicly disclosed academic information and official institutional contact channels (e.g., official university email addresses).
   * **Never collect or store personal phone numbers.**
2. **Semantic Matching Quality:**
   * Utilize `gemini-embedding-2` with `pgvector` for calculating Cosine Similarity.
   * Implement Query Expansion (translating Thai terms to English academic equivalents) before generating embeddings to ensure cross-language semantic accuracy.
3. **Code Quality:**
   * Backend: Explicit type hints, robust SQL queries, graceful fallback handling if AI services are temporarily unavailable.
