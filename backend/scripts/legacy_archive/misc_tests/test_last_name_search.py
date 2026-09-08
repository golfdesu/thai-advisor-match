# -*- coding: utf-8 -*-
import sys, urllib.parse
sys.path.append('backend')
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

test_names = [
    ("Wanwisa Udomsinprasert", "Udomsinprasert"),
    ("Pitchaya Dilokpatanamongkol", "Dilokpatanamongkol"),
    ("Kanokwan Kiatisin", "Kiatisin"),
    ("Kritsakorn Phongraktham", "Phongraktham"),
    ("Kanchanasit Thonglek", "Thonglek"),
    ("It Assoratkul", "Assoratkul"),
    ("Nopadol Rompho", "Rompho"),
    ("Nopporn Ruangvanich", "Ruangvanich"),
    ("Prinya Thaewanarumitkul", "Thaewanarumitkul"),
    ("Pokpong Srisanit", "Srisanit"),
    ("Veeraya Kamruengrit", "Kamruengrit"),
    ("Kongsajja Suwanphet", "Suwanphet"),
    ("Thapanan Niphitkun", "Niphitkun")
]

for full, last in test_names:
    enc = urllib.parse.quote(last)
    url = f"https://api.openalex.org/works?filter=raw_author_name.search:{enc}&sort=cited_by_count:desc&per_page=3"
    data = fetch_with_retry(url)
    results = data.get("results", [])
    print(f"\n{full} (Last: {last}) -> {len(results)} works found:")
    for r in results:
        t = r.get("title")
        year = r.get("publication_year")
        cites = r.get("cited_by_count")
        # Check matching author in authorships
        matched_auth = []
        for a in r.get("authorships", []):
            raw_a = a.get("raw_author_name") or ""
            if last.lower() in raw_a.lower():
                matched_auth.append(raw_a)
        print(f"   [{cites} cites] {t} ({year}) | Matched authors: {matched_auth}")
