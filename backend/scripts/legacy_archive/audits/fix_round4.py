"""
Round 4 fixes:
  1. Strip honorific (นพ./พญ.) prefix from first_name (5 rows)
  2. Normalize profile_url = '' → NULL
  3. Remove junk research_interests items (<3 chars, not valid abbreviations)
  4. Normalize spelled-out นายแพทย์ → นพ. / แพทย์หญิง → พญ. in full_name_th
     (only for simple cases: ผศ. นายแพทย์ชื่อ → ผศ. นพ. ชื่อ)
  5. Rebuild stale embedding_text

Run: python backend/scripts/audits/fix_round4.py
"""
import psycopg2, re, json

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("ROUND 4 FIXES")
print("=" * 60)

# ── Fix 1: Strip honorific prefix from first_name ─────────────────────
print("\n[Fix 1] Strip honorific from first_name")
cur.execute(r"""
    SELECT id, first_name FROM faculties
    WHERE first_name ~ '^(นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|ทญ\.)'
""")
rows = cur.fetchall()
HONOR_RE = re.compile(r'^(นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|ทญ\.)\s*')
updates = []
for rid, fn in rows:
    cleaned = HONOR_RE.sub('', fn).strip()
    if cleaned != fn:
        updates.append((cleaned, rid))
        print(f"  {fn!r} → {cleaned!r}")
if updates:
    cur.executemany("UPDATE faculties SET first_name = %s WHERE id = %s", updates)
    conn.commit()
print(f"  Fixed: {len(updates)} rows")

# ── Fix 2: profile_url = '' → NULL ────────────────────────────────────
print("\n[Fix 2] Normalize profile_url empty string → NULL")
cur.execute("SELECT COUNT(*) FROM faculties WHERE profile_url = ''")
n = cur.fetchone()[0]
print(f"  Found: {n} rows")
if n:
    cur.execute("UPDATE faculties SET profile_url = NULL WHERE profile_url = ''")
    conn.commit()
    print(f"  Fixed: {n} rows")

# Also image_url = '' → NULL
cur.execute("SELECT COUNT(*) FROM faculties WHERE image_url = ''")
n2 = cur.fetchone()[0]
print(f"  image_url empty: {n2} rows")
if n2:
    cur.execute("UPDATE faculties SET image_url = NULL WHERE image_url = ''")
    conn.commit()
    print(f"  Fixed: {n2} rows")

# ── Fix 3: Remove junk research_interests items ───────────────────────
print("\n[Fix 3] Remove junk research_interests items (<3 chars, clearly not abbrev)")
# Valid short abbreviations to keep: AI, ML, IT, KM, HR, etc. (2 uppercase letters)
# Junk: '(i', 'W0', 'สว', 'สี', 'คน', single vowels, etc.
VALID_SHORT = re.compile(r'^[A-Z]{1,3}$')  # 1-3 uppercase = valid acronym

cur.execute(r"""
    SELECT f.id, f.research_interests
    FROM faculties f
    WHERE research_interests IS NOT NULL
    AND research_interests::text != 'null'
    AND EXISTS (
        SELECT 1 FROM jsonb_array_elements_text(f.research_interests::jsonb) AS item
        WHERE length(item) < 3
    )
""")
rows = cur.fetchall()

updates3 = []
for rid, interests in rows:
    if not interests:
        continue
    items = interests if isinstance(interests, list) else []
    new_items = []
    removed = []
    for item in items:
        if isinstance(item, str) and len(item) < 3:
            if VALID_SHORT.match(item):
                new_items.append(item)  # keep valid acronym like AI, ML
            else:
                removed.append(item)  # remove junk
        else:
            new_items.append(item)
    if removed:
        updates3.append((json.dumps(new_items, ensure_ascii=False), rid))
        print(f"  {rid}: removed {removed!r}")

if updates3:
    cur.executemany(
        "UPDATE faculties SET research_interests = %s::json WHERE id = %s",
        updates3
    )
    conn.commit()
print(f"  Faculty rows updated: {len(updates3)}")

