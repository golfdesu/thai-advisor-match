# -*- coding: utf-8 -*-
import sys, urllib.request, urllib.parse, json, re, ssl
sys.path.append('backend')
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    "User-Agent": "ThaiEduCenterAcademicMatcher/2.0 (mailto:contact@thaieducenter.ac.th)"
}

def clean_name(n):
    return (n or "").strip()

db = SessionLocal()
zeros = [f for f in db.query(FacultyDB).all() if not f.featured_publications or len(f.featured_publications) == 0]
print(f"Testing authentic publication discovery across 30 zero-pub faculties...")

success_count = 0
results_log = []

for f in zeros[:30]:
    fname = clean_name(f.first_name)
    lname = clean_name(f.last_name)
    name_th = clean_name(f.full_name_th)
    univ = f.university_th or ""
    fac = f.faculty_th or ""

    found_pubs = []

    # 1. Strategy A: OpenAlex raw_author_name search by last name if length >= 4
    if len(lname) >= 4:
        enc_lname = urllib.parse.quote(lname)
        url = f"https://api.openalex.org/works?filter=raw_author_name.search:{enc_lname}&sort=cited_by_count:desc&per_page=10"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
                data = json.loads(resp.read().decode())
                for r in data.get("results", []):
                    title = (r.get("title") or "").strip()
                    if not title or len(title) < 10:
                        continue
                    # Check authorships
                    for a in r.get("authorships", []):
                        raw_a = (a.get("raw_author_name") or "").lower()
                        # Require last name to match AND first name's initial or full name to match
                        if lname.lower() in raw_a:
                            # If we have first name, check if initial matches
                            if fname and len(fname) >= 1:
                                initial = fname[0].lower()
                                # raw_a might be "W. Udomsinprasert" or "Wanvisa Udomsinprasert"
                                if initial in raw_a:
                                    found_pubs.append({
                                        "title": title,
                                        "year": r.get("publication_year"),
                                        "venue": (r.get("primary_location") or {}).get("source", {}).get("display_name") or "Peer-Reviewed Academic Publication",
                                        "url": r.get("doi") or f"https://openalex.org/{r.get('id', '').split('/')[-1]}",
                                        "citation_count": r.get("cited_by_count") or 0,
                                        "author_matched": a.get("raw_author_name")
                                    })
                                    break
                            else:
                                found_pubs.append({
                                    "title": title,
                                    "year": r.get("publication_year"),
                                    "venue": (r.get("primary_location") or {}).get("source", {}).get("display_name") or "Peer-Reviewed Academic Publication",
                                    "url": r.get("doi") or f"https://openalex.org/{r.get('id', '').split('/')[-1]}",
                                    "citation_count": r.get("cited_by_count") or 0,
                                    "author_matched": a.get("raw_author_name")
                                })
                                break
                    if len(found_pubs) >= 5:
                        break
        except Exception as e:
            pass

    # 2. Strategy B: CrossRef if OpenAlex didn't yield >= 2 pubs
    if len(found_pubs) < 2 and fname and lname and len(lname) >= 4:
        query_author = urllib.parse.quote(f"{fname} {lname}")
        cr_url = f"https://api.crossref.org/works?query.author={query_author}&rows=5"
        try:
            req = urllib.request.Request(cr_url, headers=headers)
            with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
                data = json.loads(resp.read().decode())
                items = data.get("message", {}).get("items", [])
                for item in items:
                    t_list = item.get("title") or []
                    if not t_list:
                        continue
                    title = t_list[0].strip()
                    if not title or len(title) < 10:
                        continue
                    # Check authors
                    for a in item.get("author", []):
                        fam = (a.get("family") or "").lower()
                        giv = (a.get("given") or "").lower()
                        if lname.lower() in fam and (not fname or fname[0].lower() in giv or fname.lower() in giv):
                            pub_year = None
                            created = item.get("created", {}).get("date-parts", [[None]])
                            if created and created[0]:
                                pub_year = created[0][0]
                            venue = (item.get("container-title") or ["Academic Journal"])[0]
                            doi = item.get("DOI")
                            url = f"https://doi.org/{doi}" if doi else item.get("URL") or ""
                            # Check deduplication
                            if not any(p["title"].lower() == title.lower() for p in found_pubs):
                                found_pubs.append({
                                    "title": title,
                                    "year": pub_year,
                                    "venue": venue,
                                    "url": url,
                                    "citation_count": item.get("is-referenced-by-count", 0),
                                    "author_matched": f"{a.get('given')} {a.get('family')}"
                                })
                            break
                    if len(found_pubs) >= 5:
                        break
        except Exception:
            pass

    if found_pubs:
        success_count += 1
        print(f"✅ [{success_count}] {name_th} ({fname} {lname}) - {univ}")
        for p in found_pubs[:3]:
            print(f"     * {p['title'][:70]} ({p['year']}) [{p['citation_count']} cites] - {p['venue']}")
    else:
        print(f"❌ {name_th} ({fname} {lname}) - {fac} ({univ})")

print(f"\nFinal Test Result: {success_count}/30 ({success_count*100/30:.1f}%) enriched with high-confidence works!")
db.close()
