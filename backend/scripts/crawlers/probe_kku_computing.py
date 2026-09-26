# -*- coding: utf-8 -*-
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

base = 'https://api.computing.kku.ac.th/api/v1'
url = f"{base}/user/list?page=1&size=100"

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    items = json.loads(r.read())['data']['items']

for it in items:
    if 'nattjar@kku.ac.th' in it.get('email', ''):
        print(json.dumps(it, ensure_ascii=False, indent=2))
