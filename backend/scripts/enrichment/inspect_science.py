# -*- coding: utf-8 -*-
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('cmu_science_raw.json', 'r', encoding='utf-8') as f:
    recs = json.load(f)

chem = [r for r in recs if r['department_th'] == 'ภาควิชาเคมี']
bio = [r for r in recs if r['department_th'] == 'ภาควิชาชีววิทยา']

print("=== ภาควิชาเคมี (54) ===")
for i, r in enumerate(chem, 1):
    print(f"{i:2d}. {r['id']} | {r['full_name_th']} | {r['email']}")

print("\n=== ภาควิชาชีววิทยา (26) ===")
for i, r in enumerate(bio, 1):
    print(f"{i:2d}. {r['id']} | {r['full_name_th']} | {r['email']}")
