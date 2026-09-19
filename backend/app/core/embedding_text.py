"""Canonical faculty embedding-text construction.

All faculty enrichment and embedding runners should use this builder so stored
text and newly generated vectors share one field order and null-safe JSON
serialization contract.
"""
from __future__ import annotations


def _items(values: object, *, title_key: str | None = None) -> list[str]:
    result: list[str] = []
    if not isinstance(values, list):
        return result
    for item in values:
        value = item.get(title_key) if title_key and isinstance(item, dict) else item
        if value is None:
            continue
        text = str(value).strip()
        if text:
            result.append(text)
    return result


def build_faculty_embedding_text(faculty: object, *, research_interests: list[str] | None = None) -> str:
    """Build the canonical, deterministic text representation for one faculty."""
    interests = research_interests if research_interests is not None else _items(
        getattr(faculty, "research_interests", None)
    )
    publications = _items(
        getattr(faculty, "featured_publications", None), title_key="title"
    )
    education = _items(getattr(faculty, "education", None))

    name_parts = " ".join(
        part
        for part in (
            getattr(faculty, "first_name", None),
            getattr(faculty, "last_name", None),
        )
        if part
    ).strip()
    parts = [
        getattr(faculty, "full_name_th", None),
        name_parts,
        getattr(faculty, "academic_title_th", None),
        getattr(faculty, "university_th", None) or getattr(faculty, "university", None),
        getattr(faculty, "faculty_th", None) or getattr(faculty, "faculty", None),
        getattr(faculty, "department_th", None) or getattr(faculty, "department", None),
        getattr(faculty, "role", None),
        " ".join(interests),
        " ".join(publications),
        " ".join(education),
    ]
    return " ".join(str(part).strip() for part in parts if part and str(part).strip())[:6000]
