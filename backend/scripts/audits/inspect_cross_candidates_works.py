"""Investigate publications and raw affiliations from OpenAlex."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request


def get_works_for_author(query: str):
    url = f"https://api.openalex.org/works?filter=default.search:{urllib.parse.quote(query)}&per-page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "mailto:admin@educenter.org"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=8).read().decode())
        for w in data.get("results", []):
            print(f"Title: {w.get('title')}")
            for a in w.get("authorships", []):
                name = a.get("author", {}).get("display_name", "")
                if any(q in name for q in query.split()):
                    print(f"  Author: {name} | Affil: {a.get('raw_affiliation_strings')}")
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    print("--- Tuantong Jutagate ---")
    get_works_for_author("Tuantong Jutagate")

    print("\n--- Supachai Vorapojpisut ---")
    get_works_for_author("Supachai Vorapojpisut")

    print("\n--- Pragasit Sitthitikul ---")
    get_works_for_author("Pragasit Sitthitikul")

    print("\n--- Orapha Sakulpanich ---")
    get_works_for_author("Orapha Sakulpanich")
