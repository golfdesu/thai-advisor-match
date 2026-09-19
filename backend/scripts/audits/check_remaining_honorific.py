import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '(นายแพทย์|แพทย์หญิง|สัตวแพทย์(?:หญิง)?|ทันตแพทย์(?:หญิง)?)'
""")
for r in cur.fetchall():
    print(f"  title={r[2]!r:20s}  name={r[1]!r}")
conn.close()
