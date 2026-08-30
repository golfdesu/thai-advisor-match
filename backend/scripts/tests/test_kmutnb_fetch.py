import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. KMUTNB central admission / curriculum
urls = [
    'https://reg.kmutnb.ac.th/registrar/program_info.asp',
    'https://admission.kmutnb.ac.th/',
    'https://www.kmutnb.ac.th/curriculum'
]

for u in urls:
    try:
        r = requests.get(u, timeout=10, headers=headers, verify=False)
        print(f"{u} -> status: {r.status_code}, len: {len(r.content)}")
    except Exception as e:
        print(f"{u} -> error: {e}")
