import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC")).fetchall()
    print(f"DB total {conn.execute(text('SELECT count(*) FROM courses')).scalar()}")
    for r in rows:
        print(f"{r[0][:50]:50} {r[1]:3}")
    print("--- official targets vs current ---")
    targets={
        'Chiang Mai University':334,
        'Chulalongkorn University':456,
        'Mahidol University':629,
        'Mae Fah Luang University':70,
        'Suranaree University of Technology':100,
        'National Institute of Development Administration':45,
        'Thammasat University':200,
        'Kasetsart University':200,
        'Khon Kaen University':200,
        'Prince of Songkla University':150,
        'Burapha University':150,
        'Srinakharinwirot University':200,
        'Silpakorn University':150,
    }
    for uni, target in targets.items():
        cur=conn.execute(text(f"SELECT count(*) FROM courses WHERE university='{uni}'")).scalar()
        diff=target-cur
        status="Missing" if diff>0 else "Exceeds" if diff<0 else "Complete"
        print(f"{uni[:32]:32} cur {cur:3} / target {target:3} diff {diff:+4} {status}")
    # also list universities with 0 or <20
    low=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university HAVING count(*) < 30 ORDER BY count(*)")).fetchall()
    print("\nLow count (<30) universities:")
    for r in low:
        print(f"  {r[0][:40]:40} {r[1]}")
