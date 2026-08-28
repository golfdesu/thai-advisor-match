import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    # inspect MFL english BA duplicates
    rows=conn.execute(text("SELECT id, title_th, title_en, degree_level, faculty_th, program_type FROM courses WHERE university='Mae Fah Luang University' AND title_th='หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษ'")).fetchall()
    print(f"MFL English BA duplicates: {len(rows)}")
    for r in rows:
        print(f"  id={r[0]} degree={r[3]} faculty={r[4]} program={r[5]}")
        print(f"    th={r[1][:50]} en={r[2][:50]}")
    print()
    # check CMU periodontology duplicates
    rows=conn.execute(text("SELECT id, title_th, degree_level, faculty_th FROM courses WHERE university='Chiang Mai University' AND title_th='หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาปริทันตวิทยา'")).fetchall()
    print(f"CMU periodontology duplicates: {len(rows)}")
    for r in rows:
        print(r)
    print()
    # overall duplicate grouping by title_th alone vs title_th+degree
    for uni in ['Mae Fah Luang University','Suranaree University of Technology','Chiang Mai University']:
        rows=conn.execute(text(f"SELECT count(*) FROM courses WHERE university='{uni}'")).scalar()
        distinct_th=conn.execute(text(f"SELECT count(DISTINCT title_th) FROM courses WHERE university='{uni}'")).scalar()
        # group by title_th only
        dup_groups=conn.execute(text(f"SELECT count(*) FROM (SELECT title_th FROM courses WHERE university='{uni}' GROUP BY title_th HAVING count(*)>1) t")).scalar()
        # group by title_th+degree
        dup_groups2=conn.execute(text(f"SELECT count(*) FROM (SELECT title_th, degree_level FROM courses WHERE university='{uni}' GROUP BY title_th, degree_level HAVING count(*)>1) t")).scalar()
        print(f"{uni[:15]} total={rows} distinct_th={distinct_th} groups_dup_title_only={dup_groups} groups_dup_title+degree={dup_groups2}")
