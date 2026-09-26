# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import json

def lookup_author(name, institution_id):
    encoded_name = urllib.parse.quote(name)
    url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:{institution_id}&search={encoded_name}&per-page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "ThaiEduCenter/1.0 (mailto:admin@thaieducenter.org)"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            results = data.get('results', [])
            if results:
                best = results[0]
                return {
                    "id": best['id'],
                    "name": best['display_name'],
                    "works": best.get('works_count', 0),
                    "citations": best.get('cited_by_count', 0),
                    "h_index": best.get('summary_stats', {}).get('h_index', 0)
                }
    except Exception as e:
        pass
    return None

# Test a few PSU Dent authors
psu_tests = ["Nattapon Rotpenpian", "Suwanna Jitpukdeebodintr", "Srisurang Suttapreyasri", "Prisana Pripatnanont", "Chidchanok Leethanakul", "Udom Thongudomporn"]
print("=== PSU Dent OpenAlex Tests ===")
for name in psu_tests:
    res = lookup_author(name, "I131868736")
    print(f"{name} -> {res}")

# Test a few SWU Humanities authors
swu_tests = ["Nuntana Wongthai", "Sakulrat Worathumrong", "Anchalee Jansem", "Sugunya Ruangjaroon", "Puwakorn Chatbamrungsuk"]
print("\n=== SWU Humanities OpenAlex Tests ===")
for name in swu_tests:
    res = lookup_author(name, "I76920116")
    print(f"{name} -> {res}")
