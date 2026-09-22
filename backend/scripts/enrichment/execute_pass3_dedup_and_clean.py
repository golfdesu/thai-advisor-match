# -*- coding: utf-8 -*-
"""
Execution of Pass 3 Deduplication & Leaked Email Disambiguation per Section 9 Invariant 10:
1. Merges the 83 verified same-person duplicate email clusters:
   - Primary retains max(citations), max(h_index), max(total_publications_count)
   - Union of featured_publications, research_interests, education
   - Fallback title, authentic Thai name, OpenAlex ID, image_url, etc.
   - Re-points research_labs.lead_advisor_id
   - Deletes donor records
2. For the remaining clusters where distinct individuals share an email due to scraping leakage:
   - Checks which person actually matches the email username
   - Retains email on the matching person
   - Clears email (email = None) on the non-matching person
   - Keeps both persons intact in the database
3. Saves complete snapshot to backend/data/agent_states/dedup_pass3_email_snapshot.json
4. Rebuilds embedding_text for all modified records
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

SNAPSHOT_PATH = os.path.join(
    BACKEND_DIR, "data", "agent_states", "dedup_pass3_email_snapshot.json"
)

GENERIC_USERS = {
    "info", "admin", "contact", "office", "dean", "sci", "dent", "med", "eng",
    "academic", "graduate", "service", "pr", "help", "hr", "reg", "library",
    "support", "webmaster", "postmaster", "director", "rector", "secretary"
}

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

RE_EN_PREFIX = re.compile(
    r"^(?:Dr\.?|Dr\b|Prof\.?|Prof\b|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Lecturer|Mr\.?|Mr\b|Mrs\.?|Mrs\b|Ms\.?|Ms\b|อ\.|ผศ\.|รศ\.|ศ\.)\s*",
    re.IGNORECASE
)

def get_bare_thai(name):
    if not name: return ""
    m = RE_TITLE.match(name)
    b = name[m.end():].strip() if m else name.strip()
    return re.sub(r"\s+", " ", b)

def are_same_person(f1, f2, email):
    oa1 = (f1.openalex_id or "").replace("https://openalex.org/", "").strip()
    oa2 = (f2.openalex_id or "").replace("https://openalex.org/", "").strip()
    if oa1 and oa2 and oa1 != "not_indexed" and oa2 != "not_indexed" and oa1 == oa2:
        return True

    t1 = get_bare_thai(f1.full_name_th)
    t2 = get_bare_thai(f2.full_name_th)
    has_th1 = bool(re.search(r"[฀-๿]", t1))
    has_th2 = bool(re.search(r"[฀-๿]", t2))

    if has_th1 and has_th2:
        ratio = fuzz.token_sort_ratio(t1, t2)
        if ratio >= 60:
            return True
        w1 = t1.split()
        w2 = t2.split()
        if w1 and w2:
            fn_sim = fuzz.ratio(w1[0], w2[0])
            if fn_sim >= 80:
                if len(w1) > 1 and len(w2) > 1:
                    ln_sim = fuzz.ratio(w1[1], w2[1])
                    if ln_sim >= 60:
                        return True
                    else:
                        return False
        return False

    u = email.split("@")[0].lower()
    clean_en_tokens = re.sub(r"[^a-zA-Z\s]", " ", f"{f1.first_name} {f1.last_name} {f2.first_name} {f2.last_name}").lower().split()
    non_th = t1 if not has_th1 else t2
    non_th_clean = RE_EN_PREFIX.sub("", non_th).strip().lower()

    if any(fuzz.partial_ratio(tok, non_th_clean) >= 80 for tok in clean_en_tokens):
        return True
    if any(tok in non_th_clean for tok in u.split(".")):
        return True

    return False

def score_faculty(fac, email_domain):
    s = 0
    univ = (fac.university_th or "").lower()
    if "tu.ac.th" in email_domain and "ธรรมศาสตร์" in univ: s += 500
    elif "cmu.ac.th" in email_domain and "เชียงใหม่" in univ: s += 500
    elif "kmitl.ac.th" in email_domain and "ลาดกระบัง" in univ: s += 500
    elif "mfu.ac.th" in email_domain and "แม่ฟ้าหลวง" in univ: s += 500
    elif "ku.ac.th" in email_domain and "เกษตรศาสตร์" in univ: s += 500
    elif "chula.ac.th" in email_domain and "จุฬา" in univ: s += 500
    elif "mahidol.ac.th" in email_domain and "มหิดล" in univ: s += 500
    elif "nu.ac.th" in email_domain and "นเรศวร" in univ: s += 500
    elif "psu.ac.th" in email_domain and "สงขลา" in univ: s += 500

    name_th = fac.full_name_th or ""
    if re.search(r"[฀-๿]", name_th): s += 150
    if fac.academic_title_th: s += 50
    if fac.openalex_id and fac.openalex_id != "not_indexed": s += 80
    if fac.total_citations: s += min(fac.total_citations, 50)
    if fac.featured_publications: s += len(fac.featured_publications) * 2
    if fac.department_th and fac.department_th not in ["None", "-", ""]: s += 20
    if fac.image_url: s += 10
    return s

def execute_pass3():
    db = SessionLocal()
    try:
        faculties = db.query(FacultyDB).options(defer(FacultyDB.embedding)).all()
        print(f"Loaded {len(faculties)} faculty records for Pass 3.")

        email_groups = defaultdict(list)
        for f in faculties:
            if f.email and "@" in f.email:
                em = f.email.strip().lower()
                u = em.split("@")[0]
                if u not in GENERIC_USERS and len(u) >= 3:
                    email_groups[em].append(f)

        dup_emails = {k: v for k, v in email_groups.items() if len(v) > 1}
        print(f"Found {len(dup_emails)} duplicate email clusters.")

        safe_clusters = []
        unsafe_clusters = []

        for em, cluster in dup_emails.items():
            all_same = True
            f_lead = cluster[0]
            for f_other in cluster[1:]:
                if not are_same_person(f_lead, f_other, em):
                    all_same = False
                    break
            if all_same:
                safe_clusters.append((em, cluster))
            else:
                unsafe_clusters.append((em, cluster))

        print(f"Safe verified merges (same person): {len(safe_clusters)}")
        print(f"Unsafe (different persons sharing email): {len(unsafe_clusters)}")

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "pass": "Pass 3: Verified Email Deduplication & Leak Clean",
            "merges": [],
            "cleared_emails": []
        }

        total_merged_donors = 0
        donor_ids_to_delete = []

        # 1. Execute safe merges
        for em, cluster in safe_clusters:
            domain = em.split("@")[-1]
            sorted_cluster = sorted(cluster, key=lambda f: score_faculty(f, domain), reverse=True)
            primary = sorted_cluster[0]
            donors = sorted_cluster[1:]

            merge_entry = {
                "email": em,
                "primary_id": primary.id,
                "donor_ids": [d.id for d in donors],
                "primary_before": {
                    "id": primary.id,
                    "full_name_th": primary.full_name_th,
                    "openalex_id": primary.openalex_id,
                    "total_citations": primary.total_citations,
                    "h_index": primary.h_index,
                    "total_publications_count": primary.total_publications_count,
                    "university_th": primary.university_th,
                    "department_th": primary.department_th,
                },
                "donors_data": []
            }

            for donor in donors:
                merge_entry["donors_data"].append({
                    "id": donor.id,
                    "full_name_th": donor.full_name_th,
                    "openalex_id": donor.openalex_id,
                    "total_citations": donor.total_citations,
                    "h_index": donor.h_index,
                    "total_publications_count": donor.total_publications_count,
                    "university_th": donor.university_th,
                    "department_th": donor.department_th,
                })

                # Merge metrics
                primary.total_citations = max(primary.total_citations or 0, donor.total_citations or 0)
                primary.h_index = max(primary.h_index or 0, donor.h_index or 0)
                primary.total_publications_count = max(primary.total_publications_count or 0, donor.total_publications_count or 0)
                primary.first_author_count = max(primary.first_author_count or 0, donor.first_author_count or 0)
                primary.co_author_count = max(primary.co_author_count or 0, donor.co_author_count or 0)

                # Merge identifiers & contact
                if (not primary.openalex_id or primary.openalex_id == "not_indexed") and (donor.openalex_id and donor.openalex_id != "not_indexed"):
                    primary.openalex_id = donor.openalex_id
                if not primary.academic_title_th and donor.academic_title_th:
                    primary.academic_title_th = donor.academic_title_th

                prim_has_thai = bool(re.search(r"[฀-๿]", primary.full_name_th or ""))
                donor_has_thai = bool(re.search(r"[฀-๿]", donor.full_name_th or ""))
                if not prim_has_thai and donor_has_thai:
                    primary.full_name_th = donor.full_name_th

                if not primary.image_url and donor.image_url:
                    primary.image_url = donor.image_url
                if not primary.profile_url and donor.profile_url:
                    primary.profile_url = donor.profile_url
                if not primary.scholar_url and donor.scholar_url:
                    primary.scholar_url = donor.scholar_url
                if not primary.first_name and donor.first_name:
                    primary.first_name = donor.first_name
                if not primary.last_name and donor.last_name:
                    primary.last_name = donor.last_name
                if (not primary.department_th or primary.department_th in ["None", "-", ""]) and donor.department_th:
                    primary.department_th = donor.department_th

                # Merge lists
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

                prim_ints = primary.research_interests or []
                donor_ints = donor.research_interests or []
                seen_ints = set(prim_ints)
                for i in donor_ints:
                    if i and i not in seen_ints:
                        prim_ints.append(i)
                        seen_ints.add(i)
                primary.research_interests = prim_ints

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

        # 2. Clear leaked emails on distinct individuals
        cleared_count = 0
        for em, cluster in unsafe_clusters:
            u = em.split("@")[0].lower()
            parts = u.split(".")

            # Find which record best matches the username
            best_f = None
            best_score = -1
            for f in cluster:
                name_parts = re.sub(r"[^a-zA-Z\s]", " ", f"{f.first_name} {f.last_name} {f.full_name_th}").lower().split()
                # Check match against username parts
                score = 0
                for p in parts:
                    if any(p in np or fuzz.partial_ratio(p, np) >= 80 for np in name_parts):
                        score += 10
                if score > best_score:
                    best_score = score
                    best_f = f

            # Keep email on best_f, clear from others
            if best_f and best_score > 0:
                for f in cluster:
                    if f.id != best_f.id:
                        snapshot["cleared_emails"].append({
                            "id": f.id,
                            "full_name_th": f.full_name_th,
                            "email_cleared": f.email,
                            "kept_on_id": best_f.id,
                            "kept_on_name": best_f.full_name_th
                        })
                        f.email = None
                        f.embedding_text = build_faculty_embedding_text(f)
                        cleared_count += 1

        # Save snapshot
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"Saved snapshot to {SNAPSHOT_PATH}")

        # Delete donor records
        print(f"Deleting {len(donor_ids_to_delete)} donor records...")
        batch_size = 100
        for i in range(0, len(donor_ids_to_delete), batch_size):
            chunk = donor_ids_to_delete[i:i + batch_size]
            db.query(FacultyDB).filter(FacultyDB.id.in_(chunk)).delete(synchronize_session=False)

        db.commit()
        print(f"Pass 3 successfully committed: {total_merged_donors} duplicate records merged, {cleared_count} leaked emails cleared.")

    except Exception as e:
        db.rollback()
        print(f"Error during Pass 3: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    execute_pass3()
