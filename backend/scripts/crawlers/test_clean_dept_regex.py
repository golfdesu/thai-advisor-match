# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def inspect_dept(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        # Clean text
        text = soup.get_text()
        # Find all patterns of Thai academic title
        pattern = r'((?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพ\.|ทพญ\.|นพ\.|พญ\.)[^\n\r]{2,30})'
        matches = re.findall(pattern, text)
        print(f"=== {url} ===")
        for m in matches[:15]:
            print("  ", m.strip())

inspect_dept("https://www.dent.psu.ac.th/unit/oral/index.php/staff/")
inspect_dept("https://www.dent.psu.ac.th/unit/prevent/index.php/staff/")
inspect_dept("https://www.dent.psu.ac.th/unit/surgery/index.php/staff/")
inspect_dept("https://www.dent.psu.ac.th/unit/stoma/index.php/staff/")
inspect_dept("https://www.dent.psu.ac.th/unit/prost/staff/")
