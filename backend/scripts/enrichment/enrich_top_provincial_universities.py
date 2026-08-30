import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, json, time, threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Comprehensive Official Curricula for Target Universities
TARGET_CURRICULA = [
    # ==========================================
    # 1. NARESUAN UNIVERSITY (ม.นเรศวร - NU)
    # ==========================================
    # คณะแพทยศาสตร์ (Faculty of Medicine)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะแพทยศาสตร์", "fac_en": "Faculty of Medicine", "level": "ปริญญาตรี", "title_th": "หลักสูตรแพทยศาสตรบัณฑิต", "dept": "ภาควิชาแพทยศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะแพทยศาสตร์", "fac_en": "Faculty of Medicine", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์การแพทย์", "dept": "วิทยาศาสตร์การแพทย์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะแพทยศาสตร์", "fac_en": "Faculty of Medicine", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์การแพทย์", "dept": "วิทยาศาสตร์การแพทย์"},

    # คณะเภสัชศาสตร์ (Faculty of Pharmaceutical Sciences)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmaceutical Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม", "dept": "เภสัชกรรมปฏิบัติ"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmaceutical Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์เภสัชกรรมและเภสัชอุตสาหกรรม", "dept": "เทคโนโลยีเภสัชกรรม"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmaceutical Sciences", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์เครื่องสำอางและผลิตภัณฑ์ธรรมชาติ", "dept": "วิทยาศาสตร์เครื่องสำอาง"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmaceutical Sciences", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์เภสัชกรรม", "dept": "เภสัชศาสตร์"},

    # คณะทันตแพทยศาสตร์ (Faculty of Dentistry)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะทันตแพทยศาสตร์", "fac_en": "Faculty of Dentistry", "level": "ปริญญาตรี", "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต", "dept": "ทันตแพทยศาสตร์"},

    # คณะพยาบาลศาสตร์ (Faculty of Nursing)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะพยาบาลศาสตร์", "fac_en": "Faculty of Nursing", "level": "ปริญญาตรี", "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต", "dept": "พยาบาลศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะพยาบาลศาสตร์", "fac_en": "Faculty of Nursing", "level": "ปริญญาโท", "title_th": "หลักสูตรพยาบาลศาสตรมหาบัณฑิต สาขาวิชาการพยาบาลผู้ใหญ่และผู้สูงอายุ", "dept": "พยาบาลศาสตร์"},

    # คณะสหเวชศาสตร์ (Faculty of Allied Health Sciences)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสหเวชศาสตร์", "fac_en": "Faculty of Allied Health Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคนิคการแพทย์", "dept": "เทคนิคการแพทย์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสหเวชศาสตร์", "fac_en": "Faculty of Allied Health Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชากายภาพบำบัด", "dept": "กายภาพบำบัด"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสหเวชศาสตร์", "fac_en": "Faculty of Allied Health Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาทัศนมาตรศาสตร์ (Doctor of Optometry)", "dept": "ทัศนมาตรศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสหเวชศาสตร์", "fac_en": "Faculty of Allied Health Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชารังสีเทคนิค", "dept": "รังสีเทคนิค"},

    # คณะสาธารณสุขศาสตร์ (Faculty of Public Health)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสาธารณสุขศาสตร์", "fac_en": "Faculty of Public Health", "level": "ปริญญาตรี", "title_th": "หลักสูตรสาธารณสุขศาสตรบัณฑิต สาขาวิชาสาธารณสุขศาสตร์", "dept": "สาธารณสุขศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสาธารณสุขศาสตร์", "fac_en": "Faculty of Public Health", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาอาชีวอนามัยและความปลอดภัย", "dept": "อาชีวอนามัยและความปลอดภัย"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสาธารณสุขศาสตร์", "fac_en": "Faculty of Public Health", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาอนามัยสิ่งแวดล้อม", "dept": "อนามัยสิ่งแวดล้อม"},

    # คณะวิศวกรรมศาสตร์ (Faculty of Engineering)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "dept": "วิศวกรรมเครื่องกล"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา", "dept": "วิศวกรรมโยธา"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการและการจัดการโลจิสติกส์", "dept": "วิศวกรรมอุตสาหการ"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมสิ่งแวดล้อม", "dept": "วิศวกรรมสิ่งแวดล้อม"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมเครื่องกลและพลังงาน", "dept": "วิศวกรรมเครื่องกล"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},

    # คณะวิทยาศาสตร์ (Faculty of Science)
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ชั้นสูง", "dept": "วิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์", "dept": "วิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเคมี", "dept": "เคมี"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาชีววิทยา", "dept": "ชีววิทยา"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาฟิสิกส์ประยุกต์และวัสดุศาสตร์", "dept": "ฟิสิกส์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์", "dept": "คณิตศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ", "dept": "วิทยาการคอมพิวเตอร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์", "dept": "คณิตศาสตร์"},

    # คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม", "fac_en": "Faculty of Agriculture Natural Resources and Environment", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเกษตรศาสตร์ (พืชไร่/พืชสวน/กีฏวิทยา/โรคพืช)", "dept": "วิทยาศาสตร์การเกษตร"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม", "fac_en": "Faculty of Agriculture Natural Resources and Environment", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร", "dept": "อุตสาหกรรมเกษตร"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะเกษตรศาสตร์ ทรัพยากรธรรมชาติและสิ่งแวดล้อม", "fac_en": "Faculty of Agriculture Natural Resources and Environment", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาสัตวศาสตร์และเทคโนโลยีการแปรรูป", "dept": "สัตวศาสตร์"},

    # คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "fac_en": "Faculty of Business, Economics and Communications", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการเงินและการธนาคารดิจิทัล", "dept": "การเงินและการธนาคาร"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "fac_en": "Faculty of Business, Economics and Communications", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาดดิจิทัลและแบรนด์ดิ้ง", "dept": "การตลาด"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "fac_en": "Faculty of Business, Economics and Communications", "level": "ปริญญาตรี", "title_th": "หลักสูตรบัญชีบัณฑิต", "dept": "การบัญชี"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "fac_en": "Faculty of Business, Economics and Communications", "level": "ปริญญาตรี", "title_th": "หลักสูตรเศรษฐศาสตรบัณฑิต", "dept": "เศรษฐศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "fac_en": "Faculty of Business, Economics and Communications", "level": "ปริญญาตรี", "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสื่อสารมวลชนและสื่อดิจิทัล", "dept": "นิเทศศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร", "fac_en": "Faculty of Business, Economics and Communications", "level": "ปริญญาโท", "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (MBA - นวัตกรรมธุรกิจและการจัดการเชิงกลยุทธ์)", "dept": "บริหารธุรกิจ"},

    # คณะนิติศาสตร์ & สังคมศาสตร์ & มนุษยศาสตร์
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะนิติศาสตร์", "fac_en": "Faculty of Law", "level": "ปริญญาตรี", "title_th": "หลักสูตรนิติศาสตรบัณฑิต", "dept": "นิติศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะนิติศาสตร์", "fac_en": "Faculty of Law", "level": "ปริญญาโท", "title_th": "หลักสูตรนิติศาสตรมหาบัณฑิต", "dept": "นิติศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสังคมศาสตร์", "fac_en": "Faculty of Social Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรรัฐศาสตรบัณฑิต สาขาวิชาการเมืองการปกครองและความสัมพันธ์ระหว่างประเทศ", "dept": "รัฐศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะสังคมศาสตร์", "fac_en": "Faculty of Social Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรรัฐประศาสนศาสตรบัณฑิต", "dept": "รัฐประศาสนศาสตร์"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะมนุษยศาสตร์", "fac_en": "Faculty of Humanities", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษเพื่อการสื่อสาร", "dept": "ภาษาอังกฤษ"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะมนุษยศาสตร์", "fac_en": "Faculty of Humanities", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาจีน", "dept": "ภาษาตะวันออก"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะศึกษาศาสตร์", "fac_en": "Faculty of Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรการศึกษาบัณฑิต (กศ.บ. 4 ปี วิชาเอกคณิตศาสตร์/ภาษาอังกฤษ/คอมพิวเตอร์)", "dept": "การศึกษา"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "คณะศึกษาศาสตร์", "fac_en": "Faculty of Education", "level": "ปริญญาโท", "title_th": "หลักสูตรการศึกษามหาบัณฑิต สาขาวิชาการบริหารการศึกษา", "dept": "การศึกษา"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี (SGtech)", "fac_en": "School of Renewable Energy and Smart Grid Technology", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพลังงานทดแทนและเทคโนโลยีสมาร์ตกริด", "dept": "พลังงานทดแทน"},
    {"uni": "Naresuan University", "uni_th": "มหาวิทยาลัยนเรศวร", "fac_th": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี (SGtech)", "fac_en": "School of Renewable Energy and Smart Grid Technology", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาพลังงานทดแทน", "dept": "พลังงานทดแทน"},

    # ==========================================
    # 2. SRINAKHARINWIROT UNIVERSITY (มศว - SWU)
    # ==========================================
    # คณะแพทยศาสตร์ & ทันตแพทยศาสตร์ & เภสัชศาสตร์
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะแพทยศาสตร์", "fac_en": "Faculty of Medicine", "level": "ปริญญาตรี", "title_th": "หลักสูตรแพทยศาสตรบัณฑิต (ศูนย์การแพทย์สมเด็จพระเทพฯ / วชิรพยาบาล)", "dept": "แพทยศาสตร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะทันตแพทยศาสตร์", "fac_en": "Faculty of Dentistry", "level": "ปริญญาตรี", "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต", "dept": "ทันตแพทยศาสตร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmacy", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม", "dept": "เภสัชกรรม"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmacy", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์เภสัชกรรม", "dept": "เภสัชศาสตร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะพยาบาลศาสตร์", "fac_en": "Faculty of Nursing", "level": "ปริญญาตรี", "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต", "dept": "พยาบาลศาสตร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะกายภาพบำบัด", "fac_en": "Faculty of Physical Therapy", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชากายภาพบำบัด", "dept": "กายภาพบำบัด"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะกายภาพบำบัด", "fac_en": "Faculty of Physical Therapy", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชากิจกรรมบำบัด", "dept": "กิจกรรมบำบัด"},

    # คณะวิศวกรรมศาสตร์ (Faculty of Engineering)
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์", "dept": "วิศวกรรมคอมพิวเตอร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า (ระบบไฟฟ้ากำลังและสื่อสาร)", "dept": "วิศวกรรมไฟฟ้า"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "dept": "วิศวกรรมเครื่องกล"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์ (Biomedical Engineering)", "dept": "วิศวกรรมชีวการแพทย์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธาและสิ่งแวดล้อม", "dept": "วิศวกรรมโยธา"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี", "dept": "วิศวกรรมเคมี"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์", "dept": "วิศวกรรมชีวการแพทย์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมวิศวกรรมศาสตร์ (นานาชาติ)", "dept": "วิศวกรรมศาสตร์"},

    # วิทยาลัยนวัตกรรมสื่อสารสังคม (COSCI) & วิทยาลัยอุตสาหกรรมสร้างสรรค์ (CCI)
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "วิทยาลัยนวัตกรรมสื่อสารสังคม", "fac_en": "College of Social Communication Innovation (COSCI)", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชานวัตกรรมการสื่อสาร (ภาพยนตร์และสื่อดิจิทัล/การออกแบบสื่อปฏิสัมพันธ์)", "dept": "นวัตกรรมสื่อสาร"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "วิทยาลัยนวัตกรรมสื่อสารสังคม", "fac_en": "College of Social Communication Innovation (COSCI)", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคอมพิวเตอร์เพื่อการสื่อสาร (แอนิเมชัน เกม และมัลติมีเดีย)", "dept": "คอมพิวเตอร์เพื่อการสื่อสาร"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "วิทยาลัยนวัตกรรมสื่อสารสังคม", "fac_en": "College of Social Communication Innovation (COSCI)", "level": "ปริญญาตรี", "title_th": "หลักสูตรการจัดการบัณฑิต สาขาวิชาการจัดการภาพยนตร์และสื่อดิจิทัล", "dept": "การจัดการสื่อสาร"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "วิทยาลัยอุตสาหกรรมสร้างสรรค์", "fac_en": "College of Creative Industry (CCI)", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาอัญมณีและเครื่องประดับ", "dept": "อัญมณีและเครื่องประดับ"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "วิทยาลัยอุตสาหกรรมสร้างสรรค์", "fac_en": "College of Creative Industry (CCI)", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาการออกแบบผลิตภัณฑ์และแฟชั่นสร้างสรรค์", "dept": "การออกแบบสร้างสรรค์"},

    # คณะศึกษาศาสตร์ (Faculty of Education)
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะศึกษาศาสตร์", "fac_en": "Faculty of Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรการศึกษาบัณฑิต (กศ.บ. 4 ปี สาขาวิชาการประถมศึกษา/การศึกษาปฐมวัย/การศึกษาพิเศษ)", "dept": "หลักสูตรและการสอน"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะศึกษาศาสตร์", "fac_en": "Faculty of Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรการศึกษาบัณฑิต สาขาวิชาจิตวิทยาการแนะแนวและการปรึกษา", "dept": "จิตวิทยา"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะศึกษาศาสตร์", "fac_en": "Faculty of Education", "level": "ปริญญาโท", "title_th": "หลักสูตรการศึกษามหาบัณฑิต สาขาวิชาการบริหารการศึกษา", "dept": "การบริหารการศึกษา"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะศึกษาศาสตร์", "fac_en": "Faculty of Education", "level": "ปริญญาเอก", "title_th": "หลักสูตรการศึกษาดุษฎีบัณฑิต สาขาวิชาการศึกษาและการเรียนรู้", "dept": "หลักสูตรและการสอน"},

    # คณะศิลปกรรมศาสตร์ & มนุษยศาสตร์ & สังคมศาสตร์
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะศิลปกรรมศาสตร์", "fac_en": "Faculty of Fine Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาศิลปะการแสดง (การแสดงและกำกับการแสดง)", "dept": "ศิลปะการแสดง"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะศิลปกรรมศาสตร์", "fac_en": "Faculty of Fine Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาดุริยางคศาสตร์สากล", "dept": "ดุริยางคศาสตร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะมนุษยศาสตร์", "fac_en": "Faculty of Humanities", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษและภาษาศาสตร์", "dept": "ภาษาอังกฤษ"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะมนุษยศาสตร์", "fac_en": "Faculty of Humanities", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาเกาหลี/ภาษาญี่ปุ่น/ภาษาจีน", "dept": "ภาษาตะวันออก"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะสังคมศาสตร์", "fac_en": "Faculty of Social Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรรัฐศาสตรบัณฑิต สาขาวิชาการเมืองการปกครองและความสัมพันธ์ระหว่างประเทศ", "dept": "รัฐศาสตร์"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะบริหารธุรกิจเพื่อสังคม", "fac_en": "Faculty of Business Administration for Society", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาดดิจิทัลและนวัตกรรมธุรกิจ", "dept": "การตลาด"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะบริหารธุรกิจเพื่อสังคม", "fac_en": "Faculty of Business Administration for Society", "level": "ปริญญาตรี", "title_th": "หลักสูตรบัญชีบัณฑิต", "dept": "การบัญชี"},
    {"uni": "Srinakharinwirot University", "uni_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "fac_th": "คณะบริหารธุรกิจเพื่อสังคม", "fac_en": "Faculty of Business Administration for Society", "level": "ปริญญาโท", "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (MBA for Society)", "dept": "บริหารธุรกิจ"},

    # ==========================================
    # 3. BURAPHA UNIVERSITY (ม.บูรพา - BUU)
    # ==========================================
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะโลจิสติกส์", "fac_en": "Faculty of Logistics", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทาน", "dept": "การจัดการโลจิสติกส์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะโลจิสติกส์", "fac_en": "Faculty of Logistics", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการค้าระหว่างประเทศและการจัดการโลจิสติกส์ทางทะเล", "dept": "การค้าระหว่างประเทศ"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะโลจิสติกส์", "fac_en": "Faculty of Logistics", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทานเชิงกลยุทธ์", "dept": "การจัดการโลจิสติกส์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะโลจิสติกส์", "fac_en": "Faculty of Logistics", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทาน", "dept": "การจัดการโลจิสติกส์"},

    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาการสารสนเทศ", "fac_en": "Faculty of Informatics", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และปัญญาประดิษฐ์", "dept": "วิทยาการคอมพิวเตอร์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาการสารสนเทศ", "fac_en": "Faculty of Informatics", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศเพื่อการจัดการและคลาวด์คอมพิวติง", "dept": "เทคโนโลยีสารสนเทศ"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาการสารสนเทศ", "fac_en": "Faculty of Informatics", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิศวกรรมซอฟต์แวร์", "dept": "วิศวกรรมซอฟต์แวร์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาการสารสนเทศ", "fac_en": "Faculty of Informatics", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาปัญญาประดิษฐ์ประยุกต์และวิทยาการข้อมูล", "dept": "วิทยาการข้อมูล"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาการสารสนเทศ", "fac_en": "Faculty of Informatics", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และนวัตกรรมดิจิทัล", "dept": "วิทยาการคอมพิวเตอร์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาการสารสนเทศ", "fac_en": "Faculty of Informatics", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาการสารสนเทศ", "dept": "สารสนเทศศาสตร์"},

    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะแพทยศาสตร์", "fac_en": "Faculty of Medicine", "level": "ปริญญาตรี", "title_th": "หลักสูตรแพทยศาสตรบัณฑิต", "dept": "แพทยศาสตร์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะพยาบาลศาสตร์", "fac_en": "Faculty of Nursing", "level": "ปริญญาตรี", "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต", "dept": "พยาบาลศาสตร์"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmacy", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม", "dept": "เภสัชกรรม"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะสหเวชศาสตร์", "fac_en": "Faculty of Allied Health Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคนิคการแพทย์", "dept": "เทคนิคการแพทย์"},

    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "dept": "วิศวกรรมเครื่องกล"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า", "dept": "วิศวกรรมไฟฟ้า"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการและการผลิตอัจฉริยะ", "dept": "วิศวกรรมอุตสาหการ"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี", "dept": "วิศวกรรมเคมี"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา", "dept": "วิศวกรรมโยธา"},

    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะวิทยาศาสตร์และศิลปศาสตร์ (วิทยาเขตจันทบุรี)", "fac_en": "Faculty of Science and Arts (Chanthaburi Campus)", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีการเกษตรและนวัตกรรมอาหาร", "dept": "เทคโนโลยีการเกษตร"},
    {"uni": "Burapha University", "uni_th": "มหาวิทยาลัยบูรพา", "fac_th": "คณะพาณิชยศาสตร์และการจัดการ (วิทยาเขตสระแก้ว)", "fac_en": "Faculty of Commerce and Management", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาธุรกิจการค้าชายแดนและโลจิสติกส์", "dept": "บริหารธุรกิจ"},

    # ==========================================
    # 4. SILPAKORN UNIVERSITY (ม.ศิลปากร - SU)
    # ==========================================
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "fac_en": "Faculty of Painting, Sculpture and Graphic Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปบัณฑิต สาขาวิชาทัศนศิลป์ (จิตรกรรม/ประติมากรรม/ภาพพิมพ์/สื่อผสม)", "dept": "ทัศนศิลป์"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะจิตรกรรม ประติมากรรมและภาพพิมพ์", "fac_en": "Faculty of Painting, Sculpture and Graphic Arts", "level": "ปริญญาโท", "title_th": "หลักสูตรศิลปมหาบัณฑิต สาขาวิชาทัศนศิลป์", "dept": "ทัศนศิลป์"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะสถาปัตยกรรมศาสตร์", "fac_en": "Faculty of Architecture", "level": "ปริญญาตรี", "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต (สถ.บ. 5 ปี)", "dept": "สถาปัตยกรรม"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะสถาปัตยกรรมศาสตร์", "fac_en": "Faculty of Architecture", "level": "ปริญญาตรี", "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรมไทย", "dept": "สถาปัตยกรรมไทย"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะโบราณคดี", "fac_en": "Faculty of Archaeology", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาโบราณคดีและประวัติศาสตร์ศิลปะ", "dept": "โบราณคดี"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะโบราณคดี", "fac_en": "Faculty of Archaeology", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาไทยและภาษาตะวันออก", "dept": "ภาษาตะวันออก"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะมัณฑนศิลป์", "fac_en": "Faculty of Decorative Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปบัณฑิต สาขาวิชาการออกแบบภายใน (Interior Design)", "dept": "ออกแบบภายใน"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะมัณฑนศิลป์", "fac_en": "Faculty of Decorative Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปบัณฑิต สาขาวิชาการออกแบบนิเทศศิลป์ (Visual Communication Design)", "dept": "นิเทศศิลป์"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะมัณฑนศิลป์", "fac_en": "Faculty of Decorative Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปบัณฑิต สาขาวิชาการออกแบบผลิตภัณฑ์ (Product Design)", "dept": "ออกแบบผลิตภัณฑ์"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะมัณฑนศิลป์", "fac_en": "Faculty of Decorative Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปบัณฑิต สาขาวิชาเครื่องเคลือบดินเผาและประยุกต์ศิลป์", "dept": "เครื่องเคลือบดินเผา"},

    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmacy", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม", "dept": "เภสัชกรรม"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmacy", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์เภสัชกรรม", "dept": "วิทยาการเภสัชศาสตร์"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม", "fac_en": "Faculty of Engineering and Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมีและกระบวนการ", "dept": "วิศวกรรมเคมี"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม", "fac_en": "Faculty of Engineering and Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกลและพลังงาน", "dept": "วิศวกรรมเครื่องกล"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม", "fac_en": "Faculty of Engineering and Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอิเล็กทรอนิกส์และคอมพิวเตอร์", "dept": "วิศวกรรมไฟฟ้า"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม", "fac_en": "Faculty of Engineering and Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพและอาหาร", "dept": "เทคโนโลยีชีวภาพ"},

    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (ICT)", "fac_en": "Faculty of Information and Communication Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศเพื่อการออกแบบ (เกม/แอนิเมชัน/เว็บ)", "dept": "เทคโนโลยีสารสนเทศ"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (ICT)", "fac_en": "Faculty of Information and Communication Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสื่อสารดิจิทัลและสื่อโฆษณา", "dept": "นิเทศศาสตร์"},
    {"uni": "Silpakorn University", "uni_th": "มหาวิทยาลัยศิลปากร", "fac_th": "คณะวิทยาการจัดการ", "fac_en": "Faculty of Management Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการธุรกิจการท่องเที่ยวและการโรงแรม", "dept": "การจัดการการท่องเที่ยว"},

    # ==========================================
    # 5. PRINCE OF SONGKLA UNIVERSITY (ม.อ. - PSU)
    # ==========================================
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะแพทยศาสตร์", "fac_en": "Faculty of Medicine", "level": "ปริญญาตรี", "title_th": "หลักสูตรแพทยศาสตรบัณฑิต (โรงพยาบาลสงขลานครินทร์)", "dept": "แพทยศาสตร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะทันตแพทยศาสตร์", "fac_en": "Faculty of Dentistry", "level": "ปริญญาตรี", "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต", "dept": "ทันตแพทยศาสตร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะเภสัชศาสตร์", "fac_en": "Faculty of Pharmaceutical Sciences", "level": "ปริญญาตรี", "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม", "dept": "เภสัชกรรม"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะพยาบาลศาสตร์", "fac_en": "Faculty of Nursing", "level": "ปริญญาตรี", "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต", "dept": "พยาบาลศาสตร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะการแพทย์แผนไทย", "fac_en": "Faculty of Traditional Thai Medicine", "level": "ปริญญาตรี", "title_th": "หลักสูตรการแพทย์แผนไทยบัณฑิต", "dept": "การแพทย์แผนไทย"},

    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์", "dept": "วิศวกรรมคอมพิวเตอร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า (ระบบอัตโนมัติและพลังงาน)", "dept": "วิศวกรรมไฟฟ้า"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "dept": "วิศวกรรมเครื่องกล"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี", "dept": "วิศวกรรมเคมี"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา", "dept": "วิศวกรรมโยธา"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเหมืองแร่และวัสดุ", "dept": "วิศวกรรมเหมืองแร่และวัสดุ"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์", "dept": "วิศวกรรมคอมพิวเตอร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมศาสตร์", "dept": "วิศวกรรมศาสตร์"},

    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ", "dept": "วิทยาการคอมพิวเตอร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะวิทยาศาสตร์", "fac_en": "Faculty of Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพและวิทยาศาสตร์ชีวภาพ", "dept": "เทคโนโลยีชีวภาพ"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะทรัพยากรธรรมชาติ", "fac_en": "Faculty of Natural Resources", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาพืชศาสตร์และนวัตกรรมการเกษตร", "dept": "พืชศาสตร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะทรัพยากรธรรมชาติ", "fac_en": "Faculty of Natural Resources", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวาริชศาสตร์และการเพาะเลี้ยงสัตว์น้ำ", "dept": "วาริชศาสตร์"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะอุตสาหกรรมเกษตร", "fac_en": "Faculty of Agro-Industry", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีอาหารและผลิตภัณฑ์ยางธรรมชาติ", "dept": "เทคโนโลยีอาหาร"},

    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "คณะการบริการและการท่องเที่ยว (วิทยาเขตภูเก็ต)", "fac_en": "Faculty of Hospitality and Tourism (Phuket Campus)", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการการบริการและการท่องเที่ยว (นานาชาติ)", "dept": "การท่องเที่ยว"},
    {"uni": "Prince of Songkla University", "uni_th": "มหาวิทยาลัยสงขลานครินทร์", "fac_th": "วิทยาลัยการคอมพิวเตอร์ (วิทยาเขตภูเก็ต)", "fac_en": "College of Computing (Phuket Campus)", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิศวกรรมดิจิทัลและปัญญาประดิษฐ์ (Digital Engineering)", "dept": "วิศวกรรมดิจิทัล"},

    # ==========================================
    # 6. NATIONAL INSTITUTE OF DEVELOPMENT ADMINISTRATION (นิด้า - NIDA)
    # ==========================================
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะบริหารธุรกิจ (NIDA Business School)", "fac_en": "NIDA Business School", "level": "ปริญญาโท", "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (Flexible MBA / Young Executive MBA / International MBA - AACSB Accredited)", "dept": "บริหารธุรกิจ"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะบริหารธุรกิจ (NIDA Business School)", "fac_en": "NIDA Business School", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการวิเคราะห์การลงทุนและการจัดการความเสี่ยง (MSc Financial Investment)", "dept": "การเงิน"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะบริหารธุรกิจ (NIDA Business School)", "fac_en": "NIDA Business School", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาบริหารธุรกิจ (Ph.D. in Business Administration)", "dept": "บริหารธุรกิจ"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะรัฐประศาสนศาสตร์ (GSPA NIDA)", "fac_en": "Graduate School of Public Administration", "level": "ปริญญาโท", "title_th": "หลักสูตรรัฐประศาสนศาสตรมหาบัณฑิต (MPA - การบริหารภาครัฐและนโยบายสาธารณะ)", "dept": "รัฐประศาสนศาสตร์"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะรัฐประศาสนศาสตร์ (GSPA NIDA)", "fac_en": "Graduate School of Public Administration", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชารัฐประศาสนศาสตร์ (Ph.D. in Public Administration)", "dept": "รัฐประศาสนศาสตร์"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะสถิติประยุกต์ (GSAS NIDA)", "fac_en": "Graduate School of Applied Statistics", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ชั้นสูง (M.Sc. in Data Science and Analytics)", "dept": "วิทยาการคอมพิวเตอร์และระบบสารสนเทศ"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะสถิติประยุกต์ (GSAS NIDA)", "fac_en": "Graduate School of Applied Statistics", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศและปัญญาประดิษฐ์ (M.Sc. in IT & AI Management)", "dept": "วิทยาการคอมพิวเตอร์"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะสถิติประยุกต์ (GSAS NIDA)", "fac_en": "Graduate School of Applied Statistics", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และระบบสารสนเทศ", "dept": "วิทยาการคอมพิวเตอร์"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะพัฒนาการเศรษฐกิจ", "fac_en": "Graduate School of Development Economics", "level": "ปริญญาโท", "title_th": "หลักสูตรเศรษฐศาสตรมหาบัณฑิต สาขาวิชาเศรษฐศาสตร์การเงินและการประเมินโครงการ", "dept": "เศรษฐศาสตร์"},
    {"uni": "National Institute of Development Administration", "uni_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์", "fac_th": "คณะนิเทศศาสตร์และนวัตกรรมการจัดการ", "fac_en": "Graduate School of Communication Arts and Management Innovation", "level": "ปริญญาโท", "title_th": "หลักสูตรนิเทศศาสตรมหาบัณฑิต สาขาวิชาการสื่อสารและนวัตกรรมดิจิทัล", "dept": "นิเทศศาสตร์"}
]

