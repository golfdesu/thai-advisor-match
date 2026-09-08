# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

url = "https://so05.tci-thaijo.org/index.php/tulawjournal/search/search?query=" + urllib.parse.quote("กฎหมาย")
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=6, context=ctx) as res:
        html = res.read().decode("utf-8", errors="ignore")
        print(f"HTML length: {len(html)}")

        # Search for article titles or authors
        # In OJS 3: <h3 class="title"> <a href="..."> title </a> </h3>
        titles = re.findall(r'<h3[^>]*class="title"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>\s*(.*?)\s*</a>', html, re.DOTALL)
        print(f"h3.title articles: {len(titles)}")
        for l, t in titles[:3]:
            clean = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()
            print("  h3 title:", clean)

        # Search for authors
        authors = re.findall(r'<div[^>]*class="authors"[^>]*>\s*(.*?)\s*</div>', html, re.DOTALL)
        print(f"authors divs: {len(authors)}")
        for a in authors[:3]:
            clean = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", a)).strip()
            print("  author:", clean)
except Exception as e:
    print("Error:", e)
