# -*- coding: utf-8 -*-
import sys, urllib.request, urllib.parse, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "ThaiEduCenter/2.0"}

test_scholars = [
    "Yodyium Tipsuwan",
    "Wanwisa Udomsinprasert",
    "Prinya Thaewanarumitkul",
    "Pokpong Srisanit",
    "Petchara Pattarakijwanich"
]

for name in test_scholars:
    enc = urllib.parse.quote(name)
    url = f"https://api.semanticscholar.org/graph/v1/author/search?query={enc}&fields=name,affiliations,paperCount,citationCount,papers.title,papers.year,papers.citationCount,papers.venue&limit=2"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            d = json.loads(r.read().decode())
            authors = d.get("data", [])
            print(f"\nSemantic Scholar: {name} -> {len(authors)} authors matched")
            for a in authors[:1]:
                print(f"  Author: {a.get('name')} | Total Papers: {a.get('paperCount')} | Citations: {a.get('citationCount')}")
                for p in a.get("papers", [])[:3]:
                    print(f"    * {p.get('title')} ({p.get('year')}) [{p.get('citationCount')} cites] - {p.get('venue')}")
    except Exception as e:
        print(f"Error for {name}: {e}")
