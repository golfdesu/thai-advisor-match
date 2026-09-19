# -*- coding: utf-8 -*-
"""
Apply Transactional Fixes from Fact-Check Audit of 13,559 Faculty Records.

Applies audited repairs:
1. Purge empty non-person placeholder: ku_sci_wave13_b_0072
2. Restore authentic faculty profiles at Naresuan University:
   - nu_teerapornk__3400 -> รศ.ดร. ธีรพร กงบังเกิด (Teeraporn Kongbangkerd)
   - nu_kanchaleej__0384 -> รศ.ดร. กัญชลี เจติยานนท์ (Kanchalee Jetiyanon)
   - nu_saventp__9852   -> ผศ.ดร. เสวนต์ ปัมปัสสิทธิ์ (Savent Pampasit)
3. Sanitize scraper badge artifact at Chulalongkorn:
   - cu_cbs_wave11_0172 -> ผศ.ดร. จิรพล ชิยะจันทน์ (Chiraphol Chiyachantana)
4. Merge same-university duplicate pairs:
   - Srinakharinwirot: srinakha_facultyo_730abfa1 -> srinakha_facultyo_ea3969b6
   - Khon Kaen: kku_comp_kanda_001 -> kku_eng_001
5. Disambiguate cross-university OpenAlex mover collisions by keeping OpenAlex ID
   on primary publishing institution and clearing secondary/cross-listed appointment.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB


def apply_repairs():
    db = SessionLocal()
    print("=" * 65)
    print("🚀 APPLYING AUDITED FACT-CHECK REPAIRS (13,559 FACULTIES)")
    print("=" * 65)

    try:
        # 1. Purge empty non-person placeholder
        placeholder = db.query(FacultyDB).filter(FacultyDB.id == "ku_sci_wave13_b_0072").first()
        if placeholder:
            print(f"🗑️ Purging placeholder record: {placeholder.id} ({placeholder.full_name_th})")
            # Clear any lab foreign keys just in case
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == placeholder.id).update(
                {ResearchLabDB.lead_advisor_id: None}
            )
            db.delete(placeholder)
        else:
            print("ℹ️ Placeholder ku_sci_wave13_b_0072 already purged.")

        # 2. Restore authentic faculty profiles at Naresuan University
        nu_map = {
            "nu_teerapornk__3400": {
                "full_name_th": "รศ.ดร. ธีรพร กงบังเกิด",
                "academic_title_th": "รศ.ดร.",
                "first_name": "Teeraporn",
                "last_name": "Kongbangkerd",
            },
            "nu_kanchaleej__0384": {
                "full_name_th": "รศ.ดร. กัญชลี เจติยานนท์",
                "academic_title_th": "รศ.ดร.",
                "first_name": "Kanchalee",
                "last_name": "Jetiyanon",
            },
            "nu_saventp__9852": {
                "full_name_th": "ผศ.ดร. เสวนต์ ปัมปัสสิทธิ์",
                "academic_title_th": "ผศ.ดร.",
                "first_name": "Savent",
                "last_name": "Pampasit",
                "openalex_id": "https://openalex.org/A5052926719",
            },
        }

        for fid, attrs in nu_map.items():
            fac = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if fac:
                print(f"✅ Restoring authentic profile: {fid} -> {attrs['full_name_th']} ({attrs['first_name']} {attrs['last_name']})")
                for k, v in attrs.items():
                    setattr(fac, k, v)

        # 3. Sanitize scraper badge artifact at Chulalongkorn
        cbs_fac = db.query(FacultyDB).filter(FacultyDB.id == "cu_cbs_wave11_0172").first()
        if cbs_fac:
            print(f"✅ Sanitizing badge artifact: {cbs_fac.id} -> ผศ.ดร. จิรพล ชิยะจันทน์ (Chiraphol Chiyachantana)")
            cbs_fac.full_name_th = "ผศ.ดร. จิรพล ชิยะจันทน์"
            cbs_fac.academic_title_th = "ผศ.ดร."
            cbs_fac.first_name = "Chiraphol"
            cbs_fac.last_name = "Chiyachantana"

        # 4. Merge same-university duplicate pairs
        # Srinakharinwirot pair: 730abfa1 (donor) -> ea3969b6 (canonical)
        swu_donor = db.query(FacultyDB).filter(FacultyDB.id == "srinakha_facultyo_730abfa1").first()
        swu_target = db.query(FacultyDB).filter(FacultyDB.id == "srinakha_facultyo_ea3969b6").first()
        if swu_donor and swu_target:
            print(f"🔗 Merging SWU duplicate: {swu_donor.id} into {swu_target.id}")
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == swu_donor.id).update(
                {ResearchLabDB.lead_advisor_id: swu_target.id}
            )
            db.delete(swu_donor)

        # Khon Kaen pair: kku_comp_kanda_001 (donor) -> kku_eng_001 (target)
        kku_donor = db.query(FacultyDB).filter(FacultyDB.id == "kku_comp_kanda_001").first()
        kku_target = db.query(FacultyDB).filter(FacultyDB.id == "kku_eng_001").first()
        if kku_donor and kku_target:
            print(f"🔗 Merging KKU duplicate: {kku_donor.id} into {kku_target.id}")
            kku_target.full_name_th = "รศ.ดร. กานดา รุณนะพงศา สายแก้ว"
            kku_target.first_name = "Kanda"
            kku_target.last_name = "Runapongsa Saikaew"
            kku_target.email = "kanda@kku.ac.th"
            kku_target.faculty = "College of Computing"
            # Union research interests & publications
            existing_interests = set(kku_target.research_interests or [])
            for ri in (kku_donor.research_interests or []):
                if ri not in existing_interests:
                    existing_interests.add(ri)
            kku_target.research_interests = list(existing_interests)

            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == kku_donor.id).update(
                {ResearchLabDB.lead_advisor_id: kku_target.id}
            )
            db.delete(kku_donor)

        # 5. Disambiguate cross-university OpenAlex collisions
        secondary_fids = [
            "arch-chula-012_c60c3c",
            "mu_envs_006_8baa4f",
            "mu_envs_008_7217e5",
            "chulalongk_facultyofe_chancharoenchai_022",
            "econ-cu-009_9efc88",
        ]
        for sfid in secondary_fids:
            sec_fac = db.query(FacultyDB).filter(FacultyDB.id == sfid).first()
            if sec_fac and sec_fac.openalex_id:
                print(f"🧹 Disambiguating cross-university OpenAlex ID: clearing on secondary {sfid} ({sec_fac.full_name_th})")
                sec_fac.openalex_id = None

        db.commit()
        print("\n" + "=" * 65)
        print("✅ ALL FACT-CHECK REPAIRS COMMITTED SUCCESSFULLY")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during repair execution: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_repairs()
