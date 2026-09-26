# -*- coding: utf-8 -*-
"""
Reconciliation and Ingestion Engine for Rounds 11-20 (SKILL.state Engine)
Enriches existing profiles and inserts new authentic faculty members
with 768-dimensional embeddings and 6D zero-defect compliance.
"""
import os
import sys
import json
import re
import uuid
from pathlib import Path

# Adaptive path resolution
BACKEND_DIR = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 2 else Path(__file__).resolve().parents[0]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TITLE_PREFIX_PATTERN = re.compile(
    r'^(?:ศ\.เกียรติคุณ\s*(?:นายแพทย์|นพ\.)?|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|ทพญ\.|ทพ\.|นพ\.|พญ\.|นายแพทย์|นางสาว|นาง|นาย)\s*'
)

def run_ingestion():
    from app.core.database import SessionLocal
    from app.models.db_models import FacultyDB
    from app.core.embedding_service import embedding_service
    from app.core.embedding_text import build_faculty_embedding_text

    json_path = BACKEND_DIR / "data" / "agent_states" / "rounds11_20_merged_extracted.json"
    if not json_path.exists():
        print(f"Error: {json_path} does not exist!")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        incoming_records = json.load(f)

    print(f"Loaded {len(incoming_records)} deduplicated authentic records from Rounds 11-20.")

    db = SessionLocal()

    try:
        # Load all existing faculty from target universities
        target_univs = [
            "มหาวิทยาลัยศิลปากร",
            "มหาวิทยาลัยธรรมศาสตร์",
            "มหาวิทยาลัยเชียงใหม่",
            "มหาวิทยาลัยขอนแก่น",
            "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
            "มหาวิทยาลัยสงขลานครินทร์",
        ]
        existing_rows = db.query(FacultyDB).filter(FacultyDB.university_th.in_(target_univs)).all()
        print(f"Loaded {len(existing_rows)} existing faculty records from target universities for reconciliation.")

        by_email = {}
        by_th_name = {}
        by_en_name = {}

        for ex in existing_rows:
            if ex.email:
                by_email[ex.email.lower()] = ex
            if ex.full_name_th:
                clean_th = TITLE_PREFIX_PATTERN.sub('', ex.full_name_th).strip()
                if clean_th:
                    by_th_name[clean_th] = ex
            if ex.first_name and ex.last_name:
                key_en = f"{ex.first_name.lower()} {ex.last_name.lower()}".strip()
                if len(key_en.split()) > 1:
                    by_en_name[key_en] = ex

        enriched_count = 0
        inserted_count = 0
        embedded_count = 0

        for r in incoming_records:
            matched = None
            em = (r.get("email") or "").strip().lower()
            name_th = (r.get("full_name_th") or "").strip()
            clean_th = TITLE_PREFIX_PATTERN.sub('', name_th).strip()
            fn_en = (r.get("first_name") or "").strip().lower()
            ln_en = (r.get("last_name") or "").strip().lower()
            name_en = f"{fn_en} {ln_en}".strip()

            # Generic institutional emails shouldn't match distinct individuals
            is_generic = any(em.startswith(g) for g in ["info@", "contact@", "admin@", "office@", "deans@", "fms-", "sgs@"])

            if em and not is_generic and em in by_email:
                matched = by_email[em]
            elif clean_th and clean_th in by_th_name:
                matched = by_th_name[clean_th]
            elif name_en and len(name_en.split()) > 1 and name_en in by_en_name:
                matched = by_en_name[name_en]

            if matched:
                # Enrich existing record
                changed = False
                if not matched.email and em and not is_generic:
                    matched.email = em
                    changed = True
                if not matched.profile_url and r.get("profile_url"):
                    matched.profile_url = r["profile_url"]
                    changed = True

                # Merge education
                if not matched.education and r.get("education"):
                    matched.education = r["education"]
                    changed = True

                # Merge research interests
                curr_interests = list(matched.research_interests or [])
                new_interests = r.get("research_interests") or []
                if new_interests:
                    combined_int = list(dict.fromkeys(curr_interests + new_interests))
                    if len(combined_int) > len(curr_interests):
                        matched.research_interests = combined_int
                        changed = True

                # Check if embedding is missing
                if matched.embedding is None:
                    emb_text = build_faculty_embedding_text(matched)
                    vec = embedding_service.get_embedding(emb_text)
                    if vec:
                        matched.embedding = vec
                        embedded_count += 1
                        changed = True

                if changed:
                    enriched_count += 1
            else:
                # Insert brand new authentic faculty profile
                new_id = r.get("id") or f"fac_{uuid.uuid4().hex[:12]}"
                # Double check ID uniqueness
                if db.query(FacultyDB).filter(FacultyDB.id == new_id).first():
                    new_id = f"fac_{uuid.uuid4().hex[:12]}"

                # Clean fields
                fn = r.get("first_name", "").strip()
                ln = r.get("last_name", "").strip()
                full_en = f"{fn} {ln}".strip()
                full_th = r.get("full_name_th", "").strip()
                univ_th = r.get("university_th", "").strip()
                univ_en = r.get("university", "").strip()
                fac_th = r.get("faculty_th", "").strip()
                fac_en = r.get("faculty", "").strip()
                dept_th = r.get("department_th", "").strip() or fac_th
                dept_en = r.get("department", "").strip() or fac_en

                new_fac = FacultyDB(
                    id=new_id,
                    university_th=univ_th,
                    university=univ_en,
                    faculty_th=fac_th,
                    faculty=fac_en,
                    department_th=dept_th,
                    department=dept_en,
                    academic_title_th=r.get("academic_title_th", "อ."),
                    first_name=fn,
                    last_name=ln,
                    full_name_th=full_th,
                    role=r.get("role", "อาจารย์ประจำ"),
                    email=em if (em and not is_generic) else None,
                    image_url=r.get("image_url", ""),
                    profile_url=r.get("profile_url", ""),
                    education=r.get("education", []),
                    research_interests=r.get("research_interests", []),
                    featured_publications=r.get("featured_publications", []),
                    scholar_url=r.get("scholar_url", ""),
                    total_citations=r.get("total_citations", 0),
                    h_index=r.get("h_index", 0),
                    total_publications_count=r.get("total_publications_count", 0),
                    openalex_id=r.get("openalex_id", "not_indexed"),
                )

                # Compute 768-dim embedding
                emb_text = build_faculty_embedding_text(new_fac)
                new_fac.embedding_text = emb_text
                try:
                    vec = embedding_service.get_embedding(emb_text)
                    if vec:
                        new_fac.embedding = vec
                        embedded_count += 1
                    else:
                        new_fac.embedding = [0.0] * 768
                except Exception as e:
                    print(f"Warning: embedding fallback for {full_en}: {e}")
                    new_fac.embedding = [0.0] * 768

                db.add(new_fac)
                inserted_count += 1

                # Update local lookup sets
                if em and not is_generic:
                    by_email[em] = new_fac
                if clean_th:
                    by_th_name[clean_th] = new_fac
                if name_en:
                    by_en_name[name_en] = new_fac

        db.commit()
        print("\n=================================================")
        print("🎉 INGESTION & RECONCILIATION SUMMARY (ROUNDS 11-20)")
        print("=================================================")
        print(f"  - Total Evaluated: {len(incoming_records)}")
        print(f"  - Existing Profiles Enriched: {enriched_count}")
        print(f"  - Brand New Profiles Inserted: {inserted_count}")
        print(f"  - Embeddings Generated/Updated: {embedded_count}")
        print("=================================================")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
