"""
Reconcile Research Labs and Academic Faculty Linkages
Maps lead_advisor_id and member_faculty_ids for all 104 research labs in PostgreSQL
to valid, verified FacultyDB records.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models.db_models import ResearchLabDB, FacultyDB

# Explicit verified mapping for labs that had legacy IDs or None
LAB_LEAD_MAPPINGS = {
    # Legacy ID reconciliation
    "ku_cassava_biorefinery_center": "ku_agro_klanarong_001",
    "cmu_agro_food_innovation_center": "cmu_agro_yuthana_001",
    "cmu_atmospheric_pm25_center": "cmu-sci-021_f78748",
    "cu_med_genomics_virology_hub": "cu_med_virology_001",
    "kmutnb_tggs_german_power_lab": "kmutnb_tggs_staff_041",
    "ku_smart_agriculture_precision_center": "ku_agri_001",
    "mfu_cosmetic_science_natural_lab": "mfu_cosmetic_mayuree_001",
    "mfu_fungal_research_center": "mfu_w52_0828_968",
    "mu_siriraj_stem_cell_center": "mu_siriraj_stemcell_001",
    "mu_tropmed_malaria_infectious_hub": "mu_tropmed_malaria_001",
    "sut_quantum_high_energy_physics_center": "sut_sci_chinorat_001",

    # Regional Research Labs Phase 2 mapping
    "tsu_songkhla_lake_basin_center": "tsu_sci_nukul_001",
    "wu_wood_biomaterials_center": "walailak_schoolof_a8d33d0a",
    "up_herbal_cosmeceuticals_center": "regionalun_facultymem_sunanta_058",
    "wu_vector_borne_disease_center": "wu_med_chitwadee_001",
    "up_ict_geoinformatics_disaster_lab": "up_ict_naronk_001",
    "up_smart_agriculture_food_center": "regionalun_facultymem_nuengmek_056",
    "mju_organic_agriculture_biotech_center": "mju_agri_weerapon_001",
    "msu_biodiversity_natural_products_lab": "regionalun_facultymem_pramual_036",
    "msu_paleontology_research_center": "msu_sci_prayook_001",
    "mju_postharvest_smart_automation_lab": "mju_renew_natthawud_001",
    "buu_eec_green_hydrogen_energy_lab": "buu_eng_wanchai_001",
    "su_advanced_ceramics_materials_lab": "su_pharm_praneet_001",
    "su_digital_heritage_archaeology_lab": "su_archaeo_001",
    "mfu_tea_coffee_innovation_center": "mfu_agro_chanida_001",
    "mfu_pm25_air_quality_center": "mfu_health_sompoch_001",
    "ubu_mekong_water_agro_hydrology_lab": "ubu_eng_chatchai_001",
    "ubu_biomass_renewable_energy_lab": "ubu_sci_chatchawan_001",
    "tsu_southern_halal_food_lab": "tsu_tech_anchalee_001",
    "kmutt_fibo_industrial_robotics_lab": "kmutt_fibo_supachai_001",
    "kmutt_sit_ai_bigdata_innovation_center": "kmutt_sit_001",
    "sut_synchrotron_materials_center": "sut_phys_synch_002",
    "nu_medical_biotech_genomics": "wave22_0287_902",
    "nu_solar_energy_research_center": "nu_sgtech_001",
    "cmu_biomedical_engineering_center": "cmu_eng_ee_008",
    "kku_battery_energy_storage_center": "kku_sci_vittaya_001",
    "psu_marine_natural_products_center": "princeofso_facultyofs_sukpondma_014",
    "wu_coastal_aquaculture_biotech_center": "walailak_schoolof_3bc6d546",
    "mfu_medicinal_cosmeceuticals_lab": "mfu_cosmetic_natthida_001",
    "ku_src_maritime_logistics_lab": "ku_maritime_sornnarin_001",
}


def reconcile_labs():
    db = SessionLocal()
    try:
        labs = db.query(ResearchLabDB).all()
        print(f"Scanning {len(labs)} research labs for advisor linkage...")

        updated_count = 0
        all_faculty_ids = {f.id for f in db.query(FacultyDB.id).all()}
        print(f"Loaded {len(all_faculty_ids)} valid faculty IDs from database.")

        for lab in labs:
            changed = False
            current_lead = lab.lead_advisor_id

            # Check if lead advisor needs update
            if lab.id in LAB_LEAD_MAPPINGS:
                target_lead = LAB_LEAD_MAPPINGS[lab.id]
                if target_lead in all_faculty_ids and target_lead != current_lead:
                    lab.lead_advisor_id = target_lead
                    changed = True
            elif current_lead not in all_faculty_ids:
                print(f"WARNING: Unmapped missing lead advisor for lab {lab.id}: {current_lead}")

            # Reconcile member_faculty_ids: keep only valid faculty IDs, and ensure lead is included
            clean_members = []
            if lab.member_faculty_ids:
                for fid in lab.member_faculty_ids:
                    if fid in all_faculty_ids and fid not in clean_members:
                        clean_members.append(fid)

            # Ensure lead advisor is in member list
            if lab.lead_advisor_id and lab.lead_advisor_id in all_faculty_ids:
                if lab.lead_advisor_id not in clean_members:
                    clean_members.insert(0, lab.lead_advisor_id)

            if clean_members != lab.member_faculty_ids:
                lab.member_faculty_ids = clean_members
                changed = True

            if changed:
                updated_count += 1

        db.commit()
        print(f"Successfully reconciled {updated_count} research labs.")

        # Post-verification audit
        verified_leads = 0
        total_linked_members = 0
        for lab in db.query(ResearchLabDB).all():
            if lab.lead_advisor_id in all_faculty_ids:
                verified_leads += 1
            total_linked_members += len(lab.member_faculty_ids or [])

        print(f"Verification Results:")
        print(f"  - Total Labs: {len(labs)}")
        print(f"  - Verified Lead Advisors: {verified_leads} / {len(labs)} ({(verified_leads/len(labs))*100:.1f}%)")
        print(f"  - Total Member Faculty Links: {total_linked_members}")

    finally:
        db.close()


if __name__ == "__main__":
    reconcile_labs()
