# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://llc.hu.swu.ac.th/personal"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text().strip()
        if any(w in text for w in ['ภาษา', 'บุคลากร', 'คณาจารย์']):
            print(f"{text} -> {href}")
