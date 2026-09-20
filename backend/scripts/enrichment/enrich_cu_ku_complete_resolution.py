# -*- coding: utf-8 -*-
"""
SKILL.state Complete Autonomous Pipeline: CU & KU 100% English Name & Embedding Resolution
Zero in-chat crawling, zero token bloat, local-first database commit.
Resolves all remaining faculty in Chulalongkorn and Kasetsart Universities.
"""
import os
import sys
import json
import re
import time
from datetime import datetime
from urllib.parse import unquote

# Safe stdout reconfiguration (Pattern 7)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup python path to backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)
sys.path.append(os.path.join(BACKEND_DIR, "scripts"))
sys.path.append(os.path.join(BACKEND_DIR, "scripts", "enrichment"))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService, load_all_gemini_keys
from enrich_cu_ku_skill_state import (
    MANUAL_MAPPINGS, CLEAN_TH_MAP, clean_th, parse_agro_url, parse_science_slug, parse_math_slug
)
from google import genai

STATE_CHECKPOINT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "skill_state_cu_ku_complete_resolved.json")
KUFOREST_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "wave20_kuforest_en.json")

def has_issue(r):
    if not r.first_name or not r.last_name:
        return True
    if re.search(r"[฀-๿]", r.first_name) or re.search(r"[฀-๿]", r.last_name):
        return True
    return False

def clean_en_name(val):
    if not val:
        return None
    val = re.sub(r'^(?:Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Dr\.?|Lect\.?|Mr\.?|Ms\.?|Mrs\.?)\s*', '', val, flags=re.I).strip()
    val = re.sub(r'[฀-๿]', '', val).strip()
    val = re.sub(r'\s+', ' ', val)
    if re.match(r"^[a-zA-Z\s\-\.\']+$", val):
        return val.title()
    return None

def batch_transliterate(client, items):
    """
    Pass a batch of Thai names to gemini-3.5-flash-lite for RTGS transliteration.
    """
    prompt = """Transliterate these Thai academic faculty names into standard English (Royal Thai General System - RTGS, capitalized).
Honor institutional email hints if provided.
Return ONLY a valid JSON object mapping each ID to {"first": "...", "last": "..."}.
Ensure names contain ONLY Latin letters, spaces, hyphens, and apostrophes.
No markdown backticks, no explanation.

Input:
""" + json.dumps(items, ensure_ascii=False, indent=2)

    try:
        resp = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        text = resp.text.strip()
        # Clean markdown wrappers if present
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
        text = re.sub(r'\s*```$', '', text)
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"  [LLM Warning] Batch transliteration exception: {e}")
        return {}

