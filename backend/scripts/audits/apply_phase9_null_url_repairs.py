# -*- coding: utf-8 -*-
"""Phase 9: normalize null publication arrays and URL placeholders."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB


def build_embedding_text(faculty: FacultyDB) -> str:
    parts = [
        faculty.full_name_th or "",
        f"{faculty.first_name or ''} {faculty.last_name or ''}".strip(),
        faculty.academic_title_th or "",
        faculty.university_th or faculty.university or "",
        faculty.faculty_th or faculty.faculty or "",
        faculty.department_th or faculty.department or "",
    ]
    if faculty.research_interests:
        parts.append(" ".join(str(item) for item in faculty.research_interests if item))
    if faculty.featured_publications:
        titles = []
        for publication in faculty.featured_publications:
            if isinstance(publication, dict):
                title = publication.get("title")
            else:
                title = str(publication)
            if title:
                titles.append(str(title))
        parts.append(" ".join(titles))
    return " ".join(part for part in parts if part).strip()


def run_phase9_repairs() -> None:
    db = SessionLocal()
    try:
        publication_arrays_fixed = 0
        url_placeholders_fixed = 0

        faculty = db.query(FacultyDB).filter(FacultyDB.id == "mu_sci_wave14_b_0227").first()
        if faculty is None:
            raise RuntimeError("Expected faculty record not found: mu_sci_wave14_b_0227")
        if faculty.featured_publications is None:
            faculty.featured_publications = []
            faculty.embedding_text = build_embedding_text(faculty)
            publication_arrays_fixed = 1

        faculty = db.query(FacultyDB).filter(
            FacultyDB.id == "chiangmaiu_facultyofv_akatvipat_037"
        ).first()
        if faculty is None:
            raise RuntimeError(
                "Expected faculty record not found: chiangmaiu_facultyofv_akatvipat_037"
            )
        if faculty.scholar_url is not None and faculty.scholar_url.strip() in {"", "-", "—", "ไม่มี"}:
            faculty.scholar_url = None
            url_placeholders_fixed = 1

        # Normalize every whitespace-only Scholar URL, not just the known row.
        for row in db.query(FacultyDB).filter(FacultyDB.scholar_url.isnot(None)).yield_per(500):
            if not row.scholar_url.strip():
                row.scholar_url = None
                url_placeholders_fixed += 1

        db.commit()
        print("Phase 9 committed successfully:")
        print(f"  - Null publication arrays normalized: {publication_arrays_fixed}")
        print(f"  - URL placeholders normalized: {url_placeholders_fixed}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_phase9_repairs()
