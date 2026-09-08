# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, json

name = "ญาดา เดชชัย"
url = f"https://api.crossref.org/works?query.author={urllib.parse.quote(name)}&rows=5"
req = urllib.request.Request(url, headers={'User-Agent': 'ThaiEduCenter/1.0 (mailto:admin@thaieducenter.ac.th)'})
res = urllib.request.urlopen(req)
d = json.loads(res.read().decode('utf-8'))
for it in d.get('message', {}).get('items', []):
    authors = [f"{a.get('given','')} {a.get('family','')}".strip() for a in it.get('author', [])]
    print('Title:', it.get('title', [''])[0])
    print('  Authors:', authors)
    print('  Journal:', it.get('container-title', [''])[0])
