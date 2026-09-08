# -*- coding: utf-8 -*-
import sys, urllib.parse
sys.path.append('backend')
from scripts.fetch_openalex_publication_metrics import fetch_with_retry

names = [
    ("Jaturong Napathorn", "จตุรงค์ นภาธร"),
    ("Suntonrapot Damrongpanich", "สุนทรพจน์ ดำรงค์พานิช"),
    ("Yada Dejchai", "ญาดา เดชชัย"),
    ("Wattana Saengsuwan", "วัฒนชัย แสงสุวรรณ"),
    ("Somkiart Intasing", "สมเกียรติ อินทสิงห์"),
    ("Nampueng Intanet", "น้ำผึ้ง อินทะเนตร"),
    ("Veeraya Kamruengrit", "วีรยา คำเรืองฤทธิ์")
]

for en, th in names:
    enc = urllib.parse.quote(en)
    url = f"https://api.openalex.org/works?filter=raw_author_name.search:{enc}&sort=cited_by_count:desc&per_page=5"
    d = fetch_with_retry(url)
    res = d.get('results', [])
    print(f"Results for {th} ({en}): {len(res)} works")
    for w in res[:3]:
        print(f"   -> {w.get('title')} ({w.get('publication_year')}) | Cited: {w.get('cited_by_count')}")
