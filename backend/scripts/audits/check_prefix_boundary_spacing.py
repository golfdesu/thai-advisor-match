import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

cur.execute(r"""
    SELECT full_name_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|ดร\.)[ก-๙]'
    LIMIT 20
""")
for r in cur.fetchall():
    print(repr(r[0]))

# Also show if there are remaining double-prefix rows that need attention
print("\n--- Rows with double สพ.ญ. (true double prefix) ---")
cur.execute(r"""
    SELECT full_name_th FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
    LIMIT 10
""")
for r in cur.fetchall():
    print(repr(r[0]))

conn.close()
