# -*- coding: utf-8 -*-
"""
Purge Former, Retired, Emeritus, Deceased, and On-Leave Faculty from PostgreSQL.
Saves a complete snapshot to backend/data/agent_states/skill_state_purged_former_faculty.json
before deletion to ensure reversibility.
"""
import json
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB

SNAPSHOT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "skill_state_purged_former_faculty.json")

def main():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).all()
        print(f"Total faculty before purge: {len(faculties)}")

        targets = []
        for r in faculties:
            th = r.full_name_th or ""
            title = r.academic_title_th or ""
            fn = (r.first_name or "").lower()
            ln = (r.last_name or "").lower()
            role = (r.role or "").lower()

            reasons = []
            if any(k in th for k in ["ศ.เกียรติคุณ", "ศ. เกียรติคุณ", "ศาสตราจารย์เกียรติคุณ", "ศ.คลินิกเกียรติคุณ"]):
                reasons.append("Emeritus")
            elif title in ["ศ.เกียรติคุณ", "ศาสตราจารย์เกียรติคุณ", "ศ.คลินิกเกียรติคุณ"]:
                reasons.append("Emeritus")
            elif "professor emeritus" in ln or "professor emeritus" in fn or "emeritus professor" in role:
                reasons.append("Emeritus")

            if any(k in role for k in ["อาจารย์เกษียณอายุ", "อดีตคณาจารย์"]) or any(k in th for k in ["อาจารย์เกษียณอายุ", "อดีตคณาจารย์"]):
                reasons.append("Retired/Former")

            if "ลาศึกษาต่อ" in role or "ลาศึกษาต่อ" in th or "ลาศึกษาต่อ" in (r.department_th or ""):
                reasons.append("StudyLeave")

            if "อารี วัลยะเสวี" in th:
                reasons.append("Deceased")

            if reasons:
                targets.append((r, reasons))

        print(f"Total targets identified: {len(targets)}")

        target_ids = [r.id for r, _ in targets]

        # 1. Create Snapshot for reversibility
        snapshot_records = []
        for r, reasons in targets:
            snapshot_records.append({
                "id": r.id,
                "full_name_th": r.full_name_th,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "academic_title_th": r.academic_title_th,
                "university_th": r.university_th,
                "faculty_th": r.faculty_th,
                "department_th": r.department_th,
                "email": r.email,
                "role": r.role,
                "reasons": reasons,
                "purged_at": datetime.now().isoformat()
            })

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot_records, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved checkpoint snapshot of {len(snapshot_records)} records to {SNAPSHOT_PATH}")

        # 2. Relational Integrity: clear lead_advisor_id in research_labs referencing deleted faculty
        labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id.in_(target_ids)).all()
        if labs:
            print(f"Unlinking {len(labs)} research lab lead_advisor_id references:")
            for lab in labs:
                print(f"  - Lab {lab.id} ({lab.name_th}) unlinking advisor {lab.lead_advisor_id}")
                lab.lead_advisor_id = None

        # 3. Delete records
        for r, reasons in targets:
            print(f"Deleting [{r.id}] {r.university_th} | {r.full_name_th} | {r.role} | {reasons}")
            db.delete(r)

        db.commit()
        print("Database commit successful.")

        # 4. Verify post-deletion state
        remaining_count = db.query(FacultyDB).count()
        print(f"Total faculty after purge: {remaining_count}")
        print(f"Net deleted: {len(faculties) - remaining_count}")

    except Exception as e:
        db.rollback()
        print(f"Error during purge: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
