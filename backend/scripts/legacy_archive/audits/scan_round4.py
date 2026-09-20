"""
Round 4 string bug scan — find new categories not caught in rounds 1-3.
Focus: title/name structural issues, JSON field content, field-level anomalies.
"""
import psycopg2, re, json

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

print("=" * 70)
print("STRING BUG SCAN ROUND 4")
print("=" * 70)

# ── 1. full_name_th that is just a title with no personal name ────────
print("\n[1] full_name_th = title-only (no Thai name after title)")
cur.execute(r"""
    SELECT id, full_name_th, first_name, last_name FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ|ดร)\.(ดร\.)?\s*$'
       OR full_name_th ~ '^(ศ|รศ|ผศ|อ|ดร)\.(ดร\.)?\s+(นพ|พญ|ภก|ภญ|ทพ|ทญ|สพ)\.\s*$'
       OR full_name_th ~ '^(ศาสตราจารย์|รองศาสตราจารย์|ผู้ช่วยศาสตราจารย์|อาจารย์|ดร\.)\s*$'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows")
for r in rows[:10]:
    print(f"  {r[0]:45s}  name={r[1]!r}  first={r[2]!r}  last={r[3]!r}")

# ── 2. full_name_th starts with Latin letter (possible English-only name) ─
print("\n[2] full_name_th starts with Latin/digit (not Thai)")
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '^[A-Za-z0-9]'
    AND full_name_th !~ '^(Dr\.|Prof\.|Assoc\.|Asst\.)'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows (sample):")
for r in rows[:15]:
    print(f"  {r[0]:45s}  {r[1]!r}")

# ── 3. full_name_th containing parenthetical maiden name anomalies ────
print("\n[3] full_name_th with suspicious parenthetical content")
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '\([^)]{40,}\)'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows with long parenthetical (>40 chars):")
for r in rows[:10]:
    print(f"  {r[1]!r}")

# ── 4. first_name or last_name containing honorific titles ────────────
print("\n[4] Honorific in first_name or last_name")
cur.execute(r"""
    SELECT id, first_name, last_name FROM faculties
    WHERE first_name ~ '(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|Dr\.|Prof\.)'
       OR last_name  ~ '(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นพ\.|พญ\.|Dr\.|Prof\.)'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows (sample):")
for r in rows[:10]:
    print(f"  first={r[1]!r:30s}  last={r[2]!r}")

# ── 5. full_name_th with repeated word (e.g. ชื่อ ชื่อ / สกุล สกุล) ──
print("\n[5] Repeated word/token in full_name_th")
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '([ก-๙]{3,}) \1'
    LIMIT 20
""")
rows = cur.fetchall()
print(f"  {len(rows)} sample rows:")
for r in rows:
    print(f"  {r[1]!r}")

# ── 6. academic_title_th contains characters it shouldn't ─────────────
print("\n[6] academic_title_th with digits or unexpected chars")
cur.execute(r"""
    SELECT academic_title_th, COUNT(*) FROM faculties
    WHERE academic_title_th ~ '[0-9@#%&*()=\[\]{}|\\<>]'
    GROUP BY academic_title_th ORDER BY COUNT(*) DESC
""")
rows = cur.fetchall()
print(f"  {len(rows)} distinct bad titles:")
for r in rows[:10]:
    print(f"  {r[1]:5d}  {r[0]!r}")

# ── 7. email with invalid TLD (too short or malformed) ────────────────
print("\n[7] Email with invalid/truncated TLD")
cur.execute(r"""
    SELECT id, email FROM faculties
    WHERE email IS NOT NULL
    AND email !~ '^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows with malformed email:")
for r in rows[:15]:
    print(f"  {r[0]:45s}  {r[1]!r}")

# ── 8. research_interests: items that are numbers or single words ──────
print("\n[8] research_interests: suspiciously short items (<3 chars) or numeric")
cur.execute(r"""
    SELECT f.id, f.full_name_th, item
    FROM faculties f, jsonb_array_elements_text(f.research_interests::jsonb) AS item
    WHERE length(item) < 3 OR item ~ '^[0-9]+$'
    LIMIT 20
""")
rows = cur.fetchall()
print(f"  {len(rows)} sample rows:")
for r in rows:
    print(f"  {r[0]:45s}  item={r[2]!r}")

# ── 9. research_interests: items with HTML tags ───────────────────────
print("\n[9] research_interests / education with HTML tags")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE research_interests::text ~ '<[a-zA-Z/][^>]*>'
       OR education::text ~ '<[a-zA-Z/][^>]*>'
""")
print(f"  {cur.fetchone()[0]} rows with HTML in JSON fields")
cur.execute(r"""
    SELECT id, full_name_th,
           SUBSTRING(research_interests::text, 1, 150) AS ri_snip
    FROM faculties
    WHERE research_interests::text ~ '<[a-zA-Z/][^>]*>'
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  {r[0]:45s}  {r[2]!r}")

# ── 10. full_name_th with URL or email embedded ───────────────────────
print("\n[10] full_name_th with embedded URL or email")
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~* '(https?://|www\.|@[a-z]+\.[a-z]{2,})'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows")
for r in rows[:10]:
    print(f"  {r[1]!r}")

# ── 11. profile_url pointing to wrong university (domain mismatch) ─────
print("\n[11] profile_url domain doesn't match university_th (sample)")
cur.execute(r"""
    SELECT id, full_name_th, university_th, profile_url FROM faculties
    WHERE profile_url IS NOT NULL
    AND university_th ILIKE '%จุฬา%'
    AND profile_url NOT ILIKE '%chula%'
    AND profile_url NOT ILIKE '%cu.ac.th%'
    LIMIT 8
""")
rows = cur.fetchall()
print(f"  {len(rows)} Chula faculty with non-Chula profile_url (sample):")
for r in rows:
    print(f"  {r[1]!r}  url={r[3]!r}")

# ── 12. full_name_th with numeric suffix or code ─────────────────────
print("\n[12] full_name_th ending with number or code (e.g. 'ชื่อ 001')")
cur.execute(r"""
    SELECT id, full_name_th FROM faculties
    WHERE full_name_th ~ '[ก-๙A-Za-z] [0-9]{2,}$'
       OR full_name_th ~ '[ก-๙A-Za-z]\([0-9]'
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows")
for r in rows[:10]:
    print(f"  {r[1]!r}")

# ── 13. university_th = NULL or blank ────────────────────────────────
print("\n[13] university_th NULL or empty")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties WHERE university_th IS NULL OR university_th = ''
""")
print(f"  {cur.fetchone()[0]} rows")

# ── 14. department_th containing university name (copy-paste error) ───
print("\n[14] department_th that looks like a university name")
cur.execute(r"""
    SELECT department_th, COUNT(*) FROM faculties
    WHERE department_th ~* '(มหาวิทยาลัย|university|college)'
    GROUP BY department_th ORDER BY COUNT(*) DESC LIMIT 10
""")
rows = cur.fetchall()
print(f"  {len(rows)} distinct dept values with univ name:")
for r in rows:
    print(f"  {r[1]:5d}  {r[0]!r}")

# ── 15. education items that are very short (<5 chars) ───────────────
print("\n[15] education items that are too short (<5 chars)")
cur.execute(r"""
    SELECT f.id, f.full_name_th, item
    FROM faculties f, jsonb_array_elements_text(f.education::jsonb) AS item
    WHERE length(item) < 5
    LIMIT 15
""")
rows = cur.fetchall()
print(f"  {len(rows)} sample rows:")
for r in rows:
    print(f"  {r[0]:45s}  item={r[2]!r}")

# ── 16. full_name_th with Thai honorific prefix spelled out ───────────
print("\n[16] full_name_th with spelled-out Thai honorific (นายแพทย์/แพทย์หญิง) not normalized")
cur.execute(r"""
    SELECT id, full_name_th, academic_title_th FROM faculties
    WHERE full_name_th ~ '(นายแพทย์|แพทย์หญิง|ทันตแพทย์|ทันตแพทย์หญิง)'
    LIMIT 20
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows:")
for r in rows:
    print(f"  title={r[2]!r:20s}  name={r[1]!r}")

# ── 17. Null first_name but non-null full_name_th ────────────────────
print("\n[17] first_name IS NULL but full_name_th has a parseable name")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE first_name IS NULL AND full_name_th IS NOT NULL AND full_name_th != ''
""")
print(f"  {cur.fetchone()[0]} rows")

# ── 18. full_name_th = first_name (title was not prepended) ──────────
print("\n[18] full_name_th == first_name (no title prefix)")
cur.execute(r"""
    SELECT id, full_name_th, first_name, academic_title_th FROM faculties
    WHERE full_name_th = first_name
    AND academic_title_th IS NOT NULL
    LIMIT 10
""")
rows = cur.fetchall()
print(f"  {len(rows)} rows where full_name_th equals first_name:")
for r in rows:
    print(f"  title={r[3]!r}  name={r[1]!r}")

conn.close()
print("\n[Round 4 scan complete]")
