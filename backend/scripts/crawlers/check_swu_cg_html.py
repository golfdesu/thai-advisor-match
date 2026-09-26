# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://cg.hu.swu.ac.th/Faculty-and-Staff"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    strings = [s.strip() for s in soup.stripped_strings if len(s.strip()) > 3]
    for s in strings[:40]:
        print(s)
