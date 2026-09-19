"""Repair verified structured-field duplication and hidden control characters.

Default mode is a read-only dry-run. ``--apply`` commits only these bounded
repairs to local PostgreSQL:

* remove exact Chula Psychology JavaScript-state artifacts from education;
* deduplicate repeated education values in the 24 inspected records;
* remove zero-width/format and non-printing control characters from faculty
  education, research interests, and publication objects;
* rebuild embedding_text for every changed faculty record.

This script does not alter lifetime publication metrics, publication titles,
OpenAlex identity fields, vectors, or Supabase.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import FacultyDB


# These are the 9 non-Chula education records identified in the approved
# duplicate report. Chula records are scoped separately by their inspected host.
EDUCATION_ALLOWLIST = {
    "cmu_eng_department_korapin_32",
    "cmu_eng_department_salinee_23",
    "cmu_eng_department_tanyanuparb_16",
    "cmu_eng_department_warisa_9",
    "cmu_eng_department_wichai_1",
    "ku_wave18_agrips_0001",
    "ku_wave18_engsrc_0038",
    "ku_wave18_lams_0038",
    # The two inspected records whose source host is not in the Chula URL set.
    "chulalongk_facultyofc_kruahiran_003",
    "chulalongk_facultyofc_phisitsankhatka_001",
}
CHULA_EDUCATION_HOST = "psy.chula.ac.th"
# The approved Chula finding set is exactly these 15 wave-19 records plus the
# two already-inspected Chula directory records above.
CHULA_EDUCATION_ALLOWLIST = {
    "cu_wave19_psy_0001", "cu_wave19_psy_0002", "cu_wave19_psy_0003",
    "cu_wave19_psy_0004", "cu_wave19_psy_0005", "cu_wave19_psy_0006",
    "cu_wave19_psy_0007", "cu_wave19_psy_0008", "cu_wave19_psy_0009",
    "cu_wave19_psy_0010", "cu_wave19_psy_0011", "cu_wave19_psy_0012",
    "cu_wave19_psy_0013", "cu_wave19_psy_0014", "cu_wave19_psy_0015",
    "cu_wave19_psy_0016", "cu_wave19_psy_0017", "cu_wave19_psy_0018",
    "cu_wave19_psy_0019", "cu_wave19_psy_0020", "cu_wave19_psy_0021",
    "cu_wave19_psy_0022", "cu_wave19_psy_0023", "cu_wave19_psy_0024",
    "cu_wave19_psy_0025", "cu_wave19_psy_0026", "cu_wave19_psy_0027",
    "chulalongk_facultyofc_phisitsankhatka_001",
    "chulalongk_facultyofc_pornprasertmani_002",
    "chulalongk_facultyofc_kruahiran_003",
    "chulalongk_facultyofc_tepphan_004",
    "chulalongk_facultyofc_chawowanich_005",
    "chulalongk_facultyofc_jantawarint_006",
    "chulalongk_facultyofc_nimmapirat_007",
}

# This exact value is serialized JavaScript component state, not an education.
CHULA_EDUCATION_ARTIFACT_PREFIX = (
    "edDegree: null,selectedMajor: null,modalOpen: false,"
    " modalContent: null, modalTitle: null, modalHeader: null, isS"
)

# Only code points confirmed by the read-only inspection are eligible for
# mutation. Tabs/newlines are converted to spaces only in the allowlisted
# contaminated structured fields.
FORMAT_CHARS = {"​", "‌", "‍", "⁠", "﻿"}
CONFIRMED_CONTROL_CODEPOINTS = {1, 2, 9, 10, 19}
CONTROL_RE = re.compile("[" + "".join(chr(code) for code in CONFIRMED_CONTROL_CODEPOINTS) + "]")
WHITESPACE_RE = re.compile(r"\s+")

PUBLICATION_ALLOWLIST = {
    "cmu_d5ea9798_3957",
    "cmu_a50f4528_3763",
    "cmu-eng-009_045df0",
}
INTEREST_ALLOWLIST = {
    "kasetsartu_facultyofv_amnartanan_001",
    "ku_wave17_vettech_0002",
    "cmu_eng_department__63",
    "ku_agro_wave15_0018",
}
EDUCATION_CONTROL_ALLOWLIST = {"ku_forest_wave15_0001", "kku_sci_wave14_b_0049"}
REPORT_ONLY_IDS = PUBLICATION_ALLOWLIST | INTEREST_ALLOWLIST | EDUCATION_CONTROL_ALLOWLIST


def sanitize_text(value: str) -> str:
    """Remove non-content format/control chars while preserving readable text."""
    value = "".join(char for char in value if char not in FORMAT_CHARS)
    value = CONTROL_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", value).strip()


def normalize_key(value: object) -> str:
    return WHITESPACE_RE.sub(" ", str(value or "")).strip().casefold()


def clean_scalar_list(
    values: object,
    *,
    deduplicate: bool = False,
    remove_chula_artifact: bool = False,
    sanitize: bool = False,
) -> tuple[list[object], bool, list[str]]:
    if not isinstance(values, list):
        return [], False, []

    cleaned: list[object] = []
    removed: list[str] = []
    changed = False
    seen: set[str] = set()

    for item in values:
        if not isinstance(item, str):
            cleaned.append(item)
            continue

        original = item
        value = sanitize_text(item) if sanitize else item
        if value != original:
            changed = True

        if remove_chula_artifact and value.startswith(CHULA_EDUCATION_ARTIFACT_PREFIX):
            removed.append(original)
            changed = True
            continue

        key = normalize_key(value)
        if deduplicate and key and key in seen:
            removed.append(original)
            changed = True
            continue
        if deduplicate and key:
            seen.add(key)
        cleaned.append(value)

    return cleaned, changed, removed


def education_scope(faculty: FacultyDB) -> tuple[bool, bool, bool]:
    """Return (deduplicate, remove artifact, sanitize controls) for education."""
    profile_url = (faculty.profile_url or "").lower()
    deduplicate = faculty.id in EDUCATION_ALLOWLIST or faculty.id in CHULA_EDUCATION_ALLOWLIST
    remove_artifact = faculty.id in CHULA_EDUCATION_ALLOWLIST
    sanitize = faculty.id in EDUCATION_CONTROL_ALLOWLIST
    return deduplicate, remove_artifact, sanitize


def interest_scope(faculty: FacultyDB) -> bool:
    return faculty.id in INTEREST_ALLOWLIST


def publication_scope(faculty: FacultyDB) -> bool:
    return faculty.id in PUBLICATION_ALLOWLIST


def record_has_confirmed_codepoint(faculty: FacultyDB) -> bool:
    payload = json.dumps(
        {
            "education": faculty.education,
            "research_interests": faculty.research_interests,
            "featured_publications": faculty.featured_publications,
        },
        ensure_ascii=False,
    )
    return any(char in payload for char in FORMAT_CHARS) or any(
        ord(char) in CONFIRMED_CONTROL_CODEPOINTS for char in payload
    )


def format_codepoints(value: object) -> list[str]:
    text = json.dumps(value, ensure_ascii=False)
    return sorted({f"U+{ord(char):04X}" for char in text if char in FORMAT_CHARS or ord(char) in CONFIRMED_CONTROL_CODEPOINTS})


def clean_publication_item(item: object) -> tuple[object, bool]:
    if not isinstance(item, dict):
        if isinstance(item, str):
            cleaned = sanitize_text(item)
            return cleaned, cleaned != item
        return item, False

    cleaned = dict(item)
    changed = False
    for key, value in item.items():
        if isinstance(value, str):
            new_value = sanitize_text(value)
            if new_value != value:
                cleaned[key] = new_value
                changed = True
    return cleaned, changed


def clean_publications(values: object) -> tuple[list[object], bool]:
    if not isinstance(values, list):
        return [], False
    cleaned: list[object] = []
    changed = False
    for item in values:
        new_item, item_changed = clean_publication_item(item)
        cleaned.append(new_item)
        changed = changed or item_changed
    return cleaned, changed


def main(*, apply: bool) -> None:
    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "changed_records": [],
        "education_duplicate_records": 0,
        "education_artifact_removals": 0,
        "control_character_records": 0,
        "publication_control_records": 0,
        "embedding_text_rebuilt": 0,
    }
    try:
        rows = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)
        for faculty in rows:
            old_education = faculty.education if isinstance(faculty.education, list) else []
            old_interests = faculty.research_interests if isinstance(faculty.research_interests, list) else []
            old_publications = faculty.featured_publications if isinstance(faculty.featured_publications, list) else []

            deduplicate, remove_artifact, sanitize_education = education_scope(faculty)
            new_education, education_changed, education_removed = clean_scalar_list(
                old_education,
                deduplicate=deduplicate,
                remove_chula_artifact=remove_artifact,
                sanitize=sanitize_education,
            )
            new_interests, interests_changed, _ = clean_scalar_list(
                old_interests,
                sanitize=interest_scope(faculty),
            )
            if publication_scope(faculty):
                new_publications, publications_changed = clean_publications(old_publications)
            else:
                new_publications, publications_changed = old_publications, False

            # Never touch a record merely because it appears in a broad scan;
            # require a confirmed allowlisted code point or duplicate scope.
            if faculty.id not in REPORT_ONLY_IDS and not (deduplicate or remove_artifact):
                education_changed = False
                interests_changed = False
                publications_changed = False
                new_education = old_education
                new_interests = old_interests
                new_publications = old_publications

            if faculty.id in REPORT_ONLY_IDS and not record_has_confirmed_codepoint(faculty):
                if faculty.id not in EDUCATION_ALLOWLIST and not remove_artifact:
                    education_changed = False
                if faculty.id not in INTEREST_ALLOWLIST:
                    interests_changed = False
                if faculty.id not in PUBLICATION_ALLOWLIST:
                    publications_changed = False

            # A publication allowlist entry is only mutated when sanitization
            # actually removes one of the confirmed characters.
            if publication_scope(faculty) and not any(
                codepoint in format_codepoints(old_publications)
                for codepoint in ["U+200B", "U+0001", "U+0002", "U+0009", "U+000A", "U+0013"]
            ):
                publications_changed = False
                new_publications = old_publications

            # Education duplicate cleanup is restricted to the exact inspected
            # records and the Chula host; no global duplicate pass is allowed.
            if not deduplicate and not remove_artifact and faculty.id not in EDUCATION_CONTROL_ALLOWLIST:
                education_changed = False
                new_education = old_education

            # The Chula artifact must be present before removal is proposed.
            if remove_artifact and not any(
                isinstance(item, str) and item.startswith(CHULA_EDUCATION_ARTIFACT_PREFIX)
                for item in old_education
            ):
                education_changed = False
                new_education = old_education

            # Avoid counting a scoped field when its transformed value is equal.
            education_changed = education_changed and new_education != old_education
            interests_changed = interests_changed and new_interests != old_interests
            publications_changed = publications_changed and new_publications != old_publications

            if education_changed:
                if len(new_education) < len(old_education):
                    report["education_duplicate_records"] = int(report["education_duplicate_records"]) + 1
                artifact_count = sum(
                    1 for value in education_removed
                    if str(value).startswith(CHULA_EDUCATION_ARTIFACT_PREFIX)
                )
                report["education_artifact_removals"] = int(report["education_artifact_removals"]) + artifact_count
                faculty.education = new_education

            if interests_changed:
                report["control_character_records"] = int(report["control_character_records"]) + 1
                faculty.research_interests = new_interests

            if publications_changed:
                report["publication_control_records"] = int(report["publication_control_records"]) + 1
                faculty.featured_publications = new_publications

            changed = education_changed or interests_changed or publications_changed
            if not changed:
                continue

            old_embedding = faculty.embedding_text
            new_embedding = build_faculty_embedding_text(faculty)
            faculty.embedding_text = new_embedding
            report["embedding_text_rebuilt"] = int(report["embedding_text_rebuilt"]) + 1
            record = {
                "id": faculty.id,
                "full_name_th": faculty.full_name_th,
                "profile_url": faculty.profile_url,
                "education_old": old_education,
                "education_new": new_education,
                "research_interests_old": old_interests,
                "research_interests_new": new_interests,
                "featured_publications_old": old_publications,
                "featured_publications_new": new_publications,
                "embedding_changed": old_embedding != new_embedding,
                "codepoints_before": {
                    "education": format_codepoints(old_education),
                    "research_interests": format_codepoints(old_interests),
                    "featured_publications": format_codepoints(old_publications),
                },
                "codepoints_after": {
                    "education": format_codepoints(new_education),
                    "research_interests": format_codepoints(new_interests),
                    "featured_publications": format_codepoints(new_publications),
                },
            }
            records = report["changed_records"]
            assert isinstance(records, list)
            records.append(record)

        out_path = BACKEND_DIR / "data" / "agent_states" / "structured_content_hygiene_dryrun.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print(f"Changed records: {len(report['changed_records'])}")
        print(f"Education duplicate/artifact records: {report['education_duplicate_records']}")
        print(f"Exact education artifact removals: {report['education_artifact_removals']}")
        print(f"Research-interest control records: {report['control_character_records']}")
        print(f"Publication control records: {report['publication_control_records']}")
        print(f"Embedding texts rebuilt: {report['embedding_text_rebuilt']}")
        print(f"Report: {out_path}")

        if apply:
            db.commit()
            print("Committed local PostgreSQL changes.")
        else:
            db.rollback()
            print("No changes committed.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    main(apply=args.apply)
