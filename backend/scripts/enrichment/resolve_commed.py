# -*- coding: utf-8 -*-
import json
import urllib.request
import ssl
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 mailto:admin@advisor-match.th'}

COMMED_NAMES = [
    ("วชิรนันท์ ศิริกุล", "Vachiranun", "Sirikul", "vachiranun.s@cmu.ac.th"),
    ("รุ่งนภา มาละเสาร์", "Rungnapa", "Malasao", "rungnapa.m@cmu.ac.th"),
    ("กัมปนาท วังแสน", "Kampanat", "Wangsan", "kampanat.w@cmu.ac.th"),
    ("อมรพัฐ กิจโร", "Amornphat", "Kitro", "amornphat.kit@cmu.ac.th"),
    ("ณัฐณภพ อิศรเดช", "Natnapob", "Israsena Na Ayudhya", "natnapob.i@cmu.ac.th"),
    ("วุฒิภัทร กีรติไพศาล", "Wuttipat", "Keeratipaisarl", "wuttipat.k@cmu.ac.th"),
    ("เกรียงไกร ศรีธนวิบุญชัย", "Kriengkrai", "Srithanaviboonchai", "kriengkrai.s@cmu.ac.th"),
    ("จินต์จุฑา ภานุมาสวิวัฒน์", "Jinjuta", "Panumasvivat", "jinjuta.p@cmu.ac.th"),
    ("มธุรมาศ สีเสน", "Mathuramat", "Seesen", "mathuramat.s@cmu.ac.th"),
]

for th, fn, ln, em in COMMED_NAMES:
    # Query Crossref for works
    q = f"{fn} {ln}"
    url = f"https://api.crossref.org/works?query.author={urllib.parse.quote(q)}&rows=1"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        tot = data.get('message', {}).get('total-results', 0)
        print(f"  {th} -> {fn} {ln} ({em}) | Crossref results: {tot}")
    except Exception as e:
        print(f"  {th} -> {fn} {ln} ({em}) | Error: {e}")
