# -*- coding: utf-8 -*-
import urllib.request
import json

url = "https://api.openalex.org/works?filter=institutions.id:I76920116,concepts.id:C159110408&per-page=5"
req = urllib.request.Request(url, headers={"User-Agent": "ThaiEduCenter/1.0 (mailto:admin@thaieducenter.org)"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(f"Total SWU Nursing works in OpenAlex: {data.get('meta', {}).get('count')}")
    for w in data.get('results', [])[:5]:
        print(f"  Title: {w['title']}")
        for auth in w.get('authorships', []):
            if any('Srinakharinwirot' in inst.get('display_name', '') for inst in auth.get('institutions', [])):
                print(f"    Author: {auth['author']['display_name']} ({auth['author']['id']})")
