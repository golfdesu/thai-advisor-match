# -*- coding: utf-8 -*-
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from enrich_cmu_missing_en_batch1 import BATCH1_FACULTIES

TITLE_REGEX = re.compile(
    r'^(?:ศ\.เกียรติคุณ|ศ\.เชี่ยวชาญพิเศษ|ศ\.คลินิก|ศ\.|รศ\.คลินิก|รศ\.|ผศ\.คลินิก|ผศ\.|อ\.)\s*'
    r'(?:ดร\.|พญ\.|นพ\.|ทพ\.|ทพญ\.|สพ\.ญ\.|สพ\.บ\.|รอ\.|พ\.ต\.ท\.|ร\.ต\.อ\.)*\s*'
    r'(?:ดร\.)*\s*'
)

with open('cmu_batch1_raw.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# flatten raw_data by id
raw_by_id = {}
for fac, recs in raw_data.items():
    for r in recs:
        raw_by_id[r['id']] = r

mapping = {}
for f in BATCH1_FACULTIES:
    fid = f['id']
    raw = raw_by_id.get(fid)
    if not raw:
        continue
    clean_name = TITLE_REGEX.sub('', raw['full_name_th']).strip()
    parts = clean_name.split()
    th_first = parts[0]
    mapping[th_first] = (f['first_name'], f['last_name'])

print(f"Generated {len(mapping)} canonical dictionary entries")
with open('batch1_dict_entries.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)
