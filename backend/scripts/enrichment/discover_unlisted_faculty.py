# -*- coding: utf-8 -*-
"""
SKILL.state Stage 6 Pipeline: Unlisted & New Faculty Discovery Workflow
Discovers and ingests unlisted faculty members missing due to 6-24 months of directory lag
via OpenAlex recent publication footprints (2024-2026), institutional affiliation mining,
and automated Thai nomenclature resolution.
Local-first PostgreSQL commit (localhost:5432).
"""
import os
import sys
import json
import re
import time
from datetime import datetime
import urllib.request
import urllib.parse
from collections import defaultdict

# Runbook Guardrail 2: Pytest-Safe Stdout Reconfiguration
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.config import settings
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService

from google import genai

CHECKPOINT_DIR = os.path.join(BACKEND_DIR, "data", "agent_states")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

USER_AGENT = "mailto:advisor_match_academic_discovery@example.com"

TARGET_UNIVERSITIES = [
    {
        "name_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "name_en": "Chulalongkorn University",
        "openalex_id": "I158708052",
        "id_prefix": "cu_oa_disc",
        "search_term": "chulalongkorn"
    },
    {
        "name_th": "มหาวิทยาลัยเชียงใหม่",
        "name_en": "Chiang Mai University",
        "openalex_id": "I48076826",
        "id_prefix": "cmu_oa_disc",
        "search_term": "chiang mai"
    }
]

def fetch_json(url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries - 1:
                print(f"  [Fetch Failed] {url} -> {e}")
                return None
            time.sleep(1.5)
    return None

def fetch_top_works(author_id: str, max_works: int = 5) -> list:
    url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=cited_by_count:desc&per_page={max_works}"
    data = fetch_json(url)
    if not data:
        return []

    pubs = []
    for r in data.get("results", []):
        title = (r.get("title") or "").strip()
        if not title:
            continue
        year = r.get("publication_year")
        venue = None
        host_venue = r.get("primary_location", {}).get("source") or {}
        if host_venue:
            venue = host_venue.get("display_name")
        cites = r.get("cited_by_count") or 0
        doi = r.get("doi") or r.get("id")

        pubs.append({
            "title": title,
            "year": year,
            "venue": venue or "Journal/Conference",
            "citation_count": cites,
            "url": doi
        })
    return pubs

def resolve_thai_nomenclature(client, candidates: list) -> dict:
    """
    Resolves Thai academic title, Thai full name, faculty, and department for discovered faculty.
    """
    if not candidates:
        return {}

    results = {}
    BATCH_SIZE = 25
    for i in range(0, len(candidates), BATCH_SIZE):
        chunk = candidates[i:i+BATCH_SIZE]
        prompt_input = []
        for c in chunk:
            prompt_input.append({
                "id": c["id"],
                "name_en": c["name_en"],
                "university_th": c["university_th"],
                "dept_raw": c["dept_raw"],
                "topics": c["topics"],
                "h_index": c["h_index"]
            })

        prompt = """You are an expert Thai academic registrar and nomenclature specialist.
Given a list of university faculty members with their English names, university, raw department, research topics, and h-index, provide their authentic Thai academic title, Thai full name, Thai faculty, and Thai department.

Rules:
1. Thai Academic Titles:
   - If medical topics/MD/Medicine/Surgery/Pediatrics/Radiology/Clinical: use 'ศ.นพ.', 'รศ.นพ.', 'ผศ.นพ.', 'อ.นพ.' (male) or 'ศ.พญ.', 'รศ.พญ.', 'ผศ.พญ.', 'อ.พญ.' (female). If h_index >= 35, likely 'ศ.' or 'รศ.'.
   - If non-medical doctoral researcher: use 'ศ.ดร.', 'รศ.ดร.', 'ผศ.ดร.', or 'อ.ดร.'. If h_index >= 25, likely 'ศ.ดร.' or 'รศ.ดร.'.
   - For foreign researchers whose names are English/foreign, use standard academic prefix like 'ศ.ดร.', 'รศ.ดร.', 'ผศ.ดร.', 'อ.ดร.' or keep English name with Thai title e.g. 'รศ.ดร. Jiaqian Qin', 'อ.ดร. Sudarshan Singh'.
2. Return ONLY a valid JSON object mapping each ID to:
   {
     "academic_title_th": "Title",
     "first_name_th": "ชื่อ",
     "last_name_th": "นามสกุล",
     "full_name_th": "Title ชื่อ นามสกุล",
     "faculty_th": "คณะ...",
     "department_th": "ภาควิชา...",
     "confidence": 0.95,
     "confidence_reason": "Justification for confidence level"
   }
3. No markdown backticks, no explanatory text.

Input:
""" + json.dumps(prompt_input, ensure_ascii=False, indent=2)

        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt
                )
                text = resp.text.strip()
                text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
                text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
                data = json.loads(text)
                results.update(data)
                print(f"  [Gemini Resolution] Successfully resolved chunk {i+1} to {min(i+BATCH_SIZE, len(candidates))}")
                break
            except Exception as e:
                print(f"  [Gemini Resolution Attempt {attempt+1} Failed]: {e}")
                time.sleep(2)

    return results