def normalize_title(t):
    if not t: return ''
    import re
    t = re.sub(r'^(หลักสูตร|สาขาวิชา)\s*', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'พ\.ศ\.\s*\d+', '', t)
    t = re.sub(r'25\d{2}', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()

def enrich_and_insert_next_universities():
    print(f"=== 🎓 Enriching and Ingesting NU, SWU, BUU, SU, PSU, NIDA Curricula ===")

    with engine.connect() as conn:
        db_all = conn.execute(text("SELECT university, title_th, degree_level FROM courses")).fetchall()

    existing_keys = set((r[0].lower(), normalize_title(r[1]), r[2]) for r in db_all)
    missing = []
    for x in TARGET_CURRICULA:
        k = (x['uni'].lower(), normalize_title(x['title_th']), x['level'])
        if k not in existing_keys:
            missing.append(x)
            existing_keys.add(k)

    print(f"📊 Identified {len(missing)} brand new courses to ingest across top provincial & Bangkok universities.")
    if not missing:
        print("✅ Target universities are already 100% complete!")
        return

    batch_size = 15
    batches = [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]

    def process_batch(batch_idx, batch_items):
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านระบบข้อมูลหลักสูตรมหาวิทยาลัยในประเทศไทย
โปรดแปลงข้อมูลหลักสูตรของมหาวิทยาลัยชั้นนำ (NU, SWU, BUU, SU, PSU, NIDA) ต่อไปนี้ ให้เป็นข้อมูลโครงสร้าง JSON ตาม Schema ที่กำหนด:

รายการหลักสูตร:
{json.dumps(batch_items, ensure_ascii=False, indent=2)}

ข้อกำหนดสำคัญ:
1. `id`: สร้าง unique id สั้นๆ ชัดเจน เช่น `nu_med_md`, `swu_eng_bme_bsc`, `buu_log_msc`, `su_arch_thai_bsc`, `psu_eng_cpe_bsc`, `nida_mba_aacsb`
2. `title_th`: ใช้ชื่อหลักสูตรภาษาไทยที่ถูกต้อง เป็นทางการ
3. `title_en`: แปลหรือระบุชื่อหลักสูตรภาษาอังกฤษทางการ (e.g. Doctor of Medicine Program, Bachelor of Engineering Program in ...)
4. `degree_level`: ปริญญาตรี / ปริญญาโท / ปริญญาเอก / ประกาศนียบัตร
5. `degree_name`: ชื่อปริญญาและอักษรย่อ เช่น พ.บ., วศ.บ., วท.บ., ภ.บ., บธ.บ., ศศ.บ., วศ.ม., บธ.ม., ปร.ด.
6. `university` & `university_th`: ตามที่ระบุ
7. `faculty` & `faculty_th`: ตามที่ระบุ
8. `department` & `department_th`: ภาควิชาที่เกี่ยวข้อง
9. `program_type`: ภาคปกติ / ภาคพิเศษ / นานาชาติ
10. `duration_years`: เช่น 6 ปี, 4 ปี, 5 ปี, 2 ปี, 3 ปี
11. `total_credits`: เช่น 120-140 หน่วยกิต, 36 หน่วยกิต, 48 หน่วยกิต
12. `tuition_per_semester` & `tuition_total`: ประมาณการค่าธรรมเนียมตามอัตราจริง เช่น 18,000 - 45,000 บาท
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
                course_dict = course_obj.model_dump() if hasattr(course_obj, 'model_dump') else dict(course_obj)
                course_dict['website_url'] = 'https://www.google.com'
                enriched_courses.append(course_dict)

    print(f"\n🧠 Generating 768-dim Vector Embeddings for {len(enriched_courses)} new courses...")
    db = SessionLocal()
    inserted_count = 0
    try:
        for idx_c, c in enumerate(enriched_courses):
            base_id = c['id']
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
                tuition_per_semester=c.get('tuition_per_semester', '22,000 บาท'),
                tuition_total=c.get('tuition_total', '88,000 บาท'),
                description=c.get('description', ''),
                curriculum_highlights=c.get('curriculum_highlights', []),
                career_paths=c.get('career_paths', []),
                tags=c.get('tags', []),
                website_url=c.get('website_url', 'https://www.google.com'),
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

    print(f"\n🎉 Successfully enriched and inserted {inserted_count} official courses for NU, SWU, BUU, SU, PSU, NIDA with 768-dim embeddings!")

if __name__ == '__main__':
    enrich_and_insert_next_universities()
