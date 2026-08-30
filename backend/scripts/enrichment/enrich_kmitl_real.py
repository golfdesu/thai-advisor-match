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

FAC_KMITL_MAP = {
    'faculty01': ('คณะวิศวกรรมศาสตร์', 'Faculty of Engineering'),
    'faculty02': ('คณะสถาปัตยกรรม ศิลปะและการออกแบบ', 'School of Architecture, Art, and Design'),
    'faculty03': ('คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี', 'Faculty of Industrial Education and Technology'),
    'faculty04': ('คณะเทคโนโลยีการเกษตร', 'Faculty of Agricultural Technology'),
    'faculty05': ('คณะวิทยาศาสตร์', 'Faculty of Science'),
    'faculty06': ('คณะอุตสาหกรรมอาหาร', 'School of Food Industry'),
    'faculty07': ('คณะเทคโนโลยีสารสนเทศ', 'School of Information Technology'),
    'faculty09': ('วิทยาลัยนานาชาติ', 'International College'),
    'faculty10': ('วิทยาลัยเทคโนโลยีและนวัตกรรมวัสดุ', 'College of Materials Innovation and Technology'),
    'faculty11': ('วิทยาลัยนวัตกรรมการผลิตขั้นสูง', 'College of Advanced Manufacturing Innovation'),
    'faculty12': ('คณะบริหารธุรกิจ', 'KBS Business School'),
    'faculty14': ('วิทยาลัยอุตสาหกรรมการบินนานาชาติ', 'International Academy of Aviation Industry'),
    'faculty15': ('คณะศิลปศาสตร์', 'Faculty of Liberal Arts'),
    'faculty16': ('คณะแพทยศาสตร์', 'School of Medicine'),
    'faculty18': ('วิทยาลัยวิศวกรรมสังคีต', 'College of Music Engineering and Art'),
    'faculty19': ('คณะทันตแพทยศาสตร์', 'School of Dentistry'),
    'faculty20': ('วิทยาเขตชุมพรเขตรอุดมศักดิ์', 'Prince of Chumphon Campus')
}

