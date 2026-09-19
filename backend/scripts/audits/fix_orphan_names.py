import psycopg2, re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

# Check the orphaned row
cur.execute("SELECT id, full_name_th, first_name, last_name, academic_title_th FROM faculties WHERE id = 'ku_forest_wave15_0124'")
row = cur.fetchone()
print("Orphaned row:", row)

# Rebuild from first_name + last_name if available
if row:
    rid, name_th, fn, ln, title = row
    if fn or ln:
        rebuilt = (title or "") + " " + ((fn or "") + " " + (ln or "")).strip()
        rebuilt = rebuilt.strip()
        cur.execute("UPDATE faculties SET full_name_th = %s WHERE id = %s", (rebuilt, rid))
        conn.commit()
        print(f"Rebuilt to: {rebuilt!r}")
    else:
        print("No first/last name to rebuild from — leaving as-is")

# Check for any other title-only full_name_th
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*$'
""")
print("Rows with title-only full_name_th:", cur.fetchone()[0])

cur.execute(r"""
    SELECT id, full_name_th, first_name, last_name FROM faculties
    WHERE full_name_th ~ '^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*$'
    LIMIT 10
""")
for r in cur.fetchall():
    print(" ", r)

# Rebuild remaining 3 title-only rows
cur.execute(r"""
    SELECT id, academic_title_th, first_name, last_name FROM faculties
    WHERE full_name_th ~ '^(ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.)\s*$'
""")
rows = cur.fetchall()
print("Remaining title-only rows to rebuild:", len(rows))
for rid, title, fn, ln in rows:
    name = ((fn or "") + " " + (ln or "")).strip()
    rebuilt = ((title or "") + " " + name).strip()
    cur.execute("UPDATE faculties SET full_name_th = %s WHERE id = %s", (rebuilt, rid))
    print(f"  {rid} -> {rebuilt!r}")
conn.commit()

conn.close()
print("Done.")
