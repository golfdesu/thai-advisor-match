# -*- coding: utf-8 -*-
"""
Autonomous Database Cleaning Pipeline for Waves 53-56:
Universities: All RMUT campuses, Maejo University, NIDA, and Rajabhat Universities (22 campuses).

Operations:
1. Snapshot & Delete 14 phantom, corrupted DOI, journal editor, and 'et al.' records to
   backend/data/agent_states/clean_waves53_56_deleted.json
2. Unlink any research_labs.lead_advisor_id references if present (0 found)
3. Normalize titles, whitespace, trailing punctuation, and student IDs across 92 records
4. Commit to PostgreSQL (localhost:5432/advisor_match)
5. Re-scan cluster to verify 0 defects remain
"""
import os
import sys
import re
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from sqlalchemy import or_

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "clean_waves53_56_deleted.json"
)

DELETE_TARGET_IDS = {
    "ssru_w56_1999_818",  # Non-person corrupted DOI 'S. 10.52939/ijg.v22i6.5043'
    "snru_w56_1534_675",  # Non-person / Journal placeholder 'Editor of Visitsilp Journal'
    "nida_w55_0538_310",  # Single-initial phantom 'S.'
    "nida_w55_0872_462",  # Single-initial phantom 'N.'
    "nida_w55_1090_970",  # Single-initial phantom 'U.'
    "rmu_w56_0277_965",   # Initials-only phantom 'S P'
    "rmu_w56_0316_570",   # Initials-only phantom 'P. C.'
    "snru_w56_0652_277",  # 'Narong Kamolrat et al.'
    "pcru_w56_0222_836",  # 'Nuttarin Sirirustananun et al.'
    "rmutr_w53b_0629_979",# 'Et al. Jingjing Cheng'
    "rmuti_w53b_3166_560",# 'Et al. Yu Liu'
    "rmutr_w53b_0585_252",# 'Et al. Pei Diao'
    "rmutr_w53b_0588_842",# 'Et al. Jing Fu'
    "rmutr_w53b_0643_515",# 'Et al. Jinfang Ni'
}

def clean_record(f):
    orig_name = (f.full_name_th or "").strip()
    orig_title = (f.academic_title_th or "").strip()
    orig_fn = (f.first_name or "").strip()
    orig_ln = (f.last_name or "").strip()

    name = orig_name
    title = orig_title
    fn = orig_fn
    ln = orig_ln

    # 1. Remove parenthesized numbers (e.g. "Wei Chen (23863)")
    name = re.sub(r"\s*\(\d+\)", "", name)
    fn = re.sub(r"\s*\(\d+\)", "", fn)
    ln = re.sub(r"\s*\(\d+\)", "", ln)

    # 2. Clean trailing hyphens and trailing dots on multi-letter words
    name = re.sub(r"\s*-\s*$", "", name)
    if name.endswith(".") and not re.search(r"\b[A-Z]\.$", name):
        name = re.sub(r"\s*\.\s*$", "", name)

    # 3. Collapse multiple spaces
    name = re.sub(r"\s{2,}", " ", name).strip()
    fn = re.sub(r"\s{2,}", " ", fn).strip()
    ln = re.sub(r"\s{2,}", " ", ln).strip()

    # 4. English title dot spacing
    name = re.sub(r"\b(Dr|Mr|Mrs|Ms|Prof)\.([A-Z])", r"\1. \2", name)
    name = re.sub(r"\b(Assoc\.\s*Prof|Asst\.\s*Prof)\.([A-Z])", r"\1. \2", name)

    # 5. Dot spacing in initials/names
    name = re.sub(r"\b([A-Z]\.)([A-Z][a-z])", r"\1 \2", name)

    # 6. Thai title normalization adhering to Section 9 Invariant 1
    m_th_title = re.match(r"^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*(.*)", name)
    if m_th_title:
        detected_title = m_th_title.group(1)
        rest_name = m_th_title.group(2).strip()
        name = f"{detected_title} {rest_name}".strip()
        if not title:
            title = detected_title

    changed = False
    if name != orig_name:
        f.full_name_th = name
        changed = True
    if title != orig_title:
        f.academic_title_th = title
        changed = True
    if fn != orig_fn:
        f.first_name = fn
        changed = True
    if ln != orig_ln:
        f.last_name = ln
        changed = True

    return changed

