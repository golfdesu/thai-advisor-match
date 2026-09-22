"""
Wave 60: Shared Email Disambiguation & Departmental Inbox Purge
Complies with Section 9 Quality Invariants (Invariant 10: Verified Non-Shared Personal Academic Email)
and SKILL.state 5-Pillar Architecture.

Actions:
1. Purge 6 phantom announcement records (ขอเชิญผู้สนใจเข้าร่วมการเสวนางานวิจัย...).
2. Disambiguate shared emails:
   - Keep email for the single faculty member whose English/Thai name matches the email local part.
   - Clear false email assignment on peer records.
   - Clear generic departmental/office inboxes across all faculty members.
3. Save checkpoint in backend/data/agent_states/.
"""

import json
import re
import sys
import time
from collections import defaultdict
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

GENERIC_KEYWORDS = {
    "info", "contact", "admin", "office", "dean", "pr", "support", "help", "grad",
    "registrar", "admission", "center", "division", "faculty", "department", "staff",
    "public", "news", "mail", "general", "med", "eng", "sci", "dent", "law", "pol",
    "ed", "ortho", "surgery", "anatomy", "eye", "radiology", "fibo", "agr", "cmfm",
    "tls", "cbs", "hospital", "pharma", "nurse", "vet", "physio", "chula", "buu", "tu", "swu"
}

def run_shared_email_disambiguation():
    print("=" * 70)
    print("Wave 60: Shared Email Disambiguation & Quality Hygiene")
    print("=" * 70)

    db = SessionLocal()

    # Step 1: Purge phantom announcement records
    del_phantoms = db.execute(text("""
        DELETE FROM faculties
        WHERE full_name_th LIKE '%ขอเชิญผู้สนใจเข้าร่วมการเสวนางานวิจัย%'
        RETURNING id, full_name_th;
    """)).fetchall()
    print(f"1. Purged {len(del_phantoms)} phantom announcement records.")
    for p in del_phantoms:
        print(f"   [DELETED] {p[0]}: {p[1]}")

    # Step 2: Fetch all records with shared emails
    shared_rows = db.execute(text("""
        SELECT id, full_name_th, first_name, last_name, email, university
        FROM faculties
        WHERE email IN (
            SELECT email FROM faculties WHERE email IS NOT NULL AND email != '' GROUP BY email HAVING count(*) > 1
        )
        ORDER BY email, id
    """)).fetchall()

    by_email = defaultdict(list)
    for r in shared_rows:
        by_email[r[4]].append(r)

    print(f"2. Found {len(by_email)} distinct shared emails across {len(shared_rows)} faculty records.")

    kept_single_email_owner = []
    cleared_peer_ids = []
    cleared_generic_ids = []

    for email, fac_list in by_email.items():
        local_part = email.split("@")[0].lower()

        matched_faculty = None
        # Disambiguate if any faculty's name strictly matches the local_part
        for f in fac_list:
            fn_en = (f[2] or "").lower()
            ln_en = (f[3] or "").lower()
            if fn_en and len(fn_en) > 2 and (fn_en == local_part or local_part.startswith(fn_en + ".")):
                matched_faculty = f
                break
            elif ln_en and len(ln_en) > 3 and (ln_en == local_part or local_part.endswith("." + ln_en)):
                matched_faculty = f
                break
            elif fn_en and ln_en and local_part in (f"{fn_en[0]}{ln_en}", f"{fn_en}.{ln_en[0]}", f"{ln_en}.{fn_en[0]}", f"{fn_en}_{ln_en}"):
                matched_faculty = f
                break

        # Check if local_part is generic
        is_generic = (local_part in GENERIC_KEYWORDS) or any(local_part.startswith(g + ".") or local_part.endswith("." + g) for g in GENERIC_KEYWORDS)

        if matched_faculty and not is_generic:
            kept_single_email_owner.append({
                "email": email,
                "owner_id": matched_faculty[0],
                "owner_name": matched_faculty[1],
            })
            for peer in fac_list:
                if peer[0] != matched_faculty[0]:
                    cleared_peer_ids.append(peer[0])
        else:
            for fac in fac_list:
                cleared_generic_ids.append(fac[0])

    print(f"   - Kept email for {len(kept_single_email_owner)} uniquely verified faculty owners.")
    print(f"   - Clearing falsely attributed email from {len(cleared_peer_ids)} peer records.")
    print(f"   - Clearing departmental generic inbox from {len(cleared_generic_ids)} records.")

    # Execute Updates in Batches
    all_to_clear = list(set(cleared_peer_ids + cleared_generic_ids))
    BATCH_SIZE = 500
    for i in range(0, len(all_to_clear), BATCH_SIZE):
        chunk = all_to_clear[i:i + BATCH_SIZE]
        db.execute(text("UPDATE faculties SET email = NULL WHERE id = ANY(:ids)"), {"ids": chunk})
    db.commit()

    print(f"   Successfully cleared non-personal/shared emails from {len(all_to_clear)} records.")

    # Step 3: Save Checkpoint
    checkpoint_file = CHECKPOINT_DIR / "wave60_shared_email_disambiguation_snapshot.json"
    summary = {
        "timestamp": time.time(),
        "phantoms_purged": len(del_phantoms),
        "total_shared_emails": len(by_email),
        "uniquely_preserved_emails": len(kept_single_email_owner),
        "cleared_peers_count": len(cleared_peer_ids),
        "cleared_generics_count": len(cleared_generic_ids),
        "total_records_cleared": len(all_to_clear),
        "sample_preserved": kept_single_email_owner[:10],
    }
    with open(checkpoint_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print(f"\nCheckpoint saved: {checkpoint_file.name}")
    print("=" * 70)
    db.close()

if __name__ == "__main__":
    run_shared_email_disambiguation()
