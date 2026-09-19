"""
Fix the 23 true remaining double-prefix / glued-record rows identified from check_23.py.

Categories:
1. Same professional abbrev doubled: รศ.ดร. ทญ. รศ.ดร. ทญ. → รศ.ดร. ทญ.
2. ทพญ. doubled: ศ.ทพญ. ดร. ศ. ทพญ. ดร. → ศ.ทพญ. ดร.
3. คลินิก นพ. doubled: ศ.คลินิก นพ. ศ. คลินิก นพ. → ศ.คลินิก นพ.
4. สพ.ญ. doubled: สพ.ญ. สพ.ญ. กชกร → สพ.ญ. กชกร
5. Glued two-faculty names (e.g. 'อ. นพ. สมภพ...พญ. มาริสา...') → NULL (can't safely split)
6. Cross-specialties (ทพ.+นพ.): ผศ. ทพ. นพ. — these are legitimate dual-specialty; leave as-is
"""
import psycopg2, re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 65)
print("FIX REMAINING DOUBLE-PREFIX ROWS")
print("=" * 65)

updates = []
nulled = []

# ── 1. ทญ. / นพ. / ภก. / ภญ. same-abbrev doubled ────────────────────
# Pattern: compact (acad.dr.prof.) + space + dupe(acad.dr.prof.) + name
DOUBLE_SAME = re.compile(
    r'^((?:(?:ศ|รศ|ผศ|อ)\.(?:คลินิก(?:เกียรติคุณ)? )?(?:ดร\.)?(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.)(?: ดร\.)?)'
    r'\s+'
    r'(?:(?:ศ|รศ|ผศ|อ)\.?\s*(?:คลินิก(?:เกียรติคุณ)?\s*)?(?:ดร\.)?\s*)'
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.?\s*)'
    r'(?:ดร\.\s*)?'
)

# ── 2. ทพญ. doubled ─────────────────────────────────────────────────
# ศ.ทพญ. ดร. ศ. ทพญ. ดร. → ศ.ทพญ. ดร.
DOUBLE_TPNYA = re.compile(
    r'^((?:ศ|รศ|ผศ|อ)\.ทพญ\.(?: ดร\.)?)'
    r'\s+'
    r'(?:(?:ศ|รศ|ผศ|อ)\.?\s*)'
    r'(?:ทพญ\.?\s*)'
    r'(?:ดร\.\s*)?'
)

# ── 3. สพ.ญ. สพ.ญ. ─────────────────────────────────────────────────
DOUBLE_SPFYA = re.compile(r'^(สพ\.ญ\.)\s+สพ\.ญ\.\s*')

# ── 4. Glued two-person rows ─────────────────────────────────────────
# 'อ. นพ. สมภพ อมรศรีสกุลพญ. มาริสา เดชาวิจิตร' — two names merged
# 'อ. พญ. จีน ธรมมพักตรกุลพญ. ภัทรภรณ์ อดุลย์เกษม'
# These are rows where a Thai last name is immediately followed by a new title
# → set full_name_th to NULL (unfixable without original sources)
GLUED_PERSON = re.compile(r'[ก-๙](พญ\.|นพ\.|ทพ\.|ทพญ\.|ภก\.|ภญ\.)')

cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
       OR full_name_th ~ '(นพ|พญ|ภก|ภญ|ทพ|ทญ)\. .{0,20}(นพ|พญ|ภก|ภญ|ทพ|ทญ)\.'
    ORDER BY full_name_th
""")
rows = cur.fetchall()

# Dual-specialty legit patterns (keep as-is)
LEGIT_DUAL = {
    'ผศ. ทพ. นพ. ธิติพงษ์ พฤกษศรีสกุล',
    'ผศ. ทพ. นพ. วรภัทร ตราชู',
    'อ. ทพ. นพ. เฉลิมฤทธิ์ พฤกษ์สดใส',
    'อ. นพ. ทพ. ดร. สรรพสิทธิ์ ปัญญา',
    'ศ. คลินิก ดร. นพ. ทพ. ศิริชัย เกียรติถาวรเจริญ',
    'ผศ. พญ. ทพญ. นุชดา ศรียารัณย',
}

for rid, name, title in rows:
    if name in LEGIT_DUAL:
        print(f"  [LEGIT-DUAL] {name!r}")
        continue

    # Check for glued two-person row
    if GLUED_PERSON.search(name):
        nulled.append((rid, name))
        print(f"  [GLUED-PERSON → NULL] {name!r}")
        continue

    # Try ทพญ. double
    m = DOUBLE_TPNYA.match(name)
    if m:
        clean = m.group(1).rstrip() + ' ' + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, rid))
        print(f"  [TPNYA-DUP] {name!r} → {clean!r}")
        continue

    # Try สพ.ญ. double
    m = DOUBLE_SPFYA.match(name)
    if m:
        clean = m.group(1) + ' ' + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, rid))
        print(f"  [SPFYA-DUP] {name!r} → {clean!r}")
        continue

    # Try general same-abbrev double
    m = DOUBLE_SAME.match(name)
    if m:
        clean = m.group(1).rstrip() + ' ' + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, rid))
        print(f"  [SAME-DUP] {name!r} → {clean!r}")
        continue

    print(f"  [UNHANDLED] {name!r}")

print(f"\n  Fixes to apply: {len(updates)}")
print(f"  Rows to NULL: {len(nulled)}")

if updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates)
    conn.commit()

if nulled:
    ids = [r[0] for r in nulled]
    cur.execute(
        "UPDATE faculties SET full_name_th = NULL WHERE id = ANY(%s)",
        (ids,)
    )
    conn.commit()
    print("  Nulled glued-person rows:")
    for rid, name in nulled:
        print(f"    {rid}: {name!r}")

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
    print(f"  Rebuilt {len(emb_updates)} stale embedding_text rows")

# ── Final check ───────────────────────────────────────────────────────
print("\n--- Final Verification ---")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
       OR full_name_th ~ '(ทญ|ทพญ|นพ|ภก|ภญ|พญ)\. .{0,20}(ทญ|ทพญ|นพ|ภก|ภญ|พญ)\.'
""")
print(f"  Remaining double professional prefix: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT full_name_th FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
       OR full_name_th ~ '(ทญ|ทพญ|นพ|ภก|ภญ|พญ)\. .{0,20}(ทญ|ทพญ|นพ|ภก|ภญ|พญ)\.'
    LIMIT 10
""")
residual = cur.fetchall()
if residual:
    for r in residual:
        profs = re.findall(r'(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทพญ|สพ(?:\.ญ)?|ทนพ(?:ญ)?)\.', r[0])
        print(f"  profs={profs}  {r[0]!r}")

conn.close()
print("\n[Done]")
