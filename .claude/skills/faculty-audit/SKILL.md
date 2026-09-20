---
name: faculty-audit
description: Execute the 10-dimensional zero-defect audit across faculty records in local PostgreSQL, verifying name hygiene, scraper artifacts, thesis advisor eligibility, deduplication, and vector embeddings.
---

# Faculty Data Quality & Zero-Defect Audit Skill

This skill automates the 5-Stage / 10-Dimensional Zero-Defect verification protocol for academic faculty data in the Thai EduCenter & Advisor Match project.

## Operational Invariants
1. **Local-First Zero-Egress Invariant:** Run exclusively against local containerized PostgreSQL (`localhost:5432/advisor_match`). Zero data synced to remote Supabase until 100% verified.
2. **UTF-8 Console Reconfiguration:** All Python scripts must execute with `sys.stdout.reconfigure(encoding="utf-8")` to prevent Windows `cp1252` encoding crashes.
3. **Flat Token Footprint:** Execute headless Python scripts and audit runners. Never inspect raw HTML or dump thousands of database records into conversational context.

---

## 10-Dimensional Audit Checklist

### Stage 1: Name & Nomenclature Hygiene
- **Dimension 1 (Completeness):** `first_name IS NOT NULL` and `last_name IS NOT NULL` (no blank names).
- **Dimension 2 (Latin Script Purity):** Zero Thai or Cyrillic characters in `first_name` and `last_name`. Clean zero-width spaces (`​`, `\xa0`, `﻿`).
- **Dimension 3 (No Placeholders):** Zero records with placeholder names (`REDACTED`, `Member`, `Faculty`, `Unknown`, `Staff`).
- **Dimension 4 (Title Stripping):** First names must not leak academic titles (`Prof.`, `Assoc. Prof.`, `Dr.`, `Mr.`, `Ms.`). Last names must not leak credential suffixes (`Ph.D.`, `MD`, `FACS`).
- **Dimension 5 (Bilingual Symmetry):** International/foreign faculty whose Thai name was truncated must have canonical title + name (e.g., `อ. Morten Bennedsen`).

### Stage 2: Scraper Structural Artifacts
- **Dimension 6 (Header Overwrite Purge):** Flag and clean identical high-frequency name clusters caused by breadcrumbs or table header leaks (e.g., `Endocrine Metabolism`).
- **Dimension 7 (Delimiter Safety):** Ensure Thai title prefixes use explicit period/whitespace delimiters (`ดร\.`, `ดร\s+`) so names like `นพคุณ`, `ดรุณี` are not mutilated.

### Stage 3: Thesis Advisor Eligibility
- **Dimension 8 (MHESI Regulatory Eligibility):** Active thesis advisors only. Flag, unlink (`research_labs.lead_advisor_id`), and purge ineligible categories under MHESI rules:
  - Retired faculty (`อาจารย์เกษียณอายุ`)
  - Former faculty (`อดีตคณาจารย์`)
  - Professor Emeritus without active teaching duties (`ศ.เกียรติคุณ`)
  - Personnel on multi-year study leave (`ลาศึกษาต่อ`)
  - Deceased scholars

### Stage 4 & 5: Deduplication, Metrics & Vectors
- **Dimension 9 (Three-Pass Deduplication):**
  - Pass 1: Normalized Thai name matching (`full_name_th`).
  - Pass 2: Clean English name matching (`first_name` + `last_name`).
  - Pass 3: Verified personal non-shared academic email matching.
  - *Metric Preservation:* Retain `max(total_citations)`, `max(h_index)`, union list supersets, and repoint foreign keys.
- **Dimension 10 (Vector Embedding Integrity):** 100% vector coverage with 768-dim Gemini embeddings (`build_faculty_embedding_text`).

---

## Execution Commands

Run the comprehensive database audit suite:
```bash
python backend/scripts/audits/verify_zero_defect_baseline.py
```

Run targeted former/retired faculty audit:
```bash
python backend/scripts/enrichment/audit_former_faculty.py
```

Inspect Top 5 universities zero-defect status:
```bash
python -c "
from backend.app.core.database import SessionLocal
from backend.app.models.db_models import FacultyDB
from sqlalchemy import func

db = SessionLocal()
univs = db.query(FacultyDB.university_th, func.count(FacultyDB.id)).group_by(FacultyDB.university_th).all()
for u, count in univs:
    print(f'{u}: {count} faculty')
db.close()
"
```
