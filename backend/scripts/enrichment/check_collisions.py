# -*- coding: utf-8 -*-
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('backend/scripts/enrichment/update_english_names.py', 'r', encoding='utf-8') as f:
    text = f.read()

existing = set(re.findall(r'"([^"]+)":\s*\(', text))

with open('batch1_dict_entries.json', 'r', encoding='utf-8') as f:
    batch1 = json.load(f)

collisions = []
to_add = {}
for k, v in batch1.items():
    clean_k = k.replace('รอ.', '')
    if clean_k in existing:
        collisions.append((clean_k, v))
    else:
        to_add[clean_k] = v

print(f"Existing count: {len(existing)}")
print(f"Collisions: {len(collisions)}: {collisions}")
print(f"To add: {len(to_add)}")

lines = ['    # CMU Batch 1: Dentistry, AMS, Masscomm, Economics']
for k, (fn, ln) in to_add.items():
    lines.append(f'    "{k}": ("{fn}", "{ln}"),')

with open('batch1_to_append.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
