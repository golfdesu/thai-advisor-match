# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "http://hu.swu.ac.th/academic/teacher"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    strings = [s.strip() for s in soup.stripped_strings if len(s.strip()) > 3]
    print(f"Length of strings: {len(strings)}")
    for s in strings[:60]:
        print("  ", s)
