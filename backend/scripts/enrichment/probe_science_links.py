# -*- coding: utf-8 -*-
import urllib.request
import ssl
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

url = 'http://www.biology.science.cmu.ac.th/'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

print(f"Homepage len: {len(html)}")
matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.DOTALL)
for href, text in matches:
    clean = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()
    if any(k in href.lower() or k in clean.lower() for k in ['teacher', 'staff', 'person', 'อาจารย์', 'บุคลากร', 'en', 'member']):
        print(f"  {clean} -> {href}")
