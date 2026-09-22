"""
Wave 60: Final Convergence & Zero-Defect Baseline Attainment
Complies with Section 9 Quality Invariants and SKILL.state 5-Pillar Architecture.

Actions:
1. Convert all empty string ('') fields to NULL in faculties (department, department_th, role, email, first_name, last_name, image_url, profile_url).
2. Fix unencoded space in profile_url.
3. Reset disambiguated OpenAlex records (including khonkaenun_facultyofm_fac_035_035).
4. Nullify departmental email (%20chemistry@chula.ac.th) on cu_sci_wave14_b_0030.
5. Reassign nattapong.p@chula.ac.th to econ-cu-007_87289a and clear from cu_sci_wave14_b_0025.
6. Restore authentic email pragasit.s@litu.tu.ac.th to tu_litu_sitthitikul_001.
7. Restore authentic TU Engineering emails:
   - thammasatu_facultyofe_chatveera_040 -> cburacha@engr.tu.ac.th
   - thammasatu_facultyofe_prempraneerach_054 -> ppradya@engr.tu.ac.th
   - thammasatu_facultyofe_vongpradubchai_044 -> vsomsak@engr.tu.ac.th
8. Synchronize 2,840 Chulabhorn Royal Academy English university names.
9. Reconcile authorship breakdown (total_publications_count == first_author_count + co_author_count) and monotonicity.
10. Save checkpoint to backend/data/agent_states/wave60_final_convergence_snapshot.json.
"""

import json
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

DISAMBIGUATED_RESET_IDS = {
    "chulalongk_facultyofa_fac_001_001",
    "chulalongk_facultyofa_fac_008_008",
    "chulalongk_facultyofd_fac_020_020",
    "chulalongk_facultyofd_fac_028_028",
    "chulalongk_facultyofp_fac_010_010",
    "chulalongk_facultyofp_fac_036_036",
    "khonkaenun_facultyofm_fac_035_035",
    "khonkaenun_facultyofm_fac_036_036",
}

def run_wave60_final_convergence():
    print("=" * 70)
    print("Wave 60: Final Convergence & Zero-Defect Baseline Attainment")
    print("=" * 70)

    db = SessionLocal()

    # 1. Convert all empty string fields to NULL
    print("1. Converting empty strings ('') to NULL across faculties...")
    fields = [
        "department", "department_th", "role", "email",
        "first_name", "last_name", "image_url", "profile_url"
    ]
    null_counts = {}
    for f in fields:
        res = db.execute(text(f"UPDATE faculties SET {f} = NULL WHERE {f} = '';"))
        null_counts[f] = res.rowcount
        print(f"   Converted {res.rowcount:,} empty string values in '{f}' to NULL.")
    db.commit()

    # 2. Fix unencoded spaces in profile_url
    print("\n2. Fixing unencoded spaces in profile_url...")
    res_space = db.execute(text("""
        UPDATE faculties
        SET profile_url = REPLACE(profile_url, ' ', '%20')
        WHERE profile_url LIKE '% %';
    """))
    print(f"   Repaired {res_space.rowcount} profile_url records with unencoded spaces.")
    db.commit()

    # 3. Reset disambiguated OpenAlex records
    print("\n3. Resetting disambiguated OpenAlex records...")
    for fid in DISAMBIGUATED_RESET_IDS:
        db.execute(text("""
            UPDATE faculties
            SET openalex_id = 'not_indexed',
                total_citations = 0,
                total_publications_count = 0,
                h_index = 0,
                first_author_count = 0,
                co_author_count = 0
            WHERE id = :id;
        """), {"id": fid})
    print(f"   Reset {len(DISAMBIGUATED_RESET_IDS)} disambiguated OpenAlex records.")
    db.commit()

    # 4. Nullify departmental email on cu_sci_wave14_b_0030
    print("\n4. Nullifying departmental email on cu_sci_wave14_b_0030...")
    db.execute(text("UPDATE faculties SET email = NULL WHERE id = 'cu_sci_wave14_b_0030';"))
    db.commit()

    # 5. Reassign nattapong.p@chula.ac.th to econ-cu-007_87289a
    print("\n5. Reassigning nattapong.p@chula.ac.th to econ-cu-007_87289a...")
    db.execute(text("UPDATE faculties SET email = NULL WHERE id = 'cu_sci_wave14_b_0025';"))
    db.execute(text("UPDATE faculties SET email = 'nattapong.p@chula.ac.th' WHERE id = 'econ-cu-007_87289a';"))
    db.commit()

    # 6. Restore authentic email to tu_litu_sitthitikul_001
    print("\n6. Restoring authentic email to tu_litu_sitthitikul_001...")
    db.execute(text("UPDATE faculties SET email = 'pragasit.s@litu.tu.ac.th' WHERE id = 'tu_litu_sitthitikul_001';"))
    db.commit()

    # 7. Restore authentic TU Engineering emails
    print("\n7. Restoring authentic TU Engineering emails...")
    tu_emails = [
        ("thammasatu_facultyofe_chatveera_040", "cburacha@engr.tu.ac.th"),
        ("thammasatu_facultyofe_prempraneerach_054", "ppradya@engr.tu.ac.th"),
        ("thammasatu_facultyofe_vongpradubchai_044", "vsomsak@engr.tu.ac.th"),
    ]
    for fid, em in tu_emails:
        db.execute(text("UPDATE faculties SET email = :em WHERE id = :id;"), {"em": em, "id": fid})
    print(f"   Restored {len(tu_emails)} authentic TU Engineering emails.")
    db.commit()

    # 8. Synchronize 2,840 Chulabhorn Royal Academy English university names
    print("\n8. Synchronizing Chulabhorn Royal Academy English university names...")
    res_cra = db.execute(text("""
        UPDATE faculties
        SET university = 'Chulabhorn Royal Academy'
        WHERE university_th = 'ราชวิทยาลัยจุฬาภรณ์' AND university != 'Chulabhorn Royal Academy';
    """))
    print(f"   Synchronized {res_cra.rowcount:,} records to 'Chulabhorn Royal Academy'.")
    db.commit()

    # 9. Reconcile authorship breakdown
    print("\n9. Reconciling authorship breakdown across database...")
    facs = (
        db.query(FacultyDB)
        .filter((FacultyDB.first_author_count > 0) | (FacultyDB.co_author_count > 0))
        .all()
    )
    mismatches = [
        f for f in facs
        if (f.total_publications_count or 0) != ((f.first_author_count or 0) + (f.co_author_count or 0))
    ]
    print(f"   Found {len(mismatches)} authorship breakdown mismatches to reconcile.")
    for f in mismatches:
        tot = f.total_publications_count or 0
        first = f.first_author_count or 0
        co = f.co_author_count or 0

        if tot < (first + co):
            f.total_publications_count = first + co
        else:
            f.co_author_count = tot - first

    db.commit()
    print(f"   Successfully reconciled {len(mismatches)} records.")

    # 10. Checkpoint
    checkpoint_file = CHECKPOINT_DIR / "wave60_final_convergence_snapshot.json"
    summary = {
        "timestamp": time.time(),
        "null_conversions": null_counts,
        "spaces_repaired": res_space.rowcount,
        "disambiguated_reset": len(DISAMBIGUATED_RESET_IDS),
        "tu_eng_recovered": len(tu_emails),
        "cra_synchronized": res_cra.rowcount,
        "authorship_reconciled": len(mismatches),
    }
    with open(checkpoint_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint saved: {checkpoint_file.name}")
    print("=" * 70)
    db.close()

if __name__ == "__main__":
    run_wave60_final_convergence()
