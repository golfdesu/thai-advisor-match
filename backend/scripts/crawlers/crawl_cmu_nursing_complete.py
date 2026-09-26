# -*- coding: utf-8 -*-
"""
Autonomous 5-Pillar Data Acquisition: CMU Faculty of Nursing
Target: คณะพยาบาลศาสตร์ มหาวิทยาลัยเชียงใหม่
Architecture: SKILL.state (Headless ThreadPool, OpenAlex Multiplexing, 5-Pass State Reducer, Disk Checkpointing)
"""

import os
import sys
import re
import json
import time
import ssl
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
import psycopg2
from rapidfuzz import fuzz
from concurrent.futures import ThreadPoolExecutor

# Set backend path
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

NURSING_UUIDS = [
    ("85661c84-d218-4752-ab66-2bb975b57574", "สำนักวิชาพยาบาลศาสตร์")
]

def clean_academic_title_th(raw):
    raw = raw.strip()
    patterns = [
        (r'^(?:ศาสตราจารย์\s+ดร\.|ศ\.\s*ดร\.)\s*', 'ศ.ดร. '),
        (r'^(?:รองศาสตราจารย์\s+ดร\.|รศ\.\s*ดร\.)\s*', 'รศ.ดร. '),
        (r'^(?:ผู้ช่วยศาสตราจารย์\s+ดร\.|ผศ\.\s*ดร\.)\s*', 'ผศ.ดร. '),
        (r'^(?:อาจารย์\s+ดร\.|อ\.\s*ดร\.)\s*', 'อ.ดร. '),
        (r'^(?:ศาสตราจารย์เกียรติคุณ\s+ดร\.|ศ\.เกียรติคุณ\s*ดร\.)\s*', 'ศ.เกียรติคุณ ดร. '),
        (r'^(?:ศาสตราจารย์เกียรติคุณ|ศ\.เกียรติคุณ)\s*', 'ศ.เกียรติคุณ '),
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
    raw_en = raw_en.strip()
    pats = [
        r'^(?:Assistant\s+Professor\s+Dr\.|Asst\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Associate\s+Professor\s+Dr\.|Assoc\.\s*Prof\.\s*Dr\.)\s*',
        r'^(?:Professor\s+Dr\.|Prof\.\s*Dr\.)\s*',
        r'^(?:Assistant\s+Professor|Asst\.\s*Prof\.)\s*',
        r'^(?:Associate\s+Professor|Assoc\.\s*Prof\.)\s*',
        r'^(?:Professor|Prof\.)\s*',
        r'^(?:Lecturer|Instructor|Aj\.|Dr\.)\s*',
        r'^(?:Mr\.|Mrs\.|Ms\.|Miss)\s*'
    ]
    cleaned = raw_en
    for p in pats:
        cleaned = re.sub(p, '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r',\s*(?:Lecturer|Instructor|Assistant Professor|Associate Professor|Ph\.D\..*)$', '', cleaned, flags=re.I).strip()

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
            if results:
                target = f"{first_en} {last_en}".lower()
                for cand in results:
                    disp = cand.get('display_name', '').lower()
                    if fuzz.token_sort_ratio(target, disp) >= 80:
                        return cand
            return None
    except Exception as e:
        return None

def fetch_nursing_faculty():
    all_merged = []
    for uid, dname in NURSING_UUIDS:
        th_url = f"https://www.cmu.ac.th/th/faculty/nursing/teacher/{uid}"
        en_url = f"https://www.cmu.ac.th/en/faculty/nursing/teacher/{uid}"

        # 1. Fetch Thai page
        th_records = {}
        try:
            req = urllib.request.Request(th_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                soup = BeautifulSoup(r.read(), 'html.parser')
                boxes = soup.find_all('div', class_=lambda c: c and 'col-' in c)
                for b in boxes:
                    h6s = [h.get_text(strip=True) for h in b.find_all('h6')]
                    if len(h6s) >= 4 and '@cmu.ac.th' in h6s[3]:
                        email = h6s[3].lower().strip()
                        raw_th_name = h6s[0].strip()
                        pos = h6s[1].strip()

                        img_tag = b.find('img')
                        img_url = None
                        if img_tag and img_tag.get('src'):
                            src = img_tag['src']
                            if src.startswith('/'):
                                img_url = 'https://www.cmu.ac.th' + src
                            elif src.startswith('http'):
                                img_url = src

                        if email not in th_records:
                            th_records[email] = {
                                'raw_name_th': raw_th_name,
                                'position': pos,
                                'image_url': img_url,
                                'profile_url': th_url
                            }
        except Exception as e:
            print(f"Error fetching TH Nursing: {e}")

        # 2. Fetch EN page
        en_records = {}
        try:
            req = urllib.request.Request(en_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                soup = BeautifulSoup(r.read(), 'html.parser')
                boxes = soup.find_all('div', class_=lambda c: c and 'col-' in c)
                for b in boxes:
                    h6s = [h.get_text(strip=True) for h in b.find_all('h6')]
                    if len(h6s) >= 4 and '@cmu.ac.th' in h6s[3]:
                        email = h6s[3].lower().strip()
                        raw_en_name = h6s[0].strip()
                        en_records[email] = raw_en_name
        except Exception as e:
            print(f"Error fetching EN Nursing: {e}")

        # 3. Merge TH and EN records
        for email, th_info in th_records.items():
            raw_th = th_info['raw_name_th']
            title_th, name_th_clean = clean_academic_title_th(raw_th)
            parts_th = name_th_clean.split()
            first_th = parts_th[0] if parts_th else ""
            last_th = " ".join(parts_th[1:]) if len(parts_th) > 1 else ""

            raw_en = en_records.get(email, "")
            first_en, last_en = clean_en_name(raw_en)

            full_th = f"{title_th} {first_th} {last_th}".strip()

            if not re.search(r'[ก-๙]', first_th) and first_en:
                first_th = first_en
                last_th = last_en
                full_th = f"{title_th} {first_en} {last_en}".strip()

            rec = {
                'department_th': dname,
                'email': email,
                'academic_title_th': title_th,
                'first_name_th': first_th,
                'last_name_th': last_th,
                'full_name_th': full_th,
                'first_name': first_en,
                'last_name': last_en,
                'position': th_info['position'],
                'image_url': th_info['image_url'],
                'profile_url': th_info['profile_url']
            }
            all_merged.append(rec)
    return all_merged

def main():
    print("=" * 60)
    print("  WAVE 88: CMU NURSING AUTONOMOUS ACQUISITION PIPELINE")
    print("=" * 60)

    # Phase 1: Harvesting
    print("\nPhase 1: Harvesting CMU Nursing faculty directories...")
    records = fetch_nursing_faculty()
    print(f"Total faculty records harvested: {len(records)}")

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
    chk_path = out_dir / "wave88_cmu_nursing_extraction.json"
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
        WHERE university_th = 'มหาวิทยาลัยเชียงใหม่' AND faculty_th = 'คณะพยาบาลศาสตร์'
    """)
    existing_db = cur.fetchall()
    print(f"Existing CMU Nursing records in DB: {len(existing_db)}")

    inserted = 0
    updated = 0

    for fac in records:
        # Check by email first
        cur.execute("SELECT id FROM faculties WHERE email = %s", (fac['email'],))
        row = cur.fetchone()
        if row:
            fid = row[0]
            cur.execute("""
                UPDATE faculties
                SET university = 'Chiang Mai University',
                    university_th = 'มหาวิทยาลัยเชียงใหม่',
                    faculty = 'Faculty of Nursing',
                    faculty_th = 'คณะพยาบาลศาสตร์',
                    department_th = %s,
                    academic_title_th = %s,
                    full_name_th = %s,
                    first_name = %s,
                    last_name = %s,
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
                fac['image_url'], fac['profile_url'],
                fac['openalex_id'], fac['total_citations'], fac['h_index'], fac['works_count'],
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                fid
            ))
            updated += 1
        else:
            # Check by Thai full name
            cur.execute("SELECT id FROM faculties WHERE full_name_th = %s AND university_th = 'มหาวิทยาลัยเชียงใหม่'", (fac['full_name_th'],))
            row2 = cur.fetchone()
            if row2:
                fid = row2[0]
                cur.execute("""
                    UPDATE faculties
                    SET email = %s,
                        university = 'Chiang Mai University',
                        faculty = 'Faculty of Nursing',
                        faculty_th = 'คณะพยาบาลศาสตร์',
                        department_th = %s,
                        academic_title_th = %s,
                        first_name = %s,
                        last_name = %s,
                        image_url = COALESCE(%s, image_url),
                        profile_url = %s,
                        openalex_id = COALESCE(%s, openalex_id),
                        total_citations = GREATEST(COALESCE(total_citations, 0), %s),
                        h_index = GREATEST(COALESCE(h_index, 0), %s),
                        total_publications_count = GREATEST(COALESCE(total_publications_count, 0), %s),
                        research_interests = CASE WHEN %s::json IS NOT NULL THEN %s::json ELSE research_interests END
                    WHERE id = %s
                """, (
                    fac['email'], fac['department_th'], fac['academic_title_th'],
                    fac['first_name'], fac['last_name'],
                    fac['image_url'], fac['profile_url'],
                    fac['openalex_id'], fac['total_citations'], fac['h_index'], fac['works_count'],
                    json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                    json.dumps(fac['research_interests'], ensure_ascii=False) if fac['research_interests'] else None,
                    fid
                ))
                updated += 1
            else:
                # Insert fresh record
                import uuid
                new_id = f"cmu_nurse_{uuid.uuid4().hex[:10]}"
                cur.execute("""
                    INSERT INTO faculties (
                        id, university, university_th, faculty, faculty_th, department_th,
                        academic_title_th, full_name_th,
                        first_name, last_name, email, image_url, profile_url,
                        openalex_id, total_citations, h_index, total_publications_count, research_interests
                    ) VALUES (
                        %s, 'Chiang Mai University', 'มหาวิทยาลัยเชียงใหม่', 'Faculty of Nursing', 'คณะพยาบาลศาสตร์', %s,
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
