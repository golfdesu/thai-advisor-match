"""
Wave 60: English First & Last Name Normalizer
Parses full_name_th into first_name and last_name for English-only faculty records
where first_name / last_name are currently NULL or empty.

Complies with Section 9 Quality Invariants:
- Longest title match first (Prof. Dr. before Prof., Assoc. Prof. before Assoc., etc.)
- Boundary-aware prefix stripping.
- Batch processing with streaming execution.
- Checkpointed snapshot saved to backend/data/agent_states/.
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

RE_EN_TITLE = re.compile(
    r"^(Prof\.\s*Dr\.|Assoc\.\s*Prof\.\s*Dr\.|Asst\.\s*Prof\.\s*Dr\.|"
    r"Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.|Mr\.|Mrs\.|Ms\.)\s*",
    re.IGNORECASE
)

def parse_english_tokens(full_name: str) -> tuple[str, str]:
    if not full_name:
        return ("", "")
    # Strip title prefix
    cleaned = RE_EN_TITLE.sub("", full_name.strip()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    tokens = cleaned.split()
    if not tokens:
        return ("", "")
    if len(tokens) == 1:
        return (tokens[0], "")
    elif len(tokens) == 2:
        return (tokens[0], tokens[1])
    else:
        # 3 or more tokens: e.g. "Paul M. Thompson" -> first: "Paul M.", last: "Thompson"
        return (" ".join(tokens[:-1]), tokens[-1])

def run_english_name_parsing():
    print("=" * 70)
    print("Wave 60: English First & Last Name Normalization")
    print("=" * 70)

    db = SessionLocal()

    # Query all English records where first_name is empty/null
    rows = db.execute(text("""
        SELECT id, full_name_th
        FROM faculties
        WHERE full_name_th !~ '[ก-๙]'
          AND (first_name IS NULL OR first_name = '' OR last_name IS NULL OR last_name = '')
        ORDER BY id
    """)).fetchall()

    print(f"Candidate English records to normalize: {len(rows):,}")

    updated_count = 0
    batch = []
    BATCH_SIZE = 2000

    for fid, fth in rows:
        fn, ln = parse_english_tokens(fth)
        if fn:
            batch.append({"id": fid, "fn": fn, "ln": ln})
            updated_count += 1

        if len(batch) >= BATCH_SIZE:
            db.execute(
                text("UPDATE faculties SET first_name = :fn, last_name = :ln WHERE id = :id"),
                batch
            )
            db.commit()
            print(f"   Committed batch of {len(batch):,} records ({updated_count:,} total)...")
            batch.clear()

    if batch:
        db.execute(
            text("UPDATE faculties SET first_name = :fn, last_name = :ln WHERE id = :id"),
            batch
        )
        db.commit()
        print(f"   Committed final batch of {len(batch):,} records.")

    # Save Checkpoint
    checkpoint_file = CHECKPOINT_DIR / "wave60_english_name_parsing_snapshot.json"
    summary = {
        "timestamp": time.time(),
        "total_evaluated": len(rows),
        "total_updated": updated_count,
    }
    with open(checkpoint_file, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    print(f"\nCompleted English Name Normalization: {updated_count:,} records updated.")
    print(f"Checkpoint saved: {checkpoint_file.name}")
    print("=" * 70)
    db.close()

if __name__ == "__main__":
    run_english_name_parsing()
