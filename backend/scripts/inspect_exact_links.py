import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. NU Undergrad
r1 = requests.get('https://www.admission.nu.ac.th/undergrad2.php', headers=headers, timeout=10, verify=False)
soup1 = BeautifulSoup(r1.content, 'html.parser')
for a in soup1.find_all('a', href=True):
    if 'หลักสูตร' in a.get_text() or 'curriculum' in a['href'] or '.pdf' in a['href']:
        print(f"NU Undergrad Link: {a.get_text(strip=True)} -> {a['href']}")

# 2. NU Grad
r2 = requests.get('https://www.admission.graduate.nu.ac.th/', headers=headers, timeout=10, verify=False)
soup2 = BeautifulSoup(r2.content, 'html.parser')
for a in soup2.find_all('a', href=True):
    if 'หลักสูตร' in a.get_text() or 'program' in a['href'] or '.pdf' in a['href']:
        print(f"NU Grad Link: {a.get_text(strip=True)} -> {a['href']}")

# 3. SWU "หลักสูตรที่เปิดสอน"
r3 = requests.get('https://academic.swu.ac.th/', headers=headers, timeout=10, verify=False)
soup3 = BeautifulSoup(r3.content, 'html.parser')
for a in soup3.find_all('a', href=True):
    if 'หลักสูตรที่เปิดสอน' in a.get_text():
        print(f"SWU Program Link: {a.get_text(strip=True)} -> {a['href']}")
