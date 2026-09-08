# -*- coding: utf-8 -*-
"""Quick API health check before harvesting: OpenAlex, CrossRef, ThaiJO."""
import sys, urllib.request, urllib.parse, ssl, json
sys.path.append('backend')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. OpenAlex polite tier (no key)
try:
    req = urllib.request.Request(
        "https://api.openalex.org/authors?search=Prinya%20Thaewanarumitkul",
        headers={"User-Agent": "ThaiEduCenterAcademicMatcher/2.0 (mailto:golf_chayanon@hotmail.com)"})
    with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
        d = json.loads(r.read().decode())
        print(f"OpenAlex polite: OK ({len(d.get('results', []))} results)")
except Exception as e:
    print(f"OpenAlex polite: FAIL {e}")

# 2. CrossRef
try:
    req = urllib.request.Request(
        "https://api.crossref.org/works?query.author=" + urllib.parse.quote("Wanwisa Udomsinprasert") + "&rows=1",
        headers={"User-Agent": "ThaiEduCenter/2.0 (mailto:golf_chayanon@hotmail.com)"})
    with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
        d = json.loads(r.read().decode())
        print(f"CrossRef: OK ({len(d.get('message', {}).get('items', []))} items)")
except Exception as e:
    print(f"CrossRef: FAIL {e}")

# 3. ThaiJO TU Law
try:
    req = urllib.request.Request(
        "https://so05.tci-thaijo.org/index.php/tulawjournal/search/search?query=" + urllib.parse.quote("ปกป้อง ศรีสนิท"),
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
        print(f"ThaiJO TU Law: OK ({len(r.read())} bytes)")
except Exception as e:
    print(f"ThaiJO TU Law: FAIL {e}")
