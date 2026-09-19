"""Investigate affiliations of cross-university candidates in OpenAlex and Google."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

candidates = [
    ("Woon Oh Jung", "cu_cbs_wave11_0035"),
    ("Thomas Kirchmaier", "cu_cbs_wave11_0032"),
    ("Orapha Sakulpanich", "thammasatu_facultyofp_sakulpanich_026"),
    ("Narong Sarisuta", "thammasatu_facultyofp_sarisut_027"),
    ("Cha-oncin Suksriwong", "thammasatu_facultyofp_suksriwong_002"),
    ("Pragasit Sitthitikul", "thaksinuni_facultyofm_sitthitikul_008"),
    ("Sirikan Chucherd", "thammasatu_sirindhorn_chucherd_011"),
    ("Uthai Suwankoot", "thammasatu_facultyofp_suwankoot_003"),
    ("Tuantong Jutagate", "ubonratcha_facultyofa_jutagate_001"),
    ("Supachai Vorapojpisut", "thammasatu_facultyofe_vorapojpisut_001")
]

for name, fid in candidates:
    url = f"https://api.openalex.org/authors?search={urllib.parse.quote(name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "mailto:admin@educenter.org"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=8).read().decode())
        results = data.get("results", [])
        if results:
            a = results[0]
            insts = [i.get("display_name") for i in a.get("last_known_institutions", [])]
            print(f"[{fid}] {name} -> OpenAlex: {a.get('display_name')} | Institutions: {insts}")
        else:
            print(f"[{fid}] {name} -> OpenAlex: NOT FOUND")
    except Exception as e:
        print(f"[{fid}] {name} -> Error: {e}")
