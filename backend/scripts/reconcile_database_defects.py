# -*- coding: utf-8 -*-
"""
Database Defect Reconciliation Script
Grounded Execution - Zero Fabrication Policy

Resolves:
1. Credential suffix leaks in last_name (5 records)
2. Orphaned research lab lead advisors (3 labs)
3. Duplicate email clusters:
   - Merges 41 true same-person duplicate pairs (metric preservation + archiving)
   - Sanitizes 22 scraper-leaked / generic email clusters
4. Applies verified Romanized names from thai_romanization_cache.json
"""
import sys
import os
import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ScholarUnassignedDB, ResearchLabDB, CourseDB

CACHE_PATH = BACKEND_DIR / "data" / "agent_states" / "thai_romanization_cache.json"

def clean_credential_suffixes(db):
    print("\n--- 1. Cleaning Credential Suffix Leaks ---")
    corrections = {
        "cu_sasin__003": ("Philip", "C. Zerrillo"),
        "cu_sasin__004": ("Wantanee", "Poonvoralak"),
        "cu_sasin_sorapop_048": ("Sorapop", "Kiatpongsan"),
        "tu_grad_wanny_181": ("Wanny", "Oentoro"),
        "tu_sgs_prapaporn_255": ("Prapaporn", "Tivayanond Mongkhonvanit"),
    }
    updated = 0
    for fid, (fn, ln) in corrections.items():
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f:
            f.first_name = fn
            f.last_name = ln
            updated += 1
            print(f"  Fixed [{fid}]: {fn} {ln}")
    db.commit()
    print(f"Cleaned {updated} records.")


def reconcile_research_labs(db):
    print("\n--- 2. Reconciling Research Lab Leads ---")
    lab_mappings = {
        "mfu_pm25_air_quality_center": "mfu_health_sompoch_001",
        "nu_medical_biotech_genomics": "wave22_0287_902",
        "mfu_fungal_research_center": "mfu_w52_0828_968",
    }
    all_fids = {f.id for f in db.query(FacultyDB.id).all()}

    updated = 0
    for lab_id, target_lead in lab_mappings.items():
        lab = db.query(ResearchLabDB).filter(ResearchLabDB.id == lab_id).first()
        if not lab:
            print(f"  Warning: Lab {lab_id} not found!")
            continue
        if target_lead not in all_fids:
            print(f"  Warning: Target lead {target_lead} not found in faculties!")
            continue

        lab.lead_advisor_id = target_lead

        # Clean member list
        members = [m for m in (lab.member_faculty_ids or []) if m in all_fids]
        if target_lead not in members:
            members.insert(0, target_lead)
        lab.member_faculty_ids = members
        updated += 1
        print(f"  Linked [{lab_id}] -> lead: {target_lead} (members: {len(members)})")

    db.commit()
    print(f"Reconciled {updated} labs.")


