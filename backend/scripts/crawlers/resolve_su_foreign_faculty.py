# -*- coding: utf-8 -*-
"""
Resolve Foreign Faculty Names at Silpakorn Arts
Ensures first_name and last_name are properly parsed for foreign language instructors.
"""
import psycopg2
import os
import re

db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/advisor_match")
if not os.getenv("DATABASE_URL") and os.path.exists("/app"):
    db_url = "postgresql://postgres:postgres@db:5432/advisor_match"
elif not os.getenv("DATABASE_URL"):
    db_url = "postgresql://postgres:postgres@localhost:5432/advisor_match"

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT id, full_name_th, profile_url
    FROM faculties
    WHERE (last_name IS NULL OR last_name = '') AND university_th = 'มหาวิทยาลัยศิลปากร'
""")
rows = cur.fetchall()
print(f"Found {len(rows)} foreign faculty records needing name resolution:")

for fid, raw_full, purl in rows:
    # strip Instructor, Instrutor, อ., etc.
    cleaned = re.sub(r'^(?:Instructor|Instrutor|Lecturer|อ\.)\s*', '', raw_full, flags=re.I).strip()

    parts = cleaned.split()
    if len(parts) == 2:
        # e.g. GRAHAM BROCKLEHURST, SHINJI BABA, YOSHIKO MURAKI, MEGUMI SUGITA
        # For CJK 2-part names: e.g. HE FANG, HUANG PING, ZHANG HAO
        # Western / Japanese: First Last
        # Chinese: Family Given
        if parts[0].upper() in ['HE', 'HUANG', 'ZHANG', 'LIU', 'CHEN', 'WANG', 'LI', 'YANG']:
            # Chinese: Given Name = parts[1], Family Name = parts[0]
            first = parts[1].capitalize()
            last = parts[0].capitalize()
        else:
            first = parts[0].capitalize()
            last = parts[1].capitalize()
    elif len(parts) == 3:
        # e.g. BAE JEONG EUN, KIM Hyeonyoung, NGUYEN HUY HOANG, CHARLY OSCAR MERKLE, FELIX MICHAEL PULM, LU THI NGOC, Liu Mengdan
        if parts[0].upper() in ['BAE', 'KIM', 'PARK', 'LEE', 'CHOI', 'JUNG']:
            # Korean: Family Given1 Given2
            last = parts[0].capitalize()
            first = f"{parts[1].capitalize()} {parts[2].capitalize()}".strip()
        elif parts[0].upper() in ['NGUYEN', 'TRAN', 'LE', 'PHAM', 'HOANG', 'VO', 'DANG', 'LU']:
            # Vietnamese: Family Middle Given
            last = parts[0].capitalize()
            first = f"{parts[1].capitalize()} {parts[2].capitalize()}".strip()
        elif parts[0].upper() in ['LIU', 'ZHANG', 'WANG', 'LI']:
            last = parts[0].capitalize()
            first = f"{parts[1].capitalize()} {parts[2].capitalize()}".strip()
        else:
            # Western: First Middle Last
            first = f"{parts[0].capitalize()} {parts[1].capitalize()}".strip()
            last = parts[2].capitalize()
    elif len(parts) >= 4:
        # e.g. Bricia Océane Céleste Nedzvedsky
        first = parts[0].capitalize()
        last = parts[-1].capitalize()
    else:
        first = parts[0].capitalize() if parts else ""
        last = "Unknown"

    clean_full_th = f"อ. {first} {last}".strip()
    print(f"  {fid} | '{raw_full}' -> first='{first}', last='{last}' | full_th='{clean_full_th}'")

    cur.execute("""
        UPDATE faculties
        SET first_name = %s,
            last_name = %s,
            academic_title_th = 'อ.',
            full_name_th = %s
        WHERE id = %s
    """, (first, last, clean_full_th, fid))

conn.commit()
conn.close()
print("Resolved all foreign faculty records successfully.")
