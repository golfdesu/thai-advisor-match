"""
Fix remaining round 3 double-prefix patterns.

Remaining glued sub-title: สพ.ญ. variants directly touching Thai name char.
Remaining double prefix: Various ศ./รศ./ผศ./อ. + professional title duplications.

Run: python backend/scripts/audits/fix_round3_remaining.py
"""
import psycopg2
import re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("ROUND 3 REMAINING FIXES")
print("=" * 60)

# ── Fix 1b: Insert space for remaining glued sub-title ────────────────
# Pattern: (any sub-title). directly followed by Thai char (ก-๙), no space
# The previous fix missed สพ.ญ. because the regex didn't cover \.ญ\. compound
# Also catches remaining ดร.ชื่อ, นพ.ชื่อ patterns
print("\n[Fix 1b] Insert space after glued sub-title dot+Thai char")

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|กภ\.|รภ\.|ดร\.)[ก-๙]'
""")
rows = cur.fetchall()

# Match sub-title abbrev ending in dot, directly followed by Thai char
SUB_GLUED = re.compile(
    r'((?:ภก|ภญ|นพ|พญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?|กภ|รภ|ดร)\.)'
    r'([ก-๙])'
)

updates = []
for rid, name in rows:
    fixed = SUB_GLUED.sub(r'\1 \2', name)
    if fixed != name:
        updates.append((fixed, rid))
        print(f"  {name!r}")
        print(f"    → {fixed!r}")

if updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates)
    conn.commit()
print(f"  Fixed: {len(updates)} rows")

# ── Fix 2b: Strip remaining double academic+professional prefix ───────
# Patterns found:
#   'รศ.พญ. ดร. รศ. พญ. ดร. ชื่อ'     → 'รศ.พญ. ดร. ชื่อ'
#   'ศ.นพ. ดร. ศ. นพ. ดร. ชื่อ'       → 'ศ.นพ. ดร. ชื่อ'
#   'ศ.พญ. ศ. แพทย์หญิงชื่อ'          → 'ศ.พญ. ชื่อ'
#   'ศ.นพ. นพ. ชื่อ'                  → 'ศ.นพ. ชื่อ'
#   'รศ.ดร.นพ. รศ. ดร. นายแพทย์ชื่อ' → 'รศ.ดร.นพ. ชื่อ'
#
# Strategy: keep academic_title_th as the compact prefix, strip everything
# up to and including the spelled-out expanded form, then append the name.
print("\n[Fix 2b] Strip remaining double academic+professional prefix")

cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|ทญ\.|นายแพทย์|แพทย์หญิง|ดร\.)'
""")
rows2 = cur.fetchall()

# Regex breakdown:
# group(1) = compact correct title (e.g. "ศ.นพ. ดร." or "รศ.พญ. ดร." or "รศ.ดร.นพ.")
# then whitespace, then the expanded/duplicated segment to strip,
# then the actual name follows at m.end()
DOUBLE_RE = re.compile(
    # compact title: acad. + optional dr + professional. + optional " ดร."
    r'^((?:(?:ศ|รศ|ผศ|อ)\.(?:ดร\.)?(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.)'
    r'(?:\s+ดร\.)?)'
    r'\s+'
    # --- dupe segment (one or two pieces): ---
    # dupe academic: ศ. / รศ. / ผศ. / อ. (with or without dot after) + optional space
    r'(?:(?:ศ|รศ|ผศ|อ)\.?\s*)'
    # dupe optional ดร.
    r'(?:ดร\.\s*)?'
    # dupe professional: abbreviation OR spelled-out form
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?|นายแพทย์|แพทย์หญิง)\.?\s*)'
    # optional trailing ดร. after dupe professional
    r'(?:ดร\.\s*)?'
)

updates2 = []
skipped = []
for rid, name, title in rows2:
    m = DOUBLE_RE.match(name)
    if m:
        remainder = name[m.end():]
        clean = m.group(1).rstrip() + ' ' + remainder.lstrip()
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates2.append((clean, rid))
        print(f"  {name!r}")
        print(f"    → {clean!r}")
    else:
        skipped.append(name)

if updates2:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates2)
    conn.commit()
print(f"\n  Fixed: {len(updates2)} rows")
if skipped:
    print(f"  Skipped (regex didn't match): {len(skipped)}")
    for s in skipped:
        print(f"    {s!r}")

# ── Fix 3: Rebuild stale embedding_text for rows we just changed ──────
print("\n[Fix 3] Rebuild stale embedding_text")

cur.execute(r"""
    SELECT id, full_name_th, university_th, faculty_th, department_th,
           academic_title_th, research_interests, embedding_text
    FROM faculties
    WHERE full_name_th IS NOT NULL
    AND embedding_text IS NOT NULL
    AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
stale = cur.fetchall()

def build_embedding_text(full_name_th, university_th, faculty_th, department_th,
                          academic_title_th, research_interests):
    parts = []
    if full_name_th:    parts.append(full_name_th)
    if academic_title_th: parts.append(academic_title_th)
    if university_th:   parts.append(university_th)
    if faculty_th:      parts.append(faculty_th)
    if department_th:   parts.append(department_th)
    if research_interests:
        items = research_interests if isinstance(research_interests, list) else []
        if items:
            parts.append(', '.join(str(i) for i in items[:10]))
    return ' | '.join(p for p in parts if p)

emb_updates = []
for row in stale:
    rid, full_name_th, univ, fac, dept, title, interests, old_text = row
    new_text = build_embedding_text(full_name_th, univ, fac, dept, title, interests)
    if new_text != old_text:
        emb_updates.append((new_text, rid))

if emb_updates:
    cur.executemany("UPDATE faculties SET embedding_text = %s WHERE id = %s", emb_updates)
    conn.commit()
print(f"  Rebuilt: {len(emb_updates)} embedding_text rows")

# ── Final verification ────────────────────────────────────────────────
print("\n--- Final Verification ---")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|ดร\.)[ก-๙]'
""")
print(f"  Remaining glued sub-title rows:      {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|นายแพทย์|ดร\.)'
""")
print(f"  Remaining double professional prefix: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
print(f"  Stale embedding_text rows:           {cur.fetchone()[0]}")

conn.close()
print("\n[Done]")
