import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Test NU course portal
print("=== 1. Testing NU Course Portal (acad.nu.ac.th/course/) ===")
try:
    r_nu = requests.get('https://www.acad.nu.ac.th/course/', headers=headers, timeout=12, verify=False)
    print(f"NU Course status: {r_nu.status_code}, len: {len(r_nu.content)}")
    soup_nu = BeautifulSoup(r_nu.content, 'html.parser')
    print(f"NU Course Title: {soup_nu.title.string if soup_nu.title else 'None'}")
    nu_facs = []
    for a in soup_nu.find_all('a', href=True):
        t = a.get_text(strip=True)
        if any(k in t for k in ['คณะ', 'วิทยาลัย', 'สาขาวิชา', 'หลักสูตร']):
            nu_facs.append((t, a['href']))
    print(f"NU Course links: {len(nu_facs)}")
    for t, h in nu_facs[:10]:
        print(f"  {t} -> {h}")
except Exception as e:
    print(f"NU error: {e}")

# 2. Test SWU syllabus-open
print("\n=== 2. Testing SWU Syllabus Open (academic.swu.ac.th/syllabus-open) ===")
try:
    r_swu = requests.get('https://academic.swu.ac.th/syllabus-open', headers=headers, timeout=12, verify=False)
    print(f"SWU Syllabus status: {r_swu.status_code}, len: {len(r_swu.content)}")
    soup_swu = BeautifulSoup(r_swu.content, 'html.parser')
    print(f"SWU Title: {soup_swu.title.string if soup_swu.title else 'None'}")
    swu_links = []
    for a in soup_swu.find_all('a', href=True):
        t = a.get_text(strip=True)
        if any(k in t for k in ['คณะ', 'วิทยาลัย', 'สาขาวิชา', 'หลักสูตร', 'ปริญญา']):
            swu_links.append((t, a['href']))
    print(f"SWU syllabus links: {len(swu_links)}")
    for t, h in swu_links[:10]:
        print(f"  {t} -> {h}")
except Exception as e:
    print(f"SWU error: {e}")
