import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re, requests, json, time, threading
import urllib3
urllib3.disable_warnings()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from google import genai
from pydantic import BaseModel
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from concurrent.futures import ThreadPoolExecutor

env = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), encoding='utf-8').read()
API_KEYS = [k.strip() for k in env.split('GEMINI_API_KEYS=')[-1].split('\n')[0].split(',') if k.strip()]
print(f"Loaded {len(API_KEYS)} Gemini API Keys")

_clients = {}
lock = threading.Lock()
idx = 0

def get_client():
    global idx
    with lock:
        k = API_KEYS[idx % len(API_KEYS)]
        idx = (idx + 1) % len(API_KEYS)
        if k not in _clients:
            _clients[k] = genai.Client(api_key=k)
        return _clients[k]

class CourseSchema(BaseModel):
    id: str
    title_th: str
    title_en: str
    degree_level: str
    degree_name: str
    university: str
    university_th: str
    faculty: str
    faculty_th: str
    department: str
    department_th: str
    program_type: str
    duration_years: str
    total_credits: str
    tuition_per_semester: str
    tuition_total: str
    description: str
    curriculum_highlights: list[str]
    career_paths: list[str]
    tags: list[str]

class ExtractedBatch(BaseModel):
    courses: list[CourseSchema]

def scrape_chula_all():
    print("=== Scraping Official Chulalongkorn Programs ===")
    url = 'https://www.chula.ac.th/academics/programs/'
    r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    nonce_match = re.search(r'programsFilterData\s*=\s*\{.*?nonce:\s*\'([^\']+)\'', r.text, re.DOTALL)
    nonce = nonce_match.group(1) if nonce_match else ''

    raw_list = []
    for p in range(1, 26):
        payload = {'action': 'filter_programs', 'nonce': nonce, 'paged': p}
        resp = requests.post('https://www.chula.ac.th/wp-admin/admin-ajax.php', data=payload, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        if resp.status_code != 200:
            break
        data = resp.json()
        html = data.get('html', '')
        if not html:
            break
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', attrs={'data-degree-program': True})
        if not items:
            break
        for it in items:
            h2 = it.find('h2')
            h3 = it.find('h3')
            title_th = h2.get_text(strip=True) if h2 else ''
            fac_th = h3.get_text(strip=True) if h3 else ''
            deg_slug = it.get('data-degree-program', '')
            lang = it.get('data-program-language', '')
            a_tag = it.find('a', href=True)
            link = a_tag['href'] if a_tag else 'https://www.chula.ac.th/academics/programs/'
            if title_th:
                raw_list.append({
                    'title_th': title_th,
                    'faculty_th': fac_th,
                    'deg_slug': deg_slug,
                    'lang': lang,
                    'link': link,
                    'university': 'Chulalongkorn University',
                    'university_th': 'จุฬาลงกรณ์มหาวิทยาลัย'
                })
        print(f"  CU Page {p}: {len(items)} items")
    print(f"Total CU items collected: {len(raw_list)}")
    return raw_list

def scrape_mahidol_all():
    print("=== Scraping Official Mahidol Graduate Programs ===")
    u = 'https://graduate.mahidol.ac.th/Admission/announce/program-sitemap.php'
    r = requests.get(u, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    raw_urls = [x.replace('&amp;', '&') for x in re.findall(r'<loc>(https://graduate\.mahidol\.ac\.th/[^<]+)</loc>', r.text) if 'announce.php?id=' in x and 'lang=en' not in x]
    print(f"Found {len(raw_urls)} Mahidol official announcement links")

    def parse_mu(url):
        try:
            res = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            soup = BeautifulSoup(res.content, 'html.parser')
            h1 = soup.find('h1')
            title_th = h1.get_text(strip=True) if h1 else ''
            if not title_th:
                return None
            faculty_th = ''
            degree_level = 'ปริญญาโท'
            for tr in soup.find_all('tr'):
                txt = tr.get_text(separator='|', strip=True)
                if 'คณะ/สถาบัน/วิทยาลัย' in txt:
                    parts = txt.split('|')
                    faculty_th = parts[-1].strip()
                for d in ['ปริญญาเอก', 'ปริญญาโท', 'ปริญญาตรี', 'ประกาศนียบัตรบัณฑิตชั้นสูง', 'ประกาศนียบัตรบัณฑิต']:
                    if d in txt:
                        degree_level = d
                        break
            return {
                'title_th': title_th,
                'faculty_th': faculty_th,
                'deg_slug': degree_level,
                'lang': 'international' if 'นานาชาติ' in title_th else 'thai',
                'link': url,
                'university': 'Mahidol University',
                'university_th': 'มหาวิทยาลัยมหิดล'
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        mu_list = list(filter(None, executor.map(parse_mu, raw_urls)))
    print(f"Total MU items collected: {len(mu_list)}")
    return mu_list

def enrich_and_insert_batch(batch, uni_slug):
    prompt = f"""You are an expert Thai Academic Program Cataloguing AI.
You are given a list of real degree programs for {batch[0]['university']}.
Enrich each item with exact academic details, professional English translation, English faculty name, standard degree abbreviation, career paths, curriculum highlights, and accurate description.

Input items:
{json.dumps(batch, ensure_ascii=False, indent=2)}

Rules:
1. 'id' must be unique and descriptive (e.g. {uni_slug}_[abbr_degree]_[slug]).
2. 'title_th' must match the real Thai curriculum name exactly.
3. 'title_en' must be the accurate standard academic English title (e.g. Master of Science Program in ...).
4. 'faculty_th' and 'faculty' (English) must be accurate official university faculties.
5. 'degree_level' must be one of: 'ปริญญาตรี', 'ปริญญาโท', 'ปริญญาเอก', 'ประกาศนียบัตรบัณฑิต', 'ประกาศนียบัตรบัณฑิตชั้นสูง'.
6. 'degree_name' should be Thai abbreviation (e.g. วท.ม., วศ.ม., ปร.ด., บธ.ม., น.บ.).
7. 'tuition_per_semester' & 'tuition_total': Provide realistic standard rates for this university/degree or 'ตามประกาศมหาวิทยาลัย'.
8. 'curriculum_highlights': list 2-4 key subject areas/specializations.
9. 'career_paths': list 3-5 high-demand career titles.
10. 'tags': 2-4 broad categorization tags.
"""
    client = get_client()
    try:
        resp = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': ExtractedBatch,
                'temperature': 0.1
            }
        )
        if resp.text:
            data = json.loads(resp.text)
            return data.get("courses", [])
    except Exception as e:
        print(f"  [AI Error] {e}")
    return []

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check existing titles in DB
    existing_titles = set(r[0].strip() for r in db.execute(CourseDB.__table__.select().with_only_columns(CourseDB.title_th)).fetchall())
    print(f"Total existing courses in DB: {len(existing_titles)}")

    cu_raw = scrape_chula_all()
    mu_raw = scrape_mahidol_all()

    all_to_process = []
    for c in cu_raw:
        if c['title_th'].strip() not in existing_titles:
            all_to_process.append((c, 'cu'))
            existing_titles.add(c['title_th'].strip()) # Avoid intra-batch duplicates

    for m in mu_raw:
        if m['title_th'].strip() not in existing_titles:
            all_to_process.append((m, 'mu'))
            existing_titles.add(m['title_th'].strip())

    print(f"\n==========================================")
    print(f"Total New Unique Programs to Ingest: {len(all_to_process)}")
    print(f"==========================================\n")

    # Process in batches of 15
    batch_size = 15
    inserted_count = 0

    for i in range(0, len(all_to_process), batch_size):
        chunk = all_to_process[i:i+batch_size]
        raw_items = [item[0] for item in chunk]
        uni_slug = chunk[0][1]

        print(f"Processing batch {i//batch_size + 1}/{(len(all_to_process) + batch_size - 1)//batch_size} ({len(chunk)} courses)...")
        enriched = enrich_and_insert_batch(raw_items, uni_slug)

        if not enriched:
            print("  Warning: enrichment returned empty, skipping batch")
            continue

        courses_to_db = []
        for c in enriched:
            # Generate embedding text
            c_dict = c if isinstance(c, dict) else c.model_dump()
            emb_text = f"{c_dict.get('title_th','')} {c_dict.get('title_en','')} {c_dict.get('faculty_th','')} {c_dict.get('faculty','')} {c_dict.get('degree_level','')} {' '.join(c_dict.get('career_paths',[]))} {' '.join(c_dict.get('tags',[]))} {c_dict.get('description','')}"

            # Compute Gemini embedding vector
            emb_vector = embedding_service.get_embedding(emb_text)

            # Ensure unique ID
            c_id = c_dict.get('id', '')
            if db.query(CourseDB).filter(CourseDB.id == c_id).first():
                c_id = f"{c_id}_{int(time.time()*1000)%100000}"

            course_obj = CourseDB(
                id=c_id,
                title_th=c_dict.get('title_th'),
                title_en=c_dict.get('title_en'),
                degree_level=c_dict.get('degree_level'),
                degree_name=c_dict.get('degree_name'),
                university=c_dict.get('university'),
                university_th=c_dict.get('university_th'),
                faculty=c_dict.get('faculty'),
                faculty_th=c_dict.get('faculty_th'),
                department=c_dict.get('department'),
                department_th=c_dict.get('department_th'),
                program_type=c_dict.get('program_type', 'ภาคปกติ'),
                duration_years=c_dict.get('duration_years', '2-4 ปี'),
                total_credits=c_dict.get('total_credits', 'ไม่ระบุ'),
                tuition_per_semester=c_dict.get('tuition_per_semester', 'ตามประกาศมหาวิทยาลัย'),
                tuition_total=c_dict.get('tuition_total', 'ตามประกาศมหาวิทยาลัย'),
                description=c_dict.get('description', ''),
                curriculum_highlights=c_dict.get('curriculum_highlights', []),
                career_paths=c_dict.get('career_paths', []),
                tags=c_dict.get('tags', []),
                website_url=raw_items[0].get('link', 'https://www.chula.ac.th' if 'Chula' in c_dict.get('university','') else 'https://mahidol.ac.th'),
                embedding_text=emb_text,
                embedding=emb_vector
            )
            courses_to_db.append(course_obj)

        try:
            db.add_all(courses_to_db)
            db.commit()
            inserted_count += len(courses_to_db)
            print(f"  --> Successfully committed {len(courses_to_db)} courses. Total inserted: {inserted_count}")
        except Exception as e:
            db.rollback()
            print(f"  [DB Commit Error] {e}")

        time.sleep(1)

    db.close()
    print(f"\nFINISHED! Total new courses added to database: {inserted_count}")

if __name__ == '__main__':
    main()
