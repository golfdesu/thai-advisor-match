# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

with open('cmu_batch1_raw.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Test AMS URLs
urls_to_test = [
    'https://ot.ams.cmu.ac.th/index.php?module=academicstaff&lang=en',
    'https://ams.cmu.ac.th/staff.php',
    'https://ams.cmu.ac.th/index.php?module=staff',
    'https://ams.cmu.ac.th/en/staff'
]

for url in urls_to_test:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"SUCCESS {url}: {len(html)} bytes")
    except Exception as e:
        print(f"FAILED {url}: {e}")
