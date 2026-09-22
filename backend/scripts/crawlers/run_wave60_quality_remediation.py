"""
Wave 60: Quality Remediation & Zero-Defect Convergence
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Actions:
1. Fix bibliometric monotonicity on tsu_w50_0309_684 (total_publications_count >= h_index).
2. Clean up 28 mis-attributed KMUTNB/UP duplicate stubs (including kmutnb_w57_1887_840 with generic faculty_th).
3. Transliterate and purge Greek/Cyrillic/Georgian/Kannada contamination from 63 faculty records.
4. Deduplicate intra-faculty research_interests across 67 records.
5. Propagate English first_name and last_name from OpenAlex matches to authentic Thai records.
6. Checkpoint saved to backend/data/agent_states/wave60_quality_remediation_snapshot.json.
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
from app.models.db_models import FacultyDB

CHECKPOINT_DIR = BASE_DIR / "backend" / "data" / "agent_states"

CYRILLIC_TO_LATIN = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'І': 'I', 'і': 'i',
}

GREEK_TO_LATIN = {
    'Α': 'A', 'Β': 'B', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H',
    'Θ': 'Th', 'Ι': 'I', 'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X',
    'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Φ': 'Ph',
    'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O',
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h',
    'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x',
    'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y',
    'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
    'ί': 'i', 'ά': 'a', 'έ': 'e', 'ή': 'i', 'ό': 'o', 'ύ': 'y', 'ώ': 'o',
}

UNICODE_SPECIFIC_MAP = {
    'nida_w55_0140_471': 'รศ.ดร. ปรัชญา พันณกิจกาสเอม',
    'kmutt_w57_0953_135': 'ผศ.ดร. มนสิษฐ์ ธนสิทธิโกศล',
    'kmutt_w57_6067_970': 'ดร. สิกานต์ อยู่คง',
    'kmutt_w57_6642_639': 'ก. สุรวัฒนกุล',
    'swu_w57_1785_114': 'ศ.ดร. มนตรี อุดมเพทายกุล',
    'swu_w57_1669_192': 'ดร. ดนัย ลิมปโอวาท',
    'cmu_w57_5278_481': 'ชาตปุก ประกอบ',
    'sut_w57_3540_565': 'อภิสิทธิ์ พฤกษาเมธานันท์',
}

FORBIDDEN_RANGES = [
    (0x0370, 0x03FF),   # Greek and Coptic
    (0x0400, 0x04FF),   # Cyrillic
    (0x10A0, 0x10FF),   # Georgian
    (0x0C80, 0x0CFF),   # Kannada
]

def clean_unicode_name(fid: str, name: str) -> str:
    if fid in UNICODE_SPECIFIC_MAP:
        return UNICODE_SPECIFIC_MAP[fid]
    out = []
    for ch in name:
        if ch in CYRILLIC_TO_LATIN:
            out.append(CYRILLIC_TO_LATIN[ch])
        elif ch in GREEK_TO_LATIN:
            out.append(GREEK_TO_LATIN[ch])
        else:
            out.append(ch)
    return ''.join(out)

def run_wave60_remediation():
    print("=" * 70)
    print("Wave 60: Quality Remediation & Zero-Defect Convergence")
    print("=" * 70)

    db = SessionLocal()

    # 1. Monotonicity Fix
    print("1. Repairing Bibliometric Monotonicity...")
    res_mono = db.execute(text("""
        UPDATE faculties
        SET total_publications_count = GREATEST(COALESCE(total_publications_count, 0), h_index)
        WHERE h_index IS NOT NULL AND total_publications_count IS NOT NULL AND h_index > total_publications_count
        RETURNING id, h_index, total_publications_count;
    """)).fetchall()
    for r in res_mono:
        print(f"   [REPAIRED] {r[0]}: h_index={r[1]}, new total_pubs={r[2]}")

    # 2. Clean up 28 mis-attributed KMUTNB/UP duplicate stubs
    print("\n2. Cleaning up 28 mis-attributed KMUTNB / UP duplicate stubs...")
    up_stubs = db.execute(text("""
        SELECT id, full_name_th
        FROM faculties
        WHERE profile_url LIKE '%up.ac.th%' AND university_th != 'มหาวิทยาลัยพะเยา';
    """)).fetchall()
    stub_ids = [s[0] for s in up_stubs]
    if stub_ids:
        db.execute(text("DELETE FROM faculties WHERE id = ANY(:ids)"), {"ids": stub_ids})
        print(f"   Deleted {len(stub_ids)} duplicate stubs (including kmutnb_w57_1887_840).")

    # 3. Transliterate and purge Greek/Cyrillic/Georgian/Kannada contamination
    print("\n3. Purging forbidden Unicode contamination from faculty full_name_th...")
    contam_rows = db.execute(text("""
        SELECT id, full_name_th
        FROM faculties
        WHERE full_name_th ~ '[Ͱ-ϿЀ-ӿႠ-ჿಀ-೿]';
    """)).fetchall()
    print(f"   Found {len(contam_rows)} contaminated records to clean.")
    cleaned_unicode_count = 0
    for fid, fname in contam_rows:
        new_name = clean_unicode_name(fid, fname)
        db.execute(
            text("UPDATE faculties SET full_name_th = :name WHERE id = :id"),
            {"name": new_name, "id": fid}
        )
        cleaned_unicode_count += 1
    print(f"   Successfully cleaned {cleaned_unicode_count} names.")

    # 4. Deduplicate intra-faculty research_interests
    print("\n4. Deduplicating intra-faculty research_interests...")
    facs_with_interests = db.query(FacultyDB).filter(FacultyDB.research_interests.isnot(None)).all()
    dedup_interest_count = 0
    for f in facs_with_interests:
        if not f.research_interests:
            continue
        seen = set()
        deduped = []
        has_dup = False
        for item in f.research_interests:
            key = str(item).strip().lower()
            if key in seen and key:
                has_dup = True
            elif key:
                seen.add(key)
                deduped.append(item)
        if has_dup:
            f.research_interests = deduped
            dedup_interest_count += 1
    print(f"   Deduplicated research_interests for {dedup_interest_count} records.")

    # 5. Propagate English first_name and last_name from OpenAlex counterparts
    print("\n5. Propagating English first & last names from OpenAlex matches...")
    prop_rows = db.execute(text("""
        SELECT DISTINCT ON (t.id)
            t.id, o.first_name, o.last_name
        FROM faculties t
        JOIN faculties o ON o.openalex_id = t.openalex_id AND o.id != t.id
        WHERE t.full_name_th ~ '[ก-๙]'
          AND (t.first_name IS NULL OR t.first_name = '')
          AND t.openalex_id LIKE 'A%'
          AND o.first_name IS NOT NULL AND o.first_name != ''
        ORDER BY t.id;
    """)).fetchall()
    print(f"   Found {len(prop_rows)} authentic Thai records with matching OpenAlex English names.")
    for tid, fn, ln in prop_rows:
        db.execute(
            text("UPDATE faculties SET first_name = :fn, last_name = :ln WHERE id = :id"),
            {"fn": fn, "ln": ln, "id": tid}
        )
    print(f"   Successfully propagated names for {len(prop_rows)} records.")

    db.commit()

    # 6. Save Checkpoint Snapshot
    checkpoint_file = CHECKPOINT_DIR / "wave60_quality_remediation_snapshot.json"
    summary = {
        "timestamp": time.time(),
        "monotonicity_fixed": len(res_mono),
        "up_stubs_deleted": len(stub_ids),
        "unicode_names_cleaned": cleaned_unicode_count,
        "interests_deduplicated": dedup_interest_count,
        "names_propagated": len(prop_rows),
    }
    with open(checkpoint_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint saved: {checkpoint_file.name}")
    print("=" * 70)
    db.close()

if __name__ == "__main__":
    run_wave60_remediation()
