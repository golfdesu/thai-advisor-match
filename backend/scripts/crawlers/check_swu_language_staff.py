# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0"}

urls = [
    "http://g.hu.swu.ac.th/personal01",
    "https://g.hu.swu.ac.th/personal05",
    "http://g.hu.swu.ac.th/personal03"
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            # Extract names with title
            text = soup.get_text()
            matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*[ก-๙]{3,30}\s+[ก-๙]{3,30})', text)
            print(f"=== {u} ===")
            print(f"  Matched {len(matches)} faculty names:")
            for m in matches[:6]:
                print(f"    - {m.strip()}")
    except Exception as e:
        print(f"Error {u}: {e}")
