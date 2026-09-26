# -*- coding: utf-8 -*-
import urllib.request, ssl, urllib.parse, re, json
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

test_urls = [
    'https://www.camt.cmu.ac.th/personals/ผศ-ดร-กฤติยา-ศักดิ์ศรีสถ/',
    'https://www.camt.cmu.ac.th/personals/ผศ-ดร-จิรพัฒน์-วาณิชวัฒน/',
    'https://www.camt.cmu.ac.th/personals/รศ-ดร-ภาสิทธิ์-เจริญขวัญ/',
    'https://www.camt.cmu.ac.th/personals/อ-ดร-กลวัชร-คล้ายนาค/',
    'https://www.camt.cmu.ac.th/personals/ผศ-ดร-ปิติพงษ์-ยอดมงคล/',
    'https://www.camt.cmu.ac.th/personals/ผศ-ดร-ภราดร-สุรีย์พงษ์/',
    'https://www.camt.cmu.ac.th/personals/ผศ-ดร-วรวิชญ์-จันทร์ฉาย/',
    'https://www.camt.cmu.ac.th/personals/รศ-ดร-รัฐพล-วุฒิการณ์/',
    'https://www.camt.cmu.ac.th/personals/อ-ดร-กฤตวยาน์-ทองคู่/',
    'https://www.camt.cmu.ac.th/personals/ผศ-ดร-เฉลิมพล-คงจิตต์/'
]

def parse_profile(raw_url):
    parsed = urllib.parse.urlsplit(raw_url)
    encoded = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, urllib.parse.quote(parsed.path), parsed.query, parsed.fragment))
    req = urllib.request.Request(encoded, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
        soup = BeautifulSoup(r.read(), 'html.parser')

    # Thai Name from title or heading
    title = soup.title.get_text() if soup.title else ""
    raw_th = title.split('|')[0].strip()

    # Emails
    emails = [e.lower() for e in re.findall(r'[a-zA-Z0-9._%+-]+@cmu\.ac\.th', str(soup))]
    email = emails[0] if emails else None

    # Widgets
    widgets = [w.get_text(strip=True) for w in soup.find_all('div', class_='elementor-widget-container') if w.get_text(strip=True)]

    # English name from widgets or stripped strings
    en_name = None
    for w in widgets:
        # Check if line contains English name
        if re.search(r'^[A-Za-z\s,\.-]+$', w) and not re.search(r'[ก-๙]', w):
            if any(k in w for k in ['Asst', 'Assoc', 'Prof', 'Dr', 'Ph.D.', 'Lecturer', 'Aj.']) or len(w.split()) >= 2:
                if not any(x in w.lower() for x in ['cmu', 'camt', 'skip', 'menu', 'facebook', 'talented', 'program', 'arrow', 'right']):
                    en_name = w
                    break

    # Department
    dept = ""
    lines = [s.strip() for s in soup.stripped_strings if s.strip()]
    for idx, l in enumerate(lines):
        if l in ['สังกัด:', 'สังกัด'] and idx + 1 < len(lines):
            dept = lines[idx+1]
            break

    # Image
    img = None
    for im in soup.find_all('img'):
        src = im.get('src', '')
        if any(src.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']) and 'wp-content/uploads' in src:
            if not any(x in src.lower() for x in ['logo', 'icon', 'arrow', 'banner', 'bg', 'menu']):
                img = src
                break

    return {
        'name_th': raw_th,
        'name_en': en_name,
        'email': email,
        'dept': dept,
        'img': img
    }

for u in test_urls:
    res = parse_profile(u)
    print(res['name_th'], '->', res['name_en'], '|', res['email'], '|', res['dept'])
