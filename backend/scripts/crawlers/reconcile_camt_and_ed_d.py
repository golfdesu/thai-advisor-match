# -*- coding: utf-8 -*-
"""
Reconciliation script:
1. Merge duplicate email records for Pitipong Yodmongkol and Wipawinee Chaiwino
2. Clean Ed.D / credential suffixes in SWU Faculty of Education faculty names
"""

import psycopg2
import re

conn = psycopg2.connect('postgresql://postgres:postgres@db:5432/advisor_match')
cur = conn.cursor()

# 1. Merge Pitipong Yodmongkol
print("Merging Pitipong Yodmongkol...")
# Check both records
cur.execute("SELECT id, full_name_th, email, total_citations, h_index, openalex_id FROM faculties WHERE id IN ('cmu_spp__023', 'chia_ground_yodmongkol_0d57ba')")
rows = cur.fetchall()
print("Pitipong rows:", rows)

# Keep chia_ground_yodmongkol_0d57ba (has Thai name and CAMT affiliation), repoint any lab lead
cur.execute("UPDATE research_labs SET lead_advisor_id = 'chia_ground_yodmongkol_0d57ba' WHERE lead_advisor_id = 'cmu_spp__023'")
cur.execute("DELETE FROM faculties WHERE id = 'cmu_spp__023'")
print("Merged cmu_spp__023 into chia_ground_yodmongkol_0d57ba")

# 2. Merge Wipawinee Chaiwino
print("\nMerging Wipawinee Chaiwino...")
cur.execute("SELECT id, full_name_th, email, total_citations, h_index, openalex_id FROM faculties WHERE id IN ('cmu_700d1c7d_5607', 'cmu_camt_a5b774c050')")
rows = cur.fetchall()
print("Wipawinee rows:", rows)

# Transfer metrics from cmu_camt_a5b774c050 to cmu_700d1c7d_5607 or keep cmu_camt_a5b774c050
# Let's check which has better data
r1, r2 = rows[0], rows[1]
donor_id = 'cmu_camt_a5b774c050'
target_id = 'cmu_700d1c7d_5607'

cur.execute("""
    UPDATE faculties target
    SET openalex_id = COALESCE(target.openalex_id, donor.openalex_id),
        total_citations = GREATEST(COALESCE(target.total_citations, 0), COALESCE(donor.total_citations, 0)),
        h_index = GREATEST(COALESCE(target.h_index, 0), COALESCE(donor.h_index, 0)),
        total_publications_count = GREATEST(COALESCE(target.total_publications_count, 0), COALESCE(donor.total_publications_count, 0)),
        image_url = COALESCE(target.image_url, donor.image_url),
        profile_url = COALESCE(target.profile_url, donor.profile_url),
        department_th = COALESCE(donor.department_th, target.department_th),
        academic_title_th = COALESCE(donor.academic_title_th, target.academic_title_th),
        full_name_th = COALESCE(donor.full_name_th, target.full_name_th)
    FROM faculties donor
    WHERE target.id = %s AND donor.id = %s
""", (target_id, donor_id))

cur.execute("UPDATE research_labs SET lead_advisor_id = %s WHERE lead_advisor_id = %s", (target_id, donor_id))
cur.execute("DELETE FROM faculties WHERE id = %s", (donor_id,))
print(f"Merged {donor_id} into {target_id}")

# 3. Clean credential suffixes
print("\nCleaning credential suffixes...")
suffixes = ['Ed.D', 'Ph.D', 'M.Sc', 'B.Sc', 'M.Eng', 'B.Eng', 'D.Eng', 'Cert.', 'M.D.', 'Diplomate', 'Fellow', 'D.D.S', 'M.A.', 'B.A.']
for s in suffixes:
    pat = re.compile(rf'\s+{re.escape(s)}$', re.IGNORECASE)
    cur.execute(f"SELECT id, last_name FROM faculties WHERE last_name ILIKE '%{s}%'")
    matches = cur.fetchall()
    for fid, lname in matches:
        cleaned = re.sub(rf'\s+{re.escape(s)}$', '', lname, flags=re.IGNORECASE).strip()
        cleaned = cleaned.capitalize()
        cur.execute("UPDATE faculties SET last_name = %s WHERE id = %s", (cleaned, fid))
        print(f"  Cleaned {fid}: '{lname}' -> '{cleaned}'")

conn.commit()
conn.close()
print("\nReconciliation complete.")
