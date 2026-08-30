import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re, requests, json, time, threading, urllib.parse
import urllib3
urllib3.disable_warnings()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from google import genai
from pydantic import BaseModel
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from concurrent.futures import ThreadPoolExecutor

env = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'), encoding='utf-8').read()
single_key = env.split('GEMINI_API_KEY=')[-1].split('\n')[0].strip().strip('\"')
keys_str = env.split('GEMINI_API_KEYS=')[-1].split('\n')[0].strip()
API_KEYS = [k.strip().strip('\"') for k in keys_str.split(',') if k.strip()]
if single_key and single_key not in API_KEYS:
    API_KEYS.insert(0, single_key)

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

def normalize_title(t):
    if not t: return ''
    t = re.sub(r'^(หลักสูตร|สาขาวิชา)\s*', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'พ\.ศ\.\s*\d+', '', t)
    t = re.sub(r'25\d{2}', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()

# 1. Scrape KU
def scrape_ku_all():
    print("=== 🌾 Scraping Official Kasetsart University Graduate Programs ===")
    def get_ku_programs(url, deg_level):
        try:
            r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            entry = soup.find(class_=re.compile(r'entry-content|post-content', re.I))
            results = []
            if not entry:
                return results
            for tr in entry.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    code_title = tds[0].get_text(strip=True)
                    a = tr.find('a', href=True)
                    link = a['href'] if a else url
                    m = re.match(r'([A-Z0-9]+)\s*(.*)', code_title)
                    if m:
                        code, title = m.groups()
                        if len(title) > 2 and 'Download' not in title:
                            results.append({
                                'code': code,
                                'title_th': title.strip(),
                                'degree_level': deg_level,
                                'link': link,
                                'university': 'Kasetsart University',
                                'university_th': 'มหาวิทยาลัยเกษตรศาสตร์'
                            })
            return results
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    doc_68 = get_ku_programs('https://www.grad.ku.ac.th/curriculum/cer-doc-68/', 'ปริญญาเอก')
    mas_68 = get_ku_programs('https://www.grad.ku.ac.th/curriculum/cer-mas-68/', 'ปริญญาโท')
    all_ku = doc_68 + mas_68
    print(f"Total KU scraped programs: {len(all_ku)} (Doc: {len(doc_68)}, Master: {len(mas_68)})")
    return all_ku

# 2. Scrape KKU
def scrape_kku_all():
    print("=== 🎓 Scraping Official Khon Kaen University Programs ===")
    url = 'https://reg.kku.ac.th/registrar/program_info.asp'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')

        programs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'program_info_1.asp' in href:
                parsed = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed.query, encoding='tis-620')
                prog_id = qs.get('programid', [''])[0]
                prog_name = qs.get('programname', [''])[0]
                fac_name = qs.get('facultyname', [''])[0]
                level_name = qs.get('levelname', [''])[0]

                deg_level = 'ปริญญาตรี'
                if 'เอก' in level_name:
                    deg_level = 'ปริญญาเอก'
                elif 'โท' in level_name:
                    deg_level = 'ปริญญาโท'
                elif 'ประกาศนียบัตร' in level_name:
                    deg_level = 'ประกาศนียบัตร'

                full_url = f'https://reg.kku.ac.th/registrar/{href}'
                if prog_name and len(prog_name) > 2:
                    programs.append({
                        'program_id': prog_id,
                        'title_th': prog_name.strip(),
                        'faculty_th': fac_name.strip() if fac_name else 'มหาวิทยาลัยขอนแก่น',
                        'degree_level': deg_level,
                        'link': full_url,
                        'university': 'Khon Kaen University',
                        'university_th': 'มหาวิทยาลัยขอนแก่น'
                    })

        # Deduplicate
        seen = set()
        unique_kku = []
        for p in programs:
            k = (p['title_th'], p['degree_level'], p['faculty_th'])
            if k not in seen:
                seen.add(k)
                unique_kku.append(p)

        print(f"Total KKU unique programs scraped: {len(unique_kku)}")
        return unique_kku
    except Exception as e:
        print(f"Error scraping KKU: {e}")
        return []

