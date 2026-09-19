"""
Round 3 string bug scan — driven by AGENTS.md antipatterns:
  - PDPA: Thai National IDs in any field
  - Breadcrumb/non-person first_name or last_name
  - ดร name-mangling (ดรุณี → ุณี)
  - Short TLD email corruption
  - Download links / phone numbers in education/research_interests JSON
  - embedding_text staleness for recently patched rows
  - Glued professional sub-titles (ภก./ภญ./นพ./พญ. glued to name)
  - full_name_th containing 'สถานที่ติดต่อ', 'ติดต่อ', 'ที่อยู่' etc.
  - university_th / faculty_th / department_th containing stray digits or symbols

Run: python backend/scripts/audits/scan_string_bugs_round3.py
"""
import psycopg2
import json

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 70)
print("STRING BUG SCAN ROUND 3 — AGENTS.md antipattern driven")
print("=" * 70)

# ── 1. PDPA: Thai 13-digit National IDs in any text field ─────────────
print("\n[1] Thai 13-digit National IDs (PDPA violation)")
for tbl, col in [
    ("faculties", "full_name_th"), ("faculties", "email"),
    ("faculties", "embedding_text"),
    ("faculties", "research_interests"),
    ("faculties", "education"),
]:
    cur.execute(f"""
        SELECT COUNT(*) FROM {tbl}
        WHERE {col}::text ~ '[1-9][0-9]{{12}}'
    """)
    n = cur.fetchone()[0]
    if n:
        print(f"  {tbl}.{col}: {n} rows — PDPA VIOLATION")
        cur.execute(f"""
            SELECT id, LEFT({col}::text, 120) FROM {tbl}
            WHERE {col}::text ~ '[1-9][0-9]{{12}}'
            LIMIT 5
        """)
        for r in cur.fetchall():
            print(f"    {r[0]:45s}  {r[1]!r}")
print("  (done)")

# ── 2. Breadcrumb/non-person content in first_name or last_name ───────
print("\n[2] Non-person breadcrumb text in first_name / last_name")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE first_name ~* '(department|faculty|school|college|institute|center|office|group|laboratory|division|section|สาขา|ภาควิชา|คณะ|สำนักงาน|ศูนย์|วิทยาลัย|ห้องปฏิบัติการ|สถานที่|ติดต่อ)'
    OR last_name ~* '(department|faculty|school|college|institute|center|office|group|laboratory|division|section|สาขา|ภาควิชา|คณะ|สำนักงาน|ศูนย์|วิทยาลัย|ห้องปฏิบัติการ|สถานที่|ติดต่อ)'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, first_name, last_name, university_th FROM faculties
        WHERE first_name ~* '(department|faculty|school|college|institute|center|office|group|laboratory|division|section|สาขา|ภาควิชา|คณะ|สำนักงาน|ศูนย์|วิทยาลัย|ห้องปฏิบัติการ|สถานที่|ติดต่อ)'
        OR last_name ~* '(department|faculty|school|college|institute|center|office|group|laboratory|division|section|สาขา|ภาควิชา|คณะ|สำนักงาน|ศูนย์|วิทยาลัย|ห้องปฏิบัติการ|สถานที่|ติดต่อ)'
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  first={r[1]!r}  last={r[2]!r}")

