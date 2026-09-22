# -*- coding: utf-8 -*-
import urllib.request
import json

for oa_id in ['A5093269494', 'A5151438778']:
    url = f'https://api.openalex.org/authors/{oa_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:advisor-match@thai-educenter.ac.th'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"OA {oa_id}: display_name = '{data.get('display_name')}', works_count = {data.get('works_count')}")
    except Exception as e:
        print(f"OA {oa_id} error: {e}")
