import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

# All 8 split-surname rows
cur.execute(r"""
    SELECT id, academic_title_th, first_name, last_name, full_name_th, university_th
    FROM faculties
    WHERE last_name ~ '[ก-๙]{4,}\s+[ก-๙]{4,}'
    ORDER BY id
""")
print("=== Split-surname rows ===")
for r in cur.fetchall():
    print(f"  id          : {r[0]}")
    print(f"  title       : {r[1]!r}")
    print(f"  first_name  : {r[2]!r}")
    print(f"  last_name   : {r[3]!r}")
    print(f"  full_name_th: {r[4]!r}")
    print(f"  university  : {r[5]}")
    print()

# Truncated name row
cur.execute("""
    SELECT id, academic_title_th, first_name, last_name, full_name_th
    FROM faculties WHERE id = 'chulalongk_facultyofa_sri_024'
""")
print("=== Truncated name row ===")
r = cur.fetchone()
if r:
    print(f"  id          : {r[0]}")
    print(f"  title       : {r[1]!r}")
    print(f"  first_name  : {r[2]!r}")
    print(f"  last_name   : {r[3]!r}")
    print(f"  full_name_th: {r[4]!r}")

# Duplicate openalex_id pairs
print()
print("=== Duplicate openalex_id pairs ===")
for oa_id in ["https://openalex.org/A5014426991", "https://openalex.org/A5026104752"]:
    cur.execute("""
        SELECT id, full_name_th, university_th, total_citations, h_index
        FROM faculties WHERE openalex_id = %s
    """, (oa_id,))
    rows = cur.fetchall()
    print(f"  openalex_id: {oa_id}")
    for r in rows:
        print(f"    {r[0]:45s}  name={r[1]!r}  cit={r[3]}  h={r[4]}")
    print()

conn.close()
