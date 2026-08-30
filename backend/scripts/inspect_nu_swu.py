import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# Test undergrad and grad admission urls
urls = [
    ('NU Undergrad', 'https://www.admission.nu.ac.th/undergrad2.php'),
    ('NU Grad Admission', 'https://www.admission.graduate.nu.ac.th/'),
    ('SWU Academic Programs', 'https://academic.swu.ac.th/'),
]

for name, url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"[{name}] {url} -> Status {r.status_code}, Length: {len(r.content)}")
        soup = BeautifulSoup(r.content, 'html.parser')
        # find faculty or curriculum list
        items = []
        for a in soup.find_all('a', href=True):
            t = a.get_text(strip=True)
            if any(k in t for k in ['คณะ', 'สาขาวิชา', 'หลักสูตร', 'วศ.บ.', 'วท.บ.', 'ภ.บ.', 'พ.บ.', 'ศศ.บ.', 'บธ.บ.']):
                items.append(t)
        print(f"  Extracted {len(set(items))} items:")
        for it in list(set(items))[:8]:
            print(f"    - {it}")
    except Exception as e:
        print(f"[{name}] Error: {e}")
