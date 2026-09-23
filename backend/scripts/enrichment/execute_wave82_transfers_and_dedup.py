# -*- coding: utf-8 -*-
"""
Execute Wave 82 Transfers & Cross-University Deduplication
=========================================================
Resolves authentic university transfers and cross-university duplicates:
1. Assoc. Prof. Dr. Nattapong Puttanapong:
   - Primary: tu_econ_0017 (Thammasat University - Faculty of Economics)
   - Secondary: econ-cu-007_87289a (CU artifact) -> merge 513 citations, h_index 13, OA ID
2. Assoc. Prof. Dr. Tatre Jantarakolica:
   - Primary: tu_econ_0027 (Thammasat University - Faculty of Economics)
   - Secondary: cu_cbs_wave11_0110 (CU artifact) -> merge 139 citations, h_index 7, OA ID
3. Asst. Prof. Dr. Winai Homsombat:
   - Primary: tu_econ_0056 (Thammasat University - Faculty of Economics)
   - Secondary: kmutt_gmi__156 (KMUTT inactive record) -> merge into TU Econ
4. Dr. Vipakorn Thumwimol:
   - Primary: cu_arch_0110 (Chulalongkorn University - Faculty of Architecture)
   - Secondary: wave24_0385_353 (TU inactive record) -> merge into CU Arch
"""
from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import FacultyDB
from scripts.enrichment.resolve_wave82_duplicates import merge_faculty_pair


def execute_wave82_transfers():
    print("=================================================================", flush=True)
    print("🔄 EXECUTING WAVE 82 UNIVERSITY TRANSFERS & CROSS-UNIVERSITY DEDUP", flush=True)
    print("=================================================================", flush=True)

    db = SessionLocal()
    transfers = [
        ("tu_econ_0017", "econ-cu-007_87289a", "Assoc. Prof. Dr. Nattapong Puttanapong (CU -> TU Econ)"),
        ("tu_econ_0027", "cu_cbs_wave11_0110", "Assoc. Prof. Dr. Tatre Jantarakolica (CU -> TU Econ)"),
        ("tu_econ_0056", "kmutt_gmi__156", "Asst. Prof. Dr. Winai Homsombat (KMUTT -> TU Econ)"),
        ("cu_arch_0110", "wave24_0385_353", "Dr. Vipakorn Thumwimol (TU -> CU Arch)"),
    ]

    try:
        for prim_id, sec_id, label in transfers:
            primary = db.query(FacultyDB).filter(FacultyDB.id == prim_id).first()
            secondary = db.query(FacultyDB).filter(FacultyDB.id == sec_id).first()
            if primary and secondary:
                print(f"\n--- Realigning {label} ---")
                print(f"  Primary: [{primary.id}] {primary.university_th} - {primary.full_name_th}")
                print(f"  Secondary: [{secondary.id}] {secondary.university_th} - {secondary.full_name_th}")
                merged_sec_id = merge_faculty_pair(primary, secondary, db)
                print(f"  ✅ Successfully merged {merged_sec_id} into {primary.id} with citations={primary.total_citations}, h_index={primary.h_index}")
            else:
                print(f"  ⚠️ Skip {label}: primary or secondary not found.")

        db.commit()
    finally:
        db.close()

    print("\n🎉 Wave 82 transfers and cross-university deduplication completed!")


if __name__ == "__main__":
    execute_wave82_transfers()
