# -*- coding: utf-8 -*-
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/advisor_match')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT email, count(*), string_agg(id, ', '), string_agg(full_name_th, ', ')
    FROM faculties
    WHERE email IS NOT NULL AND email != ''
    GROUP BY email
    HAVING count(*) > 1
""")
rows = cur.fetchall()
print(f"Duplicate email clusters ({len(rows)}):")
for r in rows:
    print(" ", r)

conn.close()
