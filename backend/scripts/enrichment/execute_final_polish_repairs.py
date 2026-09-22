# -*- coding: utf-8 -*-
"""
Final Polish Repairs & Complete Zero-Defect Optimization:
1. Fix remaining English names with title tokens (expanding 'Md' -> 'Mohammad', removing Dr./Ph.D./Prof./Asst.).
2. Merge the remaining 89 same-university duplicate clusters:
   - Normalizes Unicode hyphens (‐, –, —) to standard ASCII '-'.
   - Strips trailing degrees (, Ph.D., D.V.M., etc.) from surnames.
   - Normalizes dots and whitespace.
   - Merges metrics: max(total_citations), max(h_index), max(total_publications_count).
   - Unions featured_publications and research_interests.
   - Re-points research_labs.lead_advisor_id.
   - Saves snapshot to backend/data/agent_states/final_polish_repairs_snapshot.json.
3. Rebuilds primary embedding_text.
"""
import os
import sys
import re
import json
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.embedding_text import build_faculty_embedding_text

THAI_REGEX = re.compile(r'[฀-๿]')

def normalize_name(s):
    if not s: return ""
    s = re.sub(r'[‐-―−]', '-', s)
    s = re.sub(r',\s*(?:Ph\.?D\.?|D\.?V\.?M\.?(?:\s*\(Hons\))?|M\.?D\.?|M\.?Sc\.?|B\.?Sc\.?|Hons).*$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(?:Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mrs\.?|Ms\.?|Ph\.?D\.?)\s*', '', s, flags=re.IGNORECASE)
    s = s.replace('.', '')
    return re.sub(r'\s+', ' ', s).strip().lower()

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
    print("🚀 EXECUTING FINAL POLISH REPAIRS & COMPLETE DEDUPLICATION")
    print("======================================================================")

    # 1. Clean English title prefixes and expand 'Md' -> 'Mohammad'
    print("\n--- 1. Cleaning English Name Tokens ---")
    name_cleanups = [
        ('nrru_w56_0204_758', 'Atthawit', 'Singsalasang', 'ผศ.ดร.'),
        ('nstru_w56_0372_944', 'Mohammad', 'Alfanuzzaman', None),
        ('pcru_w56_0256_985', 'Xiaoyin', 'Zhang', 'ศ.ดร.'),
        ('pcru_w56_0257_171', 'Xiaoyin', 'Zhang', 'ศ.ดร.'),
        ('pnru_w56_0273_253', 'Kwanming', 'Khumprasert', 'ดร.'),
        ('pnru_w56_0287_434', 'Piphat', 'Kovitkanit', 'ดร.'),
        ('rmuti_w53b_2296_993', 'Duanpen', 'Wongsorn', 'ผศ.ดร.'),
        ('uru_w56_0226_187', 'Niramon', 'Suwangard', 'ศ.ดร.'),
        ('wu_w51_0978_780', 'Mohammad Eshrat E.', 'Alahi', None),
        ('tsu_w50_1583_132', 'Mohammad Ahbabur', 'Rahman', None),
    ]
    for fid, fn, ln, title in name_cleanups:
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f:
            f.first_name = fn
            f.last_name = ln
            if title and not f.academic_title_th:
                f.academic_title_th = title
            f.embedding_text = build_faculty_embedding_text(f)
            print(f"  Fixed {fid}: fn='{fn}', ln='{ln}', title='{title or f.academic_title_th}'")

    # 2. Merge remaining same-university duplicate clusters
    print("\n--- 2. Merging Remaining Same-University Duplicate Clusters ---")
    all_facs = db.query(FacultyDB).all()
    groups = defaultdict(list)
    for f in all_facs:
        if not f.university_th: continue
        norm = normalize_name(f.full_name_th)
        if not norm and f.first_name and f.last_name:
            norm = f"{normalize_name(f.first_name)} {normalize_name(f.last_name)}".strip()
        if norm:
            groups[(f.university_th, norm)].append(f)

    dups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"  Found {len(dups)} duplicate clusters to merge.")

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "description": "Final Polish Same-University Deduplication",
        "merges": []
    }

    total_donors_deleted = 0
    for (univ, norm_name), cluster in dups.items():
        sorted_cluster = sorted(cluster, key=score_faculty, reverse=True)
        primary = sorted_cluster[0]
        donors = sorted_cluster[1:]

        merge_entry = {
            "university_th": univ,
            "norm_name": norm_name,
            "primary_id": primary.id,
            "donor_ids": [d.id for d in donors],
            "primary_before_cites": primary.total_citations,
            "donors_count": len(donors)
        }

        # Union publications
        all_pubs = []
        seen_pub_titles = set()
        for p in (primary.featured_publications or []):
            if isinstance(p, dict) and p.get("title"):
                t = p["title"].strip().lower()
                if t not in seen_pub_titles:
                    seen_pub_titles.add(t)
                    all_pubs.append(p)

        all_interests = list(primary.research_interests or [])
        seen_interests = set(all_interests)

        for donor in donors:
            # Metrics
            primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
            primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
            primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
            primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
            primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

            # Metadata fallback
            if not primary.email and donor.email:
                primary.email = donor.email
            if (not primary.openalex_id or primary.openalex_id == "not_indexed") and (donor.openalex_id and donor.openalex_id != "not_indexed"):
                primary.openalex_id = donor.openalex_id
            if not primary.academic_title_th and donor.academic_title_th:
                primary.academic_title_th = donor.academic_title_th

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

            for p in (donor.featured_publications or []):
                if isinstance(p, dict) and p.get("title"):
                    t = p["title"].strip().lower()
                    if t not in seen_pub_titles:
                        seen_pub_titles.add(t)
                        all_pubs.append(p)

            for item in (donor.research_interests or []):
                if item not in seen_interests:
                    seen_interests.add(item)
                    all_interests.append(item)

            # Re-point research labs
            db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).update(
                {ResearchLabDB.lead_advisor_id: primary.id}, synchronize_session=False
            )

            db.delete(donor)
            total_donors_deleted += 1

        primary.featured_publications = all_pubs[:20]
        primary.research_interests = all_interests[:20]
        primary.embedding_text = build_faculty_embedding_text(primary)
        snapshot["merges"].append(merge_entry)

    print(f"  Successfully merged and deleted {total_donors_deleted} donor records across {len(dups)} clusters.")

    # Save snapshot
    snap_path = os.path.join(BACKEND_DIR, "data", "agent_states", "final_polish_repairs_snapshot.json")
    with open(snap_path, "w", encoding="utf-8") as out:
        json.dump(snapshot, out, ensure_ascii=False, indent=2)
    print(f"  Saved snapshot checkpoint to {snap_path}")

    db.commit()
    db.close()
    print("\n======================================================================")
    print("✅ FINAL POLISH REPAIRS COMPLETED AND COMMITTED")
    print("======================================================================")

if __name__ == "__main__":
    main()
