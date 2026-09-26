# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def check(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        strings = [s.strip() for s in soup.stripped_strings if len(s.strip()) > 2]
        print(f"=== {url} ({len(strings)} strings) ===")
        for s in strings[:30]:
            print("  ", s)

check("https://llc.hu.swu.ac.th/personal")
check("https://hpd.hu.swu.ac.th/personal")
