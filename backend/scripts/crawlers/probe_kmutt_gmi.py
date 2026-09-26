# -*- coding: utf-8 -*-
import urllib.request, ssl, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

req = urllib.request.Request('https://www.gmi.kmutt.ac.th/', headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    soup = BeautifulSoup(r.read(), 'html.parser')

links = soup.find_all('a', href=True)
for a in links:
    text = a.get_text(strip=True)
    href = a['href']
    if any(k in text for k in ['อาจารย์', 'บุคลากร', 'ผู้สอน', 'ทีม', 'เกี่ยวกับ', 'คณะ']):
        print(f'{text} -> {href}')
