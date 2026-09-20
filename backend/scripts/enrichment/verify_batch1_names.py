# -*- coding: utf-8 -*-
"""
Helper script to fetch official English directory names for Batch 1 CMU faculties:
1. Economics (https://www.econ.cmu.ac.th/en/faculty-members)
2. Mass Communication (https://www.masscomm.cmu.ac.th)
3. Dentistry (https://www.dent.cmu.ac.th)
4. AMS (https://ams.cmu.ac.th)
"""
import sys
import json
import urllib.request
from bs4 import BeautifulSoup
import ssl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_econ():
    url = "https://www.econ.cmu.ac.th/en/faculty-members"
    print(f"Fetching {url}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        print(f"Econ EN fetched: {len(text)} chars")
        # Find faculty cards or text blocks
        cards = soup.find_all(['div', 'li', 'article'], class_=lambda c: c and any(x in c.lower() for x in ['faculty', 'member', 'card', 'team', 'person', 'staff']))
        print(f"Found {len(cards)} candidate cards in Econ")
        return html
    except Exception as e:
        print(f"Econ fetch error: {e}")
        return ""

def fetch_dent():
    url = "https://www.dent.cmu.ac.th/web/staff"
    print(f"Fetching {url}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        print(f"Dent fetched: {len(html)} chars")
        return html
    except Exception as e:
        print(f"Dent fetch error: {e}")
        return ""

if __name__ == "__main__":
    fetch_econ()
    fetch_dent()