# ── 3. ดร-mangled Thai names (ดรุณี → ุณี) ───────────────────────────
print("\n[3] ดร-mangled Thai names (name starts with Thai vowel/tail — prefix was eaten)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '\s[ิ-ูเ-ไ็่้๊๋์ํ]'
    AND full_name_th ~ '(ดร\.|ศ\.|รศ\.|ผศ\.)'
""")
n = cur.fetchone()[0]
print(f"  {n} rows where name segment starts with a Thai combining char (possible ดร-mangle)")
if n:
    cur.execute(r"""
        SELECT id, full_name_th, university_th FROM faculties
        WHERE full_name_th ~ '\s[ิ-ูเ-ไ็่้๊๋์ํ]'
        AND full_name_th ~ '(ดร\.|ศ\.|รศ\.|ผศ\.)'
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 4. full_name_th with contact/address keywords ─────────────────────
print("\n[4] Contact/address boilerplate in full_name_th")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~* '(สถานที่ติดต่อ|ที่อยู่|ติดต่อได้ที่|โทรศัพท์|โทรสาร|เบอร์|อาคาร|ชั้น|ห้อง|ตึก)'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE full_name_th ~* '(สถานที่ติดต่อ|ที่อยู่|ติดต่อได้ที่|โทรศัพท์|โทรสาร|เบอร์|อาคาร|ชั้น|ห้อง|ตึก)'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 5. Download links in education / research_interests ───────────────
print("\n[5] Download links or file paths in education / research_interests JSON")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE education::text ~* '\.(pdf|docx?|xlsx?|pptx?|zip)\b'
    OR research_interests::text ~* '\.(pdf|docx?|xlsx?|pptx?|zip)\b'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE education::text ~* '\.(pdf|docx?|xlsx?|pptx?|zip)\b'
        OR research_interests::text ~* '\.(pdf|docx?|xlsx?|pptx?|zip)\b'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 6. Phone numbers in education / research_interests ────────────────
print("\n[6] Phone numbers in education / research_interests JSON (PDPA)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE education::text ~ '0[2689][0-9\-]{7,}'
    OR research_interests::text ~ '0[2689][0-9\-]{7,}'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th, education, research_interests FROM faculties
        WHERE education::text ~ '0[2689][0-9\-]{7,}'
        OR research_interests::text ~ '0[2689][0-9\-]{7,}'
        LIMIT 5
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}")
        print(f"      edu: {str(r[2])[:150]}")
        print(f"      res: {str(r[3])[:150]}")

# ── 7. Glued professional sub-title (ภก./ภญ./นพ./พญ. no space before name) ──
print("\n[7] Glued professional sub-title in full_name_th (e.g. 'ดร. ภก.ชื่อ' no space)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.)[ก-๙A-Za-z]'
""")
n = cur.fetchone()[0]
print(f"  {n} rows")
if n:
    cur.execute(r"""
        SELECT id, full_name_th FROM faculties
        WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.)[ก-๙A-Za-z]'
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[1]!r}")

# ── 8. embedding_text diverges from current full_name_th ──────────────
print("\n[8] embedding_text does not contain current full_name_th (stale after name fixes)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL
    AND embedding_text IS NOT NULL
    AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
n = cur.fetchone()[0]
print(f"  {n} rows where embedding_text is stale vs full_name_th")

# ── 9. university_th values with stray ASCII symbols or digits ─────────
print("\n[9] Stray symbols/digits in university_th / faculty_th")
cur.execute(r"""
    SELECT university_th, COUNT(*) FROM faculties
    WHERE university_th ~ '[0-9@#$%^&*()_+=\[\]{}|\\<>]'
    GROUP BY university_th ORDER BY COUNT(*) DESC LIMIT 10
""")
rows = cur.fetchall()
print(f"  university_th with symbols: {len(rows)} distinct values")
for r in rows:
    print(f"    {r[1]:5d}  {r[0]!r}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE faculty_th ~ '[0-9@#$%^&*()_+=\[\]{}|\\<>]'
""")
print(f"  faculty_th with symbols: {cur.fetchone()[0]}")

# ── 10. research_interests items that are too long (boilerplate paragraphs) ──
print("\n[10] Abnormally long research_interest items (>200 chars — likely full paragraphs)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties, jsonb_array_elements_text(research_interests::jsonb) as item
    WHERE length(item) > 200
""")
n = cur.fetchone()[0]
print(f"  {n} interest items >200 chars")
if n:
    cur.execute(r"""
        SELECT f.id, f.full_name_th, item
        FROM faculties f, jsonb_array_elements_text(f.research_interests::jsonb) as item
        WHERE length(item) > 200
        LIMIT 5
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  item={r[2][:120]!r}")

# ── 11. education items containing raw scraped text (office hours, etc.) ──
print("\n[11] Education items containing scraped sidebar text keywords")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties, jsonb_array_elements_text(education::jsonb) as item
    WHERE item ~* '(office hour|consultation|โทร\.|เบอร์|office:|room:|ห้อง:|อาคาร:|www\.|http)'
""")
n = cur.fetchone()[0]
print(f"  {n} education items with sidebar/contact text")
if n:
    cur.execute(r"""
        SELECT f.id, f.full_name_th, item
        FROM faculties f, jsonb_array_elements_text(f.education::jsonb) as item
        WHERE item ~* '(office hour|consultation|โทร\.|เบอร์|office:|room:|ห้อง:|อาคาร:|www\.|http)'
        LIMIT 8
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  {r[2]!r}")

# ── 12. first_name = single letter or initials only ───────────────────
print("\n[12] first_name is a single character or initials only (G, J., etc.)")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE first_name IS NOT NULL
    AND first_name ~ '^[A-Za-z]\.?$'
""")
n = cur.fetchone()[0]
print(f"  {n} rows with single-char first_name")
if n:
    cur.execute(r"""
        SELECT id, first_name, last_name, full_name_th, university_th FROM faculties
        WHERE first_name IS NOT NULL AND first_name ~ '^[A-Za-z]\.?$'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:45s}  first={r[1]!r}  last={r[2]!r}  full={r[3]!r}")

conn.close()
print("\n[Round 3 scan complete]")
