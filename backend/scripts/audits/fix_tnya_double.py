import psycopg2, re
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

# Handle the remaining 9 rows:
# 8 are แบบ acad.dr. prof. acad.dr. prof. name (ผศ.ดร. ทญ. ผศ.ดร. ทญ. ชื่อ)
# 1 is รศ.ดร. นพ. รศ. ดร. นพ. ชื่อ
# 1 is ผศ. พญ. ทพญ. นุชดา (legit dual-specialty, keep)

LEGIT_DUAL = {'ผศ. พญ. ทพญ. นุชดา ศรียารัณย'}

# General pattern: acad.dr.prof. (compact) + space + dupe(acad.dr.prof.) + name
# Covers ผศ.ดร. ทญ. and ศ.ดร. ทญ. variants
DOUBLE_DR_PROF = re.compile(
    # Compact prefix: (ศ|รศ|ผศ|อ).ดร. prof.
    r'^((?:(?:ศ|รศ|ผศ|อ)\.ดร\.) '
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.)'
    r')'
    # Then space + dupe of same compact form
    r'\s+'
    r'(?:(?:ศ|รศ|ผศ|อ)\.ดร\.?\s*)'
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.?\s*)'
)

# Also handles รศ.ดร. นพ. รศ. ดร. นพ. (expanded dupe with space after รศ.)
DOUBLE_DR_PROF2 = re.compile(
    r'^((?:(?:ศ|รศ|ผศ|อ)\.ดร\.) '
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.)'
    r')'
    r'\s+'
    r'(?:(?:ศ|รศ|ผศ|อ)\.\s*ดร\.\s*)'  # expanded: รศ. ดร.
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.?\s*)'
)

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(ทญ|นพ|พญ|ภก|ภญ|ทพ)\. .{0,20}(ทญ|นพ|พญ|ภก|ภญ|ทพ)\.'
""")
rows = cur.fetchall()

updates = []
for rid, name in rows:
    if name in LEGIT_DUAL:
        print(f"  [LEGIT] {name!r}")
        continue

    m = DOUBLE_DR_PROF.match(name) or DOUBLE_DR_PROF2.match(name)
    if m:
        clean = m.group(1) + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, rid))
        print(f"  [FIX] {name!r}")
        print(f"      → {clean!r}")
    else:
        print(f"  [UNHANDLED] {name!r}")

if updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates)
    conn.commit()
    print(f"\nFixed {len(updates)} rows")

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

# Final count
print("\n--- Final ---")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '(ทญ|นพ|พญ|ภก|ภญ|ทพ)\. .{0,20}(ทญ|นพ|พญ|ภก|ภญ|ทพ)\.'
""")
print(f"Remaining double prof prefix: {cur.fetchone()[0]}")

conn.close()
print("[Done]")
