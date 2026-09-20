# -*- coding: utf-8 -*-
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('cmu_batch1_raw.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

TITLE_REGEX = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.)\s*'
    r'(?:ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.)*\s*'
    r'(?:ดร\.)*\s*'
)

for fac, records in data.items():
    print(f"\n=== {fac} ({len(records)}) ===")
    for r in records:
        clean_name = TITLE_REGEX.sub('', r['full_name_th']).strip()
        parts = clean_name.split()
        th_first = parts[0] if len(parts) > 0 else ''
        th_last = parts[1] if len(parts) > 1 else ''
        email = r['email'] or ''
        print(f"  {r['id']}: [{clean_name}] ({th_first} {th_last}) | email: {email} | {r['profile_url']}")
