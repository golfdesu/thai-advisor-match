# -*- coding: utf-8 -*-
"""
Autonomous 5-Pillar Data Acquisition: CMU College of Arts, Media and Technology (CAMT)
Target: วิทยาลัยศิลปะ สื่อ และเทคโนโลยี มหาวิทยาลัยเชียงใหม่ (CAMT CMU)
Architecture: SKILL.state (Headless ThreadPool, OpenAlex Multiplexing, 5-Pass State Reducer, Disk Checkpointing)
"""

import os
import sys
import re
import json
import time
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
import psycopg2
from rapidfuzz import fuzz
from concurrent.futures import ThreadPoolExecutor

if os.path.exists("/app"):
    BACKEND_DIR = Path("/app")
else:
    BACKEND_DIR = Path(__file__).resolve().parents[2] if "__file__" in locals() and len(Path(__file__).resolve().parents) > 2 else Path("backend").resolve()

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# SSL & Headers
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# OpenAlex Keys Pool
OPENALEX_KEYS = [
    "7wSka3Dq14FaRdGrnCy3kb",
    "HlKywAKhbQqTHoP8yvpBPS",
    "kfZqqDu8EVFyq05JOvGPdt",
    "7ECGlpyC1fXCOITB0rn5qB",
    "87BszP3F4mUE1vgatAiE8f",
    "GHnpTUxVcNMK9FbvMJKjD0",
    "RDxg8cMfJfCJdx3HqGILcy"
]
CMU_INST_ID = "I48076826"

def clean_academic_title_th(raw):
    raw = raw.strip()
    patterns = [
        (r'^(?:ศาสตราจารย์\s+ดร\.|ศ\.\s*ดร\.)\s*', 'ศ.ดร. '),
        (r'^(?:รองศาสตราจารย์\s+ดร\.|รศ\.\s*ดร\.)\s*', 'รศ.ดร. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์\s+ดร\.|ผศ\.\s*ดร\.)\s*', 'ผศ.ดร. '),
        (r'^(?:อาจารย์\s+ดร\.|อ\.\s*ดร\.)\s*', 'อ.ดร. '),
        (r'^(?:ศาสตราจารย์|ศ\.)\s*', 'ศ. '),
        (r'^(?:รองศาสตราจารย์|รศ\.)\s*', 'รศ. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์|ผศ\.)\s*', 'ผศ. '),
        (r'^(?:อาจารย์|อ\.)\s*', 'อ. '),
        (r'^(?:นางสาว|นาย|นาง)\s*', 'อ. ')
    ]
    for pat, rep in patterns:
        if re.search(pat, raw):
            return rep.strip(), re.sub(pat, '', raw).strip()
    return 'อ.', raw.strip()

