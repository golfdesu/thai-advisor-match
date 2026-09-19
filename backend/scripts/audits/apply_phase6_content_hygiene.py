# -*- coding: utf-8 -*-
"""
Phase 6: Microscopic Content Hygiene & Final Deep Polish
Cleanses research_interests array tokens across all 13,483 faculty records:
1. Strips pure numbers, table indices, and lone punctuation tokens.
2. Expands unparsed pipe ('|') and slash (' / ') delimited string lists into atomic interest items.
3. Cleans leading conjunctions ('and ', 'or ') and bullet characters ('•', '-', '*', numbering).
4. Trims trailing periods, semicolons, and commas (preserving academic abbreviations like sp., spp., etc.).
5. Resolves crawler stuttering text (ku_wave18_agrips_0129: 'egg hatching...', 'nematode management...').
6. Purges synthetic crawler notes, LLM commentary, and provenance traces (e.g. 'Verified via...', 'Identity confirmed...').
7. Strips narrative prefixes ('His research centers on...', 'Her listed area of expertise is...') leaving pure thematic tags.
8. Ensures profiles whose commentary was purged receive clean canonical departmental tags.
9. Recalculates embedding_text to preserve Text-Vector Symmetry.
"""
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB


def build_standard_embedding_text(f: FacultyDB) -> str:
    parts = [
        f.full_name_th or "",
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.academic_title_th or "",
        f.university_th or f.university or "",
        f.faculty_th or f.faculty or "",
        f.department_th or f.department or "",
    ]
    if f.research_interests:
        parts.append(" ".join(f.research_interests))
    if f.featured_publications:
        pub_titles = [
            p.get("title", "") if isinstance(p, dict) else str(p)
            for p in f.featured_publications
        ]
        parts.append(" ".join([t for t in pub_titles if t]))
    return " ".join([p for p in parts if p]).strip()


PROVENANCE_DROP_PHRASES = [
    "verified via",
    "identity confirmed",
    "this summary is",
    "no areas of expertise",
    "no specific publications",
    "stated area of expertise",
    "only just joined",
    "per his own",
    "per her own",
    "linkedin profile",
    "researchgate profile",
    "faculty page",
    "source page",
    "faculty-members listing",
    "google scholar",
    "could be independently",
    "not listed here because",
    "is a faculty member",
    "eng.buu.ac.th",
    "email)",
    "email for him",
    "email for her",
    "burapha university",
    "department of engineering",
    "no further specifics",
    "specific publications are not",
    "holding a ph.d",
    "he holds a ph.d",
    "she holds a ph.d",
]

NARRATIVE_PREFIX_PATTERNS = [
    r"^(his|her)\s+listed\s+area\s+of\s+expertise\s+is\s+",
    r"^(his|her)\s+research\s+centers\s+on\s+",
    r"^(his|her)\s+research\s+is\s+in\s+",
    r"^(his|her)\s+research\s+spans\s+",
    r"^(his|her)\s+research\s+interests?\s+(include|span)\s+",
    r"^(his|her)\s+work\s+(focuses\s+on|spans)\s+",
    r"^(his|her)\s+documented\s+research\s+centers\s+on\s+",
    r"^(his|her)\s+focus\s+is\s+on\s+",
]