def resolve_duplicate_emails(db):
    print("\n--- 3. Resolving Duplicate Email Clusters ---")

    # 3A: Scraper-leaked / generic email clusters
    # Format: email -> (authentic_owner_id_or_None, [ids_to_clear_or_None_for_all_others])
    scraper_leaks = {
        "jgsee@kmutt.ac.th": None, # generic school contact, clear from all individuals
        "saraban-srt-scit@psu.ac.th": None, # generic registry, clear from all
        "icwww@mahidol.ac.th": None, # webmaster, clear from all
        "csunis@kku.ac.th": "kk_ph_005", # Sunisa Chaiklieng
        "pornpch@kku.ac.th": "kku_ph__006", # Pornpimon Chupanit
        "wongsa@kku.ac.th": "kk_ph_006", # Wongsa Laohasiriwong
        "spongd@kku.ac.th": "kk_ph_001", # Pongdech Sarakarn
        "tiamsoon@tu.ac.th": "tu_socanth__009", # Tiamsoon Sirisrisak
        "kritti.t@tu.ac.th": "tu_grad__071_x", # Kritthee Tandasiddhi
        "siri.sra@mahidol.ac.th": "mahidoluni_collegeofm_sranoi_115", # Siri Sranoi
        "hyuk.cha@mahidol.edu": "mahidoluni_collegeofm_cha_073", # Thomas Hyuk Cha
        "suvich.kli@mahidol.ac.th": "mahidoluni_collegeofm_klinsmith_120", # Suvich Klinsmith
        "pat.s@chula.ac.th": "cu_ds_wave11_0019", # Pat Seeumpornroj
        "kanikap@g.swu.ac.th": "srinakhari_facultyofe_fac_067_067", # Kanika Phongphunsathaporn
        "patipat@su.ac.th": "su_eng_teacher_066", # Patipat Hongsuwan
        "wwararat@wu.ac.th": "wu_w51_0352_440", # Wararat Whanchit
        "sujin@su.ac.th": "su_eng_teacher_079", # Sujin Wootthichaiwat
        "cooper.wri@mahidol.ac.th": "mahidoluni_collegeofm_wright_150", # Cooper Wright
        "tana.tac@mahidol.ac.th": "mu_sci_wave14_b_0065", # Tana Taechalertpaisarn
        "krit@tbs.tu.ac.th": "tu_bus_tbs_023", # Krit Pathamaroj
        "kanda@kku.ac.th": "kku_eng_001", # Kanda Runapongsa Saikaew
        "pisan.su@kmitl.ac.th": "kmitl_w39_0180_995", # Pisan Sukwisute
    }

    cleared_emails_count = 0
    for email, authentic_id in scraper_leaks.items():
        records = db.query(FacultyDB).filter(FacultyDB.email == email).all()
        for r in records:
            if authentic_id is None or r.id != authentic_id:
                r.email = None
                cleared_emails_count += 1
    db.commit()
    print(f"Cleared {cleared_emails_count} misassigned/generic email references across {len(scraper_leaks)} clusters.")

    # 3B: Same-person duplicate pairs (Primary ID, Duplicate ID to merge & archive)
    same_person_pairs = [
        # CMU Public Policy College vs Primary Faculty
        ("chiangmaiu_facultyofp_khumsup_003", "cmu_spp__009"),
        ("chiangmaiu_facultyofp_leerasiri_031", "cmu_spp__027"),
        ("chiangmaiu_facultyofp_lee_033", "cmu_spp__022"),
        ("cmu_7ba9b6a6_1016", "cmu_spp__025"),
        ("cmu_eng_department_prof_58", "cmu_spp__001"),
        ("chiangmaiu_facultyofp_charoensri_038", "cmu_spp__016"),
        ("wave29_0002_116", "cmu_spp__026"),
        ("cmu_eng_department_wongkot_102", "cmu_spp__021"),
        ("chiangmaiu_facultyofp_chongrak_020", "cmu_spp__018"),
        ("cmu_4ebdaae7_4576", "cmu_spp__015"),
        ("cmu_bus_003", "cmu_spp__020"),
        ("cmu_eng_me_006", "cmu_spp__024"),
        ("chiangmaiu_facultyofp_gunawong_026", "cmu_spp__017"),

        # KMUTT SBT Thai vs EN duplicate pairs
        ("wave22_1333_602", "kmutt_sbt__018"),
        ("wave22_1326_115", "kmutt_sbt__003"),
        ("wave22_1334_633", "kmutt_sbt__020"),
        ("wave22_1330_509", "kmutt_sbt__012"),
        ("wave22_1328_695", "kmutt_sbt__006"),
        ("wave22_1327_307", "kmutt_sbt__005"),
        ("wave22_1325_223", "kmutt_sbt__001"),
        ("wave22_1332_818", "kmutt_sbt__013"),
        ("wave22_1335_550", "kmutt_sbt__021"),
        ("wave22_1331_522", "kmutt_sbt__011"),
        ("wave22_1324_339", "kmutt_sbt__002"),
        ("wave22_1329_752", "kmutt_sbt__008"),

        # Mahidol Institute for Innovative Learning duplicates
        ("mu_il_khajornsak_001", "mu_il__0166"),
        ("mu_il__0181", "mu_il__0167"),
        ("mu_il__0183", "mu_il__0178"),
        ("mu_il__0180", "mu_il__0179"),

        # Mahidol Liberal Arts & Environment duplicates
        ("mu_la__006", "mu_w57_10328_628"),
        ("mu_la__007", "mu_w57_9037_180"),
        ("mu_env__031", "mu_w57_4472_522"),
        ("mu_env__044", "cu_w58_6362_417"),
        ("mu_env__009", "mu_w57_4244_417"),
        ("mu_env__018", "mu_w57_2604_515"),
        ("mu_env__011", "mu_w57_2800_118"),

        # Others
        ("kmutt_jgsee_staff_012", "kmutt_jgsee__001"),
        ("cmu_fa__037", "silpakornu_facultyoff_wanjring_011"),
        ("mfu_im_21667", "wave30_0188_164"),
        ("tu_econ_0001", "chulalongk_facultyofe_phankitnirundor_014"),
        ("cu_arch_0120", "cu_ds_wave11_0031"),
    ]

    merged_count = 0
    for prim_id, sec_id in same_person_pairs:
        prim = db.query(FacultyDB).filter(FacultyDB.id == prim_id).first()
        sec = db.query(FacultyDB).filter(FacultyDB.id == sec_id).first()
        if not prim or not sec:
            print(f"  Skip pair {prim_id} / {sec_id}: one or both not found.")
            continue

        # Merge metrics
        prim.total_citations = max(prim.total_citations or 0, sec.total_citations or 0)
        prim.h_index = max(prim.h_index or 0, sec.h_index or 0)
        prim.total_publications_count = max(prim.total_publications_count or 0, sec.total_publications_count or 0)
        prim.first_author_count = max(prim.first_author_count or 0, sec.first_author_count or 0)
        prim.co_author_count = max(prim.co_author_count or 0, sec.co_author_count or 0)

        # Union lists
        def union_lists(l1, l2):
            s = list(l1 or [])
            for item in (l2 or []):
                if item not in s:
                    s.append(item)
            return s

        prim.research_interests = union_lists(prim.research_interests, sec.research_interests)
        prim.featured_publications = union_lists(prim.featured_publications, sec.featured_publications)
        prim.taught_courses = union_lists(prim.taught_courses, sec.taught_courses)
        prim.education = union_lists(prim.education, sec.education)

        # Fill missing scalar attributes
        if not prim.email and sec.email:
            prim.email = sec.email
        if not prim.image_url and sec.image_url:
            prim.image_url = sec.image_url
        if not prim.openalex_id and sec.openalex_id:
            prim.openalex_id = sec.openalex_id
        if (not prim.first_name or not prim.first_name.isascii()) and sec.first_name and sec.first_name.isascii():
            prim.first_name = sec.first_name
        if (not prim.last_name or not prim.last_name.isascii()) and sec.last_name and sec.last_name.isascii():
            prim.last_name = sec.last_name

        # Re-point research labs lead_advisor_id or member list
        labs_led = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == sec.id).all()
        for l in labs_led:
            l.lead_advisor_id = prim.id

        all_labs = db.query(ResearchLabDB).all()
        for l in all_labs:
            if l.member_faculty_ids and sec.id in l.member_faculty_ids:
                l.member_faculty_ids = [prim.id if m == sec.id else m for m in l.member_faculty_ids]
                # dedup
                l.member_faculty_ids = list(dict.fromkeys(l.member_faculty_ids))

        # Archive sec into scholars_unassigned
        existing_arch = db.query(ScholarUnassignedDB).filter(ScholarUnassignedDB.id == sec.id).first()
        if not existing_arch:
            arch = ScholarUnassignedDB(
                id=sec.id,
                university=sec.university,
                university_th=sec.university_th,
                faculty=sec.faculty,
                faculty_th=sec.faculty_th,
                department=sec.department,
                department_th=sec.department_th,
                academic_title_th=sec.academic_title_th,
                first_name=sec.first_name,
                last_name=sec.last_name,
                full_name_th=sec.full_name_th,
                role=sec.role,
                email=sec.email,
                image_url=sec.image_url,
                profile_url=sec.profile_url,
                education=sec.education,
                research_interests=sec.research_interests,
                taught_courses=sec.taught_courses,
                featured_publications=sec.featured_publications,
                total_publications_count=sec.total_publications_count,
                first_author_count=sec.first_author_count,
                co_author_count=sec.co_author_count,
                total_citations=sec.total_citations,
                h_index=sec.h_index,
                openalex_id=sec.openalex_id,
                scholar_url=sec.scholar_url,
                embedding_text=sec.embedding_text,
                embedding=sec.embedding,
            )
            db.add(arch)

        # Remove sec from faculties
        db.delete(sec)
        merged_count += 1
        print(f"  Merged [{sec_id}] into primary [{prim_id}] ({prim.full_name_th})")

    db.commit()
    print(f"Merged and archived {merged_count} duplicate scholar records.")


