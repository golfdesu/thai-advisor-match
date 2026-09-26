# -*- coding: utf-8 -*-
import urllib.request
import json
import os

SERPAPI_KEY = "daf8c9183556d38c6a5ce3e2fd68f9f484d764ae153d46a4fb2c4e088adc513d"

def search_google(query):
    url = f"https://serpapi.com/search.json?engine=google&q={urllib.parse.quote(query)}&api_key={SERPAPI_KEY}&num=5&hl=th&gl=th"
    req = urllib.request.Request(url, headers={"User-Agent": "ThaiEduCenter/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            print(f"\nQuery: {query}")
            for r in data.get("organic_results", [])[:4]:
                print(f"  Title: {r.get('title')}")
                print(f"  Link : {r.get('link')}")
                print(f"  Snippet: {r.get('snippet')[:100]}...\n")
    except Exception as e:
        print(f"Error for query '{query}': {e}")

search_google("คณะทันตแพทยศาสตร์ มหาวิทยาลัยสงขลานครินทร์ คณาจารย์")
search_google("คณะมนุษยศาสตร์ มหาวิทยาลัยศรีนครินทรวิโรฒ คณาจารย์ บุคลากร")
search_google("คณะพยาบาลศาสตร์ มหาวิทยาลัยศรีนครินทรวิโรฒ คณาจารย์ บุคลากร")