def enrich_and_insert_ku_kku():
    ku_raw = scrape_ku_all()
    kku_raw = scrape_kku_all()

    with engine.connect() as conn:
        db_ku = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university='Kasetsart University' OR university_th LIKE '%เกษตรศาสตร์%'")).fetchall()
        db_kku = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university='Khon Kaen University' OR university_th LIKE '%ขอนแก่น%'")).fetchall()

    existing_ku_keys = set(normalize_title(r[0]) for r in db_ku)
    existing_kku_keys = set(normalize_title(r[0]) for r in db_kku)

    missing_ku = []
    for it in ku_raw:
        norm = normalize_title(it['title_th'])
        if norm not in existing_ku_keys:
            missing_ku.append(it)
            existing_ku_keys.add(norm)

    missing_kku = []
    for it in kku_raw:
        norm = normalize_title(it['title_th'])
        if norm not in existing_kku_keys:
            missing_kku.append(it)
            existing_kku_keys.add(norm)

    print(f"\n📊 Summary of Missing Programs to Ingest:")
    print(f"  - Kasetsart University (KU) Missing: {len(missing_ku)} programs")
    print(f"  - Khon Kaen University (KKU) Missing: {len(missing_kku)} programs")

    total_to_process = [(x, 'ku') for x in missing_ku] + [(x, 'kku') for x in missing_kku]
    if not total_to_process:
        print("✅ KU and KKU are already completely ingested and up to date!")
        return

    print(f"\nTotal programs to enrich via Gemini AI: {len(total_to_process)}")

    batch_size = 15
    batches = [total_to_process[i:i+batch_size] for i in range(0, len(total_to_process), batch_size)]

    def process_batch(batch_idx, batch_items):
        raw_items = [b[0] for b in batch_items]
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านระบบข้อมูลหลักสูตรมหาวิทยาลัยในประเทศไทย
โปรดแปลงข้อมูลหลักสูตรของ มหาวิทยาลัยเกษตรศาสตร์ (KU) และ มหาวิทยาลัยขอนแก่น (KKU) ต่อไปนี้ ให้เป็นข้อมูลโครงสร้าง JSON ตาม Schema ที่กำหนด:

รายการหลักสูตร:
{json.dumps(raw_items, ensure_ascii=False, indent=2)}

