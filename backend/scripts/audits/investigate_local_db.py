"""
Local PostgreSQL string bug investigation.
Run: python backend/scripts/audits/investigate_local_db.py
"""
import psycopg2
import re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("LOCAL DB AUDIT — advisor_match")
print("=" * 60)

# ── Inventory ──────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM faculties")
fac_total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM courses")
crs_total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM research_labs")
lab_total = cur.fetchone()[0]
print(f"\n[Inventory]")
print(f"  Faculty : {fac_total:,}")
print(f"  Courses : {crs_total:,}")
print(f"  Labs    : {lab_total:,}")

# ── Missing embeddings ─────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM faculties WHERE embedding IS NULL")
miss_emb_fac = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM courses WHERE embedding IS NULL")
miss_emb_crs = cur.fetchone()[0]
print(f"\n[Embeddings]")
print(f"  Missing faculty embeddings : {miss_emb_fac}")
print(f"  Missing course embeddings  : {miss_emb_crs}")

# ── Mixed-script corruption ────────────────────────────────
# Thai range U+0E00–U+0E7F, ASCII printable, common punctuation
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL
    AND full_name_th ~ '[^\x00-\x7F฀-๿ \-\.\,\(\)\:\|\/]'
""")
mixed_script = cur.fetchone()[0]
print(f"\n[String Bugs]")
print(f"  Mixed-script corrupted full_name_th : {mixed_script}")

# ── Empty-string emails ────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM faculties WHERE email = ''")
empty_email = cur.fetchone()[0]
print(f"  Empty-string emails (should be NULL): {empty_email}")

# ── Invalid email TLD ──────────────────────────────────────
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE email IS NOT NULL AND email != ''
    AND email !~ '^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
""")
bad_email = cur.fetchone()[0]
print(f"  Invalid email format                : {bad_email}")

# ── Double-title mangling ──────────────────────────────────
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^อ\. (Dr\.|Assoc\.|Associate|Prof\.)'
    AND academic_title_th = 'อ.'
""")
double_title = cur.fetchone()[0]
print(f"  Double-title prefix (อ. Dr./Prof.)  : {double_title}")

# ── Foreign faculty with Thai อ. prefix ───────────────────
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE academic_title_th = 'อ.'
    AND first_name ~ '^[A-Za-z]'
    AND last_name ~ '^[A-Za-z]'
    AND full_name_th LIKE 'อ. %'
    AND full_name_th !~ '[ก-๙]'
""")
foreign_thai_prefix = cur.fetchone()[0]
print(f"  Foreign (Latin) names with อ. prefix: {foreign_thai_prefix}")

# ── Boilerplate / non-person names ────────────────────────
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~* 'สาขา|ภาควิชา|คณะ|สำนักงาน|ศูนย์|ห้องปฏิบัติการ|วิทยาลัย'
    OR full_name_th ~* '(Department|Faculty|School|College|Institute|Center|Office|Group|Laboratory)'
""")
boilerplate = cur.fetchone()[0]
print(f"  Boilerplate/non-person in full_name_th: {boilerplate}")

# ── Duplicate name+university pairs ───────────────────────
cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT full_name_th, university_th, COUNT(*) as cnt
        FROM faculties
        GROUP BY full_name_th, university_th
        HAVING COUNT(*) > 1
    ) d
""")
dup_pairs = cur.fetchone()[0]
print(f"  Duplicate name+university pairs     : {dup_pairs}")

# ── Sample mixed-script rows ───────────────────────────────
cur.execute(r"""
    SELECT id, full_name_th, university_th
    FROM faculties
    WHERE full_name_th IS NOT NULL
    AND full_name_th ~ '[^\x00-\x7F฀-๿ \-\.\,\(\)\:\|\/]'
    ORDER BY id
    LIMIT 20
""")
rows = cur.fetchall()
if rows:
    print(f"\n[Sample mixed-script corrupted rows]")
    for r in rows:
        print(f"  {r[0]:50s}  {r[1]}")

# ── Sample double-title rows ───────────────────────────────
cur.execute(r"""
    SELECT id, full_name_th, university_th
    FROM faculties
    WHERE full_name_th ~ '^อ\. (Dr\.|Assoc\.|Associate|Prof\.)'
    AND academic_title_th = 'อ.'
    LIMIT 15
""")
rows2 = cur.fetchall()
if rows2:
    print(f"\n[Sample double-title rows]")
    for r in rows2:
        print(f"  {r[0]:50s}  {r[1]}")

# ── Sample boilerplate names ───────────────────────────────
cur.execute(r"""
    SELECT id, full_name_th, university_th
    FROM faculties
    WHERE full_name_th ~* 'สาขา|ภาควิชา|คณะ|สำนักงาน|ศูนย์|ห้องปฏิบัติการ|วิทยาลัย'
    OR full_name_th ~* '(Department|Faculty|School|College|Institute|Center|Office|Group|Laboratory)'
    LIMIT 20
""")
rows3 = cur.fetchall()
if rows3:
    print(f"\n[Sample boilerplate names]")
    for r in rows3:
        print(f"  {r[0]:50s}  {r[1]}")

# ── Sample invalid emails ──────────────────────────────────
cur.execute(r"""
    SELECT id, email, full_name_th
    FROM faculties
    WHERE email IS NOT NULL AND email != ''
    AND email !~ '^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    LIMIT 20
""")
rows4 = cur.fetchall()
if rows4:
    print(f"\n[Sample invalid emails]")
    for r in rows4:
        print(f"  {r[0]:40s}  email={r[1]!r}")

conn.close()
print("\n[Done]")
