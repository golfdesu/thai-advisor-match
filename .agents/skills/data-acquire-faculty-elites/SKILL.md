---
name: data-acquire-faculty-elites
description: Methodology for discovering, verifying, and ingesting both National Elite Researchers (award winners) and university-specific faculty members, ensuring strict zero-duplication and deep canonical merging.
---

# Faculty Elite & University-Wide Acquisition Methodology

When instructed to discover, scrape, or acquire new faculty members—whether targeting National Outstanding Researchers (นักวิจัยดีเด่นแห่งชาติ) or expanding coverage for specific universities (e.g., MFU, PSU, SWU, KMITL)—you MUST strictly follow this comprehensive methodology to ensure data accuracy, academic prestige, and zero database redundancy.

## 1. Discovery & Verification Strategy

### A. National Elite & Breakthrough Researchers Discovery
When asked to "find outstanding professors" or "world-class researchers":
- **Target Recognized Awardees:** Prioritize researchers who have received the National Outstanding Researcher Award (นักวิจัยดีเด่นแห่งชาติ), Senior Research Scholar grants (เมธีวิจัยอาวุโส วช.), Outstanding Scientist of Thailand awards (นักวิทยาศาสตร์ดีเด่นแห่งชาติ), or are recognized as Highly Cited Researchers.
- **Multi-Disciplinary Coverage:** Ensure candidates span diverse fields: Engineering, Medicine, Science, Agriculture, Law, Economics, and Business Administration.
- **Accredited Universities ONLY:** Verify that the researcher is actively affiliated with an accredited Thai Higher Education Institution. DO NOT include researchers from private non-university research institutes (e.g., VISTEC, NSTDA, BIOTEC) unless they hold a joint professorship at a university.

### B. University-Wide Comprehensive Scrapes
When asked to "expand a specific university" (e.g., MFU, KU):
- **All Major Schools:** Cover all major faculties, especially specialized ones (e.g., Cosmetic Science at MFU, Forestry at KU).
- **Direct Directory Reverse-Engineering:** Extract from official faculty directories (`staff` or `personnel` pages).

## 2. Strict Pre-Flight Deduplication (Zero Redundancy Rule)

BEFORE formatting the final JSON dataset or inserting into the database, you MUST perform a database pre-check to prevent duplication.

1. **Query Existing Database:** Use Python scripts via the `Bash` or `PowerShell` tool to query `SessionLocal()`.
2. **Key Checks:**
   - Search by Thai Name (`full_name_th.like("%ชื่อ%")`)
   - Search by English Name (`first_name` and `last_name`)
   - Search by Email (`email`)
3. **If Found:** Skip adding the new profile. If the new profile has better/richer data (more publications, better interests), schedule a targeted update to the existing record instead.

## 3. Data Structure & Profile Synthesis

Every newly acquired faculty profile MUST follow this precise schema:
```json
{
    "id": "univ_faculty_name_001",
    "university": "English Name",
    "university_th": "Thai Name",
    "faculty": "Faculty in English",
    "faculty_th": "Faculty in Thai",
    "department": "Department in English",
    "department_th": "Department in Thai",
    "academic_title": "Prof. Dr.",
    "academic_title_th": "ศ.ดร.",
    "first_name": "English First",
    "last_name": "English Last",
    "full_name_th": "ศ.ดร. ชื่อ นามสกุล",
    "role": "Outstanding National Researcher / Title",
    "email": "official@univ.ac.th",
    "profile_url": "https://...",
    "education": ["Ph.D. (...)", "M.Sc. (...)", "B.Sc. (...)"],
    "research_interests": ["Domain 1", "Domain 2", "Domain 3"],
    "featured_publications": ["Title 1", "Title 2"],
    "scholar_url": "https://scholar.google.com/..."
}
```
**Hygiene Rules:**
- Clean repeated titles in Thai names (e.g., fix `"ศ.ดร. ศ.ดร."` to `"ศ.ดร. "`).
- Ensure no personal phone numbers are included.

## 4. Deep Canonical Merging Pipeline

If overlaps occur due to institutional transfers or dual affiliations (e.g., a professor listed at both SUT and TU), run the Canonical Merge pipeline:
- **Identify Keeper vs. Obsolete:** Keep the ID corresponding to their primary, current, active university affiliation.
- **Deep Merge Arrays:** Use `deduplicate_list()` to merge `research_interests`, `featured_publications`, and `education`.
- **Merge Missing Fields:** Copy `image_url`, `scholar_url`, `email` from the obsolete record if missing in the keeper.
- **Delete Obsolete:** Remove the duplicate record from `FacultyDB`.
- **Re-Vectorize:** Regenerate `embedding_text` and the 768-dim vector for the keeper.

## 5. Seamless Ingestion & Vectorization

Always use the established ingestion runner (`backend/scripts/faculty_massive_ingestion_runner.py`) which guarantees:
1. **Upsert Logic:** Inserts new and updates existing without crashing.
2. **Multi-Threaded Vectorization:** Instantly computes 768-dim `gemini-embedding-2` vectors using thread pools.
3. **Database Commit:** Saves vectors directly to Supabase `pgvector`.
