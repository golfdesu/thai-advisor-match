# -*- coding: utf-8 -*-
"""
ThaiJO Academic Journal Crawler & Enricher for Thai Humanities, Law, Social Sciences, Business
Directly queries designated ThaiJO academic journal search engines by faculty author name
to discover peer-reviewed Thai academic articles, law review publications, and research papers.
"""

import sys
import os
import re
import time
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ThaiJO runs OJS3 sharded over so0N.tci-thaijo.org hosts. Per-journal
# /index.php/<journal>/search/search now renders only the search form (zero results) —
# since the OJS3 upgrade all hits come from the AGGREGATE endpoint
# /index.php/index/search/search?query=..., which we must poll per shard.
# (Verified 10 ก.ย.: old journal-scoped GETs returned the <h3 class="title"> markup
# that no longer exists → the whole 3,809-faculty wave enriched exactly 0 rows.)
THAIJO_SHARDS = [f"https://so{n:02d}.tci-thaijo.org" for n in range(1, 7)]

# Aggregate result item: <h3 class="title"><a id="article-89" href="URL">TITLE</a></h3>
# <div class="meta"><div class="authors">A, B, C</div>...<div class="published">2025-02-10</div>
ITEM_RE = re.compile(
    r'<h3 class="title">\s*<a[^>]*href="(?P<url>[^"]+)"[^>]*>\s*(?P<title>.*?)\s*</a>\s*</h3>'
    r'\s*<div class="meta">\s*<div class="authors">(?P<authors>.*?)</div>'
    r'.*?(?:<div class="published">\s*(?P<date>\d{4})|\Z)',
    re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
JOURNAL_PATH_RE = re.compile(r"index\.php/([^/]+)/article/view")


def clean_base_thai_name(raw_name: str) -> str:
    """Strip academic titles to get clean 'ชื่อ นามสกุล' for search query"""
    name = TITLE_STRIP_REGEX.sub("", raw_name.strip()).strip()
    # Also clean single letter abbreviations like นาย, นาง, นางสาว
    name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", name).strip()
    return name


def query_thaijo_shard(shard: str, author_query: str) -> list:
    """Author-scoped search on one ThaiJO OJS3 shard's aggregate search endpoint.

    The `authors` GET field is the OJS3 metadata author filter (verified live: a
    full Thai 'name surname' returns that person's own articles, not everyone
    mentioning the string). We still re-check the rendered author list before
    accepting a hit — a wrong publication attributed to a real researcher is
    worse than none, since these titles feed advisor profiles and embeddings.
    """
    params = urllib.parse.urlencode({"authors": author_query})
    full_url = f"{shard}/index.php/index/search/search?{params}"
    req = urllib.request.Request(full_url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as res:
            html = res.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    results = []
    for m in ITEM_RE.finditer(html):
        clean_title = re.sub(r"\s+", " ", TAG_RE.sub("", m.group("title"))).strip()
        authors_txt = re.sub(r"\s+", " ", TAG_RE.sub("", m.group("authors"))).strip()
        if not clean_title or author_query not in authors_txt:
            continue
        jm = JOURNAL_PATH_RE.search(m.group("url") or "")
        results.append({
            "title": clean_title,
            "venue": f"ThaiJO ({jm.group(1)})" if jm else "ThaiJO",
            "url": m.group("url"),
            "year": int(m.group("date")) if m.group("date") else None,
            "citation_count": 0,
        })
    return results


def search_all_thaijo_for_faculty(faculty_name_th: str, faculty_field: str) -> list:
    """Author-scoped ThaiJO search across the so01..so06 shards for one faculty name."""
    clean_name = clean_base_thai_name(faculty_name_th)
    if not clean_name or len(clean_name) < 4 or not re.search(r"[฀-๿]", clean_name):
        return []

    all_found = []
    seen_titles = set()
    for shard in THAIJO_SHARDS:
        for it in query_thaijo_shard(shard, clean_name):
            if it["title"].lower() not in seen_titles:
                seen_titles.add(it["title"].lower())
                all_found.append(it)
        if len(all_found) >= 5:
            break

    return all_found[:5]


def run_thaijo_enrichment():
    db = SessionLocal()
    # Find faculties with 0 or < 2 publications in Social Sciences, Law, Humanities, Education, Business
    facs = db.query(FacultyDB).all()
    target_faculties = []
    for f in facs:
        pubs = f.featured_publications or []
        if len(pubs) < 2:
            target_faculties.append((f.id, f.full_name_th, f.faculty_th or f.faculty or "", pubs))
    db.close()

    total = len(target_faculties)
    print("=" * 65)
    print(f"🚀 STARTING THAIJO ACADEMIC ARTICLE CRAWLER FOR {total} TARGET FACULTIES")
    print("=" * 65)

    enriched_count = 0
    start_time = time.time()

    def crawl_task(item):
        fid, name_th, f_field, existing_pubs = item
        found_articles = search_all_thaijo_for_faculty(name_th, f_field)
        return fid, name_th, found_articles, existing_pubs

    # Run in batches of 40
    batch_size = 40
    for i in range(0, total, batch_size):
        chunk = target_faculties[i:i + batch_size]
        chunk_results = []

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(crawl_task, item) for item in chunk]
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    chunk_results.append(res)
                except Exception:
                    pass

        # Write to DB
        db_write = SessionLocal()
        saved_chunk = 0
        for fid, name_th, found_articles, existing_pubs in chunk_results:
            if not found_articles:
                continue

            rec = db_write.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if not rec:
                continue

            existing_titles = set()
            merged = []
            for ep in (rec.featured_publications or []):
                t = ep.get("title") if isinstance(ep, dict) else str(ep)
                if t:
                    existing_titles.add(t.lower())
                    merged.append(ep)

            for fa in found_articles:
                ft = fa["title"]
                if ft.lower() not in existing_titles:
                    existing_titles.add(ft.lower())
                    merged.append(fa)

            rec.featured_publications = merged
            saved_chunk += 1
            enriched_count += 1

        db_write.commit()
        db_write.close()

        completed = min(i + batch_size, total)
        print(f"[{completed}/{total}] ThaiJO matches in chunk: {saved_chunk} | Total enriched: {enriched_count}")

    print("=" * 65)
    print(f"✅ THAIJO CRAWLER COMPLETED! Total enriched: {enriched_count} faculties in {time.time() - start_time:.1f}s")
    print("=" * 65)


if __name__ == "__main__":
    run_thaijo_enrichment()
