import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

targets = [
    # NU
    ('NU Central', 'https://www.nu.ac.th/?page_id=2374'),
    ('NU Admission', 'https://admission.nu.ac.th/'),
    ('NU Grad', 'https://www.grad.nu.ac.th/'),
    # SWU
    ('SWU Central', 'https://www.swu.ac.th/curriculum.php'),
    ('SWU Acad', 'https://academic.swu.ac.th/'),
    ('SWU Grad', 'https://grad.swu.ac.th/'),
    # PSU
    ('PSU Central', 'https://www.psu.ac.th/th/academics/programs'),
    ('PSU Acad', 'https://e-curriculum.psu.ac.th/'),
    ('PSU Reg Hat Yai', 'https://regist.psu.ac.th/'),
    ('PSU Grad', 'https://grad.psu.ac.th/'),
    # NIDA
    ('NIDA Central', 'https://nida.ac.th/th/school/'),
    ('NIDA GSAS', 'https://gsas.nida.ac.th/'),
    ('NIDA GSPA', 'https://gspa.nida.ac.th/'),
    ('NIDA NIDA Business School', 'https://mba.nida.ac.th/')
]

for name, url in targets:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{name}] {url} -> Status {r.status_code}, Length: {len(r.content)} bytes")
    except Exception as e:
        print(f"[{name}] {url} -> Error: {e}")
