# -*- coding: utf-8 -*-
import urllib.request
import ssl
import re
import urllib.parse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

url = 'http://www.chem.science.cmu.ac.th/personnel/2/' + urllib.parse.quote('คณาจารย์')
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Match links: ./person-detail/{num}/{thai_name}
links = re.findall(r'href=["\'](\./person-detail/(\d+)/([^"\'#]+))["\']', html)
print(f"Total raw links: {len(links)}")

roster = {}
for full_href, pid, raw_name in links:
    clean_name = raw_name.replace('-', ' ').strip()
    if clean_name not in roster:
        roster[clean_name] = {
            'pid': pid,
            'url': f"http://www.chem.science.cmu.ac.th/person-detail/{pid}/{urllib.parse.quote(raw_name)}"
        }

print(f"Unique faculty in Chem roster: {len(roster)}")
with open('chem_roster.json', 'w', encoding='utf-8') as f:
    json.dump(roster, f, ensure_ascii=False, indent=2)

with open('cmu_science_raw.json', 'r', encoding='utf-8') as f:
    raw_science = json.load(f)

chem_science = [r for r in raw_science if r['department_th'] == 'ภาควิชาเคมี']
matched = 0
for r in chem_science:
    # strip title
    name = re.sub(r'^(?:ศ\.|รศ\.|ผศ\.|อ\.)\s*(?:ดร\.)*\s*', '', r['full_name_th']).strip()
    if name in roster:
        matched += 1
    else:
        print(f"Unmatched: {name}")

print(f"\nMatched with Chem website: {matched}/{len(chem_science)}")
