# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import ssl
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) mailto:admin@advisor-match.th'
}

with open('cmu_batch1_raw.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Query Crossref by email user part or query
masscomm_records = data['คณะการสื่อสารมวลชน']

print(f"Checking {len(masscomm_records)} Masscomm records...")
for r in masscomm_records:
    email = r['email']
    user = email.split('@')[0] if email else ''
    # clean Thai name
    th_name = re.sub(r'^(?:ผศ\.ดร\.|รศ\.ดร\.|อ\.ดร\.|ผศ\.|รศ\.|อ\.)\s*', '', r['full_name_th']).strip()

    # Query Crossref using author name if English or query
    # E.g., user is "supparerk.pothi" -> first="Supparerk", last="Pothipairatana"
    parts = user.split('.')
    fn = parts[0].capitalize() if parts else ''
    ln_prefix = parts[1] if len(parts) > 1 else ''

    url = f"https://api.crossref.org/works?query.author={fn}&rows=3"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            cdata = json.loads(resp.read().decode('utf-8'))
        items = cdata.get('message', {}).get('items', [])
        found_author = ""
        for it in items:
            for auth in it.get('author', []):
                given = auth.get('given', '')
                family = auth.get('family', '')
                if fn.lower() in given.lower() or (ln_prefix and ln_prefix.lower() in family.lower()):
                    found_author = f"{given} {family}"
                    break
            if found_author:
                break
        print(f"[{r['id']}] {th_name} | {email} -> {fn} ... (Found on Crossref: {found_author})")
    except Exception as e:
        print(f"[{r['id']}] {th_name} | {email} -> Error: {e}")
