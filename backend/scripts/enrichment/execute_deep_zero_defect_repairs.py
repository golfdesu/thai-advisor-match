# -*- coding: utf-8 -*-
"""
Comprehensive Deep Zero-Defect Database Repairs & Alignment:
1. Fix 12 duplicate email collisions (set secondary/misaligned emails to None).
2. Clean English first_name / last_name containing title prefixes (swu, mfu, ku, tsu, wu).
3. Fix the 8 'Agro' last_name records at Kasetsart University to authentic surnames.
4. Disambiguate cmu_eng_department_tanchaisawat_45 OpenAlex ID to 'not_indexed'.
5. Normalize Thai in first_name/last_name to None (where full_name_th already has Thai name).
6. Populate first_name and last_name from English full_name_th where first_name is None.
7. Execute Pass 2 Deduplication on the same-university duplicate clusters (Waves 53-56).
   - Preserves maximum metrics (total_citations, h_index, total_publications_count).
   - Unions featured_publications and research_interests.
   - Re-points research_labs.lead_advisor_id.
   - Saves checkpoint snapshot to backend/data/agent_states/dedup_pass2_waves53_56_snapshot.json.
8. Rebuild primary embedding_text.
"""
import os
import sys
import re
import json
from datetime import datetime
from collections import defaultdict
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text
from sqlalchemy.orm import defer

THAI_REGEX = re.compile(r'[฀-๿]')
RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b)\s*",
    re.IGNORECASE
)

def parse_en_name(full_name):
    if not full_name:
        return None, None
    s = RE_EN_PREFIX.sub("", full_name).strip()
    # Strip any trailing degrees like ', Ph.D.'
    s = re.sub(r',\s*Ph\.?D\.?$', '', s, flags=re.IGNORECASE).strip()
    parts = s.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return None, None

def score_faculty(fac):
    s = 0
    name_th = fac.full_name_th or ""
    if THAI_REGEX.search(name_th): s += 150
    if fac.academic_title_th: s += 50
    if fac.email and len(fac.email) > 5 and "@" in fac.email: s += 100
    if fac.openalex_id and fac.openalex_id != "not_indexed": s += 80
    if fac.total_citations: s += min(fac.total_citations, 50)
    if fac.featured_publications: s += len(fac.featured_publications) * 2
    if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 20
    if fac.image_url: s += 10
    return s

