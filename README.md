# Thai Advisor Match (ระบบค้นหาอาจารย์ที่ปรึกษาวิทยานิพนธ์ด้วย AI)

**Thai Advisor Match** is an AI-powered thesis advisor discovery platform built for prospective Master's and Ph.D. students in Thailand.

---

##  Key Features

1. **AI Semantic Advisor Matching:** Input thesis ideas/topics (in Thai or English) and get ranked professors and universities with a % match score.
2. **AI Match Explanations:** Automated summaries justifying why each advisor aligns with your research goals.
3. **Faculty & University Explorer:** Search and filter by university, faculty, and department.
4. **Comprehensive Advisor Profiles:** Academic background, research fields, publications, and official contact channels.
5. **AI Cold Email Generator:** Generate professional research inquiry emails in Thai and English with 1 click.

---

## ️ Tech Stack

* **Backend:** Python (FastAPI, Pydantic, Requests/BeautifulSoup)
* **Frontend:** Next.js (App Router, Tailwind CSS, TypeScript, Lucide Icons)
* **AI & NLP:** Google Gemini Embeddings (`text-embedding-004`), Hybrid Vector/Lexical Matcher
* **Database:** PostgreSQL (`pgvector`) / SQLite

---

##  Getting Started

### 1. Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m app.main
```

The API will be available at `http://localhost:8000` with Swagger documentation at `http://localhost:8000/docs`.

### 2. Testing the Matching Engine

Run the test suite:
```bash
cd backend
python -m tests.test_search
```

---

##  Project Architecture

See [`AGENTS.md`](./AGENTS.md) for full architectural guidelines, data schemas, and scraping standards.

---

## 🚀 Deployment (Render.com)

The project includes a `render.yaml` configuration file for zero-config deployment.

1. Create a [Render](https://render.com/) account.
2. Go to your Dashboard and click **New+** -> **Blueprint**.
3. Connect your GitHub repository containing this code.
4. Render will automatically detect the `render.yaml` file.
5. Provide the required Environment Variables in the Render Dashboard when prompted:
   - `DATABASE_URL`: Your Supabase connection string (PostgreSQL).
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `SERPAPI_KEY`: Your SerpApi API Key (for Google Scholar).
6. Click **Apply** to deploy the FastAPI backend.
