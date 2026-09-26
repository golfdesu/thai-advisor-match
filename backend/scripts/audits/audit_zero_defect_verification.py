# -*- coding: utf-8 -*-
"""
Zero-Defect Verification Audit
Runs against the local containerized PostgreSQL database (advisor_match).
"""
import sys
from pathlib import Path

parents = Path(__file__).resolve().parents
BACKEND_DIR = parents[2] if len(parents) > 2 else parents[0]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from sqlalchemy import text

def run_audit():
    db = SessionLocal()
    try:
        total_faculties = db.execute(text("SELECT count(*) FROM faculties")).scalar()
        total_labs = db.execute(text("SELECT count(*) FROM research_labs")).scalar()
        total_courses = db.execute(text("SELECT count(*) FROM courses")).scalar()

        null_embs = db.execute(text("SELECT count(*) FROM faculties WHERE embedding IS NULL")).scalar()

        invalid_labs = db.execute(text("""
            SELECT count(*)
            FROM research_labs r
            LEFT JOIN faculties f ON r.lead_advisor_id = f.id
            WHERE f.id IS NULL
        """)).scalar()

        dup_emails = db.execute(text("""
            SELECT count(*)
            FROM (
                SELECT email
                FROM faculties
                WHERE email IS NOT NULL AND email != ''
                GROUP BY email
                HAVING count(*) > 1
            ) sub
        """)).scalar()

        suffix_leaks = db.execute(text("""
            SELECT count(*)
            FROM faculties
            WHERE last_name ~* '(\\yPh\\.?D\\y|\\yM\\.?D\\b|\\yD\\.?B\\.?A\\b|DPHIL\\b|,\\s*(Ph|MD|Dr|DPHIL))'
        """)).scalar()

        thai_in_en = db.execute(text("""
            SELECT count(*)
            FROM faculties
            WHERE first_name ~ '[ก-๙]' OR last_name ~ '[ก-๙]'
        """)).scalar()

        null_ln = db.execute(text("""
            SELECT count(*)
            FROM faculties
            WHERE last_name IS NULL OR last_name = ''
        """)).scalar()

        print("==================================================")
        print("       ZERO-DEFECT DATABASE AUDIT REPORT          ")
        print("==================================================")
        print(f"Total Active Faculty Records : {total_faculties}")
        print(f"Total Research Labs          : {total_labs}")
        print(f"Total Courses                : {total_courses}")
        print("--------------------------------------------------")
        print(f"1. Missing Embeddings        : {null_embs} (0 expected) -> {'PASS' if null_embs == 0 else 'FAIL'}")
        print(f"2. Orphaned Lab Lead Advisors: {invalid_labs} (0 expected) -> {'PASS' if invalid_labs == 0 else 'FAIL'}")
        print(f"3. Duplicate Email Clusters  : {dup_emails} (0 expected) -> {'PASS' if dup_emails == 0 else 'FAIL'}")
        print(f"4. Credential Suffix Leaks   : {suffix_leaks} (0 expected) -> {'PASS' if suffix_leaks == 0 else 'FAIL'}")
        print(f"5. Thai Characters in EN     : {thai_in_en} (0 expected) -> {'PASS' if thai_in_en == 0 else 'FAIL'}")
        print(f"6. Missing Surnames          : {null_ln} (0 expected) -> {'PASS' if null_ln == 0 else 'FAIL'}")
        print("==================================================")

        all_passed = all(x == 0 for x in [null_embs, invalid_labs, dup_emails, suffix_leaks, thai_in_en, null_ln])
        if all_passed:
            print("STATUS: ALL 6 AUDIT CRITERIA PASSED WITH ZERO DEFECTS.")
        else:
            print("STATUS: DEFECTS DETECTED.")
            sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_audit()