def main():
    db = SessionLocal()
    print("======================================================================")
    print("🚀 STARTING DEEP ZERO-DEFECT REPAIRS & REFINEMENTS")
    print("======================================================================")

    # ---------------------------------------------------------
    # 1. Fix 12 duplicate email collisions
    # ---------------------------------------------------------
    print("\n--- 1. Fixing Duplicate Email Collisions ---")
    null_emails = [
        ('cu_sci_wave14_b_0025', 'cu_sci_wave14_b_0025 Nattapong Paiboonvorachat (keep econ-cu-007_87289a)'),
        ('regionalun_facultymem_klinmanee_049', 'regionalun_facultymem_klinmanee_049 Nathamon Klinmanee (keep wu_w51_0352_440 Wararat)'),
        ('psu_w41_0107_806', 'psu_w41_0107_806 Pattama Sentong (keep psu_w41_0078_660 Parinuch)'),
        ('wave21_0082_514', 'wave21_0082_514 Ubolluk Rattanasak (keep wave21_0081_607 Rungnapha)'),
        ('wave21_0105_902', 'wave21_0105_902 Manatsawee Janrod (not nattapon)'),
        ('wave21_0106_886', 'wave21_0106_886 Sarayut Vetchasit (not nattapon)'),
        ('wave21_0133_726', 'wave21_0133_726 Suriyawut (keep wave21_0132_914 Piyapong)'),
        ('wave21_0138_739', 'wave21_0138_739 Vorathep (keep wave21_0137_971 Teeraphot)'),
        ('wave21_0156_975', 'wave21_0156_975 Witchapol (keep wave21_0155_491 Purimpat)'),
        ('wave21_0159_724', 'wave21_0159_724 Poramet (keep wave21_0158_439 Adisorn)'),
        ('wave21_0163_156', 'wave21_0163_156 Nattapong (keep wave21_0162_421 Sitthidet)'),
        ('wave21_0168_445', 'wave21_0168_445 Korawin (keep wave21_0167_913 Surapol)'),
        ('wave21_0206_129', 'wave21_0206_129 Somkid (keep wave21_0205_480 Sunanta)'),
    ]
    for fid, reason in null_emails:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f and f.email:
            print(f"  Nulled email on {reason}: {f.email}")
            f.email = None
            f.embedding_text = build_faculty_embedding_text(f)

    # ---------------------------------------------------------
    # 2. Clean English names containing title prefixes
    # ---------------------------------------------------------
    print("\n--- 2. Cleaning English Names with Title Prefixes ---")
    en_fixes = [
        ('wu_w51_0978_780', 'Md Eshrat E.', 'Alahi'),
        ('swu_w44_0101_161', 'Chalao', 'Thepchalerm'),
        ('mfu_w52_0181_934', 'Khen Suan', 'Khai'),
        ('ku_agro_wave15_0011', 'Suttipun', 'Keawsompong'),
        ('ku_agro_wave15_0021', 'Namfone', 'Lumdubwong'),
        ('tsu_w50_0169_438', 'Wassana', 'Suwanvijit'),
        ('tsu_w50_1583_132', 'Md Ahbabur', 'Rahman'),
    ]
    for fid, fn, ln in en_fixes:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f:
            print(f"  Fixed {fid}: fn='{f.first_name}' -> '{fn}', ln='{f.last_name}' -> '{ln}'")
            f.first_name = fn
            f.last_name = ln
            f.embedding_text = build_faculty_embedding_text(f)

    # ---------------------------------------------------------
    # 3. Fix 8 'Agro' last_name records at Kasetsart University
    # ---------------------------------------------------------
    print("\n--- 3. Fixing 'Agro' Surnames at Kasetsart University ---")
    agro_fixes = [
        ('kasetsartu_facultyofa_pharakulsuksati_005', 'Pharakulsuksathit'),
        ('ku_agro_wave15_0034', 'Charoensiddhi'),
        ('ku_agro_wave15_0082', 'Lekuthai'),
        ('ku_agro_wave15_0089', 'Prompen'),
        ('ku_wave18_nrai_0045', 'Phattayakorn'),
        ('ku_wave18_nrai_0047', 'Photiset'),
        ('ku_wave18_nrai_0052', 'Phosanam'),
        ('ku_wave18_nrai_0014', 'Phongkaew'),
    ]
    for fid, true_ln in agro_fixes:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f:
            print(f"  Fixed {fid} ({f.full_name_th}): ln='{f.last_name}' -> '{true_ln}'")
            f.last_name = true_ln
            f.embedding_text = build_faculty_embedding_text(f)

    # ---------------------------------------------------------
    # 4. Disambiguate cmu_eng_department_tanchaisawat_45 OpenAlex ID
    # ---------------------------------------------------------
    print("\n--- 4. Disambiguating OpenAlex ID on cmu_eng_department_tanchaisawat_45 ---")
    cmu_tan = db.query(FacultyDB).filter(FacultyDB.id == 'cmu_eng_department_tanchaisawat_45').first()
    if cmu_tan and cmu_tan.openalex_id == 'https://openalex.org/A5029182143':
        print(f"  Reset OpenAlex ID on {cmu_tan.id} ({cmu_tan.full_name_th}) from {cmu_tan.openalex_id} to 'not_indexed'.")
        cmu_tan.openalex_id = 'not_indexed'
        cmu_tan.total_citations = 0
        cmu_tan.h_index = 0
        cmu_tan.total_publications_count = 0
        cmu_tan.embedding_text = build_faculty_embedding_text(cmu_tan)

    # ---------------------------------------------------------
    # 5. Normalize Thai in first_name/last_name to None
    # ---------------------------------------------------------
    print("\n--- 5. Normalizing Thai Characters in first_name/last_name ---")
    thai_name_facs = db.query(FacultyDB).filter(
        (FacultyDB.first_name.op('~')('[฀-๿]')) |
        (FacultyDB.last_name.op('~')('[฀-๿]'))
    ).all()
    print(f"  Found {len(thai_name_facs)} records with Thai characters in first_name/last_name.")
    for f in thai_name_facs:
        f.first_name = None
        f.last_name = None

    # ---------------------------------------------------------
    # 6. Populate first_name and last_name from English full_name_th
    # ---------------------------------------------------------
    print("\n--- 6. Populating first_name and last_name from English full_name_th ---")
    all_facs = db.query(FacultyDB).all()
    populated_count = 0
    for f in all_facs:
        if not f.first_name and f.full_name_th and not THAI_REGEX.search(f.full_name_th):
            fn, ln = parse_en_name(f.full_name_th)
            if fn and ln:
                f.first_name = fn
                f.last_name = ln
                populated_count += 1
    print(f"  Populated first_name and last_name on {populated_count} records.")

    # ---------------------------------------------------------
    # 7. Execute Pass 2 Deduplication on Same-University Clusters
    # ---------------------------------------------------------
    print("\n--- 7. Executing Pass 2 Deduplication (Clean English Name + University) ---")
    pass2_groups = defaultdict(list)
    for f in all_facs:
        fn = f.first_name
        ln = f.last_name
        if fn and ln and not THAI_REGEX.search(fn) and not THAI_REGEX.search(ln) and f.university_th:
            fn_clean = fn.strip().lower()
            ln_clean = ln.strip().lower()
            if len(fn_clean.replace('.', '')) >= 2 and len(ln_clean.replace('.', '')) >= 2:
                pass2_groups[(f.university_th, f"{fn_clean} {ln_clean}")].append(f)

    p2_dups = {k: v for k, v in pass2_groups.items() if len(v) > 1}
    print(f"  Found {len(p2_dups)} same-university duplicate clusters.")

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "pass": "Pass 2 Waves 53-56 Clean English Name + University",
        "merges": []
    }

    total_donors_deleted = 0
    for (univ, name_en), cluster in p2_dups.items():
        sorted_cluster = sorted(cluster, key=score_faculty, reverse=True)
        primary = sorted_cluster[0]
        donors = sorted_cluster[1:]

        merge_entry = {
            "university_th": univ,
            "name_en": name_en,
            "primary_id": primary.id,
            "donor_ids": [d.id for d in donors],
            "primary_before": {
                "id": primary.id,
                "full_name_th": primary.full_name_th,
                "email": primary.email,
                "openalex_id": primary.openalex_id,
                "total_citations": primary.total_citations,
                "h_index": primary.h_index,
                "total_publications_count": primary.total_publications_count,
            },
            "donors_data": []
        }

        # Collect union of publications and interests
        all_pubs = []
        seen_pub_titles = set()
        for p in (primary.featured_publications or []):
            if isinstance(p, dict) and p.get("title"):
                norm_t = p["title"].strip().lower()
                if norm_t not in seen_pub_titles:
                    seen_pub_titles.add(norm_t)
                    all_pubs.append(p)

        all_interests = list(primary.research_interests or [])
        seen_interests = set(all_interests)

        for donor in donors:
            merge_entry["donors_data"].append({
                "id": donor.id,
                "full_name_th": donor.full_name_th,
                "email": donor.email,
                "openalex_id": donor.openalex_id,
                "total_citations": donor.total_citations,
                "h_index": donor.h_index,
                "total_publications_count": donor.total_publications_count,
            })

            # Metrics
            primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
            primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
            primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
            primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
            primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

            # Contact & ID
            if not primary.email and donor.email:
                primary.email = donor.email
            if (not primary.openalex_id or primary.openalex_id == "not_indexed") and (donor.openalex_id and donor.openalex_id != "not_indexed"):
                primary.openalex_id = donor.openalex_id
            if not primary.academic_title_th and donor.academic_title_th:
                primary.academic_title_th = donor.academic_title_th

            # Thai name
            prim_has_thai = bool(THAI_REGEX.search(primary.full_name_th or ""))
            donor_has_thai = bool(THAI_REGEX.search(donor.full_name_th or ""))
            if not prim_has_thai and donor_has_thai:
                primary.full_name_th = donor.full_name_th

            if not primary.faculty_th and donor.faculty_th:
                primary.faculty_th = donor.faculty_th
            if not primary.department_th and donor.department_th:
                primary.department_th = donor.department_th
            if not primary.image_url and donor.image_url:
                primary.image_url = donor.image_url
            if not primary.profile_url and donor.profile_url:
                primary.profile_url = donor.profile_url

            # Publications union
            for p in (donor.featured_publications or []):
                if isinstance(p, dict) and p.get("title"):
                    norm_t = p["title"].strip().lower()
                    if norm_t not in seen_pub_titles:
                        seen_pub_titles.add(norm_t)
                        all_pubs.append(p)

            # Interests union
            for item in (donor.research_interests or []):
                if item not in seen_interests:
                    seen_interests.add(item)
                    all_interests.append(item)

            # Re-point research labs
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).update(
                {ResearchLabDB.lead_advisor_id: primary.id}, synchronize_session=False
            )

            # Delete donor
            db.delete(donor)
            total_donors_deleted += 1

        primary.featured_publications = all_pubs[:20]
        primary.research_interests = all_interests[:20]
        primary.embedding_text = build_faculty_embedding_text(primary)
        snapshot["merges"].append(merge_entry)

    print(f"  Successfully merged and deleted {total_donors_deleted} donor records across {len(p2_dups)} clusters.")

    # Save checkpoint snapshot
    snap_p2 = os.path.join(BACKEND_DIR, "data", "agent_states", "dedup_pass2_waves53_56_snapshot.json")
    with open(snap_p2, "w", encoding="utf-8") as out:
        json.dump(snapshot, out, ensure_ascii=False, indent=2)
    print(f"  Saved snapshot checkpoint to {snap_p2}")

    db.commit()
    db.close()
    print("\n======================================================================")
    print("✅ ALL DEEP ZERO-DEFECT REPAIRS COMPLETED AND COMMITTED")
    print("======================================================================")

if __name__ == "__main__":
    main()
