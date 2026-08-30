import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

r_js = requests.get('https://reg.kmutnb.ac.th/registrar/main.a8f82319f26077ee.js', headers=headers, timeout=15, verify=False)
js_text = r_js.text

# search for urls and endpoints
urls = re.findall(r'https?://[^\s"\'`]+|/[a-zA-Z0-9_\-\./]+program[a-zA-Z0-9_\-\./]*', js_text)
print("Extracted endpoints:")
for u in set(urls):
    if any(k in u for k in ['program', 'curriculum', 'reg', 'kmutnb']):
        print(f"  {u}")

# search for backend base url
base_urls = re.findall(r'baseUrl\s*[:=]\s*["\']([^"\']+)["\']|apiUrl\s*[:=]\s*["\']([^"\']+)["\']|SERVER_URL\s*[:=]\s*["\']([^"\']+)["\']', js_text)
print(f"Base URLs found: {base_urls}")
