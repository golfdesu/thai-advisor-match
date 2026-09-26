# -*- coding: utf-8 -*-
import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@db:5432/advisor_match')
cur = conn.cursor()

# 1. Duplicate email clusters
cur.execute('''
    SELECT lower(email), COUNT(*), array_agg(id), array_agg(full_name_th)
    FROM faculties
    WHERE email IS NOT NULL AND email != ''
    GROUP BY lower(email)
    HAVING COUNT(*) > 1
''')
print('=== DUPLICATE EMAILS ===')
for row in cur.fetchall():
    print(row)

# 2. Credential Suffix Leaks
suffixes = ['ph.d', 'm.sc', 'b.sc', 'm.eng', 'b.eng', 'd.eng', 'ed.d', 'cert.', 'm.d.', 'diplomate', 'fellow', 'd.d.s', 'm.a.', 'b.a.']
conds = ' OR '.join([f"lower(last_name) LIKE '%{s}%'" for s in suffixes])
cur.execute(f'''
    SELECT id, first_name, last_name, full_name_th, university_th
    FROM faculties
    WHERE {conds}
''')
print('\n=== CREDENTIAL SUFFIX LEAKS ===')
for row in cur.fetchall():
    print(row)

conn.close()
