"""
Wave 60: Structural & Title Inversion Repairs
Fixes:
1. Inverted faculty_th / department_th hierarchy where faculty_th = university_th
   (e.g., Naresuan University medical science faculty and Walailak University schools).
2. Clears redundant university-level placeholders where faculty_th = university_th.
3. Populates missing academic_title_th when full_name_th contains explicit Thai title prefixes.

Complies with SKILL.state 5-Pillar Architecture and Section 9 Quality Invariants.
"""

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

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"

RE_THAI_TITLE = re.compile(
    r"^(ศ\.\s*ดร\.|รศ\.\s*ดร\.|ผศ\.\s*ดร\.|อ\.\s*ดร\.|ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|"
    r"นายแพทย์|ทันตแพทย์หญิง|ทันตแพทย์|สัตวแพทย์หญิง|สัตวแพทย์|เภสัชกรหญิง|เภสัชกร|"
    r"นาย|นางสาว|นาง|นพ\.|พญ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|ภก\.|ภญ\.)\s*",
    re.IGNORECASE
)

def canonical_title_th(t: str) -> str:
    t_clean = re.sub(r"\s+", "", t.strip())
    if "ศ.ดร" in t_clean: return "ศ.ดร."
    if "รศ.ดร" in t_clean: return "รศ.ดร."
    if "ผศ.ดร" in t_clean: return "ผศ.ดร."
    if "อ.ดร" in t_clean: return "อ.ดร."
    if "ศ." in t_clean or t_clean == "ศ": return "ศ."
    if "รศ." in t_clean or t_clean == "รศ": return "รศ."
    if "ผศ." in t_clean or t_clean == "ผศ": return "ผศ."
    if "ดร." in t_clean or t_clean == "ดร": return "ดร."
    if "อ." in t_clean or t_clean == "อ": return "อ."
    return t.strip()

def run_structural_repairs():
    print("=" * 70)
    print("Wave 60: Structural Hierarchy & Academic Title Repairs")
    print("=" * 70)

    db = SessionLocal()

    # Step 1: Repair inverted department_th where department_th is actually a faculty
    sql_inverted = """
    UPDATE faculties
    SET faculty_th = department_th, department_th = NULL
    WHERE faculty_th = university_th
      AND (department_th LIKE 'คณะ%' OR department_th LIKE 'วิทยาลัย%' OR department_th LIKE 'สถาบัน%' OR department_th LIKE 'โรงเรียนสาธิต%')
    RETURNING id, university_th, faculty_th;
    """
    inverted_fixed = db.execute(text(sql_inverted)).fetchall()
    print(f"1. Inverted Faculty/Department Hierarchies Repaired: {len(inverted_fixed)} records")
    for r in inverted_fixed[:5]:
        print(f"   [ID: {r[0]}] {r[1]} -> Faculty: {r[2]}")

    # Step 2: Clear redundant placeholder where faculty_th = university_th and department_th is NULL
    sql_clear_univ = """
    UPDATE faculties
    SET faculty_th = NULL
    WHERE faculty_th = university_th AND department_th IS NULL
    RETURNING id;
    """
    cleared_placeholders = db.execute(text(sql_clear_univ)).fetchall()
    print(f"2. Redundant University-Level Faculty Placeholders Cleared: {len(cleared_placeholders)} records")

    # Step 3: Populate academic_title_th from full_name_th when title is missing
    sql_titles_to_fix = """
    SELECT id, full_name_th
    FROM faculties
    WHERE (academic_title_th IS NULL OR academic_title_th = '')
      AND full_name_th ~ '^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นายแพทย์|ทันตแพทย์|สัตวแพทย์|เภสัชกร|นาย|นางสาว|นาง|นพ\.|พญ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|ภก\.|ภญ\.)';
    """
    title_rows = db.execute(text(sql_titles_to_fix)).fetchall()
    print(f"3. Identified {len(title_rows)} records with missing title but prefix in full_name_th.")

    updated_titles = 0
    for fid, fth in title_rows:
        m = RE_THAI_TITLE.match(fth.strip())
        if m:
            raw_title = m.group(1).strip()
            norm_title = canonical_title_th(raw_title)
            db.execute(text("UPDATE faculties SET academic_title_th = :t WHERE id = :id"), {"t": norm_title, "id": fid})
            updated_titles += 1

    db.commit()
    print(f"   Successfully populated academic_title_th for {updated_titles} records.")

    # Save Checkpoint Snapshot
    checkpoint_file = CHECKPOINT_DIR / "wave60_structural_repairs_snapshot.json"
    summary = {
        "timestamp": time.time(),
        "inverted_faculties_repaired": len(inverted_fixed),
        "placeholders_cleared": len(cleared_placeholders),
        "titles_populated": updated_titles,
    }
    with open(checkpoint_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint saved to: {checkpoint_file.name}")
    print("=" * 70)
    db.close()

if __name__ == "__main__":
    run_structural_repairs()
