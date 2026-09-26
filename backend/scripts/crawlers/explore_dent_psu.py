# -*- coding: utf-8 -*-
import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.dent.psu.ac.th/dent/department/', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

links = set(re.findall(r'href=[\'"]([^\'"]+)[\'"]', html))
print("Department links on /dent/department/:")
for l in sorted(links):
    if any(k in l.lower() for k in ['dept', 'department', 'unit', 'staff', 'ortho', 'pedo', 'perio', 'oral', 'prostho']):
        print(" ", l)
