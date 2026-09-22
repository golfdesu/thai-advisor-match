# -*- coding: utf-8 -*-
"""
Comprehensive Database Quality Hygiene & Invariant Enforcement:
1. Null out 832 personal freemails (@gmail.com, @hotmail.com, @yahoo.com, @outlook.com, @live.com) per Section 7 PDPA.
2. Rename 'citations' to 'citation_count' in featured_publications for 2 records.
3. Clean unparsed slash in research_interests for kmutt_w38_0199_459.
4. Deduplicate intra-faculty duplicate items in research_interests (26 records).
5. Resolve relative image URL for psu_eng_wave11_0052.
6. Set canonical English university name for 30 Chula discovery records.
7. Reset MFU Komsan Suriya metrics (not_indexed, 0 citations).
8. Clear cross-contaminated CMU email on KKU record (khonkaenun_facultyofm_fac_012_012).
9. Enforce mathematical monotonicity: total_publications_count >= h_index across all records.
10. Save disk snapshots to backend/data/agent_states/.
"""
import os
import sys
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from sqlalchemy.orm import defer
from scripts.audits.apply_secondary_scan_repairs import TH_TO_EN_CANONICAL

def build_faculty_embedding_text(f: FacultyDB) -> str:
    parts = []
    if f.full_name_th:
        parts.append(f.full_name_th)
    en_name = f"{f.first_name or ''} {f.last_name or ''}".strip()
    if en_name:
        parts.append(en_name)
    if f.university_th:
        parts.append(f.university_th)
    if f.faculty_th:
        parts.append(f.faculty_th)
    if f.department_th:
        parts.append(f.department_th)
    if f.research_interests:
        interests = " ".join(f.research_interests) if isinstance(f.research_interests, list) else str(f.research_interests)
        parts.append(interests)
    if f.featured_publications and isinstance(f.featured_publications, list):
        pub_titles = [p.get("title", "") for p in f.featured_publications if isinstance(p, dict) and p.get("title")]
        if pub_titles:
            parts.append(" ".join(pub_titles[:5]))
    return " | ".join([p for p in parts if p.strip()])

