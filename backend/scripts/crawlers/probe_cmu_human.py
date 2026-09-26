# -*- coding: utf-8 -*-
import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.human.cmu.ac.th', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
    html = r.read().decode('utf-8', errors='ignore')

scripts = re.findall(r'src="(/_next/static/chunks/[^"]+)"', html)
for s in scripts:
    url = 'https://www.human.cmu.ac.th' + s
    try:
        r2 = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx, timeout=5)
        content = r2.read().decode('utf-8', errors='ignore')
        # check for keywords in thai or english
        matches = re.findall(r'[฀-๿]{4,}', content)
        if matches:
            print(f"File {s}: found {len(matches)} Thai words")
            # print unique words
            unique = list(dict.fromkeys(matches))[:15]
            print("  sample:", unique)
    except Exception as e:
        print(f"Error {s}: {e}")






