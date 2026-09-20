# -*- coding: utf-8 -*-
import json
import re
import urllib.request
import ssl
from bs4 import BeautifulSoup
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

with open('cmu_med_raw.json', 'r', encoding='utf-8') as f:
    raw_med = json.load(f)

TITLE_REGEX = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.)\s*'
    r'(?:ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.)*\s*'
    r'(?:ดร\.)*\s*'
)

def clean_th(name):
    return TITLE_REGEX.sub('', name).strip()

# 1. Pediatrics (6)
peds = [r for r in raw_med if r['department_th'] == 'ภาควิชากุมารเวชศาสตร์']
print(f"Pediatrics records in DB: {len(peds)}")

PEDS_MAPPING = {
    "cmu_5f786e04_8467": ("Prapai", "Dejkhamron", "prapai.dej@cmu.ac.th"),
    "cmu_1f715dc1_8993": ("Kanokkarn", "Sunkonkit", "kanokkarn.sun@cmu.ac.th"),
    "cmu_5df7b6b7_2221": ("Lalita", "Sathitsamitphong", "lalita.sat@cmu.ac.th"),
    "cmu_47be69f5_1076": ("Nattawan", "Arkarattanakul", "nattawan.ark@cmu.ac.th"),
    "cmu_3c7c4cd0_9284": ("Supapitch", "Chanthong", "supapitch.cha@cmu.ac.th"),
    "cmu_1b60ed35_5175": ("Lanlana", "Nimmankiatkul", "lanlana.nim@cmu.ac.th"),
}

for p in peds:
    pid = p['id']
    if pid in PEDS_MAPPING:
        fn, ln, em = PEDS_MAPPING[pid]
        print(f"  [OK] {p['full_name_th']} -> {fn} {ln} ({em})")
    else:
        print(f"  [MISSING] {p['full_name_th']} ({pid})")

# 2. Pharmacology (1)
pharm = [r for r in raw_med if r['department_th'] == 'ภาควิชาเภสัชวิทยา']
print(f"\nPharmacology records in DB: {len(pharm)}")
PHARM_MAPPING = {
    "khonkaenun_facultyofm_fac_012_012": ("Nat", "Koonrungsesomboon", "nat.koonrung@cmu.ac.th")
}
for p in pharm:
    pid = p['id']
    fn, ln, em = PHARM_MAPPING[pid]
    print(f"  [OK] {p['full_name_th']} -> {fn} {ln} ({em})")
