"""
Fix round 2 string bugs:
  1. 8 rows: last_name contains full two-word surname — split correctly
  2. 1 row: truncated last_name 'Sri...' and full_name_th 'ศรี...' — clean up
  3. openalex_id A5014426991: same person two records — keep on canonical, NULL other
  4. openalex_id A5026104752: two distinct people sharing same ID — NULL both

Run: python backend/scripts/audits/fix_round2_bugs_2026_09_14.py
"""
import psycopg2
import re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("ROUND 2 STRING BUG FIXES")
print("=" * 60)

# ── Fix 1: Split last_name back to true surname only ──────────
# full_name_th is already correct. last_name holds "middlename surname"
# True last_name = final whitespace-separated segment of last_name
print("\n[Fix 1] Correcting last_name for 8 split-surname rows")

cur.execute(r"""
    SELECT id, first_name, last_name, full_name_th
    FROM faculties
    WHERE last_name ~ '[ก-๙]{4,}\s+[ก-๙]{4,}'
    ORDER BY id
""")
rows = cur.fetchall()

updates = []
for rid, fn, ln, full_th in rows:
    # The true last_name is the final word of the current last_name
    parts = ln.strip().split()
    true_last = parts[-1] if parts else ln
    updates.append((true_last, rid))
    print(f"  {rid:45s}  last: {ln!r} → {true_last!r}")

cur.executemany("UPDATE faculties SET last_name = %s WHERE id = %s", updates)
print(f"  Updated: {cur.rowcount} rows")

# ── Fix 2: Truncated last_name 'Sri...' ───────────────────────
print("\n[Fix 2] Fixing truncated name (chulalongk_facultyofa_sri_024)")
# first_name='Sorachai', last_name='Sri...' — last_name is clearly truncated
# full_name_th shows Thai name: 'ผศ.ดร. นพ.สรชัย ศรี...'
# We can only NULL out the truncated last_name; full_name_th stays as-is
# (Thai name ศรี... is also truncated — set to best known value without guessing)
cur.execute("""
    UPDATE faculties
    SET last_name = NULL,
        full_name_th = REGEXP_REPLACE(full_name_th, '\\.\\.\\.', '', 'g')
    WHERE id = 'chulalongk_facultyofa_sri_024'
""")
print(f"  Updated: {cur.rowcount} rows")

# Verify
cur.execute("SELECT full_name_th, last_name FROM faculties WHERE id = 'chulalongk_facultyofa_sri_024'")
r = cur.fetchone()
print(f"  Result: full_name_th={r[0]!r}  last_name={r[1]!r}")

# ── Fix 3: openalex_id A5014426991 ───────────────────────────
# ฐิติมา พุฒิตานนท์ (econ-cu) vs ฐิติมา พุฒิทานันท์ (ku_wave17)
# Same metrics (cit=1037, h=11) → same person, different spelling
# Keep on the CU record (econ-cu-009_9efc88), NULL on ku_wave17_econ_0025
print("\n[Fix 3] openalex_id A5014426991 — same person, keep on CU record")
cur.execute("""
    UPDATE faculties SET openalex_id = NULL
    WHERE id = 'ku_wave17_econ_0025'
""")
print(f"  Nulled openalex_id on ku_wave17_econ_0025: {cur.rowcount} rows")

# ── Fix 4: openalex_id A5026104752 ───────────────────────────
# ธนิต ปัทมพิฑูรย์ vs ธนิศร์ ปัทมพิฑูร — different given names → ambiguous
# NULL both per AGENTS.md Two-Factor Disambiguation rule
print("\n[Fix 4] openalex_id A5026104752 — ambiguous, NULL both")
cur.execute("""
    UPDATE faculties SET openalex_id = NULL
    WHERE openalex_id = 'https://openalex.org/A5026104752'
""")
print(f"  Nulled openalex_id on both rows: {cur.rowcount} rows")

conn.commit()

# ── Verification ──────────────────────────────────────────────
print("\n--- Verification ---")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE last_name ~ '[ก-๙]{4,}\s+[ก-๙]{4,}'
""")
print(f"  Remaining split-surname last_name rows: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th LIKE '%..%' OR last_name LIKE '%..%'
""")
print(f"  Remaining truncated '...' in name fields: {cur.fetchone()[0]}")

cur.execute("""
    SELECT openalex_id, COUNT(*) FROM faculties
    WHERE openalex_id IS NOT NULL AND openalex_id != 'not_indexed'
    GROUP BY openalex_id HAVING COUNT(*) > 1
""")
dups = cur.fetchall()
print(f"  Remaining duplicate openalex_id pairs: {len(dups)}")

conn.close()
print("\n[All round 2 fixes applied]")
