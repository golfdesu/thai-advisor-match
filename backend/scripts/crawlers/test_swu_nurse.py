# -*- coding: utf-8 -*-
import urllib.request
import json

url = "https://api.openalex.org/authors?filter=last_known_institutions.id:I76920116&per-page=5"
req = urllib.request.Request(url, headers={"User-Agent": "ThaiEduCenter/1.0 (mailto:admin@thaieducenter.org)"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(f"SWU total authors in OpenAlex: {data.get('meta', {}).get('count')}")
    for a in data.get('results', []):
        print(f"  {a['id']} | {a['display_name']} | Affil: {a.get('last_known_institutions', [{}])[0].get('display_name')}")
