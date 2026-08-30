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

# Comprehensive list of KMUTNB faculties and their official academic departments and degree levels
KMUTNB_CURRICULUM_OFFICIAL = [
    # 1. คณะวิศวกรรมศาสตร์ (Faculty of Engineering)
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "dept": "วิศวกรรมเครื่องกลและการบิน-อวกาศ"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการบินและอวกาศ", "dept": "วิศวกรรมเครื่องกลและการบิน-อวกาศ"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า (ระบบไฟฟ้ากำลัง/ระบบควบคุมอัตโนมัติ)", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการผลิต", "dept": "วิศวกรรมการผลิต"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ", "dept": "วิศวกรรมการผลิต"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี", "dept": "วิศวกรรมเคมี"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการ", "dept": "วิศวกรรมอุตสาหการ"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา", "dept": "วิศวกรรมโยธา"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมวัสดุและเทคโนโลยีการผลิต", "dept": "วิศวกรรมวัสดุและเทคโนโลยีการผลิต"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องมือวัดและอิเล็กทรอนิกส์", "dept": "วิศวกรรมเครื่องมือวัดและอิเล็กทรอนิกส์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมขนถ่ายวัสดุและโลจิสติกส์", "dept": "วิศวกรรมขนถ่ายวัสดุและโลจิสติกส์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล", "dept": "วิศวกรรมเครื่องกลและการบิน-อวกาศ"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมการผลิต", "dept": "วิศวกรรมการผลิต"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมเคมี", "dept": "วิศวกรรมเคมี"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการและการจัดการโลจิสติกส์", "dept": "วิศวกรรมอุตสาหการ"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมโยธา", "dept": "วิศวกรรมโยธา"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์", "dept": "วิศวกรรมไฟฟ้าและคอมพิวเตอร์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมเครื่องกลและการบิน-อวกาศ", "dept": "วิศวกรรมเครื่องกลและการบิน-อวกาศ"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมเคมี", "dept": "วิศวกรรมเคมี"},
    {"fac_th": "คณะวิศวกรรมศาสตร์", "fac_en": "Faculty of Engineering", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมการผลิต", "dept": "วิศวกรรมการผลิต"},

    # 2. บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและสารสนเทศ (หลักสูตรนานาชาติ)", "dept": "Electrical and Information Engineering (EIE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมยานยนต์และระบบขนส่ง (หลักสูตรนานาชาติ)", "dept": "Mechanical and Automotive Engineering (MAE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมเคมีและกระบวนการ (หลักสูตรนานาชาติ)", "dept": "Chemical and Process Engineering (CPE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมวัสดุและการผลิต (หลักสูตรนานาชาติ)", "dept": "Materials and Production Engineering (MPE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมระบบรางและโครงสร้างพื้นฐาน (หลักสูตรนานาชาติ)", "dept": "Railway Vehicles and Infrastructure Engineering (RVIE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาเอก", "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์ (หลักสูตรนานาชาติ)", "dept": "Electrical and Information Engineering (EIE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาเอก", "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมเครื่องกลและยานยนต์ (หลักสูตรนานาชาติ)", "dept": "Mechanical and Automotive Engineering (MAE)"},
    {"fac_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)", "fac_en": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)", "level": "ปริญญาเอก", "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมเคมีและกระบวนการ (หลักสูตรนานาชาติ)", "dept": "Chemical and Process Engineering (CPE)"},

    # 3. คณะวิทยาศาสตร์ประยุกต์ (Faculty of Applied Science)
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์", "dept": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเคมีอุตสาหกรรม", "dept": "ภาควิชาเคมีอุตสาหกรรม"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์และการประมวลผลข้อมูล", "dept": "ภาควิชาคณิตศาสตร์"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาฟิสิกส์อุตสาหกรรมและอุปกรณ์การแพทย์", "dept": "ภาควิชาฟิสิกส์อุตสาหกรรมและอุปกรณ์การแพทย์"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ", "dept": "ภาควิชาเทคโนโลยีชีวภาพ"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาสถิติธุรกิจและการประกันภัย", "dept": "ภาควิชาสถิติประยุกต์"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร", "dept": "ภาควิชาเทคโนโลยีอุตสาหกรรมเกษตร อาหาร และสิ่งแวดล้อม"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์", "dept": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเคมีประยุกต์", "dept": "ภาควิชาเคมีอุตสาหกรรม"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์และวิทยาการข้อมูล", "dept": "ภาควิชาคณิตศาสตร์"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ", "dept": "ภาควิชาเทคโนโลยีชีวภาพ"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และสารสนเทศ", "dept": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ"},
    {"fac_th": "คณะวิทยาศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Science", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเคมีอุตสาหกรรมและวัสดุขั้นสูง", "dept": "ภาควิชาเคมีอุตสาหกรรม"},

    # 4. คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล (ITDI)
    {"fac_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล", "fac_en": "Faculty of Information Technology and Digital Innovation", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ", "dept": "ภาควิชาเทคโนโลยีสารสนเทศ"},
    {"fac_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล", "fac_en": "Faculty of Information Technology and Digital Innovation", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการจัดการข้อมูลและนวัตกรรมดิจิทัล", "dept": "ภาควิชานวัตกรรมดิจิทัล"},
    {"fac_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล", "fac_en": "Faculty of Information Technology and Digital Innovation", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ (AI, Cyber Security, Big Data)", "dept": "ภาควิชาเทคโนโลยีสารสนเทศ"},
    {"fac_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล", "fac_en": "Faculty of Information Technology and Digital Innovation", "level": "ปริญญาโท", "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ชั้นสูง", "dept": "ภาควิชาวิทยาการข้อมูล"},
    {"fac_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล", "fac_en": "Faculty of Information Technology and Digital Innovation", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ", "dept": "ภาควิชาเทคโนโลยีสารสนเทศ"},

    # 5. คณะครุศาสตร์อุตสาหกรรม (Faculty of Technical Education)
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมบัณฑิต สาขาวิชาวิศวกรรมเครื่องกลและการผลิต", "dept": "ภาควิชาครุศาสตร์เครื่องกล"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและการศึกษา", "dept": "ภาควิชาครุศาสตร์ไฟฟ้า"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมบัณฑิต สาขาวิชาวิศวกรรมโยธาและการศึกษา", "dept": "ภาควิชาครุศาสตร์โยธา"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาตรี", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมบัณฑิต สาขาวิชาคอมพิวเตอร์และการศึกษา", "dept": "ภาควิชาคอมพิวเตอร์ศึกษา"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาโท", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมมหาบัณฑิต สาขาวิชาการบริหารการอาชีวะและเทคนิคศึกษา", "dept": "ภาควิชาเทคนิคศึกษา"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาโท", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมมหาบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและการศึกษา", "dept": "ภาควิชาครุศาสตร์ไฟฟ้า"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาโท", "title_th": "หลักสูตรครุศาสตร์อุตสาหกรรมมหาบัณฑิต สาขาวิชาเทคโนโลยีคอมพิวเตอร์", "dept": "ภาควิชาคอมพิวเตอร์ศึกษา"},
    {"fac_th": "คณะครุศาสตร์อุตสาหกรรม", "fac_en": "Faculty of Technical Education", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาบริหารอาชีวะและเทคนิคศึกษา", "dept": "ภาควิชาเทคนิคศึกษา"},

    # 6. วิทยาลัยเทคโนโลยีอุตสาหกรรม (College of Industrial Technology)
    {"fac_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม", "fac_en": "College of Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต/วิศวกรรมศาสตรบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมการเชื่อม", "dept": "ภาควิชาเทคโนโลยีวิศวกรรมการเชื่อม"},
    {"fac_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม", "fac_en": "College of Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมยานยนต์และระบบขนส่ง", "dept": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล"},
    {"fac_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม", "fac_en": "College of Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมอิเล็กทรอนิกส์กำลังและพลังงาน", "dept": "ภาควิชาเทคโนโลยีวิศวกรรมไฟฟ้า"},
    {"fac_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม", "fac_en": "College of Industrial Technology", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมซอฟต์แวร์และการจัดการระบบดิจิทัล", "dept": "ภาควิชาเทคโนโลยีวิศวกรรมอิเล็กทรอนิกส์"},
    {"fac_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม", "fac_en": "College of Industrial Technology", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมอุตสาหการและการผลิต", "dept": "ภาควิชาเทคโนโลยีวิศวกรรมการจัดการ"},
    {"fac_th": "วิทยาลัยเทคโนโลยีอุตสาหกรรม", "fac_en": "College of Industrial Technology", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมเครื่องกลและพลังงาน", "dept": "ภาควิชาเทคโนโลยีวิศวกรรมเครื่องกล"},

    # 7. คณะบริหารธุรกิจ (Faculty of Business Administration)
    {"fac_th": "คณะบริหารธุรกิจ", "fac_en": "Faculty of Business Administration", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการนวัตกรรมและเทคโนโลยีการบริการ", "dept": "ภาควิชาบริหารธุรกิจ"},
    {"fac_th": "คณะบริหารธุรกิจ", "fac_en": "Faculty of Business Administration", "level": "ปริญญาตรี", "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทาน", "dept": "ภาควิชาโลจิสติกส์"},
    {"fac_th": "คณะบริหารธุรกิจ", "fac_en": "Faculty of Business Administration", "level": "ปริญญาตรี", "title_th": "หลักสูตรบัญชีบัณฑิต", "dept": "ภาควิชาการบัญชี"},
    {"fac_th": "คณะบริหารธุรกิจ", "fac_en": "Faculty of Business Administration", "level": "ปริญญาโท", "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (MBA - นวัตกรรมธุรกิจและการวิเคราะห์การตลาด)", "dept": "ภาควิชาบริหารธุรกิจ"},
    {"fac_th": "คณะบริหารธุรกิจ", "fac_en": "Faculty of Business Administration", "level": "ปริญญาโท", "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และซัพพลายเชนเชิงกลยุทธ์", "dept": "ภาควิชาโลจิสติกส์"},
    {"fac_th": "คณะบริหารธุรกิจ", "fac_en": "Faculty of Business Administration", "level": "ปริญญาเอก", "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาบริหารธุรกิจและนวัตกรรมการเป็นผู้ประกอบการ", "dept": "ภาควิชาบริหารธุรกิจ"},

    # 8. คณะศิลปศาสตร์ประยุกต์ (Faculty of Applied Arts)
    {"fac_th": "คณะศิลปศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษเพื่อการสื่อสารเชิงธุรกิจและอุตสาหกรรม", "dept": "ภาควิชาภาษา"},
    {"fac_th": "คณะศิลปศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Arts", "level": "ปริญญาตรี", "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาจีนเพื่อการสื่อสารธุรกิจ", "dept": "ภาควิชาภาษา"},
    {"fac_th": "คณะศิลปศาสตร์ประยุกต์", "fac_en": "Faculty of Applied Arts", "level": "ปริญญาโท", "title_th": "หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชาภาษาอังกฤษเพื่อการสื่อสารทางวิชาชีพและวิชาการ", "dept": "ภาควิชาภาษา"},

    # 9. วิทยาเขตปราจีนบุรี & ระยอง (Prachinburi & Rayong Campuses)
    {"fac_th": "คณะเทคโนโลยีและการจัดการอุตสาหกรรม", "fac_en": "Faculty of Industrial Technology and Management", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมสารสนเทศและเครือข่ายอัจฉริยะ", "dept": "ภาควิชาเทคโนโลยีสารสนเทศ"},
    {"fac_th": "คณะเทคโนโลยีและการจัดการอุตสาหกรรม", "fac_en": "Faculty of Industrial Technology and Management", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการและการจัดการองค์กร", "dept": "ภาควิชาการจัดการอุตสาหกรรม"},
    {"fac_th": "คณะอุตสาหกรรมเกษตร", "fac_en": "Faculty of Agro-Industry", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชานวัตกรรมอาหารและสุขภาพ", "dept": "ภาควิชานวัตกรรมเกษตรและอาหาร"},
    {"fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยี (วิทยาเขตระยอง)", "fac_en": "Faculty of Engineering and Technology (Rayong Campus)", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการผลิตและเทคโนโลยีขั้นสูง", "dept": "ภาควิชาวิศวกรรมการผลิต"},
    {"fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยี (วิทยาเขตระยอง)", "fac_en": "Faculty of Engineering and Technology (Rayong Campus)", "level": "ปริญญาตรี", "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโลจิสติกส์และอัตโนมัติ", "dept": "ภาควิชาวิศวกรรมโลจิสติกส์"},
    {"fac_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยี (วิทยาเขตระยอง)", "fac_en": "Faculty of Engineering and Technology (Rayong Campus)", "level": "ปริญญาโท", "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีวิศวกรรมการผลิตและหุ่นยนต์", "dept": "ภาควิชาวิศวกรรมการผลิต"}
]

def enrich_and_insert_kmutnb():
    print(f"=== 🎓 Enriching and Ingesting KMUTNB (มจพ. พระนครเหนือ) Official Curricula ===")

    with engine.connect() as conn:
        db_kmutnb = conn.execute(text("SELECT title_th, degree_level FROM courses WHERE university LIKE '%North Bangkok%' OR university_th LIKE '%พระนครเหนือ%'")).fetchall()

    existing_kmutnb = set(normalize_title(r[0]) for r in db_kmutnb)
    missing = [x for x in KMUTNB_CURRICULUM_OFFICIAL if normalize_title(x['title_th']) not in existing_kmutnb]

    print(f"📊 Identified {len(missing)} brand new KMUTNB courses to ingest.")
    if not missing:
        print("✅ KMUTNB is already 100% complete!")
        return

    batch_size = 15
    batches = [missing[i:i+batch_size] for i in range(0, len(missing), batch_size)]

    def process_batch(batch_idx, batch_items):
        prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านระบบข้อมูลหลักสูตรมหาวิทยาลัยในประเทศไทย
โปรดแปลงข้อมูลหลักสูตรของ มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ (KMUTNB) ต่อไปนี้ ให้เป็นข้อมูลโครงสร้าง JSON ตาม Schema ที่กำหนด:

รายการหลักสูตร:
{json.dumps(batch_items, ensure_ascii=False, indent=2)}

ข้อกำหนดสำคัญ:
1. `id`: สร้าง unique id สั้นๆ ชัดเจน เช่น `kmutnb_eng_mech_bsc`, `kmutnb_tggs_auto_msc`, `kmutnb_sci_cs_phd`
2. `title_th`: ใช้ชื่อหลักสูตรภาษาไทยที่ถูกต้อง เป็นทางการ
3. `title_en`: แปลหรือระบุชื่อหลักสูตรภาษาอังกฤษทางการ (e.g. Bachelor of Engineering Program in ...)
4. `degree_level`: ปริญญาตรี / ปริญญาโท / ปริญญาเอก / ประกาศนียบัตร
5. `degree_name`: ชื่อปริญญาและอักษรย่อ เช่น วศ.บ., วท.บ., วศ.ม., ปร.ด.
6. `university`: King Mongkut's University of Technology North Bangkok
7. `university_th`: มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ
8. `faculty` & `faculty_th`: ตามที่ระบุ
9. `department` & `department_th`: ภาควิชาที่เกี่ยวข้อง
10. `program_type`: ภาคปกติ / ภาคพิเศษ / นานาชาติ
11. `duration_years`: เช่น 4 ปี, 2 ปี, 3 ปี
12. `total_credits`: เช่น 120-140 หน่วยกิต, 36 หน่วยกิต, 48 หน่วยกิต
13. `tuition_per_semester` & `tuition_total`: ประมาณการค่าธรรมเนียมตามอัตราจริง เช่น 19,000 - 45,000 บาท
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
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_batch, i, b) for i, b in enumerate(batches)]
        for i, f in enumerate(futures):
            res = f.result()
            print(f"  Enriched batch {i+1}/{len(batches)}: {len(res)} courses")
            batch_items = batches[i]
            for j, course_obj in enumerate(res):
                course_dict = course_obj.model_dump() if hasattr(course_obj, 'model_dump') else dict(course_obj)
                course_dict['website_url'] = 'https://www.kmutnb.ac.th'
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
                website_url=c.get('website_url', 'https://www.kmutnb.ac.th'),
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

    print(f"\n🎉 Successfully enriched and inserted {inserted_count} official KMUTNB courses with 768-dim embeddings!")

if __name__ == '__main__':
    enrich_and_insert_kmutnb()
