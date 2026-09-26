# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def inspect_page(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        print(f"=== {url} ===")
        # Look for text in tables, cards, or headings
        lines = [s.strip() for s in soup.stripped_strings if len(s.strip()) > 3]
        for l in lines[:40]:
            print("  ", l)

inspect_page("https://www.dent.psu.ac.th/unit/conser/index.php/personnel/")
inspect_page("https://www.dent.psu.ac.th/unit/prost/staff/")
