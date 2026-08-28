import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    print('CU', conn.execute(text("SELECT count(*) FROM courses WHERE university='Chulalongkorn University'")).scalar())
    print('MU', conn.execute(text("SELECT count(*) FROM courses WHERE university='Mahidol University'")).scalar())
    print('total', conn.execute(text("SELECT count(*) FROM courses")).scalar())
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC LIMIT 10")).fetchall()
    for r in rows:
        print(r)
