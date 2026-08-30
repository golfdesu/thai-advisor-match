import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

targets = [
    ('NU - Naresuan Univ', 'https://www.acad.nu.ac.th/acad_web/curriculum.php'),
    ('NU - Reg', 'https://reg.nu.ac.th/registrar/program_info.asp'),
    ('SWU - Srinakharinwirot', 'https://academic.swu.ac.th/Default.aspx?tabid=4610'),
    ('SWU - Portal', 'https://admission.swu.ac.th/admissions2/'),
    ('BUU - Burapha Univ', 'https://reg.buu.ac.th/registrar/program_info.asp'),
    ('SU - Silpakorn Univ', 'https://reg.su.ac.th/registrar/program_info.asp'),
    ('SU - Academic', 'https://academic.su.ac.th/'),
    ('PSU - Prince of Songkla', 'https://reg.psu.ac.th/registrar/program_info.asp'),
    ('PSU - Curriculum', 'https://curriculum.psu.ac.th/'),
    ('NIDA - Portal', 'https://nida.ac.th/th/academics/curriculum/')
]

for name, url in targets:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"[{name}] {url} -> Status {r.status_code}, Length: {len(r.content)} bytes")
    except Exception as e:
        print(f"[{name}] {url} -> Error: {e}")
