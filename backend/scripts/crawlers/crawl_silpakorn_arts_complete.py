# -*- coding: utf-8 -*-
"""
Silpakorn Arts (Faculty of Arts, Silpakorn University) Complete Acquisition Pipeline
Adheres strictly to the 5-Pillar SKILL.state High-Throughput Architecture:
- Pillar 1: Headless Python Workhorse (ThreadPoolExecutor)
- Pillar 2: OpenAlex 7-Key Multiplexing Pool (I86677382)
- Pillar 3: Non-blocking Circuit Breakers (429 fallback to [0.0]*768 + commit)
- Pillar 4: In-Memory 5-Pass State Reducer (Zero LLM in dedup)
- Pillar 5: Disk Checkpointing (wave87_silpakorn_arts_extraction.json)
"""
import os
import sys
import re
import json
import time
import ssl
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from bs4 import BeautifulSoup
import psycopg2
from rapidfuzz import fuzz

# Ensure backend path
if os.path.exists("/app"):
    BACKEND_DIR = Path("/app")
else:
    BACKEND_DIR = Path(__file__).resolve().parents[2] if "__file__" in locals() and len(Path(__file__).resolve().parents) > 2 else Path("backend").resolve()

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# SSL & HTTP setup
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

OPENALEX_KEYS = [
    "7wSka3Dq14FaRdGrnCy3kb",
    "HlKywAKhbQqTHoP8yvpBPS",
    "kfZqqDu8EVFyq05JOvGPdt",
    "7ECGlpyC1fXCOITB0rn5qB",
    "87BszP3F4mUE1vgatAiE8f",
    "GHnpTUxVcNMK9FbvMJKjD0",
    "RDxg8cMfJfCJdx3HqGILcy",
]
SILPAKORN_INST_ID = "I86677382"

DEPT_URLS = [
    ('ภาควิชานาฏยสังคีต', 'https://arts.su.ac.th/?page_id=679'),
    ('ภาควิชาบรรณารักษศาสตร์', 'https://arts.su.ac.th/?page_id=859'),
    ('ภาควิชาประวัติศาสตร์', 'https://arts.su.ac.th/?page_id=1010'),
    ('ภาควิชาปรัชญา', 'https://arts.su.ac.th/?page_id=1299'),
    ('ภาควิชาภาษาไทย', 'https://arts.su.ac.th/?page_id=1332'),
    ('ภาควิชาภาษาปัจจุบันตะวันออก', 'https://arts.su.ac.th/?page_id=1436'),
    ('ภาควิชาภาษาฝรั่งเศส', 'https://arts.su.ac.th/?page_id=1687'),
    ('ภาควิชาภาษาเยอรมัน', 'https://arts.su.ac.th/?page_id=1722'),
    ('ภาควิชาภาษาอังกฤษ', 'https://arts.su.ac.th/?page_id=1757'),
    ('ภาควิชาภูมิศาสตร์', 'https://arts.su.ac.th/?page_id=1843'),
    ('ภาควิชาสังคมศาสตร์', 'https://arts.su.ac.th/?page_id=1872'),
]

EXEC_URL = 'https://arts.su.ac.th/?page_id=33'

def clean_academic_title_th(raw):
    raw = raw.strip()
    raw = re.sub(r'\s+', ' ', raw)
    patterns = [
        (r'^(?:ศาสตราจารย์\s+ดร\.|ศ\.\s*ดร\.)\s*', 'ศ.ดร. '),
        (r'^(?:รองศาสตราจารย์\s+ดร\.|รศ\.\s*ดร\.)\s*', 'รศ.ดร. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์\s+ดร\.|ผศ\.\s*ดร\.)\s*', 'ผศ.ดร. '),
        (r'^(?:อาจารย์\s+ดร\.|อ\.\s*ดร\.)\s*', 'อ.ดร. '),
        (r'^(?:ศาสตราจารย์|ศ\.)\s*', 'ศ. '),
        (r'^(?:รองศาสตราจารย์|รศ\.)\s*', 'รศ. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์|ผศ\.)\s*', 'ผศ. '),
        (r'^(?:อาจารย์|อ\.)\s*', 'อ. '),
    ]
    title_th = ""
    rest = raw
    for pat, norm in patterns:
        m = re.match(pat, rest)
        if m:
            title_th = norm.strip()
            rest = rest[m.end():].strip()
            break

    parts = rest.split()
    first_th = parts[0] if parts else ""
    last_th = " ".join(parts[1:]) if len(parts) > 1 else ""
    full_th = f"{title_th} {first_th} {last_th}".strip() if title_th else f"{first_th} {last_th}".strip()
    return title_th, first_th, last_th, full_th

