# -*- coding: utf-8 -*-
"""
SKILL.state Autonomous Pipeline: Mahidol University (MU) & Khon Kaen University (KKU)
Deep Quality Remediation, RTGS Romanization, Ineligible Purge, and 3-Way Deduplication
Zero in-chat crawling, zero token bloat, local-first database commit.
"""
import os
import sys
import json
import re
import time
from datetime import datetime

# Safe stdout reconfiguration (Runbook Guardrail 2)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, ResearchLabDB
from app.core.config import settings
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService

from google import genai

CHECKPOINT_DIR = os.path.join(BACKEND_DIR, "data", "agent_states")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

TITLE_PATTERN = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.|'
    r'ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.|สพ\.ญ\.|สพ\.บ\.|ทนพ\.|ทนพญ\.|กภ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.|'
    r'น\.สพ\.|สัตวแพทย์หญิง|สัตวแพทย์|นายแพทย์\s+|แพทย์หญิง\s+|อาจารย์\s+|ผศ\s+|รศ\s+|ศ\s+|ดร\s+|นพ\s+|พญ\s+|'
    r'Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?|Dr\.?|Lect\.?|Mr\.?|Ms\.?|Mrs\.?)\s*',
    re.IGNORECASE
)

def clean_th_name(name):
    if not name:
        return ""
    curr = name.replace('​', '').replace('﻿', '').replace('\xa0', ' ').strip()
    prev = ""
    while prev != curr:
        prev = curr
        curr = TITLE_PATTERN.sub('', curr).strip()
    curr = re.sub(r'\s+', ' ', curr)
    return curr

def union_lists(l1, l2):
    res = list(l1 or [])
    for item in (l2 or []):
        if item and item not in res:
            res.append(item)
    return res

