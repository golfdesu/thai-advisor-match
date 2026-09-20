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

req = urllib.request.Request('https://dept.med.cmu.ac.th/physiology/personnel-officer/', headers=headers)
html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

# Look at all 'a' tags with 'ข้อมูลเพิ่มเติม'
links = soup.find_all('a', string=re.compile(r'ข้อมูลเพิ่มเติม'))
print(f"Total 'ข้อมูลเพิ่มเติม' links: {len(links)}")

physio_portal_data = []
for a in links:
    url = a.get('href', '')
    # URL format: https://scholars.med.cmu.ac.th/LastName/FirstName/ or similar
    # Find preceding text/name
    p = a.find_parent('div')
    for _ in range(3):
        if p and len(p.get_text()) > 50:
            break
        if p and p.parent:
            p = p.parent
    txt = p.get_text(separator=' | ', strip=True) if p else ''
    # Find email
    em_m = re.search(r'[\w\.-]+@(?:cmu\.ac\.th|[\w\.-]+\.[a-zA-Z]{2,})', txt)
    email = em_m.group(0) if em_m else ''
    physio_portal_data.append((url, email, txt))

for u, em, txt in physio_portal_data:
    print(f"\nURL: {u} | Email: {em}")
    print(f"  Text: {txt[:120]}")
