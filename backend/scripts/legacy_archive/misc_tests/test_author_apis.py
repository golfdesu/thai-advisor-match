# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {"User-Agent": "ThaiEduCenter/1.0 (mailto:academic-research@thaieducenter.ac.th)"}

def test_apis():
    test_scholars = [
        ("Nopadol Rompho", "นภดล ร่มโพธิ์", "tu_bus"),
        ("Surasak Likasitwatanakul", "สุรศักดิ์ ลิขสิทธิ์วัฒนกุล", "tu_law"),
        ("Prinya Thaewanarumitkul", "ปริญญา เทวานฤมิตรกุล", "tu_law"),
        ("Pokpong Srisanit", "ปกป้อง ศรีสนิท", "tu_law"),
        ("Veeraya Kamruengrit", "วีรยา คำเรืองฤทธิ์", "cmu_edu"),
        ("Nopporn Ruangvanich", "นพพร เรืองวานิช", "tu_bus"),
        ("Kongsajja Suwanphet", "คงสัจจา สุวรรณเพ็ชร", "tu_law"),
        ("Thapanan Niphitkun", "ฐาปนันท์ นิพิฏฐกุล", "tu_law")
    ]

    for en_name, th_name, tag in test_scholars:
        print(f"\n==========================================")
        print(f"Scholar: {th_name} ({en_name})")

        # 1. OpenAlex works with raw_author_name.search
        enc_en = urllib.parse.quote(en_name)
        oa_url = f"https://api.openalex.org/works?filter=raw_author_name.search:{enc_en}&per_page=3"
        req = urllib.request.Request(oa_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=4, context=ctx) as res:
                data = json.loads(res.read().decode())
                results = data.get("results", [])
                print(f"  OpenAlex raw_author_name ({en_name}): {len(results)} works found")
                for r in results:
                    print(f"    - {r.get('title')} ({r.get('publication_year')}) [{r.get('cited_by_count')} cites]")
        except Exception as e:
            print(f"  OpenAlex error: {e}")

        # 2. CrossRef works query.author
        cr_url = f"https://api.crossref.org/works?query.author={enc_en}&rows=3"
        req2 = urllib.request.Request(cr_url, headers=headers)
        try:
            with urllib.request.urlopen(req2, timeout=4, context=ctx) as res:
                data = json.loads(res.read().decode())
                items = data.get("message", {}).get("items", [])
                print(f"  CrossRef query.author ({en_name}): {len(items)} works found")
                for item in items:
                    title = (item.get("title") or [""])[0]
                    # Verify author family name in authors list
                    authors = item.get("author", [])
                    matched_author = False
                    for a in authors:
                        family = a.get("family", "")
                        given = a.get("given", "")
                        if family.lower() in en_name.lower():
                            matched_author = True
                            break
                    if matched_author:
                        print(f"    - [VERIFIED AUTHOR] {title} ({item.get('created', {}).get('date-parts', [[None]])[0][0]})")
        except Exception as e:
            print(f"  CrossRef error: {e}")

if __name__ == "__main__":
    test_apis()