def batch_transliterate(client, records_to_trans):
    """
    Transliterates a batch of Thai names into standard RTGS English names using gemini-3.5-flash-lite,
    taking email usernames into account as phonetic hints.
    """
    results = {}
    BATCH_SIZE = 30

    for i in range(0, len(records_to_trans), BATCH_SIZE):
        chunk = records_to_trans[i:i+BATCH_SIZE]
        prompt_input = []
        for r in chunk:
            prompt_input.append({
                "id": r["id"],
                "clean_th": r["clean_th"],
                "email": r.get("email") or ""
            })

        prompt = """You are an expert Royal Thai General System (RTGS) romanization engine for academic faculty names.
Given the clean Thai full name (First Last) and optional institutional email hint, generate the authentic English first name and last name.
Rules:
1. Return ONLY a valid JSON object mapping each ID to {"first": "...", "last": "..."}.
2. Ensure both 'first' and 'last' contain ONLY Latin letters, spaces, hyphens, and apostrophes. No Thai, no titles (Dr, Asst, etc.).
3. Capitalize properly (Title Case).
4. If the email local-part suggests a specific transliteration (e.g. email 'skhema@kku.ac.th' for 'เขมจิต เสนา' -> first='Khemajit', last='Sena' / email 'somchan@kku.ac.th' for 'สมพงศ์ จันทร์แก้ว' -> first='Sompong', last='Chankaew'), follow the email hint.
5. No markdown backticks, no explanatory text.

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
                print(f"  [RTGS Batch] Successfully transliterated chunk {i+1} to {min(i+BATCH_SIZE, len(records_to_trans))}")
                break
            except Exception as e:
                print(f"  [RTGS Batch Attempt {attempt+1} Failed]: {e}")
                time.sleep(2)

    return results

def main():
    print("=================================================================")
    print("🚀 SKILL.state AUTONOMOUS PIPELINE: MU & KKU DEEP REMEDIATION")
    print("=================================================================")

    db = SessionLocal()
    embedder = EmbeddingService()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        # -------------------------------------------------------------
        # 1. PURGE INELIGIBLE EMERITUS RECORDS (MU: Pojaman Srinawarat)
        # -------------------------------------------------------------
        print("\n--- STAGE 1: Purging Ineligible Emeritus Records ---")
        pojaman_records = db.query(FacultyDB).filter(
            FacultyDB.university_th == "มหาวิทยาลัยมหิดล",
            FacultyDB.full_name_th.like("%พจมาน ศรีนวรัตน์%")
        ).all()

        purged_snapshot = []
        for p in pojaman_records:
            purged_snapshot.append({
                "id": p.id,
                "full_name_th": p.full_name_th,
                "academic_title_th": p.academic_title_th,
                "university_th": p.university_th,
                "faculty_th": p.faculty_th,
                "reason": "Emeritus Professor (ศ.คลินิกเกียรติคุณ)",
                "purged_at": datetime.now().isoformat()
            })
            print(f"  Purging [{p.id}] {p.full_name_th} ({p.role})")
            db.delete(p)

        with open(os.path.join(CHECKPOINT_DIR, "skill_state_mu_kku_emeritus_purged.json"), "w", encoding="utf-8") as f:
            json.dump(purged_snapshot, f, ensure_ascii=False, indent=2)
        print(f"  Checkpoint saved: skill_state_mu_kku_emeritus_purged.json ({len(purged_snapshot)} records)")
        db.commit()

        # -------------------------------------------------------------
        # 2. RESOLVE MU DEFECTS (Foreign Names & Specific Corrections)
        # -------------------------------------------------------------
        print("\n--- STAGE 2: Resolving MU Names & Field Hygiene ---")
        mu_specific = {
            "mu_sci_wave14_b_0094": ("Bui", "Phuoc Minh", "ดร. บุย เฟื้อก มินห์"),
            "mu_sci_wave14_b_0139": ("Manh", "Van Nguyen", "ดร. มัน วัน เหงียน"),
            "mu_sci_wave14_b_0220": ("Alejandro", "Saez Rivera", "ดร. อเลฮานโดร ซาอีส ริเวรา"),
            "mu_sci_wave14_b_0153": ("Ruth J.", "Skulkhu", "ผศ.ดร. รู้ธ จ. สกุลคู"),
            "mu_sci_wave14_b_0221": ("Amornrat", "Naranuntarat Jensen", "รศ.ดร. อมรรัตน์ นรานันทรัตน์ เจนเซน"),
            "mu_sci_wave14_b_0117": ("Ponpan", "Matangkasombut Choopong", "รศ.ดร. พรพรรณ มาตังคสมบัติ ชูพงศ์"),
            "mu_sci_wave14_b_0141": ("Michael Anthony", "Allen", "รศ.ดร. ไมเคิล แอนโทนี่ เอเลน"),
            "chulalongk_facultyofa_sri_024": ("Sorachai", "Srisuma", "ผศ.ดร. นพ. สรชัย ศรีสุมา"),
            "wave30_0013_570": ("Nanthinee", "Nantawanich Saengfai", "ผศ. ทพญ. นันทินี นันทวณิชย์ แสงไฟ"),
            # College of Music Foreign Faculty (Stage 1.4 Bilingual Restoration)
            "mahidoluni_collegeofm_lynch_170": ("Nathan", "Lynch", "อ. Nathan Lynch"),
            "mahidoluni_collegeofm_matsushima_111": ("Yoshimi", "Matsushima", "อ. Yoshimi Matsushima"),
            "mahidoluni_collegeofm_parente_094": ("David", "Parente", "อ. David Parente"),
            "mahidoluni_collegeofm_matsushima_148": ("Hiroshi", "Matsushima", "อ. Hiroshi Matsushima"),
            "mahidoluni_collegeofm_wright_150": ("Cooper", "Wright", "อ. Cooper Wright"),
            "mahidoluni_collegeofm_jung_155": ("Yu-Jin", "Jung", "อ. Yu-Jin Jung"),
            "mahidoluni_collegeofm_grund_129": ("Martin", "Grund", "อ. Martin Grund"),
        }

        mu_updated = []
        for fid, (fn, ln, th) in mu_specific.items():
            f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if f:
                f.first_name = fn
                f.last_name = ln
                f.full_name_th = th
                f.embedding_text = build_faculty_embedding_text(f)
                f.embedding = embedder.get_embedding(f.embedding_text)
                mu_updated.append({
                    "id": f.id,
                    "first_name": fn,
                    "last_name": ln,
                    "full_name_th": th
                })
                print(f"  Fixed MU [{f.id}] -> {fn} {ln} ({th})")

        db.commit()

        # -------------------------------------------------------------
        # 3. RESOLVE KKU DEFECTS (194 Records via Batch RTGS Romanization)
        # -------------------------------------------------------------
        print("\n--- STAGE 3: Resolving KKU Names via Batch RTGS Romanization ---")
        kku_faculties = db.query(FacultyDB).filter(FacultyDB.university_th == "มหาวิทยาลัยขอนแก่น").all()
        kku_to_fix = []
        for f in kku_faculties:
            fn = (f.first_name or "").strip()
            ln = (f.last_name or "").strip()
            th = (f.full_name_th or "").strip()

            is_missing = not fn or not ln or fn.lower() == "none" or ln.lower() == "none"
            is_thai = bool(re.search(r"[฀-๿]", fn)) or bool(re.search(r"[฀-๿]", ln))

            if is_missing or is_thai:
                clean_th = clean_th_name(th)
                kku_to_fix.append({
                    "id": f.id,
                    "clean_th": clean_th,
                    "email": f.email,
                    "original_th": th
                })

        print(f"  Identified {len(kku_to_fix)} KKU records requiring RTGS transliteration.")

        rtgs_results = batch_transliterate(client, kku_to_fix)

        kku_updated = []
        for item in kku_to_fix:
            fid = item["id"]
            if fid in rtgs_results:
                en = rtgs_results[fid]
                fn = en.get("first", "").strip().title()
                ln = en.get("last", "").strip().title()

                # Validation
                if not re.match(r"^[a-zA-Z\s\-\.\']+$", f"{fn} {ln}"):
                    print(f"  [Validation Warning] Non-Latin transliteration for {fid}: {fn} {ln}")
                    continue

                f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
                if f:
                    f.first_name = fn
                    f.last_name = ln
                    f.embedding_text = build_faculty_embedding_text(f)
                    f.embedding = embedder.get_embedding(f.embedding_text)
                    kku_updated.append({
                        "id": f.id,
                        "full_name_th": f.full_name_th,
                        "first_name": fn,
                        "last_name": ln,
                        "email": f.email
                    })
            else:
                print(f"  [Missing Transliteration Result] {fid}")

        db.commit()
        print(f"  Successfully updated {len(kku_updated)} KKU faculty members with authentic English names.")

        # Save checkpoint for name resolutions
        en_resolved_state = {
            "timestamp": datetime.now().isoformat(),
            "mu_count": len(mu_updated),
            "kku_count": len(kku_updated),
            "mu_records": mu_updated,
            "kku_records": kku_updated
        }
        with open(os.path.join(CHECKPOINT_DIR, "skill_state_mu_kku_en_resolved.json"), "w", encoding="utf-8") as f:
            json.dump(en_resolved_state, f, ensure_ascii=False, indent=2)
        print("  Checkpoint saved: skill_state_mu_kku_en_resolved.json")

        # -------------------------------------------------------------
        # 4. THREE-PASS DEDUPLICATION (MU: 3 Clusters, KKU: 7 Clusters)
        # -------------------------------------------------------------
        print("\n--- STAGE 4: Three-Pass Deduplication & Metric Preservation ---")
        dedup_plan = [
            # MU
            ("wave22_0607_418", "mu_vet_walasinee_001", "MU Vet Walasinee duplicate"),
            ("wave27_0078_256", "mu-sh-002_d7cb1b", "MU Social Sciences Chalermpol duplicate"),
            ("wave30_0042_417", "wave30_0046_245", "MU Dentistry Premwara duplicate"),
            # KKU
            ("wave30_0024_302", "wave29_0045_227", "KKU Humanities Dararat duplicate"),
            ("wave22_0417_132", "kku_med_jureerut_001", "KKU AMS Jureerut duplicate"),
            ("wave22_0397_171", "wave22_0335_276", "KKU Dentistry Jarin duplicate"),
            ("wave22_0383_187", "wave22_0339_202", "KKU Dentistry Dutsadee duplicate"),
            ("wave22_0380_493", "wave22_0365_707", "KKU Dentistry Anoma duplicate"),
            ("wave22_0418_989", "kku_ams_patcharee_001", "KKU AMS Patcharee duplicate"),
            ("wave30_0032_991", "wave30_0031_881", "KKU Humanities Banchakarn duplicate"),
        ]

        dedup_records = []
        for survivor_id, donor_id, reason in dedup_plan:
            survivor = db.query(FacultyDB).filter(FacultyDB.id == survivor_id).first()
            donor = db.query(FacultyDB).filter(FacultyDB.id == donor_id).first()
            if not survivor or not donor:
                print(f"  [Skip Dedup] Missing {survivor_id} or {donor_id}")
                continue

            # Preserve lifetime metrics
            old_cites = survivor.total_citations
            old_h = survivor.h_index
            survivor.total_citations = max(survivor.total_citations or 0, donor.total_citations or 0)
            survivor.h_index = max(survivor.h_index or 0, donor.h_index or 0)
            survivor.research_interests = union_lists(survivor.research_interests, donor.research_interests)
            survivor.featured_publications = union_lists(survivor.featured_publications, donor.featured_publications)
            if not survivor.email and donor.email:
                survivor.email = donor.email

            # Re-point foreign keys in research_labs
            labs = db.query(ResearchLabDB).filter(ResearchLabDB.lead_advisor_id == donor.id).all()
            for lab in labs:
                print(f"  Re-pointing lab {lab.id} advisor from {donor.id} to {survivor.id}")
                lab.lead_advisor_id = survivor.id

            survivor.embedding_text = build_faculty_embedding_text(survivor)
            survivor.embedding = embedder.get_embedding(survivor.embedding_text)

            dedup_records.append({
                "survivor_id": survivor.id,
                "donor_id": donor.id,
                "survivor_name_th": survivor.full_name_th,
                "survivor_name_en": f"{survivor.first_name} {survivor.last_name}",
                "citations": survivor.total_citations,
                "h_index": survivor.h_index,
                "reason": reason
            })

            print(f"  Merged: [{donor.id}] -> [{survivor.id}] {survivor.full_name_th} (Cites: {old_cites}->{survivor.total_citations}, H: {old_h}->{survivor.h_index})")
            db.delete(donor)

        db.commit()

        with open(os.path.join(CHECKPOINT_DIR, "skill_state_mu_kku_dedup.json"), "w", encoding="utf-8") as f:
            json.dump(dedup_records, f, ensure_ascii=False, indent=2)
        print(f"  Checkpoint saved: skill_state_mu_kku_dedup.json ({len(dedup_records)} merges)")

        print("\n✨ All operations committed successfully to local PostgreSQL!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error encountered during execution: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