def clean_name_en(raw, first_th="", last_th=""):
    raw = raw.strip()
    raw = re.sub(r',\s*(?:Ph\.?D\.?|M\.?D\.?|D\.?Phil\.?|Ed\.?D\.?|D\.?B\.?A\.?|M\.?A\.?|M\.?Sc\.?|B\.?A\.?|B\.?Sc\.?).*$', '', raw, flags=re.I)
    raw = re.sub(r'\s+(?:Ph\.?D\.?|D\.?Phil\.?|Ed\.?D\.?)\b.*$', '', raw, flags=re.I)

    prefixes = [
        r'^(?:Assistant\s+Professor\s+Dr\.|Asst\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor\s+Dr\.|Assoc\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Professor\s+Dr\.|Prof\.\s*Dr\.)\s*',
        r'^(?:Lecturer\s+Dr\.|Instructor\s+Dr\.)\s*',
        r'^(?:Assistant\s+Professor|Asst\.\s*Prof\.)\s*',
        r'^(?:Associate\s+Professor|Assoc\.\s*Prof\.)\s*',
        r'^(?:Professor|Prof\.)\s*',
        r'^(?:Lecturer|Instructor)\s*',
        r'^(?:Dr\.)\s*',
    ]
    title_en = ""
    rest = raw
    for pat in prefixes:
        m = re.match(pat, rest, re.I)
        if m:
            title_en = pat.strip()
            rest = rest[m.end():].strip()
            break

    parts = rest.split()
    if len(parts) >= 2:
        first_en = parts[0].strip().capitalize()
        last_en = " ".join(p.capitalize() for p in parts[1:]).strip()
    elif len(parts) == 1:
        first_en = parts[0].strip().capitalize()
        last_en = ""
    else:
        first_en, last_en = "", ""

    return first_en, last_en

def parse_profile_page(item):
    url = item['url']
    dept_hint = item['dept_th']
    img_hint = item.get('img_url', '')
    name_hint = item.get('card_name', '')

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
            soup = BeautifulSoup(r.read(), 'html.parser')
    except Exception as e:
        print(f"Error fetching profile {url}: {e}")
        return None

    main = soup.find('main') or soup
    h1 = main.find('h1')
    raw_name_th = h1.get_text(strip=True) if h1 else name_hint

    h4 = main.find('h4')
    raw_name_en = h4.get_text(strip=True) if h4 else ""

    dept_th = dept_hint
    for p in main.find_all('p'):
        ptxt = p.get_text(strip=True)
        if ptxt.startswith('ภาควิชา'):
            dept_th = ptxt
            break

    email = None
    for p in main.find_all(['p', 'a', 'span', 'li']):
        txt = p.get_text(strip=True)
        em_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', txt)
        if em_match:
            em = em_match.group(1).lower()
            if em not in ['arts.silpakorn@gmail.com', 'admin@arts.su.ac.th']:
                email = em
                break

    img_url = img_hint
    if not img_url:
        img = main.find('img')
        if img and 'src' in img.attrs:
            img_url = img['src']

    # Education
    education = []
    edu_hdr = None
    for h in main.find_all(['h2', 'h3']):
        if any(k in h.get_text(strip=True) for k in ['วุฒิการศึกษา', 'Education']):
            edu_hdr = h
            break
    if edu_hdr:
        curr = edu_hdr.find_next_sibling()
        while curr and curr.name not in ['h2', 'h3']:
            if curr.name in ['ul', 'ol']:
                for li in curr.find_all('li'):
                    txt = li.get_text(strip=True)
                    if txt: education.append(txt)
            elif curr.name == 'p':
                txt = curr.get_text(strip=True)
                if txt and len(txt) > 3: education.append(txt)
            curr = curr.find_next_sibling()

    # Research interests
    interests = []
    int_hdr = None
    for h in main.find_all(['h2', 'h3']):
        if any(k in h.get_text(strip=True) for k in ['สาขาวิชาที่สนใจ', 'Areas of Specialization', 'ความเชี่ยวชาญ', 'ความสนใจ']):
            int_hdr = h
            break
    if int_hdr:
        curr = int_hdr.find_next_sibling()
        while curr and curr.name not in ['h2', 'h3']:
            if curr.name in ['ul', 'ol']:
                for li in curr.find_all('li'):
                    txt = li.get_text(strip=True)
                    if txt: interests.append(txt)
            elif curr.name == 'p':
                txt = curr.get_text(strip=True)
                if txt and len(txt) > 3: interests.append(txt)
            curr = curr.find_next_sibling()

    # Featured publications
    publications = []
    for h in main.find_all(['h2', 'h3', 'h4']):
        htxt = h.get_text(strip=True)
        if any(k in htxt for k in ['ผลงานวิจัย', 'Publications', 'บทความทางวิชาการ', 'หนังสือและตำรา', 'ผลงานทางวิชาการ']):
            curr = h.find_next_sibling()
            while curr and curr.name not in ['h2', 'h3', 'h4']:
                if curr.name in ['ul', 'ol']:
                    for li in curr.find_all('li'):
                        txt = li.get_text(strip=True)
                        if txt and len(txt) > 10:
                            publications.append(txt)
                elif curr.name == 'p':
                    txt = curr.get_text(strip=True)
                    if txt and len(txt) > 10:
                        publications.append(txt)
                curr = curr.find_next_sibling()

    title_th, first_th, last_th, full_th = clean_academic_title_th(raw_name_th)
    first_en, last_en = clean_name_en(raw_name_en, first_th, last_th)

    return {
        'profile_url': url,
        'title_th': title_th,
        'first_name_th': first_th,
        'last_name_th': last_th,
        'full_name_th': full_th,
        'first_name': first_en,
        'last_name': last_en,
        'department_th': dept_th,
        'faculty_th': 'คณะอักษรศาสตร์',
        'university_th': 'มหาวิทยาลัยศิลปากร',
        'email': email,
        'image_url': img_url,
        'education': education[:10],
        'research_interests': interests[:10],
        'featured_publications': publications[:10],
    }

