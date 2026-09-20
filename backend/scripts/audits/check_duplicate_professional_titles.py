import psycopg2, re
conn = psycopg2.connect(host='localhost', port=5432, dbname='advisor_match', user='postgres', password='postgres')
cur = conn.cursor()

# Show the 23 flagged rows
cur.execute(r"""
    SELECT full_name_th FROM faculties
    WHERE full_name_th ~ 'สพ\.ญ\. (?:ดร\. )?สพ\.ญ\.'
       OR full_name_th ~ '(นพ|พญ|ภก|ภญ|ทพ|ทญ)\. .{0,20}(นพ|พญ|ภก|ภญ|ทพ|ทญ)\.'
    ORDER BY full_name_th
""")
rows = cur.fetchall()
print(f"Total: {len(rows)}")
for r in rows:
    name = r[0]
    # Count professional abbreviation occurrences
    profs = re.findall(r'(?:นพ|พญ|ภก|ภญ|ทพ|ทญ|สพ(?:\.ญ)?|ทนพ(?:ญ)?)\.', name)
    status = "DUP" if len(profs) > 1 else "OK"
    print(f"  [{status}] profs={profs}  {name!r}")
conn.close()
