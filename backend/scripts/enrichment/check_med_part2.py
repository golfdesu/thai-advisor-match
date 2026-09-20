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

# 1. Pathology (18)
patho = [r for r in raw_med if r['department_th'] == 'ภาควิชาพยาธิวิทยา']
print(f"Pathology records in DB: {len(patho)}")

req = urllib.request.Request('https://w1.med.cmu.ac.th/patho/about-us/medical-teacher/', headers=headers)
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

patho_mapped = {}
for p in patho:
    th_name = p['full_name_th']
    last = th_name.split()[-1]
    first = th_name.split()[-2] if len(th_name.split()) >= 2 else th_name
    m = soup.find(string=lambda s: s and last in s)
    if m:
        # Search surrounding container
        card = m.parent
        for _ in range(5):
            if card and len(card.get_text()) > 100:
                break
            if card and card.parent:
                card = card.parent
        txt = card.get_text(separator=' | ', strip=True) if card else ''
        # Find email
        em_m = re.search(r'[\w\.-]+@(?:cmu\.ac\.th|[\w\.-]+\.[a-zA-Z]{2,})', txt)
        email = em_m.group(0) if em_m else (p['email'] or f"{first.lower()}@cmu.ac.th")
        # Find English name
        en_m = re.search(r'(?:Prof\.|Assoc\.\s*Prof\.|Assist\.\s*Prof\.|Emeritus\s*Prof\.|Lect\.|Dr\.)\s*([A-Za-z\s]+?)(?:,\s*MD|,\s*PhD|\s*MD|\s*PhD|\||$)', txt)
        if en_m:
            en_full = en_m.group(1).strip()
            parts = en_full.split()
            en_first = parts[0]
            en_last = " ".join(parts[1:])
            patho_mapped[p['id']] = (en_first, en_last, email)
            print(f"  [OK] {th_name} -> {en_first} {en_last} ({email})")
        else:
            print(f"  [NO EN NAME] {th_name}: {txt[:100]}")
    else:
        print(f"  [NOT FOUND ON PAGE] {th_name}")

print(f"Pathology mapped: {len(patho_mapped)}/{len(patho)}")
