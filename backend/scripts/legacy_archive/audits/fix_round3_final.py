"""
Fix the 2 skipped rows from fix_round3_remaining.py and 1 remaining glued sub-title.
Run: python backend/scripts/audits/fix_round3_final.py
"""
import psycopg2
import re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("ROUND 3 FINAL TARGETED FIXES")
print("=" * 60)

# ── First, show the exact state of the 2 skipped rows ────────────────
print("\n[Inspect] Skipped rows and remaining glued:")
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th LIKE 'ศ.นพ. นพ. ดำเนินสันต์%'
       OR full_name_th LIKE 'รศ.สพ. ญ. ดร. รศ.%'
       OR full_name_th LIKE '%รศ.สพ. ญ. ดร. รศ.%'
""")
for r in cur.fetchall():
    print(f"  id={r[0]}")
    print(f"  name={r[1]!r}")
    print(f"  title={r[2]!r}")

# Also show remaining glued
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|ดร\.)[ก-๙]'
""")
glued = cur.fetchall()
print(f"\n[Remaining truly glued] {len(glued)} rows:")
for r in glued:
    print(f"  {r[1]!r}")

# ── Fix A: 'ศ.นพ. นพ. ดำเนินสันต์ พฤกษากร' → 'ศ.นพ. ดำเนินสันต์ พฤกษากร' ──
# Pattern: compact_title + ' ' + same_professional. + ' ' + name
DOUBLE_PROF_ONLY_RE = re.compile(
    # compact: acad.prof.
    r'^((?:ศ|รศ|ผศ|อ)\.(?:ดร\.)?(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\s*\.\s*ญ)?)\.)'
    r'\s+'
    # dupe: same professional abbreviation (no academic repeat here)
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\s*\.\s*ญ)?)\.)'
    r'\s+'
)

# ── Fix B: 'รศ.สพ. ญ. ดร. รศ. สพ. ญ. ดร. อารีย์' → 'รศ.สพ. ญ. ดร. อารีย์' ──
# After Fix 1b split สพ.ญ. → สพ. ญ., the pattern is now different
# Pattern: acad.prof. ญ. ดร. (dupe-acad. dupe-prof. ญ. ดร.) name
DOUBLE_SPF_JNG_RE = re.compile(
    r'^((?:(?:ศ|รศ|ผศ|อ)\.(?:ดร\.)?(?:สพ|ทนพ)\.)\s*ญ\.\s*(?:ดร\.\s*)?)'
    r'(?:(?:ศ|รศ|ผศ|อ)\.?\s*)'         # dupe academic
    r'(?:(?:สพ|ทนพ)\.?\s*ญ\.?\s*)'     # dupe prof
    r'(?:ดร\.\s*)?'                      # optional ดร.
)

print("\n[Fix] Apply targeted fixes:")

cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND (
        full_name_th ~ '\. (นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
        OR full_name_th ~ '\. (นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)$'
      )
""")
targeted_rows = cur.fetchall()
print(f"  Found {len(targeted_rows)} rows matching simplified pattern")
for r in targeted_rows:
    print(f"    {r[1]!r}")

# Direct targeted UPDATE for the known specific patterns
updates = []

# Pattern 1: ศ.นพ. นพ. ดำเนินสันต์ → ศ.นพ. ดำเนินสันต์
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|สพ)\. (นพ|พญ|ภก|ภญ|ทพ|ทญ)\. '
""")
for rid, name in cur.fetchall():
    m = DOUBLE_PROF_ONLY_RE.match(name)
    if m:
        clean = m.group(1) + ' ' + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, rid))
        print(f"  FIX-A: {name!r} → {clean!r}")

# Pattern 2: double สพ. ญ. ดร. pattern (split form after Fix 1b)
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(สพ|ทนพ)\. ญ\. ดร\. (ศ|รศ|ผศ|อ)\.'
""")
for rid, name in cur.fetchall():
    m = DOUBLE_SPF_JNG_RE.match(name)
    if m:
        clean = m.group(1) + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates.append((clean, rid))
        print(f"  FIX-B: {name!r} → {clean!r}")
    else:
        # Fall back: strip everything between first ' ดร. ' and the real name
        # 'รศ.สพ. ญ. ดร. รศ. สพ. ญ. ดร. อารีย์' → find position of second 'ดร. '
        parts = re.split(r'(?<=ดร\.) ', name)
        print(f"  FIX-B fallback, split parts: {parts}")
        if len(parts) >= 2:
            # Keep compact prefix (everything up to and including first 'ดร. ')
            # + last segment (actual name)
            prefix_end = name.find('ดร. ') + 4  # after 'ดร. '
            # Find second occurrence of ดร. if any
            second = name.find('ดร.', prefix_end)
            if second > 0:
                name_start = second + 4  # after second 'ดร. '
                clean = name[:prefix_end].strip() + ' ' + name[name_start:].strip()
                clean = re.sub(r' {2,}', ' ', clean).strip()
                updates.append((clean, rid))
                print(f"  FIX-B fallback: {name!r} → {clean!r}")

if updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates)
    conn.commit()
print(f"\n  Applied {len(updates)} targeted fixes")

# ── Fix C: any remaining glued sub-title ─────────────────────────────
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|ดร\.)[ก-๙]'
""")
glued_rows = cur.fetchall()
GLUED_FIX = re.compile(
    r'((?:ภก|ภญ|นพ|พญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?|กภ|รภ|ดร)\.)'
    r'([ก-๙])'
)
glued_updates = []
for rid, name in glued_rows:
    fixed = GLUED_FIX.sub(r'\1 \2', name)
    if fixed != name:
        glued_updates.append((fixed, rid))
        print(f"  GLUED: {name!r} → {fixed!r}")

if glued_updates:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", glued_updates)
    conn.commit()
print(f"  Fixed {len(glued_updates)} remaining glued rows")

# ── Rebuild stale embedding_text ──────────────────────────────────────
cur.execute(r"""
    SELECT id, full_name_th, university_th, faculty_th, department_th,
           academic_title_th, research_interests
    FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
stale = cur.fetchall()

def build_embedding_text(full_name_th, university_th, faculty_th, department_th,
                          academic_title_th, research_interests):
    parts = [p for p in [full_name_th, academic_title_th, university_th, faculty_th, department_th] if p]
    if research_interests:
        items = research_interests if isinstance(research_interests, list) else []
        if items:
            parts.append(', '.join(str(i) for i in items[:10]))
    return ' | '.join(parts)

emb_updates = []
for row in stale:
    rid, full_name_th, univ, fac, dept, title, interests = row
    new_text = build_embedding_text(full_name_th, univ, fac, dept, title, interests)
    emb_updates.append((new_text, rid))

if emb_updates:
    cur.executemany("UPDATE faculties SET embedding_text = %s WHERE id = %s", emb_updates)
    conn.commit()
print(f"  Rebuilt {len(emb_updates)} stale embedding_text rows")

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

# Show any residual double-prefix
cur.execute(r"""
    SELECT full_name_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|นายแพทย์|ดร\.)'
    LIMIT 20
""")
residual = cur.fetchall()
if residual:
    print(f"\n  Residual rows:")
    for r in residual:
        print(f"    {r[0]!r}")

conn.close()
print("\n[Done]")
