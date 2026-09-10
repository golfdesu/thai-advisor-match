"""Discover staff-directory seed URLs for sparse famous faculties via SERPAPI."""
import os
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

SERPAPI_KEYS = [k.strip() for k in os.getenv("SERPAPI_KEYS", "").split(",") if k.strip()]

TARGETS = [
    # Chulalongkorn
    {"univ_th": "จุฬาลงกรณ์มหาวิทยาลัย", "univ_en": "Chulalongkorn University", "faculty_th": "คณะวารสารศาสตร์และสื่อสารมวลชน", "faculty_en": "Faculty of Communication Arts", "key": "cu_commarts"},
    {"univ_th": "จุฬาลงกรณ์มหาวิทยาลัย", "univ_en": "Chulalongkorn University", "faculty_th": "คณะศิลปกรรมศาสตร์", "faculty_en": "Faculty of Fine and Applied Arts", "key": "cu_finearts"},
    {"univ_th": "จุฬาลงกรณ์มหาวิทยาลัย", "univ_en": "Chulalongkorn University", "faculty_th": "คณะสัตวแพทยศาสตร์", "faculty_en": "Faculty of Veterinary Science", "key": "cu_vet"},
    # Mahidol
    {"univ_th": "มหาวิทยาลัยมหิดล", "univ_en": "Mahidol University", "faculty_th": "คณะกายภาพบำบัด", "faculty_en": "Faculty of Physical Therapy", "key": "mu_pt"},
    {"univ_th": "มหาวิทยาลัยมหิดล", "univ_en": "Mahidol University", "faculty_th": "คณะสัตวแพทยศาสตร์", "faculty_en": "Faculty of Veterinary Science", "key": "mu_vet"},
    {"univ_th": "มหาวิทยาลัยมหิดล", "univ_en": "Mahidol University", "faculty_th": "วิทยาลัยดุริยางคศิลป์", "faculty_en": "College of Music", "key": "mu_music"},
    # Chiang Mai
    {"univ_th": "มหาวิทยาลัยเชียงใหม่", "univ_en": "Chiang Mai University", "faculty_th": "คณะสัตวแพทยศาสตร์", "faculty_en": "Faculty of Veterinary Medicine", "key": "cmu_vet"},
    {"univ_th": "มหาวิทยาลัยเชียงใหม่", "univ_en": "Chiang Mai University", "faculty_th": "คณะเภสัชศาสตร์", "faculty_en": "Faculty of Pharmacy", "key": "cmu_pharmacy"},
    {"univ_th": "มหาวิทยาลัยเชียงใหม่", "univ_en": "Chiang Mai University", "faculty_th": "คณะทันตแพทยศาสตร์", "faculty_en": "Faculty of Dentistry", "key": "cmu_dentistry"},
    # Thammasat
    {"univ_th": "มหาวิทยาลัยธรรมศาสตร์", "univ_en": "Thammasat University", "faculty_th": "คณะเภสัชศาสตร์", "faculty_en": "Faculty of Pharmacy", "key": "tu_pharmacy"},
    {"univ_th": "มหาวิทยาลัยธรรมศาสตร์", "univ_en": "Thammasat University", "faculty_th": "คณะศิลปศาสตร์", "faculty_en": "Faculty of Liberal Arts", "key": "tu_liberalarts"},
]

QUERY_TEMPLATES = [
    '{f} {u} ทำเนียบอาจารย์',
    '{f} {u} อาจารย์ประจำ รายชื่อ',
    '{f} {u} staff directory lecturer',
]


def serpapi_search(query: str, key_idx: int = 0) -> list:
    if not SERPAPI_KEYS:
        return []
    key = SERPAPI_KEYS[key_idx % len(SERPAPI_KEYS)]
    try:
        resp = requests.get(
            "https://serpapi.com/search.json",
            params={"q": query, "api_key": key, "num": 10},
            timeout=15,
        )
        data = resp.json()
        return [
            {"link": r.get("link", ""), "title": r.get("title", "")}
            for r in data.get("organic_results", [])
            if r.get("link")
        ]
    except Exception as e:
        print(f"  SERP error: {e}")
        return []


def main():
    out_path = os.path.join(BACKEND_DIR, "data", "agent_states", "seed_discovery_results.json")
    results = {}
    if os.path.exists(out_path):
        results = json.load(open(out_path, encoding="utf-8"))

    for i, t in enumerate(TARGETS):
        key = t["key"]
        if key in results and results[key].get("candidates"):
            print(f"[{i+1}/{len(TARGETS)}] {key}: cached ({len(results[key]['candidates'])})")
            continue
        print(f"[{i+1}/{len(TARGETS)}] {t['faculty_th']} ...")
        cands = []
        for qi, q in enumerate(QUERY_TEMPLATES):
            hits = serpapi_search(q.format(f=t["faculty_th"], u=t["univ_th"]), key_idx=(i + qi))
            for h in hits:
                if h["link"] not in [c["link"] for c in cands]:
                    cands.append(h)
            time.sleep(0.5)
        results[key] = {
            "univ_th": t["univ_th"], "univ_en": t["univ_en"],
            "faculty_th": t["faculty_th"], "faculty_en": t["faculty_en"],
            "candidates": cands,
        }
        json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  -> {len(cands)} candidates")
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
