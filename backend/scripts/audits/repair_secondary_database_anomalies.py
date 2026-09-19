"""Repair secondary database anomalies in local PostgreSQL.

Default mode is a read-only dry-run. ``--apply`` commits only these bounded repairs:

* Delete non-person geographic scraper artifact ('srinakha_facultyo_6dde3ed5' -> 'อ. องครักษ์ จ.นครนายก');
* Nullify cross-faculty contaminated personal email on 'khonkaenun_facultyofm_fac_012_012';
* Normalize and URL-encode unencoded spaces / trailing whitespace in profile_url and image_url;
* Normalize empty strings ("") to SQL NULL in department, department_th, and role (faculties)
  and degree_name (courses);
* Rebuild embedding_text for every updated faculty record.

This script does not alter lifetime publication metrics, OpenAlex IDs, vectors, or remote Supabase.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.orm import defer

from app.core.database import SessionLocal
from app.core.embedding_text import build_faculty_embedding_text
from app.models.db_models import CourseDB, FacultyDB, ResearchLabDB


NON_PERSON_IDS_TO_DELETE = {
    "srinakha_facultyo_6dde3ed5",  # "อ. องครักษ์ จ.นครนายก"
}

EMAIL_CORRUPT_ALLOWLIST = {
    "khonkaenun_facultyofm_fac_012_012": "kitti.th@cmu.ac.th",  # Nat Koonrangsrisomboon
}


def clean_url(url: str | None) -> str | None:
    """Normalize URLs by stripping trailing markers and URL-encoding unencoded spaces."""
    if not url:
        return None
    s = url.strip()
    # Strip (New) or (Old) revision markers
    s = re.sub(r"\s*\((?:New|Old|ใหม่|เก่า)\)\s*$", "", s, flags=re.I)
    # Strip spaces before file extension (e.g. '123    .jpg')
    s = re.sub(r"\s+(\.[a-zA-Z0-9]+(?:\?.*)?)$", r"\1", s)
    # Collapse multiple consecutive spaces to single space in paths / query params
    s = re.sub(r" {2,}", " ", s)
    # URL encode remaining ASCII spaces
    s = s.replace(" ", "%20")
    return s


def normalize_empty_string(value: str | None) -> str | None:
    """Return None if string is None or whitespace-only/empty string."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def main(*, apply: bool) -> None:
    db = SessionLocal()
    report: dict[str, object] = {
        "apply": apply,
        "deleted_faculty_ids": [],
        "cleared_contaminated_emails": [],
        "cleaned_profile_urls": [],
        "cleaned_image_urls": [],
        "normalized_empty_string_faculties": {
            "department": 0,
            "department_th": 0,
            "role": 0,
        },
        "normalized_empty_string_courses": {
            "degree_name": 0,
        },
        "embedding_texts_rebuilt": 0,
    }

    try:
        # 1. DELETE NON-PERSON SCRAPER ARTIFACTS
        for fac_id in NON_PERSON_IDS_TO_DELETE:
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f:
                # Double check no foreign keys reference this ID
                lab_ref = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == fac_id).first()
                if lab_ref:
                    print(f"SKIPPING deletion of {fac_id}: referenced by lab {lab_ref.id}")
                    continue
                report["deleted_faculty_ids"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "university_th": f.university_th,
                    "faculty_th": f.faculty_th,
                })
                if apply:
                    db.delete(f)

        # 2. CLEAR KNOWN CONTAMINATED EMAILS
        for fac_id, bad_email in EMAIL_CORRUPT_ALLOWLIST.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fac_id).first()
            if f and f.email and f.email.strip().lower() == bad_email.lower():
                report["cleared_contaminated_emails"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "old_email": f.email,
                    "new_email": None,
                })
                f.email = None
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1

        # 3. CLEAN PROFILE_URL, IMAGE_URL, AND EMPTY STRINGS ACROSS ALL FACULTIES
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(500)
        for f in faculties:
            if f.id in NON_PERSON_IDS_TO_DELETE:
                continue

            changed = False

            # URL cleaning
            if f.profile_url:
                cleaned_p = clean_url(f.profile_url)
                if cleaned_p != f.profile_url:
                    report["cleaned_profile_urls"].append({
                        "id": f.id,
                        "old": f.profile_url,
                        "new": cleaned_p,
                    })
                    f.profile_url = cleaned_p
                    changed = True

            if f.image_url:
                cleaned_i = clean_url(f.image_url)
                if cleaned_i != f.image_url:
                    report["cleaned_image_urls"].append({
                        "id": f.id,
                        "old": f.image_url,
                        "new": cleaned_i,
                    })
                    f.image_url = cleaned_i
                    changed = True

            # Empty string normalization to NULL
            if f.department == "":
                f.department = None
                report["normalized_empty_string_faculties"]["department"] += 1
                changed = True

            if f.department_th == "":
                f.department_th = None
                report["normalized_empty_string_faculties"]["department_th"] += 1
                changed = True

            if f.role == "":
                f.role = None
                report["normalized_empty_string_faculties"]["role"] += 1
                changed = True

            if changed:
                old_emb = f.embedding_text
                f.embedding_text = build_faculty_embedding_text(f)
                if old_emb != f.embedding_text:
                    report["embedding_texts_rebuilt"] = int(report["embedding_texts_rebuilt"]) + 1

        # 4. CLEAN EMPTY STRINGS ACROSS COURSES
        courses = db.query(CourseDB).options(defer(CourseDB.embedding)).yield_per(500)
        for c in courses:
            if c.degree_name == "":
                c.degree_name = None
                report["normalized_empty_string_courses"]["degree_name"] += 1

        out_filename = (
            "secondary_database_anomalies_apply.json"
            if apply
            else "secondary_database_anomalies_dryrun.json"
        )
        out_path = BACKEND_DIR / "data" / "agent_states" / out_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 70)
        print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
        print("=" * 70)
        print(f"Deleted non-person faculty records: {len(report['deleted_faculty_ids'])}")
        print(f"Cleared cross-contaminated personal emails: {len(report['cleared_contaminated_emails'])}")
        print(f"Cleaned profile URLs with spaces/markers: {len(report['cleaned_profile_urls'])}")
        print(f"Cleaned image URLs with spaces/markers: {len(report['cleaned_image_urls'])}")
        print("Normalized empty strings in FacultyDB:")
        print(f"  - department: {report['normalized_empty_string_faculties']['department']}")
        print(f"  - department_th: {report['normalized_empty_string_faculties']['department_th']}")
        print(f"  - role: {report['normalized_empty_string_faculties']['role']}")
        print(f"Normalized empty strings in CourseDB (degree_name): {report['normalized_empty_string_courses']['degree_name']}")
        print(f"Total faculty embedding texts rebuilt: {report['embedding_texts_rebuilt']}")
        print(f"Report written to: {out_path}")

        if apply:
            db.commit()
            print("Successfully committed changes to local PostgreSQL.")
        else:
            db.rollback()
            print("Dry-run complete. No changes were committed.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Commit changes to local database")
    args = parser.parse_args()
    main(apply=args.apply)
