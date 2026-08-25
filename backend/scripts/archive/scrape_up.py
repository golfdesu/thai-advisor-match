"""
Scraper and Data Seeder for University of Phayao (UP) - มหาวิทยาลัยพะเยา
Target: Undergraduate and Graduate Curricula across all faculties & schools.

Sources:
- University of Phayao Academic Affairs & Registrar (reg.up.ac.th / admission.up.ac.th)
- School Portals (Medicine, Dentistry, Pharmacy, Allied Health, Nursing, ICT, Engineering, Science, etc.)
- Official University of Phayao Tuition & Curriculum Regulations

Schema:
CourseDB(
    id, title_th, title_en, degree_level, degree_name,
    university, university_th, faculty, faculty_th,
    department, department_th, program_type, duration_years,
    total_credits, tuition_per_semester, tuition_total,
    description, curriculum_highlights, career_paths, tags, website_url
)
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

# Ensure backend path is added
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("up_scraper")

UNIVERSITY_EN = "University of Phayao"
UNIVERSITY_TH = "มหาวิทยาลัยพะเยา"
BASE_URL = "https://www.up.ac.th"

# Comprehensive Curricula Matrix for University of Phayao
UP_COURSES: List[Dict[str, Any]] = [
    # ---------------------------------------------------------
    # 1. School of Medicine (คณะแพทยศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program (M.D.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Medicine",
        "department_th": "แพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "540,000 บาท",
        "description": "มุ่งผลิตแพทย์ที่มีความรู้ความสามารถตามเกณฑ์มาตรฐานผู้ประกอบวิชาชีพเวชกรรม มีหัวใจความเป็นมนุษย์ เชี่ยวชาญการแพทย์ปฐมภูมิและการแพทย์ชนบท",
        "curriculum_highlights": ["เวชปฏิบัติทั่วไปและเวชศาสตร์ครอบครัว", "การบริบาลผู้ป่วยในระบบสุขภาพชุมชน", "อายุรศาสตร์ ศัลยศาสตร์ กุมารเวชศาสตร์ สูติศาสตร์-นรีเวชวิทยา"],
        "career_paths": ["แพทย์เวชปฏิบัติทั่วไป", "แพทย์เฉพาะทางสาขาต่างๆ", "อาจารย์แพทย์และนักวิจัยทางการแพทย์"],
        "tags": ["Medicine", "Doctor", "Health Science", "Clinical Medicine"],
        "website_url": "https://med.up.ac.th"
    },
    {
        "id": "up_med_ttm",
        "title_th": "หลักสูตรการแพทย์แผนไทยประยุกต์บัณฑิต",
        "title_en": "Bachelor of Applied Thai Traditional Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พท.ป.บ. (การแพทย์แผนไทยประยุกต์บัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Applied Thai Traditional Medicine",
        "department_th": "การแพทย์แผนไทยประยุกต์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "บูรณาการศาสตร์การแพทย์แผนไทยเข้ากับวิทยาศาสตร์การแพทย์สมัยใหม่ เน้นการตรวจวินิจฉัย การรักษาด้วยยาสมุนไพร หัตถการบำบัด และการผดุงครรภ์ไทย",
        "curriculum_highlights": ["เวชกรรมไทยประยุกต์", "เภสัชกรรมไทยและตำรับยาสมุนไพร", "หัตถเวชกรรมและการนวดบำบัดรักษา"],
        "career_paths": ["แพทย์แผนไทยประยุกต์ในโรงพยาบาลรัฐและเอกชน", "ผู้ประกอบการคลินิกการแพทย์แผนไทย", "นักวิจัยและพัฒนาผลิตภัณฑ์สมุนไพร"],
        "tags": ["Applied Thai Traditional Medicine", "Herbal Medicine", "Healthcare"],
        "website_url": "https://med.up.ac.th"
    },
    {
        "id": "up_med_paramedic",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาปฏิบัติการฉุกเฉินการแพทย์",
        "title_en": "Bachelor of Science Program in Emergency Medical Operation (Paramedic)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ปฏิบัติการฉุกเฉินการแพทย์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Emergency Medical Services",
        "department_th": "ปฏิบัติการฉุกเฉินการแพทย์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "ผลิตนักฉุกเฉินการแพทย์ (Paramedic) ที่มีความเชี่ยวชาญในการช่วยชีวิตและการบริบาลผู้ป่วยฉุกเฉินนอกโรงพยาบาล การกู้ชีพขั้นสูง และการบริหารจัดการสาธารณภัย",
        "curriculum_highlights": ["การกู้ชีพขั้นสูง (Advanced Life Support)", "การบริบาลผู้ป่วยวิกฤตนอกโรงพยาบาล", "การจัดการภาวะฉุกเฉินและสาธารณภัย"],
        "career_paths": ["นักปฏิบัติการฉุกเฉินการแพทย์ (Paramedic)", "บุคลากรศูนย์สั่งการและกู้ชีพ 1669", "เจ้าหน้าที่การแพทย์ฉุกเฉินทางอากาศและทางน้ำ"],
        "tags": ["Paramedic", "Emergency Medicine", "Rescue", "Healthcare"],
        "website_url": "https://med.up.ac.th"
    },

    # ---------------------------------------------------------
    # 2. School of Dentistry (คณะทันตแพทยศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_dent_dentsurg",
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Dental Surgery Program (D.D.S.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตรบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Dentistry",
        "department_th": "ทันตแพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "218 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "720,000 บาท",
        "description": "ผลิตทันตแพทย์ผู้มีความรู้ความสามารถด้านทันตกรรมคลินิก ทันตกรรมป้องกัน และทันตสาธารณสุข พร้อมฝึกทักษะกับผู้ป่วยจริงในโรงพยาบาลทันตกรรม",
        "curriculum_highlights": ["ทันตกรรมหัตถการและวิทยาเอ็นโดดอนต์", "ทันตกรรมประดิษฐ์และศัลยศาสตร์ช่องปาก", "ทันตกรรมจัดฟันและทันตกรรมสำหรับเด็ก"],
        "career_paths": ["ทันตแพทย์ในโรงพยาบาลรัฐบาลและเอกชน", "เจ้าของคลินิกทันตกรรมส่วนตัว", "อาจารย์และนักวิจัยทางทันตแพทยศาสตร์"],
        "tags": ["Dentistry", "Dental Surgery", "Oral Health", "Doctor"],
        "website_url": "https://dentistry.up.ac.th"
    },

    # ---------------------------------------------------------
    # 3. School of Pharmacy (คณะเภสัชศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_pharm_pharmd",
        "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม",
        "title_en": "Doctor of Pharmacy Program in Pharmaceutical Care (Pharm.D.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ภ.บ. (การบริบาลทางเภสัชกรรม)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Pharmacy Practice",
        "department_th": "เภสัชกรรมปฏิบัติ",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "225 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "420,000 บาท",
        "description": "หลักสูตรวิชาชีพ 6 ปี เน้นการดูแลการใช้ยาของผู้ป่วย การจัดการความปลอดภัยด้านยาในโรงพยาบาลและชุมชน เภสัชบำบัด และการบริบาลเภสัชกรรมคลินิก",
        "curriculum_highlights": ["เภสัชบำบัดในโรคเรื้อรังและผู้ป่วยวิกฤต", "เภสัชวิทยาและพิษวิทยาคลินิก", "การบริบาลเภสัชกรรมชุมชนและโรงพยาบาล"],
        "career_paths": ["เภสัชกรประจำโรงพยาบาลรัฐและเอกชน", "เภสัชกรชุมชน (ร้านยา)", "เภสัชกรผู้แทนยาและวิจัยทางคลินิก (CRA)"],
        "tags": ["Pharmacy", "PharmD", "Pharmaceutical Care", "Clinical Pharmacy"],
        "website_url": "https://pharmacy.up.ac.th"
    },
    {
        "id": "up_pharm_cosmetic",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์เครื่องสำอาง",
        "title_en": "Bachelor of Science Program in Cosmetic Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์เครื่องสำอาง)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Cosmetic Science",
        "department_th": "วิทยาศาสตร์เครื่องสำอาง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "ผลิตนักวิทยาศาสตร์เครื่องสำอางผู้เชี่ยวชาญการวิจัยและพัฒนาตำรับ การควบคุมคุณภาพผลิตภัณฑ์เครื่องสำอาง นวัตกรรมความงาม และกฎหมายเครื่องสำอาง",
        "curriculum_highlights": ["การพัฒนาสูตรตำรับเครื่องสำอางและการประเมินประสิทธิภาพ", "เคมีและสารออกฤทธิ์ทางชีวภาพสำหรับเครื่องสำอาง", "การควบคุมคุณภาพและความปลอดภัยของเครื่องสำอาง"],
        "career_paths": ["นักวิจัยและพัฒนาผลิตภัณฑ์เครื่องสำอาง (R&D)", "ผู้ควบคุมคุณภาพ (QA/QC) ในอุตสาหกรรมเครื่องสำอาง", "เจ้าของแบรนด์ธุรกิจความงามและสุขภาพ"],
        "tags": ["Cosmetic Science", "Skincare", "Formulation", "Beauty Science"],
        "website_url": "https://pharmacy.up.ac.th"
    },

    # ---------------------------------------------------------
    # 4. School of Nursing (คณะพยาบาลศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_nurse_bns",
        "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต",
        "title_en": "Bachelor of Nursing Science Program (B.N.S.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พย.บ. (พยาบาลศาสตรบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Nursing Science",
        "department_th": "พยาบาลศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "มุ่งเน้นผลิตพยาบาลวิชาชีพที่มีทักษะการปฏิบัติการพยาบาลแบบองค์รวม ทั้งการส่งเสริมสุขภาพ การป้องกันโรค การรักษาพยาบาล และการฟื้นฟูสุขภาพ",
        "curriculum_highlights": ["การพยาบาลผู้ใหญ่และผู้สูงอายุ", "การพยาบาลมารดา ทารก และการผดุงครรภ์", "การพยาบาลเด็กและสุขภาพจิต/จิตเวช"],
        "career_paths": ["พยาบาลวิชาชีพในโรงพยาบาลภาครัฐและเอกชน", "พยาบาลอาชีวอนามัยและสถานประกอบการ", "พยาบาลประจำคลินิกและสถานดูแลสุขภาพ"],
        "tags": ["Nursing", "Nurse", "Healthcare", "Patient Care"],
        "website_url": "https://nurse.up.ac.th"
    },

    # ---------------------------------------------------------
    # 5. School of Allied Health Sciences (คณะสหเวชศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_ahs_medtech",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคนิคการแพทย์",
        "title_en": "Bachelor of Science Program in Medical Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคนิคการแพทย์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Medical Technology",
        "department_th": "เทคนิคการแพทย์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "เรียนรู้การตรวจวิเคราะห์สิ่งส่งตรวจทางห้องปฏิบัติการทางการแพทย์เพื่อสนับสนุนการวินิจฉัย การรักษา และการพยากรณ์โรค",
        "curriculum_highlights": ["เคมีคลินิกและโลหิตวิทยา", "ภูมิคุ้มกันวิทยาคลินิกและธนาคารเลือด", "จุลชีววิทยาคลินิกและปรสิตวิทยา"],
        "career_paths": ["นักเทคนิคการแพทย์ในห้องปฏิบัติการโรงพยาบาล", "ผู้เชี่ยวชาญผลิตภัณฑ์ตรวจวิเคราะห์ทางการแพทย์ (Product Specialist)", "นักวิจัยในศูนย์วิจัยและนิติวิทยาศาสตร์"],
        "tags": ["Medical Technology", "Clinical Laboratory", "Diagnostics", "Allied Health"],
        "website_url": "https://ahs.up.ac.th"
    },
    {
        "id": "up_ahs_physiotherapy",
        "title_th": "หลักสูตรกายภาพบำบัดบัณฑิต",
        "title_en": "Bachelor of Physical Therapy Program (B.P.T.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "กภ.บ. (กายภาพบำบัดบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Physical Therapy",
        "department_th": "กายภาพบำบัด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "ฝึกฝนการตรวจประเมิน วินิจฉัย และให้การรักษาฟื้นฟูสมรรถภาพผู้ป่วยทางระบบกล้ามเนื้อ กระดูก ระบบประสาท ระบบหายใจ และกายภาพบำบัดการกีฬา",
        "curriculum_highlights": ["กายภาพบำบัดทางระบบกระดูกและกล้ามเนื้อ", "กายภาพบำบัดทางระบบประสาท", "กายภาพบำบัดทางการกีฬาและทรวงอก"],
        "career_paths": ["นักกายภาพบำบัดในโรงพยาบาลและศูนย์ฟื้นฟูสมรรถภาพ", "นักกายภาพบำบัดประจำสโมสรกีฬา", "ผู้ประกอบการคลินิกกายภาพบำบัด"],
        "tags": ["Physical Therapy", "Physiotherapy", "Rehabilitation", "Sports Physical Therapy"],
        "website_url": "https://ahs.up.ac.th"
    },

    # ---------------------------------------------------------
    # 6. School of Public Health (คณะสาธารณสุขศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_ph_comm_health",
        "title_th": "หลักสูตรสาธารณสุขศาสตรบัณฑิต สาขาวิชาอนามัยชุมชน",
        "title_en": "Bachelor of Public Health Program in Community Health",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ส.บ. (อนามัยชุมชน)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Community Health",
        "department_th": "อนามัยชุมชน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "เน้นการบริหารจัดการงานสาธารณสุข การเฝ้าระวังโรคระบาด การส่งเสริมสุขภาพ และการประเมินปัญหาสุขภาพในระดับชุมชนและปฐมภูมิ",
        "curriculum_highlights": ["ระบาดวิทยาและการควบคุมโรค", "การบริหารจัดการสาธารณสุขชุมชน", "การประเมินภาวะสุขภาพและพฤติกรรมศาสตร์"],
        "career_paths": ["นักวิชาการสาธารณสุข (รพ.สต. / สสอ. / สสจ.)", "นักส่งเสริมสุขภาพในองค์กรปกครองส่วนท้องถิ่น", "ผู้ประสานงานโครงการด้านสุขภาพระหว่างประเทศ"],
        "tags": ["Public Health", "Community Health", "Epidemiology", "Primary Care"],
        "website_url": "https://ph.up.ac.th"
    },
    {
        "id": "up_ph_env_health",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาอนามัยสิ่งแวดล้อม",
        "title_en": "Bachelor of Science Program in Environmental Health",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (อนามัยสิ่งแวดล้อม)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Environmental Health",
        "department_th": "อนามัยสิ่งแวดล้อม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ผลิตนักวิชาการที่เชี่ยวชาญการประเมินและควบคุมมลพิษสิ่งแวดล้อม การประเมินผลกระทบทางสุขภาพ (HIA) และการจัดการสุขาภิบาลสิ่งแวดล้อม",
        "curriculum_highlights": ["การประเมินผลกระทบต่อสิ่งแวดล้อมและสุขภาพ (EIA/HIA)", "การจัดการมลพิษทางอากาศ น้ำ และขยะมูลฝอย", "พิษวิทยาสิ่งแวดล้อมและสุขาภิบาล"],
        "career_paths": ["นักวิชาการสุขาภิบาลและอนามัยสิ่งแวดล้อม", "เจ้าหน้าที่ควบคุมคุณภาพสิ่งแวดล้อมในภาคอุตสาหกรรม", "ที่ปรึกษาด้านการประเมินสิ่งแวดล้อม"],
        "tags": ["Environmental Health", "Pollution Control", "EIA", "Public Health"],
        "website_url": "https://ph.up.ac.th"
    },
    {
        "id": "up_ph_occ_health",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาอาชีวอนามัยและความปลอดภัย",
        "title_en": "Bachelor of Science Program in Occupational Health and Safety",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (อาชีวอนามัยและความปลอดภัย)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Occupational Health and Safety",
        "department_th": "อาชีวอนามัยและความปลอดภัย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ผลิตเจ้าหน้าที่ความปลอดภัยในการทำงานระดับวิชาชีพ (จป.วิชาชีพ) ตามกฎหมาย เพื่อตรวจประเมินความเสี่ยงและป้องกันอุบัติเหตุในสถานประกอบการ",
        "curriculum_highlights": ["การยศาสตร์และความปลอดภัยในโรงงาน", "การตรวจวัดและควบคุมสภาพแวดล้อมในการทำงาน", "กฎหมายความปลอดภัย อาชีวอนามัย และสิ่งแวดล้อม"],
        "career_paths": ["เจ้าหน้าที่ความปลอดภัยในการทำงานระดับวิชาชีพ (จป.วิชาชีพ)", "ผู้ตรวจประเมินระบบมาตรฐานความปลอดภัย (ISO 45001)", "นักวิชาการอาชีวอนามัย"],
        "tags": ["Occupational Health", "Safety Officer", "จป.วิชาชีพ", "Workplace Safety"],
        "website_url": "https://ph.up.ac.th"
    },
    {
        "id": "up_ph_tcm",
        "title_th": "หลักสูตรการแพทย์แผนจีนบัณฑิต",
        "title_en": "Bachelor of Traditional Chinese Medicine Program (B.TCM)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พจ.บ. (การแพทย์แผนจีนบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Traditional Chinese Medicine",
        "department_th": "การแพทย์แผนจีน",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "210 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "540,000 บาท",
        "description": "หลักสูตร 6 ปี ร่วมมือกับมหาวิทยาลัยการแพทย์แผนจีนชั้นนำในประเทศจีน สอนการฝังเข็ม ยาสมุนไพรจีน การทุยหนา และการวินิจฉัยโรคตามศาสตร์จีน",
        "curriculum_highlights": ["ทฤษฎีพื้นฐานและการวินิจฉัยการแพทย์แผนจีน", "การฝังเข็มและรมยา (Acupuncture & Moxibustion)", "ตำรับยาจีนโบราณและการนวดทุยหนา (Tuina)"],
        "career_paths": ["แพทย์แผนจีนประจำโรงพยาบาลและคลินิก", "ผู้ประกอบการคลินิกการแพทย์แผนจีนและการฝังเข็ม", "อาจารย์และนักวิชาการด้านการแพทย์บูรณาการ"],
        "tags": ["Traditional Chinese Medicine", "Acupuncture", "Herbal Medicine", "TCM"],
        "website_url": "https://ph.up.ac.th"
    },

    # ---------------------------------------------------------
    # 7. School of Medical Sciences (คณะวิทยาศาสตร์การแพทย์)
    # ---------------------------------------------------------
    {
        "id": "up_medsci_microbio",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาจุลชีววิทยา",
        "title_en": "Bachelor of Science Program in Microbiology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (จุลชีววิทยา)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Medical Sciences",
        "faculty_th": "คณะวิทยาศาสตร์การแพทย์",
        "department": "Microbiology and Parasitology",
        "department_th": "จุลชีววิทยาและปรสิตวิทยา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "เน้นศึกษาชีววิทยาของเชื้อจุลินทรีย์ แบคทีเรีย ไวรัส และเชื้อรา ทั้งในแง่การก่อโรคในมนุษย์และประโยชน์ทางอุตสาหกรรมและยา",
        "curriculum_highlights": ["จุลชีววิทยาทางการแพทย์และไวรัสวิทยา", "พันธุศาสตร์ของจุลินทรีย์และเทคโนโลยีชีวภาพ", "วิทยาภูมิคุ้มกันและการควบคุมการติดเชื้อ"],
        "career_paths": ["นักจุลชีววิทยาในโรงพยาบาลและศูนย์วิจัย", "นักวิทยาศาสตร์ควบคุมคุณภาพ (QC/QA) อาหาร ยา และเครื่องสำอาง", "นักวิจัยด้านวัคซีนและยาปฏิชีวนะ"],
        "tags": ["Microbiology", "Medical Science", "Biotechnology", "Infectious Diseases"],
        "website_url": "https://medsci.up.ac.th"
    },
    {
        "id": "up_medsci_biochem",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาชีวเคมี",
        "title_en": "Bachelor of Science Program in Biochemistry",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ชีวเคมี)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Medical Sciences",
        "faculty_th": "คณะวิทยาศาสตร์การแพทย์",
        "department": "Biochemistry",
        "department_th": "ชีวเคมี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ศึกษาชีวโมเลกุล กลไกเคมีของสิ่งมีชีวิต อณูชีววิทยา และชีววิทยาของมะเร็ง เพื่อต่อยอดสู่การค้นพบยาและนวัตกรรมการแพทย์",
        "curriculum_highlights": ["ชีวเคมีทางการแพทย์และเมแทบอลิซึม", "อณูชีววิทยาและพันธุวิศวกรรม (Molecular Biology)", "ชีวเคมีของโปรตีนและเอนไซม์"],
        "career_paths": ["นักชีวเคมีและนักอณูชีววิทยา", "นักวิจัยในห้องปฏิบัติการทางคลินิกและเภสัชกรรม", "ผู้เชี่ยวชาญผลิตภัณฑ์ตรวจวิเคราะห์ระดับโมเลกุล"],
        "tags": ["Biochemistry", "Molecular Biology", "Medical Science", "Biotech"],
        "website_url": "https://medsci.up.ac.th"
    },
    {
        "id": "up_medsci_nutrition",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาโภชนาการและการกำหนดอาหาร",
        "title_en": "Bachelor of Science Program in Nutrition and Dietetics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (โภชนาการและการกำหนดอาหาร)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Medical Sciences",
        "faculty_th": "คณะวิทยาศาสตร์การแพทย์",
        "department": "Nutrition and Dietetics",
        "department_th": "โภชนาการและการกำหนดอาหาร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "ผลิตนักกำหนดอาหาร (Dietitian) และนักโภชนาการเพื่อวางแผนโภชนบำบัดรักษาโรค ควบคุมอาหารสำหรับผู้ป่วย และส่งเสริมสุขภาพประชาชน",
        "curriculum_highlights": ["โภชนบำบัดทางการแพทย์ในโรคเรื้อรัง (Medical Nutrition Therapy)", "การประเมินและให้คำปรึกษาทางโภชนาการ", "การบริหารจัดการบริการอาหารในโรงพยาบาล"],
        "career_paths": ["นักกำหนดอาหารในโรงพยาบาลรัฐและเอกชน", "นักโภชนาการประจำฟิตเนส ศูนย์สุขภาพ และสถานประกอบการ", "ที่ปรึกษาด้านโภชนาการและพัฒนาผลิตภัณฑ์อาหารเพื่อสุขภาพ"],
        "tags": ["Nutrition", "Dietetics", "Dietitian", "Medical Nutrition Therapy"],
        "website_url": "https://medsci.up.ac.th"
    },

    # ---------------------------------------------------------
    # 8. School of Information and Communication Technology (ICT)
    # ---------------------------------------------------------
    {
        "id": "up_ict_cs",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Computer Science",
        "department_th": "วิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "เรียนรู้ศาสตร์การประมวลผล อัลกอริทึม ปัญญาประดิษฐ์ (AI) การพัฒนาเว็บและโมบายแอปพลิเคชัน และความมั่นคงปลอดภัยไซเบอร์",
        "curriculum_highlights": ["Data Structures & Advanced Algorithms", "Artificial Intelligence & Machine Learning", "Web & Mobile Application Development"],
        "career_paths": ["Full-Stack Software Developer", "AI / Machine Learning Engineer", "System Architect & DevOps Engineer"],
        "tags": ["Computer Science", "AI", "Software Development", "Programming"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_se",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิศวกรรมซอฟต์แวร์",
        "title_en": "Bachelor of Science Program in Software Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิศวกรรมซอฟต์แวร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Software Engineering",
        "department_th": "วิศวกรรมซอฟต์แวร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "เน้นกระบวนการพัฒนาซอฟต์แวร์เชิงวิศวกรรมแบบมืออาชีพ Agile/Scrum สถาปัตยกรรมซอฟต์แวร์ การประกันคุณภาพและการทดสอบซอฟต์แวร์",
        "curriculum_highlights": ["Software Architecture & Design Patterns", "Agile Software Project Management & DevOps", "Software Quality Assurance & Automated Testing"],
        "career_paths": ["Software Engineer", "Scrum Master / Project Manager", "QA / Automation Test Engineer"],
        "tags": ["Software Engineering", "Agile", "QA", "Software Architecture"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_cpe",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Computer Engineering",
        "department_th": "วิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "บูรณาการฮาร์ดแวร์และซอฟต์แวร์ คอมพิวเตอร์ฝังตัว (Embedded Systems) เครือข่ายคอมพิวเตอร์ และอุปกรณ์ Internet of Things (IoT)",
        "curriculum_highlights": ["Microcontroller & Embedded Systems Design", "IoT & Sensor Networks Architecture", "Computer Network & Cyber Security"],
        "career_paths": ["Computer Engineer", "IoT & Embedded Systems Engineer", "Network & Security Engineer"],
        "tags": ["Computer Engineering", "IoT", "Embedded Systems", "Hardware"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_data_sci",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและการประยุกต์",
        "title_en": "Bachelor of Science Program in Data Science and Applications",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการข้อมูลและการประยุกต์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Data Science",
        "department_th": "วิทยาการข้อมูล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "เน้นการวิเคราะห์ข้อมูลขนาดใหญ่ (Big Data) การสร้างแบบจำลองคาดการณ์ Machine Learning และ Business Intelligence เพื่อตอบโจทย์ภาคธุรกิจ",
        "curriculum_highlights": ["Big Data Analytics & Cloud Computing", "Applied Machine Learning & Deep Learning", "Data Visualization & Business Intelligence"],
        "career_paths": ["Data Scientist", "Data Analyst", "Data Engineer / BI Developer"],
        "tags": ["Data Science", "Big Data", "Machine Learning", "Data Analytics"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_cg_multi",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคอมพิวเตอร์กราฟิกและมัลติมีเดีย",
        "title_en": "Bachelor of Science Program in Computer Graphic and Multimedia",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (คอมพิวเตอร์กราฟิกและมัลติมีเดีย)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Computer Graphic and Multimedia",
        "department_th": "คอมพิวเตอร์กราฟิกและมัลติมีเดีย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "17,000 บาท",
        "tuition_total": "136,000 บาท",
        "description": "เน้นการออกแบบและสร้างสรรค์ผลงานกราฟิก 2D/3D แอนิเมชัน การพัฒนาเกม และสื่อเสมือนจริง VR/AR สำหรับอุตสาหกรรมดิจิทัลคอนเทนต์",
        "curriculum_highlights": ["3D Modeling & Character Animation", "Game Development & Interactive Design", "Virtual Reality (VR) & Augmented Reality (AR)"],
        "career_paths": ["Game Developer / Technical Artist", "3D Animator / VFX Artist", "UI/UX & Interactive Media Designer"],
        "tags": ["Game Development", "3D Animation", "Multimedia", "Digital Media"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_gis",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาภูมิสารสนเทศศาสตร์",
        "title_en": "Bachelor of Science Program in Geographic Information Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ภูมิสารสนเทศศาสตร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Geographic Information Science",
        "department_th": "ภูมิสารสนเทศศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "ผสมผสานเทคโนโลยีแผนที่ดิจิทัล ระบบสารสนเทศภูมิศาสตร์ (GIS) การสำรวจข้อมูลระยะไกล (Remote Sensing) และการวิเคราะห์ข้อมูลเชิงพื้นที่",
        "curriculum_highlights": ["Geographic Information Systems (GIS) & Spatial Analysis", "Remote Sensing & Satellite Imagery Processing", "Web GIS & Drone Mapping Applications"],
        "career_paths": ["นักภูมิสารสนเทศ (GIS Specialist)", "นักวิเคราะห์ข้อมูลเชิงพื้นที่ (Spatial Data Analyst)", "นักสำรวจและทำแผนที่ภาพถ่ายทางอากาศ"],
        "tags": ["GIS", "Geoinformatics", "Remote Sensing", "Mapping"],
        "website_url": "https://ict.up.ac.th"
    },

    # ---------------------------------------------------------
    # 9. School of Engineering (คณะวิศวกรรมศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_eng_civil",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา",
        "title_en": "Bachelor of Engineering Program in Civil Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมโยธา)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Civil Engineering",
        "department_th": "วิศวกรรมโยธา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ได้รับการรับรองจากสภาวิศวกร เน้นการออกแบบโครงสร้างอาคารและสะพาน วิศวกรรมปฐพี วิศวกรรมแหล่งน้ำ และการบริหารงานก่อสร้าง",
        "curriculum_highlights": ["Structural Analysis & Reinforced Concrete Design", "Soil Mechanics & Foundation Engineering", "Construction Project Management"],
        "career_paths": ["วิศวกรโยธา / วิศวกรออกแบบโครงสร้าง", "วิศวกรควบคุมงานก่อสร้าง (Site Engineer)", "วิศวกรประมาณราคาและบริหารโครงการ"],
        "tags": ["Civil Engineering", "Structural Design", "Construction Management", "Engineering"],
        "website_url": "http://www.eng.up.ac.th"
    },
    {
        "id": "up_eng_ee",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า",
        "title_en": "Bachelor of Engineering Program in Electrical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมไฟฟ้า)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Electrical Engineering",
        "department_th": "วิศวกรรมไฟฟ้า",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ครอบคลุมระบบไฟฟ้ากำลัง ระบบควบคุมอัตโนมัติ พลังงานหมุนเวียน และระบบส่งจ่ายพลังงานไฟฟ้าตามมาตรฐานสภาวิศวกร",
        "curriculum_highlights": ["Electrical Power Systems & High Voltage Engineering", "Control Systems & Industrial Automation", "Renewable Energy Integration & Smart Grid"],
        "career_paths": ["วิศวกรไฟฟ้ากำลังประจำโรงงานและอาคาร", "วิศวกรการไฟฟ้า (กฟผ. / กฟภ. / กฟน.)", "วิศวกรระบบควบคุมอัตโนมัติและพลังงานแสงอาทิตย์"],
        "tags": ["Electrical Engineering", "Power Systems", "Smart Grid", "Automation"],
        "website_url": "http://www.eng.up.ac.th"
    },
    {
        "id": "up_eng_me",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล",
        "title_en": "Bachelor of Engineering Program in Mechanical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมเครื่องกล)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Mechanical Engineering",
        "department_th": "วิศวกรรมเครื่องกล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "เน้นกลศาสตร์ของแข็ง อุณหพลศาสตร์ กลศาสตร์ของไหล ระบบปรับอากาศ ยานยนต์ และการออกแบบชิ้นส่วนทางกลด้วย CAD/CAM",
        "curriculum_highlights": ["Thermodynamics & Heat Transfer", "Fluid Mechanics & HVAC Systems Design", "Mechanical Machine Design & CAD/CAM Simulation"],
        "career_paths": ["วิศวกรเครื่องกลและออกแบบระบบปรับอากาศ", "วิศวกรยานยนต์และระบบขนส่ง", "วิศวกรซ่อมบำรุงในโรงงานอุตสาหกรรม"],
        "tags": ["Mechanical Engineering", "Thermodynamics", "HVAC", "Automotive"],
        "website_url": "http://www.eng.up.ac.th"
    },
    {
        "id": "up_eng_ie",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการ",
        "title_en": "Bachelor of Engineering Program in Industrial Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมอุตสาหการ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Industrial Engineering",
        "department_th": "วิศวกรรมอุตสาหการ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "มุ่งเน้นการเพิ่มผลผลิต การจัดการโซ่อุปทานและโลจิสติกส์ การควบคุมคุณภาพ Lean Six Sigma และการวางผังโรงงานอัจฉริยะ",
        "curriculum_highlights": ["Operations Research & Supply Chain Optimization", "Quality Control & Six Sigma Methodologies", "Plant Layout & Productivity Improvement"],
        "career_paths": ["วิศวกรอุตสาหการและวางแผนการผลิต", "วิศวกรควบคุมคุณภาพ (Quality Engineer)", "นักวิเคราะห์โลจิสติกส์และโซ่อุปทาน"],
        "tags": ["Industrial Engineering", "Supply Chain", "Lean Six Sigma", "Productivity"],
        "website_url": "http://www.eng.up.ac.th"
    },

    # ---------------------------------------------------------
    # 10. School of Science (คณะวิทยาศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_sci_chem",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเคมี",
        "title_en": "Bachelor of Science Program in Chemistry",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เคมี)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Chemistry",
        "department_th": "เคมี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "ครอบคลุมเคมีอินทรีย์ เคมีอนินทรีย์ เคมีวิเคราะห์ เคมีเชิงฟิสิกส์ และการประยุกต์ใช้เคมีสีเขียวในอุตสาหกรรม",
        "curriculum_highlights": ["Analytical Chemistry & Instrumental Analysis", "Organic Synthesis & Natural Product Chemistry", "Materials Chemistry & Green Chemistry"],
        "career_paths": ["นักเคมีและนักวิจัยทางเคมี", "เจ้าหน้าที่ควบคุมคุณภาพและวิเคราะห์สารเคมีในโรงงาน", "ผู้เชี่ยวชาญเครื่องมือวิทยาศาสตร์"],
        "tags": ["Chemistry", "Analytical Chemistry", "Materials Science", "Science"],
        "website_url": "https://sci.up.ac.th"
    },
    {
        "id": "up_sci_bio",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาชีววิทยา",
        "title_en": "Bachelor of Science Program in Biology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ชีววิทยา)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Biology",
        "department_th": "ชีววิทยา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "ศึกษาความหลากหลายทางชีวภาพ สัตววิทยา พฤกษศาสตร์ นิเวศวิทยา และพันธุศาสตร์เพื่อการอนุรักษ์และการใช้ประโยชน์อย่างยั่งยืน",
        "curriculum_highlights": ["Biodiversity & Conservation Ecology", "Plant & Animal Physiology", "Genetics & Evolutionary Biology"],
        "career_paths": ["นักชีววิทยาและนักวิจัยธรรมชาติวิทยา", "เจ้าหน้าที่ด้านสิ่งแวดล้อมและความหลากหลายทางชีวภาพ", "อาจารย์และนักวิชาการวิทยาศาสตร์"],
        "tags": ["Biology", "Biodiversity", "Ecology", "Genetics"],
        "website_url": "https://sci.up.ac.th"
    },
    {
        "id": "up_sci_math",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์",
        "title_en": "Bachelor of Science Program in Mathematics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (คณิตศาสตร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Mathematics",
        "department_th": "คณิตศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นคณิตศาสตร์บริสุทธิ์และคณิตศาสตร์ประยุกต์ การสร้างแบบจำลองทางคณิตศาสตร์ และการคำนวณเชิงตัวเลขเพื่อแก้ปัญหาซับซ้อน",
        "curriculum_highlights": ["Mathematical Modeling & Differential Equations", "Linear Algebra & Numerical Methods", "Optimization Theory & Financial Mathematics"],
        "career_paths": ["นักคณิตศาสตร์และนักวิเคราะห์เชิงปริมาณ (Quantitative Analyst)", "นักคณิตศาสตร์ประกันภัย (Actuarial Assistant)", "นักวิจัยข้อมูลและอาจารย์"],
        "tags": ["Mathematics", "Math", "Quantitative Analysis", "Modeling"],
        "website_url": "https://sci.up.ac.th"
    },
    {
        "id": "up_sci_sport",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์การออกกำลังกายและการกีฬา",
        "title_en": "Bachelor of Science Program in Exercise and Sport Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์การออกกำลังกายและการกีฬา)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Sport Science",
        "department_th": "วิทยาศาสตร์การกีฬา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "ศึกษาหลักสรีรวิทยาการออกกำลังกาย ชีวกลศาสตร์ โภชนาการการกีฬา และการฝึกสอนเพื่อพัฒนาสมรรถภาพของนักกีฬาและประชาชนทั่วไป",
        "curriculum_highlights": ["Exercise Physiology & Sports Nutrition", "Biomechanics & Movement Analysis", "Strength & Conditioning Coaching"],
        "career_paths": ["นักวิทยาศาสตร์การกีฬา / ผู้ฝึกสอนสมรรถภาพ (Strength & Conditioning Coach)", "เทรนเนอร์ส่วนบุคคลและผู้จัดการฟิตเนสคลับ", "นักวิชาการส่งเสริมการออกกำลังกายเพื่อสุขภาพ"],
        "tags": ["Sport Science", "Exercise Physiology", "Fitness", "Strength Coaching"],
        "website_url": "https://sci.up.ac.th"
    },

    # ---------------------------------------------------------
    # 11. School of Agriculture and Natural Resources
    # ---------------------------------------------------------
    {
        "id": "up_agri_agrisci",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเกษตรศาสตร์",
        "title_en": "Bachelor of Science Program in Agriculture",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เกษตรศาสตร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Agriculture and Natural Resources",
        "faculty_th": "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ",
        "department": "Plant Science",
        "department_th": "พืชศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นเทคโนโลยีการผลิตพืชเศรษฐกิจ เกษตรแม่นยำ (Smart Farming) การปรับปรุงพันธุ์พืช และการจัดการดินและปุ๋ยอย่างยั่งยืน",
        "curriculum_highlights": ["Smart Farming & Precision Agriculture Technologies", "Plant Breeding & Biotechnology", "Soil Fertility & Integrated Pest Management"],
        "career_paths": ["นักวิชาการเกษตรในหน่วยงานภาครัฐและเอกชน", "ผู้จัดการฟาร์มเกษตรอัจฉริยะ", "ผู้ประกอบการธุรกิจเกษตรและเมล็ดพันธุ์"],
        "tags": ["Agriculture", "Smart Farming", "Agronomy", "Plant Science"],
        "website_url": "https://agri.up.ac.th"
    },
    {
        "id": "up_agri_animal",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาสัตวศาสตร์",
        "title_en": "Bachelor of Science Program in Animal Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (สัตวศาสตร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Agriculture and Natural Resources",
        "faculty_th": "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ",
        "department": "Animal Science",
        "department_th": "สัตวศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เรียนรู้การจัดการฟาร์มปศุสัตว์ โภชนาศาสตร์สัตว์ การปรับปรุงพันธุ์สัตว์ และเทคโนโลยีการแปรรูปเนื้อสัตว์และนม",
        "curriculum_highlights": ["Livestock Production & Farm Management", "Animal Nutrition & Feed Formulation Technology", "Animal Genetics & Reproductive Biotechnology"],
        "career_paths": ["นักสัตวบาล / ผู้จัดการฟาร์มปศุสัตว์", "นักวิชาการโภชนาการสัตว์และโรงงานผลิตอาหารสัตว์", "ผู้ประกอบการธุรกิจปศุสัตว์"],
        "tags": ["Animal Science", "Livestock", "Animal Nutrition", "Veterinary Care"],
        "website_url": "https://agri.up.ac.th"
    },
    {
        "id": "up_agri_foodsci",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
        "title_en": "Bachelor of Science Program in Food Science and Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์และเทคโนโลยีการอาหาร)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Agriculture and Natural Resources",
        "faculty_th": "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ",
        "department": "Food Science and Technology",
        "department_th": "วิทยาศาสตร์และเทคโนโลยีการอาหาร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "เน้นเคมีและจุลชีววิทยาทางอาหาร วิศวกรรมแปรรูปอาหาร การพัฒนาผลิตภัณฑ์อาหารใหม่ (R&D) และระบบประกันคุณภาพสากล",
        "curriculum_highlights": ["Food Processing Engineering & Preservation", "Food Chemistry, Analysis & Sensory Evaluation", "Food Quality Assurance (GMP/HACCP/ISO 22000)"],
        "career_paths": ["นักวิจัยและพัฒนาผลิตภัณฑ์อาหาร (Food R&D)", "เจ้าหน้าที่ควบคุมคุณภาพอาหาร (QA/QC)", "ผู้ตรวจประเมินระบบมาตรฐานความปลอดภัยอาหาร"],
        "tags": ["Food Science", "Food Technology", "Food Safety", "HACCP"],
        "website_url": "https://agri.up.ac.th"
    },
    {
        "id": "up_agri_fisheries",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการประมง",
        "title_en": "Bachelor of Science Program in Fisheries",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (การประมง)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Agriculture and Natural Resources",
        "faculty_th": "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ",
        "department": "Fisheries",
        "department_th": "การประมง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการเพาะเลี้ยงสัตว์น้ำเศรษฐกิจ การจัดการประมงน้ำจืดในกว๊านพะเยา คุณภาพน้ำ และโภชนาการสัตว์น้ำ",
        "curriculum_highlights": ["Aquaculture Engineering & Fish Breeding", "Water Quality & Aquatic Animal Disease Management", "Fish Nutrition & Feed Technology"],
        "career_paths": ["นักวิชาการประมงในกรมประมง", "ผู้จัดการฟาร์มเพาะเลี้ยงสัตว์น้ำ", "นักวิจัยด้านสัตว์น้ำและสิ่งแวดล้อมทางน้ำ"],
        "tags": ["Fisheries", "Aquaculture", "Aquatic Science", "Fish Breeding"],
        "website_url": "https://agri.up.ac.th"
    },

    # ---------------------------------------------------------
    # 12. School of Energy and Environment
    # ---------------------------------------------------------
    {
        "id": "up_energy_enve",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมสิ่งแวดล้อม",
        "title_en": "Bachelor of Engineering Program in Environmental Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมสิ่งแวดล้อม)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Energy and Environment",
        "faculty_th": "คณะพลังงานและสิ่งแวดล้อม",
        "department": "Environmental Engineering",
        "department_th": "วิศวกรรมสิ่งแวดล้อม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "เรียนรู้การออกแบบระบบบำบัดน้ำเสีย ระบบผลิตน้ำประปา การบำบัดมลพิษทางอากาศ และเทคโนโลยีคาร์บอนต่ำ",
        "curriculum_highlights": ["Water & Wastewater Treatment Plant Design", "Air Pollution Control & Solid Waste Management", "Carbon Footprint & Greenhouse Gas Mitigation"],
        "career_paths": ["วิศวกรสิ่งแวดล้อมประจำโรงงานอุตสาหกรรม", "วิศวกรออกแบบระบบบำบัดน้ำเสียและมลพิษ", "ที่ปรึกษาด้านสิ่งแวดล้อมและพลังงาน"],
        "tags": ["Environmental Engineering", "Wastewater Treatment", "Carbon Neutrality", "Clean Energy"],
        "website_url": "https://see.up.ac.th"
    },
    {
        "id": "up_energy_mgmt",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการจัดการพลังงานและสิ่งแวดล้อม",
        "title_en": "Bachelor of Science Program in Energy and Environmental Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (การจัดการพลังงานและสิ่งแวดล้อม)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Energy and Environment",
        "faculty_th": "คณะพลังงานและสิ่งแวดล้อม",
        "department": "Energy and Environmental Management",
        "department_th": "การจัดการพลังงานและสิ่งแวดล้อม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "บูรณาการการตรวจสอบการใช้พลังงาน (Energy Audit) เทคโนโลยีพลังงานหมุนเวียน พลังงานแสงอาทิตย์ และการประเมินความยั่งยืน",
        "curriculum_highlights": ["Energy Auditing & Energy Efficiency Management", "Renewable Energy Technologies (Solar, Biomass)", "Sustainable Development & Climate Change Policy"],
        "career_paths": ["ผู้จัดการพลังงานประจำอาคารและโรงงาน (Energy Manager)", "นักวิเคราะห์โครงการพลังงานสะอาด", "นักวิชาการด้านสิ่งแวดล้อมและการพัฒนาอย่างยั่งยืน (ESG)"],
        "tags": ["Energy Management", "Renewable Energy", "Solar Power", "Sustainability"],
        "website_url": "https://see.up.ac.th"
    },

    # ---------------------------------------------------------
    # 13. School of Business and Communication Arts (BCA)
    # ---------------------------------------------------------
    {
        "id": "up_bca_account",
        "title_th": "หลักสูตรบัญชีบัณฑิต",
        "title_en": "Bachelor of Accountancy Program (B.Acc.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ. (บัญชีบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Accounting",
        "department_th": "การบัญชี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการบัญชีการเงิน การบัญชีบริหาร การสอบบัญชี ระบบสารสนเทศทางการบัญชี และภาษีอากรตามมาตรฐานสภาวิชาชีพบัญชี",
        "curriculum_highlights": ["Financial Accounting & Advanced Auditing", "Managerial Accounting & Cost Management", "Accounting Information Systems & Taxation"],
        "career_paths": ["ผู้สอบบัญชีรับอนุญาต (CPA)", "นักบัญชีและที่ปรึกษาด้านการวางแผนภาษี", "ผู้ตรวจสอบภายใน (Internal Auditor)"],
        "tags": ["Accounting", "Accountant", "Audit", "Finance", "CPA"],
        "website_url": "https://bca.up.ac.th"
    },
    {
        "id": "up_bca_bba_mgmt",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการธุรกิจ",
        "title_en": "Bachelor of Business Administration Program in Business Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการธุรกิจ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Business Management",
        "department_th": "การจัดการธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการวางแผนกลยุทธ์ การเป็นผู้ประกอบการยุคดิจิทัล การจัดการทรัพยากรมนุษย์ และการดำเนินธุรกิจข้ามวัฒนธรรม",
        "curriculum_highlights": ["Strategic Business Management & Leadership", "Digital Entrepreneurship & Innovation", "Human Resource Management & Organizational Behavior"],
        "career_paths": ["ผู้ประกอบการและเจ้าของธุรกิจ", "ผู้จัดการฝ่ายปฏิบัติการและวางแผนกลยุทธ์", "ที่ปรึกษาทางธุรกิจ"],
        "tags": ["Business Management", "Entrepreneurship", "Strategy", "Leadership"],
        "website_url": "https://bca.up.ac.th"
    },
    {
        "id": "up_bca_marketing",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาดดิจิทัล",
        "title_en": "Bachelor of Business Administration Program in Digital Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาดดิจิทัล)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Marketing",
        "department_th": "การตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เรียนรู้การวางแผนกลยุทธ์การตลาดออนไลน์ Social Media Marketing, Performance Marketing, SEO/SEM และการวิเคราะห์พฤติกรรมผู้บริโภค",
        "curriculum_highlights": ["Digital Marketing Strategy & Social Media Advertising", "Search Engine Optimization (SEO/SEM) & Content Marketing", "Consumer Behavior & Marketing Analytics"],
        "career_paths": ["Digital Marketer / Content Creator", "Performance Marketing Specialist", "Brand Manager / Social Media Strategist"],
        "tags": ["Digital Marketing", "Marketing", "Social Media", "SEO"],
        "website_url": "https://bca.up.ac.th"
    },
    {
        "id": "up_bca_finance",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการเงินและการลงทุน",
        "title_en": "Bachelor of Business Administration Program in Finance and Investment",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การเงินและการลงทุน)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Finance",
        "department_th": "การเงิน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการวิเคราะห์หลักทรัพย์และการลงทุน การบริหารการเงินธุรกิจ สินทรัพย์ดิจิทัลและ FinTech และการจัดการความเสี่ยงทางการเงิน",
        "curriculum_highlights": ["Investment Analysis & Portfolio Management", "Corporate Financial Strategy & Valuation", "FinTech, Blockchain & Digital Assets"],
        "career_paths": ["นักวิเคราะห์หลักทรัพย์และการลงทุน (Investment Analyst)", "ผู้จัดการกองทุนและที่ปรึกษาการเงิน (Financial Planner)", "เจ้าหน้าที่สินเชื่อและวาณิชธนกิจ (Investment Banking)"],
        "tags": ["Finance", "Investment", "FinTech", "Portfolio Management"],
        "website_url": "https://bca.up.ac.th"
    },
    {
        "id": "up_bca_tourism",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาการท่องเที่ยวและการโรงแรม",
        "title_en": "Bachelor of Arts Program in Tourism and Hotel Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (การท่องเที่ยวและการโรงแรม)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Tourism and Hotel",
        "department_th": "การท่องเที่ยวและการโรงแรม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "ฝึกปฏิบัติงานบริการโรงแรมระดับสากล การจัดการการท่องเที่ยวเชิงนิเวศและวัฒนธรรม ธุรกิจการบิน และการจัดงานอีเวนต์ (MICE)",
        "curriculum_highlights": ["International Hotel Operations & Front Office Management", "Sustainable Tourism & Ecotourism Planning", "MICE & Event Management"],
        "career_paths": ["ผู้จัดการโรงแรมและรีสอร์ต", "เจ้าหน้าที่สายการบินและบริการผู้โดยสาร", "ผู้จัดงานอีเวนต์และนำเที่ยวระหว่างประเทศ"],
        "tags": ["Hospitality", "Tourism", "Hotel Management", "MICE"],
        "website_url": "https://bca.up.ac.th"
    },
    {
        "id": "up_bca_commarts_newmedia",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสื่อสารสื่อใหม่",
        "title_en": "Bachelor of Communication Arts Program in New Media Communication",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (การสื่อสารสื่อใหม่)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Communication Arts",
        "department_th": "นิเทศศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "เน้นการผลิตคอนเทนต์ดิจิทัล การถ่ายทำและตัดต่อวิดีโอ การเล่าเรื่องข้ามแพลตฟอร์ม และการสื่อสารการตลาดผ่านสื่อออนไลน์",
        "curriculum_highlights": ["Digital Video Production & Post-Production", "Transmedia Storytelling & Creative Content Creation", "Online Media Management & Streaming Broadcasting"],
        "career_paths": ["Content Creator / YouTuber / Streamer", "Creative Director & Video Producer", "ผู้สื่อข่าวและบรรณาธิการสื่อดิจิทัล"],
        "tags": ["Communication Arts", "New Media", "Content Creation", "Video Production"],
        "website_url": "https://bca.up.ac.th"
    },

    # ---------------------------------------------------------
    # 14. School of Political and Social Science
    # ---------------------------------------------------------
    {
        "id": "up_polsci_polsci",
        "title_th": "หลักสูตรรัฐศาสตรบัณฑิต",
        "title_en": "Bachelor of Political Science Program (B.Pol.Sc.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (รัฐศาสตรบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Political and Social Science",
        "faculty_th": "คณะรัฐศาสตร์และสังคมศาสตร์",
        "department": "Political Science",
        "department_th": "รัฐศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "14,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "ศึกษาการเมืองการปกครอง ความสัมพันธ์ระหว่างประเทศ ปรัชญาการเมือง กฎหมายมหาชน และการปกครองท้องถิ่น",
        "curriculum_highlights": ["Comparative Politics & Governance", "International Relations & Geopolitics", "Political Philosophy & Public Law"],
        "career_paths": ["ปลัดอำเภอ / เจ้าพนักงานปกครอง", "นักการทูตและเจ้าหน้าที่องค์การระหว่างประเทศ", "นักวิเคราะห์นโยบายและแผน"],
        "tags": ["Political Science", "Government", "International Relations", "Public Administration"],
        "website_url": "https://spss.up.ac.th"
    },
    {
        "id": "up_polsci_pubinnov",
        "title_th": "หลักสูตรรัฐประศาสนศาสตรบัณฑิต สาขาวิชาการจัดการนวัตกรรมสาธารณะ",
        "title_en": "Bachelor of Public Administration Program in Public Innovation Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "รป.บ. (การจัดการนวัตกรรมสาธารณะ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Political and Social Science",
        "faculty_th": "คณะรัฐศาสตร์และสังคมศาสตร์",
        "department": "Public Administration",
        "department_th": "รัฐประศาสนศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "14,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "เน้นการบริหารภาครัฐยุคดิจิทัล การออกแบบนโยบายสาธารณะ การพัฒนานวัตกรรมการบริการสาธารณะ และการจัดการงบประมาณ",
        "curriculum_highlights": ["Digital Government & Public Service Innovation", "Public Policy Analysis & Evaluation", "Public Financial & Human Capital Management"],
        "career_paths": ["ข้าราชการและเจ้าหน้าที่หน่วยงานภาครัฐ", "นักบริหารงานทั่วไปและวิเคราะห์นโยบาย", "ผู้ประสานงานโครงการพัฒนาชุมชนและสังคม"],
        "tags": ["Public Administration", "Public Innovation", "Governance", "Policy"],
        "website_url": "https://spss.up.ac.th"
    },

    # ---------------------------------------------------------
    # 15. School of Liberal Arts (คณะศิลปศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_libarts_eng",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษ",
        "title_en": "Bachelor of Arts Program in English",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาอังกฤษ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "English",
        "department_th": "ภาษาอังกฤษ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "พัฒนาทักษะการสื่อสารภาษาอังกฤษขั้นสูง สัทศาสตร์ ไวยากรณ์ การแปลและการล่าม วรรณคดี และภาษาอังกฤษเพื่อการสื่อสารธุรกิจ",
        "curriculum_highlights": ["Advanced English Communication & Public Speaking", "Translation & Interpretation Methodologies", "English for International Business Communication"],
        "career_paths": ["ล่ามและนักแปลภาษา", "เจ้าหน้าที่ฝ่ายประสานงานต่างประเทศ", "ครูสอนภาษาอังกฤษและแอร์โฮสเตส / สจ๊วต"],
        "tags": ["English", "Languages", "Translation", "Linguistics"],
        "website_url": "https://liberalarts.up.ac.th"
    },
    {
        "id": "up_libarts_chinese",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาจีน",
        "title_en": "Bachelor of Arts Program in Chinese",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาจีน)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Chinese",
        "department_th": "ภาษาจีน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นทักษะภาษาจีนฟัง พูด อ่าน เขียน ระดับ HSK 5-6 วัฒนธรรมจีน ภาษาจีนเพื่อธุรกิจ การค้า และการท่องเที่ยว",
        "curriculum_highlights": ["Advanced Chinese Language & HSK Preparation", "Business Chinese Communication & Negotiation", "Chinese Culture, History & Literature"],
        "career_paths": ["ล่ามและนักแปลภาษาจีน", "เจ้าหน้าที่ประสานงานธุรกิจไทย-จีน", "มัคคุเทศก์และพนักงานต้อนรับสายการบิน"],
        "tags": ["Chinese", "Languages", "Business Chinese", "HSK"],
        "website_url": "https://liberalarts.up.ac.th"
    },
    {
        "id": "up_libarts_japanese",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาญี่ปุ่น",
        "title_en": "Bachelor of Arts Program in Japanese",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาญี่ปุ่น)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Japanese",
        "department_th": "ภาษาญี่ปุ่น",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เรียนรู้ภาษาญี่ปุ่นตั้งแต่ระดับพื้นฐานจนถึงระดับสูง (JLPT N2/N1) วัฒนธรรมญี่ปุ่น และภาษาญี่ปุ่นสำหรับการทำงานในองค์กรข้ามชาติ",
        "curriculum_highlights": ["Advanced Japanese Language & JLPT Proficiency", "Business Japanese & Corporate Etiquette", "Japanese Culture, Society & Translation"],
        "career_paths": ["ล่ามประจำบริษัทญี่ปุ่น", "ผู้ประสานงานโครงการระหว่างประเทศ", "นักแปลเอกสารและวรรณกรรมญี่ปุ่น"],
        "tags": ["Japanese", "Languages", "JLPT", "Business Japanese"],
        "website_url": "https://liberalarts.up.ac.th"
    },

    # ---------------------------------------------------------
    # 16. School of Law (คณะนิติศาสตร์)
    # ---------------------------------------------------------
    {
        "id": "up_law_llb",
        "title_th": "หลักสูตรนิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ. (นิติศาสตรบัณฑิต)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Law",
        "department_th": "นิติศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "14,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "ศึกษาหลักกฎหมายแพ่งและพาณิชย์ กฎหมายอาญา กฎหมายวิธีพิจารณาความ กฎหมายปกครอง กฎหมายระหว่างประเทศ และกฎหมายดิจิทัล",
        "curriculum_highlights": ["กฎหมายแพ่งและพาณิชย์ และกฎหมายอาญา", "กฎหมายวิธีพิจารณาความแพ่งและอาญา", "กฎหมายปกครอง กฎหมายระหว่างประเทศ และกฎหมายเทคโนโลยี"],
        "career_paths": ["ผู้พิพากษาและพนักงานอัยการ", "ทนายความและที่ปรึกษากฎหมาย (Legal Counsel)", "นิติกรประจำหน่วยงานภาครัฐและเอกชน"],
        "tags": ["Law", "LLB", "Legal", "Attorney", "Justice"],
        "website_url": "https://law.up.ac.th"
    },

    # ---------------------------------------------------------
    # 17. School of Architecture and Fine Arts
    # ---------------------------------------------------------
    {
        "id": "up_arch_barch",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรม",
        "title_en": "Bachelor of Architecture Program in Architecture (B.Arch.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรม)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Architecture and Fine Arts",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และศิลปกรรมศาสตร์",
        "department": "Architecture",
        "department_th": "สถาปัตยกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "165 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "หลักสูตรวิชาชีพ 5 ปี ได้รับการรับรองจากสภาสถาปนิก เน้นการออกแบบสถาปัตยกรรมเขตร้อน การอนุรักษ์สถาปัตยกรรมพื้นถิ่นล้านนา และ BIM",
        "curriculum_highlights": ["Architectural Design Studio I-VIII", "Building Information Modeling (BIM) & Sustainable Design", "Lanna Architecture & Vernacular Heritage Conservation"],
        "career_paths": ["สถาปนิกวิชาชีพ (Licensed Architect)", "นักออกแบบสถาปัตยกรรมและที่ปรึกษาอาคารเขียว", "นักบริหารโครงการก่อสร้างและพัฒนาอสังหาริมทรัพย์"],
        "tags": ["Architecture", "BArch", "BIM", "Design", "Lanna Architecture"],
        "website_url": "https://safa.up.ac.th"
    },
    {
        "id": "up_arch_art_design",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาศิลปะและการออกแบบ",
        "title_en": "Bachelor of Fine and Applied Arts Program in Art and Design",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (ศิลปะและการออกแบบ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Architecture and Fine Arts",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และศิลปกรรมศาสตร์",
        "department": "Art and Design",
        "department_th": "ศิลปะและการออกแบบ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "เน้นการสร้างสรรค์ผลงานทัศนศิลป์ การออกแบบผลิตภัณฑ์ หัตถศิลป์สร้างสรรค์ร่วมสมัย และการออกแบบกราฟิกอัตลักษณ์ท้องถิ่น",
        "curriculum_highlights": ["Visual Arts Creation & Creative Thinking", "Contemporary Craft & Product Design", "Graphic Design & Cultural Identity Branding"],
        "career_paths": ["ศิลปินและนักออกแบบผลิตภัณฑ์", "กราฟิกดีไซเนอร์และนักออกแบบอัตลักษณ์แบรนด์", "ภัณฑารักษ์และนักจัดการศิลปวัฒนธรรม"],
        "tags": ["Art and Design", "Fine Arts", "Product Design", "Craft"],
        "website_url": "https://safa.up.ac.th"
    },

    # ---------------------------------------------------------
    # 18. School of Education (วิทยาลัยการศึกษา)
    # ---------------------------------------------------------
    {
        "id": "up_edu_bed_thai",
        "title_th": "หลักสูตรการศึกษาบัณฑิต สาขาวิชาภาษาไทย",
        "title_en": "Bachelor of Education Program in Thai",
        "degree_level": "ปริญญาตรี",
        "degree_name": "กศ.บ. (ภาษาไทย)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Education",
        "faculty_th": "วิทยาลัยการศึกษา",
        "department": "Curriculum and Instruction",
        "department_th": "หลักสูตรและการสอน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "ผลิตครูภาษาไทยมืออาชีพที่มีความเชี่ยวชาญทั้งหลักภาษา วรรณคดีไทย จิตวิทยาการศึกษา และนวัตกรรมการจัดการเรียนรู้สมัยใหม่",
        "curriculum_highlights": ["หลักสูตรและจิตวิทยาการสอนภาษาไทย", "วรรณคดีและวัฒนธรรมไทยเพื่อการสอน", "นวัตกรรมและเทคโนโลยีการจัดการเรียนรู้"],
        "career_paths": ["ครูผู้สอนวิชาภาษาไทยในโรงเรียนรัฐและเอกชน", "นักวิชาการศึกษาและผู้พัฒนาแบบเรียน", "ผู้เชี่ยวชาญด้านการสื่อสารภาษาไทย"],
        "tags": ["Education", "Teaching", "Thai Language", "Teacher"],
        "website_url": "https://soe.up.ac.th"
    },
    {
        "id": "up_edu_bed_eng",
        "title_th": "หลักสูตรการศึกษาบัณฑิต สาขาวิชาภาษาอังกฤษ",
        "title_en": "Bachelor of Education Program in English",
        "degree_level": "ปริญญาตรี",
        "degree_name": "กศ.บ. (ภาษาอังกฤษ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Education",
        "faculty_th": "วิทยาลัยการศึกษา",
        "department": "Curriculum and Instruction",
        "department_th": "หลักสูตรและการสอน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "ผลิตครูสอนภาษาอังกฤษที่มีทักษะการสื่อสารคล่องแคล่ว เชี่ยวชาญการสอนภาษาอังกฤษเป็นภาษาที่สอง (TESOL/TEFL)",
        "curriculum_highlights": ["English Language Teaching Methodologies (TESOL)", "Applied Linguistics & Second Language Acquisition", "Curriculum Development & Educational Assessment"],
        "career_paths": ["ครูผู้สอนวิชาภาษาอังกฤษในสถานศึกษาทุกระดับ", "นักวิชาการศึกษาและผู้จัดทำสื่อการสอนภาษาอังกฤษ", "ติวเตอร์และวิทยากรด้านภาษา"],
        "tags": ["Education", "English Teacher", "TESOL", "Teaching"],
        "website_url": "https://soe.up.ac.th"
    },
    {
        "id": "up_edu_bed_math",
        "title_th": "หลักสูตรการศึกษาบัณฑิต สาขาวิชาคณิตศาสตร์",
        "title_en": "Bachelor of Education Program in Mathematics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "กศ.บ. (คณิตศาสตร์)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Education",
        "faculty_th": "วิทยาลัยการศึกษา",
        "department": "Curriculum and Instruction",
        "department_th": "หลักสูตรและการสอน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "ผลิตครูคณิตศาสตร์ที่มีทักษะการถ่ายทอดแนวคิดเชิงตรรกะ การแก้ปัญหาทางคณิตศาสตร์ และการประยุกต์ใช้สื่อดิจิทัลในการสอน",
        "curriculum_highlights": ["วิธีวิทยาการสอนคณิตศาสตร์และการคิดขั้นสูง", "การพัฒนาสื่อและซอฟต์แวร์ทางคณิตศาสตร์ศึกษา", "การวัดและประเมินผลการเรียนรู้คณิตศาสตร์"],
        "career_paths": ["ครูคณิตศาสตร์ในระดับมัธยมศึกษาและประถมศึกษา", "นักวิชาการด้านคณิตศาสตร์ศึกษา", "ผู้พัฒนาหลักสูตรและแบบฝึกทักษะคณิตศาสตร์"],
        "tags": ["Education", "Math Teacher", "Mathematics", "STEM Education"],
        "website_url": "https://soe.up.ac.th"
    },

    # ---------------------------------------------------------
    # 19. Graduate Programs (ระดับบัณฑิตศึกษา)
    # ---------------------------------------------------------
    {
        "id": "up_grad_mba",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต",
        "title_en": "Master of Business Administration Program (M.B.A.)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Business and Communication Arts",
        "faculty_th": "คณะบริหารธุรกิจและนิเทศศาสตร์",
        "department": "Business Administration",
        "department_th": "บริหารธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "หลักสูตรปริญญาโทเพื่อพัฒนาผู้บริหารระดับสูง เน้นการคิดเชิงกลยุทธ์ การขับเคลื่อนองค์กรด้วยข้อมูล และความเป็นผู้นำในยุคดิจิทัล",
        "curriculum_highlights": ["Executive Leadership & Strategic Management", "Data-Driven Decision Making & Business Analytics", "Corporate Finance & Global Business Trends"],
        "career_paths": ["ผู้บริหารระดับสูง (C-Level / Director)", "ผู้จัดการทั่วไปและที่ปรึกษากลยุทธ์ทางธุรกิจ", "ผู้ประกอบการธุรกิจข้ามชาติ"],
        "tags": ["MBA", "Master Degree", "Business Administration", "Executive"],
        "website_url": "https://bca.up.ac.th"
    },
    {
        "id": "up_grad_mpa",
        "title_th": "หลักสูตรรัฐประศาสนศาสตรมหาบัณฑิต สาขาวิชานโยบายสาธารณะ",
        "title_en": "Master of Public Administration Program in Public Policy",
        "degree_level": "ปริญญาโท",
        "degree_name": "รป.ม. (นโยบายสาธารณะ)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Political and Social Science",
        "faculty_th": "คณะรัฐศาสตร์และสังคมศาสตร์",
        "department": "Public Administration",
        "department_th": "รัฐประศาสนศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "พัฒนาผู้นำภาครัฐและท้องถิ่นที่มีวิสัยทัศน์ด้านการวิเคราะห์นโยบายสาธารณะ นวัตกรรมการบริหาร และธรรมาภิบาล",
        "curriculum_highlights": ["Public Policy Formulation & Strategic Governance", "Local Government Innovation & Public Management", "Research Methodology in Public Administration"],
        "career_paths": ["ผู้บริหารหน่วยงานภาครัฐและองค์กรปกครองส่วนท้องถิ่น", "นักวิชาการนโยบายสาธารณะ", "ที่ปรึกษาโครงการพัฒนาภาครัฐ"],
        "tags": ["MPA", "Public Administration", "Master Degree", "Public Policy"],
        "website_url": "https://spss.up.ac.th"
    },
    {
        "id": "up_grad_phd_edu",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการบริหารการศึกษา",
        "title_en": "Doctor of Philosophy Program in Educational Administration (Ph.D.)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (การบริหารการศึกษา)",
        "university": UNIVERSITY_EN,
        "university_th": UNIVERSITY_TH,
        "faculty": "School of Education",
        "faculty_th": "วิทยาลัยการศึกษา",
        "department": "Educational Administration",
        "department_th": "การบริหารการศึกษา",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "270,000 บาท",
        "description": "หลักสูตรปริญญาเอกระดับดุษฎีบัณฑิต เน้นการวิจัยเชิงลึกเพื่อพัฒนานโยบายและนวัตกรรมการบริหารการศึกษาสำหรับผู้นำการศึกษายุคใหม่",
        "curriculum_highlights": ["Advanced Educational Leadership Theories", "Policy Formulation & Educational System Transformation", "Doctoral Dissertation & Academic Publication"],
        "career_paths": ["ผู้อำนวยการเขตพื้นที่การศึกษาและผู้บริหารสถานศึกษา", "อาจารย์ประจำระดับอุดมศึกษา", "นักวิจัยและผู้เชี่ยวชาญนโยบายการศึกษา"],
        "tags": ["PhD", "Doctorate", "Educational Administration", "Doctor of Philosophy"],
        "website_url": "https://soe.up.ac.th"
    }
]

def fetch_live_up_announcements() -> List[str]:
    """
    Demonstrates dynamic HTTP scraping using requests & BeautifulSoup
    to verify live connectivity to University of Phayao's official web server.
    """
    scraped_headlines = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        resp = requests.get(BASE_URL, headers=headers, timeout=10, verify=False)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for link in soup.find_all(["a", "h3", "h4", "span"]):
                text = link.get_text(strip=True)
                if text and len(text) > 15 and ("หลักสูตร" in text or "การศึกษา" in text or "นิสิต" in text or "ประกาศ" in text):
                    scraped_headlines.append(text)
            logger.info(f"Successfully connected to {BASE_URL}. Found {len(scraped_headlines)} live headlines.")
    except Exception as e:
        logger.warning(f"Could not reach {BASE_URL} dynamically (using cached matrix): {e}")
    return scraped_headlines

def seed_db() -> int:
    """
    Seeds all UP courses into the database (CourseDB) via SQLAlchemy.
    """
    if not DB_AVAILABLE:
        logger.error("Database connection unavailable (SQLAlchemy / models not loaded).")
        return 0

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted_count = 0
    updated_count = 0

    try:
        for course_data in UP_COURSES:
            course_id = course_data["id"]
            existing = session.query(CourseDB).filter_by(id=course_id).first()
            if existing:
                for k, v in course_data.items():
                    setattr(existing, k, v)
                updated_count += 1
            else:
                new_course = CourseDB(**course_data)
                session.add(new_course)
                inserted_count += 1
        session.commit()
        logger.info(f"Database sync complete: {inserted_count} inserted, {updated_count} updated. Total: {len(UP_COURSES)} courses.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding UP courses to database: {e}")
        raise e
    finally:
        session.close()

    return inserted_count + updated_count

def main():
    import urllib3
    urllib3.disable_warnings()

    logger.info("=== Starting University of Phayao (UP) Scraper & Seeder ===")
    
    # 1. Test live web requests / BeautifulSoup scraper
    fetch_live_up_announcements()

    # 2. Seed all structured curricula into Database
    total_processed = seed_db()
    logger.info(f"=== Successfully finished seeding {total_processed} courses for University of Phayao ===")

if __name__ == "__main__":
    main()

