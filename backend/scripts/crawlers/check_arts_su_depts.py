# -*- coding: utf-8 -*-
import urllib.request, ssl, re
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

dept_urls = [
    ('ผู้บริหาร', 'https://arts.su.ac.th/?page_id=33'),
    ('ภาควิชานาฏยสังคีต', 'https://arts.su.ac.th/?page_id=679'),
    ('ภาควิชาบรรณารักษศาสตร์', 'https://arts.su.ac.th/?page_id=859'),
    ('ภาควิชาประวัติศาสตร์', 'https://arts.su.ac.th/?page_id=1010'),
    ('ภาควิชาปรัชญา', 'https://arts.su.ac.th/?page_id=1299'),
    ('ภาควิชาภาษาไทย', 'https://arts.su.ac.th/?page_id=1332'),
    ('ภาควิชาภาษาปัจจุบันตะวันออก', 'https://arts.su.ac.th/?page_id=1436'),
    ('ภาควิชาภาษาฝรั่งเศส', 'https://arts.su.ac.th/?page_id=1687'),
    ('ภาควิชาภาษาเยอรมัน', 'https://arts.su.ac.th/?page_id=1722'),
    ('ภาควิชาภาษาอังกฤษ', 'https://arts.su.ac.th/?page_id=1757'),
    ('ภาควิชาภูมิศาสตร์', 'https://arts.su.ac.th/?page_id=1843'),
    ('ภาควิชาสังคมศาสตร์', 'https://arts.su.ac.th/?page_id=1872'),
]

all_profiles = {}

for dname, u in dept_urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            soup = BeautifulSoup(r.read(), 'html.parser')
            # Look for article or links with ?page_id=
            links = []
            for art in soup.find_all('article'):
                h2 = art.find(['h2', 'h3'])
                a = art.find('a', href=True)
                img = art.find('img')
                img_src = img['src'] if img and 'src' in img.attrs else ''
                if h2 and h2.find('a'):
                    name_th = h2.get_text(strip=True)
                    href = h2.find('a')['href']
                    links.append((name_th, href, img_src))
                elif a:
                    name_th = a.get_text(strip=True)
                    href = a['href']
                    if name_th:
                        links.append((name_th, href, img_src))

            # also for page_id=33 (executives)
            if u.endswith('33'):
                # parse executive blocks
                for tr in soup.find_all(['tr', 'div', 'p']):
                    text = tr.get_text(separator='|', strip=True)
                    if '@su.ac.th' in text:
                        parts = [p.strip() for p in text.split('|') if p.strip()]
                        # e.g. name, role, email
                        # let's see
                        pass

            print(f"[{dname}] found {len(links)} profile cards")
            for name, href, img in links:
                if href not in all_profiles:
                    all_profiles[href] = {
                        'name': name,
                        'dept': dname,
                        'img': img
                    }
    except Exception as e:
        print(f"Error {dname} ({u}): {e}")

print(f"\nTotal unique faculty profiles across Silpakorn Arts: {len(all_profiles)}")
