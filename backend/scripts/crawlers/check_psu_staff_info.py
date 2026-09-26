# -*- coding: utf-8 -*-
import urllib.request
import ssl
from bs4 import BeautifulSoup
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

URLS = [
    ("สาขาวิชาทันตกรรมอนุรักษ์ (ทันตกรรมหัตถการ)", "https://www.dent.psu.ac.th/unit/conser/index.php/operative_dentistry/"),
    ("สาขาวิชาทันตกรรมอนุรักษ์ (วิทยาเอ็นโดดอนต์)", "https://www.dent.psu.ac.th/unit/conser/index.php/endodontics/"),
    ("สาขาวิชาทันตกรรมอนุรักษ์ (ปริทันตวิทยา)", "https://www.dent.psu.ac.th/unit/conser/index.php/periodontology/"),
    ("สาขาวิชาชีววิทยาช่องปาก", "https://www.dent.psu.ac.th/unit/oral/index.php/staff/"),
    ("สาขาวิชาทันตกรรมป้องกัน", "https://www.dent.psu.ac.th/unit/prevent/index.php/staff/"),
    ("สาขาวิชาทันตกรรมประดิษฐ์", "https://www.dent.psu.ac.th/unit/prost/staff/"),
    ("สาขาวิชาโอษฐวิทยา", "https://www.dent.psu.ac.th/unit/stoma/index.php/staff/"),
    ("สาขาวิชาศัลยศาสตร์ช่องปากและแม็กซิลโลเฟเชียล", "https://www.dent.psu.ac.th/unit/surgery/index.php/staff/")
]

TITLE_START = re.compile(r'^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|ทพ\.|ทพญ\.|นพ\.|พญ\.)')

for dept, url in URLS:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
        soup = BeautifulSoup(resp.read(), 'html.parser')
        lines = [l.strip() for l in soup.get_text(separator='\n').split('\n') if l.strip()]
        matches = []
        for i, l in enumerate(lines):
            if TITLE_START.match(l) and not any(b in l for b in ["หลังปริญญา", "ปริญญาตรี", "ทันตแพทย์"]):
                # Look at next lines for surname, english, email
                matches.append((l, lines[i+1] if i+1 < len(lines) else ""))
        print(f"=== {dept} ({len(matches)} title matches) ===")
        for m in matches[:5]:
            print("  ", m[0], "| next:", m[1])
