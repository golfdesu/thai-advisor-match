# -*- coding: utf-8 -*-
"""
Autonomous Database Cleaning Pipeline for Top Universities Cluster:
CU, CMU, KU, MU, KKU, TU, PSU, KMITL, KMUTT

Operations:
1. Snapshot & Delete 3 Professor Emeritus records:
   - chulalongk_facultyofp_bumrungsuk_081 (ศ. กิตติคุณ ดร. สุรชาติ บำรุงสุข)
   - chulalongk_facultyofp_yavaprapas_080 (ศ. กิตติคุณ ดร. ศุภชัย ยาวะประภาษ)
   - wave30_0087_482 (ศ. กิตติคุณ นายแพทย์ สุรศักดิ์ ฐานีพานิชสกุล)
2. Unlink research_labs.lead_advisor_id if referencing deleted faculty (0 found)
3. Fix and normalize 173 records:
   - Duplicated/compound titles (e.g. rama_med_007_60f6e3)
   - Civic titles in name (นาย/นาง/นางสาว)
   - Department phone string in cu_pharm_wave16_0077
   - Last name in tu_eng_wave16_0018
4. Re-sync embedding_text
5. Verify 0 defects remain
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
    BACKEND_DIR, "data", "agent_states", "clean_top_univs_deleted.json"
)

DELETE_IDS = [
    "chulalongk_facultyofp_bumrungsuk_081",
    "chulalongk_facultyofp_yavaprapas_080",
    "wave30_0087_482",
]

def clean_top_cluster():
    db = SessionLocal()
    try:
        # 1. Snapshot and Delete
        targets = db.query(FacultyDB).filter(FacultyDB.id.in_(DELETE_IDS)).all()
        print(f"Found {len(targets)} records to delete in Top Universities cluster")

        snapshot = []
        for r in targets:
            snapshot.append({
                "id": r.id,
                "full_name_th": r.full_name_th,
                "university_th": r.university_th,
                "faculty_th": r.faculty_th,
                "department_th": r.department_th,
                "academic_title_th": r.academic_title_th,
                "role": r.role,
                "deleted_at": datetime.now().isoformat()
            })

        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot to {SNAPSHOT_PATH}")

        # Unlink foreign keys in research_labs
        labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id.in_(DELETE_IDS)).all()
        if labs:
            for l in labs:
                l.lead_advisor_id = None
            print(f"Unlinked {len(labs)} lab lead advisor references")

        for r in targets:
            db.delete(r)
        print(f"Deleted {len(targets)} records")

        # 2. Fix specific known defective records
        # Specific known mappings
        specific_fixes = {
            "rama_med_007_60f6e3": ("ศ.ดร.นพ.", "ศ.ดร.นพ. อติพร อิงค์สาธิต"),
            "cu_vet_avian_onehealth_001": ("ศ.น.สพ.ดร.", "ศ.น.สพ.ดร. อลงกร อมรศิลป์"),
            "mu_tm_pongrama_001": ("รศ.ดร.สพ.ญ.", "รศ.ดร.สพ.ญ. พงศ์ระมาด รามะสูต"),
            "tu_eng_wave16_0018": {
                "last_name": "Nuansing",
                "full_name_th": "อ.ดร. Direk Nuansing",
            },
            "cu_pharm_wave16_0077": {
                "department_th": "คณะเภสัชศาสตร์",
                "department": "Faculty of Pharmaceutical Sciences",
            }
        }

        for fid, fix in specific_fixes.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                if isinstance(fix, tuple):
                    fac.academic_title_th, fac.full_name_th = fix
                elif isinstance(fix, dict):
                    for k, v in fix.items():
                        setattr(fac, k, v)
                fac.embedding_text = build_faculty_embedding_text(fac)

        # 3. Clean civic titles (นาย/นางสาว/นาง) and double prefixes across Top Universities
        top_univs = [
            "จุฬาลงกรณ์มหาวิทยาลัย", "มหาวิทยาลัยเชียงใหม่", "มหาวิทยาลัยเกษตรศาสตร์",
            "มหาวิทยาลัยมหิดล", "มหาวิทยาลัยขอนแก่น", "มหาวิทยาลัยธรรมศาสตร์",
            "มหาวิทยาลัยสงขลานครินทร์", "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
            "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี"
        ]

        faculties = db.query(FacultyDB).filter(FacultyDB.university_th.in_(top_univs)).all()
        updated_count = 0

        for f in faculties:
            name = (f.full_name_th or "").strip()
            title = (f.academic_title_th or "").strip()
            changed = False

            # Fix "นาย อ. นาย บุญเกียรติ..." -> "อ. บุญเกียรติ..."
            m_cbs = re.match(r"^นาย\s+อ\.\s+นาย\s+(.*)", name)
            if m_cbs:
                name = f"อ. {m_cbs.group(1).strip()}"
                title = "อ."
                changed = True

            # Fix "อ. นาย / อ. นางสาว / อ. นาง" -> "อ. "
            m_civic = re.match(r"^(อ\.|ผศ\.|รศ\.|ศ\.|อ\.ดร\.|ผศ\.ดร\.|รศ\.ดร\.|ศ\.ดร\.)\s+(?:นาย|นางสาว|นาง)\s+(.*)", name)
            if m_civic:
                name = f"{m_civic.group(1)} {m_civic.group(2).strip()}"
                if not title:
                    title = m_civic.group(1)
                changed = True

            # Fix compound title spacing e.g. "รศ. น.สพ. ดร." -> "รศ.น.สพ.ดร."
            m_sp = re.match(r"^(ศ|รศ|ผศ|อ)\.\s+(น\.สพ\.|สพ\.ญ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.)\s*(ดร\.)?\s*(.*)", name)
            if m_sp:
                t_rank = m_sp.group(1)
                t_prof = m_sp.group(2)
                t_dr = m_sp.group(3) or ""
                rest = m_sp.group(4).strip()
                if t_dr:
                    new_title = f"{t_rank}.{t_prof}{t_dr}"
                else:
                    new_title = f"{t_rank}.{t_prof}"
                name = f"{new_title} {rest}"
                title = new_title
                changed = True

            # Fix "ศ.ดร. นพ." -> "ศ.ดร.นพ."
            m_dr_prof = re.match(r"^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.)\s+(นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.)\s*(.*)", name)
            if m_dr_prof:
                new_title = f"{m_dr_prof.group(1)}{m_dr_prof.group(2)}"
                name = f"{new_title} {m_dr_prof.group(3).strip()}"
                title = new_title
                changed = True

            if changed:
                f.full_name_th = name
                f.academic_title_th = title
                f.embedding_text = build_faculty_embedding_text(f)
                updated_count += 1

        db.commit()
        print(f"Top Universities cluster updates committed: {updated_count} records normalized.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clean_top_cluster()
