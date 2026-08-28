import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)

# Step 1: Purge UUID synthetic
with engine.begin() as conn:
    total_before=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"Total before purge: {total_before}")
    # Count UUID
    rows=conn.execute(text("SELECT id FROM courses")).fetchall()
    uuid_pat=re.compile(r'_[0-9a-f]{6}$')
    to_delete=[r[0] for r in rows if uuid_pat.search(r[0])]
    print(f"UUID to delete: {len(to_delete)}")
    # Delete in batches
    batch=500
    deleted=0
    for i in range(0, len(to_delete), batch):
        chunk=to_delete[i:i+batch]
        placeholders=",".join(["'" + x.replace("'", "''") + "'" for x in chunk])
        res=conn.execute(text(f"DELETE FROM courses WHERE id IN ({placeholders})"))
        deleted+=res.rowcount
        print(f"  deleted batch {i//batch+1}: {res.rowcount}")
    print(f"Deleted UUID total: {deleted}")

with engine.connect() as conn:
    total_after=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"\nTotal after purge: {total_after} (removed {total_before - total_after})")
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC LIMIT 15")).fetchall()
    print("Remaining after purge:")
    for r in rows:
        print(f"  {r[0][:40]:40} {r[1]}")
    # Check NIDA bachelor still exists
    nida_bach=conn.execute(text("SELECT count(*) FROM courses WHERE university='National Institute of Development Administration' AND degree_level='ปริญญาตรี'")).scalar()
    print(f"NIDA bachelor remaining: {nida_bach}")
    nida_total=conn.execute(text("SELECT count(*) FROM courses WHERE university='National Institute of Development Administration'")).scalar()
    print(f"NIDA total remaining: {nida_total}")
