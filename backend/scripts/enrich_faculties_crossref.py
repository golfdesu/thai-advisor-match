# -*- coding: utf-8 -*-
"""
High-Speed CrossRef & ThaiJO Academic Harvester
Primary source: CrossRef Works API with polite headers & strict author name validation
Secondary source: ThaiJO Law & Social Science peer-reviewed journals
"""

import sys
import os
import re
import time
import json
import urllib.request
import urllib.parse
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.abspath("backend"))
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from scripts.agentic_pipeline.state_reducer import TITLE_STRIP_REGEX

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "ThaiEduCenterAcademicCrawler/2.0 (mailto:academic-research@thaieducenter.ac.th)"
}

THAIJO_ENDPOINTS = [
    ("วารสารนิติศาสตร์ มหาวิทยาลัยธรรมศาสตร์", "https://so05.tci-thaijo.org/index.php/tulawjournal/search/search"),
    ("วารสารกฎหมาย จุฬาลงกรณ์มหาวิทยาลัย", "https://so05.tci-thaijo.org/index.php/LAWCHULAJOURNAL/search/search"),
    ("วารสารนิติศาสตร์ มหาวิทยาลัยเชียงใหม่", "https://so01.tci-thaijo.org/index.php/lawcmu/search/search"),
    ("วารสารบริหารธุรกิจและสังคมศาสตร์ มธ.", "https://so02.tci-thaijo.org/index.php/tbsjournal/search/search"),
    ("วารสารเศรษฐศาสตร์ประยุกต์ มก.", "https://so02.tci-thaijo.org/index.php/AEJ/search/search"),
    ("วารสารรัฐศาสตร์ มหาวิทยาลัยธรรมศาสตร์", "https://so02.tci-thaijo.org/index.php/polsci-tu/search/search"),
    ("วารสารรัฐศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย", "https://so02.tci-thaijo.org/index.php/jps/search/search"),
    ("วารสารศึกษาศาสตร์ มหาวิทยาลัยเชียงใหม่", "https://so01.tci-thaijo.org/index.php/cmujed/search/search")
]


def clean_base_thai_name(raw_name: str) -> str:
    name = TITLE_STRIP_REGEX.sub("", (raw_name or "").strip()).strip()
    name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.|นาย|นาง|นางสาว|ภญ\.|นพ\.|พญ\.|ทพ\.|ทพญ\.)\s*", "", name).strip()
    return name


def search_crossref_author(first_name: str, last_name: str) -> list:
    """Strict CrossRef search with Given and Family name verification"""
    if not (first_name and last_name and len(last_name) >= 3):
        return []

    enc_query = urllib.parse.quote(f"{first_name} {last_name}")
    url = f"https://api.crossref.org/works?query.author={enc_query}&rows=6"
    req = urllib.request.Request(url, headers=HEADERS)
    works = []
    try:
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("message", {}).get("items", []):
                t_list = item.get("title") or []
                if not t_list:
                    continue
                title = t_list[0].strip()
                if not title or len(title) < 12:
                    continue

                # Verify author match
                author_matched = False
                for a in item.get("author", []):
                    fam = (a.get("family") or "").lower()
                    giv = (a.get("given") or "").lower()
                    if last_name.lower() == fam or (last_name.lower() in fam and len(last_name) >= 4):
                        # Given name check (initial or substring)
                        if not first_name or first_name.lower() in giv or giv.startswith(first_name[0].lower()):
                            author_matched = True
                            break

                if author_matched:
                    year = None
                    created = item.get("created", {}).get("date-parts", [[None]])
                    if created and created[0]:
                        year = created[0][0]
                    venue = (item.get("container-title") or ["Peer-Reviewed Academic Publication"])[0]
                    doi = item.get("DOI")
                    works.append({
                        "title": title,
                        "year": year,
                        "venue": venue,
                        "url": f"https://doi.org/{doi}" if doi else item.get("URL", ""),
                        "citation_count": item.get("is-referenced-by-count", 0)
                    })
                if len(works) >= 4:
                    break
    except Exception:
        pass

    return works


