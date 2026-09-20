# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

with open('cmu_batch1_raw.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dent_results = {}
for r in data['คณะทันตแพทยศาสตร์']:
    url = r['profile_url']
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else ''
        m = re.search(r'\(([^)]+)\)', title)
        en_name = m.group(1).strip() if m else ''
        parts = en_name.split()
        first_name = parts[0] if parts else ''
        last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        dent_results[r['id']] = {'first_name': first_name, 'last_name': last_name, 'email': r['email']}
        print(f"{r['id']}: {r['full_name_th']} -> {first_name} {last_name} ({r['email']})")
    except Exception as e:
        print(f"{r['id']} error: {e}")

with open('dent_verified.json', 'w', encoding='utf-8') as f:
    json.dump(dent_results, f, ensure_ascii=False, indent=2)
