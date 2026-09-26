# -*- coding: utf-8 -*-
import psycopg2
import os

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/advisor_match')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    UPDATE faculties
    SET email = NULL
    WHERE id = 'swu_hum_naprapha_2f06f2'
""")
conn.commit()
print("Updated swu_hum_naprapha_2f06f2 email to NULL")

conn.close()
