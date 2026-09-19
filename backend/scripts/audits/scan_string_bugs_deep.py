"""
Deep string bug scan across all text fields in faculties table.
Run: python backend/scripts/audits/scan_string_bugs_deep.py
"""
import psycopg2
import json

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 70)
print("DEEP STRING BUG SCAN — faculties table")
print("=" * 70)

# ── 1. Null bytes in any varchar field ────────────────────────────────
print("\n[1] Null bytes (\\x00) in string fields")
for col in ["full_name_th", "email", "academic_title_th", "first_name", "last_name",
            "department_th", "faculty_th", "university_th", "profile_url", "image_url"]:
    cur.execute(f"SELECT COUNT(*) FROM faculties WHERE {col} ~ '\\x00'")
    n = cur.fetchone()[0]
    if n:
        print(f"  {col}: {n} rows")
print("  (done)")

# ── 2. Leading/trailing whitespace ────────────────────────────────────
print("\n[2] Leading/trailing whitespace in key fields")
for col in ["full_name_th", "email", "academic_title_th", "first_name", "last_name",
            "department_th", "faculty_th"]:
    cur.execute(f"""
        SELECT COUNT(*) FROM faculties
        WHERE {col} IS NOT NULL AND {col} != ''
        AND ({col} != TRIM({col}))
    """)
    n = cur.fetchone()[0]
    if n:
        print(f"  {col}: {n} rows with leading/trailing whitespace")
print("  (done)")

