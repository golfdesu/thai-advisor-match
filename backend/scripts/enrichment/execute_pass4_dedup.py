# -*- coding: utf-8 -*-
"""
Pass 4 Deduplication & OpenAlex Quality Resolution:
1. Merge 33 verified same-person clusters (33 donor records) sharing identical OpenAlex IDs within same university.
2. Disambiguate 2 conflated/group OpenAlex IDs (40 records: 38 CMU pediatricians, 2 KU professors) by setting openalex_id = None.
3. Preserve all bibliometric metrics (max citations, h-index, works), union publications, re-point research_labs.
4. Save disk snapshots to backend/data/agent_states/.
"""
import os
import sys
import json
import re
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from sqlalchemy.orm import defer
from rapidfuzz import fuzz

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

def score_faculty(f: FacultyDB) -> int:
    score = 0
    # Prefer authentic Thai name over abbreviation or English-only stub in full_name_th
    th_name = (f.full_name_th or "").strip()
    if re.search(r"[฀-๿]{3,}", th_name):
        score += 150
    if f.email and "@" in f.email:
        score += 100
        # Bonus if email matches university domain
        if "sut.ac.th" in f.email or "nu.ac.th" in f.email or "mju.ac.th" in f.email or "wu.ac.th" in f.email or "ssru.ac.th" in f.email or "ku.ac.th" in f.email:
            score += 200
    if f.academic_title_th and f.academic_title_th not in ["นาย", "นาง", "นางสาว", "อ."]:
        score += 50
    if f.first_name and f.last_name and not re.search(r"^[A-Z]\.\s*", f.first_name):
        score += 60
    if f.department_th and f.department_th.strip():
        score += 40
    if f.research_interests and len(f.research_interests) > 0:
        score += 30
    if f.total_citations:
        score += min(f.total_citations, 50)
    return score

def main():
    db = SessionLocal()

    # 1. First address the two conflation/group OpenAlex IDs:
    # A5151438778 (38 CMU pediatricians)
    # A5093269494 (2 KU professors)
    CONFLATED_OA = ["A5151438778", "A5093269494"]

    conflated_faculties = db.query(FacultyDB).filter(
        FacultyDB.openalex_id.in_([
            "https://openalex.org/A5151438778", "A5151438778",
            "https://openalex.org/A5093269494", "A5093269494"
        ])
    ).all()

    conflated_snapshot = []
    print(f"Clearing conflated/group OpenAlex IDs on {len(conflated_faculties)} records...")
    for f in conflated_faculties:
        conflated_snapshot.append({
            "id": f.id,
            "full_name_th": f.full_name_th,
            "first_name": f.first_name,
            "last_name": f.last_name,
            "university_th": f.university_th,
            "old_openalex_id": f.openalex_id
        })
        f.openalex_id = None
        f.embedding_text = build_faculty_embedding_text(f)

    db.commit()
    print(f"Successfully cleared OpenAlex IDs on {len(conflated_snapshot)} records.")

    # Save snapshot
    conflated_file = os.path.join(BACKEND_DIR, "data", "agent_states", "clean_oa_conflations_snapshot.json")
    with open(conflated_file, "w", encoding="utf-8") as out:
        json.dump(conflated_snapshot, out, ensure_ascii=False, indent=2)

    # 2. Now find remaining intra-university duplicate OpenAlex clusters
    from collections import defaultdict
    all_faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).yield_per(1000)
    oa_groups = defaultdict(list)
    for f in all_faculties:
        if f.openalex_id and f.openalex_id != "not_indexed" and f.openalex_id.strip():
            clean_oa = f.openalex_id.replace("https://openalex.org/", "").strip()
            oa_groups[(f.university_th, clean_oa)].append(f)

    dup_oa = {k: v for k, v in oa_groups.items() if len(v) > 1}
    print(f"\nRemaining intra-university duplicate OpenAlex clusters: {len(dup_oa)}")

    merge_snapshot = []
    total_merged_donors = 0

    for (univ, oa_id), cluster in dup_oa.items():
        # Sort by score descending
        cluster.sort(key=score_faculty, reverse=True)
        primary = cluster[0]
        donors = cluster[1:]

        for donor in donors:
            total_merged_donors += 1
            merge_record = {
                "univ": univ,
                "oa_id": oa_id,
                "primary_id": primary.id,
                "primary_name": primary.full_name_th,
                "donor_id": donor.id,
                "donor_name": donor.full_name_th,
                "donor_metrics": {
                    "citations": donor.total_citations,
                    "h_index": donor.h_index,
                    "pubs": donor.total_publications_count
                }
            }
            merge_snapshot.append(merge_record)

            # Metric preservation
            primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
            primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
            primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
            primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
            primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

            # Preserve missing fields
            if not primary.email and donor.email:
                primary.email = donor.email
            if not primary.image_url and donor.image_url:
                primary.image_url = donor.image_url
            if not primary.profile_url and donor.profile_url:
                primary.profile_url = donor.profile_url
            if not primary.department_th and donor.department_th:
                primary.department_th = donor.department_th
            if not primary.first_name and donor.first_name:
                primary.first_name = donor.first_name
            if not primary.last_name and donor.last_name:
                primary.last_name = donor.last_name

            # Union research interests
            p_interests = list(primary.research_interests or [])
            d_interests = list(donor.research_interests or [])
            seen_interests = set(p_interests)
            for interest in d_interests:
                if interest not in seen_interests:
                    p_interests.append(interest)
                    seen_interests.add(interest)
            primary.research_interests = p_interests

            # Union featured publications
            p_pubs = list(primary.featured_publications or [])
            d_pubs = list(donor.featured_publications or [])
            seen_titles = {
                (p.get("title", "").lower().strip() if isinstance(p, dict) else str(p).lower().strip())
                for p in p_pubs
            }
            for pub in d_pubs:
                pub_title = pub.get("title", "").lower().strip() if isinstance(pub, dict) else str(pub).lower().strip()
                if pub_title and pub_title not in seen_titles:
                    p_pubs.append(pub)
                    seen_titles.add(pub_title)
            primary.featured_publications = p_pubs

            # Re-point foreign keys in research_labs
            donor_labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).all()
            for lab in donor_labs:
                lab.lead_advisor_id = primary.id

            # Rebuild embedding text
            primary.embedding_text = build_faculty_embedding_text(primary)

            # Delete donor
            db.delete(donor)

        print(f"Merged cluster {univ} | {oa_id}: Primary {primary.id} ({primary.full_name_th}) <- {len(donors)} donors")

    db.commit()
    print(f"\nSuccessfully merged {total_merged_donors} donor records into primary records.")

    # Save merge snapshot
    merge_file = os.path.join(BACKEND_DIR, "data", "agent_states", "dedup_pass4_openalex_snapshot.json")
    with open(merge_file, "w", encoding="utf-8") as out:
        json.dump(merge_snapshot, out, ensure_ascii=False, indent=2)

    db.close()

if __name__ == "__main__":
    main()
