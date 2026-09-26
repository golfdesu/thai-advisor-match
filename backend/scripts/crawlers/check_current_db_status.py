# -*- coding: utf-8 -*-
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/advisor_match')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT count(*), count(embedding)
    FROM faculties
    WHERE university_th = 'มหาวิทยาลัยสงขลานครินทร์' AND faculty_th ILIKE '%ทันต%'
""")
print('PSU Dent (total, with embedding):', cur.fetchone())

cur.execute("""
    SELECT count(*), count(embedding)
    FROM faculties
    WHERE university_th = 'มหาวิทยาลัยศรีนครินทรวิโรฒ' AND faculty_th ILIKE '%มนุษย%'
""")
print('SWU Humanities (total, with embedding):', cur.fetchone())

cur.execute("""
    SELECT count(*)
    FROM faculties
    WHERE embedding IS NULL
""")
print('Total missing embeddings across whole DB:', cur.fetchone())

conn.close()
