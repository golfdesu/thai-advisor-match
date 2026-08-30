import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Check admission portal
r = requests.get('https://admission.kmutnb.ac.th/', timeout=15, headers=headers, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
print(f"Admission title: {soup.title.string if soup.title else 'None'}")

# find all faculty links or curriculum links
found_links = set()
for a in soup.find_all('a', href=True):
    href = a['href']
    txt = a.get_text(strip=True)
    if any(k in href or k in txt for k in ['curriculum', 'course', 'faculty', 'program', 'คณะ', 'หลักสูตร', 'สาขาวิชา']):
        found_links.add((txt, href))

print(f"Found {len(found_links)} relevant links on admission portal:")
for txt, href in list(found_links)[:25]:
    print(f"  {txt} -> {href}")