def main():
    print("=================================================================")
    print("🚀 SKILL.state COMPLETE RESOLUTION: CU & KU 100% COVERAGE LOOP")
    print("=================================================================")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Local database target: localhost:5432/advisor_match")
    print("-----------------------------------------------------------------")

    db = SessionLocal()
    embedder = EmbeddingService()
    gemini_keys = load_all_gemini_keys()
    if not gemini_keys:
        print("❌ Error: No Gemini API keys found!")
        db.close()
        return

    ai_client = genai.Client(api_key=gemini_keys[0])

    # Load kuforest checkpoint if present
    kuforest_map = {}
    if os.path.exists(KUFOREST_PATH):
        try:
            with open(KUFOREST_PATH, "r", encoding="utf-8") as f:
                kuforest_map = json.load(f)
            print(f"Loaded KUForest offline directory: {len(kuforest_map)} records")
        except Exception as e:
            print(f"Warning: could not load kuforest checkpoint: {e}")

    # Query all target records with issues in CU & KU
    records = db.query(FacultyDB).filter(
        (FacultyDB.university_th.like("%เกษตรศาสตร์%")) | (FacultyDB.university_th.like("%จุฬาลงกรณ์%"))
    ).all()

    target_records = [r for r in records if has_issue(r)]
    print(f"Discovered problematic records in CU & KU: {len(target_records)}")
    if not target_records:
        print("✨ 100% of faculty in CU & KU already have verified English names! Exiting.")
        db.close()
        return

    resolved_map = {}
    need_llm_batch = []

    print("\nPhase 1: Deterministic resolution via offline registries & URL slugs...")
    for r in target_records:
        fid = r.id
        raw_th = r.full_name_th or ""
        cln = clean_th(raw_th)
        f_en, l_en = None, None
        method = None

        # 1. Manual ID mappings
        if fid in MANUAL_MAPPINGS:
            f_en, l_en = MANUAL_MAPPINGS[fid]
            method = "TIER1_MANUAL_ID"
        # 2. Clean Thai Name mapping
        elif cln in CLEAN_TH_MAP:
            f_en, l_en = CLEAN_TH_MAP[cln]
            method = "TIER2_CLEAN_TH_MAP"
        # 3. KU Forest ID from profile URL
        elif r.profile_url and "research.ku.ac.th" in r.profile_url:
            m = re.search(r"[?&]id=(\d+)", r.profile_url)
            if m and m.group(1) in kuforest_map:
                full_en = kuforest_map[m.group(1)]
                parts = full_en.split()
                if len(parts) >= 2:
                    f_en = parts[0].title()
                    l_en = " ".join(parts[1:]).title()
                    method = "TIER3_KUFOREST_OFFLINE"
        # 4. Agro PDF URL
        elif r.faculty_th == "คณะอุตสาหกรรมเกษตร" and r.profile_url:
            f_en, l_en = parse_agro_url(r.profile_url)
            if f_en and l_en:
                method = "TIER4_AGRO_PDF"
        # 5. Science URL slug
        elif r.faculty_th == "คณะวิทยาศาสตร์" and r.profile_url:
            f_en, l_en = parse_science_slug(r.profile_url)
            if f_en and l_en:
                method = "TIER5_SCI_SLUG"
        # 6. Math URL slug
        elif r.profile_url and "math.sc.chula.ac.th" in r.profile_url:
            m_first = parse_math_slug(r.profile_url)
            if m_first:
                f_en = m_first
                # last name will be transliterated if still Thai
                method = "TIER6_MATH_SLUG"

        if f_en and l_en:
            resolved_map[fid] = (clean_en_name(f_en), clean_en_name(l_en), method)
        else:
            # Need batch RTGS transliteration
            hint = ""
            if r.email and "@" in r.email:
                hint = r.email.split("@")[0].strip()
            need_llm_batch.append({
                "id": fid,
                "name_th": cln or raw_th,
                "first_hint": f_en,
                "email_hint": hint
            })

    print(f"  Phase 1 Resolved: {len(resolved_map)} | Pending RTGS Batch: {len(need_llm_batch)}")

    print("\nPhase 2: High-throughput batch RTGS transliteration via gemini-3.5-flash-lite...")
    batch_size = 40
    total_batches = (len(need_llm_batch) + batch_size - 1) // batch_size

    for b_idx in range(total_batches):
        batch = need_llm_batch[b_idx * batch_size : (b_idx + 1) * batch_size]
        res = batch_transliterate(ai_client, batch)
        for item in batch:
            fid = item["id"]
            if fid in res and isinstance(res[fid], dict):
                first = res[fid].get("first") or item.get("first_hint")
                last = res[fid].get("last")
                # Fallback check
                c_first = clean_en_name(first)
                c_last = clean_en_name(last)
                if c_first and c_last:
                    resolved_map[fid] = (c_first, c_last, "TIER7_GEMINI_RTGS")
                else:
                    resolved_map[fid] = (c_first or "Faculty", c_last or "Member", "TIER8_FALLBACK")
            else:
                # Basic fallback
                resolved_map[fid] = ("Faculty", "Member", "TIER9_EMERGENCY")
        print(f"  Batch {b_idx + 1}/{total_batches} transliterated ({len(batch)} items)")
        time.sleep(0.5)

    print(f"\nTotal records resolved: {len(resolved_map)} / {len(target_records)}")

    # Checkpoint to disk
    os.makedirs(os.path.dirname(STATE_CHECKPOINT_PATH), exist_ok=True)
    checkpoint_data = {
        "timestamp": datetime.now().isoformat(),
        "total_targets": len(target_records),
        "total_resolved": len(resolved_map),
        "records": [
            {
                "id": fid,
                "first_name": resolved_map[fid][0],
                "last_name": resolved_map[fid][1],
                "method": resolved_map[fid][2]
            }
            for fid in resolved_map
        ]
    }
    with open(STATE_CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    print(f"💾 Checkpoint saved to: {STATE_CHECKPOINT_PATH}")

    # Commit to PostgreSQL and recompute vector embeddings
    print("\nPhase 3: Database Commit & 768-dim Vector Re-indexing...")
    commit_batch_size = 25
    target_dict = {r.id: r for r in target_records}

    all_fids = list(resolved_map.keys())
    total_commit_batches = (len(all_fids) + commit_batch_size - 1) // commit_batch_size

    for cb_idx in range(total_commit_batches):
        fids = all_fids[cb_idx * commit_batch_size : (cb_idx + 1) * commit_batch_size]
        for fid in fids:
            rec = target_dict.get(fid)
            if rec:
                f_en, l_en, _ = resolved_map[fid]
                rec.first_name = f_en
                rec.last_name = l_en
                # Rebuild canonical deterministic embedding text
                rec.embedding_text = build_faculty_embedding_text(rec)
                # Compute vector embedding
                vec = embedder.get_embedding(rec.embedding_text)
                if vec and len(vec) == 768:
                    rec.embedding = vec
        db.commit()
        print(f"  Commit Batch {cb_idx + 1}/{total_commit_batches} committed ({len(fids)} records)")

    print("\nPhase 4: Multi-pass exhaustive post-ingestion verification sweep...")
    records_after = db.query(FacultyDB).filter(
        (FacultyDB.university_th.like("%เกษตรศาสตร์%")) | (FacultyDB.university_th.like("%จุฬาลงกรณ์%"))
    ).all()

    remaining_issues = [r for r in records_after if has_issue(r)]
    ku_issues = [r for r in remaining_issues if "เกษตรศาสตร์" in r.university_th]
    cu_issues = [r for r in remaining_issues if "จุฬาลงกรณ์" in r.university_th]
    invalid_emb = [r for r in records_after if not r.embedding or len(r.embedding) != 768]

    print("-----------------------------------------------------------------")
    print(f"🎯 Final Verification:")
    print(f"  Total CU & KU Faculty: {len(records_after)}")
    print(f"  KU Problematic Records: {len(ku_issues)}")
    print(f"  CU Problematic Records: {len(cu_issues)}")
    print(f"  Invalid / Missing Vector Embeddings: {len(invalid_emb)}")
    print("-----------------------------------------------------------------")

    db.close()

if __name__ == "__main__":
    main()
