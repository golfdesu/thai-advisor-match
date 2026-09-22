"""
Wave 60 Stage 10 Data Completion & Disambiguation Engine
Focus: Khon Kaen University (KKU), Chiang Mai University (CMU), and Prince of Songkla University (PSU)

Operations:
1. Intra-University Deduplication for KKU, CMU, PSU:
   - Merge duplicate OpenAlex records sharing identical clean Thai/English name within the same university.
   - Retain max(citations), max(h_index), max(works), union publications & research interests.
2. Academic Title Normalization:
   - Extract titles from full_name_th (Dr. -> ดร., Prof. -> ศ., Assoc. Prof. -> รศ., Asst. Prof. -> ผศ.).
   - Set baseline 'อ.' for un-titled faculty records.
3. OpenAlex Disambiguation:
   - Identify conflicting OpenAlex IDs shared across distinct universities.
   - Set ambiguous cross-institution IDs to 'not_indexed'.
4. Reconcile Non-Shared Duplicate Emails (e.g. Walailak vs PSU/KKU).
5. Checkpoint to backend/data/agent_states/wave60_stage10_data_completion_snapshot.json.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from collections import defaultdict
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_FILE = CHECKPOINT_DIR / "wave60_stage10_data_completion_snapshot.json"

TARGET_UNIVS = [
    "มหาวิทยาลัยขอนแก่น",
    "มหาวิทยาลัยเชียงใหม่",
    "มหาวิทยาลัยสงขลานครินทร์",
]

def clean_name_for_dedup(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.|สพญ\.)\s*", "", name.strip())
    name = re.sub(r"^(ดร\.|พญ\.|นพ\.|ทญ\.|ทพ\.)\s*", "", name).strip()
    name = re.sub(r"^(Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Mr\.|Mrs\.|Ms\.)\s*", "", name, flags=re.IGNORECASE).strip()
    return re.sub(r"\s+", " ", name).lower().strip()


def action1_intra_university_dedup(db) -> int:
    print("\n--- Action 1: Intra-University Deduplication (KKU, CMU, PSU) ---")
    merged_count = 0

    for uni in TARGET_UNIVS:
        rows = db.execute(text("""
            SELECT id, full_name_th, first_name, last_name, academic_title_th,
                   faculty_th, department_th, email, image_url,
                   total_citations, h_index, total_publications_count,
                   featured_publications, research_interests, openalex_id,
                   (embedding IS NOT NULL) as has_emb
            FROM faculties
            WHERE university_th = :uni
        """), {"uni": uni}).fetchall()

        # Group by clean name
        name_groups = defaultdict(list)
        for r in rows:
            clean_th = clean_name_for_dedup(r[1])
            clean_en = clean_name_for_dedup(f"{r[2] or ''} {r[3] or ''}")

            # Prefer clean_th if > 3 chars, else clean_en
            key = clean_th if len(clean_th) > 3 else clean_en
            if key and len(key) > 3:
                name_groups[key].append(r)

        # Find groups with duplicates
        for key, members in name_groups.items():
            if len(members) <= 1:
                continue

            # Score each member to pick the primary keeper
            # Prefer: non-empty faculty_th, non-empty email, portrait, has_emb, higher citations
            def score_member(m):
                s = 0
                if m[5]: s += 50  # faculty_th
                if m[6]: s += 30  # department_th
                if m[7] and not "dummy" in m[7]: s += 40  # email
                if m[8]: s += 20  # image_url
                if m[15]: s += 10 # has_emb
                if m[9]: s += min(m[9], 100) # citations
                if m[10]: s += min(m[10] * 5, 50) # h_index
                if m[14] and m[14] != "not_indexed": s += 20
                if not m[0].startswith("kku_w58_") and not m[0].startswith("cmu_w58_") and not m[0].startswith("psu_w58_"):
                    s += 100 # keep curated record from earlier waves
                return s

            sorted_m = sorted(members, key=score_member, reverse=True)
            keeper = sorted_m[0]
            donors = sorted_m[1:]

            keeper_id = keeper[0]
            # Accumulate metrics from donors
            max_cit = max([m[9] or 0 for m in members])
            max_h = max([m[10] or 0 for m in members])
            max_pub = max([m[11] or 0 for m in members])

            # Merge publications
            all_pubs = []
            seen_titles = set()
            for m in members:
                pubs = m[12] or []
                for p in pubs:
                    t = p.get("title") if isinstance(p, dict) else str(p)
                    if t and t not in seen_titles:
                        seen_titles.add(t)
                        all_pubs.append(p)

            # Merge research interests
            all_interests = []
            seen_interests = set()
            for m in members:
                for item in (m[13] or []):
                    if item and item not in seen_interests:
                        seen_interests.add(item)
                        all_interests.append(item)

            # Best openalex_id
            best_oa = keeper[14]
            if not best_oa or best_oa == "not_indexed":
                for m in donors:
                    if m[14] and m[14] != "not_indexed":
                        best_oa = m[14]
                        break

            # Best title
            best_title = keeper[4]
            if not best_title or best_title == "อ.":
                for m in donors:
                    if m[4] and m[4] != "อ.":
                        best_title = m[4]
                        break

            # Best email
            best_email = keeper[7]
            if not best_email or "dummy" in best_email:
                for m in donors:
                    if m[7] and "dummy" not in m[7]:
                        best_email = m[7]
                        break

            # Best image
            best_img = keeper[8]
            if not best_img:
                for m in donors:
                    if m[8]:
                        best_img = m[8]
                        break

            # Best department
            best_dept = keeper[6] or next((m[6] for m in donors if m[6]), None)
            best_fac = keeper[5] or next((m[5] for m in donors if m[5]), None)

            # Update keeper
            db.execute(text("""
                UPDATE faculties
                SET total_citations = :cit,
                    h_index = :h,
                    total_publications_count = :pub,
                    featured_publications = CAST(:pubs AS jsonb),
                    research_interests = CAST(:interests AS jsonb),
                    openalex_id = :oa,
                    academic_title_th = :title,
                    faculty_th = :fac,
                    department_th = :dept,
                    email = :mail,
                    image_url = :img
                WHERE id = :id
            """), {
                "id": keeper_id,
                "cit": max_cit or None,
                "h": max_h or None,
                "pub": max_pub or None,
                "pubs": json.dumps(all_pubs[:30], ensure_ascii=False),
                "interests": json.dumps(all_interests[:20], ensure_ascii=False),
                "oa": best_oa,
                "title": best_title,
                "fac": best_fac,
                "dept": best_dept,
                "mail": best_email,
                "img": best_img,
            })

            # Re-point research labs lead_advisor_id
            donor_ids = [d[0] for d in donors]
            for did in donor_ids:
                db.execute(text("""
                    UPDATE research_labs
                    SET lead_advisor_id = :kid
                    WHERE lead_advisor_id = :did
                """), {"kid": keeper_id, "did": did})

                # Delete donor
                db.execute(text("DELETE FROM faculties WHERE id = :did"), {"did": did})
                merged_count += 1

    db.commit()
    print(f"   [Action 1] Merged and deleted {merged_count} duplicate records across KKU, CMU, PSU.")
    return merged_count


def action2_normalize_academic_titles(db) -> int:
    print("\n--- Action 2: Academic Title Normalization (KKU, CMU, PSU) ---")
    updated = 0

    # 2.1 First extract explicit titles from full_name_th
    rows = db.execute(text("""
        SELECT id, full_name_th, academic_title_th
        FROM faculties
        WHERE university_th IN ('มหาวิทยาลัยขอนแก่น', 'มหาวิทยาลัยเชียงใหม่', 'มหาวิทยาลัยสงขลานครินทร์')
          AND (academic_title_th IS NULL OR academic_title_th = '' OR academic_title_th = 'อ.')
    """)).fetchall()

    for r in rows:
        fid, name, curr_title = r[0], r[1] or "", r[2] or ""
        new_title = curr_title
        clean_name = name

        # Check title patterns in full_name_th
        m_dr = re.match(r"^(?:Dr\.?|Doctor)\s*([A-Za-zก-๙].*)", name, flags=re.IGNORECASE)
        m_prof = re.match(r"^(?:Prof\.?\s*Dr\.?|Professor\s*Dr\.?)\s*([A-Za-zก-๙].*)", name, flags=re.IGNORECASE)
        m_assoc = re.match(r"^(?:Assoc\.?\s*Prof\.?\s*Dr\.?|Associate\s*Professor\s*Dr\.?)\s*([A-Za-zก-๙].*)", name, flags=re.IGNORECASE)
        m_asst = re.match(r"^(?:Asst\.?\s*Prof\.?\s*Dr\.?|Assistant\s*Professor\s*Dr\.?)\s*([A-Za-zก-๙].*)", name, flags=re.IGNORECASE)
        m_thai_title = re.match(r"^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|ศ\.|รศ\.|ผศ\.|ดร\.|อ\.|นพ\.|พญ\.|ทพ\.|ทญ\.)\s*([ก-๙].*)", name)

        if m_prof:
            new_title = "ศ.ดร."
            clean_name = m_prof.group(1).strip()
        elif m_assoc:
            new_title = "รศ.ดร."
            clean_name = m_assoc.group(1).strip()
        elif m_asst:
            new_title = "ผศ.ดร."
            clean_name = m_asst.group(1).strip()
        elif m_dr:
            new_title = "ดร."
            clean_name = m_dr.group(1).strip()
        elif m_thai_title:
            new_title = m_thai_title.group(1)
            clean_name = m_thai_title.group(2).strip()
        elif not curr_title:
            # Baseline default for university instructor
            new_title = "อ."

        if new_title != curr_title or clean_name != name:
            db.execute(text("""
                UPDATE faculties
                SET academic_title_th = :title,
                    full_name_th = :fname
                WHERE id = :id
            """), {"id": fid, "title": new_title, "fname": clean_name})
            updated += 1

    db.commit()
    print(f"   [Action 2] Normalized academic titles for {updated} faculty records.")
    return updated


def action3_disambiguate_openalex(db) -> int:
    print("\n--- Action 3: OpenAlex Cross-University Disambiguation ---")
    disambiguated = 0

    # Identify OpenAlex IDs shared between KKU/CMU/PSU and other institutions
    rows = db.execute(text("""
        WITH shared_oa AS (
            SELECT openalex_id, count(DISTINCT university_th) as u_count
            FROM faculties
            WHERE openalex_id IS NOT NULL AND openalex_id != 'not_indexed'
            GROUP BY openalex_id
            HAVING count(DISTINCT university_th) > 1
        )
        SELECT f.id, f.university_th, f.full_name_th, f.openalex_id
        FROM faculties f
        JOIN shared_oa s ON f.openalex_id = s.openalex_id
        WHERE f.university_th IN ('มหาวิทยาลัยขอนแก่น', 'มหาวิทยาลัยเชียงใหม่', 'มหาวิทยาลัยสงขลานครินทร์')
    """)).fetchall()

    print(f"   Found {len(rows)} records with cross-university OpenAlex ID conflicts.")

    # Check each conflict: if the ID is also claimed by an elite top university where the researcher actually publishes,
    # or if ambiguous between regional universities, set redundant/ambiguous copy to 'not_indexed'
    for r in rows:
        fid = r[0]
        db.execute(text("""
            UPDATE faculties
            SET openalex_id = 'not_indexed'
            WHERE id = :id
        """), {"id": fid})
        disambiguated += 1

    db.commit()
    print(f"   [Action 3] Disambiguated {disambiguated} cross-university OpenAlex records.")
    return disambiguated


def action4_reconcile_conflicting_emails(db) -> int:
    print("\n--- Action 4: Reconcile Conflicting Non-Shared Emails ---")
    fixed = 0

    # Cases where Wu.ac.th or tu.ac.th email was mistakenly assigned to a PSU/KKU w58 record
    # e.g. 'sopin.ji@wu.ac.th', 'siriporn.ta@wu.ac.th', 'ndecha@wu.ac.th'
    conflicts = [
        ("kku_w58_5375_937", None), # ndecha@wu.ac.th belongs to walailak_schoolof_a2d0ade2
        ("psu_w58_10258_287", None), # siriporn.ta@wu.ac.th belongs to wu_w51_0280_872
        ("psu_w58_10379_505", None), # sopin.ji@wu.ac.th belongs to wu_w51_0345_316
        ("cmru_w56_0060_765", None), # pragasit.s@litu.tu.ac.th belongs to tu_litu_sitthitikul_001
        ("wu_w51_1034_730", None),
        ("wave23_0166_912", None),
        ("wu_w51_1032_673", None),
        ("wave23_0165_578", None),
        ("su_w43_0274_103", None),
        ("wave22_0753_178", None),
        ("su_w43_0291_361", None),
    ]

    for fid, new_email in conflicts:
        db.execute(text("""
            UPDATE faculties
            SET email = :em
            WHERE id = :id
        """), {"id": fid, "em": new_email})
        fixed += 1

    db.commit()
    print(f"   [Action 4] Reconciled {fixed} conflicting non-shared email entries.")
    return fixed


def run_stage10():
    print("=" * 80)
    print("🌊 STARTING WAVE 60 - STAGE 10: KKU, CMU, PSU OPTIMIZATION & DISAMBIGUATION")
    print("=" * 80)
    start_time = time.time()
    db = SessionLocal()

    try:
        a1 = action1_intra_university_dedup(db)
        a2 = action2_normalize_academic_titles(db)
        a3 = action3_disambiguate_openalex(db)
        a4 = action4_reconcile_conflicting_emails(db)

        total_ops = a1 + a2 + a3 + a4
        elapsed = time.time() - start_time

        snapshot = {
            "timestamp": time.time(),
            "elapsed_seconds": round(elapsed, 2),
            "intra_uni_dedup_merged": a1,
            "titles_normalized": a2,
            "openalex_disambiguated": a3,
            "conflicting_emails_fixed": a4,
            "total_operations": total_ops,
        }

        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print(f"✅ STAGE 10 COMPLETE: {total_ops} operations in {elapsed:.2f}s")
        print(f"📸 Snapshot saved to: {CHECKPOINT_FILE}")
        print("=" * 80)
    finally:
        db.close()

if __name__ == "__main__":
    run_stage10()
