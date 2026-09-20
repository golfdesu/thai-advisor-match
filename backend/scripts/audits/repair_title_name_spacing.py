import psycopg2, re
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

# The fix removed the trailing space of the compact prefix group
# so we got 'รศ.ดร. ทญ.ชุติมา' — need to add the space back
# Fix: ensure space between title+prof abbrev and name
# Pattern: (ก-๙ or A-Za-z) immediately after prof abbrev dot

RESPACE = re.compile(
    r'((?:ทญ|ทพ|ทพญ|นพ|พญ|ภก|ภญ|สพ(?:\.ญ)?|ทนพ(?:ญ)?)\.)'
    r'([ก-๙A-Z])'  # Thai/uppercase immediately after (no space)
)

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(ทญ\.|ทพ\.|นพ\.|พญ\.)[ก-๙A-Z]'
""")
rows = cur.fetchall()

updates = []
for rid, name in rows:
    fixed = RESPACE.sub(r'\1 \2', name)
    if fixed != name:
        updates.append((fixed, rid))
        print(f"  {name!r} → {fixed!r}")

if updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates)
    conn.commit()
    print(f"Fixed {len(updates)} rows")

# Rebuild stale embedding_text
cur.execute(r"""
    SELECT id, full_name_th, university_th, faculty_th, department_th,
           academic_title_th, research_interests
    FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
stale = cur.fetchall()
def build_emb(n, u, f, d, t, r):
    parts = [p for p in [n, t, u, f, d] if p]
    if r:
        items = r if isinstance(r, list) else []
        if items: parts.append(', '.join(str(i) for i in items[:10]))
    return ' | '.join(parts)
emb_updates = [(build_emb(*row[1:]), row[0]) for row in stale]
if emb_updates:
    cur.executemany("UPDATE faculties SET embedding_text = %s WHERE id = %s", emb_updates)
    conn.commit()
    print(f"Rebuilt {len(emb_updates)} stale embedding_text")

# Final verification
print("\n--- Verification ---")
cur.execute(r"""SELECT COUNT(*) FROM faculties WHERE full_name_th ~ '(ทญ\.|นพ\.|พญ\.|ภก\.|ทพ\.)[ก-๙]'""")
print(f"  Remaining glued (excl สพ.ญ.): {cur.fetchone()[0]}")

cur.execute(r"""SELECT COUNT(*) FROM faculties WHERE full_name_th LIKE '%  %'""")
print(f"  Double spaces: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
print(f"  Stale embedding_text: {cur.fetchone()[0]}")

conn.close()
print("[Done]")
