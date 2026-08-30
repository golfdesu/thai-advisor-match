import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

faculties_kmutnb = [
    ('eng', 'คณะวิศวกรรมศาสตร์', 'Faculty of Engineering', 'https://eng.kmutnb.ac.th/'),
    ('fte', 'คณะครุศาสตร์อุตสาหกรรม', 'Faculty of Technical Education', 'https://fte.kmutnb.ac.th/'),
    ('sci', 'คณะวิทยาศาสตร์ประยุกต์', 'Faculty of Applied Science', 'https://sci.kmutnb.ac.th/'),
    ('fba', 'คณะบริหารธุรกิจ', 'Faculty of Business Administration', 'https://fba.kmutnb.ac.th/'),
    ('it', 'คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล', 'Faculty of Information Technology and Digital Innovation', 'https://it.kmutnb.ac.th/'),
    ('fas', 'คณะศิลปศาสตร์ประยุกต์', 'Faculty of Applied Arts', 'https://fas.kmutnb.ac.th/'),
    ('fitm', 'คณะเทคโนโลยีและการจัดการอุตสาหกรรม', 'Faculty of Industrial Technology and Management', 'https://fitm.kmutnb.ac.th/'),
    ('agro', 'คณะอุตสาหกรรมเกษตร', 'Faculty of Agro-Industry', 'https://agro.kmutnb.ac.th/'),
    ('iet', 'คณะวิศวกรรมศาสตร์และเทคโนโลยี', 'Faculty of Engineering and Technology', 'https://iet.kmutnb.ac.th/'),
    ('cit', 'วิทยาลัยเทคโนโลยีอุตสาหกรรม', 'College of Industrial Technology', 'https://cit.kmutnb.ac.th/'),
    ('grad', 'บัณฑิตวิทยาลัย', 'The Graduate School', 'https://grad.kmutnb.ac.th/'),
    ('tggs', 'บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน', 'Sirindhorn International TGGS', 'https://tggs.kmutnb.ac.th/')
]

for code, th, en, url in faculties_kmutnb:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        # find curriculum links
        cur_links = []
        for a in soup.find_all('a', href=True):
            t = a.get_text(strip=True)
            h = a['href']
            if any(k in t or k in h for k in ['หลักสูตร', 'สาขาวิชา', 'curriculum', 'program', 'course']):
                if len(t) > 2 and len(t) < 60:
                    cur_links.append((t, h))
        print(f"[{code}] {th} ({url}) -> Status {r.status_code}, Found {len(cur_links)} curriculum links")
        for t, h in cur_links[:5]:
            print(f"    - {t} -> {h}")
    except Exception as e:
        print(f"[{code}] {th} -> Error: {e}")
