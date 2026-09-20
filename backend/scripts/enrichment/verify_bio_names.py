# -*- coding: utf-8 -*-
import urllib.request
import ssl
import re
import urllib.parse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

names = [
    ("นฎา อารยะสกุล", "Nada"),
    ("จุฑารัตน์ ปัญจขันธ์", "Jutarat"),
    ("นิลิตา มุขแจ้ง", "Nilita"),
    ("ภัทรสุดา ฉายาภักดี", "Phattrasuda"),
]

for th_name, en_hint in names:
    query = f'"{th_name}"'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        snippets = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.I | re.DOTALL)
        print(f"\n=== {th_name} ===")
        for s in snippets[:3]:
            clean_s = re.sub(r'<[^>]+>', '', s).strip()
            print("  Snippet:", clean_s[:200])
    except Exception as e:
        print(f"Error: {e}")