def main():
    db = SessionLocal()

    # 1. Null out personal freemails
    freemail_domains = ("@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com", "@live.com")
    all_facs = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)

    freemail_snapshot = []
    freemail_count = 0
    for f in all_facs:
        if f.email:
            em_lower = f.email.strip().lower()
            if any(em_lower.endswith(dom) for dom in freemail_domains):
                freemail_snapshot.append({
                    "id": f.id,
                    "full_name_th": f.full_name_th,
                    "old_email": f.email
                })
                f.email = None
                f.embedding_text = build_faculty_embedding_text(f)
                freemail_count += 1

    print(f"1. Nulled {freemail_count} personal freemail addresses.")

    # 2. Rename 'citations' to 'citation_count' in featured_publications
    citations_key_count = 0
    for fid in ['cmu_eng_civil_tantrapongsatorn_011', 'cmu_eng_cpe_sakgasit_025']:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f and f.featured_publications:
            new_pubs = []
            for p in f.featured_publications:
                if isinstance(p, dict):
                    p_copy = dict(p)
                    if 'citations' in p_copy:
                        p_copy['citation_count'] = p_copy.pop('citations')
                    new_pubs.append(p_copy)
                else:
                    new_pubs.append(p)
            f.featured_publications = new_pubs
            f.embedding_text = build_faculty_embedding_text(f)
            citations_key_count += 1
    print(f"2. Fixed 'citations' key in {citations_key_count} records.")

    # 3. Clean unparsed slash in research_interests for kmutt_w38_0199_459
    kmutt_f = db.query(FacultyDB).filter(FacultyDB.id == 'kmutt_w38_0199_459').first()
    if kmutt_f and kmutt_f.research_interests:
        new_ints = []
        for it in kmutt_f.research_interests:
            if ' / ' in str(it):
                new_ints.append(str(it).replace(' / ', ' and '))
            else:
                new_ints.append(it)
        kmutt_f.research_interests = new_ints
        kmutt_f.embedding_text = build_faculty_embedding_text(kmutt_f)
        print("3. Fixed unparsed slash in kmutt_w38_0199_459.")

    # 4. Deduplicate intra-faculty duplicate items in research_interests
    all_facs2 = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)
    dedup_interest_count = 0
    for f in all_facs2:
        if f.research_interests and isinstance(f.research_interests, list):
            # Check duplicates
            seen = set()
            cleaned = []
            has_dup = False
            for it in f.research_interests:
                s = str(it).strip()
                if s:
                    s_lower = s.lower()
                    if s_lower in seen:
                        has_dup = True
                    else:
                        seen.add(s_lower)
                        cleaned.append(s)
            if has_dup:
                f.research_interests = cleaned
                f.embedding_text = build_faculty_embedding_text(f)
                dedup_interest_count += 1
    print(f"4. Deduplicated interests in {dedup_interest_count} records.")

    # 5. Resolve relative image URL for psu_eng_wave11_0052
    psu_f = db.query(FacultyDB).filter(FacultyDB.id == 'psu_eng_wave11_0052').first()
    if psu_f and psu_f.image_url and psu_f.image_url.startswith('/'):
        psu_f.image_url = f"https://ee.psu.ac.th{psu_f.image_url}"
        print(f"5. Resolved relative image for psu_eng_wave11_0052: {psu_f.image_url}")

    # 6. Set canonical English university name for Chula discovery records
    cu_disc = db.query(FacultyDB).filter(
        FacultyDB.university_th == 'จุฬาลงกรณ์มหาวิทยาลัย',
        FacultyDB.university.is_(None)
    ).all()
    for f in cu_disc:
        f.university = 'Chulalongkorn University'
    print(f"6. Synchronized English university name on {len(cu_disc)} Chula records.")

    # 7. Reset MFU Komsan Suriya metrics
    mfu_komsan = db.query(FacultyDB).filter(FacultyDB.id == 'mfu_med_komsan_001').first()
    if mfu_komsan:
        mfu_komsan.total_citations = 0
        mfu_komsan.h_index = 0
        mfu_komsan.total_publications_count = 0
        mfu_komsan.openalex_id = "not_indexed"
        mfu_komsan.embedding_text = build_faculty_embedding_text(mfu_komsan)
        print("7. Reset MFU Komsan Suriya metrics.")

    # 8. Clear cross-contaminated CMU email on KKU record
    kku_nat = db.query(FacultyDB).filter(FacultyDB.id == 'khonkaenun_facultyofm_fac_012_012').first()
    if kku_nat and kku_nat.email:
        kku_nat.email = None
        kku_nat.embedding_text = build_faculty_embedding_text(kku_nat)
        print("8. Cleared cross-contaminated email on khonkaenun_facultyofm_fac_012_012.")

    # 9. Enforce mathematical monotonicity: total_publications_count >= h_index
    all_facs3 = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)
    monotonic_count = 0
    for f in all_facs3:
        if f.h_index and (f.total_publications_count is None or f.total_publications_count < f.h_index):
            f.total_publications_count = f.h_index
            monotonic_count += 1
    print(f"9. Enforced total_publications_count >= h_index on {monotonic_count} records.")

    db.commit()

    # Save snapshot
    snap_file = os.path.join(BACKEND_DIR, "data", "agent_states", "database_quality_hygiene_snapshot.json")
    with open(snap_file, "w", encoding="utf-8") as out:
        json.dump({
            "freemails_nulled": freemail_count,
            "citations_key_fixed": citations_key_count,
            "dedup_interests_fixed": dedup_interest_count,
            "cu_disc_fixed": len(cu_disc),
            "monotonic_fixed": monotonic_count
        }, out, indent=2)
    print(f"Checkpoints saved to {snap_file}.")

    db.close()

if __name__ == "__main__":
    main()
