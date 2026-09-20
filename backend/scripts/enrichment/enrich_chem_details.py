# -*- coding: utf-8 -*-
import urllib.request
import ssl
import re
import urllib.parse
import json
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

with open('chem_roster.json', 'r', encoding='utf-8') as f:
    roster = json.load(f)

with open('cmu_science_raw.json', 'r', encoding='utf-8') as f:
    raw_science = json.load(f)

chem_science = [r for r in raw_science if r['department_th'] == 'ภาควิชาเคมี']

print(f"Processing {len(chem_science)} Chemistry faculty...")

results = []
for i, fac in enumerate(chem_science, 1):
    clean_th = re.sub(r'^(?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)*\s*', '', fac['full_name_th']).strip()
    entry = roster.get(clean_th)
    if not entry:
        print(f"[{i}/{len(chem_science)}] Missing in roster: {clean_th}")
        continue

    url = entry['url']
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # Extract email: look for @cmu.ac.th
        emails = re.findall(r'[\w\.-]+@(?:cmu\.ac\.th|science\.cmu\.ac\.th|chem\.science\.cmu\.ac\.th)', html)
        # Filter out generic department emails like chem-sci@cmu.ac.th
        personal_emails = [e for e in emails if not e.startswith('chem-sci@')]
        found_email = personal_emails[0] if personal_emails else (fac.get('email') or None)

        # Extract English name or education
        # Ph.D. or B.Sc. lines often have English names or university
        edu_match = re.search(r'ประวัติการศึกษา(.*?)แนวทางการวิจัย', html, re.DOTALL)
        edu_text = ""
        if edu_match:
            edu_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', edu_match.group(1))).strip()

        # Research interests
        res_match = re.search(r'แนวทางการวิจัย(.*?)งานวิจัยเด่น', html, re.DOTALL)
        res_text = ""
        if res_match:
            res_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', res_match.group(1))).strip()

        results.append({
            'id': fac['id'],
            'full_name_th': fac['full_name_th'],
            'clean_th': clean_th,
            'email': found_email,
            'existing_email': fac.get('email'),
            'pid': entry['pid'],
            'edu_text': edu_text[:120],
            'res_text': res_text[:120]
        })
        print(f"[{i:2d}/{len(chem_science)}] {clean_th} -> email={found_email} | edu={edu_text[:40]}")
    except Exception as e:
        print(f"[{i:2d}/{len(chem_science)}] Error for {clean_th}: {e}")

with open('chem_enriched_details.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nCompleted {len(results)}/{len(chem_science)} Chemistry details")
