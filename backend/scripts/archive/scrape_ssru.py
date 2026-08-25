"""
Comprehensive Scraper and Course Data Pipeline for Suan Sunandha Rajabhat University (SSRU)
มหาวิทยาลัยราชภัฏสวนสุนันทา
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
logger = logging.getLogger("SSRU_Scraper")

SSRU_COURSES = [
    # คณะครุศาสตร์
    {
        "id": "ssru_edu_thai",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาภาษาไทย",
        "title_en": "Bachelor of Education Program in Thai Language",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (ภาษาไทย)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Thai Language Education",
        "department_th": "สาขาวิชาภาษาไทย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "หลักสูตรผลิตครูภาษาไทยที่มีความเชี่ยวชาญด้านภาษา วรรณคดี และเทคนิคการจัดการเรียนรู้ภาษาไทยสมัยใหม่",
        "curriculum_highlights": ["หลักและทักษะภาษาไทย", "วรรณคดีและวรรณกรรมศึกษา", "นวัตกรรมและเทคโนโลยีการสอนภาษาไทย", "การวิจัยในชั้นเรียน"],
        "career_paths": ["ครูผู้สอนภาษาไทย", "นักวิชาการศึกษา", "นักเขียน/บรรณาธิการ", "ผู้ผลิตสื่อนวัตกรรมการศึกษา"],
        "tags": ["ครุศาสตร์", "ภาษาไทย", "การศึกษา", "วิชาชีพครู"],
        "website_url": "https://edu.ssru.ac.th"
    },
    {
        "id": "ssru_edu_eng",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษ",
        "title_en": "Bachelor of Education Program in English",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (ภาษาอังกฤษ)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "English Education",
        "department_th": "สาขาวิชาภาษาอังกฤษ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "15,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "มุ่งเน้นพัฒนาทักษะภาษาอังกฤษเชิงวิชาการ การสอนภาษาอังกฤษเป็นภาษาต่างประเทศ และการใช้สื่อดิจิทัลในการสอน",
        "curriculum_highlights": ["English Linguistics for Teachers", "Second Language Acquisition", "Innovative English Teaching Methods", "Classroom Action Research"],
        "career_paths": ["ครูภาษาอังกฤษ", "นักพัฒนาหลักสูตรภาษาอังกฤษ", "ติวเตอร์วิชาการ", "เจ้าหน้าที่วิเทศสัมพันธ์"],
        "tags": ["ครุศาสตร์", "ภาษาอังกฤษ", "English Teaching", "Education"],
        "website_url": "https://edu.ssru.ac.th"
    },
    {
        "id": "ssru_edu_earlychildhood",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาการศึกษาปฐมวัย",
        "title_en": "Bachelor of Education Program in Early Childhood Education",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (การศึกษาปฐมวัย)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Early Childhood Education",
        "department_th": "สาขาวิชาการศึกษาปฐมวัย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "เน้นจิตวิทยาพัฒนาการเด็กปฐมวัย การออกแบบกิจกรรมการเรียนรู้ผ่านการเล่น และการจัดสภาพแวดล้อมเพื่อส่งเสริมศักยภาพเด็ก",
        "curriculum_highlights": ["จิตวิทยาพัฒนาการเด็กปฐมวัย", "การจัดประสบการณ์เรียนรู้ผ่านการเล่น", "การประเมินพัฒนาการเด็ก", "การบริหารสถานศึกษาปฐมวัย"],
        "career_paths": ["ครูปฐมวัย/อนุบาล", "ผู้เชี่ยวชาญการส่งเสริมพัฒนาการเด็ก", "ผู้บริหารสถานรับเลี้ยงเด็กปฐมวัย"],
        "tags": ["การศึกษาปฐมวัย", "ครูปฐมวัย", "จิตวิทยาเด็ก", "Early Childhood"],
        "website_url": "https://edu.ssru.ac.th"
    },
    {
        "id": "ssru_edu_math",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์",
        "title_en": "Bachelor of Education Program in Mathematics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (คณิตศาสตร์)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Mathematics Education",
        "department_th": "สาขาวิชาคณิตศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "14,500 บาท",
        "tuition_total": "116,000 บาท",
        "description": "พัฒนาทักษะการคิดเชิงคณิตศาสตร์ กระบวนการแก้ปัญหา และนวัตกรรมการจัดกิจกรรมการเรียนรู้คณิตศาสตร์",
        "curriculum_highlights": ["แคลคูลัสและพีชคณิตนามธรรม", "เรขาคณิตและการพิสูจน์", "นวัตกรรมการสอนคณิตศาสตร์", "การใช้ซอฟต์แวร์คณิตศาสตร์"],
        "career_paths": ["ครูคณิตศาสตร์", "นักวิชาการคณิตศาสตร์ศึกษา", "ผู้พัฒนาสื่อการสอนคณิตศาสตร์"],
        "tags": ["ครุศาสตร์", "คณิตศาสตร์", "STEM", "Mathematics Education"],
        "website_url": "https://edu.ssru.ac.th"
    },

    # คณะวิทยาศาสตร์และเทคโนโลยี
    {
        "id": "ssru_sci_cs",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และนวัตกรรมข้อมูล",
        "title_en": "Bachelor of Science in Computer Science and Data Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์และนวัตกรรมข้อมูล)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "16,500 บาท",
        "tuition_total": "132,000 บาท",
        "description": "เน้นการพัฒนาซอฟต์แวร์ ปัญญาประดิษฐ์ วิทยาการข้อมูล คลาวด์คอมพิวติง และความมั่นคงปลอดภัยไซเบอร์",
        "curriculum_highlights": ["Data Structures & Algorithms", "Full Stack Development", "Applied Artificial Intelligence", "Cloud Computing & DevOps", "Cybersecurity Essentials"],
        "career_paths": ["Software Engineer", "Full-Stack Developer", "Data Analyst", "AI Practitioner", "System Administrator"],
        "tags": ["Computer Science", "Software Engineering", "AI", "Data Science", "IT"],
        "website_url": "https://sci.ssru.ac.th"
    },
    {
        "id": "ssru_sci_it",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science in Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศ)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "เน้นการออกแบบและบริหารจัดการระบบเทคโนโลยีสารสนเทศ เครือข่ายคอมพิวเตอร์ และการพัฒนาเว็บแอปพลิเคชันเชิงธุรกิจ",
        "curriculum_highlights": ["Network Infrastructure", "Database Management Systems", "Web Application Frameworks", "IT Project Management"],
        "career_paths": ["Network Engineer", "IT Support Specialist", "Database Administrator", "Web Developer"],
        "tags": ["Information Technology", "Networking", "Database", "Web Development"],
        "website_url": "https://sci.ssru.ac.th"
    },
    {
        "id": "ssru_sci_forensic",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชานิติวิทยาศาสตร์",
        "title_en": "Bachelor of Science in Forensic Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (นิติวิทยาศาสตร์)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Forensic Science",
        "department_th": "สาขาวิชานิติวิทยาศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "ศึกษาการประยุกต์ใช้วิทยาศาสตร์ในการตรวจพิสูจน์พยานหลักฐาน การตรวจดีเอ็นเอ สารพิษ และนิติวิทยาศาสตร์ดิจิทัล",
        "curriculum_highlights": ["Crime Scene Investigation", "Forensic DNA Analysis", "Forensic Toxicology", "Digital Forensics & Cyber Evidence"],
        "career_paths": ["นักนิติวิทยาศาสตร์", "เจ้าหน้าที่พิสูจน์หลักฐาน", "นักวิจัยทางนิติวิทยาศาสตร์", "ผู้เชี่ยวชาญการตรวจพิสูจน์ทางวิทยาศาสตร์"],
        "tags": ["Forensic Science", "นิติวิทยาศาสตร์", "Investigation", "Science"],
        "website_url": "https://sci.ssru.ac.th"
    },

    # วิทยาลัยนิเทศศาสตร์
    {
        "id": "ssru_commarts_film",
        "title_th": "นิเทศศาสตรบัณฑิต สาขาวิชาภาพยนตร์และสื่อดิจิทัล",
        "title_en": "Bachelor of Communication Arts in Film and Digital Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (ภาพยนตร์และสื่อดิจิทัล)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "College of Communication Arts",
        "faculty_th": "วิทยาลัยนิเทศศาสตร์",
        "department": "Film and Digital Media",
        "department_th": "สาขาวิชาภาพยนตร์และสื่อดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "18,500 บาท",
        "tuition_total": "148,000 บาท",
        "description": "เน้นกระบวนการผลิตภาพยนตร์ตั้งแต่การเขียนบท การกำกับ การถ่ายทำ ตัดต่อ สเปเชียลเอฟเฟกต์ และการบริหารจัดการสื่อภาพยนตร์",
        "curriculum_highlights": ["Screenwriting & Directing", "Cinematography & Lighting", "Digital Video Editing & VFX", "Film Business & Marketing"],
        "career_paths": ["ผู้กำกับภาพยนตร์", "นักเขียนบท", "ผู้กำกับภาพ", "นักตัดต่อและทำเอฟเฟกต์", "ผู้ผลิตคอนเทนต์วิดีโอ"],
        "tags": ["Communication Arts", "Film Production", "Cinematography", "Digital Media"],
        "website_url": "https://cca.ssru.ac.th"
    },
    {
        "id": "ssru_commarts_advertising",
        "title_th": "นิเทศศาสตรบัณฑิต สาขาวิชาการโฆษณาและการสื่อสารการตลาดดิจิทัล",
        "title_en": "Bachelor of Communication Arts in Advertising and Digital Marketing Communication",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (การโฆษณาและการสื่อสารการตลาดดิจิทัล)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "College of Communication Arts",
        "faculty_th": "วิทยาลัยนิเทศศาสตร์",
        "department": "Advertising and Digital Marketing Communication",
        "department_th": "สาขาวิชาการโฆษณาและการสื่อสารการตลาดดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "17,500 บาท",
        "tuition_total": "140,000 บาท",
        "description": "เน้นการวางแผนกลยุทธ์การสื่อสารแบรนด์ การสร้างสรรค์แคมเปญโฆษณา การตลาดดิจิทัล และการวิเคราะห์สื่อออนไลน์",
        "curriculum_highlights": ["Creative Advertising Design", "Digital Marketing Strategy", "Brand Communications", "Social Media Analytics"],
        "career_paths": ["Digital Marketer", "Creative Copywriter", "Brand Strategist", "Media Planner", "Content Strategist"],
        "tags": ["Advertising", "Digital Marketing", "Branding", "Communication Arts"],
        "website_url": "https://cca.ssru.ac.th"
    },

    # คณะวิทยาการจัดการ
    {
        "id": "ssru_fms_marketing",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการตลาดดิจิทัล",
        "title_en": "Bachelor of Business Administration in Digital Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาดดิจิทัล)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Management Science",
        "faculty_th": "คณะวิทยาการจัดการ",
        "department": "Marketing",
        "department_th": "สาขาวิชาการตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "15,500 บาท",
        "tuition_total": "124,000 บาท",
        "description": "พัฒนาทักษะการตลาดสมัยใหม่ การตลาดบนแพลตฟอร์มอีคอมเมิร์ซ การวิเคราะห์พฤติกรรมผู้บริโภคยุคดิจิทัล และการยิงแอดโฆษณา",
        "curriculum_highlights": ["Consumer Behavior Analysis", "E-Commerce Strategy", "Search Engine Optimization (SEO/SEM)", "Data-Driven Marketing"],
        "career_paths": ["นักการตลาดดิจิทัล", "นักวางแผนกลยุทธ์การตลาด", "ผู้จัดการร้านค้าออนไลน์/E-commerce Specialist", "นักวิเคราะห์การตลาด"],
        "tags": ["Business", "Marketing", "E-Commerce", "Digital Marketing"],
        "website_url": "https://fms.ssru.ac.th"
    },
    {
        "id": "ssru_fms_account",
        "title_th": "บัญชีบัณฑิต",
        "title_en": "Bachelor of Accountancy",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ. (การบัญชี)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Management Science",
        "faculty_th": "คณะวิทยาการจัดการ",
        "department": "Accounting",
        "department_th": "สาขาวิชาการบัญชี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "15,500 บาท",
        "tuition_total": "124,000 บาท",
        "description": "เน้นมาตรฐานการบัญชีไทยและสากล การตรวจสอบบัญชี การวางระบบบัญชีดิจิทัล และการวางแผนภาษีอากร",
        "curriculum_highlights": ["Financial Accounting & Reporting", "Auditing & Assurance Services", "Taxation Planning", "Accounting Information Systems (AIS)"],
        "career_paths": ["นักบัญชี", "ผู้ตรวจสอบบัญชี (Auditor)", "ที่ปรึกษาภาษีอากร", "ผู้วิเคราะห์การเงิน"],
        "tags": ["Accounting", "Audit", "Finance", "Business"],
        "website_url": "https://fms.ssru.ac.th"
    },

    # วิทยาลัยโลจิสติกส์และซัพพลายเชน
    {
        "id": "ssru_cls_logistics",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และซัพพลายเชน",
        "title_en": "Bachelor of Business Administration in Logistics and Supply Chain Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการโลจิสติกส์และซัพพลายเชน)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "College of Logistics and Supply Chain",
        "faculty_th": "วิทยาลัยโลจิสติกส์และซัพพลายเชน",
        "department": "Logistics and Supply Chain",
        "department_th": "สาขาวิชาการจัดการโลจิสติกส์และซัพพลายเชน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "17,000 บาท",
        "tuition_total": "136,000 บาท",
        "description": "เน้นการวางแผนและจัดการโซ่อุปทาน คลังสินค้า การขนส่งทั้งในและระหว่างประเทศ และระบบเทคโนโลยีโลจิสติกส์อัจฉริยะ",
        "curriculum_highlights": ["Supply Chain Optimization", "Warehouse & Inventory Management", "International Freight Transport", "Smart Logistics Technology"],
        "career_paths": ["Logistics Analyst", "Supply Chain Planner", "Warehouse Manager", "Freight Forwarder Specialist"],
        "tags": ["Logistics", "Supply Chain", "Transportation", "Operations"],
        "website_url": "https://cls.ssru.ac.th"
    },

    # วิทยาลัยพยาบาลและสุขภาพ
    {
        "id": "ssru_nurse_bns",
        "title_th": "พยาบาลศาสตรบัณฑิต",
        "title_en": "Bachelor of Nursing Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พย.บ.",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "College of Nursing and Health",
        "faculty_th": "วิทยาลัยพยาบาลและสุขภาพ",
        "department": "Nursing Science",
        "department_th": "พยาบาลศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "280,000 บาท",
        "description": "ผลิตพยาบาลวิชาชีพที่มีทักษะการพยาบาลแบบองค์รวม ความรู้ทางการแพทย์ และจรรยาบรรณวิชาชีพตามมาตรฐานสภาการพยาบาล",
        "curriculum_highlights": ["Adult & Gerontological Nursing", "Maternal & Child Health", "Community Health Nursing", "Psychiatric & Mental Health Care"],
        "career_paths": ["พยาบาลวิชาชีพในโรงพยาบาลรัฐและเอกชน", "พยาบาลประจำคลินิก/สถานประกอบการ", "พยาบาลชุมชน", "นักวิชาการสาธารณสุข"],
        "tags": ["Nursing", "Health Science", "พยาบาล", "การแพทย์"],
        "website_url": "https://nurse.ssru.ac.th"
    },

    # บัณฑิตวิทยาลัย (ระดับปริญญาโท)
    {
        "id": "ssru_grad_mba",
        "title_th": "บริหารธุรกิจมหาบัณฑิต สาขาวิชาบริหารธุรกิจ",
        "title_en": "Master of Business Administration (MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Graduate School",
        "faculty_th": "บัณฑิตวิทยาลัย",
        "department": "Business Administration",
        "department_th": "สาขาวิชาบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "หลักสูตรระดับปริญญาโทพัฒนาภาวะผู้นำ การบริหารจัดการเชิงกลยุทธ์ นวัตกรรมองค์กร และการวิเคราะห์ธุรกิจขั้นสูง",
        "curriculum_highlights": ["Strategic Management & Leadership", "Financial Decision Making", "Digital Transformation in Business", "Independent Study & Research"],
        "career_paths": ["ผู้บริหารระดับกลางและสูง", "ผู้ประกอบการธุรกิจ", "ที่ปรึกษาธุรกิจ", "นักวิเคราะห์กลยุทธ์องค์กร"],
        "tags": ["MBA", "Business Administration", "Master Degree", "Leadership"],
        "website_url": "https://grad.ssru.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE:
        logger.warning("Database module not available. Writing courses to JSON data file instead.")
        data_path = Path(__file__).resolve().parent / "data" / "ssru_courses.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(SSRU_COURSES, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(SSRU_COURSES)} SSRU courses to {data_path}")
        return

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    try:
        for c in SSRU_COURSES:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
        session.commit()
        logger.info(f"SSRU Seeding completed: {inserted} inserted, {updated} updated.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding SSRU: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_db()
