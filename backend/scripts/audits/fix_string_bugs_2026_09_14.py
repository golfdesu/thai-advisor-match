"""
Fix all 4 string bugs found in scan_string_bugs_deep.py:
  1. Double space in full_name_th (1 row)
  2. Glued academic title prefix — no space after dot (7,987 rows)
  3. academic_title_th present but full_name_th missing the prefix (636 rows)
  4. Departmental/generic emails → NULL (452 rows)

Run: python backend/scripts/audits/fix_string_bugs_2026_09_14.py
"""
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("STRING BUG FIX — faculties table")
print("=" * 60)

# ── Fix 1: Double spaces ───────────────────────────────────
cur.execute(r"""
    UPDATE faculties
    SET full_name_th = REGEXP_REPLACE(full_name_th, '\s{2,}', ' ', 'g')
    WHERE full_name_th LIKE '%  %'
""")
n1 = cur.rowcount
print(f"\n[Fix 1] Double spaces normalized       : {n1} rows")

# ── Fix 2: Glued title prefix (no space after dot) ────────
# Handles patterns like: รศ.ดร.ชื่อ → รศ.ดร. ชื่อ
# Targets: (ศ.|รศ.|ผศ.|อ.)(ดร.)? immediately followed by a Thai/Latin char (no space)
cur.execute(r"""
    UPDATE faculties
    SET full_name_th = REGEXP_REPLACE(
        full_name_th,
        '^((?:ศ|รศ|ผศ|อ)\.(?:ดร\.)?)([฀-๿A-Za-z])',
        '\1 \2'
    )
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?[฀-๿A-Za-z]'
""")
n2 = cur.rowcount
print(f"[Fix 2] Glued title prefix fixed        : {n2} rows")

# ── Fix 3: full_name_th missing academic_title_th prefix ──
# Only prepend when:
#   - academic_title_th is set and non-empty
#   - full_name_th is set and non-empty
#   - full_name_th does NOT already start with the title
cur.execute(r"""
    UPDATE faculties
    SET full_name_th = academic_title_th || ' ' || full_name_th
    WHERE academic_title_th IS NOT NULL
    AND academic_title_th != ''
    AND full_name_th IS NOT NULL
    AND full_name_th != ''
    AND full_name_th NOT LIKE academic_title_th || ' %'
    AND full_name_th NOT LIKE academic_title_th || '%'
""")
n3 = cur.rowcount
print(f"[Fix 3] Missing title prefix prepended  : {n3} rows")

# ── Fix 4: Departmental/generic emails → NULL ─────────────
cur.execute(r"""
    UPDATE faculties
    SET email = NULL
    WHERE email ~ '^(info|sci|dent|eng|med|admin|office|contact|mail|webmaster|noreply)@'
""")
n4 = cur.rowcount
print(f"[Fix 4] Departmental emails → NULL      : {n4} rows")

conn.commit()

# ── Verify ─────────────────────────────────────────────────
print("\n--- Verification ---")

cur.execute("SELECT COUNT(*) FROM faculties WHERE full_name_th LIKE '%  %'")
print(f"  Remaining double spaces        : {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?[฀-๿A-Za-z]'
""")
print(f"  Remaining glued titles         : {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE academic_title_th IS NOT NULL AND academic_title_th != ''
    AND full_name_th IS NOT NULL AND full_name_th != ''
    AND full_name_th NOT LIKE academic_title_th || ' %'
    AND full_name_th NOT LIKE academic_title_th || '%'
""")
print(f"  Remaining missing-prefix rows  : {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE email ~ '^(info|sci|dent|eng|med|admin|office|contact|mail|webmaster|noreply)@'
""")
print(f"  Remaining departmental emails  : {cur.fetchone()[0]}")

conn.close()
print("\n[All fixes applied and verified]")
