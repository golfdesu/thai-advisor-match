import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
from collections import defaultdict

try:
    from rapidfuzz import fuzz
    HAS_FUZZ=True
except:
    HAS_FUZZ=False
    print("rapidfuzz not available, need to pip install")
    sys.exit(1)

env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)

def normalize_title(t):
    if not t:
        return ""
    t=re.sub(r'\(.*?\)', '', t)
    t=re.sub(r'\[.*?\]', '', t)
    t=re.sub(r'\s+', ' ', t).strip()
    return t

THRESHOLD=96  # only merge near-identical (1-2 char diff), to avoid merging distinct majors

with engine.connect() as conn:
    total_before=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"Total before fuzzy: {total_before}")
    rows=conn.execute(text("SELECT id, title_th, degree_level, university, program_type FROM courses ORDER BY university, degree_level, title_th")).fetchall()
    # group by university+degree
    from collections import defaultdict
    uni_degree_groups=defaultdict(list)
    for r in rows:
        key=(r[3], r[2])  # university, degree_level
        uni_degree_groups[key].append(r)

    to_delete_ids=set()
    kept_groups=0
    # For each university+degree, cluster titles
    for (uni, deg), recs in uni_degree_groups.items():
        # Build list of normalized titles
        norm_map={}
        for r in recs:
            norm=normalize_title(r[1])
            norm_map[r[0]]=(norm, r)
        # Sort by norm length to compare efficiently
        sorted_recs=sorted(recs, key=lambda x: normalize_title(x[1]))
        # Use simple O(n^2) but n per uni+degree is small (max ~200)
        visited=set()
        for i in range(len(sorted_recs)):
            id_i, title_i, deg_i, uni_i, pt_i = sorted_recs[i]
            if id_i in visited or id_i in to_delete_ids:
                continue
            norm_i=normalize_title(title_i)
            for j in range(i+1, len(sorted_recs)):
                id_j, title_j, deg_j, uni_j, pt_j = sorted_recs[j]
                if id_j in visited or id_j in to_delete_ids:
                    continue
                norm_j=normalize_title(title_j)
                # quick length filter
                if abs(len(norm_i)-len(norm_j))>5:
                    continue
                # only compare same degree already, check fuzzy
                ratio=fuzz.ratio(norm_i, norm_j)
                if ratio >= THRESHOLD:
                    # also check token ratio to be safe
                    # Keep the shorter id (earlier) and delete j if same normalized but minor diff
                    # Prefer to keep regular vs international separate: don't merge if one is international and other is regular and titles differ by "นานาชาติ" suffix already removed
                    # Since we removed parentheses, "นานาชาติ" still in program_type not title, so titles are same; we should NOT merge intl vs reg if they are same base title but we already kept 2 per base in previous step.
                    # Here fuzzy is for titles that are same base but had typo, so they should be considered same base and we keep 1 per intl/reg already.
                    # To avoid merging distinct programs, only merge if titles are almost identical and program_type same type (both intl or both reg)
                    is_intl_i = ("นานาชาติ" in (pt_i or "")) or ("international" in (pt_i or "").lower()) or ("นานาชาติ" in title_i)
                    is_intl_j = ("นานาชาติ" in (pt_j or "")) or ("international" in (pt_j or "").lower()) or ("นานาชาติ" in title_j)
                    if is_intl_i != is_intl_j:
                        continue  # don't merge intl vs regular
                    # merge j into i
                    to_delete_ids.add(id_j)
                    visited.add(id_j)
        kept_groups+=1

    print(f"Fuzzy groups to delete: {len(to_delete_ids)} (threshold {THRESHOLD})")
    # show examples
    with engine.connect() as conn2:
        for del_id in list(to_delete_ids)[:10]:
            safe=del_id.replace("'", "''")
            r=conn2.execute(text(f"SELECT title_th, university, degree_level FROM courses WHERE id='{safe}'")).fetchone()
            if r:
                print(f"  delete {del_id[:30]:30} | {r[1][:25]:25} | {r[2]:10} | {r[0][:50]}")

# Execute
if to_delete_ids:
    with engine.begin() as conn:
        batch=500
        lst=list(to_delete_ids)
        deleted=0
        for i in range(0, len(lst), batch):
            chunk=lst[i:i+batch]
            placeholders=",".join(["'" + x.replace("'", "''") + "'" for x in chunk])
            res=conn.execute(text(f"DELETE FROM courses WHERE id IN ({placeholders})"))
            deleted+=res.rowcount
            print(f"Deleted batch {i//batch+1}: {res.rowcount}")
        print(f"Total fuzzy deleted: {deleted}")
else:
    print("No fuzzy duplicates found")

with engine.connect() as conn:
    total_after=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"\nTotal after fuzzy: {total_after} (removed {total_before - total_after})")
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC LIMIT 12")).fetchall()
    for r in rows:
        print(f"  {r[0][:40]:40} {r[1]}")
