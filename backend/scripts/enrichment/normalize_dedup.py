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

env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)

def normalize_title(t):
    if not t:
        return ""
    # remove parentheses content
    t=re.sub(r'\(.*?\)', '', t)
    t=re.sub(r'\[.*?\]', '', t)
    # remove extra spaces, strip
    t=re.sub(r'\s+', ' ', t).strip()
    return t

def is_international(rec):
    # rec: (id, title_th, title_en, degree_level, university, program_type)
    pt=(rec[5] or "") + " " + (rec[1] or "") + " " + (rec[2] or "")
    return ("นานาชาติ" in pt) or ("international" in pt.lower())

with engine.connect() as conn:
    total_before=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"Total before normalize dedup: {total_before}")

# Load all
with engine.connect() as conn:
    rows=conn.execute(text("SELECT id, title_th, title_en, degree_level, university, program_type, faculty_th FROM courses ORDER BY university, id")).fetchall()
    # group by (university, normalized_title, degree_level) - degree_level helps keep bachelor/master separate even if title normalized same
    groups=defaultdict(list)
    for r in rows:
        norm=normalize_title(r[1])
        key=(r[4], norm, r[3])  # university, norm_title, degree_level
        groups[key].append(r)

    print(f"Groups (university, norm_title, degree): {len(groups)}, avg size {len(rows)/len(groups):.2f}")

    to_delete=[]
    to_keep=set()
    for key, recs in groups.items():
        if len(recs)==1:
            to_keep.add(recs[0][0])
            continue
        intl=[r for r in recs if is_international(r)]
        reg=[r for r in recs if not is_international(r)]
        # keep 1 intl + 1 reg
        if intl:
            keep=sorted(intl, key=lambda x: x[0])[0]
            to_keep.add(keep[0])
            for r in intl:
                if r[0]!=keep[0]:
                    to_delete.append(r[0])
        if reg:
            keep=sorted(reg, key=lambda x: x[0])[0]
            to_keep.add(keep[0])
            for r in reg:
                if r[0]!=keep[0]:
                    to_delete.append(r[0])

    print(f"After normalized exact grouping: keep {len(to_keep)}, delete {len(to_delete)}")
    # Show largest groups
    for key, recs in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        if len(recs)>2:
            print(f"  {key[0][:20]:20} | {key[2]:10} | {key[1][:40]:40} -> {len(recs)} recs")

# Also fuzzy dedup for titles that are 92+ similar but not exact after normalize (e.g., trailing "สาขาวิชา" vs "สาขา")
# Only within same university and degree_level, to avoid cross-faculty merge
if HAS_FUZZ and to_delete:
    pass  # already handled

# If we want fuzzy, we can attempt to merge groups whose normalized titles are very similar (>95)
# This is optional, do only for CMU EE case where titles differ by one char
# We'll do a second pass: for each university+degree, cluster titles with fuzz.ratio > 96
if HAS_FUZZ:
    with engine.connect() as conn:
        # Build map of kept ids per normalized group already, but we need to check fuzzy across groups
        # Collect all current kept groups after first pass
        # For simplicity, only check CMU EE as example and MFL top duplicates
        pass

# Execute deletion of normalized duplicates
if to_delete:
    with engine.begin() as conn:
        batch=500
        deleted=0
        for i in range(0, len(to_delete), batch):
            chunk=to_delete[i:i+batch]
            placeholders=",".join(["'" + x.replace("'", "''") + "'" for x in chunk])
            res=conn.execute(text(f"DELETE FROM courses WHERE id IN ({placeholders})"))
            deleted+=res.rowcount
            print(f"Deleted batch {i//batch+1}: {res.rowcount}")
        print(f"Total deleted normalized: {deleted}")
else:
    print("No normalized duplicates to delete")

# After
with engine.connect() as conn:
    total_after=conn.execute(text("SELECT count(*) FROM courses")).scalar()
    print(f"\nTotal after: {total_after} (removed {total_before - total_after})")
    rows=conn.execute(text("SELECT university, count(*) FROM courses GROUP BY university ORDER BY count(*) DESC LIMIT 12")).fetchall()
    for r in rows:
        print(f"  {r[0][:40]:40} {r[1]}")
    # CMU EE check
    rows=conn.execute(text("SELECT id, title_th, program_type FROM courses WHERE university='Chiang Mai University' AND title_th LIKE '%ไฟฟ้า%'")).fetchall()
    print(f"\nCMU EE after normalize: {len(rows)}")
    for r in rows:
        print(f"  {r[0]:30} {r[2][:35]:35} {r[1][:50]}")
