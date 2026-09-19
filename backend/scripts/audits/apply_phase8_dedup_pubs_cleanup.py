# -*- coding: utf-8 -*-
"""
Phase 8: Publication Shape Normalization and English/Thai Name Hygiene.

This phase deliberately avoids destructive deduplication when an identifier is
not person-specific: ``not_indexed`` and departmental inboxes are placeholders,
not evidence that two faculty records are the same person. Valid OpenAlex ID
collisions are handled only when they are present in the backend database.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB


# These are scraper contamination cases confirmed in the backend database.
MIXED_LANGUAGE_NAME_FIXES = {
    "ku_eng_cpe_009": {"first_name": "Yod", "last_name": "Thipsuwan"},
    "tu_law_070": {"first_name": "Supreeya", "last_name": "Kaewla-iat"},
    "chulalongk_facultyofs_torg_057": {"first_name": "Panthana", "last_name": "Torg"},
    "thammasatu_facultyofn_raethong_216": {"first_name": "Parinya", "last_name": "Raethong"},
    "chulalongk_facultyofl_niyom_030": {"first_name": "Patch", "last_name": "Niyomsilp"},
}


def build_standard_embedding_text(faculty: FacultyDB) -> str:
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


def normalize_publication(item: object) -> dict | None:
    """Convert legacy string citations to the API's Publication shape."""
    if isinstance(item, str):
        title = item.strip()
        if not title:
            return None
        return {
            "title": title,
            "year": None,
            "venue": None,
            "url": None,
            "citation_count": 0,
        }
    if not isinstance(item, dict):
        return None

    title = item.get("title") or item.get("name")
    if not title:
        return None

    year = item.get("year")
    if not isinstance(year, int):
        year = None
    citation_count = item.get("citation_count", item.get("citations", 0))
    if not isinstance(citation_count, int):
        citation_count = 0

    return {
        "title": str(title).strip(),
        "year": year,
        "venue": item.get("venue") or item.get("journal"),
        "url": item.get("url"),
        "citation_count": citation_count,
    }


def valid_openalex_id(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip().lower() not in {"not_indexed", "none", "null", "unknown"})


def merge_lists(primary: list, donor: list) -> list:
    result = []
    seen = set()
    for item in [*(primary or []), *(donor or [])]:
        key = repr(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def rebuild_embedding_text(faculty: FacultyDB) -> None:
    faculty.embedding_text = build_standard_embedding_text(faculty)


def merge_openalex_collisions(db) -> tuple[int, int]:
    """Merge only real OpenAlex collisions; placeholder values are excluded."""
    from sqlalchemy import func

    collisions = (
        db.query(FacultyDB.openalex_id)
        .filter(FacultyDB.openalex_id.isnot(None))
        .filter(FacultyDB.openalex_id != "")
        .filter(func.lower(FacultyDB.openalex_id).notin_(["not_indexed", "none", "null", "unknown"]))
        .group_by(FacultyDB.openalex_id)
        .having(func.count(FacultyDB.id) > 1)
        .all()
    )
    merged = 0
    cleared = 0
    for (openalex_id,) in collisions:
        records = db.query(FacultyDB).filter(FacultyDB.openalex_id == openalex_id).all()
        # A collision requires human/entity-resolution review. Keep the
        # authoritative ID on the strongest record and clear it on others;
        # do not delete rows or silently merge institutions.
        records.sort(key=lambda row: (
            1 if row.full_name_th and row.full_name_th.strip() else 0,
            1 if row.email and "@" in row.email else 0,
            row.total_citations or 0,
            row.h_index or 0,
            len(row.research_interests or []),
        ), reverse=True)
        for duplicate in records[1:]:
            duplicate.openalex_id = "not_indexed"
            cleared += 1
        merged += 1
    return merged, cleared


def run_phase8_repairs() -> None:
    db = SessionLocal()
    try:
        publication_records = 0
        publication_items = 0
        name_records = 0
        openalex_groups = 0
        openalex_cleared = 0

        print("=== Phase 8: Publication Shape + Name Hygiene ===")

        # Normalize every publication array, including mixed string/object arrays.
        for faculty in db.query(FacultyDB).yield_per(500):
            original = faculty.featured_publications
            if not isinstance(original, list):
                continue
            normalized = []
            for item in original:
                clean = normalize_publication(item)
                if clean is not None:
                    normalized.append(clean)
            if normalized != original:
                faculty.featured_publications = normalized
                rebuild_embedding_text(faculty)
                publication_records += 1
                publication_items += sum(isinstance(item, str) for item in original)

        # Fix only the five confirmed mixed-language English name fields.
        for faculty_id, replacement in MIXED_LANGUAGE_NAME_FIXES.items():
            faculty = db.query(FacultyDB).filter(FacultyDB.id == faculty_id).first()
            if faculty is None:
                raise RuntimeError(f"Expected faculty record not found: {faculty_id}")
            faculty.first_name = replacement["first_name"]
            faculty.last_name = replacement["last_name"]
            rebuild_embedding_text(faculty)
            name_records += 1

        # The backend DB currently has no valid OpenAlex collisions. Keep this
        # check executable for future runs without treating placeholders as IDs.
        openalex_groups, openalex_cleared = merge_openalex_collisions(db)

        db.commit()
        print("Phase 8 committed successfully:")
        print(f"  - Faculty publication arrays normalized: {publication_records}")
        print(f"  - Legacy string publication items converted: {publication_items}")
        print(f"  - Mixed-language English name records fixed: {name_records}")
        print(f"  - Valid OpenAlex collision groups handled: {openalex_groups}")
        print(f"  - Non-primary OpenAlex IDs cleared: {openalex_cleared}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_phase8_repairs()
