# -*- coding: utf-8 -*-
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/advisor_match')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT id, title_th, university_th, faculty_th
    FROM courses
    WHERE university_th = 'มหาวิทยาลัยสงขลานครินทร์' AND faculty_th ILIKE '%ทันต%'
""")
rows = cur.fetchall()
print(f"PSU Dent Courses ({len(rows)}):")
for r in rows:
    print(" ", r)

cur.execute("""
    SELECT id, title_th, university_th, faculty_th
    FROM courses
    WHERE university_th = 'มหาวิทยาลัยศรีนครินทรวิโรฒ' AND faculty_th ILIKE '%มนุษย%'
""")
rows2 = cur.fetchall()
print(f"\nSWU Humanities Courses ({len(rows2)}):")
for r in rows2:
    print(" ", r)

conn.close()
