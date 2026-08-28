import io, sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    for uni in ['Mae Fah Luang University','Suranaree University of Technology','Chiang Mai University','Chulalongkorn University','Mahidol University']:
        total=conn.execute(text(f"SELECT count(*) FROM courses WHERE university='{uni}'")).scalar()
        distinct_id=conn.execute(text(f"SELECT count(DISTINCT id) FROM courses WHERE university='{uni}'")).scalar()
        distinct_title=conn.execute(text(f"SELECT count(DISTINCT title_th) FROM courses WHERE university='{uni}'")).scalar()
        distinct_en=conn.execute(text(f"SELECT count(DISTINCT title_en) FROM courses WHERE university='{uni}'")).scalar()
        print(f"{uni[:30]:30} total={total:4} distinct_id={distinct_id:4} distinct_title_th={distinct_title:4} distinct_title_en={distinct_en:4}")
        # sample 3 titles
        rows=conn.execute(text(f"SELECT id, title_th, degree_level FROM courses WHERE university='{uni}' LIMIT 3")).fetchall()
        for r in rows:
            print(f"  - {r[0]:30} {r[2]:10} {r[1][:45]}")
        print()
    # check MFL duplicate titles
    rows=conn.execute(text("SELECT title_th, count(*) as c FROM courses WHERE university='Mae Fah Luang University' GROUP BY title_th HAVING count(*) > 1 ORDER BY c DESC LIMIT 5")).fetchall()
    print("MFL duplicate titles:", rows)
    rows=conn.execute(text("SELECT title_th, count(*) as c FROM courses WHERE university='Chiang Mai University' GROUP BY title_th HAVING count(*) > 1 ORDER BY c DESC LIMIT 5")).fetchall()
    print("CMU duplicate titles:", rows)
