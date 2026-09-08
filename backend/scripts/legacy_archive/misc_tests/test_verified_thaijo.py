# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "Mozilla/5.0"}

test_authors = [
    "ฐาปนันท์ นิพิฏฐกุล",
    "คงสัจจา สุวรรณเพ็ชร",
    "นพพร เรืองวานิช",
    "อารยา บัวบาล",
    "ว่องวิช ขวัญพัทลุง",
    "ศักดิ์ชาย จินะวงค์",
    "ชาตรี เรืองเดชณรงค์",
    "ปกป้อง ศรีสนิท",
    "กิตติศักดิ์ เจกมนตรี",
    "ปริญญา เทวานฤมิตรกุล"
]

journals = [
    ("วารสารนิติศาสตร์ มธ.", "https://so05.tci-thaijo.org/index.php/tulawjournal/search/search"),
    ("วารสารกฎหมาย จุฬาฯ", "https://so05.tci-thaijo.org/index.php/LAWCHULAJOURNAL/search/search"),
    ("วารสารนิติศาสตร์ มช.", "https://so01.tci-thaijo.org/index.php/lawcmu/search/search")
]

for author in test_authors:
    print(f"\nSearching for: {author}")
    enc = urllib.parse.quote(author)
    for jtitle, jurl in journals:
        url = f"{jurl}?query={enc}&authors={enc}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5, context=ctx) as res:
                html = res.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'<h3[^>]*class="title"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>\s*(.*?)\s*</a>', html, re.DOTALL)
                author_matches = re.findall(r'<div[^>]*class="authors"[^>]*>\s*(.*?)\s*</div>', html, re.DOTALL)

                valid_articles = []
                for idx, (link, raw_t) in enumerate(matches):
                    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw_t)).strip()
                    auth = ""
                    if idx < len(author_matches):
                        auth = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", author_matches[idx])).strip()
                    # Check if author matches target
                    if any(part in auth for part in author.split() if len(part) >= 3):
                        valid_articles.append((link, t, auth))

                if valid_articles:
                    print(f"  [{jtitle}] Matched {len(valid_articles)} authentic papers:")
                    for l, t, a in valid_articles:
                        print(f"    - \"{t}\" by {a} ({l})")
        except Exception as e:
            pass
