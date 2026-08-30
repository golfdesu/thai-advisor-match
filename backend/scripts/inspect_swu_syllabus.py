import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://academic.swu.ac.th/syllabus-open', headers=headers, timeout=12, verify=False)
soup = BeautifulSoup(r.content, 'html.parser')

print("SWU syllabus page text sample:")
text = soup.get_text(separator='\n', strip=True)
lines = [l for l in text.split('\n') if len(l) > 3]
print(f"Total non-empty lines: {len(lines)}")
for l in lines[:40]:
    print(f"  {l}")

# check for tables or accordions
accordions = soup.find_all(class_=re.compile(r'accordion|card|panel|collapse|table|tab', re.I))
print(f"\nFound {len(accordions)} structural elements in SWU page")
