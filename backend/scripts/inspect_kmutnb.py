import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests, re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get('https://reg.kmutnb.ac.th/registrar/program_info.asp', timeout=15, headers=headers, verify=False)
r.encoding = 'tis-620'
soup = BeautifulSoup(r.text, 'html.parser')

print(f"Title: {soup.title.string if soup.title else 'None'}")

# find all links and table rows
rows = soup.find_all('tr')
print(f"Total rows in reg portal: {len(rows)}")

items = []
current_deg = "ปริญญาตรี"
current_fac = "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ"

for tr in rows:
    txt = tr.get_text(separator=' ', strip=True)
    if 'ระดับ' in txt:
        if 'เอก' in txt: current_deg = 'ปริญญาเอก'
        elif 'โท' in txt: current_deg = 'ปริญญาโท'
        elif 'ตรี' in txt: current_deg = 'ปริญญาตรี'
        elif 'ประกาศนียบัตร' in txt: current_deg = 'ประกาศนียบัตร'

    if 'คณะ' in txt and len(txt) < 80:
        current_fac = txt.strip()

    tds = tr.find_all('td')
    if len(tds) >= 2:
        title = tds[1].get_text(strip=True) if len(tds) > 1 else tds[0].get_text(strip=True)
        if len(title) > 3 and not title.isdigit() and 'หลักสูตร' not in title[:6] and 'รหัส' not in title:
            items.append((current_deg, current_fac, title))

print(f"Parsed items: {len(items)}")
for it in items[:15]:
    print(f"  [{it[0]}] {it[1]} -> {it[2]}")
