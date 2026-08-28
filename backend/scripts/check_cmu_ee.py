import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    # CMU Electrical Engineering total
    rows=conn.execute(text("SELECT id, title_th, title_en, degree_level, degree_name, department_th, program_type, total_credits FROM courses WHERE university='Chiang Mai University' AND (faculty_th LIKE '%วิศวกรรมศาสตร์%' OR faculty LIKE '%Engineering%') AND (department_th LIKE '%ไฟฟ้า%' OR department LIKE '%Electrical%' OR title_th LIKE '%ไฟฟ้า%' OR title_en LIKE '%Electrical%') ORDER BY degree_level, title_th")).fetchall()
    print(f"CMU EE matched: {len(rows)}")
    for r in rows:
        print(f"  {r[0]:30} | {r[3]:10} | {r[4]:20} | {r[1][:50]}")
        print(f"    EN: {r[2][:60]} | dept: {r[5]} | type: {r[6]} | credits: {r[7]}")
    print()
    # Also count all CMU Engineering
    rows2=conn.execute(text("SELECT degree_level, count(*) FROM courses WHERE university='Chiang Mai University' AND faculty_th LIKE '%วิศวกรรมศาสตร์%' GROUP BY degree_level")).fetchall()
    print("CMU Engineering by degree:", rows2)
    # All CMU by faculty
    rows3=conn.execute(text("SELECT faculty_th, count(*) FROM courses WHERE university='Chiang Mai University' GROUP BY faculty_th ORDER BY count(*) DESC LIMIT 10")).fetchall()
    print("CMU top faculties:")
    for r in rows3:
        print(f"  {r[0][:40]:40} {r[1]}")
    # Check duplicate EE title
    rows4=conn.execute(text("SELECT title_th, count(*) as c FROM courses WHERE university='Chiang Mai University' AND (title_th LIKE '%ไฟฟ้า%') GROUP BY title_th HAVING count(*)>1")).fetchall()
    print(f"Duplicate EE titles: {rows4}")
