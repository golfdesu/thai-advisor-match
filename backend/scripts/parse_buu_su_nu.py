import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. BUU (Burapha)
print("=== 1. Testing BUU (Burapha) Registrar ===")
r_buu = requests.get('https://reg.buu.ac.th/registrar/program_info.asp', headers=headers, timeout=10, verify=False)
r_buu.encoding = 'tis-620'
soup_buu = BeautifulSoup(r_buu.text, 'html.parser')
links_buu = [a['href'] for a in soup_buu.find_all('a', href=True) if 'program_info_1.asp' in a['href']]
print(f"BUU program links found: {len(links_buu)}")

# 2. SU (Silpakorn)
print("\n=== 2. Testing SU (Silpakorn) Registrar ===")
r_su = requests.get('https://reg.su.ac.th/registrar/program_info.asp', headers=headers, timeout=10, verify=False)
r_su.encoding = 'tis-620'
soup_su = BeautifulSoup(r_su.text, 'html.parser')
links_su = [a['href'] for a in soup_su.find_all('a', href=True) if 'program_info_1.asp' in a['href']]
print(f"SU program links found: {len(links_su)}")

# 3. NU (Naresuan)
print("\n=== 3. Testing NU Central Page ===")
r_nu = requests.get('https://www.nu.ac.th/?page_id=2374', headers=headers, timeout=10, verify=False)
soup_nu = BeautifulSoup(r_nu.text, 'html.parser')
print(f"NU title: {soup_nu.title.string if soup_nu.title else 'None'}")
nu_links = [a for a in soup_nu.find_all('a', href=True) if any(k in a.get_text() for k in ['สาขาวิชา', 'หลักสูตร', 'คณะ', 'บัณฑิต'])]
print(f"NU relevant links: {len(nu_links)}")
for a in nu_links[:10]:
    print(f"  {a.get_text(strip=True)} -> {a['href']}")