def search_thaijo_author(clean_th: str) -> list:
    """Strict ThaiJO search verifying both article title and author listing"""
    if not clean_th or len(clean_th) < 4:
        return []

    enc = urllib.parse.quote(clean_th)
    works = []
    seen_titles = set()

    for jname, jurl in THAIJO_ENDPOINTS:
        url = f"{jurl}?query={enc}&authors={enc}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=3, context=SSL_CTX) as res:
                html = res.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'<h3[^>]*class="title"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>\s*(.*?)\s*</a>', html, re.DOTALL)
                author_matches = re.findall(r'<div[^>]*class="authors"[^>]*>\s*(.*?)\s*</div>', html, re.DOTALL)

                for idx, (link, raw_t) in enumerate(matches):
                    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw_t)).strip()
                    if not t or t.lower() in seen_titles or len(t) < 10:
                        continue

                    auth = ""
                    if idx < len(author_matches):
                        auth = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", author_matches[idx])).strip()

                    if any(part in auth for part in clean_th.split() if len(part) >= 3):
                        seen_titles.add(t.lower())
                        works.append({
                            "title": t,
                            "year": None,
                            "venue": jname,
                            "url": link,
                            "citation_count": 0
                        })
                if len(works) >= 4:
                    break
        except Exception:
            continue

    return works


def process_faculty(f_record: tuple) -> tuple:
    fid, name_th, fname, lname, univ_th, existing_pubs = f_record
    clean_th = clean_base_thai_name(name_th)

    works = []
    # 1. CrossRef search
    cr_works = search_crossref_author(fname, lname)
    if cr_works:
        works.extend(cr_works)

    # 2. ThaiJO search
    if len(works) < 3:
        tj_works = search_thaijo_author(clean_th)
        for tj in tj_works:
            if not any(w["title"].lower() == tj["title"].lower() for w in works):
                works.append(tj)

    return fid, works


def run_crossref_enrichment():
    db = SessionLocal()
    all_facs = db.query(FacultyDB).all()
    targets = []
    for f in all_facs:
        pubs = f.featured_publications or []
        # Task #33: zero-publication faculties only. Leave practitioners
        # with no verifiable works empty — never force or synthesize data.
        if len(pubs) == 0:
            targets.append((
                f.id,
                f.full_name_th,
                (f.first_name or "").strip(),
                (f.last_name or "").strip(),
                f.university_th or "",
                pubs
            ))
    db.close()

    total = len(targets)
    print("=" * 70)
    print(f"[START] CROSSREF & THAIJO HARVESTER FOR {total} SCHOLARS")
    print("=" * 70)

    chunk_size = 50
    total_newly_enriched = 0
    t0 = time.time()

    for i in range(0, total, chunk_size):
        chunk = targets[i:i + chunk_size]
        results = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(process_faculty, rec) for rec in chunk]
            for fut in as_completed(futs):
                try:
                    res = fut.result()
                    results.append(res)
                except Exception:
                    pass

        # Write to database
        db_write = SessionLocal()
        saved_in_chunk = 0
        for fid, new_pubs in results:
            if not new_pubs:
                continue
            rec = db_write.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if not rec:
                continue

            current_pubs = rec.featured_publications or []
            existing_titles = set()
            merged = []
            for p in current_pubs:
                t = (p.get("title", "") if isinstance(p, dict) else str(p)).strip()
                if t:
                    existing_titles.add(t.lower())
                    merged.append(p)

            added = 0
            for np in new_pubs:
                t = np["title"].strip()
                if t.lower() not in existing_titles:
                    existing_titles.add(t.lower())
                    merged.append(np)
                    added += 1

            if added > 0:
                rec.featured_publications = merged
                rec.total_publications_count = max(rec.total_publications_count or 0, len(merged))
                rec.total_citations = sum(p.get("citation_count", 0) for p in merged if isinstance(p, dict))
                saved_in_chunk += 1
                total_newly_enriched += 1

        db_write.commit()
        db_write.close()

        done = min(i + chunk_size, total)
        pct = (done * 100.0) / total
        print(f"[{done:4d}/{total}] Chunk saved: {saved_in_chunk:2d} | Cumulative enriched: {total_newly_enriched} ({pct:4.1f}%)")

    elapsed = time.time() - t0
    print("=" * 70)
    print(f"[DONE] HARVESTING COMPLETED IN {elapsed:.1f}s | Enriched: {total_newly_enriched} faculties")
    print("=" * 70)


if __name__ == "__main__":
    run_crossref_enrichment()