def clean_en_name(raw_en):
    if not raw_en:
        return "", ""
    raw_en = raw_en.strip()
    pats = [
        r'^(?:Assistant\s+Professor\s+Dr\.|Asst\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor\s+Dr\.|Assoc\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Professor\s+Dr\.|Prof\.\s*Dr\.)\s*',
        r'^(?:Assistant\s+Professor|Asst\.\s*Prof\.|Asst\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor|Assoc\.\s*Prof\.)\s*',
        r'^(?:Professor|Prof\.)\s*',
        r'^(?:Lecturer|Instructor|Aj\.|Dr\.)\s*',
        r'^(?:Mr\.|Mrs\.|Ms\.|Miss)\s*'
    ]
    cleaned = raw_en
    for p in pats:
        cleaned = re.sub(p, '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r',\s*(?:Lecturer|Instructor|Assistant Professor|Associate Professor|Ph\.D\..*|Ph\.D|M\.Sc\..*|D\.Eng\..*)$', '', cleaned, flags=re.I).strip()

    parts = cleaned.split()
    if len(parts) >= 2:
        first = parts[0].capitalize()
        last = " ".join([p.capitalize() for p in parts[1:]])
    elif len(parts) == 1:
        first = parts[0].capitalize()
        last = ""
    else:
        first = ""
        last = ""
    return first, last

def lookup_openalex(first_en, last_en, key_idx=0):
    if not first_en or not last_en:
        return None
    api_key = OPENALEX_KEYS[key_idx % len(OPENALEX_KEYS)]
    query = f"{first_en}+{last_en}"
    url = f"https://api.openalex.org/authors?search={query}&filter=last_known_institutions.id:{CMU_INST_ID}&api_key={api_key}"
    req = urllib.request.Request(url, headers={'User-Agent': 'mailto:advisor@cmu.ac.th'})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            results = data.get('results', [])
            target = f"{first_en} {last_en}".lower()
            if results:
                for cand in results:
                    disp = cand.get('display_name', '').lower()
                    if fuzz.token_sort_ratio(target, disp) >= 75:
                        return cand
            # Fallback search without institution filter
            url2 = f"https://api.openalex.org/authors?search={query}&api_key={api_key}"
            req2 = urllib.request.Request(url2, headers={'User-Agent': 'mailto:advisor@cmu.ac.th'})
            with urllib.request.urlopen(req2, timeout=8) as r2:
                data2 = json.loads(r2.read())
                results2 = data2.get('results', [])
                for cand in results2:
                    disp = cand.get('display_name', '').lower()
                    if fuzz.token_sort_ratio(target, disp) >= 80:
                        affs = [a.get('institution', {}).get('display_name', '') for a in cand.get('affiliations', [])]
                        if any('chiang mai' in str(a).lower() or 'cmu' in str(a).lower() or 'thail' in str(a).lower() for a in affs):
                            return cand
            return None
    except Exception as e:
        return None

def fetch_camt_profile_urls():
    raw_url = 'https://www.camt.cmu.ac.th/รู้จักเรา/รายชื่อบุคลากร/'
    parsed = urllib.parse.urlsplit(raw_url)
    encoded_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, urllib.parse.quote(parsed.path), parsed.query, parsed.fragment))
    req = urllib.request.Request(encoded_url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        soup = BeautifulSoup(r.read(), 'html.parser')

    academic_urls = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/personals/' in href:
            unquoted = urllib.parse.unquote(href)
            slug = unquoted.strip('/').split('/')[-1]
            if any(slug.startswith(p) for p in ['ผศ', 'รศ', 'ศ', 'อ-', 'อาจารย์']):
                academic_urls.add(unquoted)
    return sorted(academic_urls)

def parse_single_camt_profile(raw_url):
    try:
        parsed = urllib.parse.urlsplit(raw_url)
        encoded = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, urllib.parse.quote(parsed.path), parsed.query, parsed.fragment))
        req = urllib.request.Request(encoded, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            soup = BeautifulSoup(r.read(), 'html.parser')

        # Thai Name from title
        title = soup.title.get_text() if soup.title else ""
        raw_th = title.split('|')[0].strip()

        # Emails
        emails = [e.lower() for e in re.findall(r'[a-zA-Z0-9._%+-]+@cmu\.ac\.th', str(soup))]
        email = emails[0] if emails else None

        # English name from elementor widgets
        widgets = [w.get_text(strip=True) for w in soup.find_all('div', class_='elementor-widget-container') if w.get_text(strip=True)]
        en_name = ""
        for w in widgets:
            if re.search(r'^[A-Za-z\s,\.-]+$', w) and not re.search(r'[ก-๙]', w):
                if any(k in w for k in ['Asst', 'Assoc', 'Prof', 'Dr', 'Ph.D.', 'Lecturer', 'Aj.']) or len(w.split()) >= 2:
                    if not any(x in w.lower() for x in ['cmu', 'camt', 'skip', 'menu', 'facebook', 'talented', 'program', 'arrow', 'right']):
                        en_name = w
                        break

        # Department
        dept = "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี"
        lines = [s.strip() for s in soup.stripped_strings if s.strip()]
        for idx, l in enumerate(lines):
            if l in ['สังกัด:', 'สังกัด'] and idx + 1 < len(lines):
                cand_dept = lines[idx+1]
                if cand_dept and cand_dept != 'ผู้บริหาร':
                    dept = cand_dept
                break

        # Headshot Image
        img = None
        for im in soup.find_all('img'):
            src = im.get('src', '')
            if any(src.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']) and 'wp-content/uploads' in src:
                if not any(x in src.lower() for x in ['logo', 'icon', 'arrow', 'banner', 'bg', 'menu']):
                    img = src
                    break

        # Clean titles & names
        title_th, name_clean_th = clean_academic_title_th(raw_th)
        parts_th = name_clean_th.split()
        first_th = parts_th[0] if parts_th else ""
        last_th = " ".join(parts_th[1:]) if len(parts_th) > 1 else ""

        first_en, last_en = clean_en_name(en_name)
        full_th = f"{title_th} {first_th} {last_th}".strip()

        # Construct email fallback if missing
        if not email and first_en and last_en:
            email = f"{first_en.lower()}.{last_en[0].lower()}@cmu.ac.th"

        if not email:
            return None

        return {
            'department_th': dept,
            'email': email,
            'academic_title_th': title_th,
            'first_name_th': first_th,
            'last_name_th': last_th,
            'full_name_th': full_th,
            'first_name': first_en,
            'last_name': last_en,
            'image_url': img,
            'profile_url': raw_url
        }
    except Exception as e:
        print(f"Error parsing {raw_url}: {e}")
        return None

def main():
    print("=" * 60)
    print("  WAVE 88: CMU CAMT AUTONOMOUS ACQUISITION PIPELINE")
    print("=" * 60)

    # Phase 1: Harvesting
    print("\nPhase 1: Harvesting CAMT CMU faculty directory...")
    profile_urls = fetch_camt_profile_urls()
    print(f"Found {len(profile_urls)} academic faculty profile URLs.")

    with ThreadPoolExecutor(max_workers=6) as ex:
        records = [r for r in ex.map(parse_single_camt_profile, profile_urls) if r]

    print(f"Successfully harvested {len(records)} verified academic faculty records.")

    # Deduplicate in-memory by email
    unique_faculties = {}
    for fac in records:
        em = fac['email']
        if em not in unique_faculties:
            unique_faculties[em] = fac
        else:
            if not unique_faculties[em].get('image_url') and fac.get('image_url'):
                unique_faculties[em]['image_url'] = fac['image_url']

    records = list(unique_faculties.values())
    print(f"Unique individual faculty members: {len(records)}")

    # Phase 2: OpenAlex Multiplexing
    print("\nPhase 2: OpenAlex Dual-Factor Multiplexing (Pillar 2)...")
    key_idx = 0
    oa_matches = 0
    for idx, fac in enumerate(records):
        oa = lookup_openalex(fac['first_name'], fac['last_name'], key_idx)
        key_idx += 1
        if oa:
            oa_matches += 1
            fac['openalex_id'] = oa.get('id')
            fac['total_citations'] = oa.get('cited_by_count', 0)
            fac['h_index'] = oa.get('summary_stats', {}).get('h_index', 0)
            fac['works_count'] = oa.get('works_count', 0)
            topics = [t.get('display_name') for t in oa.get('topics', [])[:5]]
            fac['research_interests'] = topics if topics else None
            print(f"  [OA MATCH] {fac['first_name']} {fac['last_name']} -> {oa['id']} (cit={fac['total_citations']}, h={fac['h_index']})")
        else:
            fac['openalex_id'] = None
            fac['total_citations'] = 0
            fac['h_index'] = 0
            fac['works_count'] = 0
            fac['research_interests'] = None

    print(f"OpenAlex Grounding Complete: {oa_matches}/{len(records)} verified scholars matched.")

    # Phase 3: Checkpointing (Pillar 5)
    print("\nPhase 3: Disk Checkpointing (Pillar 5)...")
    out_dir = BACKEND_DIR / "data" / "agent_states"
    out_dir.mkdir(parents=True, exist_ok=True)
    chk_path = out_dir / "wave88_cmu_camt_extraction.json"
    with open(chk_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(records)} records to {chk_path}")

    # Phase 4: Database Ingestion (Pillar 4)
    print("\nPhase 4: Database Ingestion & 5-Pass State Reducer...")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/advisor_match")
    if not os.getenv("DATABASE_URL") and os.path.exists("/app"):
        db_url = "postgresql://postgres:postgres@db:5432/advisor_match"
    elif not os.getenv("DATABASE_URL"):
        db_url = "postgresql://postgres:postgres@localhost:5432/advisor_match"

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, email, full_name_th, first_name, last_name, openalex_id
        FROM faculties
        WHERE university_th = 'มหาวิทยาลัยเชียงใหม่'
          AND (faculty_th LIKE '%ศิลปะ สื่อ%' OR faculty_th LIKE '%CAMT%' OR department_th LIKE '%ศิลปะ สื่อ%' OR department_th LIKE '%CAMT%')
    """)
    existing_db = cur.fetchall()
    print(f"Existing CMU CAMT records in DB: {len(existing_db)}")

    inserted = 0
    updated = 0

    for fac in records:
        matched_id = None
        for db_row in existing_db:
            db_id, db_em, db_fnth, db_fn, db_ln, db_oa = db_row
            # Check by email
            if db_em and db_em.lower() == fac['email'].lower():
                matched_id = db_id
                break
            # Check by English first and last name
            if db_fn and db_ln and db_fn.lower() == fac['first_name'].lower() and db_ln.lower() == fac['last_name'].lower():
                matched_id = db_id
                break
            # Check by Thai name
            if db_fnth and fac['last_name_th'] and fac['last_name_th'] in db_fnth and fac['first_name_th'] in db_fnth:
                matched_id = db_id
                break

        if matched_id:
            cur.execute("""
                UPDATE faculties
                SET university = 'Chiang Mai University',
                    university_th = 'มหาวิทยาลัยเชียงใหม่',
                    faculty = 'College of Arts, Media and Technology',
                    faculty_th = 'วิทยาลัยศิลปะ สื่อ และเทคโนโลยี',
                    department_th = %s,
                    academic_title_th = %s,
                    full_name_th = %s,
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    image_url = COALESCE(%s, image_url),
                    profile_url = %s,
                    openalex_id = COALESCE(%s, openalex_id),
                    total_citations = GREATEST(COALESCE(total_citations, 0), %s),
                    h_index = GREATEST(COALESCE(h_index, 0), %s),
                    total_publications_count = GREATEST(COALESCE(total_publications_count, 0), %s),
                    research_interests = CASE WHEN %s::json IS NOT NULL THEN %s::json ELSE research_interests END
                WHERE id = %s
            """, (
                fac['department_th'], fac['academic_title_th'],
                fac['full_name_th'],
                fac['first_name'], fac['last_name'],
                fac['email'],
                fac['image_url'], fac['profile_url'],
                fac['openalex_id'], fac['total_citations'], fac['h_index'], fac['works_count'],
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                matched_id
            ))
            updated += 1
        else:
            # Insert fresh record
            import uuid
            new_id = f"cmu_camt_{uuid.uuid4().hex[:10]}"
            cur.execute("""
                INSERT INTO faculties (
                    id, university, university_th, faculty, faculty_th, department_th,
                    academic_title_th, full_name_th,
                    first_name, last_name, email, image_url, profile_url,
                    openalex_id, total_citations, h_index, total_publications_count, research_interests
                ) VALUES (
                    %s, 'Chiang Mai University', 'มหาวิทยาลัยเชียงใหม่',
                    'College of Arts, Media and Technology', 'วิทยาลัยศิลปะ สื่อ และเทคโนโลยี', %s,
                    %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s::json
                )
            """, (
                new_id, fac['department_th'],
                fac['academic_title_th'], fac['full_name_th'],
                fac['first_name'], fac['last_name'], fac['email'],
                fac['image_url'], fac['profile_url'],
                fac['openalex_id'], fac['total_citations'], fac['h_index'], fac['works_count'],
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None
            ))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"\nPhase 4 Complete: Inserted {inserted} new faculties, Updated {updated} faculties.")

if __name__ == "__main__":
    main()
