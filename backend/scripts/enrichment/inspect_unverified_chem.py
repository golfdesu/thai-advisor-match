# -*- coding: utf-8 -*-
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('chem_enriched_details.json', 'r', encoding='utf-8') as f:
    details = json.load(f)

with open('chem_verified.json', 'r', encoding='utf-8') as f:
    verified = json.load(f)

ver_dict = {v['th_name']: v for v in verified}

unverified = [d for d in details if not ver_dict.get(d['clean_th'], {}).get('found')]

print(f"Unverified Chemistry faculty: {len(unverified)}")
for u in unverified:
    print(f"\n{u['clean_th']} (id={u['id']}):")
    print(f"  Edu: {u['edu_text']}")
    print(f"  Res: {u['res_text']}")
