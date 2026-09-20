# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Fetch main directory to get all detail links
url = 'https://ot.ams.cmu.ac.th/index.php?module=academicstaff'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
links = {}
for a in soup.find_all('a'):
    href = a.get('href', '')
    if 'academicstaff-detail' in href:
        text = a.get_text().strip().replace('\xa0', ' ')
        # extract thai name
        m = re.search(r'([ก-๙]+\s+[ก-๙]+(?:\s+[ก-๙]+)?)', text)
        if m:
            links[m.group(1).strip()] = 'https://ot.ams.cmu.ac.th/' + href

print(f"Found {len(links)} staff detail links in AMS OT")

# Now fetch each link
en_names = {}
for th_name, link in links.items():
    try:
        req = urllib.request.Request(link, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            page = resp.read().decode('utf-8', errors='ignore')
        psoup = BeautifulSoup(page, 'html.parser')
        # Look for English name line: "Prof.", "Assoc. Prof.", "Asst. Prof.", "Lecturer", "Dr."
        found_en = ""
        for tag in psoup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'div', 'span']):
            t = tag.get_text().strip().replace('\xa0', ' ')
            if re.search(r'(?:Prof\.|Assoc\.|Asst\.|Dr\.|Lecturer)\s+[A-Za-z]+', t) and not re.search(r'[ก-๙]', t):
                found_en = t
                break
        if not found_en:
            # Fallback regex search in raw text
            m_en = re.search(r'((?:Prof\.|Assoc\.\s*Prof\.|Asst\.\s*Prof\.|Dr\.)\s+[A-Za-z\s\-\.]+)', page.replace('\xa0', ' '))
            if m_en:
                found_en = m_en.group(1).strip()
        print(f"[{th_name}] -> {found_en} ({link})")
        en_names[th_name] = found_en
    except Exception as e:
        print(f"Error on {th_name}: {e}")

with open('ams_verified.json', 'w', encoding='utf-8') as f:
    json.dump(en_names, f, ensure_ascii=False, indent=2)
