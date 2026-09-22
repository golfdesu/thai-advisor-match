# -*- coding: utf-8 -*-
"""
Clean English header/sidebar leaks, phantom records, and mismatched emails:
1. Purge phantom records:
   - 'up_w48_0022_351' (อ. Contact Us)
   - 'tu_77228bb7_6146' (ผศ.ดร. empty name stub)
2. Clear/fix 34 records with English boilerplate leaks (spambots, textbooks copyrights, grants, redacted phone, telephone)
3. Clear English chair name leaks on KMITL Architecture records (Scott Drake, Chandra Pratama Ph)
4. Clear mismatched email hemmarat@go.buu.ac.th on buu_infor_015_9202 (ดร. คนึงนิจ กุโบลา)
5. Save reversible snapshot to backend/data/agent_states/clean_en_leaks_and_phantoms_snapshot.json
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
from app.core.embedding_text import build_faculty_embedding_text

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "clean_en_leaks_and_phantoms_snapshot.json"
)

PURGE_IDS = [
    "up_w48_0022_351",  # 'อ. Contact Us'
    "tu_77228bb7_6146", # 'ผศ.ดร. ' empty name stub
]

CLEAR_EN_IDS = [
    # 15 Burapha records with spambots notice
    "wave21_0109_306", "wave21_0111_405", "wave21_0113_998", "wave21_0115_619",
    "wave21_0116_252", "wave21_0117_888", "wave21_0118_942", "wave21_0119_805",
    "wave21_0120_433", "wave21_0121_313", "wave21_0122_918", "wave21_0124_159",
    "wave21_0112_110", "wave21_0110_213", "wave21_0123_662",
    # Thammasat records with 'Textbooks Copyrights' or 'Grants'
    "tu_4aca8d5f_1738", "tu_57924e58_9988", "tu_6d9e7108_9058", "tu_e323d8f2_9762", "tu_651a4139_1203",
    "tu_169da454_9893", "tu_1e1bf9a4_9760", "tu_37991aa4_4542", "tu_606a9742_1534", "tu_5200d1b2_4797",
    "tu_b3251a1a_8975", "tu_6a3b3f2d_7399",
    # Maejo records with 'REDACTED PHONE'
    "mju_21b4e29f_0552", "mju_3d45eb1b_4854", "mju_5b31ef04_4102", "mju_7f3a1b96_6242", "mju_24f9c3b5_9637",
    "wave21_0114_166",
    # KMITL Architecture records with chair names
    "kmitl_aad_wave16_0135", "kmitl_aad_wave16_0136", "kmitl_aad_wave16_0140", "kmitl_aad_wave16_0141"
]

def execute_clean():
    db = SessionLocal()
    try:
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "purged": [],
            "modified": []
        }

        # 1. Purge phantom records
        for fid in PURGE_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                snapshot["purged"].append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "first_name": f.first_name,
                    "last_name": f.last_name,
                    "email": f.email,
                    "university_th": f.university_th
                })
                # unlink labs
                labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == f.id).all()
                for l in labs: l.lead_advisor_id = None
                db.delete(f)
                print(f"Purged phantom record: {fid} ('{f.full_name_th}')")

        # 2. Fix srinakha_facultyo_498d1392 (Telephone Deachapunya -> Chattri Deachapunya)
        swu_fac = db.query(FacultyDB).filter(FacultyDB.id == "srinakha_facultyo_498d1392").first()
        if swu_fac:
            snapshot["modified"].append({
                "id": swu_fac.id,
                "field": "en_name",
                "old_first": swu_fac.first_name,
                "old_last": swu_fac.last_name,
                "new_first": "Chattri",
                "new_last": "Deachapunya"
            })
            swu_fac.first_name = "Chattri"
            swu_fac.last_name = "Deachapunya"
            swu_fac.embedding_text = build_faculty_embedding_text(swu_fac)
            print(f"Fixed EN name for swu_fac: {swu_fac.id} -> Chattri Deachapunya")

        # 3. Clear boilerplate EN names
        for fid in CLEAR_EN_IDS:
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                snapshot["modified"].append({
                    "id": f.id,
                    "field": "clear_en_boilerplate",
                    "old_first": f.first_name,
                    "old_last": f.last_name,
                    "new_first": None,
                    "new_last": None
                })
                f.first_name = None
                f.last_name = None
                f.embedding_text = build_faculty_embedding_text(f)

        # 4. Clear mismatched email on buu_infor_015_9202 (ดร. คนึงนิจ กุโบลา)
        buu_fac = db.query(FacultyDB).filter(FacultyDB.id == "buu_infor_015_9202").first()
        if buu_fac and buu_fac.email == "hemmarat@go.buu.ac.th":
            snapshot["modified"].append({
                "id": buu_fac.id,
                "field": "clear_mismatched_email",
                "old_email": buu_fac.email,
                "new_email": None
            })
            buu_fac.email = None
            buu_fac.embedding_text = build_faculty_embedding_text(buu_fac)
            print(f"Cleared mismatched email on buu_infor_015_9202")

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as out:
            json.dump(snapshot, out, ensure_ascii=False, indent=2)
        print(f"Saved snapshot to {SNAPSHOT_PATH}")

        db.commit()
        print(f"Successfully committed: {len(snapshot['purged'])} purged, {len(snapshot['modified'])} modified.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_clean()
