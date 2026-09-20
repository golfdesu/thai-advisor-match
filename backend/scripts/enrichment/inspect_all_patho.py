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

patho = [r for r in raw_med if r['department_th'] == 'ภาควิชาพยาธิวิทยา']

req = urllib.request.Request('https://w1.med.cmu.ac.th/patho/about-us/medical-teacher/', headers=headers)
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

for i, p in enumerate(patho, 1):
    th_name = p['full_name_th']
    last = th_name.split()[-1]
    m = soup.find(string=lambda s: s and last in s)
    print(f"\n[{i}/18] {th_name} (ID={p['id']}):")
    if m:
        card = m.parent
        for _ in range(5):
            if card and len(card.get_text()) > 100:
                break
            if card and card.parent:
                card = card.parent
        print(f"  Card: {card.get_text(separator=' | ', strip=True) if card else ''}")
    else:
        print("  Not found on page!")
