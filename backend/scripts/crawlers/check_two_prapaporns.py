# -*- coding: utf-8 -*-
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/advisor_match')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT id, full_name_th, first_name, last_name, email, profile_url, university_th, faculty_th
    FROM faculties
    WHERE id = 'swu_pharm_001'
""")
print('swu_pharm_001:', cur.fetchone())

cur.execute("""
    SELECT id, full_name_th, first_name, last_name, email, profile_url, university_th, faculty_th
    FROM faculties
    WHERE id = 'swu_hum_naprapha_2f06f2'
""")
print('swu_hum_naprapha_2f06f2:', cur.fetchone())

conn.close()
