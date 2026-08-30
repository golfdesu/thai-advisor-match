import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://reg.kmutnb.ac.th/registrar/programinfo', headers=headers, timeout=10, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')

scripts = [s['src'] for s in soup.find_all('script', src=True)]
print(f"Found {len(scripts)} scripts:")
for s in scripts:
    print(f"  {s}")

# inspect main or runtime bundle for api urls
for s in scripts:
    if 'main' in s or 'app' in s or 'chunk' in s:
        full_url = f"https://reg.kmutnb.ac.th/registrar/{s.lstrip('/')}"
        print(f"Fetching JS bundle: {full_url}")
        r_js = requests.get(full_url, headers=headers, timeout=15, verify=False)
        # find api paths
        apis = re.findall(r'["\'](/[^"\']*(?:api|service|program|curriculum)[^"\']*)["\']', r_js.text, re.IGNORECASE)
        print(f"Found {len(apis)} API routes in {s}:")
        for a in set(apis)[:15]:
            print(f"    {a}")
