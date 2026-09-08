# -*- coding: utf-8 -*-
import sys, urllib.parse
sys.path.append('backend')
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

test_names = [
    "Pitchaya Dilokpatanamongkol",
    "Kanokwan Kiatisin",
    "Wanwisa Udomsinprasert",
    "Yodyium Tipsuwan",
    "Kanchanasit Thonglek"
]

for name in test_names:
    enc = urllib.parse.quote(name)
    data = fetch_with_retry(f"https://api.openalex.org/authors?search={enc}&per_page=3")
    results = data.get("results", [])
    print(f"{name} -> {len(results)} results")
    for r in results:
        print(f"   {r.get('display_name')} ({r.get('works_count')} works) [{r.get('id')}]")
