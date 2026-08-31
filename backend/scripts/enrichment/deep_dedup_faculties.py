import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('backend/.env')
sys.path.append('backend')

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from collections import defaultdict
from sqlalchemy.orm import defer

def deduplicate_list(items):
    if not items:
        return []
    seen = set()
    res = []
    for x in items:
        if isinstance(x, dict):
            key = json.dumps(x, sort_keys=True, ensure_ascii=False)
        else:
            key = str(x).strip()
        if key not in seen and key:
            seen.add(key)
            res.append(x)
    return res

def deep_merge_and_deduplicate():
    print("=== 🧹 AUDITING AND DEEP MERGING FACULTY RECORDS ===")
    db = SessionLocal()

    # Load all faculty records
    faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
    print(f"Total faculty records loaded: {len(faculties)}")

    # 1. Group by email (if valid institutional email)
    email_groups = defaultdict(list)
    name_groups = defaultdict(list)

    for f in faculties:
        if f.email and "@" in f.email:
            email_groups[f.email.strip().lower()].append(f)

        # Also group by (university_th, normalized thai name) or (university, first_name, last_name)
        if f.university_th and f.full_name_th:
            clean_th_name = f.full_name_th.replace("ศ.ดร.", "").replace("รศ.ดร.", "").replace("ผศ.ดร.", "").replace("ดร.", "").replace("ศ.", "").replace("รศ.", "").replace("ผศ.", "").replace("อาจารย์", "").strip()
            if clean_th_name:
                name_groups[(f.university_th.strip(), clean_th_name)].append(f)
        elif f.university and f.first_name and f.last_name:
            name_groups[(f.university.strip().lower(), f.first_name.strip().lower(), f.last_name.strip().lower())].append(f)

    # Process duplicate groups
    merged_count = 0
    deleted_ids = set()

    all_duplicate_groups = []
    for email, group in email_groups.items():
        if len(group) > 1:
            all_duplicate_groups.append(group)

    for key, group in name_groups.items():
        if len(group) > 1:
            all_duplicate_groups.append(group)

    for group in all_duplicate_groups:
        # Filter out already deleted
        active_group = [f for f in group if f.id not in deleted_ids]
        if len(active_group) <= 1:
            continue

        # Select master record (prefer one with longest research interests or more complete info)
        primary = max(active_group, key=lambda f: len(f.research_interests or []) + len(f.featured_publications or []) + (10 if f.image_url else 0))
        others = [f for f in active_group if f.id != primary.id]

        for duplicate in others:
            # Merge fields into primary
            if not primary.image_url and duplicate.image_url:
                primary.image_url = duplicate.image_url
            if not primary.profile_url and duplicate.profile_url:
                primary.profile_url = duplicate.profile_url
            if not primary.scholar_url and duplicate.scholar_url:
                primary.scholar_url = duplicate.scholar_url
            if not primary.role and duplicate.role:
                primary.role = duplicate.role
            if not primary.department_th and duplicate.department_th:
                primary.department_th = duplicate.department_th
            if not primary.email and duplicate.email:
                primary.email = duplicate.email

            primary.research_interests = deduplicate_list((primary.research_interests or []) + (duplicate.research_interests or []))
            primary.featured_publications = deduplicate_list((primary.featured_publications or []) + (duplicate.featured_publications or []))
            primary.education = deduplicate_list((primary.education or []) + (duplicate.education or []))
            primary.taught_courses = deduplicate_list((primary.taught_courses or []) + (duplicate.taught_courses or []))

            db.delete(duplicate)
            deleted_ids.add(duplicate.id)
            merged_count += 1

    db.commit()
    print(f"✅ Deep merge complete! Merged and deleted {merged_count} duplicate records.")

    # Re-verify remaining count
    remaining = db.query(FacultyDB).count()
    print(f"📊 Final Unique Faculty Count: {remaining}")
    db.close()

if __name__ == "__main__":
    deep_merge_and_deduplicate()
