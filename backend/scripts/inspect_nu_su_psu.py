import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. NU page_id=1929
print("=== 1. NU Curriculum Page (page_id=1929) ===")
r_nu_cur = requests.get('https://www.nu.ac.th/?page_id=1929', headers=headers, timeout=10, verify=False)
soup_nu_cur = BeautifulSoup(r_nu_cur.text, 'html.parser')
nu_courses = []
for el in soup_nu_cur.find_all(['li', 'p', 'a', 'h3', 'h4']):
    t = el.get_text(strip=True)
    if any(k in t for k in ['สาขาวิชา', 'หลักสูตร', 'วศ.บ.', 'วท.บ.', 'ภ.บ.', 'พ.บ.', 'น.บ.', 'ศศ.บ.', 'บธ.บ.']):
        if len(t) > 5 and len(t) < 100:
            nu_courses.append(t)
print(f"NU items extracted: {len(set(nu_courses))}")
for c in list(set(nu_courses))[:10]:
    print(f"  NU: {c}")

# 2. SU inspect table rows
print("\n=== 2. SU Inspect Table Rows ===")
r_su = requests.get('https://reg.su.ac.th/registrar/program_info.asp', headers=headers, timeout=10, verify=False)
r_su.encoding = 'tis-620'
soup_su = BeautifulSoup(r_su.text, 'html.parser')
su_items = []
for tr in soup_su.find_all('tr'):
    tds = tr.find_all('td')
    if len(tds) >= 2:
        title = tds[1].get_text(strip=True) if len(tds) > 1 else tds[0].get_text(strip=True)
        if len(title) > 3 and not title.isdigit() and 'หลักสูตร' not in title[:6]:
            su_items.append(title)
print(f"SU items extracted: {len(set(su_items))}")
for c in list(set(su_items))[:10]:
    print(f"  SU: {c}")

# 3. PSU Grad Portal
print("\n=== 3. PSU Grad Portal ===")
r_psu = requests.get('https://grad.psu.ac.th/', headers=headers, timeout=10, verify=False)
soup_psu = BeautifulSoup(r_psu.text, 'html.parser')
psu_links = [a['href'] for a in soup_psu.find_all('a', href=True) if 'curriculum' in a['href'] or 'program' in a['href'] or 'course' in a['href']]
print(f"PSU Grad links: {len(psu_links)}")
for l in psu_links[:5]:
    print(f"  PSU link: {l}")