def evaluate_discovery_confidence(scholar: dict, res_info: dict, pubs: list) -> tuple[float, list[str]]:
    """
    Evaluates confidence score (0.0 to 1.0) and quarantine flags for unlisted faculty candidates.
    TypeSafe Quality Pattern: Records with score < 0.85 are isolated to quarantine state
    instead of polluting the authoritative database.
    """
    score = 0.50  # Base prior
    flags = []

    # 1. Academic metrics verification
    h_idx = scholar.get("h_index", 0)
    cites = scholar.get("total_citations", 0)
    works = scholar.get("works_count", 0)

    if h_idx >= 15 or cites >= 500:
        score += 0.20
    elif h_idx >= 5 or cites >= 100:
        score += 0.15
    elif h_idx >= 3:
        score += 0.05
    else:
        flags.append("marginal_h_index")
        score -= 0.15

    if works >= 10:
        score += 0.05
    else:
        flags.append("low_works_count")

    # 2. Institutional affiliation & department specificity
    raw_dept = scholar.get("dept_raw", "")
    if any(k in raw_dept.lower() for k in ["department", "faculty", "division", "center", "ภาควิชา", "คณะ"]):
        score += 0.10
    else:
        flags.append("non_specific_department")
        score -= 0.05

    # 3. Nomenclature authenticity
    title_th = res_info.get("academic_title_th", "").strip()
    valid_titles = {"ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.นพ.", "รศ.นพ.", "ผศ.นพ.", "อ.นพ.", "ศ.พญ.", "รศ.พญ.", "ผศ.พญ.", "อ.พญ.", "ดร.", "อ."}
    if title_th in valid_titles:
        score += 0.10
    else:
        flags.append("non_standard_academic_title")
        score -= 0.15

    fac_th = res_info.get("faculty_th", "").strip()
    if fac_th.startswith(("คณะ", "สำนักวิชา", "วิทยาลัย", "สถาบัน")):
        score += 0.05
    else:
        flags.append("unverified_faculty_prefix")
        score -= 0.10

    # 4. Publication evidence
    if len(pubs) >= 3:
        score += 0.05
    elif len(pubs) == 0:
        flags.append("zero_publication_evidence")
        score -= 0.20

    # 5. LLM self-assessed confidence
    model_conf = res_info.get("confidence")
    if isinstance(model_conf, (int, float)):
        if model_conf < 0.80:
            flags.append(f"low_model_confidence_{model_conf:.2f}")
            score -= 0.15
        elif model_conf >= 0.90:
            score += 0.05

    score = max(0.0, min(1.0, round(score, 2)))
    return score, flags

