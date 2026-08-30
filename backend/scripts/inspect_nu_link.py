import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://www.nu.ac.th/?page_id=1929', headers=headers, timeout=10, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')

for a in soup.find_all('a', href=True):
    if 'รายชื่อหลักสูตรทั้งหมด' in a.get_text() or 'nu.ac.th' in a['href'] or '.pdf' in a['href'] or 'google.com' in a['href']:
        print(f"NU Link: {a.get_text(strip=True)} -> {a['href']}")