ข้อกำหนดสำคัญ:
1. `id`: สร้าง unique id สั้นๆ ชัดเจน เช่น `ku_eng_cpe_msc`, `kku_sci_chem_phd`, `ku_agr_biotech_phd`
2. `title_th`: ใช้ชื่อหลักสูตรภาษาไทยที่ถูกต้อง เป็นทางการ
3. `title_en`: แปลหรือระบุชื่อหลักสูตรภาษาอังกฤษทางการ (e.g. Master of Science Program in ...)
4. `degree_level`: ปริญญาตรี / ปริญญาโท / ปริญญาเอก / ประกาศนียบัตร
5. `degree_name`: ชื่อปริญญาและอักษรย่อ เช่น วท.ม., วศ.ม., ปร.ด., ศษ.ม.
6. `university` & `university_th`: Kasetsart University (มหาวิทยาลัยเกษตรศาสตร์) หรือ Khon Kaen University (มหาวิทยาลัยขอนแก่น)
7. `faculty` & `faculty_th`: คณะต้นสังกัดทางการ
8. `department` & `department_th`: ภาควิชาที่เกี่ยวข้อง
9. `program_type`: ภาคปกติ / ภาคพิเศษ / นานาชาติ
10. `duration_years`: เช่น 4 ปี, 2 ปี, 3 ปี
11. `total_credits`: เช่น 120-140 หน่วยกิต, 36 หน่วยกิต, 48 หน่วยกิต
12. `tuition_per_semester` & `tuition_total`: ประมาณการค่าธรรมเนียมตามอัตราจริง เช่น 18,000 - 35,000 บาท
13. `description`: คำอธิบายจุดเด่นหลักสูตร วัตถุประสงค์ และการเรียนการสอน (ภาษาไทย 2-3 ประโยค)
14. `curriculum_highlights`: รายการวิชาเด่นหรือทักษะที่ได้ 3-4 ข้อ
15. `career_paths`: สายอาชีพที่รองรับ 3-4 อาชีพ
16. `tags`: คำสำคัญที่เกี่ยวข้อง
"""
        client = get_client()
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': ExtractedBatch,
                        'temperature': 0.1
                    }
                )
                data = json.loads(response.text)
                return data.get('courses', [])
            except Exception as e:
                print(f"Batch {batch_idx+1} retry {attempt+1}: {e}")
                time.sleep(2 * (attempt + 1))
        return []

    print(f"Executing AI enrichment across {len(batches)} batches in parallel...")
    enriched_courses = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_batch, i, b) for i, b in enumerate(batches)]
        for i, f in enumerate(futures):
            res = f.result()
            print(f"  Enriched batch {i+1}/{len(batches)}: {len(res)} courses")
            batch_items = batches[i]
            for j, course_obj in enumerate(res):
                link = batch_items[j][0].get('link', 'https://www.ku.ac.th') if j < len(batch_items) else 'https://www.ku.ac.th'
                course_dict = course_obj.model_dump() if hasattr(course_obj, 'model_dump') else dict(course_obj)
                course_dict['website_url'] = link
                enriched_courses.append(course_dict)

    print(f"\n🧠 Generating 768-dim Vector Embeddings for {len(enriched_courses)} new courses...")
    db = SessionLocal()
    inserted_count = 0
    try:
        for idx_c, c in enumerate(enriched_courses):
            base_id = c['id']
            chk = db.query(CourseDB).filter(CourseDB.id == base_id).first()
            if chk:
                base_id = f"{base_id}_{int(time.time()*1000)%100000}"

            emb_text = f"{c['title_th']} {c.get('title_en','')} {c['university_th']} {c['faculty_th']} {c.get('department_th','')} {c.get('description','')} {' '.join(c.get('career_paths',[]))} {' '.join(c.get('curriculum_highlights',[]))}"
            vec = embedding_service.get_embedding(emb_text)

            new_db = CourseDB(
                id=base_id,
                title_th=c['title_th'],
                title_en=c.get('title_en'),
                degree_level=c['degree_level'],
                degree_name=c.get('degree_name'),
                university=c['university'],
                university_th=c['university_th'],
                faculty=c['faculty'],
                faculty_th=c['faculty_th'],
                department=c.get('department'),
                department_th=c.get('department_th'),
                program_type=c.get('program_type', 'ภาคปกติ'),
                duration_years=c.get('duration_years', '4 ปี'),
                total_credits=c.get('total_credits', '120 หน่วยกิต'),
                tuition_per_semester=c.get('tuition_per_semester', '25,000 บาท'),
                tuition_total=c.get('tuition_total', '100,000 บาท'),
                description=c.get('description', ''),
                curriculum_highlights=c.get('curriculum_highlights', []),
                career_paths=c.get('career_paths', []),
                tags=c.get('tags', []),
                website_url=c.get('website_url', 'https://www.ku.ac.th'),
                embedding_text=emb_text,
                embedding=vec
            )
            db.add(new_db)
            inserted_count += 1

            if inserted_count % 15 == 0 or inserted_count == len(enriched_courses):
                db.commit()
                print(f"  Persisted & Indexed: {inserted_count}/{len(enriched_courses)} courses")
    except Exception as e:
        db.rollback()
        print(f"Error during insertion: {e}")
    finally:
        db.close()

    print(f"\n🎉 Successfully enriched and inserted {inserted_count} official KU & KKU courses with 768-dim embeddings!")

if __name__ == '__main__':
    enrich_and_insert_ku_kku()
