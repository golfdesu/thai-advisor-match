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

FAC_NAME_MAP = {
    'mass_communication': ('คณะการสื่อสารมวลชน', 'Faculty of Mass Communication'),
    'agriculture': ('คณะเกษตรศาสตร์', 'Faculty of Agriculture'),
    'dentistry': ('คณะทันตแพทยศาสตร์', 'Faculty of Dentistry'),
    'associated_medical_sciences': ('คณะเทคนิคการแพทย์', 'Faculty of Associated Medical Sciences'),
    'law': ('คณะนิติศาสตร์', 'Faculty of Law'),
    'business_administration': ('คณะบริหารธุรกิจ', 'Chiang Mai University Business School'),
    'nursing': ('คณะพยาบาลศาสตร์', 'Faculty of Nursing'),
    'medicine': ('คณะแพทยศาสตร์', 'Faculty of Medicine'),
    'pharmacy': ('คณะเภสัชศาสตร์', 'Faculty of Pharmacy'),
    'humanities': ('คณะมนุษยศาสตร์', 'Faculty of Humanities'),
    'political_science_and_public_administration': ('คณะรัฐศาสตร์และรัฐประศาสนศาสตร์', 'Faculty of Political Science and Public Administration'),
    'fine_arts': ('คณะวิจิตรศิลป์', 'Faculty of Fine Arts'),
    'science': ('คณะวิทยาศาสตร์', 'Faculty of Science'),
    'engineering': ('คณะวิศวกรรมศาสตร์', 'Faculty of Engineering'),
    'education': ('คณะศึกษาศาสตร์', 'Faculty of Education'),
    'economics': ('คณะเศรษฐศาสตร์', 'Faculty of Economics'),
    'architecture': ('คณะสถาปัตยกรรมศาสตร์', 'Faculty of Architecture'),
    'social_sciences': ('คณะสังคมศาสตร์', 'Faculty of Social Sciences'),
    'veterinary_medicine': ('คณะสัตวแพทยศาสตร์', 'Faculty of Veterinary Medicine'),
    'public_health': ('คณะสาธารณสุขศาสตร์', 'Faculty of Public Health'),
    'agro_industry': ('คณะอุตสาหกรรมเกษตร', 'Faculty of Agro-Industry'),
    'international_college_and_digital_innovation': ('วิทยาลัยนานาชาตินวัตกรรมดิจิทัล', 'International College of Digital Innovation'),
    'the_graduate_school': ('วิทยาลัยพหุวิทยาการและสหวิทยาการ', 'College of Multidisciplinary and Interdisciplinary Studies'),
    'the_college_of_arts_media_and_technology': ('วิทยาลัยศิลปะ สื่อ และเทคโนโลยี', 'College of Arts, Media and Technology'),
    'school_of_public_policy': ('สถาบันนโยบายสาธารณะ', 'School of Public Policy'),
    'biomedical_engineering_center': ('สถาบันวิศวกรรมชีวการแพทย์', 'Biomedical Engineering Institute')
}

DEGREE_MAPPING = {
    1: 'ปริญญาตรี',
    2: 'ปริญญาโท',
    3: 'ปริญญาเอก',
    4: 'ประกาศนียบัตร'
}

