# -*- coding: utf-8 -*-
import sys, urllib.request, urllib.parse, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "Mozilla/5.0"}

test_names = [
    "ฐาปนันท์ นิพิฏฐกุล",
    "คงสัจจา สุวรรณเพ็ชร",
    "นพพร เรืองวานิช",
    "อารยา บัวบาล",
    "ว่องวิช ขวัญพัทลุง",
    "ชาตรี เรืองเดชณรงค์",
    "วีรยา คำเรืองฤทธิ์"
]

journals = [
    ("TU Law", "https://so05.tci-thaijo.org/index.php/tulawjournal/search/search"),
    ("Chula Law", "https://so05.tci-thaijo.org/index.php/LAWCHULAJOURNAL/search/search"),
    ("CMU Law", "https://so01.tci-thaijo.org/index.php/lawcmu/search/search"),
    ("TBS Journal", "https://so02.tci-thaijo.org/index.php/tbsjournal/search/search"),
    ("CMU Ed", "https://so01.tci-thaijo.org/index.php/cmujed/search/search")
]

for name in test_names:
    print(f"\nAuthor: {name}")
    enc = urllib.parse.quote(name)
    found_any = False
    for jtitle, jurl in journals:
        url = f"{jurl}?query={enc}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=4, context=ctx) as res:
                html = res.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'<a\s+(?:id="article-\d+"\s+)?href="([^"]+)"[^>]*>\s*(.*?)\s*</a>', html, re.DOTALL)
                valid = []
                for link, raw_title in matches:
                    clean_t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw_title)).strip()
                    if clean_t and not any(skip in clean_t.lower() for skip in ["pdf", "view", "download", "login", "register"]):
                        valid.append((link, clean_t))
                if valid:
                    found_any = True
                    print(f"  [{jtitle}] {len(valid)} found:")
                    for l, t in valid[:2]:
                        print(f"    - {t[:80]}")
        except Exception:
            continue
    if not found_any:
        print("  (No direct matches in these 5 journals)")
