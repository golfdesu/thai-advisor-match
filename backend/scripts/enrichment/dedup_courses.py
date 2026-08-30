"""
Deduplicate courses by (university, title_th, degree_level, faculty_th)
Keep earliest id (MIN) per group, delete others.
Reports per university.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)

# First audit
with engine.connect() as conn:
    rows=conn.execute(text("SELECT university, count(*) as total, count(DISTINCT title_th) as distinct_th FROM courses GROUP BY university ORDER BY total DESC")).fetchall()
    print("Before dedup:")
    for r in rows[:15]:
        print(f"  {r[0][:40]:40} total={r[1]:4} distinct_title_th={r[2]:4} dup={r[1]-r[2]:3}")
    total_before=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"Total before: {total_before}")

# Dedup: for each (university, title_th) group with >1, keep one with smallest id (lexicographically)
# To be safe, group by university + title_th only, keep MIN(id)
# If same title but different degree/faculty, it's likely still duplicate per earlier audit (degree same), but we keep conservative: only dedup exact title_th match
with engine.begin() as conn:
    # Find duplicates to delete: all ids except MIN(id) per (university, title_th)
    # Use window or subquery: collect ids to delete
    to_delete = conn.execute(text("""
        SELECT c.id FROM courses c
        JOIN (
            SELECT university, title_th, MIN(id) as keep_id
            FROM courses
            GROUP BY university, title_th
            HAVING count(*) > 1
        ) keep ON c.university = keep.university AND c.title_th = keep.title_th AND c.id != keep.keep_id
    """)).fetchall()
    delete_ids = [r[0] for r in to_delete]
    print(f"\nFound {len(delete_ids)} duplicate rows to delete (exact title_th match)")
    if delete_ids:
        # Delete in batches of 500 to avoid huge IN clause
        batch_size = 500
        deleted = 0
        for i in range(0, len(delete_ids), batch_size):
            batch = delete_ids[i:i+batch_size]
            placeholders = ",".join(["'" + x.replace("'", "''") + "'" for x in batch])
            res = conn.execute(text(f"DELETE FROM courses WHERE id IN ({placeholders})"))
            deleted += res.rowcount
            print(f"  deleted batch {i//batch_size+1}: {res.rowcount} rows")
        print(f"Total deleted: {deleted}")
    else:
        print("No duplicates found")

# After audit
with engine.connect() as conn:
    rows=conn.execute(text("SELECT university, count(*) as total, count(DISTINCT title_th) as distinct_th FROM courses GROUP BY university ORDER BY total DESC LIMIT 15")).fetchall()
    print("\nAfter dedup:")
    for r in rows[:15]:
        print(f"  {r[0][:40]:40} total={r[1]:4} distinct_title_th={r[2]:4}")
    total_after=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"Total after: {total_after} (removed {total_before - total_after})")
