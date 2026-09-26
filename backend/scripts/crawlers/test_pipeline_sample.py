# -*- coding: utf-8 -*-
import os
import sys
import json
import urllib.request
import urllib.parse
from google import genai

# Load .env for keys
gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
keys = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
if not keys:
    # try reading backend/.env
    if os.path.exists("backend/.env"):
        with open("backend/.env", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEYS="):
                    v = line.strip().split("=", 1)[1].strip("'\"")
                    keys = [k.strip() for k in v.split(",") if k.strip()]
print(f"Loaded {len(keys)} Gemini keys.")

client = genai.Client(api_key=keys[0])

def romanize_names_batch(names):
    prompt = f"""Transliterate each Thai scholar name into English according to RTGS (Royal Thai General System of Transcription).
Output JSON list of objects with:
- "thai": original Thai name
- "first_name": Latin ASCII given name
- "last_name": Latin ASCII surname
STRICT INVARIANT: Output must contain ONLY pure Latin ASCII letters [a-zA-Z -]. Zero Thai characters.

Names to transliterate:
{json.dumps(names, ensure_ascii=False, indent=2)}
"""
    resp = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=genai.types.GenerateContentConfig(response_mime_type="application/json")
    )
    return json.loads(resp.text)

def lookup_openalex(first_name, last_name, inst_id):
    query = f"{first_name} {last_name}"
    q = urllib.parse.quote(query)
    url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:{inst_id}&search={q}&per-page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "ThaiEduCenter/1.0 (mailto:admin@thaieducenter.org)"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            results = data.get('results', [])
            for res in results:
                # check surname match
                disp = res.get('display_name', '')
                if last_name.lower() in disp.lower():
                    return res
    except Exception as e:
        pass
    return None

test_psu = [
    "ชิดชนก ลีธนะกุล",
    "อุดม ทองอุดมพร",
    "สมจินต์ รัตนเสถียร",
    "สายใจ ตัณฑนุช",
    "ศรีสุรางค์ สุทธปรียาศรี"
]

print("Romanizing PSU...")
rom_psu = romanize_names_batch(test_psu)
print(json.dumps(rom_psu, ensure_ascii=False, indent=2))

for item in rom_psu:
    f_en = item['first_name']
    l_en = item['last_name']
    oa = lookup_openalex(f_en, l_en, "I131868736")
    if oa:
        print(f"MATCH: {item['thai']} -> {oa['display_name']} ({oa['id']}) | Works: {oa.get('works_count')} | Citations: {oa.get('cited_by_count')}")
    else:
        print(f"NOT INDEXED: {item['thai']} -> {f_en} {l_en}")
