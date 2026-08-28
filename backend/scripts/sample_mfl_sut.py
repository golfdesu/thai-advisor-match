import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    for uni in ['Mae Fah Luang University','Suranaree University of Technology']:
        print(f"== {uni} ==")
        rows=conn.execute(text(f"SELECT title_th, degree_level FROM courses WHERE university='{uni}' LIMIT 5")).fetchall()
        for r in rows:
            print(f"  {r[1]:12} | {r[0][:55]}")
        cnt=conn.execute(text(f"SELECT count(*) FROM courses WHERE university='{uni}'")).scalar()
        print(f"  total {cnt}")
        print()
