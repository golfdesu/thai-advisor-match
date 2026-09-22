# -*- coding: utf-8 -*-
"""
Execution of Pass 1 Deduplication (Thai Name + University) per Section 9 Invariant 10:
- Groups records by (university_th, normalized_thai_name_bare).
- Selects the best primary record based on email, openalex_id, title, department, citations.
- Merges all donor fields into primary:
  - max(total_citations)
  - max(h_index)
  - max(works_count)
  - union of featured_publications
  - union of research_interests
  - union of education
  - openalex_id, email, image_url, profile_url fallback
- Re-points any research_labs.lead_advisor_id from donor.id to primary.id
- Saves snapshot to backend/data/agent_states/dedup_pass1_thai_name_snapshot.json
- Deletes donor records
- Rebuilds primary.embedding_text
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
from sqlalchemy.orm import defer

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "dedup_pass1_thai_name_snapshot.json"
)

RE_TITLE = re.compile(
    r"^(ศ\.เชี่ยวชาญพิเศษ\s+ดร\.\s+นพ\.|ศ\.คลินิก\s+ดร\.\s+สพ\.ญ\.|ศ\.คลินิก\s+ทพญ\.|"
    r"ศ\.ดร\.นพ\.|ศ\.ดร\.พญ\.|ศ\.ดร\.ภก\.|ศ\.ดร\.ภญ\.|ศ\.ดร\.น\.สพ\.|ศ\.ดร\.สพ\.ญ\.|"
    r"รศ\.ดร\.นพ\.|รศ\.ดร\.พญ\.|รศ\.ดร\.ภก\.|รศ\.ดร\.ภญ\.|รศ\.ดร\.น\.สพ\.|รศ\.ดร\.สพ\.ญ\.|รศ\.ดร\.ทพ\.|รศ\.ดร\.ทพญ\.|"
    r"ผศ\.ดร\.นพ\.|ผศ\.ดร\.พญ\.|ผศ\.ดร\.ภก\.|ผศ\.ดร\.ภญ\.|ผศ\.ดร\.น\.สพ\.|ผศ\.ดร\.สพ\.ญ\.|ผศ\.ดร\.ทพ\.|ผศ\.ดร\.ทพญ\.|"
    r"ศ\.นพ\.|ศ\.พญ\.|ศ\.ภก\.|ศ\.ภญ\.|ศ\.น\.สพ\.|ศ\.สพ\.ญ\.|ศ\.ทพ\.|ศ\.ทพญ\.|"
    r"รศ\.นพ\.|รศ\.พญ\.|รศ\.ภก\.|รศ\.ภญ\.|รศ\.น\.สพ\.|รศ\.สพ\.ญ\.|รศ\.ทพ\.|รศ\.ทพญ\.|"
    r"ผศ\.นพ\.|ผศ\.พญ\.|ผศ\.ภก\.|ผศ\.ภญ\.|ผศ\.น\.สพ\.|ผศ\.สพ\.ญ\.|ผศ\.ทพ\.|ผศ\.ทพญ\.|"
    r"อ\.นพ\.|อ\.พญ\.|อ\.ภก\.|อ\.ภญ\.|อ\.น\.สพ\.|อ\.สพ\.ญ\.|อ\.ทพ\.|อ\.ทพญ\.|"
    r"ศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+พญ\.|ผศ\.พิเศษ\s+นพ\.|"
    r"ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|"
    r"ศ\.คลินิก|รศ\.คลินิก|ผศ\.คลินิก|ศ\.\(พิเศษ\)|รศ\.\(พิเศษ\)|ผศ\.\(พิเศษ\)|"
    r"ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|น\.สพ\.|สพ\.ญ\.)\s*"
)

def score_faculty(fac):
    s = 0
    if fac.email and len(fac.email) > 5: s += 100
    if fac.openalex_id and fac.openalex_id != "not_indexed": s += 50
    if fac.academic_title_th: s += 20
    if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 15
    if fac.total_citations: s += min(fac.total_citations, 50)
    if fac.featured_publications: s += len(fac.featured_publications) * 2
    if fac.image_url: s += 10
    return s

def execute_pass1_dedup():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
        print(f"Loaded {len(faculties)} faculty records for Pass 1 deduplication.")

        groups = defaultdict(list)
        for f in faculties:
            name_th = (f.full_name_th or "").strip()
            if re.search(r"[฀-๿]", name_th):
                m = RE_TITLE.match(name_th)
                bare_th = name_th[m.end():].strip() if m else name_th
                bare_th = re.sub(r"\s+", " ", bare_th)
                words = bare_th.split()
                if len(words) >= 2 and len(bare_th) >= 6:
                    groups[(f.university_th, bare_th)].append(f)

        dup_clusters = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"Found {len(dup_clusters)} duplicate clusters across universities.")

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "pass": "Pass 1: Thai Name + University",
            "merges": []
        }

        total_merged_donors = 0
        donor_ids_to_delete = []

        for (univ, bare_name), cluster in dup_clusters.items():
            # Sort cluster to select best primary
            sorted_cluster = sorted(cluster, key=score_faculty, reverse=True)
            primary = sorted_cluster[0]
            donors = sorted_cluster[1:]

            merge_entry = {
                "university_th": univ,
                "bare_name": bare_name,
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
                    "faculty_th": primary.faculty_th,
                    "department_th": primary.department_th,
                },
                "donors_data": []
            }

            for donor in donors:
                merge_entry["donors_data"].append({
                    "id": donor.id,
                    "full_name_th": donor.full_name_th,
                    "email": donor.email,
                    "openalex_id": donor.openalex_id,
                    "total_citations": donor.total_citations,
                    "h_index": donor.h_index,
                    "total_publications_count": donor.total_publications_count,
                    "faculty_th": donor.faculty_th,
                    "department_th": donor.department_th,
                })

                # Merge metrics
                primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
                primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
                primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
                primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
                primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

                # Merge identifiers & contact
                if not primary.email and donor.email:
                    primary.email = donor.email
                if (not primary.openalex_id or primary.openalex_id == "not_indexed") and (donor.openalex_id and donor.openalex_id != "not_indexed"):
                    primary.openalex_id = donor.openalex_id
                if not primary.scholar_url and donor.scholar_url:
                    primary.scholar_url = donor.scholar_url
                if not primary.academic_title_th and donor.academic_title_th:
                    primary.academic_title_th = donor.academic_title_th
                if not primary.image_url and donor.image_url:
                    primary.image_url = donor.image_url
                if not primary.profile_url and donor.profile_url:
                    primary.profile_url = donor.profile_url
                if not primary.first_name and donor.first_name:
                    primary.first_name = donor.first_name
                if not primary.last_name and donor.last_name:
                    primary.last_name = donor.last_name
                if (not primary.department_th or primary.department_th in ["None", "-", ""]) and donor.department_th:
                    primary.department_th = donor.department_th

                # Merge lists
                # Publications
                prim_pubs = primary.featured_publications or []
                donor_pubs = donor.featured_publications or []
                seen_titles = {p.get("title", "").strip().lower() for p in prim_pubs if isinstance(p, dict)}
                for p in donor_pubs:
                    if isinstance(p, dict):
                        t = p.get("title", "").strip().lower()
                        if t and t not in seen_titles:
                            prim_pubs.append(p)
                            seen_titles.add(t)
                primary.featured_publications = prim_pubs

                # Research interests
                prim_ints = primary.research_interests or []
                donor_ints = donor.research_interests or []
                seen_ints = set(prim_ints)
                for i in donor_ints:
                    if i and i not in seen_ints:
                        prim_ints.append(i)
                        seen_ints.add(i)
                primary.research_interests = prim_ints

                # Education
                prim_edu = primary.education or []
                donor_edu = donor.education or []
                seen_edu = set(prim_edu)
                for e in donor_edu:
                    if e and e not in seen_edu:
                        prim_edu.append(e)
                        seen_edu.add(e)
                primary.education = prim_edu

                # Re-point research_labs foreign key
                labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).all()
                for l in labs:
                    l.lead_advisor_id = primary.id

                donor_ids_to_delete.append(donor.id)
                total_merged_donors += 1

            primary.embedding_text = build_faculty_embedding_text(primary)
            snapshot["merges"].append(merge_entry)

        # Save snapshot
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot to {SNAPSHOT_PATH}")

        # Delete donor records in batches
        print(f"Deleting {len(donor_ids_to_delete)} donor records...")
        batch_size = 100
        for i in range(0, len(donor_ids_to_delete), batch_size):
            chunk = donor_ids_to_delete[i:i + batch_size]
            db.query(FacultyDB).filter(FacultyDB.id.in_(chunk)).delete(synchronize_session=False)

        db.commit()
        print(f"Pass 1 Deduplication successfully committed: {total_merged_donors} duplicate records merged and cleaned.")

    except Exception as e:
        db.rollback()
        print(f"Error during Pass 1 deduplication: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_pass1_dedup()
