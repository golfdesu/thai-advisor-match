import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, json
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://reg.kmutnb.ac.th/registrar/programinfo'
}

endpoints = [
    'https://reg.kmutnb.ac.th/registrar/api/program_info',
    'https://reg.kmutnb.ac.th/registrar/api/programinfo',
    'https://reg.kmutnb.ac.th/registrar/api/v1/programinfo',
    'https://reg.kmutnb.ac.th/registrar/api/curriculum',
    'https://reg.kmutnb.ac.th/registrar/api/faculty',
    'https://reg.kmutnb.ac.th/registrar/service/programinfo',
]

for ep in endpoints:
    try:
        r = requests.get(ep, headers=headers, timeout=5, verify=False)
        print(f"{ep} -> {r.status_code}, type: {r.headers.get('Content-Type')}, len: {len(r.content)}")
        if r.status_code == 200 and 'json' in r.headers.get('Content-Type', ''):
            print(f"  Sample: {r.text[:200]}")
    except Exception as e:
        print(f"{ep} -> {e}")
