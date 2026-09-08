# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, re, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

names = ['กิตติวัฒน์ จันทร์แจ่มใส', 'ทวีศักดิ์ เอื้ออมรวนิช', 'ธีระรัตน์ จีระวัฒนา', 'กมลวรรณ จิรวิศิษฎ์']
for n in names:
    url = f'https://so05.tci-thaijo.org/index.php/tulawjournal/search/search?query={urllib.parse.quote(n)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=5, context=ctx) as res:
            html = res.read().decode('utf-8', errors='ignore')
            titles = re.findall(r'<h3 class="title">\s*<a[^>]*>(.*?)</a>', html, re.DOTALL)
            clean = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip() for t in titles]
            print(f"{n}: {len(clean)} articles")
            for c in clean[:2]:
                print("   -", c[:70])
    except Exception as e:
        print(f"{n}: error {e}")
