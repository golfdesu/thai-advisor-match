# -*- coding: utf-8 -*-
import json
import re
import urllib.request
import ssl
from bs4 import BeautifulSoup
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('cmu_med_raw.json', 'r', encoding='utf-8') as f:
    raw_med = json.load(f)

physio = [r for r in raw_med if r['department_th'] == 'ภาควิชาสรีรวิทยา']
print(f"Physiology records in DB: {len(physio)}")

req = urllib.request.Request('https://dept.med.cmu.ac.th/physiology/personnel-officer/', headers=headers)
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

for i, p in enumerate(physio, 1):
    th_name = p['full_name_th']
    last = th_name.split()[-1]
    first = th_name.split()[-2] if len(th_name.split()) >= 2 else th_name
    m = soup.find(string=lambda s: s and (last in s or first in s))
    print(f"\n[{i}/14] {th_name} (ID={p['id']}):")
    if m:
        card = m.parent
        for _ in range(6):
            if card and len(card.get_text()) > 100:
                break
            if card and card.parent:
                card = card.parent
        txt = card.get_text(separator=' | ', strip=True) if card else ''
        print(f"  Card text: {txt}")
        # Look for scholars link or CV
        links = card.find_all('a') if card else []
        for l in links:
            print(f"    Link: {l.text.strip()} -> {l.get('href')}")
    else:
        print("  Not found on page!")
