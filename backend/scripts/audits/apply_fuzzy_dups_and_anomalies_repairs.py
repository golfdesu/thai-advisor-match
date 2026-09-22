# -*- coding: utf-8 -*-
import os
import sys
import json
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text
from sqlalchemy.orm.attributes import flag_modified

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SNAPSHOT_FILE = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_fuzzy_dups_and_anomalies_snapshot.json")

def merge_faculty(db, primary_id, donor_id):
    primary = db.query(FacultyDB).filter(FacultyDB.id == primary_id).first()
    donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()
    if not primary or not donor:
        print(f"Error: Could not find primary {primary_id} or donor {donor_id}")
        return None

    # Merge scalar metrics (max)
    primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
    primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
    primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
    primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
    primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

    # Merge missing fields
    if not primary.email and donor.email:
        primary.email = donor.email
    if not primary.profile_url and donor.profile_url:
        primary.profile_url = donor.profile_url
    if not primary.image_url and donor.image_url:
        primary.image_url = donor.image_url
    if not primary.faculty_th and donor.faculty_th:
        primary.faculty_th = donor.faculty_th
    if not primary.department_th and donor.department_th:
        primary.department_th = donor.department_th
    if not primary.openalex_id and donor.openalex_id:
        primary.openalex_id = donor.openalex_id

    # Merge JSON lists (publications, interests, courses, education)
    # Publications dedup by title
    existing_titles = set()
    merged_pubs = []
    for p in (primary.featured_publications or []):
        if isinstance(p, dict) and p.get("title"):
            t_clean = p["title"].strip().lower()
            if t_clean not in existing_titles:
                existing_titles.add(t_clean)
                merged_pubs.append(p)
    for p in (donor.featured_publications or []):
        if isinstance(p, dict) and p.get("title"):
            t_clean = p["title"].strip().lower()
            if t_clean not in existing_titles:
                existing_titles.add(t_clean)
                merged_pubs.append(p)
    primary.featured_publications = merged_pubs
    flag_modified(primary, "featured_publications")

    # Research interests dedup
    existing_ri = set(x.strip().lower() for x in (primary.research_interests or []) if isinstance(x, str))
    merged_ri = list(primary.research_interests or [])
    for ri in (donor.research_interests or []):
        if isinstance(ri, str) and ri.strip().lower() not in existing_ri:
            existing_ri.add(ri.strip().lower())
            merged_ri.append(ri)
    primary.research_interests = merged_ri
    flag_modified(primary, "research_interests")

    # Re-point foreign keys in research_labs
    labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor_id).all()
    for lab in labs:
        lab.lead_advisor_id = primary_id
        print(f"  Re-pointed lab {lab.id} lead_advisor_id to {primary_id}")

    # Rebuild embedding text
    primary.embedding_text = build_faculty_embedding_text(primary)

    # Delete donor
    db.delete(donor)
    print(f"Merged donor {donor_id} into primary {primary_id} and deleted donor")
    return {
        "primary_id": primary_id,
        "donor_id": donor_id,
        "primary_name": primary.full_name_th,
        "donor_name": donor.full_name_th,
    }

def main():
    db = SessionLocal()
    snapshot = {
        "merges": [],
        "name_repairs": [],
        "interest_cleanups": []
    }

    # 1. Intra-university fuzzy duplicate merges
    dups_to_merge = [
        ("fca-cu-004_5fac49", "cu_324b07ab_4553"),   # Saravudh Anantachart (Chula CommArts)
        ("ssru_w56_1849_809", "ssru_w56_1735_335"),   # ลำไผ่ ตระกูลสันติ (SSRU)
        ("mju_w54_1545_646", "mju_w54_1585_128"),     # เฉลิมชัย ปัญญาดี (MJU)
        ("udru_w56_0257_734", "udru_w56_0619_105"),   # กฤตติกา แสนโภชน์ (UDRU)
        ("pbru_w56_0246_723", "pbru_w56_0287_924"),   # ณฐกร นิลเนตร (PBRU)
    ]

    print("\n--- 1. Merging 5 Verified Intra-University Duplicates ---")
    for prim_id, don_id in dups_to_merge:
        res = merge_faculty(db, prim_id, don_id)
        if res:
            snapshot["merges"].append(res)

    # 2. Fix rmuti_w53b_3731_548 name corruption
    print("\n--- 2. Fixing Name Corruption for rmuti_w53b_3731_548 ---")
    f_rmuti = db.query(FacultyDB).filter(FacultyDB.id == "rmuti_w53b_3731_548").first()
    if f_rmuti:
        f_rmuti.academic_title_th = "ดร."
        f_rmuti.first_name = "M."
        f_rmuti.last_name = "Madhavi"
        f_rmuti.full_name_th = "M. Madhavi"
        f_rmuti.embedding_text = build_faculty_embedding_text(f_rmuti)
        snapshot["name_repairs"].append({
            "id": f_rmuti.id,
            "old_fn": "(Ph.D)",
            "old_ln": "Mrs. M. Madhavi M. Tech",
            "new_fn": "M.",
            "new_ln": "Madhavi",
            "new_full_name_th": "M. Madhavi"
        })
        print(f"Fixed rmuti_w53b_3731_548 -> M. Madhavi (ดร.)")

    # 3. Clean junk tokens from research_interests
    print("\n--- 3. Cleaning Junk Tokens from Research Interests ---")
    junk_tokens = {"2010-2016", "1844-1900", ":", "/??", "etc.", "etc", "...", "-", "--", "ฯลฯ"}
    interest_targets = [
        "ku_wave17_soc_0066", "ku_wave17_hum_0041", "su_w43_0085_645", "su_w43_0087_840",
        "su_w43_0089_949", "su_w43_0091_443", "su_w43_0093_240", "su_w43_0083_529",
        "su_w43_0094_640", "ku_wave17_hum_0062", "kku_sci_wave14_b_0096"
    ]
    for fid in interest_targets:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f and f.research_interests:
            old_ri = list(f.research_interests)
            new_ri = [x for x in old_ri if str(x).strip() not in junk_tokens and len(str(x).strip()) > 1]
            if len(new_ri) != len(old_ri):
                f.research_interests = new_ri
                flag_modified(f, "research_interests")
                f.embedding_text = build_faculty_embedding_text(f)
                snapshot["interest_cleanups"].append({
                    "id": fid,
                    "removed": [x for x in old_ri if x not in new_ri]
                })
                print(f"Cleaned research interests for {fid}: removed {[x for x in old_ri if x not in new_ri]}")

    db.commit()
    db.close()

    os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"\nCheckpoint written to: {SNAPSHOT_FILE}")

if __name__ == "__main__":
    main()
