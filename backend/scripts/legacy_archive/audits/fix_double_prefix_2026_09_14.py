"""
Fix double-prefix rows created by fix_string_bugs_2026_09_14.py Fix 3.
Pattern: "ผศ.ดร. ผศ. ดร. ชื่อ" → "ผศ.ดร. ชื่อ"
Also fix "ผศ.ดร. ผศ.ดร. ชื่อ" and similar variations.

Run: python backend/scripts/audits/fix_double_prefix_2026_09_14.py
"""
import psycopg2
import re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("DOUBLE-PREFIX FIX — faculties table")
print("=" * 60)

# Fetch all rows with potential double prefix
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th
    FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)? (?:ศ\.|รศ\.|ผศ\.|อ\.)'
""")
rows = cur.fetchall()
print(f"\nRows to fix: {len(rows)}")

# Python-side: strip the duplicated leading title
# Pattern: <title1> <title2_spaced> <name>  →  <title1> <name>
# e.g. "ผศ.ดร. ผศ. ดร. ชื่อ" → "ผศ.ดร. ชื่อ"
# e.g. "รศ.ดร. รศ. ดร. ชื่อ" → "รศ.ดร. ชื่อ"
# e.g. "อ. อ. ชื่อ" → "อ. ชื่อ"
title_prefix_re = re.compile(
    r'^((?:ศ|รศ|ผศ|อ)\.(?:ดร\.)?) '   # group 1: the compact title (already correct)
    r'(?:(?:ศ|รศ|ผศ|อ)\. ?(?:ดร\.)? )' # the duplicated expanded title to strip
)

updates = []
skipped = 0
for row_id, name, title in rows:
    if not name:
        skipped += 1
        continue
    m = title_prefix_re.match(name)
    if m:
        clean = m.group(1) + " " + name[m.end():]
        # Normalize any accidental double spaces
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, row_id))
    else:
        skipped += 1

print(f"Updates prepared : {len(updates)}")
print(f"Skipped (no match): {skipped}")

# Sample 10 before committing
print("\nSample fixes:")
for new_name, rid in updates[:10]:
    print(f"  {rid:45s}  → {new_name!r}")

# Apply
if updates:
    cur.executemany(
        "UPDATE faculties SET full_name_th = %s WHERE id = %s",
        updates
    )
    print(f"\nRows updated: {cur.rowcount}")
    conn.commit()

# Verify
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)? (?:ศ\.|รศ\.|ผศ\.|อ\.)'
""")
remaining = cur.fetchone()[0]
print(f"Remaining double-prefix rows: {remaining}")

conn.close()
print("\n[Done]")