def scrape_kmitl_portal():
    print("=== 🎓 Scraping KMITL (สจล. ลาดกระบัง) from Registrar Portal ===")
    r = requests.get('https://reg.kmitl.ac.th/curriculum/_index.php', timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')

    all_pages = []
    for a in soup.find_all('a', href=True):
        h = a['href']
        if 'faculty' in h and (h.endswith('b.php') or h.endswith('g.php')):
            all_pages.append(f'https://reg.kmitl.ac.th/curriculum/{h}')

    kmitl_courses = []
    for p in all_pages:
        try:
            r_p = requests.get(p, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            soup_p = BeautifulSoup(r_p.content, 'html.parser')

            # get fac key
            fac_slug = p.split('/')[-1].replace('b.php', '').replace('g.php', '')
            fac_th, fac_en = FAC_KMITL_MAP.get(fac_slug, ('สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง', 'KMITL'))

            deg_lvl = 'ปริญญาตรี' if p.endswith('b.php') else 'ปริญญาโท'

            for tr in soup_p.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    txt = tds[0].get_text(strip=True)
                    if any(k in txt for k in ['บัณฑิต', 'มหาบัณฑิต', 'ดุษฎีบัณฑิต']):
                        if 'ดุษฎีบัณฑิต' in txt or 'ปร.ด.' in txt or 'วศ.ด.' in txt:
                            deg_lvl_item = 'ปริญญาเอก'
                        elif 'มหาบัณฑิต' in txt or 'วท.ม.' in txt or 'วศ.ม.' in txt:
                            deg_lvl_item = 'ปริญญาโท'
                        else:
                            deg_lvl_item = deg_lvl

                        clean_title = re.sub(r'\s+', ' ', txt).strip()
                        if len(clean_title) > 5 and len(clean_title) < 120 and 'ปีหลักสูตร' not in clean_title:
                            kmitl_courses.append({
                                'title_th': clean_title,
                                'faculty_th': fac_th,
                                'faculty_en': fac_en,
                                'degree_level': deg_lvl_item,
                                'link': p,
                                'university': "King Mongkut's Institute of Technology Ladkrabang",
                                'university_th': 'สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง'
                            })
        except Exception as e:
            print(f"Err {p}: {e}")

    # Deduplicate
    seen = set()
    unique_kmitl = []
    for c in kmitl_courses:
        k = (normalize_title(c['title_th']), c['degree_level'])
        if k not in seen:
            seen.add(k)
            unique_kmitl.append(c)

    print(f"Extracted {len(unique_kmitl)} unique KMITL curricula from official registry.")
    return unique_kmitl

def enrich_and_insert_kmitl():
    kmitl_raw = scrape_kmitl_portal()

    with engine.connect() as conn:
        db_kmitl = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university LIKE '%Ladkrabang%' OR university_th LIKE '%ลาดกระบัง%'")).fetchall()

    existing_kmitl = set(normalize_title(r[0]) for r in db_kmitl)
    missing = [x for x in kmitl_raw if normalize_title(x['title_th']) not in existing_kmitl]

    print(f"📊 Identified {len(missing)} brand new KMITL courses to ingest.")
    if not missing:
        print("✅ KMITL is already 100% complete!")
        return

    batch_size = 15
    batches = [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]

    def process_batch(batch_idx, batch_items):
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านระบบข้อมูลหลักสูตรมหาวิทยาลัยในประเทศไทย
โปรดแปลงข้อมูลหลักสูตรของ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง (KMITL) ต่อไปนี้ ให้เป็นข้อมูลโครงสร้าง JSON ตาม Schema ที่กำหนด:

รายการหลักสูตร:
{json.dumps(batch_items, ensure_ascii=False, indent=2)}

ข้อกำหนดสำคัญ:
1. `id`: สร้าง unique id สั้นๆ ชัดเจน เช่น `kmitl_eng_cpe_bsc`, `kmitl_arch_msc`, `kmitl_it_phd`
2. `title_th`: ใช้ชื่อหลักสูตรภาษาไทยที่ถูกต้อง เป็นทางการ
3. `title_en`: แปลหรือระบุชื่อหลักสูตรภาษาอังกฤษทางการ
4. `degree_level`: ปริญญาตรี / ปริญญาโท / ปริญญาเอก / ประกาศนียบัตร
5. `degree_name`: ชื่อปริญญาและอักษรย่อ เช่น วศ.บ., วท.บ., สถ.บ., วศ.ม., ปร.ด.
6. `university`: King Mongkut's Institute of Technology Ladkrabang
7. `university_th`: สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง
8. `faculty` & `faculty_th`: ตามที่ระบุ
9. `department` & `department_th`: ภาควิชาที่เกี่ยวข้อง
10. `program_type`: ภาคปกติ / ภาคพิเศษ / นานาชาติ
11. `duration_years`: เช่น 4 ปี, 2 ปี, 3 ปี
12. `total_credits`: เช่น 120-140 หน่วยกิต, 36 หน่วยกิต, 48 หน่วยกิต
13. `tuition_per_semester` & `tuition_total`: ประมาณการค่าธรรมเนียมตามอัตราจริง เช่น 22,000 - 45,000 บาท
14. `description`: คำอธิบายจุดเด่นหลักสูตร วัตถุประสงค์ และการเรียนการสอน (ภาษาไทย 2-3 ประโยค)
15. `curriculum_highlights`: รายการวิชาเด่นหรือทักษะที่ได้ 3-4 ข้อ
16. `career_paths`: สายอาชีพที่รองรับ 3-4 อาชีพ
17. `tags`: คำสำคัญที่เกี่ยวข้อง
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
                link = batch_items[j].get('link', 'https://curriculum.kmitl.ac.th') if j < len(batch_items) else 'https://curriculum.kmitl.ac.th'
                course_dict = course_obj.model_dump() if hasattr(course_obj, 'model_dump') else dict(course_obj)
                course_dict['website_url'] = link
                enriched_courses.append(course_dict)

    print(f"\n🧠 Generating 768-dim Vector Embeddings for {len(enriched_courses)} new courses...")
    db = SessionLocal()
    inserted_count = 0
    try:
        for idx_c, c in enumerate(enriched_courses):
            base_id = c['id']
            # generate uniquely safe ID
            safe_id = f"{base_id}_{int(time.time()*1000)%100000}_{idx_c}"

            emb_text = f"{c['title_th']} {c.get('title_en','')} {c['university_th']} {c['faculty_th']} {c.get('department_th','')} {c.get('description','')} {' '.join(c.get('career_paths',[]))} {' '.join(c.get('curriculum_highlights',[]))}"
            vec = embedding_service.get_embedding(emb_text)

            new_db = CourseDB(
                id=safe_id,
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
                website_url=c.get('website_url', 'https://curriculum.kmitl.ac.th'),
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

    print(f"\n🎉 Successfully enriched and inserted {inserted_count} official KMITL courses with 768-dim embeddings!")

if __name__ == '__main__':
    enrich_and_insert_kmitl()
