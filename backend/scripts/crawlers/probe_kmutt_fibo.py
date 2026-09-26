# -*- coding: utf-8 -*-
import urllib.request, ssl, re, json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

detail_urls = [
    'https://fibo.kmutt.ac.th/%e0%b8%a3%e0%b8%a8-%e0%b8%94%e0%b8%a3-%e0%b8%aa%e0%b8%a2%e0%b8%b2%e0%b8%a1-%e0%b9%80%e0%b8%88%e0%b8%a3%e0%b8%b4%e0%b8%8d%e0%b9%80%e0%b8%aa%e0%b8%b5%e0%b8%a2%e0%b8%87-assoc-prof-dr-siam-charoensea/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%9b%e0%b8%a3%e0%b8%b2%e0%b8%81%e0%b8%b2%e0%b8%a3%e0%b9%80%e0%b8%81%e0%b8%b5%e0%b8%a2%e0%b8%a3%e0%b8%95%e0%b8%b4-%e0%b8%a2%e0%b8%b1%e0%b8%87%e0%b8%84%e0%b8%87-dr-prakarnkiat/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%ad%e0%b8%b2%e0%b8%9a%e0%b8%97%e0%b8%b4%e0%b8%9e%e0%b8%a2%e0%b9%8c-%e0%b8%98%e0%b8%b5%e0%b8%a3%e0%b8%a7%e0%b8%87%e0%b8%a8%e0%b9%8c%e0%b8%81%e0%b8%b4%e0%b8%88-dr-arbtip-dheer/',
    'https://fibo.kmutt.ac.th/%e0%b8%9c%e0%b8%a8-%e0%b8%94%e0%b8%a3-%e0%b9%80%e0%b8%ad%e0%b8%81%e0%b8%8a%e0%b8%b1%e0%b8%a2-%e0%b9%80%e0%b8%9b%e0%b9%87%e0%b8%87%e0%b8%a7%e0%b8%b1%e0%b8%87-asst-prof-dr-eakkachai-pengwang/',
    'https://fibo.kmutt.ac.th/%e0%b8%9c%e0%b8%a8-%e0%b8%94%e0%b8%a3-%e0%b8%ad%e0%b8%a3%e0%b8%9e%e0%b8%94%e0%b8%b5-%e0%b8%88%e0%b8%b9%e0%b8%89%e0%b8%b4%e0%b8%a1-asst-dr-orapadee-joochim/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%a7%e0%b8%a3%e0%b8%b2%e0%b8%aa%e0%b8%b4%e0%b8%93%e0%b8%b5-%e0%b8%89%e0%b8%b2%e0%b8%a2%e0%b9%81%e0%b8%aa%e0%b8%87%e0%b8%a1%e0%b8%87%e0%b8%84%e0%b8%a5-dr-warasinee-chaisangmongk/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%93%e0%b8%a3%e0%b8%87%e0%b8%84%e0%b8%a8%e0%b8%81%e0%b8%94-%e0%b8%96%e0%b8%a3%e0%b8%aa%e0%b8%99%e0%b8%97%e0%b8%a3%e0%b8%b2%e0%b8%81%e0%b8%a5-dr-narongsak-tirasuntarakul/',
    'https://fibo.kmutt.ac.th/%e0%b8%99%e0%b8%b2%e0%b8%87%e0%b8%aa%e0%b8%b2%e0%b8%a7%e0%b8%9e%e0%b8%b9%e0%b8%99%e0%b8%aa%e0%b8%b4%e0%b8%a3%e0%b8%b4-%e0%b9%83%e0%b8%88%e0%b8%a5%e0%b8%b1%e0%b8%87%e0%b8%81%e0%b8%b2%e0%b8%a3%e0%b9%8c/',
    'https://fibo.kmutt.ac.th/%e0%b8%99%e0%b8%b2%e0%b8%a2%e0%b8%87%e0%b8%8a%e0%b8%b2%e0%b8%a7%e0%b8%a5%e0%b8%b4%e0%b8%95-%e0%b8%98%e0%b8%a3%e0%b8%a3%e0%b8%a1%e0%b8%97%e0%b8%b4%e0%b8%99%e0%b9%82%e0%b8%99-mr-chaowwalit-thammatinno/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%9b%e0%b8%b4%e0%b8%95%e0%b8%b4%e0%b8%a7%e0%b8%b8%e0%b8%92%e0%b8%8d%e0%b9%8c-%e0%b8%98%e0%b8%b5%e0%b8%a3%e0%b8%81%e0%b8%b4%e0%b8%95%e0%b8%95%e0%b8%b4%e0%b8%81%e0%b8%b8%e0%b8%a5/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%9a%e0%b8%b8%e0%b8%8d%e0%b8%91%e0%b8%a3%e0%b8%b4%e0%b8%81%e0%b8%b2-%e0%b9%80%e0%b8%81%e0%b8%a9%e0%b8%a1%e0%b8%aa%e0%b8%b1%e0%b8%99%e0%b8%95%e0%b8%b4%e0%b8%98%e0%b8%a3%e0%b8%a3/',
    'https://fibo.kmutt.ac.th/%e0%b8%94%e0%b8%a3-%e0%b8%aa%e0%b8%b8%e0%b8%a3%e0%b8%b4%e0%b8%a2%e0%b8%b2-%e0%b8%99%e0%b8%b1%e0%b8%8f%e0%b8%aa%e0%b8%b8%e0%b8%a0%e0%b8%b1%e0%b8%84%e0%b8%9e%e0%b8%87%e0%b8%a8%e0%b9%8c-dr-suriya-natsu/'
]

def fetch_detail(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        soup = BeautifulSoup(r.read(), 'html.parser')
    emails = [e.lower() for e in re.findall(r'[a-zA-Z0-9._%+-]+@(?:kmutt\.ac\.th|mail\.kmutt\.ac\.th|fibo\.kmutt\.ac\.th)', str(soup)) if e.lower() != 'fibo@kmutt.ac.th']
    h = soup.find(['h1', 'h2', 'h3'])
    title_text = h.get_text(strip=True) if h else ""
    return url, title_text, set(emails)

with ThreadPoolExecutor(max_workers=6) as ex:
    results = ex.map(fetch_detail, detail_urls)

for u, title, emails in results:
    print(f"{title[:50]} -> {emails}")
