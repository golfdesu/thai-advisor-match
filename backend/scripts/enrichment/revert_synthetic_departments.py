# -*- coding: utf-8 -*-
"""
Revert synthetic departments and enforce ground-truth roster affiliations.
Preserves authentic departments from verified university rosters, crawler checkpoints,
and official data sources. For records without verified roster data, explicitly sets
department_th = "ระบุไม่ได้" and department = "Not specified" to prevent data fabrication.
"""

import ast
import json
import re
import sys
import time
from pathlib import Path
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from scripts.enrichment import enrich_departments as ed

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"
CHECKPOINT_FILE = CHECKPOINT_DIR / "revert_synthetic_departments_snapshot.json"


def clean_name(n: str | None) -> str:
    if not n:
        return ""
    for t in [
        "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ศ.", "รศ.", "ผศ.", "ดร.", "อ.",
        "นายแพทย์", "พญ.", "นพ.", "ทพ.", "ทพญ.", "สพ.ญ.", "น.สพ."
    ]:
        if n.startswith(t):
            n = n[len(t):].strip()
    return re.sub(r"\s+", "", n)


def run_revert_synthetic_departments():
    print("=" * 80)
    print("🚀 REVERTING SYNTHETIC DEPARTMENTS & ENFORCING GROUND TRUTH")
    print("=" * 80)
    start_time = time.time()

    # 1. Harvest all authentic departments from verified JSON and Python data sources
    print("\n--- Step 1: Ingesting Verified Roster Data Sources ---")
    authentic_by_id = {}
    authentic_by_uni_name = {}
    authentic_by_email = {}

    # Ingest JSON wave extractions & crawler checkpoints
    for jf in BASE_DIR.rglob("*.json"):
        if "node_modules" in str(jf) or ".git" in str(jf):
            continue
        if "snapshot" in jf.name or "roster_enrich" in jf.name or "revert_synthetic" in jf.name:
            continue
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            items = (
                data
                if isinstance(data, list)
                else (
                    data.get("faculties")
                    or data.get("data")
                    or (list(data.values()) if isinstance(data, dict) else [])
                )
            )
            if not isinstance(items, list):
                continue
            for it in items:
                if not isinstance(it, dict):
                    continue
                dth = it.get("department_th") or it.get("department")
                if not dth or not isinstance(dth, str) or len(dth.strip()) < 2:
                    continue
                dth = dth.strip()
                if "ทั่วไป" in dth or "สาขาวิชาประจำ" in dth or dth == "ระบุไม่ได้":
                    continue
                den = it.get("department_en") or ("Department of " + dth.replace("ภาควิชา", "").replace("สาขาวิชา", "").strip())
                fid = it.get("id")
                if fid:
                    authentic_by_id[fid] = (dth, den)
                uni = it.get("university_th") or it.get("university")
                name = it.get("full_name_th") or it.get("thai_name") or f"{it.get('first_name', '')} {it.get('last_name', '')}".strip()
                cn = clean_name(name)
                mail = (it.get("email") or "").lower().strip()
                if uni and cn:
                    authentic_by_uni_name[(uni, cn)] = (dth, den)
                if mail and "@" in mail:
                    authentic_by_email[mail] = (dth, den)
        except Exception:
            pass

    # Ingest Python data source files
    data_sources_dir = BASE_DIR / "backend" / "scripts" / "data_sources"
    if data_sources_dir.exists():
        for pyf in data_sources_dir.glob("*.py"):
            try:
                content = pyf.read_text(encoding="utf-8")
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Dict):
                        dth, uni, name, fid, mail = None, None, None, None, None
                        for k, v in zip(node.keys, node.values):
                            if isinstance(k, ast.Constant):
                                if k.value in ["department_th", "department"] and isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    dth = v.value.strip()
                                elif k.value in ["university_th", "university"] and isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    uni = v.value.strip()
                                elif k.value in ["full_name_th", "thai_name", "name"] and isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    name = v.value.strip()
                                elif k.value == "id" and isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    fid = v.value.strip()
                                elif k.value == "email" and isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    mail = v.value.lower().strip()
                        if dth and len(dth) > 2 and "ทั่วไป" not in dth and "สาขาวิชาประจำ" not in dth and dth != "ระบุไม่ได้":
                            den = "Department of " + dth.replace("ภาควิชา", "").replace("สาขาวิชา", "").strip()
                            if fid:
                                authentic_by_id[fid] = (dth, den)
                            if uni and name:
                                cn = clean_name(name)
                                if cn:
                                    authentic_by_uni_name[(uni, cn)] = (dth, den)
                            if mail and "@" in mail:
                                authentic_by_email[mail] = (dth, den)
            except Exception:
                pass

    print(f"   Authentic IDs indexed: {len(authentic_by_id):,}")
    print(f"   Authentic (uni, name) pairs indexed: {len(authentic_by_uni_name):,}")
    print(f"   Authentic email mappings indexed: {len(authentic_by_email):,}")

    # 2. Database Evaluation
    print("\n--- Step 2: Evaluating Database Records Against Ground Truth ---")
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT id, university_th, full_name_th, email, faculty_th, research_interests, department_th, department
            FROM faculties
        """)).fetchall()

        total_records = len(rows)
        print(f"   Total faculty records in database: {total_records:,}")

        updates_to_authentic = []
        updates_to_unspecified = []
        already_authentic = 0

        for r in rows:
            fid = r[0]
            uni = r[1]
            name = r[2]
            mail = (r[3] or "").lower().strip()
            fac_th = r[4] or ""
            interests = r[5] or []
            current_dth = r[6]
            current_den = r[7]
            cn = clean_name(name)

            # Check if record has authentic roster evidence
            verified_target = None
            if fid in authentic_by_id:
                verified_target = authentic_by_id[fid]
            elif (uni, cn) in authentic_by_uni_name:
                verified_target = authentic_by_uni_name[(uni, cn)]
            elif mail and mail in authentic_by_email:
                verified_target = authentic_by_email[mail]
            else:
                # Check if current_dth differs from what the synthetic heuristic produces
                interests_str = " ".join(interests).lower()
                res = ed.resolve_department_from_interests(fac_th, interests_str)
                synth_dth = res[0] if res else ("สาขาวิชาประจำ" + fac_th.replace("คณะ", "").replace("สำนักวิชา", "").strip())
                if current_dth and current_dth != synth_dth and "ทั่วไป" not in current_dth and not current_dth.startswith("สาขาวิชาประจำ") and current_dth != "ระบุไม่ได้":
                    # This was an authentic department already present in the database!
                    verified_target = (current_dth, current_den or ("Department of " + current_dth.replace("ภาควิชา", "").replace("สาขาวิชา", "").strip()))

            if verified_target:
                v_dth, v_den = verified_target
                if current_dth == v_dth and current_den == v_den:
                    already_authentic += 1
                else:
                    updates_to_authentic.append((fid, v_dth, v_den))
            else:
                if current_dth != "ระบุไม่ได้" or current_den != "Not specified":
                    updates_to_unspecified.append(fid)

        print(f"   Records already authentic & unchanged: {already_authentic:,}")
        print(f"   Records to align with authentic roster: {len(updates_to_authentic):,}")
        print(f"   Records to reset to 'ระบุไม่ได้' (Not specified): {len(updates_to_unspecified):,}")

        # 3. Database Updates
        print("\n--- Step 3: Committing Batch Updates to Local PostgreSQL ---")
        batch_size = 2000

        # Apply authentic updates
        if updates_to_authentic:
            print(f"   Updating {len(updates_to_authentic):,} records to verified authentic departments...")
            for i in range(0, len(updates_to_authentic), batch_size):
                chunk = updates_to_authentic[i : i + batch_size]
                for fid, v_dth, v_den in chunk:
                    db.execute(text("""
                        UPDATE faculties
                        SET department_th = :dth,
                            department = :den
                        WHERE id = :fid
                    """), {"fid": fid, "dth": v_dth, "den": v_den})
                db.commit()

        # Apply reset to 'ระบุไม่ได้'
        if updates_to_unspecified:
            print(f"   Resetting {len(updates_to_unspecified):,} records to 'ระบุไม่ได้' / 'Not specified'...")
            for i in range(0, len(updates_to_unspecified), batch_size):
                chunk = updates_to_unspecified[i : i + batch_size]
                db.execute(text("""
                    UPDATE faculties
                    SET department_th = :dth,
                        department = :den
                    WHERE id = ANY(:fids)
                """), {
                    "dth": "ระบุไม่ได้",
                    "den": "Not specified",
                    "fids": chunk
                })
                db.commit()
                print(f"      Committed chunk {min(i + batch_size, len(updates_to_unspecified)):,} / {len(updates_to_unspecified):,}...")

        elapsed = time.time() - start_time
        final_authentic_count = already_authentic + len(updates_to_authentic)
        final_unspecified_count = len(updates_to_unspecified)

        snapshot = {
            "timestamp": time.time(),
            "elapsed_seconds": round(elapsed, 2),
            "total_records": total_records,
            "authentic_departments_preserved": final_authentic_count,
            "unspecified_departments_set": final_unspecified_count,
            "authentic_pct": round(final_authentic_count / total_records * 100, 2),
            "unspecified_pct": round(final_unspecified_count / total_records * 100, 2),
        }
        CHECKPOINT_FILE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

        print("\n" + "=" * 80)
        print(f"✅ GROUND-TRUTH REVERT COMPLETE in {elapsed:.2f}s")
        print(f"   Verified Authentic Preserved: {final_authentic_count:,} ({snapshot['authentic_pct']}%)")
        print(f"   Explicitly Marked 'ระบุไม่ได้': {final_unspecified_count:,} ({snapshot['unspecified_pct']}%)")
        print(f"📸 Snapshot saved to: {CHECKPOINT_FILE}")
        print("=" * 80)
    finally:
        db.close()


if __name__ == "__main__":
    run_revert_synthetic_departments()