def execute_cleaning():
    db = SessionLocal()
    try:
        cluster_filter = or_(
            FacultyDB.university_th.like("%ราชมงคล%"),
            FacultyDB.university_th.like("%แม่โจ้%"),
            FacultyDB.university_th.like("%พัฒนบริหารศาสตร์%"),
            FacultyDB.university_th.like("%ราชภัฏ%"),
        )

        initial_count = db.query(FacultyDB).filter(cluster_filter).count()
        print(f"Total faculty in cluster before cleaning: {initial_count}")

        # Step 1: Fetch and snapshot deletion candidates
        targets = db.query(FacultyDB).filter(FacultyDB.id.in_(list(DELETE_TARGET_IDS))).all()
        print(f"Target records found for deletion: {len(targets)}")

        snapshot_data = []
        for r in targets:
            snapshot_data.append({
                "id": r.id,
                "full_name_th": r.full_name_th,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "academic_title_th": r.academic_title_th,
                "university": r.university,
                "university_th": r.university_th,
                "faculty_th": r.faculty_th,
                "department_th": r.department_th,
                "email": r.email,
                "openalex_id": r.openalex_id,
                "total_citations": r.total_citations,
                "h_index": r.h_index,
                "role": r.role,
                "deleted_at": datetime.now().isoformat(),
            })

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot of {len(snapshot_data)} records to: {SNAPSHOT_PATH}")

        # Step 2: Unlink research_labs
        labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id.in_(list(DELETE_TARGET_IDS))).all()
        if labs:
            print(f"Unlinking {len(labs)} lab lead_advisor_id references")
            for l in labs:
                l.lead_advisor_id = None
        else:
            print("No research labs referencing deleted faculty (0 references).")

        # Step 3: Delete records
        db.query(FacultyDB).filter(FacultyDB.id.in_(list(DELETE_TARGET_IDS))).delete(synchronize_session=False)
        print(f"Deleted {len(targets)} records from database.")

        # Step 4: Apply normalizations
        faculties = db.query(FacultyDB).filter(cluster_filter).all()
        updated_count = 0
        for f in faculties:
            if clean_record(f):
                updated_count += 1

        print(f"Updated and normalized {updated_count} records.")

        # Step 5: Commit changes
        db.commit()
        print("Database commit successful.")

        # Step 6: Post-cleaning verification
        post_count = db.query(FacultyDB).filter(cluster_filter).count()
        print(f"\nTotal faculty in cluster after cleaning: {post_count} (Net change: -{initial_count - post_count})")

        # Defect check loop
        remaining_defects = 0
        for f in faculties:
            name = (f.full_name_th or "").strip()
            # Check for parenthesized numbers, trailing hyphens, trailing dots on multi-letter words
            if re.search(r"\(\d+\)", name) or re.search(r"\s*-\s*$", name):
                remaining_defects += 1
            if name.endswith(".") and not re.search(r"\b[A-Z]\.$", name):
                remaining_defects += 1
            if re.search(r"\s{2,}", name):
                remaining_defects += 1

        print(f"Post-cleaning defect scan: {remaining_defects} defects found in cluster.")
        if remaining_defects == 0:
            print("VERIFICATION PASSED: 0 DEFECTS REMAIN.")

        return {
            "initial_count": initial_count,
            "deleted_count": len(targets),
            "updated_count": updated_count,
            "post_count": post_count,
            "remaining_defects": remaining_defects,
            "snapshot_path": SNAPSHOT_PATH
        }

    except Exception as e:
        db.rollback()
        print(f"Error during execution: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_cleaning()
