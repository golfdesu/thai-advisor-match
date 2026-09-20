# -*- coding: utf-8 -*-
import psycopg2
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/advisor_match")
cur = conn.cursor()

cur.execute("""
    SELECT id, full_name_th, department_th, email, academic_title_th, profile_url
    FROM faculties
    WHERE university_th = 'มหาวิทยาลัยเชียงใหม่'
      AND faculty_th = 'คณะแพทยศาสตร์'
      AND (first_name IS NULL OR first_name = '' OR first_name = full_name_th)
    ORDER BY department_th, full_name_th;
""")

rows = cur.fetchall()
cur.close()
conn.close()

data = []
for r in rows:
    data.append({
        "id": r[0],
        "full_name_th": r[1],
        "department_th": r[2],
        "email": r[3],
        "academic_title_th": r[4],
        "profile_url": r[5]
    })

print(f"Exported {len(data)} CMU Medicine raw records")
with open('cmu_med_raw.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
