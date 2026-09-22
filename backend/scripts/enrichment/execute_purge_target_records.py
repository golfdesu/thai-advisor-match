# -*- coding: utf-8 -*-
"""
Autonomous Purge Script:
1. 8 Emeritus and Study-Leave records
2. 2 Email-as-name erroneous records
3. 905 Wave 53 original uncorrected foreign institution records

Saves backup snapshot to backend/data/agent_states/purge_former_and_erroneous_faculty_checkpoint.json
before deletion to guarantee complete reversibility.
"""
import os
import sys
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from sqlalchemy import text

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "purge_former_and_erroneous_faculty_checkpoint.json"
)

def execute_purge():
    db = SessionLocal()
    try:
        initial_count = db.query(FacultyDB).count()
        print(f"Total faculty before purge: {initial_count}")

        # 1. Target Group A: Emeritus & Study Leave (8 records)
        target_a_ids = [
            "chula-arts-016_6c3067",   # ศ.ดร. อัมรา ประสิทธิ์รัฐสินธุ์ (Professor Emeritus)
            "wu_w51_0550_325",         # ศ. (เกียรติคุณ) ดร.ธวัชชัย ศุภดิษฐ์
            "mfu_w52_0004_622",        # คลินิกเกียรติคุณ ทพญ.ดร.วรุณี เกิดวงศ์บัณฑิต
            "mfu_w52_0112_865",        # จารุกิตติ์ ไชยวรรณ์ (ลาศึกษาต่อ)
            "mfu_w52_0147_122",        # ดลพร สุวรรณเทพ (ลาศึกษาต่อ)
            "mfu_w52_0153_580",        # กุสุมา ทุ่งพรวน (ลาศึกษาต่อ)
            "mfu_w52_0170_294",        # ชินพงศ์ กันนา (ลาศึกษาต่อ)
            "up_w48_0014_539",         # อ. นางสาวอดิศยา เจริญผล (ลาศึกษาต่อ)
        ]

        # 2. Target Group B: Email-as-name (2 records)
        target_b_ids = [
            "rmutt_w53_0001_303",      # sciteched@rmutt.ac.th
            "nu_w45_0171_779",         # อ. e-mail : jintanapo@nu.ac.th
        ]

        # 3. Target Group C: Wave 53 original wrong foreign institution IDs (905 records)
        w53_wrong_ids = [
            r[0] for r in db.execute(
                text("SELECT id FROM faculties WHERE id LIKE '%\\_w53\\_%' ESCAPE '\\'")
            ).fetchall()
            if r[0] not in target_b_ids  # avoid duplicate
        ]

        all_target_ids = list(dict.fromkeys(target_a_ids + target_b_ids + w53_wrong_ids))
        print(f"Total unique target IDs to purge: {len(all_target_ids)}")

        # Fetch records for snapshot
        targets = db.query(FacultyDB).filter(FacultyDB.id.in_(all_target_ids)).all()
        print(f"Total target records found in DB: {len(targets)}")

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
                "purged_at": datetime.now().isoformat(),
            })

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot checkpoint ({len(snapshot_data)} records) -> {SNAPSHOT_PATH}")

        # Check and unlink foreign keys in research_labs
        labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id.in_(all_target_ids)).all()
        if labs:
            print(f"Unlinking {len(labs)} research lab lead_advisor_id references:")
            for lab in labs:
                print(f"  - Lab {lab.id} ({lab.name_th}) unlinking advisor {lab.lead_advisor_id}")
                lab.lead_advisor_id = None

        # Delete records in batches
        batch_size = 500
        for i in range(0, len(all_target_ids), batch_size):
            batch = all_target_ids[i:i + batch_size]
            db.query(FacultyDB).filter(FacultyDB.id.in_(batch)).delete(synchronize_session=False)

        db.commit()
        print("Database commit successful.")

        # Verify post-deletion state
        remaining_count = db.query(FacultyDB).count()
        print(f"Total faculty after purge: {remaining_count}")
        print(f"Net deleted: {initial_count - remaining_count}")

    except Exception as e:
        db.rollback()
        print(f"Error during purge: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_purge()
