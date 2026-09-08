# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, re

q = 'site:tci-thaijo.org "ญาดา เดชชัย"'
url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'<h2 class="result__title">\s*<a[^>]*>(.*?)</a>', html, re.DOTALL)
        print("DuckDuckGo results:", len(titles))
        for t, s in zip(titles[:3], snippets[:3]):
            clean_t = re.sub(r'<[^>]+>', '', t).strip()
            clean_s = re.sub(r'<[^>]+>', '', s).strip()
            print("Title:", clean_t)
            print("Snippet:", clean_s[:80])
except Exception as e:
    print("Error:", e)
