# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0"}

def test_url(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title.string.strip() if soup.title else ""
            text = soup.get_text()
            matches = re.findall(r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*[ก-๙]{3,30}\s+[ก-๙]{3,30})', text)
            print(f"[{resp.status}] {url} | Title: {title} | Matches: {len(matches)}")
            for m in matches[:4]:
                print(f"    {m.strip()}")
    except Exception as e:
        print(f"[FAIL] {url} : {e}")

urls = [
    "http://g.hu.swu.ac.th/personal01",
    "http://g.hu.swu.ac.th/personal02",
    "http://g.hu.swu.ac.th/personal03",
    "http://g.hu.swu.ac.th/personal04",
    "http://g.hu.swu.ac.th/personal05",
    "http://g.hu.swu.ac.th/personal06",
    "http://g.hu.swu.ac.th/personal07",
    "https://cgs.hu.swu.ac.th/people/en",
    "https://cgs.hu.swu.ac.th/people/th",
    "https://cgs.hu.swu.ac.th/people/ling",
    "https://hpd.hu.swu.ac.th/personal",
    "https://cg.hu.swu.ac.th/personal"
]

for u in urls:
    test_url(u)
