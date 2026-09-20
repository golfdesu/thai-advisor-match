# -*- coding: utf-8 -*-
"""
Phase 2: CMU Deep Cleaning & Enrichment Pipeline
Fixes:
1. 38 CMU Pediatric Medicine faculty with 'Endocrine Metabolism'
2. 1 CMU Pharmacy accent 'Kiartisín' -> 'Kiartisin'
3. 2 CMU Foreign faculty full_name_th ('อ.ดร.' / 'รศ.ดร.')
4. Generates 768-dim vector embeddings
5. Checkpoints state to disk
"""
import os
import sys
import json
import re
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService, load_all_gemini_keys
from google import genai

STATE_CHECKPOINT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "skill_state_cmu_deep_clean.json")

TITLE_PATTERN = re.compile(
    r'^(?:ศ\.เชี่ยวชาญพิเศษ|ศ\.เกียรติคุณ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.|'
    r'ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|สพ\.ญ\.|สพ\.บ\.|ทนพ\.|ทนพญ\.|กภ\.|รอ\.|'
    r'น\.สพ\.|สัตวแพทย์หญิง|สัตวแพทย์|นายแพทย์\s+|แพทย์หญิง\s+|อาจารย์\s+|ผศ\s+|รศ\s+|ศ\s+|ดร\s+|นพ\s+|พญ\s+)\s*',
    re.IGNORECASE
)

def clean_th_title(raw_th):
    if not raw_th:
        return ""
    cur = raw_th.strip()
    for _ in range(4):
        nxt = TITLE_PATTERN.sub("", cur).strip()
        if nxt == cur:
            break
        cur = nxt
    return cur

def transliterate_cmu_batch(client, items):
    prompt = """Transliterate these Thai medical faculty names into standard English (Royal Thai General System - RTGS, capitalized).
Honor institutional email hints if provided.
Return ONLY a valid JSON object mapping each ID to {"first": "...", "last": "..."}.
Ensure names contain ONLY Latin letters, spaces, hyphens, and apostrophes.
No markdown backticks, no explanation.

Input:
""" + json.dumps(items, ensure_ascii=False, indent=2)

    resp = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )
    text = resp.text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)

def main():
    print("=================================================================")
    print("🚀 PHASE 2: CMU DEEP QUALITY RESOLUTION & EMBEDDINGS")
    print("=================================================================")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db = SessionLocal()
    embedder = EmbeddingService()
    gemini_keys = load_all_gemini_keys()
    if not gemini_keys:
        print("❌ Error: No Gemini API keys found!")
        db.close()
        return
    ai_client = genai.Client(api_key=gemini_keys[0])

    # 1. Target 38 CMU Pediatric Medicine faculty
    endo_records = db.query(FacultyDB).filter(
        FacultyDB.university_th.like("%เชียงใหม่%"),
        FacultyDB.first_name.ilike("endocrine")
    ).all()
    print(f"Found CMU Endocrine records: {len(endo_records)}")

    batch_items = []
    for r in endo_records:
        th_clean = clean_th_title(r.full_name_th)
        email_hint = r.email.split("@")[0] if r.email and "@" in r.email else ""
        batch_items.append({
            "id": r.id,
            "name_th": th_clean or r.full_name_th,
            "email_hint": email_hint
        })

    print(f"Batch transliterating {len(batch_items)} CMU faculty names via gemini-3.5-flash-lite...")
    res = transliterate_cmu_batch(ai_client, batch_items)

    resolved_map = {}
    for r in endo_records:
        fid = r.id
        if fid in res and isinstance(res[fid], dict):
            f_en = res[fid].get("first", "").strip().title()
            l_en = res[fid].get("last", "").strip().title()
            if f_en and l_en and re.match(r"^[a-zA-Z\s\-\.\']+$", f_en) and re.match(r"^[a-zA-Z\s\-\.\']+$", l_en):
                resolved_map[fid] = (f_en, l_en)
                r.first_name = f_en
                r.last_name = l_en
                r.embedding_text = build_faculty_embedding_text(r)
                r.embedding = embedder.get_embedding(r.embedding_text)
                print(f"  ✓ {fid}: {r.full_name_th} -> {f_en} {l_en}")

    # 2. Fix accent in Kanokwan Kiartisín
    k_rec = db.query(FacultyDB).filter(FacultyDB.id == "wave22_0015_918").first()
    if k_rec:
        k_rec.last_name = "Kiartisin"
        k_rec.embedding_text = build_faculty_embedding_text(k_rec)
        k_rec.embedding = embedder.get_embedding(k_rec.embedding_text)
        print(f"  ✓ wave22_0015_918: Kanokwan Kiartisín -> Kanokwan Kiartisin")

    # 3. Fix CMU foreign faculty full_name_th
    cmu_foreign = {
        "cmu_6c77b1e6_7673": "อ.ดร. Xuefeng Zhang",
        "cmu_d542da29_8423": "รศ.ดร. Tri Indrarini Wirjantoro"
    }
    for fid, th_val in cmu_foreign.items():
        rec = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if rec:
            rec.full_name_th = th_val
            rec.embedding_text = build_faculty_embedding_text(rec)
            rec.embedding = embedder.get_embedding(rec.embedding_text)
            print(f"  ✓ {fid}: full_name_th -> {th_val}")

    db.commit()
    print("✅ All CMU records successfully committed to PostgreSQL!")

    # Checkpoint to disk
    os.makedirs(os.path.dirname(STATE_CHECKPOINT_PATH), exist_ok=True)
    checkpoint_data = {
        "timestamp": datetime.now().isoformat(),
        "total_cmu_resolved": len(resolved_map) + 3,
        "records": [
            {"id": fid, "first_name": resolved_map[fid][0], "last_name": resolved_map[fid][1]}
            for fid in resolved_map
        ]
    }
    with open(STATE_CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    print(f"💾 State checkpoint saved to: {STATE_CHECKPOINT_PATH}")

    db.close()

if __name__ == "__main__":
    main()
