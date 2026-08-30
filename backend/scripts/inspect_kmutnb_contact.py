import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Fetch contact-curriculum page from admission portal
r = requests.get('https://admission.kmutnb.ac.th/contact-curriculum', headers=headers, timeout=15, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')

print(f"Status: {r.status_code}")
links = soup.find_all('a', href=True)
print(f"Links found: {len(links)}")
for a in links:
    href = a['href']
    txt = a.get_text(strip=True)
    if txt and len(txt) > 2:
        print(f"  {txt} -> {href}")

# Find faculty tables or text
for tr in soup.find_all('tr'):
    tds = tr.find_all('td')
    if len(tds) >= 2:
        print("  ROW:", [td.get_text(strip=True) for td in tds])
