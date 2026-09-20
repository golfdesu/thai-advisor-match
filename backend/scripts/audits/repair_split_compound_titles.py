import psycopg2, re
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

# Fix 1b split สพ.ญ. into สพ. ญ. (wrong — it's one compound abbreviation)
# Also น.สพ. (another vet abbreviation) may need the same treatment
# Correct form: สพ.ญ. (dot between สพ and ญ, period after ญ)
print("Fixing over-split สพ. ญ. → สพ.ญ. and similar compound abbreviations")

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ 'สพ\. ญ\.'
       OR full_name_th ~ 'ทนพ\. ญ\.'
""")
rows = cur.fetchall()
print(f"Rows with over-split compound abbrev: {len(rows)}")

# สพ. ญ. → สพ.ญ. (no space between สพ and ญ — it's the female suffix)
SPLIT_FIX = re.compile(r'(สพ|ทนพ)\. (ญ)\.')
updates = []
for rid, name in rows:
    fixed = SPLIT_FIX.sub(r'\1.\2.', name)
    if fixed != name:
        updates.append((fixed, rid))
        print(f"  {name!r} → {fixed!r}")

if updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates)
    conn.commit()
    print(f"Fixed {len(updates)} rows")

# Also rebuild stale embedding_text for those rows
if updates:
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

# Final check
print("\n--- Final counts ---")
cur.execute(r"""SELECT COUNT(*) FROM faculties WHERE full_name_th ~ 'สพ\. ญ\.'""")
print(f"  Remaining สพ. ญ. split: {cur.fetchone()[0]}")
cur.execute(r"""SELECT COUNT(*) FROM faculties WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|ดร\.)[ก-๙]'""")
print(f"  Remaining glued sub-title rows: {cur.fetchone()[0]}")

conn.close()
print("[Done]")
