# -*- coding: utf-8 -*-
import sys, urllib.parse, json
sys.path.append('backend')
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

names = [
    "Napathorn",
    "Damrongpanich",
    "Thienprasit",
    "Saengsuwan",
    "Intasing",
    "Intanet"
]

for ln in names:
    enc = urllib.parse.quote(ln)
    url = f"https://api.openalex.org/works?filter=raw_author_name.search:{enc},institutions.country_code:TH&sort=cited_by_count:desc&per_page=5"
    d = fetch_with_retry(url)
    res = d.get('results', [])
    print(f"Results for lastname '{ln}' in TH: {len(res)} works")
    for w in res[:2]:
        authors = [a.get('raw_author_name') for a in w.get('authorships', [])]
        print(f"   -> {w.get('title')[:60]} | Authors: {authors[:3]}")
