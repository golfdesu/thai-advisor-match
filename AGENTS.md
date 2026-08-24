# Thai Advisor Match — Project Guidelines & Architecture

## 1. Project Overview & Vision
**Thai Advisor Match** is an AI-powered thesis advisor matching platform designed for prospective graduate students (Master's and Ph.D. candidates) in Thailand. It solves the critical problem where aspiring researchers struggle to identify suitable thesis advisors and find universities actively conducting research in their fields of interest.

### Core Features:
1. **AI Semantic Search & Matching:** Students input their research topics, abstracts, or ideas. The platform semantically indexes, matches, and ranks faculty members and universities with the highest alignment, displaying a percentage match score (% Match Score).
2. **AI Match Explanation:** Automatically synthesizes concise explanations of why a specific professor is an ideal match for the student's research direction.
3. **Faculty & University Directory:** Structured browsing and filtering by university, faculty/school, department, and research domains.
4. **Advisor Profile View:** Comprehensive profile pages displaying academic background, research interests, supervised courses, publication links (Google Scholar / Scopus / institutional repositories), and official contact information.
5. **AI Cold Email Generator:** An AI assistant that drafts professional inquiry emails and research proposals for contacting prospective advisors.

---

## 2. Tech Stack & Architecture

```
[ Frontend: Next.js (App Router, Tailwind CSS, TypeScript) ]
                          ↕ (REST API)
[ Backend: Python FastAPI (Semantic Search & Scraper Engine) ]
                          ↕
[ AI Layer: Gemini Embeddings / NLP ] ↔ [ Database: PostgreSQL + pgvector / Supabase ]
```

* **Frontend:**
  * **Framework:** Next.js (React, TypeScript, App Router)
  * **Styling:** Tailwind CSS, Lucide React Icons, shadcn/ui
  * **State & Data Fetching:** React Query / SWR / Fetch API
* **Backend:**
  * **Framework:** Python (FastAPI, Uvicorn, Pydantic v2)
  * **AI & NLP:** Google Gemini API (`text-embedding-004`, `gemini-1.5-flash`), NumPy / Scikit-learn
  * **Scraping Engine:** `requests`, `beautifulsoup4`, `playwright` (for JavaScript-rendered pages)
* **Database & Vector Store:**
  * **Production:** PostgreSQL + `pgvector` (Supabase or Self-hosted)
  * **Development / Local:** SQLite / ChromaDB / Local pgvector

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
    "M.Eng. (Electrical Engineering), Chiang Mai University",
    "B.Eng. (Electrical Engineering), King Mongkut's Institute of Technology Ladkrabang"
  ],
  "research_interests": [
    "Power Electronics",
    "Microgrids and Renewable Energy",
    "Energy Storage Systems for Electric Vehicles",
    "Industrial Automation"
  ],
  "featured_publications": [],
  "scholar_url": "http://apps2.lib.cmu.ac.th/scholars/profile/35305627600",
  "embedding_text": "Asst. Prof. Dr. Watcharin Srirattanawichaikul Chiang Mai University Faculty of Engineering Department of Electrical Engineering. Expertise: Power Electronics, Microgrids, Electric Vehicles, Energy Storage Systems, Renewable Energy."
}
```

---

## 4. Project Directory Structure

```text
Teacher/
├── AGENTS.md                     # Project guidelines, architecture & roadmap (this file)
├── README.md                     # Project overview and setup instructions
├── cmu_ee_faculty.json           # Initial test dataset (CMU Electrical Engineering)
│
├── backend/
│   ├── app/
│   │   ├── api/                  # API Endpoints (v1: search, faculty, match, email)
│   │   │   ├── routes_search.py
│   │   │   ├── routes_faculty.py
│   │   │   └── routes_universities.py
│   │   ├── core/                 # Config, Database connection, AI Client
│   │   │   ├── config.py
│   │   │   └── embedding_service.py
│   │   ├── models/               # Pydantic schemas & DB models
│   │   │   └── schema.py
│   │   ├── scrapers/             # University scraper modules
│   │   │   ├── base_scraper.py
│   │   │   ├── cmu/
│   │   │   ├── cu/
│   │   │   ├── ku/
│   │   │   └── mahidol/
│   │   └── main.py               # FastAPI Entrypoint
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── app/                  # Next.js App Router Pages
    │   │   ├── page.tsx          # Homepage & AI Search Bar
    │   │   ├── search/page.tsx   # Search Results & Match Filters
    │   │   └── faculty/[id]/page.tsx # Detailed Professor Profile
    │   ├── components/           # UI Components
    │   │   ├── SearchHero.tsx
    │   │   ├── FacultyCard.tsx
    │   │   ├── MatchScoreBadge.tsx
    │   │   └── ColdEmailModal.tsx
    │   └── lib/                  # Utilities & API Client
    ├── package.json
    └── tailwind.config.js
```

---

## 5. Development Guidelines & Best Practices

1. **Scraping Ethics & PDPA Compliance:**
   * Collect only publicly disclosed academic information and official institutional contact channels (e.g., official university email addresses).
   * **Never collect or store personal phone numbers.**
   * Implement appropriate User-Agents and rate limiting to avoid overloading institutional servers.
2. **Modular Scrapers:**
   * Scrapers for each university must inherit from a common `BaseScraper` interface and output standard JSON schema objects.
3. **Semantic Matching Quality:**
   * Construct `embedding_text` by blending the professor's name, bilingual research interests, publication keywords, and lab descriptions for maximum vector similarity accuracy.
4. **Code Quality:**
   * Backend: Explicit type hints, clear separation of concern between the Service layer and API routing layer.
   * Frontend: Responsive UI, modern Tailwind aesthetics, full bilingual support (Thai & English).
