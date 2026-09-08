# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
q = "ญาดา เดชชัย"
url = f"https://so05.tci-thaijo.org/index.php/tulawjournal/search/search?query={urllib.parse.quote(q)}"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=5) as res:
        html = res.read().decode('utf-8', errors='ignore')
        # Extract article titles from search results
        titles = re.findall(r'<h3 class="title">\s*<a[^>]*>(.*?)</a>', html, re.DOTALL)
        clean_titles = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip() for t in titles]
        print(f"ThaiJO search for '{q}': {len(clean_titles)} articles found")
        for ct in clean_titles:
            print("  -", ct)
except Exception as e:
    print("Error:", e)
