"""
Inspect round 3 bugs before fixing.
Run: python backend/scripts/audits/inspect_round3_bugs.py
"""
import psycopg2, re

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

# ── PDPA rows: show the actual 13-digit hit ───────────────────────────
print("=== PDPA: 13-digit IDs in embedding_text ===")
cur.execute(r"""
    SELECT id, full_name_th, LEFT(embedding_text, 300)
    FROM faculties
    WHERE embedding_text ~ '[1-9][0-9]{12}'
""")
for r in cur.fetchall():
    hits = re.findall(r'[1-9][0-9]{12}', r[2])
    print(f"  {r[0]:45s}  name={r[1]!r}  hits={hits}")

# ── Double-prefix sub-title samples ──────────────────────────────────
print("\n=== Glued sub-title samples ===")
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|สพ\.)[ก-๙A-Za-z]'
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"  [{r[2]!r}]  {r[1]!r}")

# ── Double-prefix pattern: "ศ. นพ." ──────────────────────────────────
print("\n=== Double academic+professional prefix ===")
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.(ดร\.)?(นพ|พญ|ภก|ภญ|ทพ|ทญ|สพ)\.'
       OR full_name_th ~ '(ศ\.|รศ\.|ผศ\.|อ\.) (นพ\.|พญ\.|ภก\.|ภญ\.|ทพ\.|ทญ\.)(ศ\.|รศ\.|ผศ\.|อ\.)'
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  [{r[2]!r}]  {r[1]!r}")

# ── Long research_interest items ──────────────────────────────────────
print("\n=== Long research_interest items (>200 chars) ===")
cur.execute(r"""
    SELECT f.id, f.full_name_th, item
    FROM faculties f, jsonb_array_elements_text(f.research_interests::jsonb) as item
    WHERE length(item) > 200
""")
for r in cur.fetchall():
    print(f"  {r[0]:45s}  len={len(r[2])}  {r[2][:120]!r}")

conn.close()