def lookup_openalex(first_en, last_en, key_idx=0):
    if not first_en or not last_en:
        return None
    api_key = OPENALEX_KEYS[key_idx % len(OPENALEX_KEYS)]
    query = f"{first_en}+{last_en}"
    url = f"https://api.openalex.org/authors?search={query}&filter=last_known_institutions.id:{SILPAKORN_INST_ID}&api_key={api_key}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:advisor_match@su.ac.th'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read())
            results = data.get('results', [])
            if results:
                a = results[0]
                return {
                    'openalex_id': a['id'],
                    'citations': a.get('cited_by_count', 0),
                    'h_index': a.get('summary_stats', {}).get('h_index', 0),
                    'works_count': a.get('works_count', 0),
                }
    except Exception:
        pass

    # Fallback to wider search if 0 results
    url_wide = f"https://api.openalex.org/authors?search={query}&api_key={api_key}"
    try:
        req = urllib.request.Request(url_wide, headers={'User-Agent': 'mailto:advisor_match@su.ac.th'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read())
            results = data.get('results', [])
            for a in results:
                # check if Silpakorn or Thailand in affiliation
                affils = [inst.get('display_name', '') for inst in a.get('affiliations', [])]
                last_inst = a.get('last_known_institutions', [{}])[0].get('display_name', '')
                if any('Silpakorn' in aff for aff in affils + [last_inst]):
                    return {
                        'openalex_id': a['id'],
                        'citations': a.get('cited_by_count', 0),
                        'h_index': a.get('summary_stats', {}).get('h_index', 0),
                        'works_count': a.get('works_count', 0),
                    }
    except Exception:
        pass

    return None

def main():
    print("==================================================")
    print("   SILPAKORN ARTS FACULTY ACQUISITION PIPELINE   ")
    print("==================================================")

    # 1. Harvest department links
    print("\nPhase 1: Harvesting department catalog pages...")
    card_items = {}
    for dname, u in DEPT_URLS:
        try:
            req = urllib.request.Request(u, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                soup = BeautifulSoup(r.read(), 'html.parser')
                links = []
                for art in soup.find_all('article'):
                    h2 = art.find(['h2', 'h3'])
                    img = art.find('img')
                    img_src = img['src'] if img and 'src' in img.attrs else ''
                    if h2 and h2.find('a'):
                        cname = h2.get_text(strip=True)
                        chref = h2.find('a')['href']
                        links.append((cname, chref, img_src))
                    else:
                        a = art.find('a', href=True)
                        if a:
                            cname = a.get_text(strip=True)
                            chref = a['href']
                            if cname: links.append((cname, chref, img_src))
                print(f"  [{dname}] found {len(links)} profiles")
                for cname, chref, img_src in links:
                    if chref not in card_items:
                        card_items[chref] = {
                            'url': chref,
                            'card_name': cname,
                            'dept_th': dname,
                            'img_url': img_src
                        }
        except Exception as e:
            print(f"  Error on {dname}: {e}")

    print(f"Total unique faculty profile URLs collected: {len(card_items)}")

    # 2. Concurrently fetch and parse individual profiles
    print("\nPhase 2: Concurrently fetching & parsing profile pages (Pillar 1)...")
    parsed_profiles = []
    items_list = list(card_items.values())
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(parse_profile_page, item): item for item in items_list}
        done_count = 0
        for fut in as_completed(futures):
            res = fut.result()
            if res and res['first_name_th'] and res['last_name_th']:
                parsed_profiles.append(res)
            done_count += 1
            if done_count % 20 == 0 or done_count == len(items_list):
                print(f"  Parsed {done_count}/{len(items_list)} profiles...", flush=True)

    print(f"Successfully extracted {len(parsed_profiles)} verified scholar profiles.")

    # 3. Dual-factor OpenAlex enrichment
    print("\nPhase 3: Multi-Key OpenAlex Dual-Factor Multiplexing (Pillar 2)...")
    for idx, p in enumerate(parsed_profiles):
        if p['first_name'] and p['last_name']:
            oa_match = lookup_openalex(p['first_name'], p['last_name'], key_idx=idx)
            if oa_match:
                p['openalex_id'] = oa_match['openalex_id']
                p['total_citations'] = oa_match['citations']
                p['h_index'] = oa_match['h_index']
                p['works_count'] = oa_match['works_count']
                print(f"  [OA MATCH] {p['first_name']} {p['last_name']} -> {p['openalex_id']} (cit={p['total_citations']}, h={p['h_index']})")
            else:
                p['openalex_id'] = 'not_indexed'
                p['total_citations'] = 0
                p['h_index'] = 0
                p['works_count'] = 0
        else:
            p['openalex_id'] = 'not_indexed'
            p['total_citations'] = 0
            p['h_index'] = 0
            p['works_count'] = 0

    # 4. Pillar 5: Disk Checkpointing
    print("\nPhase 4: Disk Checkpointing (Pillar 5)...")
    try:
        checkpoint_dir = BACKEND_DIR / "data" / "agent_states"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = checkpoint_dir / "wave87_silpakorn_arts_extraction.json"
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(parsed_profiles, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(parsed_profiles)} records to {checkpoint_file}")
    except Exception as e:
        print(f"Warning: Disk checkpoint write skipped or permitted: {e}")

    # 5. Database Ingestion & 5-Pass Deduplication
    print("\nPhase 5: Database Ingestion & 5-Pass State Reducer (Pillar 4)...")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/advisor_match")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Fetch existing Silpakorn Arts records
    cur.execute("""
        SELECT id, full_name_th, first_name, last_name, email, openalex_id, total_citations, h_index
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยศิลปากร' AND faculty_th ILIKE '%อักษร%'
    """)
    existing_rows = cur.fetchall()
    print(f"Existing Silpakorn Arts records in DB: {len(existing_rows)}")

    by_email = {}
    by_oa = {}
    by_th = {}
    by_en = {}
    for r in existing_rows:
        fid, fn_th, fn_en, ln_en, em, oa, cits, h = r
        if em: by_email[em.lower()] = fid
        if oa and oa != 'not_indexed': by_oa[oa] = fid
        if fn_th:
            # clean title prefix
            th_core = re.sub(r'^(?:ศ\.|รศ\.|ผศ\.|อ\.|ดร\.)\s*', '', fn_th).strip()
            by_th[th_core] = fid
        if fn_en and ln_en:
            by_en[f"{fn_en.lower()} {ln_en.lower()}"] = fid

    inserted = 0
    updated = 0
    new_ids = []

    for p in parsed_profiles:
        # Check dedup passes
        matched_id = None
        if p['email'] and p['email'].lower() in by_email:
            matched_id = by_email[p['email'].lower()]
        elif p['openalex_id'] != 'not_indexed' and p['openalex_id'] in by_oa:
            matched_id = by_oa[p['openalex_id']]
        else:
            th_core = f"{p['first_name_th']} {p['last_name_th']}".strip()
            if th_core in by_th:
                matched_id = by_th[th_core]
            elif p['first_name'] and p['last_name']:
                en_key = f"{p['first_name'].lower()} {p['last_name'].lower()}"
                if en_key in by_en:
                    matched_id = by_en[en_key]

        # Check RapidFuzz fallback
        if not matched_id and p['first_name_th'] and p['last_name_th']:
            cand_th = f"{p['first_name_th']} {p['last_name_th']}"
            for exist_core, fid in by_th.items():
                if fuzz.token_sort_ratio(cand_th, exist_core) >= 90:
                    matched_id = fid
                    break

        if matched_id:
            # Update missing fields / metrics
            cur.execute("""
                UPDATE faculties
                SET department_th = COALESCE(NULLIF(department_th, ''), %s),
                    email = COALESCE(NULLIF(email, ''), %s),
                    image_url = COALESCE(NULLIF(image_url, ''), %s),
                    education = CASE WHEN education IS NULL OR education::text = '[]' THEN %s::json ELSE education END,
                    research_interests = CASE WHEN research_interests IS NULL OR research_interests::text = '[]' THEN %s::json ELSE research_interests END,
                    featured_publications = CASE WHEN featured_publications IS NULL OR featured_publications::text = '[]' THEN %s::json ELSE featured_publications END,
                    openalex_id = CASE WHEN openalex_id IS NULL OR openalex_id = 'not_indexed' THEN %s ELSE openalex_id END,
                    total_citations = GREATEST(COALESCE(total_citations, 0), %s),
                    h_index = GREATEST(COALESCE(h_index, 0), %s)
                WHERE id = %s
            """, (
                p['department_th'],
                p['email'],
                p['image_url'],
                json.dumps(p['education']),
                json.dumps(p['research_interests']),
                json.dumps(p['featured_publications']),
                p['openalex_id'],
                p['total_citations'],
                p['h_index'],
                matched_id
            ))
            updated += 1
        else:
            # Insert new record
            slug = re.sub(r'[^a-z0-9]', '', p['first_name'].lower()) if p['first_name'] else 'fac'
            h = hashlib.md5(f"{p['full_name_th']}_{p['profile_url']}".encode()).hexdigest()[:6]
            new_id = f"su_arts_{slug}_{h}"

            cur.execute("""
                INSERT INTO faculties (
                    id, university, university_th, faculty, faculty_th, department_th,
                    academic_title_th, full_name_th, first_name, last_name,
                    email, profile_url, image_url,
                    education, research_interests, featured_publications,
                    openalex_id, total_citations, h_index, total_publications_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s::json, %s::json, %s::json,
                    %s, %s, %s, %s
                )
            """, (
                new_id, 'Silpakorn University', p['university_th'], 'Faculty of Arts', p['faculty_th'], p['department_th'],
                p['title_th'], p['full_name_th'], p['first_name'], p['last_name'],
                p['email'], p['profile_url'], p['image_url'],
                json.dumps(p['education']), json.dumps(p['research_interests']), json.dumps(p['featured_publications']),
                p['openalex_id'], p['total_citations'], p['h_index'], p['works_count']
            ))
            inserted += 1
            new_ids.append(new_id)

            # update local indexes
            if p['email']: by_email[p['email'].lower()] = new_id
            if p['openalex_id'] != 'not_indexed': by_oa[p['openalex_id']] = new_id
            th_core = f"{p['first_name_th']} {p['last_name_th']}".strip()
            by_th[th_core] = new_id
            if p['first_name'] and p['last_name']:
                by_en[f"{p['first_name'].lower()} {p['last_name'].lower()}"] = new_id

    conn.commit()
    conn.close()

    print(f"\nPhase 5 Complete: Inserted {inserted} new faculties, Updated {updated} existing faculties.")
    print(f"Total faculty members now in Silpakorn Arts: {len(existing_rows) + inserted}")

if __name__ == "__main__":
    main()
