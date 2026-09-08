# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

q = "ญาดา เดชชัย"
params = urllib.parse.urlencode({"query": q})
url = f"https://so05.tci-thaijo.org/index.php/tulawjournal/search/search?{params}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
res = urllib.request.urlopen(req, timeout=5, context=ctx)
html = res.read().decode("utf-8", errors="ignore")

# Extract article links and text with clean regex
pattern = re.compile(r'<a\s+id="article-\d+"\s+href="([^"]+)">\s*(.*?)\s*</a>', re.DOTALL)
articles = pattern.findall(html)
print(f"Extracted {len(articles)} articles!")
for link, title in articles:
    clean_t = re.sub(r"\s+", " ", title).strip()
    print("  -", clean_t[:80])
