import psycopg2, re
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

print('=== Glued sub-title (dot+Thai char, no space) ===')
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ\.)[ก-๙]'
    LIMIT 30
""")
rows = cur.fetchall()
print(f'Count: {len(rows)}')
for r in rows:
    print(f'  {r[1]!r}')

print()
print('=== Double professional prefix ===')
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|นายแพทย์|แพทย์หญิง|ดร\.)'
    LIMIT 30
""")
rows2 = cur.fetchall()
print(f'Count: {len(rows2)}')
for r in rows2:
    print(f'  title={r[2]!r:25s}  name={r[1]!r}')
conn.close()
