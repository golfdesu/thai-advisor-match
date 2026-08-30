import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
from collections import defaultdict
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)

def is_international(rec):
    pt=(rec[6] or "") + " " + (rec[1] or "") + " " + (rec[2] or "")
    pt_low=pt.lower()
    return ("นานาชาติ" in pt) or ("international" in pt_low)

# Audit before
with engine.connect() as conn:
    total_before=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"Total before: {total_before}")
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC LIMIT 15")).fetchall()
    for r in rows:
        print(f"  {r[0][:40]:40} {r[1]}")

# Build groups: (university, title_th)
with engine.connect() as conn:
    all_rows=conn.execute(text("SELECT id, title_th, title_en, degree_level, university, program_type, faculty_th FROM courses ORDER BY university, title_th, id")).fetchall()
    # group
    groups=defaultdict(list)
    for r in all_rows:
        key=(r[4], r[1])  # university, title_th
        groups[key].append(r)

    to_keep_ids=set()
    to_delete_ids=[]
    for key, recs in groups.items():
        if len(recs)==1:
            to_keep_ids.add(recs[0][0])
            continue
        # split into international vs regular
        intl=[r for r in recs if is_international(r)]
        regular=[r for r in recs if not is_international(r)]
        # keep one international (earliest id) if exists
        if intl:
            keep_intl=sorted(intl, key=lambda x: x[0])[0]
            to_keep_ids.add(keep_intl[0])
            # rest intl are duplicates to delete
            for r in intl:
                if r[0]!=keep_intl[0]:
                    to_delete_ids.append(r[0])
        if regular:
            keep_reg=sorted(regular, key=lambda x: x[0])[0]
            to_keep_ids.add(keep_reg[0])
            for r in regular:
                if r[0]!=keep_reg[0]:
                    to_delete_ids.append(r[0])
        # if group had only intl or only regular, we keep 1, already handled
        # if group has both intl and regular, we keep 2

    print(f"\nGroups total: {len(groups)}")
    print(f"Keep: {len(to_keep_ids)}, Delete: {len(to_delete_ids)}")
    # show example groups with >2
    for key, recs in groups.items():
        if len(recs)>2:
            uni, title=key
            if len(recs)<=5:
                print(f"  {uni[:20]:20} | {title[:40]:40} | {len(recs)} -> keep {1 if len([r for r in recs if is_international(r)])>0 else 0} intl + {1 if len([r for r in recs if not is_international(r)])>0 else 0} reg = {len(to_keep_ids & set([r[0] for r in recs]))} keep, delete {len([r for r in recs if r[0] in to_delete_ids])}")

# Execute deletion
if to_delete_ids:
    with engine.begin() as conn:
        batch=500
        deleted=0
        for i in range(0, len(to_delete_ids), batch):
            chunk=to_delete_ids[i:i+batch]
            placeholders=",".join(["'" + x.replace("'", "''") + "'" for x in chunk])
            res=conn.execute(text(f"DELETE FROM courses WHERE id IN ({placeholders})"))
            deleted+=res.rowcount
            print(f"Deleted batch {i//batch+1}: {res.rowcount}")
        print(f"Total deleted: {deleted}")
else:
    print("No deletes")

# After
with engine.connect() as conn:
    total_after=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"\nTotal after: {total_after} (removed {total_before - total_after})")
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC LIMIT 15")).fetchall()
    for r in rows:
        print(f"  {r[0][:40]:40} {r[1]}")
    # check CMU EE again
    rows=conn.execute(text("SELECT id, title_th, program_type FROM courses WHERE university='Chiang Mai University' AND title_th LIKE '%ไฟฟ้า%'")).fetchall()
    print(f"\nCMU EE after: {len(rows)}")
    for r in rows:
        print(f"  {r[0]:30} {r[2]:30} {r[1][:45]}")