# ── Fix 4: Normalize spelled-out honorifics in full_name_th ──────────
print("\n[Fix 4] Normalize นายแพทย์ → นพ. / แพทย์หญิง → พญ. / สัตวแพทย์หญิง → สพ.ญ.")
# Pattern: (acad title) นายแพทย์(name) → (acad title) นพ. (name)
# But only for simple cases where the spelled-out form is used as a sub-title
# Do NOT touch: ศ. เกียรติคุณ นายแพทย์ชื่อ — เกียรติคุณ modifies ศ., not a professional title

NORMALIZE_MAP = [
    # Thai has no whitespace word boundary inside a glued title/name. Require
    # the title to start at the string boundary or after whitespace instead.
    (re.compile(r'(?<!\S)นายแพทย์\s*'), 'นพ. '),
    (re.compile(r'(?<!\S)แพทย์หญิง\s*'), 'พญ. '),
    (re.compile(r'(?<!\S)สัตวแพทย์หญิง\s*'), 'สพ.ญ. '),
    (re.compile(r'(?<!\S)สัตวแพทย์\s*(?!หญิง)'), 'สพ. '),
    (re.compile(r'(?<!\S)ทันตแพทย์หญิง\s*'), 'ทพญ. '),
    (re.compile(r'(?<!\S)ทันตแพทย์\s*(?!หญิง)'), 'ทพ. '),
    (re.compile(r'(?<!\S)ภัสรชาแพทย์\s*'), 'ภก. '),  # edge case
]

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(นายแพทย์|แพทย์หญิง|สัตวแพทย์หญิง|สัตวแพทย์|ทันตแพทย์หญิง|ทันตแพทย์)'
""")
rows4 = cur.fetchall()

updates4 = []
for rid, name in rows4:
    fixed = name
    for pattern, replacement in NORMALIZE_MAP:
        fixed = pattern.sub(replacement, fixed)
    # Clean double spaces
    fixed = re.sub(r' {2,}', ' ', fixed).strip()
    if fixed != name:
        updates4.append((fixed, rid))
        print(f"  {name!r}")
        print(f"    → {fixed!r}")

if updates4:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates4)
    conn.commit()
print(f"\n  Fixed: {len(updates4)} rows")

# ── Fix 5: Rebuild stale embedding_text ───────────────────────────────
print("\n[Fix 5] Rebuild stale embedding_text")
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
        if items:
            parts.append(', '.join(str(i) for i in items[:10]))
    return ' | '.join(parts)

emb_updates = []
for row in stale:
    rid, n, u, f, d, t, r = row
    new_text = build_emb(n, u, f, d, t, r)
    emb_updates.append((new_text, rid))

if emb_updates:
    cur.executemany("UPDATE faculties SET embedding_text = %s WHERE id = %s", emb_updates)
    conn.commit()
print(f"  Rebuilt: {len(emb_updates)} rows")

# ── Final verification ────────────────────────────────────────────────
print("\n--- Final Verification ---")

cur.execute(r"""SELECT COUNT(*) FROM faculties WHERE first_name ~ '^(นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|ทญ\.)'""")
print(f"  first_name with honorific prefix: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM faculties WHERE profile_url = ''")
print(f"  Empty profile_url: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM faculties WHERE image_url = ''")
print(f"  Empty image_url: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties, jsonb_array_elements_text(research_interests::jsonb) AS item
    WHERE length(item) < 3 AND item !~ '^[A-Z]{1,3}$'
""")
print(f"  Junk research_interest items (<3 chars, non-acronym): {cur.fetchone()[0]}")

cur.execute(r"""SELECT COUNT(*) FROM faculties WHERE full_name_th ~ '(นายแพทย์|แพทย์หญิง|สัตวแพทย์(?:หญิง)?|ทันตแพทย์(?:หญิง)?)'""")
print(f"  Remaining spelled-out honorifics in full_name_th: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
print(f"  Stale embedding_text: {cur.fetchone()[0]}")

conn.close()
print("\n[Round 4 fixes complete]")
