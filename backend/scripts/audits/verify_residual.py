import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

# Show the actual academic_title_th for residual rows to confirm they are correct
cur.execute(r"""
    SELECT full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|นายแพทย์|ดร\.)'
""")
rows = cur.fetchall()
print(f"Rows flagged by check: {len(rows)}")
for r in rows:
    name = r[0]
    title = r[1]
    # Check if this looks like a duplicate — does the name have the title pattern repeated?
    # A correct name is: acad.prof. dr. <firstname> <lastname>
    # A duplicate would be: acad.prof. dr. acad. prof. dr. <name>
    import re
    # Count how many times an academic prefix appears
    acad_count = len(re.findall(r'(?:ศ|รศ|ผศ|อ)\.', name))
    prof_count = len(re.findall(r'(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|สพ|ทนพ|ทญ)\.', name))
    status = "POSSIBLE_DUP" if (acad_count > 1 or prof_count > 1) else "OK"
    print(f"  [{status}] title={title!r:20s}  name={name!r}")

conn.close()
