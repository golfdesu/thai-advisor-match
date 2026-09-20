# -*- coding: utf-8 -*-
import urllib.request
import json
import ssl
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 mailto:admin@advisor-match.th'}

for query in ["Arayasakul", "Panjakhan", "Mookjaeng", "Chayaphakdee"]:
    url = f"https://api.crossref.org/works?query.author={query}&rows=3"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    print(f"\nQuery: {query}")
    for it in data['message']['items'][:3]:
        print("  Title:", it.get('title', [''])[0][:50])
        print("  Authors:", [(a.get('given'), a.get('family')) for a in it.get('author', [])[:4]])