def main():
    print("=================================================================")
    print("🚀 STAGE 6: UNLISTED & NEW FACULTY DISCOVERY PIPELINE")
    print("=================================================================")

    db = SessionLocal()
    embedder = EmbeddingService()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        # 1. Load existing faculty names to compute symmetric difference
        existing_names_by_univ = defaultdict(set)
        all_faculties = db.query(FacultyDB).all()
        for f in all_faculties:
            fn = (f.first_name or "").strip().lower()
            ln = (f.last_name or "").strip().lower()
            if fn and ln:
                existing_names_by_univ[f.university_th].add(f"{fn} {ln}")

        qualified_records = []
        quarantined_records = []

        for univ in TARGET_UNIVERSITIES:
            univ_th = univ["name_th"]
            univ_en = univ["name_en"]
            inst_id = univ["openalex_id"]
            prefix = univ["id_prefix"]
            search_term = univ["search_term"]

            print(f"\n--- Harvesting Footprint 3 for {univ_th} ({univ_en}) ---")
            existing_names = existing_names_by_univ[univ_th]
            print(f"  Existing verified faculty in DB: {len(existing_names)}")

            # Fetch recent works (2024-2026)
            works_url = f"https://api.openalex.org/works?filter=institutions.id:{inst_id},publication_year:2024|2025|2026&sort=cited_by_count:desc&per_page=100"
            works_data = fetch_json(works_url)
            if not works_data:
                print("  Failed to fetch works data, skipping...")
                continue

            candidates_map = {}
            for w in works_data.get("results", []):
                for a in w.get("authorships", []):
                    author = a.get("author", {})
                    aid = author.get("id")
                    if not aid:
                        continue
                    m = re.search(r"(A\d+)", aid)
                    if not m:
                        continue
                    short_aid = m.group(1)

                    raw_name = author.get("display_name", "").strip()
                    if not raw_name:
                        continue

                    # Clean Latin Name (Runbook Stage 1.1)
                    clean_name = re.sub(
                        r"^(?:Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Dr\.?|Mr\.?|Ms\.?|Mrs\.?)\s+",
                        "",
                        raw_name,
                        flags=re.IGNORECASE
                    ).strip()
                    clean_name = re.sub(r",\s*(?:MD|Ph\.?D|FACS|FRCS).*$", "", clean_name, flags=re.IGNORECASE).strip()
                    parts = clean_name.split()
                    if len(parts) < 2:
                        continue
                    fn = parts[0].strip().title()
                    ln = " ".join(parts[1:]).strip().title()

                    if not re.match(r"^[a-zA-Z\s\-\.\']+$", f"{fn} {ln}"):
                        continue

                    norm_name = f"{fn.lower()} {ln.lower()}"

                    if norm_name in existing_names:
                        continue

                    # Check Institutional Affiliation
                    raw_affils = a.get("raw_affiliation_strings", [])
                    univ_affil = False
                    dept_str = None
                    for aff in raw_affils:
                        if search_term in aff.lower():
                            univ_affil = True
                            dm = re.search(r"(?:Department|Faculty|Division|Center) of ([^,]+)", aff, re.IGNORECASE)
                            if dm:
                                dept_str = dm.group(0).strip()
                            else:
                                dept_str = aff.strip()
                            break

                    if not univ_affil:
                        continue

                    if short_aid not in candidates_map:
                        candidates_map[short_aid] = {
                            "aid": short_aid,
                            "first_name_en": fn,
                            "last_name_en": ln,
                            "name_en": f"{fn} {ln}",
                            "dept_raw": dept_str or univ_en,
                            "sample_work": w.get("title")
                        }

            print(f"  Harvested {len(candidates_map)} potential unlisted author candidates.")

            # Filter candidates against author profile criteria
            qualified_authors = []
            for aid, cand in candidates_map.items():
                author_url = f"https://api.openalex.org/authors/{aid}"
                author_data = fetch_json(author_url)
                if not author_data:
                    continue

                last_insts = [i.get("display_name", "") for i in author_data.get("last_known_institutions", [])]
                is_affiliated = any(search_term in inst.lower() for inst in last_insts)
                h_index = author_data.get("summary_stats", {}).get("h_index", 0)
                works_cnt = author_data.get("works_count", 0)
                cites = author_data.get("cited_by_count", 0)

                # Qualification filter: real academic researcher with proven track record
                if is_affiliated and h_index >= 3 and works_cnt >= 8:
                    topics = [t.get("display_name") for t in author_data.get("topics", [])[:3]]
                    qualified_authors.append({
                        "id": aid,
                        "first_name_en": cand["first_name_en"],
                        "last_name_en": cand["last_name_en"],
                        "name_en": cand["name_en"],
                        "university_th": univ_th,
                        "dept_raw": cand["dept_raw"],
                        "works_count": works_cnt,
                        "total_citations": cites,
                        "h_index": h_index,
                        "topics": topics,
                        "sample_work": cand["sample_work"]
                    })

            print(f"  Qualified High-Impact Unlisted Faculty: {len(qualified_authors)}")

            # Limit per university wave to top 15 most prominent scholars
            qualified_authors.sort(key=lambda x: (x["h_index"], x["total_citations"]), reverse=True)
            selected_cohort = qualified_authors[:15]

            # Resolve Thai nomenclature via Gemini
            print(f"  Resolving Thai nomenclature for {len(selected_cohort)} scholars...")
            resolved_dict = resolve_thai_nomenclature(client, selected_cohort)

            # Fetch top cited publications, evaluate confidence & assemble records
            for idx, scholar in enumerate(selected_cohort):
                aid = scholar["id"]
                fn_en = scholar["first_name_en"]
                ln_en = scholar["last_name_en"]

                res_info = resolved_dict.get(aid, {})
                title_th = (res_info.get("academic_title_th") or "ดร.").strip()
                fn_th = (res_info.get("first_name_th") or fn_en).strip()
                ln_th = (res_info.get("last_name_th") or ln_en).strip()
                full_th = res_info.get("full_name_th") or f"{title_th} {fn_th} {ln_th}"
                full_th = re.sub(r"\s+", " ", full_th).strip()
                fac_th = (res_info.get("faculty_th") or "คณะวิทยาศาสตร์").strip()
                dept_th = (res_info.get("department_th") or scholar["dept_raw"]).strip()

                # Fetch publications
                pubs = fetch_top_works(aid, max_works=5)
                interests = [t for t in scholar["topics"] if t]

                # Evaluate confidence score & quarantine criteria (TypeSafe Quality Pattern)
                conf_score, q_flags = evaluate_discovery_confidence(scholar, res_info, pubs)
                is_quarantined = conf_score < 0.85

                new_record = {
                    "id": f"{prefix}_{aid.lower()}",
                    "first_name": fn_en,
                    "last_name": ln_en,
                    "academic_title_th": title_th,
                    "full_name_th": full_th,
                    "university_th": univ_th,
                    "faculty_th": fac_th,
                    "department_th": dept_th,
                    "total_citations": scholar["total_citations"],
                    "h_index": scholar["h_index"],
                    "research_interests": interests,
                    "featured_publications": pubs,
                    "openalex_id": f"https://openalex.org/{aid}",
                    "confidence_score": conf_score,
                    "quarantine_flags": q_flags,
                    "is_quarantined": is_quarantined,
                    "discovered_via": "Stage 6 Footprint 3 (OpenAlex Recent Works Mining)",
                    "ingested_at": datetime.now().isoformat()
                }

                if is_quarantined:
                    quarantined_records.append(new_record)
                    print(f"  [⚠️ Quarantined ({conf_score:.2f})] {new_record['id']}: {full_th} | Flags: {', '.join(q_flags)}")
                else:
                    qualified_records.append(new_record)
                    print(f"  [✅ Qualified ({conf_score:.2f})] {new_record['id']}: {full_th} ({fn_en} {ln_en}) | h={scholar['h_index']} | cites={scholar['total_citations']}")

        # Checkpoint qualified discovered records to agent states
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "skill_state_unlisted_discovery.json")
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(qualified_records, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Checkpoint saved: {checkpoint_file} ({len(qualified_records)} qualified records)")

        # Checkpoint quarantined records to quarantine state
        quarantine_file = os.path.join(CHECKPOINT_DIR, "skill_state_unresolved_quarantine.json")
        with open(quarantine_file, "w", encoding="utf-8") as f:
            json.dump(quarantined_records, f, ensure_ascii=False, indent=2)
        print(f"🛡️ Quarantine state saved: {quarantine_file} ({len(quarantined_records)} quarantined records)")

        # Database Ingestion & Vectorization (ONLY qualified records)
        print("\n--- Ingesting Qualified Faculty into PostgreSQL & Vectorizing ---")
        ingested_count = 0
        for rec in qualified_records:
            fid = rec["id"]
            existing = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if existing:
                continue

            faculty = FacultyDB(
                id=fid,
                first_name=rec["first_name"],
                last_name=rec["last_name"],
                academic_title_th=rec["academic_title_th"],
                full_name_th=rec["full_name_th"],
                university_th=rec["university_th"],
                faculty_th=rec["faculty_th"],
                department_th=rec["department_th"],
                total_citations=rec["total_citations"],
                h_index=rec["h_index"],
                research_interests=rec["research_interests"],
                featured_publications=rec["featured_publications"],
                email=None
            )

            # Generate embedding text and 768-dim vector embedding
            faculty.embedding_text = build_faculty_embedding_text(faculty)
            faculty.embedding = embedder.get_embedding(faculty.embedding_text)

            db.add(faculty)
            ingested_count += 1

        db.commit()
        print(f"✨ Successfully ingested {ingested_count} newly discovered faculty members into local PostgreSQL!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error encountered: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