# ── 3. Double spaces inside names ─────────────────────────────────────
print("\n[3] Double spaces inside full_name_th")
cur.execute("""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th LIKE '%  %'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute("""
        SELECT id, full_name_th, university_th FROM faculties
        WHERE full_name_th LIKE '%  %' LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 4. HTML entities or tags in text fields ───────────────────────────
print("\n[4] HTML entities / tags in full_name_th, department_th, faculty_th")
for col in ["full_name_th", "department_th", "faculty_th"]:
    cur.execute(f"""
        SELECT COUNT(*) FROM faculties
        WHERE {col} ~ '(&amp;|&lt;|&gt;|&nbsp;|&#[0-9]+;|<[a-z]+>)'
    """)
    n = cur.fetchone()[0]
    if n:
        print(f"  {col}: {n} rows")
        cur.execute(f"""
            SELECT id, {col}, university_th FROM faculties
            WHERE {col} ~ '(&amp;|&lt;|&gt;|&nbsp;|&#[0-9]+;|<[a-z]+>)'
            LIMIT 5
        """)
        for r in cur.fetchall():
            print(f"    {r[0]:45s}  {r[1]!r}")
print("  (done)")

# ── 5. Glued academic title (no space after dot) ──────────────────────
print("\n[5] Glued academic title prefix (e.g. 'ศ.ดร.ชื่อ' no space)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?[ก-๙A-Za-z]'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th, university_th FROM faculties
        WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?[ก-๙A-Za-z]'
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 6. academic_title_th/full_name_th mismatch ───────────────────────
print("\n[6] academic_title_th vs full_name_th prefix mismatch")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE academic_title_th IS NOT NULL
    AND full_name_th IS NOT NULL
    AND full_name_th NOT LIKE academic_title_th || ' %'
    AND full_name_th NOT LIKE academic_title_th || '%'
    AND full_name_th != ''
    AND academic_title_th != ''
""")
n = cur.fetchone()[0]
print(f"  {n} rows where full_name_th doesn't start with academic_title_th")
if n:
    cur.execute(r"""
        SELECT id, academic_title_th, full_name_th, university_th FROM faculties
        WHERE academic_title_th IS NOT NULL
        AND full_name_th IS NOT NULL
        AND full_name_th NOT LIKE academic_title_th || ' %'
        AND full_name_th NOT LIKE academic_title_th || '%'
        AND full_name_th != ''
        AND academic_title_th != ''
        LIMIT 20
    """)
    for r in cur.fetchall():
        print(f"    [{r[1]!r}] vs [{r[2]!r}]  ({r[0]})")

# ── 7. Broken profile_url (no scheme or localhost) ────────────────────
print("\n[7] Broken profile_url (no http, or localhost, or just '/')")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE profile_url IS NOT NULL
    AND profile_url != ''
    AND profile_url !~ '^https?://'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with non-http profile_url")
if n:
    cur.execute(r"""
        SELECT id, profile_url, university_th FROM faculties
        WHERE profile_url IS NOT NULL
        AND profile_url != ''
        AND profile_url !~ '^https?://'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 8. image_url pointing to localhost or file:// ─────────────────────
print("\n[8] Suspicious image_url (localhost / file:// / relative)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE image_url IS NOT NULL
    AND image_url != ''
    AND (image_url ~ '^(file://|/(?!/)|\.|localhost)' OR image_url !~ '^https?://')
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, image_url, university_th FROM faculties
        WHERE image_url IS NOT NULL
        AND image_url != ''
        AND (image_url ~ '^(file://|/(?!/)|\.|localhost)' OR image_url !~ '^https?://')
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 9. Duplicate emails across different faculty ──────────────────────
print("\n[9] Shared personal emails across multiple faculty members")
cur.execute("""
    SELECT email, COUNT(*) as cnt, array_agg(full_name_th) as names
    FROM faculties
    WHERE email IS NOT NULL
    AND email NOT LIKE '%@%ac.th'
    AND email NOT LIKE '%@%edu'
    GROUP BY email
    HAVING COUNT(*) > 1
    LIMIT 20
""")
rows = cur.fetchall()
print(f"  {len(rows)} shared non-institutional emails")
for r in rows:
    print(f"    {r[0]!r} ({r[1]}x): {r[2][:3]}")

# ── 10. Institutional/departmental emails in email field ──────────────
print("\n[10] Departmental/generic emails (info@, sci@, dent@, etc.)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE email ~ '^(info|sci|dent|eng|med|admin|office|contact|mail|webmaster|noreply)@'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with departmental inbox emails")
if n:
    cur.execute(r"""
        SELECT id, email, full_name_th FROM faculties
        WHERE email ~ '^(info|sci|dent|eng|med|admin|office|contact|mail|webmaster|noreply)@'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 11. research_interests with phone-number-like strings ─────────────
print("\n[11] Phone numbers in research_interests or education JSON")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE research_interests::text ~ '0[689][0-9]{8}'
    OR education::text ~ '0[689][0-9]{8}'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with phone patterns in JSON fields")

# ── 12. Emoji in name fields ──────────────────────────────────────────
print("\n[12] Emoji in full_name_th / first_name / last_name")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '[\U0001F300-\U0001FFFF]'
    OR first_name ~ '[\U0001F300-\U0001FFFF]'
    OR last_name ~ '[\U0001F300-\U0001FFFF]'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with emoji in name fields")

# ── 13. first_name or last_name is NULL or empty ─────────────────────
print("\n[13] NULL or empty first_name / last_name")
cur.execute("""
    SELECT
        SUM(CASE WHEN first_name IS NULL OR first_name = '' THEN 1 ELSE 0 END) as null_first,
        SUM(CASE WHEN last_name IS NULL OR last_name = '' THEN 1 ELSE 0 END) as null_last
    FROM faculties
""")
r = cur.fetchone()
print(f"  NULL/empty first_name: {r[0]}")
print(f"  NULL/empty last_name : {r[1]}")

# ── 14. university_th mismatch with university (EN) ──────────────────
print("\n[14] Distinct university_th values (sanity check)")
cur.execute("""
    SELECT university_th, COUNT(*) as cnt
    FROM faculties
    GROUP BY university_th
    ORDER BY cnt DESC
    LIMIT 25
""")
for r in cur.fetchall():
    print(f"  {r[1]:5d}  {r[0]}")

conn.close()
print("\n[Scan complete]")
