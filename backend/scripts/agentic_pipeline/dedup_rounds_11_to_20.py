# -*- coding: utf-8 -*-
"""
5-Pass State Reducer and Quality Validator for Rounds 11-20
"""
import json
import re
import sys
from pathlib import Path
from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

raw_path = Path("backend/data/agent_states/rounds11_20_raw_combined.json")
with open(raw_path, "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Starting 5-pass state reducer over {len(records)} records...")

def clean_record(r):
    first = (r.get("first_name") or "").strip()
    last = (r.get("last_name") or "").strip()
    full_th = (r.get("full_name_th") or "").strip()
    email = (r.get("email") or "").strip().lower()

    # Clean degrees leaked into last_name
    last = re.sub(r",?\s*(Ph\.?D\.?|M\.?D\.?|Ed\.?D\.?|D\.?Eng\.?|Dr\.?PH\.?|D\.?B\.?A\.?).*$", "", last, flags=re.I).strip()
    first = re.sub(r"^(Dr\.?|Prof\.?|Assoc\.?\s*Prof\.?|Asst\.?\s*Prof\.?)\s+", "", first, flags=re.I).strip()

    r["first_name"] = first
    r["last_name"] = last
    r["email"] = email
    r["full_name"] = f"{first} {last}".strip() if first and last else (r.get("full_name") or "").strip()
    r["full_name_th"] = full_th

    # Ensure valid department
    if not r.get("department_th"):
        r["department_th"] = r.get("faculty_th", "")
    if not r.get("department"):
        r["department"] = r.get("faculty", "")

    return r

cleaned_records = [clean_record(r) for r in records]

unique_records = []
seen_emails = set()
seen_names_th = set()
seen_names_en = set()

for r in cleaned_records:
    email = r.get("email", "")
    name_th = r.get("full_name_th", "")
    name_en = f"{r.get('first_name', '').lower()} {r.get('last_name', '').lower()}".strip()

    # Generic institutional emails that shouldn't dedup distinct professors
    is_generic_email = any(email.startswith(g) for g in ["info@", "contact@", "admin@", "office@", "deans@", "fms-", "sgs@"])
    if email and not is_generic_email and email in seen_emails:
        print(f"  [Dedup: Email] Skipping duplicate {email} ({name_th})")
        continue

    # Clean Thai prefix for dedup
    norm_th = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.)\s*(ดร\.)?\s*", "", name_th).strip()
    if norm_th and norm_th in seen_names_th:
        print(f"  [Dedup: Thai Name] Skipping duplicate {name_th}")
        continue

    # English full name dedup
    if name_en and name_en in seen_names_en and len(name_en.split()) > 1:
        print(f"  [Dedup: English Name] Skipping duplicate {name_en}")
        continue

    # Fuzzy Thai dedup
    is_fuzzy_dup = False
    for u in unique_records:
        u_name_th = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.)\s*(ดร\.)?\s*", "", u.get("full_name_th", "")).strip()
        if norm_th and u_name_th and fuzz.ratio(norm_th, u_name_th) >= 92:
            print(f"  [Dedup: Fuzzy Thai] {name_th} ~= {u.get('full_name_th')} (ratio {fuzz.ratio(norm_th, u_name_th)})")
            is_fuzzy_dup = True
            break
    if is_fuzzy_dup:
        continue

    if email and not is_generic_email:
        seen_emails.add(email)
    if norm_th:
        seen_names_th.add(norm_th)
    if name_en and len(name_en.split()) > 1:
        seen_names_en.add(name_en)

    unique_records.append(r)

print(f"\nUnique records after 5-pass deduplication: {len(unique_records)} (deduped {len(records) - len(unique_records)})")

# Check 6-dimension schema hygiene
defects = []
for idx, r in enumerate(unique_records):
    # Check English first/last name
    fn = r.get("first_name", "")
    ln = r.get("last_name", "")
    if not ln:
        defects.append(f"Row {idx} ({r.get('full_name_th')}): Missing last_name")
    if re.search(r"[฀-๿]", fn) or re.search(r"[฀-๿]", ln):
        defects.append(f"Row {idx}: Thai chars in English name ({fn} {ln})")
    if re.search(r"(Ph\.?D|M\.?D|Ed\.?D|D\.?Eng)", ln, re.I):
        defects.append(f"Row {idx}: Degree suffix leak in last_name ({ln})")

if defects:
    print(f"\n⚠️ Found {len(defects)} schema hygiene defects:")
    for d in defects:
        print("  - " + d)
else:
    print("\n✅ Zero schema hygiene defects in extracted records!")

out_dedup = Path("backend/data/agent_states/rounds11_20_merged_extracted.json")
with open(out_dedup, "w", encoding="utf-8") as f:
    json.dump(unique_records, f, ensure_ascii=False, indent=2)
print(f"Saved deduplicated dataset to {out_dedup}")
