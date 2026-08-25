"""
Comprehensive Scraper and Course Data Pipeline for Chiang Mai Rajabhat University (CMRU)
มหาวิทยาลัยราชภัฏเชียงใหม่
"""
import sys
import os
import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CMRU_Scraper")

CMRU_COURSES = [
    # คณะครุศาสตร์ (Faculty of Education)
    {
        "id": "cmru_edu_thai",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาภาษาไทย",
        "title_en": "Bachelor of Education Program in Thai Language",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (ภาษาไทย)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Thai Language Education",
        "department_th": "สาขาวิชาภาษาไทย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "13,500 บาท",
        "tuition_total": "108,000 บาท",
        "description": "ผลิตครูภาษาไทยที่มีจิตวิญญาณความเป็นครู มีความรู้ลึกซึ้งในภาษาและวรรณกรรมล้านนา-ไทย และการใช้นวัตกรรมการสอนดิจิทัล",
        "curriculum_highlights": ["ภาษาและวรรณคดีไทย", "วรรณกรรมท้องถิ่นล้านนา", "การจัดการเรียนรู้ภาษาไทยเชิงรุก (Active Learning)", "การปฏิบัติการวิชาชีพครูในสถานศึกษา"],
        "career_paths": ["ครูผู้สอนภาษาไทย", "นักวิชาการศึกษา", "ผู้สร้างสรรค์สื่อการเรียนรู้", "นักเขียนและบรรณาธิการ"],
        "tags": ["ครุศาสตร์", "ภาษาไทย", "ล้านนา", "วิชาชีพครู", "CMRU"],
        "website_url": "https://edu.cmru.ac.th"
    },
    {
        "id": "cmru_edu_eng",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษ",
        "title_en": "Bachelor of Education Program in English",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (ภาษาอังกฤษ)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "English Education",
        "department_th": "สาขาวิชาภาษาอังกฤษ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "14,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "เน้นพัฒนาทักษะภาษาอังกฤษเพื่อการสื่อสารระดับสากล นวัตกรรมการจัดการเรียนการสอนภาษาอังกฤษในยุคดิจิทัล และการฝึกประสบการณ์วิชาชีพครู",
        "curriculum_highlights": ["English Applied Linguistics", "TESOL Methodologies", "Digital Media in English Teaching", "Classroom Research"],
        "career_paths": ["ครูผู้สอนวิชาภาษาอังกฤษ", "วิทยากรด้านภาษาอังกฤษ", "นักพัฒนาสื่อการสอนภาษา", "เจ้าหน้าที่สถาบันภาษา"],
        "tags": ["ครุศาสตร์", "ภาษาอังกฤษ", "TESOL", "English Education"],
        "website_url": "https://edu.cmru.ac.th"
    },
    {
        "id": "cmru_edu_math",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์",
        "title_en": "Bachelor of Education Program in Mathematics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (คณิตศาสตร์)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Mathematics Education",
        "department_th": "สาขาวิชาคณิตศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "13,500 บาท",
        "tuition_total": "108,000 บาท",
        "description": "เสริมสร้างทักษะการคิดเชิงคณิตศาสตร์ ตรรกศาสตร์ การแก้ปัญหาเชิงโครงสร้าง และการจัดการเรียนรู้คณิตศาสตร์ตามแนวคิด STEM Education",
        "curriculum_highlights": ["Mathematical Thinking & Logic", "Calculus and Mathematical Modeling", "STEM-Based Learning Design", "Assessment in Mathematics"],
        "career_paths": ["ครูคณิตศาสตร์", "นักวิชาการวัดและประเมินผลการศึกษา", "นักพัฒนาหลักสูตรคณิตศาสตร์"],
        "tags": ["ครุศาสตร์", "คณิตศาสตร์", "STEM", "Mathematics"],
        "website_url": "https://edu.cmru.ac.th"
    },
    {
        "id": "cmru_edu_earlychildhood",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาการศึกษาปฐมวัย",
        "title_en": "Bachelor of Education Program in Early Childhood Education",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (การศึกษาปฐมวัย)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Early Childhood Education",
        "department_th": "สาขาวิชาการศึกษาปฐมวัย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "13,500 บาท",
        "tuition_total": "108,000 บาท",
        "description": "มุ่งเน้นการดูแลและส่งเสริมพัฒนาการเด็กปฐมวัยแบบองค์รวม การจัดสภาพแวดล้อมที่กระตุ้นการเรียนรู้ และจิตวิทยาพัฒนาการเด็ก",
        "curriculum_highlights": ["Early Childhood Developmental Psychology", "Play-Based Curriculum Design", "Child Healthcare & Nutrition", "Kindergarten Administration"],
        "career_paths": ["ครูระดับปฐมวัยและอนุบาล", "นักวิชาการศึกษาเด็กปฐมวัย", "ผู้บริหารสถานรับเลี้ยงเด็กและศูนย์พัฒนาเด็กเล็ก"],
        "tags": ["ปฐมวัย", "ครูปฐมวัย", "Early Childhood", "Education"],
        "website_url": "https://edu.cmru.ac.th"
    },

    # คณะวิทยาศาสตร์และเทคโนโลยี (Faculty of Science and Technology)
    {
        "id": "cmru_sci_cs",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "15,500 บาท",
        "tuition_total": "124,000 บาท",
        "description": "เน้นการพัฒนาโปรแกรม ซอฟต์แวร์ประยุกต์ ปัญญาประดิษฐ์ วิทยาการข้อมูล การคำนวณแบบคลาวด์ และเทคโนโลยีเว็บสมัยใหม่",
        "curriculum_highlights": ["Algorithm Design & Data Structures", "Software Engineering & Clean Code", "Applied Artificial Intelligence & Machine Learning", "Web & Mobile App Development", "Database Architecture"],
        "career_paths": ["Software Engineer", "Full-Stack Developer", "AI/ML Developer", "System Analyst", "Data Engineer"],
        "tags": ["Computer Science", "Software Engineering", "AI", "Machine Learning", "Tech"],
        "website_url": "https://science.cmru.ac.th"
    },
    {
        "id": "cmru_sci_it",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science in Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศ)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการบริหารจัดการระบบเครือข่าย ระบบแม่ข่าย ความปลอดภัยสารสนเทศ และการพัฒนานวัตกรรมดิจิทัลสำหรับองค์กร",
        "curriculum_highlights": ["Network Infrastructure & Security", "Server & Cloud Administration", "IT Solutions Architecture", "Cybersecurity Operations"],
        "career_paths": ["Network Engineer", "System Administrator", "IT Support Specialist", "Cybersecurity Analyst"],
        "tags": ["Information Technology", "Networking", "Cybersecurity", "IT Infrastructure"],
        "website_url": "https://science.cmru.ac.th"
    },
    {
        "id": "cmru_sci_env",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์สิ่งแวดล้อม",
        "title_en": "Bachelor of Science in Environmental Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์สิ่งแวดล้อม)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Environmental Science",
        "department_th": "สาขาวิชาวิทยาศาสตร์สิ่งแวดล้อม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นการศึกษาการจัดการทรัพยากรธรรมชาติ การตรวจวัดคุณภาพสิ่งแวดล้อม การควบคุมมลพิษ และการจัดการสิ่งแวดล้อมในพื้นที่ภาคเหนือ",
        "curriculum_highlights": ["Environmental Impact Assessment (EIA)", "Air & Water Pollution Control", "Geographic Information Systems (GIS)", "Waste Management & Sustainability"],
        "career_paths": ["นักวิชาการสิ่งแวดล้อม", "เจ้าหน้าที่สิ่งแวดล้อมประจำโรงงาน/องค์กร (จป.วิชาชีพ)", "นักวิจัยด้านนิเวศวิทยา", "ที่ปรึกษาด้านการประเมินผลกระทบสิ่งแวดล้อม"],
        "tags": ["Environmental Science", "Ecology", "Sustainability", "GIS"],
        "website_url": "https://science.cmru.ac.th"
    },

    # คณะมนุษยศาสตร์และสังคมศาสตร์ (Faculty of Humanities and Social Sciences)
    {
        "id": "cmru_hum_tourism",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาการท่องเที่ยวและการบริการ",
        "title_en": "Bachelor of Arts in Tourism and Hospitality",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (การท่องเที่ยวและการบริการ)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Humanities and Social Sciences",
        "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        "department": "Tourism and Hospitality",
        "department_th": "สาขาวิชาการท่องเที่ยวและการบริการ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "ใช้ประโยชน์จากอัตลักษณ์เมืองท่องเที่ยวเชียงใหม่ เน้นการท่องเที่ยวเชิงวัฒนธรรมเชิงนิเวศ มัคคุเทศก์มืออาชีพ และการจัดการธุรกิจบริการ",
        "curriculum_highlights": ["Cultural & Eco-Tourism Management", "Tour Guiding & Operation (บัตรมัคคุเทศก์)", "Hospitality Service Standards", "Tourism Destination Marketing"],
        "career_paths": ["มัคคุเทศก์ (Tour Guide)", "ผู้ประกอบการธุรกิจนำเที่ยว", "เจ้าหน้าที่ประสานงานการท่องเที่ยว", "ผู้บริหารงานบริการในโรงแรม"],
        "tags": ["Tourism", "Hospitality", "Chiang Mai", "Tour Guide", "Travel"],
        "website_url": "https://human.cmru.ac.th"
    },
    {
        "id": "cmru_hum_chinese",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาภาษาจีน",
        "title_en": "Bachelor of Arts Program in Chinese",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาจีน)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Humanities and Social Sciences",
        "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        "department": "Chinese Language",
        "department_th": "สาขาวิชาภาษาจีน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "เน้นทักษะภาษาจีนระดับสูง ภาษาจีนเพื่อธุรกิจ การแปล ล่าม และความรู้ทางวัฒนธรรมจีน พร้อมโอกาสแลกเปลี่ยนกับมหาวิทยาลัยในประเทศจีน",
        "curriculum_highlights": ["Advanced Chinese Communication", "Business Chinese", "Translation & Interpretation", "Chinese Culture and Society"],
        "career_paths": ["ล่ามและนักแปลภาษาจีน", "เจ้าหน้าที่ประสานงานธุรกิจไทย-จีน", "เจ้าหน้าที่วิเทศสัมพันธ์", "ไกด์ภาษาจีน"],
        "tags": ["Chinese Language", "Business Chinese", "Translation", "Humanities"],
        "website_url": "https://human.cmru.ac.th"
    },
    {
        "id": "cmru_hum_polsci",
        "title_th": "รัฐประศาสนศาสตรบัณฑิต",
        "title_en": "Bachelor of Public Administration",
        "degree_level": "ปริญญาตรี",
        "degree_name": "รป.บ.",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Humanities and Social Sciences",
        "faculty_th": "คณะมนุษยศาสตร์และสังคมศาสตร์",
        "department": "Public Administration",
        "department_th": "สาขาวิชารัฐประศาสนศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "13,500 บาท",
        "tuition_total": "108,000 บาท",
        "description": "พัฒนาความรู้ด้านการบริหารงานภาครัฐ การกำหนดและวิเคราะห์นโยบายสาธารณะ การบริหารทรัพยากรมนุษย์ และการปกครองส่วนท้องถิ่น",
        "curriculum_highlights": ["Public Policy Formulation & Analysis", "Local Governance Administration", "Human Resource Management in Public Sector", "Public Financial Management"],
        "career_paths": ["ปลัดอำเภอ", "นักวิเคราะห์นโยบายและแผน", "ข้าราชการองค์กรปกครองส่วนท้องถิ่น (อปท.)", "เจ้าหน้าที่บริหารงานบุคคลภาครัฐ"],
        "tags": ["Public Administration", "รัฐประศาสนศาสตร์", "ข้าราชการ", "นโยบายสาธารณะ"],
        "website_url": "https://human.cmru.ac.th"
    },

    # คณะวิทยาการจัดการ (Faculty of Management Science)
    {
        "id": "cmru_fms_digital_biz",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการจัดการธุรกิจดิจิทัล",
        "title_en": "Bachelor of Business Administration in Digital Business Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการธุรกิจดิจิทัล)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Management Science",
        "faculty_th": "คณะวิทยาการจัดการ",
        "department": "Digital Business Management",
        "department_th": "สาขาวิชาการจัดการธุรกิจดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "เรียนรู้การวางกลยุทธ์ธุรกิจดิจิทัล การตลาดออนไลน์ การบริหารแพลตฟอร์มอีคอมเมิร์ซ และการสร้างโมเดลธุรกิจสตาร์ทอัพ",
        "curriculum_highlights": ["Digital Business Model Innovation", "E-Commerce Logistics & Operations", "Digital Marketing & CRM", "Data Analytics for Business Decisions"],
        "career_paths": ["Digital Business Developer", "E-Commerce Manager", "ผู้ประกอบการดิจิทัล/Start-up Founder", "Online Marketing Specialist"],
        "tags": ["Digital Business", "E-Commerce", "Marketing", "Management"],
        "website_url": "https://fms.cmru.ac.th"
    },
    {
        "id": "cmru_fms_account",
        "title_th": "บัญชีบัณฑิต",
        "title_en": "Bachelor of Accountancy",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ. (การบัญชี)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Management Science",
        "faculty_th": "คณะวิทยาการจัดการ",
        "department": "Accounting",
        "department_th": "สาขาวิชาการบัญชี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "14,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "เน้นมาตรฐานการรายงานทางการเงิน การสอบบัญชี ระบบสารสนเทศทางการบัญชี และการวางแผนภาษีอากรสำหรับธุรกิจยุคใหม่",
        "curriculum_highlights": ["Financial Accounting & Reporting", "Auditing Standards & Practice", "Managerial Accounting", "Tax Law & Tax Planning"],
        "career_paths": ["นักบัญชี", "ผู้ตรวจสอบบัญชี", "ที่ปรึกษาทางการเงินและภาษี", "นักวิเคราะห์งบการเงิน"],
        "tags": ["Accounting", "Audit", "Finance", "Business"],
        "website_url": "https://fms.cmru.ac.th"
    },

    # คณะเทคโนโลยีการเกษตร (Faculty of Agricultural Technology)
    {
        "id": "cmru_agri_smart",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเกษตรศาสตร์และนวัตกรรมเกษตร",
        "title_en": "Bachelor of Science in Agriculture and Agricultural Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เกษตรศาสตร์และนวัตกรรมเกษตร)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Agricultural Technology",
        "faculty_th": "คณะเทคโนโลยีการเกษตร",
        "department": "Agriculture and Agricultural Innovation",
        "department_th": "สาขาวิชาเกษตรศาสตร์และนวัตกรรมเกษตร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "เน้นการทำเกษตรอัจฉริยะ (Smart Farming) การใช้เทคโนโลยีไอโอทีในการเพาะปลูก เทคโนโลยีหลังการเก็บเกี่ยว และการแปรรูปผลผลิตเกษตรมูลค่าสูง",
        "curriculum_highlights": ["Smart Farming & IoT Applications", "Precision Agriculture", "Plant Biotechnology & Protection", "Agribusiness & Value Chain Management"],
        "career_paths": ["นักวิชาการเกษตร", "ผู้เชี่ยวชาญเทคโนโลยีสมาร์ทฟาร์ม", "ผู้ประกอบการธุรกิจเกษตรสมัยใหม่", "นักวิจัยด้านการปรับปรุงพันธุ์พืช"],
        "tags": ["Agriculture", "Smart Farming", "AgriTech", "Innovation"],
        "website_url": "https://agri.cmru.ac.th"
    },

    # คณะพยาบาลศาสตร์ (Faculty of Nursing)
    {
        "id": "cmru_nurse_bns",
        "title_th": "พยาบาลศาสตรบัณฑิต",
        "title_en": "Bachelor of Nursing Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พย.บ.",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Nursing Science",
        "department_th": "พยาบาลศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "34,000 บาท",
        "tuition_total": "272,000 บาท",
        "description": "ผลิตพยาบาลวิชาชีพที่มีทักษะการพยาบาลแบบองค์รวม การดูแลสุขภาพชุมชนในเขตพื้นที่ภาคเหนือ และจรรยาบรรณวิชาชีพตามมาตรฐานสภาการพยาบาล",
        "curriculum_highlights": ["Adult & Geriatric Nursing", "Maternal & Child Health Nursing", "Community & Northern Indigenous Healthcare", "Critical & Emergency Care"],
        "career_paths": ["พยาบาลวิชาชีพในโรงพยาบาลรัฐและเอกชน", "พยาบาลประจำคลินิก/โรงพยาบาลส่งเสริมสุขภาพตำบล", "พยาบาลผู้ดูแลผู้สูงอายุ"],
        "tags": ["Nursing", "พยาบาล", "Healthcare", "Medical"],
        "website_url": "https://nurse.cmru.ac.th"
    },

    # บัณฑิตวิทยาลัย (ระดับปริญญาโท)
    {
        "id": "cmru_grad_medu_admin",
        "title_th": "ครุศาสตรมหาบัณฑิต สาขาวิชาการบริหารการศึกษา",
        "title_en": "Master of Education in Educational Administration",
        "degree_level": "ปริญญาโท",
        "degree_name": "ค.ม. (การบริหารการศึกษา)",
        "university": "Chiang Mai Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏเชียงใหม่",
        "faculty": "Graduate School",
        "faculty_th": "บัณฑิตวิทยาลัย",
        "department": "Educational Administration",
        "department_th": "สาขาวิชาการบริหารการศึกษา",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "มุ่งเน้นการเสริมสร้างศักยภาพผู้นำทางวิชาการ การบริหารจัดการสถานศึกษาในยุคดิจิทัล การวางแผนกลยุทธ์ทางการศึกษา และการประกันคุณภาพการศึกษา",
        "curriculum_highlights": ["Strategic Educational Leadership", "School Financial & Resource Management", "Educational Policy Analysis", "Advanced Educational Research & Thesis"],
        "career_paths": ["ผู้อำนวยการสถานศึกษา/ผู้บริหารโรงเรียน", "ศึกษานิเทศก์", "ผู้บริหารการศึกษาในระดับเขตพื้นที่", "นักวิชาการศึกษา"],
        "tags": ["Master of Education", "Educational Administration", "Leadership", "บัณฑิตศึกษา"],
        "website_url": "https://grad.cmru.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE:
        logger.warning("Database module not available. Writing courses to JSON data file instead.")
        data_path = Path(__file__).resolve().parent / "data" / "cmru_courses.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(CMRU_COURSES, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(CMRU_COURSES)} CMRU courses to {data_path}")
        return

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    try:
        for c in CMRU_COURSES:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
        session.commit()
        logger.info(f"CMRU Seeding completed: {inserted} inserted, {updated} updated.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding CMRU: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_db()
