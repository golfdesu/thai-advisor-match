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

# 1. Scrape KMUTT (บางมด)
def scrape_kmutt_all():
    print("=== 🎓 Scraping KMUTT (มจธ. บางมด) Programs ===")
    levels = [
        ('bachelor', 'ปริญญาตรี', 'https://admission.kmutt.ac.th/bachelor'),
        ('master', 'ปริญญาโท', 'https://admission.kmutt.ac.th/master'),
        ('doctoral', 'ปริญญาเอก', 'https://admission.kmutt.ac.th/doctoral')
    ]
    courses = []
    for slug, deg_lvl, url in levels:
        try:
            r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            # find all text blocks containing สาขาวิชา
            for el in soup.find_all(['h3', 'h4', 'h5', 'p', 'li', 'a', 'div']):
                t = el.get_text(separator=' ', strip=True)
                if 'สาขาวิชา' in t and len(t) < 120 and len(t) > 5:
                    clean_title = re.sub(r'[\r\n\t]+', ' ', t).strip()
                    courses.append({
                        'title_th': clean_title,
                        'degree_level': deg_lvl,
                        'link': url,
                        'university': "King Mongkut's University of Technology Thonburi",
                        'university_th': 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี'
                    })
        except Exception as e:
            print(f"Error fetching KMUTT {slug}: {e}")

    # Unique
    seen = set()
    unique_kmutt = []
    for c in courses:
        k = (normalize_title(c['title_th']), c['degree_level'])
        if k not in seen:
            seen.add(k)
            unique_kmutt.append(c)
    print(f"Total KMUTT unique programs scraped: {len(unique_kmutt)}")
    return unique_kmutt

# 2. Scrape KMITL (ลาดกระบัง)
def scrape_kmitl_all():
    print("=== 🎓 Scraping KMITL (สจล. ลาดกระบัง) Programs ===")
    courses = []
    for i in range(1, 13):
        url = f'https://curriculum.kmitl.ac.th/faculty/{i}'
        try:
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            h1 = soup.find('h1') or soup.find('h2')
            fac_name = h1.get_text(strip=True) if h1 else 'สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง'

            for a in soup.find_all('a', href=True):
                t = a.get_text(separator=' ', strip=True)
                if any(k in t for k in ['หลักสูตร', 'สาขาวิชา', 'วศ.บ.', 'วท.บ.', 'สถ.บ.', 'ค.อ.บ.', 'บธ.บ.', 'ศศ.บ.', 'พ.บ.', 'ท.บ.', 'พย.บ.']):
                    if len(t) < 140 and len(t) > 6 and 'ดูภาควิชา' not in t:
                        deg_lvl = 'ปริญญาตรี'
                        if 'ปริญญาโท' in t or 'มหาบัณฑิต' in t:
                            deg_lvl = 'ปริญญาโท'
                        elif 'ปริญญาเอก' in t or 'ดุษฎีบัณฑิต' in t:
                            deg_lvl = 'ปริญญาเอก'
                        clean_title = re.sub(r'[\r\n\t]+', ' ', t).strip()
                        courses.append({
                            'title_th': clean_title,
                            'faculty_th': fac_name,
                            'degree_level': deg_lvl,
                            'link': url,
                            'university': "King Mongkut's Institute of Technology Ladkrabang",
                            'university_th': 'สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง'
                        })
        except Exception as e:
            print(f"Error fetching KMITL faculty {i}: {e}")

    # Unique
    seen = set()
    unique_kmitl = []
    for c in courses:
        k = (normalize_title(c['title_th']), c['degree_level'])
        if k not in seen:
            seen.add(k)
            unique_kmitl.append(c)
    print(f"Total KMITL unique programs scraped: {len(unique_kmitl)}")
    return unique_kmitl

# 3. Scrape KMUTNB (พระนครเหนือ)
def scrape_kmutnb_all():
    print("=== 🎓 Scraping KMUTNB (มจพ. พระนครเหนือ) Programs ===")
    url = 'https://reg.kmutnb.ac.th/registrar/program_info.asp'
    courses = []
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        r.encoding = 'tis-620'
        soup = BeautifulSoup(r.text, 'html.parser')

        current_deg = 'ปริญญาตรี'
        current_fac = 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ'

        for tr in soup.find_all('tr'):
            txt = tr.get_text(separator=' ', strip=True)
            if 'ระดับการศึกษา' in txt or 'ระดับ' in txt:
                if 'เอก' in txt: current_deg = 'ปริญญาเอก'
                elif 'โท' in txt: current_deg = 'ปริญญาโท'
                elif 'ตรี' in txt: current_deg = 'ปริญญาตรี'
                elif 'ประกาศนียบัตร' in txt: current_deg = 'ประกาศนียบัตร'

            if 'คณะ' in txt and len(txt) < 80:
                current_fac = txt.strip()

            tds = tr.find_all('td')
            if len(tds) >= 2:
                title = tds[1].get_text(strip=True) if len(tds) > 1 else tds[0].get_text(strip=True)
                if len(title) > 3 and not title.isdigit() and 'หลักสูตร' not in title[:6]:
                    courses.append({
                        'title_th': title.strip(),
                        'faculty_th': current_fac,
                        'degree_level': current_deg,
                        'link': url,
                        'university': "King Mongkut's University of Technology North Bangkok",
                        'university_th': 'มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ'
                    })
    except Exception as e:
        print(f"Error fetching KMUTNB: {e}")

    # Fallback to key official curriculum portal
    seen = set()
    unique_kmutnb = []
    for c in courses:
        k = (normalize_title(c['title_th']), c['degree_level'])
        if k not in seen:
            seen.add(k)
            unique_kmutnb.append(c)
    print(f"Total KMUTNB unique programs scraped: {len(unique_kmutnb)}")
    return unique_kmutnb

