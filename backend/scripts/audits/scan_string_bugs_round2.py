"""
Extended string bug scan — round 2.
Checks fields and patterns not covered in the first scan.
Run: python backend/scripts/audits/scan_string_bugs_round2.py
"""
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 70)
print("STRING BUG SCAN ROUND 2 — faculties + courses + research_labs")
print("=" * 70)

# ── 1. Honorific/gender prefix contaminating first_name ───────────────
print("\n[1] Honorific/gender title in first_name (Mr./Mrs./Miss/นาย/นาง/นางสาว/ภก./ภญ.)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE first_name ~ '^(Mr\.?|Mrs\.?|Miss\.?|Dr\.?|Prof\.?|นาย|นาง|นางสาว|ภก\.|ภญ\.|พญ\.|นพ\.)\s'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, first_name, last_name, full_name_th, university_th FROM faculties
        WHERE first_name ~ '^(Mr\.?|Mrs\.?|Miss\.?|Dr\.?|Prof\.?|นาย|นาง|นางสาว|ภก\.|ภญ\.|พญ\.|นพ\.)\s'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  first={r[1]!r}")

# ── 2. last_name contains full Thai name (scraper dumped full name into last_name) ──
print("\n[2] last_name contains full Thai sentence (likely full name dumped into last_name)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE last_name IS NOT NULL
    AND last_name ~ '[ก-๙]{4,}\s+[ก-๙]{4,}'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, last_name, full_name_th FROM faculties
        WHERE last_name ~ '[ก-๙]{4,}\s+[ก-๙]{4,}'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  last={r[1]!r}")

# ── 3. full_name_th contains URL or email ─────────────────────────────
print("\n[3] URL or email leaked into full_name_th")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ 'https?://|@[a-z]+\.(ac\.th|edu|com)'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE full_name_th ~ 'https?://|@[a-z]+\.(ac\.th|edu|com)'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 4. academic_title_th values that are non-standard ─────────────────
print("\n[4] Non-standard academic_title_th values")
cur.execute("""
    SELECT academic_title_th, COUNT(*) as cnt
    FROM faculties
    WHERE academic_title_th IS NOT NULL AND academic_title_th != ''
    GROUP BY academic_title_th
    ORDER BY cnt DESC
""")
rows = cur.fetchall()
standard = {'ศ.ดร.','รศ.ดร.','ผศ.ดร.','อ.ดร.','ศ.','รศ.','ผศ.','อ.','ดร.','Prof. Dr.','Assoc. Prof. Dr.','Asst. Prof. Dr.','Prof.','Assoc. Prof.','Asst. Prof.'}
non_std = [(t, c) for t, c in rows if t not in standard]
print(f"  {len(non_std)} non-standard values (top 20):")
for t, c in non_std[:20]:
    print(f"    {c:5d}  {t!r}")

# ── 5. full_name_th contains parenthesised English transliteration beyond normal ──
print("\n[5] full_name_th with suspicious parenthetical content")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '\([^)]{30,}\)'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with long parenthetical in full_name_th")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE full_name_th ~ '\([^)]{30,}\)'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 6. email domain doesn't match university_th ───────────────────────
print("\n[6] Email domain / university mismatch spot-check (cross-uni personal emails)")
cur.execute(r"""
    SELECT id, email, university_th, full_name_th FROM faculties
    WHERE email IS NOT NULL
    AND university_th = 'มหาวิทยาลัยเกษตรศาสตร์'
    AND email NOT LIKE '%@ku.ac.th'
    AND email NOT LIKE '%@kasetsart.ac.th'
    AND email NOT LIKE '%@nontri.ku.ac.th'
    LIMIT 10
""")
rows = cur.fetchall()
print(f"  KU faculty with non-KU email: {len(rows)}")
for r in rows:
    print(f"    {r[0]:45s}  {r[1]!r}")

# ── 7. research_interests contains raw URL strings ────────────────────
print("\n[7] Raw URLs in research_interests JSON")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE research_interests::text ~ 'https?://'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th, research_interests FROM faculties
        WHERE research_interests::text ~ 'https?://'
        LIMIT 5
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  interests={str(r[2])[:100]!r}")

# ── 8. Trailing punctuation / garbage in full_name_th ─────────────────
print("\n[8] Trailing punctuation/garbage in full_name_th")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '[,;:\-_\.]{2,}$'
    OR full_name_th ~ '\s[,;:\-_\.]$'
    OR full_name_th ~ '^\s'
    OR full_name_th ~ '\s$'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE full_name_th ~ '[,;:\-_\.]{2,}$'
        OR full_name_th ~ '\s[,;:\-_\.]$'
        OR full_name_th ~ '^\s'
        OR full_name_th ~ '\s$'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 9. Courses: title_th or title_en is NULL/empty ────────────────────
print("\n[9] Courses with NULL/empty title_th or title_en")
cur.execute("""
    SELECT
        SUM(CASE WHEN title_th IS NULL OR title_th = '' THEN 1 ELSE 0 END) as null_title_th,
        SUM(CASE WHEN title_en IS NULL OR title_en = '' THEN 1 ELSE 0 END) as null_title_en
    FROM courses
""")
r = cur.fetchone()
print(f"  NULL/empty title_th: {r[0]}")
print(f"  NULL/empty title_en: {r[1]}")

# ── 10. Courses: degree_level non-standard values ─────────────────────
print("\n[10] Non-standard degree_level in courses")
cur.execute("""
    SELECT degree_level, COUNT(*) as cnt
    FROM courses
    GROUP BY degree_level
    ORDER BY cnt DESC
""")
for r in cur.fetchall():
    print(f"  {r[1]:5d}  {r[0]!r}")

# ── 11. research_labs: name_th or name_en NULL/empty ──────────────────
print("\n[11] Research labs with NULL/empty name fields")
cur.execute("""
    SELECT
        SUM(CASE WHEN name_th IS NULL OR name_th = '' THEN 1 ELSE 0 END) as null_th,
        SUM(CASE WHEN name_en IS NULL OR name_en = '' THEN 1 ELSE 0 END) as null_en
    FROM research_labs
""")
r = cur.fetchone()
print(f"  NULL/empty name_th: {r[0]}")
print(f"  NULL/empty name_en: {r[1]}")

# ── 12. full_name_th contains digits (phone/ID contamination) ─────────
print("\n[12] Digits in full_name_th (possible phone/ID contamination)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '\d{4,}'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with 4+ consecutive digits in full_name_th")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE full_name_th ~ '\d{4,}'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 13. Duplicate openalex_id assigned to multiple faculty ────────────
print("\n[13] Duplicate openalex_id assigned to multiple faculty")
cur.execute("""
    SELECT openalex_id, COUNT(*) as cnt, array_agg(full_name_th) as names
    FROM faculties
    WHERE openalex_id IS NOT NULL AND openalex_id != ''
    GROUP BY openalex_id
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 15
""")
rows = cur.fetchall()
print(f"  {len(rows)} duplicate openalex_id assignments")
for r in rows:
    print(f"    {r[0]}  ({r[1]}x)  {r[2][:3]}")

# ── 14. profile_url duplicated across multiple faculty ────────────────
print("\n[14] Same profile_url assigned to multiple faculty")
cur.execute("""
    SELECT profile_url, COUNT(*) as cnt
    FROM faculties
    WHERE profile_url IS NOT NULL AND profile_url != ''
    GROUP BY profile_url
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    LIMIT 15
""")
rows = cur.fetchall()
print(f"  {len(rows)} duplicate profile_urls")
for r in rows[:10]:
    print(f"    ({r[1]}x)  {r[0]!r}")

conn.close()
print("\n[Round 2 scan complete]")