def normalize_title(t):
    if not t: return ''
    t = re.sub(r'^(หลักสูตร|สาขาวิชา)\s*', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'พ\.ศ\.\s*\d+', '', t)
    t = re.sub(r'25\d{2}', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()

def scrape_cmu_all():
    print("=== 🎓 Scraping Official Chiang Mai University Programs ===")
    r_main = requests.get('https://www.cmu.ac.th/th/faculty/course', timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
    soup_main = BeautifulSoup(r_main.content, 'html.parser')

    faculties = []
    for a in soup_main.find_all('a', href=True):
        href = a['href']
        if '/course/head' in href:
            slug = href.split('/')[0] if not href.startswith('/') else href.split('/')[3]
            faculties.append(slug)

    seen_slugs = set()
    unique_slugs = []
    for s in faculties:
        if s not in seen_slugs and s:
            seen_slugs.add(s)
            unique_slugs.append(s)

    all_courses = []
    for slug in unique_slugs:
        url = f'https://www.cmu.ac.th/th/faculty/{slug}/course/head'
        try:
            r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            fac_th, fac_en = FAC_NAME_MAP.get(slug, (slug, slug))

            for tab_idx in range(1, 5):
                pane = soup.find(id=f'tabsNavigationSimple{tab_idx}')
                if not pane:
                    continue
                deg_level = DEGREE_MAPPING[tab_idx]
                for a in pane.find_all('a', href=True):
                    title = a.get_text(separator=' ', strip=True)
                    href = a['href']
                    if not title or 'ขออภัย' in title:
                        continue
                    clean_title = re.sub(r'[\r\n\t]+', ' ', title).strip()
                    all_courses.append({
                        'faculty_th': fac_th,
                        'faculty_en': fac_en,
                        'faculty_slug': slug,
                        'degree_level': deg_level,
                        'title_th': clean_title,
                        'link': href,
                        'university': 'Chiang Mai University',
                        'university_th': 'มหาวิทยาลัยเชียงใหม่'
                    })
        except Exception as e:
            print(f"  Error fetching {slug}: {e}")

    print(f"Scraped {len(all_courses)} total programs from CMU portal.")
    return all_courses

def enrich_and_insert():
    # 1. Scrape all official CMU programs
    cmu_raw = scrape_cmu_all()

    # 2. Get existing courses in DB
    with engine.connect() as conn:
        db_courses = conn.execute(text("SELECT id, title_th, degree_level, faculty_th FROM courses WHERE university_th LIKE '%เชียงใหม่%'")).fetchall()

    existing_keys = set()
    for c in db_courses:
        norm = normalize_title(c[1])
        existing_keys.add(norm)

    # 3. Filter missing
    missing = []
    for it in cmu_raw:
        norm = normalize_title(it['title_th'])
        if norm not in existing_keys:
            missing.append(it)
            existing_keys.add(norm)

    print(f"📊 Identified {len(missing)} brand new CMU courses to enrich and insert.")

    if not missing:
        print("✅ CMU courses are already 100% complete and up-to-date!")
        return

    # Process in batches of 15
    batch_size = 15
    batches = [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]
    print(f"Splitting into {len(batches)} batches for Gemini AI enrichment...")

    def process_batch(batch_idx, batch_items):
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านระบบข้อมูลหลักสูตรมหาวิทยาลัยในประเทศไทย
โปรดแปลงข้อมูลหลักสูตรของ มหาวิทยาลัยเชียงใหม่ (CMU) ต่อไปนี้ ให้เป็นข้อมูลโครงสร้าง JSON ตาม Schema ที่กำหนด:

รายการหลักสูตร:
{json.dumps(batch_items, ensure_ascii=False, indent=2)}

ข้อกำหนดสำคัญ:
1. `id`: สร้าง unique id สั้นๆ ชัดเจน เช่น `cmu_eng_ai_msc`, `cmu_med_nurse_bsc`, `cmu_sci_chem_phd`
2. `title_th`: ใช้ชื่อหลักสูตรภาษาไทยที่ถูกต้อง เป็นทางการ
3. `title_en`: แปลหรือระบุชื่อหลักสูตรภาษาอังกฤษทางการ (e.g. Master of Science Program in ...)
4. `degree_level`: ปริญญาตรี / ปริญญาโท / ปริญญาเอก / ประกาศนียบัตร
5. `degree_name`: ชื่อปริญญาและอักษรย่อ เช่น วท.บ. (วิทยาการข้อมูล), วศ.ม. (วิศวกรรมคอมพิวเตอร์), ปร.ด. (ฟิสิกส์)
6. `university`: Chiang Mai University
7. `university_th`: มหาวิทยาลัยเชียงใหม่
8. `faculty` & `faculty_th`: ตามที่ระบุ
9. `department` & `department_th`: ภาควิชาที่เกี่ยวข้อง
10. `program_type`: ภาคปกติ / ภาคพิเศษ / นานาชาติ
11. `duration_years`: เช่น 4 ปี, 2 ปี, 3 ปี
12. `total_credits`: เช่น 120-140 หน่วยกิต, 36 หน่วยกิต, 48 หน่วยกิต
13. `tuition_per_semester` & `tuition_total`: ประมาณการค่าธรรมเนียมตามอัตราจริงของ มช. เช่น 20,000 - 35,000 บาท
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

    # Run AI Enrichment in parallel
    enriched_courses = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_batch, i, b) for i, b in enumerate(batches)]
        for i, f in enumerate(futures):
            res = f.result()
            print(f"  Enriched batch {i+1}/{len(batches)}: {len(res)} courses")
            # attach original link
            batch_items = batches[i]
            for j, course_obj in enumerate(res):
                link = batch_items[j]['link'] if j < len(batch_items) else 'https://www.cmu.ac.th'
                course_dict = course_obj.model_dump() if hasattr(course_obj, 'model_dump') else dict(course_obj)
                course_dict['website_url'] = link
                enriched_courses.append(course_dict)

    print(f"\n🧠 Generating 768-dim Vector Embeddings for {len(enriched_courses)} new courses...")
    db = SessionLocal()
    inserted_count = 0
    try:
        for idx_c, c in enumerate(enriched_courses):
            # check if ID exists
            base_id = c['id']
            chk = db.query(CourseDB).filter(CourseDB.id == base_id).first()
            if chk:
                base_id = f"{base_id}_{int(time.time()*1000)%100000}"

            # Create embedding text
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
                website_url=c.get('website_url', 'https://www.cmu.ac.th'),
                embedding_text=emb_text,
                embedding=vec
            )
            db.add(new_db)
            inserted_count += 1

            if inserted_count % 10 == 0 or inserted_count == len(enriched_courses):
                db.commit()
                print(f"  Persisted & Indexed: {inserted_count}/{len(enriched_courses)} courses")
    except Exception as e:
        db.rollback()
        print(f"Error during insertion: {e}")
    finally:
        db.close()

    print(f"\n🎉 Successfully enriched and inserted {inserted_count} official CMU courses with 768-dim embeddings!")

if __name__ == '__main__':
    enrich_and_insert()