def enrich_and_insert_3phrajomklao():
    kmutt_raw = scrape_kmutt_all()
    kmitl_raw = scrape_kmitl_all()
    kmutnb_raw = scrape_kmutnb_all()

    with engine.connect() as conn:
        db_kmutt = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university LIKE '%Thonburi%' OR university_th LIKE '%ธนบุรี%'")).fetchall()
        db_kmitl = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university LIKE '%Ladkrabang%' OR university_th LIKE '%ลาดกระบัง%'")).fetchall()
        db_kmutnb = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university LIKE '%North Bangkok%' OR university_th LIKE '%พระนครเหนือ%'")).fetchall()

    existing_kmutt = set(normalize_title(r[0]) for r in db_kmutt)
    existing_kmitl = set(normalize_title(r[0]) for r in db_kmitl)
    existing_kmutnb = set(normalize_title(r[0]) for r in db_kmutnb)

    missing_kmutt = [x for x in kmutt_raw if normalize_title(x['title_th']) not in existing_kmutt]
    missing_kmitl = [x for x in kmitl_raw if normalize_title(x['title_th']) not in existing_kmitl]
    missing_kmutnb = [x for x in kmutnb_raw if normalize_title(x['title_th']) not in existing_kmutnb]

    print(f"\n📊 Summary of Missing Programs to Ingest:")
    print(f"  - KMUTT (มจธ. บางมด) Missing: {len(missing_kmutt)} programs")
    print(f"  - KMITL (สจล. ลาดกระบัง) Missing: {len(missing_kmitl)} programs")
    print(f"  - KMUTNB (มจพ. พระนครเหนือ) Missing: {len(missing_kmutnb)} programs")

    total_to_process = missing_kmutt + missing_kmitl + missing_kmutnb
    if not total_to_process:
        print("✅ 3 King Mongkut Institutes are already completely ingested!")
        return

    print(f"\nTotal programs to enrich via Gemini AI: {len(total_to_process)}")

    batch_size = 15
    batches = [total_to_process[i:i+batch_size] for i in range(0, len(total_to_process), batch_size)]

    def process_batch(batch_idx, batch_items):
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านระบบข้อมูลหลักสูตรมหาวิทยาลัยในประเทศไทย
โปรดแปลงข้อมูลหลักสูตรของกลุ่ม 3 พระจอมเกล้า (KMUTT, KMITL, KMUTNB) ต่อไปนี้ ให้เป็นข้อมูลโครงสร้าง JSON ตาม Schema ที่กำหนด:

รายการหลักสูตร:
{json.dumps(batch_items, ensure_ascii=False, indent=2)}

ข้อกำหนดสำคัญ:
1. `id`: สร้าง unique id สั้นๆ ชัดเจน เช่น `kmutt_cpe_bsc`, `kmitl_robotics_msc`, `kmutnb_me_phd`
2. `title_th`: ใช้ชื่อหลักสูตรภาษาไทยที่ถูกต้อง เป็นทางการ
3. `title_en`: แปลหรือระบุชื่อหลักสูตรภาษาอังกฤษทางการ (e.g. Bachelor of Engineering Program in ...)
4. `degree_level`: ปริญญาตรี / ปริญญาโท / ปริญญาเอก / ประกาศนียบัตร
5. `degree_name`: ชื่อปริญญาและอักษรย่อ เช่น วศ.บ., วท.บ., วศ.ม., ปร.ด.
6. `university` & `university_th`: ระบุชื่อมหาวิทยาลัยให้ตรงกับรายการ
7. `faculty` & `faculty_th`: คณะต้นสังกัดทางการ (เช่น Faculty of Engineering / คณะวิศวกรรมศาสตร์, คณะเทคโนโลยีสารสนเทศ ฯลฯ)
8. `department` & `department_th`: ภาควิชาที่เกี่ยวข้อง
9. `program_type`: ภาคปกติ / ภาคพิเศษ / นานาชาติ
10. `duration_years`: เช่น 4 ปี, 2 ปี, 3 ปี
11. `total_credits`: เช่น 120-140 หน่วยกิต, 36 หน่วยกิต, 48 หน่วยกิต
12. `tuition_per_semester` & `tuition_total`: ประมาณการค่าธรรมเนียมตามอัตราจริง เช่น 20,000 - 45,000 บาท
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
                link = batch_items[j].get('link', 'https://www.kmutt.ac.th') if j < len(batch_items) else 'https://www.kmutt.ac.th'
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
                tuition_per_semester=c.get('tuition_per_semester', '28,000 บาท'),
                tuition_total=c.get('tuition_total', '112,000 บาท'),
                description=c.get('description', ''),
                curriculum_highlights=c.get('curriculum_highlights', []),
                career_paths=c.get('career_paths', []),
                tags=c.get('tags', []),
                website_url=c.get('website_url', 'https://www.kmutt.ac.th'),
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

    print(f"\n🎉 Successfully enriched and inserted {inserted_count} official 3 King Mongkut courses with 768-dim embeddings!")

if __name__ == '__main__':
    enrich_and_insert_3phrajomklao()
