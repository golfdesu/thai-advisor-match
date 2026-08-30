import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Fetch engineering courses
r_eng = requests.get('https://www.eng.kmutnb.ac.th/tcas/', headers=headers, timeout=10, verify=False)
soup_eng = BeautifulSoup(r_eng.text, 'html.parser')
print(f"Eng TCAS Title: {soup_eng.title.string if soup_eng.title else 'None'}")
for a in soup_eng.find_all(['a', 'h3', 'h4', 'h5', 'p', 'li']):
    t = a.get_text(strip=True)
    if any(k in t for k in ['วิศวกรรม', 'สาขาวิชา', 'หลักสูตร', 'วศ.บ.', 'วศ.ม.', 'ปร.ด.']):
        if len(t) > 5 and len(t) < 100:
            print(f"  ENG: {t}")

# 2. Fetch TGGS
r_tggs = requests.get('https://tggs.kmutnb.ac.th/master-programs', headers=headers, timeout=10, verify=False)
soup_tggs = BeautifulSoup(r_tggs.text, 'html.parser')
for h in soup_tggs.find_all(['h2', 'h3', 'h4', 'a']):
    t = h.get_text(strip=True)
    if any(k in t for k in ['Engineering', 'Program', 'Master', 'Doctoral', 'M.Eng', 'D.Eng']):
        if len(t) > 6 and len(t) < 100:
            print(f"  TGGS: {t}")
