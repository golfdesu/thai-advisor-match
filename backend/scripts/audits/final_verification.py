"""
Final verification of all string bugs after all rounds of fixes.
"""
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

print("=" * 65)
print("FINAL VERIFICATION — ALL STRING BUG CATEGORIES")
print("=" * 65)

# ── Check for truly glued sub-titles (dot directly touching Thai
#    char where the abbrev is NOT สพ.ญ. itself) ─────────────────────
print("\n[1] Truly glued sub-titles (dot+Thai char, excluding สพ.ญ. abbreviation):")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '(ภก\.|ภญ\.|นพ\.|พญ\.|ทพ\.|ทญ\.|ทนพญ?\.|ดร\.)[ก-๙]'
""")
print(f"  Glued (excl สพ.ญ.): {cur.fetchone()[0]}")

# Check สพ.ญ. glued only — สพ.ญ followed by Thai char with no space
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\.[ก-๙]'
""")
print(f"  สพ.ญ. truly glued (dot+Thai, no space): {cur.fetchone()[0]}")

# ── Double prefix checks ───────────────────────────────────────────
print("\n[2] Remaining academic title doubled (two academic prefixes):")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ '^(ศ|รศ|ผศ|อ)\.. *(ศ|รศ|ผศ|อ)\.'
""")
print(f"  Double academic prefix: {cur.fetchone()[0]}")

print("\n[3] Remaining double professional prefix:")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
       OR full_name_th ~ '(นพ|พญ|ภก|ภญ|ทพ|ทญ)\. .{0,20}(นพ|พญ|ภก|ภญ|ทพ|ทญ)\.'
""")
print(f"  Double professional (สพ.ญ.+สพ.ญ. or others): {cur.fetchone()[0]}")

# ── Stale embedding_text ──────────────────────────────────────────
print("\n[4] Stale embedding_text:")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties
    WHERE full_name_th IS NOT NULL AND embedding_text IS NOT NULL AND full_name_th != ''
    AND embedding_text NOT LIKE '%' || full_name_th || '%'
""")
print(f"  Stale rows: {cur.fetchone()[0]}")

# ── Long research_interest items ─────────────────────────────────
print("\n[5] Long research_interest items (>200 chars):")
cur.execute(r"""
    SELECT COUNT(*) FROM faculties, jsonb_array_elements_text(research_interests::jsonb) AS item
    WHERE length(item) > 200
""")
print(f"  Items >200 chars: {cur.fetchone()[0]}")

# ── Null/empty emails (should be NULL not '') ─────────────────────
print("\n[6] Empty string emails (should be NULL):")
cur.execute("SELECT COUNT(*) FROM faculties WHERE email = ''")
print(f"  Empty string email rows: {cur.fetchone()[0]}")

# ── Double spaces in full_name_th ─────────────────────────────────
print("\n[7] Double spaces in full_name_th:")
cur.execute("SELECT COUNT(*) FROM faculties WHERE full_name_th LIKE '%  %'")
print(f"  Rows with double spaces: {cur.fetchone()[0]}")

# ── Specific double-prefix known patterns ──────────────────────────
print("\n[8] Known double-prefix patterns (spot check):")
for pat, label in [
    (r"'ศ.ดร. สพ.ญ. ศ.ดร. สพ.ญ.'", "ศ.ดร.สพ.ญ. doubled"),
    (r"'รศ.ดร. สพ.ญ. รศ.ดร. สพ.ญ.'", "รศ.ดร.สพ.ญ. doubled"),
]:
    cur.execute(f"SELECT COUNT(*) FROM faculties WHERE full_name_th LIKE {pat}")
    print(f"  {label}: {cur.fetchone()[0]}")

# ── Summary counts ────────────────────────────────────────────────
print("\n[Summary]")
cur.execute("SELECT COUNT(*) FROM faculties")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM faculties WHERE embedding_text IS NOT NULL")
with_emb = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM faculties WHERE email IS NOT NULL")
with_email = cur.fetchone()[0]
print(f"  Total rows: {total}")
print(f"  With embedding_text: {with_emb}")
print(f"  With email: {with_email}")

# Show true double สพ.ญ. rows
print("\n[True remaining duplicate-prefix rows]:")
cur.execute(r"""
    SELECT full_name_th FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  {r[0]!r}")

conn.close()
print("\n[Verification complete]")