def clean_single_interest(raw: str) -> list[str]:
    """Clean and optionally split a raw interest string into 1 or more cleaned items."""
    s = raw.strip()
    if not s:
        return []

    # Handle known crawler stuttering cases
    if "egg hatching" in s and "paralysis" in s:
        return ["egg hatching and paralysis"]
    if "managementnematode" in s or ("nematode management" in s and len(s) > 50):
        return ["nematode management"]

    low = s.lower()

    # Drop provenance / commentary / crawler meta tokens
    if any(phrase in low for phrase in PROVENANCE_DROP_PHRASES):
        return []

    # Strip narrative bio sentences
    if len(s) > 100 and (
        s.startswith(("He joined the division", "This summary is derived", "He received his", "She received her"))
        or "following doctoral research at INSA" in s
    ):
        return []

    # Check for pipe-separated or slash-separated lists
    tokens = []
    if "|" in s:
        tokens = [t.strip() for t in s.split("|") if t.strip()]
    elif " / " in s:
        tokens = [t.strip() for t in s.split(" / ") if t.strip()]
    else:
        tokens = [s]

    cleaned_tokens = []
    for tok in tokens:
        t = tok.strip()

        # Check provenance phrases again after splitting
        if any(phrase in t.lower() for phrase in PROVENANCE_DROP_PHRASES):
            continue

        # Strip narrative prefixes
        for pat in NARRATIVE_PREFIX_PATTERNS:
            t = re.sub(pat, "", t, flags=re.IGNORECASE).strip()

        # Clean trailing sentence breaks
        t = re.split(r"\.\s+(?:As|He|She|This|These|That|The)\s+", t)[0].strip()

        # Drop pure digit tokens (table indices, bullet numbers, years as solo tags)
        if re.match(r"^\d+$", t):
            continue
        # Drop single character non-alphanumeric tokens
        if len(t) <= 1 and not t.isalnum():
            continue

        # Strip leading bullet chars or numbering: '• ', '- ', '* ', '1. ', '2) '
        t = re.sub(r"^[\s\•\-\*\–\—]+", "", t).strip()
        t = re.sub(r"^\d+[\.\)]\s*", "", t).strip()

        # Strip leading conjunctions ('and ', 'or ')
        t = re.sub(r"^(and\s+|or\s+)", "", t, flags=re.IGNORECASE).strip()

        # Strip trailing punctuation (.,;:|/-) preserving valid abbreviations
        if re.search(r"[\.,;:\-\|/]$", t):
            if not re.search(r"\b(etc|al|sp|spp|dr|mr|mrs|prof)\.$", t, flags=re.IGNORECASE):
                t = re.sub(r"[\.,;:\-\|/\s]+$", "", t).strip()

        # Validate remaining content
        if t and len(t) > 1 and not re.match(r"^\d+$", t) and not any(p in t.lower() for p in PROVENANCE_DROP_PHRASES):
            cleaned_tokens.append(t)

    return cleaned_tokens


def get_canonical_department_interests(f: FacultyDB) -> list[str]:
    """Provide canonical fallback interests when all scraped tags were commentary."""
    dept = f.department_th or f.department or ""
    fac = f.faculty_th or f.faculty or ""

    if "เครื่องกล" in dept or "Mechanical" in dept:
        return ["วิศวกรรมเครื่องกล", "Mechanical Engineering"]
    elif "เคมี" in dept or "Chemical" in dept:
        return ["วิศวกรรมเคมี", "Chemical Engineering"]
    elif "โยธา" in dept or "Civil" in dept:
        return ["วิศวกรรมโยธา", "Civil Engineering"]
    elif "ไฟฟ้า" in dept or "Electrical" in dept:
        return ["วิศวกรรมไฟฟ้า", "Electrical Engineering"]
    elif "อุตสาหการ" in dept or "Industrial" in dept:
        return ["วิศวกรรมอุตสาหการ", "Industrial Engineering"]
    elif "คอมพิวเตอร์" in dept or "Computer" in dept:
        return ["วิศวกรรมคอมพิวเตอร์", "Computer Engineering"]
    elif "วิศวกรรม" in fac or "Engineering" in fac:
        return ["วิศวกรรมศาสตร์", "Engineering"]
    else:
        return [dept] if dept else ["วิชาการและการวิจัย"]


def run_phase6_hygiene():
    db = SessionLocal()
    try:
        print("=== Starting Phase 6: Microscopic Content Hygiene & Final Polish ===")
        faculties = db.query(FacultyDB).all()
        print(f"Total faculty records loaded: {len(faculties)}")

        modified_count = 0
        total_tokens_removed = 0
        total_tokens_expanded = 0
        fallback_applied_count = 0

        for f in faculties:
            if not f.research_interests:
                continue

            orig_interests = list(f.research_interests)
            new_interests = []

            for item in orig_interests:
                cleaned_items = clean_single_interest(str(item))
                for c in cleaned_items:
                    # Deduplicate case-insensitively while preserving first seen form
                    if not any(c.lower() == existing.lower() for existing in new_interests):
                        new_interests.append(c)

            # If all tokens were pruned because they were pure commentary/provenance
            if not new_interests:
                new_interests = get_canonical_department_interests(f)
                fallback_applied_count += 1

            if orig_interests != new_interests:
                f.research_interests = new_interests
                f.embedding_text = build_standard_embedding_text(f)
                modified_count += 1
                if len(new_interests) > len(orig_interests):
                    total_tokens_expanded += (len(new_interests) - len(orig_interests))
                elif len(new_interests) < len(orig_interests):
                    total_tokens_removed += (len(orig_interests) - len(new_interests))

        db.commit()
        print("Phase 6 execution successful:")
        print(f"  - Total faculty profiles sanitized: {modified_count}")
        print(f"  - Fallback departmental interests assigned: {fallback_applied_count}")
        print(f"  - Net token expansion from delimited strings: {total_tokens_expanded}")
        print(f"  - Net noisy/number/bio/commentary tokens purged: {total_tokens_removed}")

    except Exception as e:
        db.rollback()
        print(f"ERROR during Phase 6 hygiene: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_phase6_hygiene()
