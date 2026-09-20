# -*- coding: utf-8 -*-
import urllib.request
import json
import ssl
import urllib.parse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 mailto:admin@advisor-match.th'}

tests = [
    ("Suree Chiang Mai", "Suree"),
    ("Piyarat Nimmanpipat", "Nimmanpipat"),
    ("Apinan Kanpiengjai", "Kanpiengjai"),
    ("Tinnakorn Kanyanee Chiang Mai", "Kanyanee"),
    ("Thanwadee Limtrakul", "Limtrakul"),
    ("Theeraboon Pojankarun", "Pojankarun"),
]

for q, target in tests:
    url = f"https://api.crossref.org/works?query={urllib.parse.quote(q)}&rows=3"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        items = data.get('message', {}).get('items', [])
        print(f"\nQuery: {q}")
        for it in items:
            authors = [(a.get('given'), a.get('family')) for a in it.get('author', [])]
            print(f"  cites={it.get('is-referenced-by-count', 0)} | {authors[:4]} | '{it.get('title', [''])[0][:50]}'")
    except Exception as e:
        print(f"Error: {e}")
