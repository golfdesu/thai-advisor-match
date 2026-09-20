"""
Fix round 3 string bugs:
  1. Glued professional sub-title: ภก./ภญ./นพ./พญ./ทพ./ทนพ./สพ. + no space before name → insert space
  2. Double academic+professional prefix: ศ.นพ. ศ. นพ.ชื่อ → ศ.นพ. ชื่อ
  3. Long research_interest items (>200 chars) → truncate at sentence/comma boundary ≤200 chars
  4. Stale embedding_text → rebuild from current field values for all stale rows

Run: python backend/scripts/audits/fix_round3_bugs_2026_09_14.py
"""
import psycopg2
import re
import json

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 60)
print("ROUND 3 STRING BUG FIXES")
print("=" * 60)

# ── Fix 1: Insert space after glued professional sub-title ────────────
# Pattern: (ภก|ภญ|นพ|พญ|ทพ|ทญ|ทนพ|ทนพญ|สพ|กภ|รภ).<Thai/Latin char>
# → (ภก|...). <char>
print("\n[Fix 1] Insert space after glued professional sub-title")
SUB_TITLE_RE = re.compile(
    r'(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ(?:ญ)?\.|สพ(?:\.ญ)?\.|กภ\.|รภ\.|ภก\.|ทนพ\.)([ก-๙A-Za-z])'
)

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ|สพ\.|กภ\.|รภ\.)[ก-๙A-Za-z]'
""")
rows = cur.fetchall()
updates1 = []
for rid, name in rows:
    fixed = SUB_TITLE_RE.sub(r'\1 \2', name)
    if fixed != name:
        updates1.append((fixed, rid))

if updates1:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates1)
print(f"  Rows fixed: {len(updates1)}")

# ── Fix 2: Double academic+professional prefix ────────────────────────
# e.g. "ศ.นพ. ศ. นพ.ชื่อ" → "ศ.นพ. ชื่อ"
# e.g. "ศ.ดร.นพ. ศ.ดร. นพ.ชื่อ" → "ศ.ดร.นพ. ชื่อ"
# e.g. "ศ.นพ. ศ. นายแพทย์ชื่อ" → "ศ.นพ. ชื่อ"
print("\n[Fix 2] Strip double academic+professional prefix")
DOUBLE_PROF_RE = re.compile(
    r'^((ศ|รศ|ผศ|อ)\.(?:ดร\.)?(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?)\.) '  # group1: compact correct title
    r'(?:(?:ศ|รศ|ผศ|อ)\.?(?:ดร\.)? )'                                               # dupe academic part
    r'(?:(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ(?:ญ)?|สพ(?:\.ญ)?|นายแพทย์|แพทย์หญิง)\.? ?)'    # dupe professional part
)

cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|นายแพทย์)'
""")
rows2 = cur.fetchall()
updates2 = []
for rid, name in rows2:
    m = DOUBLE_PROF_RE.match(name)
    if m:
        clean = m.group(1) + ' ' + name[m.end():]
        clean = re.sub(r' {2,}', ' ', clean).strip()
        updates2.append((clean, rid))

if updates2:
    cur.executemany("UPDATE faculties SET full_name_th = %s WHERE id = %s", updates2)
print(f"  Rows fixed: {len(updates2)}")

# Sample result
if updates2:
    for new_name, rid in updates2[:5]:
        print(f"    {rid:45s}  → {new_name!r}")

# ── Fix 3: Truncate long research_interest items ──────────────────────
print("\n[Fix 3] Truncate research_interest items >200 chars")

cur.execute(r"""
    SELECT id, research_interests FROM faculties
    WHERE research_interests IS NOT NULL
    AND research_interests::text != 'null'
    AND EXISTS (
        SELECT 1 FROM jsonb_array_elements_text(research_interests::jsonb) item
        WHERE length(item) > 200
    )
""")
rows3 = cur.fetchall()

def truncate_item(text, max_len=200):
    """Truncate at last sentence end or comma before max_len."""
    if len(text) <= max_len:
        return text
    chunk = text[:max_len]
    # Try sentence boundary
    for sep in ('. ', '。', '! ', '? '):
        pos = chunk.rfind(sep)
        if pos > 80:
            return chunk[:pos + 1].strip()
    # Try comma
    pos = chunk.rfind(', ')
    if pos > 80:
        return chunk[:pos].strip()
    # Hard cut
    return chunk.rstrip(' ,;').strip()

updates3 = []
for rid, interests in rows3:
    if not interests:
        continue
    items = interests if isinstance(interests, list) else []
    new_items = [truncate_item(i) if isinstance(i, str) else i for i in items]
    if new_items != items:
        updates3.append((json.dumps(new_items, ensure_ascii=False), rid))

if updates3:
    cur.executemany(
        "UPDATE faculties SET research_interests = %s::json WHERE id = %s",
        updates3
    )
print(f"  Faculty rows updated: {len(updates3)}")

# ── Fix 4: Rebuild stale embedding_text ───────────────────────────────
print("\n[Fix 4] Rebuild stale embedding_text for rows where it diverges from full_name_th")

cur.execute(r"""
    SELECT id, full_name_th, university_th, faculty_th, department_th,
           academic_title_th, research_interests, embedding_text
    FROM faculties
    WHERE full_name_th IS NOT NULL
    AND embedding_text IS NOT NULL
    AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
rows4 = cur.fetchall()

def build_embedding_text(full_name_th, university_th, faculty_th, department_th,
                          academic_title_th, research_interests):
    parts = []
    if full_name_th:
        parts.append(full_name_th)
    if academic_title_th:
        parts.append(academic_title_th)
    if university_th:
        parts.append(university_th)
    if faculty_th:
        parts.append(faculty_th)
    if department_th:
        parts.append(department_th)
    if research_interests:
        items = research_interests if isinstance(research_interests, list) else []
        if items:
            parts.append(', '.join(str(i) for i in items[:10]))
    return ' | '.join(p for p in parts if p)

updates4 = []
for row in rows4:
    rid, full_name_th, univ, fac, dept, title, interests, old_text = row
    new_text = build_embedding_text(full_name_th, univ, fac, dept, title, interests)
    if new_text != old_text:
        updates4.append((new_text, rid))

if updates4:
    cur.executemany("UPDATE faculties SET embedding_text = %s WHERE id = %s", updates4)
print(f"  Rows rebuilt: {len(updates4)}")

conn.commit()

# ── Verification ──────────────────────────────────────────────────────
print("\n--- Verification ---")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพ|สพ\.|กภ\.|รภ\.)[ก-๙A-Za-z]'
""")
print(f"  Remaining glued sub-title rows      : {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|ทนพ|สพ)\. '
      AND full_name_th ~ ' (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|นายแพทย์)'
""")
print(f"  Remaining double professional prefix: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties, jsonb_array_elements_text(research_interests::jsonb) as item
    WHERE length(item) > 200
""")
print(f"  Remaining long research_interest items: {cur.fetchone()[0]}")

cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
print(f"  Remaining stale embedding_text rows : {cur.fetchone()[0]}")

conn.close()
print("\n[All round 3 fixes applied]")
