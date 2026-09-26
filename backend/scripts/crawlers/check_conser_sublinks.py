# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for i in range(8, 20):
    u = f"http://g.hu.swu.ac.th/personal{i:02d}"
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=4) as resp:
            soup = BeautifulSoup(resp.read(), 'html.parser')
            title = soup.title.string.strip() if soup.title else ""
            print(f"[{resp.status}] {u} | {title} | len: {len(soup.get_text())}")
    except Exception as e:
        print(f"[{u}] -> {e}")
