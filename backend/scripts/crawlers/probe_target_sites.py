# -*- coding: utf-8 -*-
import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.human.cmu.ac.th/', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx) as r:
    content = r.read().decode('utf-8', errors='ignore')
    chunks = re.findall(r'src=["\'](/_next/static/chunks/[^"\']+)["\']', content)
    print("Chunks found:", len(chunks))
    for c in chunks:
        chunk_url = "https://www.human.cmu.ac.th" + c
        try:
            req_c = urllib.request.Request(chunk_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_c, context=ctx, timeout=5) as resp:
                js = resp.read().decode('utf-8', errors='ignore')
                routes = set(re.findall(r'["\'](/(?:th|en)?/[a-zA-Z0-9_\-/]+)["\']', js))
                matching_routes = [r for r in routes if any(k in r.lower() for k in ['person', 'staff', 'faculty', 'dept', 'department', 'about'])]
                if matching_routes:
                    print(f"In {c}:")
                    for mr in matching_routes:
                        print("  ", mr)
        except Exception as e:
            pass