def apply_romanization_cache(db):
    print("\n--- 4. Applying Verified Romanization Cache ---")
    if not CACHE_PATH.exists():
        print("  Warning: thai_romanization_cache.json not found!")
        return

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    print(f"Loaded cache with {len(cache)} entries.")

    # Target 1: Thai characters in English name fields
    thai_in_en = db.query(FacultyDB).filter(
        (FacultyDB.first_name.op("~")("[ก-๙]")) | (FacultyDB.last_name.op("~")("[ก-๙]"))
    ).all()

    # Target 2: Empty or null last_name
    null_ln = db.query(FacultyDB).filter(
        (FacultyDB.last_name.is_(None)) | (FacultyDB.last_name == "")
    ).all()

    targets = {f.id: f for f in (thai_in_en + null_ln)}
    print(f"Total targets needing clean English names: {len(targets)}")

    applied = 0
    for fid, fac in targets.items():
        if fid in cache:
            entry = cache[fid]
            fn = entry.get("first_name", "").strip()
            ln = entry.get("last_name", "").strip()
            if fn.isascii() and ln.isascii() and len(fn) >= 2 and len(ln) >= 2:
                fac.first_name = fn
                fac.last_name = ln
                applied += 1

    db.commit()
    print(f"Successfully applied verified Romanized names to {applied} records from disk cache.")


def main():
    db = SessionLocal()
    try:
        clean_credential_suffixes(db)
        reconcile_research_labs(db)
        resolve_duplicate_emails(db)
        apply_romanization_cache(db)
        print("\nAll Stages 1-4 completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
