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

# Key Institutional ThaiJO Journal Endpoints across Disciplines
DISCIPLINE_JOURNALS = {
    "law": [
        ("วารสารนิติศาสตร์ มหาวิทยาลัยธรรมศาสตร์", "https://so05.tci-thaijo.org/index.php/tulawjournal/search/search"),
        ("วารสารกฎหมาย จุฬาลงกรณ์มหาวิทยาลัย", "https://so05.tci-thaijo.org/index.php/LAWCHULAJOURNAL/search/search"),
        ("วารสารนิติศาสตร์ มหาวิทยาลัยเชียงใหม่", "https://so01.tci-thaijo.org/index.php/lawcmu/search/search"),
        ("วารสารนิติศาสตร์ มหาวิทยาลัยนเรศวร", "https://so04.tci-thaijo.org/index.php/law-nu/search/search")
    ],
    "business": [
        ("วารสารบริหารธุรกิจ นิด้า (NIDA Business Journal)", "https://so04.tci-thaijo.org/index.php/abacjournal/search/search"),
        ("วารสารบริหารธุรกิจและสังคมศาสตร์ มธ.", "https://so02.tci-thaijo.org/index.php/tbsjournal/search/search"),
        ("วารสารเศรษฐศาสตร์ประยุกต์ มก.", "https://so02.tci-thaijo.org/index.php/AEJ/search/search")
    ],
    "polsci": [
        ("วารสารรัฐศาสตร์ มหาวิทยาลัยธรรมศาสตร์", "https://so02.tci-thaijo.org/index.php/polsci-tu/search/search"),
        ("วารสารรัฐศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย", "https://so02.tci-thaijo.org/index.php/jps/search/search"),
        ("วารสารการบริหารท้องถิ่น มข.", "https://so04.tci-thaijo.org/index.php/colakkujournal/search/search")
    ],
    "education": [
        ("วารสารศึกษาศาสตร์ มหาวิทยาลัยเชียงใหม่", "https://so01.tci-thaijo.org/index.php/cmujed/search/search"),
        ("วารสารศึกษาศาสตร์ มหาวิทยาลัยนเรศวร", "https://so06.tci-thaijo.org/index.php/edunu/search/search")
    ],
    "regional": [
        ("วารสารวิจัย มหาวิทยาลัยนเรศวร", "https://www.journal.nu.ac.th/NUJST/search/search"),
        ("วารสารมหาวิทยาลัยทักษิณ", "https://so02.tci-thaijo.org/index.php/tsujournal/search/search"),
        ("วารสารมนุษยศาสตร์และสังคมศาสตร์ มมส.", "https://so03.tci-thaijo.org/index.php/humsujournal/search/search")
    ]
}


def clean_base_thai_name(raw_name: str) -> str:
    """Strip academic titles to get clean 'ชื่อ นามสกุล' for search query"""
    name = TITLE_STRIP_REGEX.sub("", raw_name.strip()).strip()
    # Also clean single letter abbreviations like นาย, นาง, นางสาว
    name = re.sub(r"^(ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*", "", name).strip()
    return name


def query_thaijo_journal(journal_name: str, search_url: str, author_query: str) -> list:
    """Query a specific ThaiJO journal for author's published articles"""
    params = urllib.parse.urlencode({"query": author_query})
    full_url = f"{search_url}?{params}"
    req = urllib.request.Request(full_url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as res:
            html = res.read().decode("utf-8", errors="ignore")
            # Extract article titles and links
            matches = re.findall(r'<h3 class="title">\s*<a\s+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
            results = []
            for link, title_raw in matches:
                clean_title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title_raw)).strip()
                if clean_title:
                    results.append({
                        "title": clean_title,
                        "venue": journal_name,
                        "url": link,
                        "year": None,
                        "citation_count": 0
                    })
            return results
    except Exception:
        return []


def search_all_thaijo_for_faculty(faculty_name_th: str, faculty_field: str) -> list:
    """Search relevant ThaiJO journals based on faculty discipline"""
    clean_name = clean_base_thai_name(faculty_name_th)
    if not clean_name or len(clean_name) < 4:
        return []

    # Map discipline
    field_lower = faculty_field.lower()
    endpoints = []
    if "นิติ" in field_lower or "law" in field_lower:
        endpoints.extend(DISCIPLINE_JOURNALS["law"])
    elif "พาณิชย์" in field_lower or "บริหาร" in field_lower or "การบัญชี" in field_lower or "เศรษฐ" in field_lower:
        endpoints.extend(DISCIPLINE_JOURNALS["business"])
    elif "รัฐศาสตร์" in field_lower or "polsci" in field_lower or "การเมือง" in field_lower:
        endpoints.extend(DISCIPLINE_JOURNALS["polsci"])
    elif "ศึกษา" in field_lower or "ครุศาสตร์" in field_lower:
        endpoints.extend(DISCIPLINE_JOURNALS["education"])
    else:
        endpoints.extend(DISCIPLINE_JOURNALS["regional"])
        endpoints.extend(DISCIPLINE_JOURNALS["law"][:1])

    all_found = []
    seen_titles = set()

    for jname, jurl in endpoints:
        items = query_thaijo_journal(jname, jurl, clean_name)
        for it in items:
            t = it["title"]
            if t.lower() not in seen_titles:
                seen_titles.add(t.lower())
                all_found.append(it)
        if len(all_found) >= 5:
            break

    return all_found


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
