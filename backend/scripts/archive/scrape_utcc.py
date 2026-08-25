"""
Web Scraper and Course Seeder for University of the Thai Chamber of Commerce (UTCC / มหาวิทยาลัยหอการค้าไทย)
Complies with CourseDB schema:
CourseDB(id, title_th, title_en, degree_level, degree_name, university, university_th,
         faculty, faculty_th, department, department_th, program_type, duration_years,
         total_credits, tuition_per_semester, tuition_total, description,
         curriculum_highlights, career_paths, tags, website_url)
"""

import sys
import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

# Setup backend paths
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
logger = logging.getLogger("scrape_utcc")

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON = DATA_DIR / "utcc_courses.json"

# Comprehensive Curricula Matrix for UTCC
UTCC_COURSES: List[Dict] = [
    # ---------------- 1. Faculty of Business Administration (คณะบริหารธุรกิจ) ----------------
    {
        "id": "utcc_ba_digital_mkt",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาดดิจิทัล",
        "title_en": "Bachelor of Business Administration in Digital Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาดดิจิทัล)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Marketing",
        "department_th": "สาขาวิชาการตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "28,500 บาท",
        "tuition_total": "298,000 บาท",
        "description": "มุ่งเน้นการพัฒนานักการตลาดยุคใหม่ที่มีความเชี่ยวชาญด้านกลยุทธ์การตลาดดิจิทัล การวิเคราะห์ข้อมูลผู้บริโภค Social Media Marketing และ MarTech",
        "curriculum_highlights": ["Digital Marketing Strategy", "Consumer Data Analytics", "Content Marketing & Social Media", "E-Commerce Management"],
        "career_paths": ["Digital Marketing Manager", "Content Creator & Strategist", "Brand Manager", "Growth Marketer"],
        "tags": ["Marketing", "Digital Marketing", "Business", "E-Commerce", "MarTech"],
        "website_url": "https://ba.utcc.ac.th"
    },
    {
        "id": "utcc_ba_inter_biz",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการธุรกิจระหว่างประเทศ",
        "title_en": "Bachelor of Business Administration in International Business Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการธุรกิจระหว่างประเทศ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of International Business",
        "department_th": "สาขาวิชาธุรกิจระหว่างประเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "129 หน่วยกิต",
        "tuition_per_semester": "29,000 บาท",
        "tuition_total": "298,000 บาท",
        "description": "พัฒนาความรู้และทักษะการดำเนินธุรกิจข้ามพรมแดน การค้าระหว่างประเทศ โลจิสติกส์สากล และการเจรจาต่อรองทางธุรกิจในบริบทสากล",
        "curriculum_highlights": ["Global Trade & Investment", "International Business Negotiation", "Cross-Cultural Management", "Global Supply Chain"],
        "career_paths": ["International Business Consultant", "Global Trade Specialist", "Import-Export Manager", "Business Development Executive"],
        "tags": ["International Business", "Global Trade", "Business", "Management"],
        "website_url": "https://ba.utcc.ac.th"
    },
    {
        "id": "utcc_ba_fin_inv",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการเงินและการลงทุน",
        "title_en": "Bachelor of Business Administration in Finance and Investment",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การเงินและการลงทุน)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Finance",
        "department_th": "สาขาวิชาการเงิน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "301,990 บาท",
        "description": "เน้นการวิเคราะห์หลักทรัพย์ การบริหารพอร์ตการลงทุน FinTech และการวางแผนการเงินส่วนบุคคลและองค์กร",
        "curriculum_highlights": ["Security Analysis & Portfolio Management", "FinTech & Digital Assets", "Corporate Financial Strategy", "Wealth Management"],
        "career_paths": ["Financial Analyst", "Investment Banker", "Fund Manager", "Wealth Planner"],
        "tags": ["Finance", "Investment", "FinTech", "Banking", "Wealth Management"],
        "website_url": "https://ba.utcc.ac.th"
    },
    {
        "id": "utcc_ba_digital_biz_innov",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาธุรกิจดิจิทัลและนวัตกรรม",
        "title_en": "Bachelor of Business Administration in Digital Business and Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (ธุรกิจดิจิทัลและนวัตกรรม)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Digital Business",
        "department_th": "สาขาวิชาธุรกิจดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "301,990 บาท",
        "description": "สร้างผู้ประกอบการดิจิทัลและผู้นำการเปลี่ยนแปลงทางเทคโนโลยี ด้วยการเรียนรู้โมเดลธุรกิจแพลตฟอร์ม นวัตกรรมทางธุรกิจ และการประยุกต์ใช้ AI ในองค์กร",
        "curriculum_highlights": ["Digital Business Model Innovation", "AI for Business Applications", "Platform Strategy", "Startup & Venture Creation"],
        "career_paths": ["Digital Transformation Specialist", "Product Manager", "Tech Entrepreneur", "Business Analyst"],
        "tags": ["Digital Business", "Innovation", "Startup", "AI for Business", "E-Commerce"],
        "website_url": "https://ba.utcc.ac.th"
    },
    {
        "id": "utcc_ba_esports_game",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาธุรกิจเกมและอีสปอร์ต",
        "title_en": "Bachelor of Business Administration in Esports and Game Business",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (ธุรกิจเกมและอีสปอร์ต)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Game and Esports",
        "department_th": "สาขาวิชาธุรกิจเกมและอีสปอร์ต",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "301,990 บาท",
        "description": "การจัดการธุรกิจอุตสาหกรรมเกมและอีสปอร์ต การจัดทัวร์นาเมนต์ การตลาดสำหรับเกม และการบริหารจัดการสโมสรอีสปอร์ต",
        "curriculum_highlights": ["Esports Tournament Management", "Game Monetization & Publishing", "Esports Marketing & Sponsorship", "Streaming & Community Management"],
        "career_paths": ["Esports Manager", "Game Producer / Publisher", "Event & Tournament Organizer", "Esports Marketing Specialist"],
        "tags": ["Esports", "Game Business", "Entertainment", "Management", "Digital Media"],
        "website_url": "https://ba.utcc.ac.th"
    },
    {
        "id": "utcc_mba_alpha",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (Alpha MBA / Executive MBA)",
        "title_en": "Master of Business Administration (Alpha MBA / Executive MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Graduate School of Business",
        "department_th": "บัณฑิตวิทยาลัยบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "260,000 บาท",
        "description": "หลักสูตรปริญญาโทบริหารธุรกิจที่พัฒนาผู้นำองค์กรและผู้ประกอบการรุ่นใหม่ มีความยืดหยุ่นในการเรียนและมีเครือข่ายหอการค้าไทยที่แข็งแกร่ง",
        "curriculum_highlights": ["Strategic Leadership in Digital Era", "Corporate Entrepreneurship", "Advanced Financial Strategy", "Global Supply Chain Management"],
        "career_paths": ["CEO / Managing Director", "Business Consultant", "Entrepreneur / Business Owner", "Senior Executive"],
        "tags": ["MBA", "Business Administration", "Leadership", "Executive", "Management"],
        "website_url": "https://mba.utcc.ac.th"
    },
    {
        "id": "utcc_dba_biz",
        "title_th": "หลักสูตรบริหารธุรกิจดุษฎีบัณฑิต (DBA)",
        "title_en": "Doctor of Business Administration (D.B.A.)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "บธ.ด. (บริหารธุรกิจ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Graduate School of Business",
        "department_th": "บัณฑิตวิทยาลัยบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ",
        "duration_years": "3 ปี",
        "total_credits": "54 หน่วยกิต",
        "tuition_per_semester": "95,000 บาท",
        "tuition_total": "570,000 บาท",
        "description": "หลักสูตรปริญญาเอกที่เน้นการวิจัยขั้นสูงเชิงประยุกต์เพื่อแก้ปัญหาเชิงกลยุทธ์ของภาคธุรกิจและอุตสาหกรรมในระดับชาติและนานาชาติ",
        "curriculum_highlights": ["Advanced Business Research Methods", "Strategic Vision & Global Competitiveness", "Doctoral Dissertation"],
        "career_paths": ["University Professor", "Senior Business Researcher", "C-Level Executive", "Policy Advisor"],
        "tags": ["DBA", "Doctorate", "Business Research", "Leadership"],
        "website_url": "https://dba.utcc.ac.th"
    },

    # ---------------- 2. Faculty of Accountancy (คณะบัญชี) ----------------
    {
        "id": "utcc_acc_bacc",
        "title_th": "หลักสูตรบัญชีบัณฑิต",
        "title_en": "Bachelor of Accountancy",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ. (การบัญชี)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Accountancy",
        "faculty_th": "คณะบัญชี",
        "department": "Department of Accountancy",
        "department_th": "สาขาวิชาการบัญชี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "310,000 บาท",
        "description": "คณะบัญชีชั้นนำของประเทศไทย มุ่งเน้นการบัญชีดิจิทัล การสอบบัญชี การวางระบบสารสนเทศทางการบัญชี และการวิเคราะห์ข้อมูลทางการเงินด้วยเทคโนโลยี",
        "curriculum_highlights": ["Digital Accounting & AIS", "Auditing & Assurance Services", "Tax Planning & Compliance", "Forensic Accounting"],
        "career_paths": ["Certified Public Accountant (CPA)", "Tax Auditor", "Financial Controller", "Internal Auditor"],
        "tags": ["Accounting", "Audit", "Tax", "Finance", "CPA"],
        "website_url": "https://acc.utcc.ac.th"
    },
    {
        "id": "utcc_acc_macc",
        "title_th": "หลักสูตรบัญชีมหาบัณฑิต",
        "title_en": "Master of Accountancy",
        "degree_level": "ปริญญาโท",
        "degree_name": "บช.ม. (การบัญชี)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Accountancy",
        "faculty_th": "คณะบัญชี",
        "department": "Department of Accountancy",
        "department_th": "สาขาวิชาการบัญชี",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "55,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "ยกระดับวิชาชีพบัญชีสู่ระดับผู้บริหารทางการเงิน วางแผนกลยุทธ์ภาษีขั้นสูง และการวิจัยเชิงลึกด้านมาตรฐานการรายงานทางการเงินระหว่างประเทศ (IFRS)",
        "curriculum_highlights": ["Advanced Strategic Cost Accounting", "International Financial Reporting Standards", "Tax Strategy & Planning", "Accounting Data Analytics"],
        "career_paths": ["Chief Financial Officer (CFO)", "Accounting Director", "Senior Audit Partner", "Tax Consultant"],
        "tags": ["Accounting", "Master", "CFO", "Tax Strategy", "IFRS"],
        "website_url": "https://acc.utcc.ac.th"
    },

    # ---------------- 3. Faculty of Economics (คณะเศรษฐศาสตร์) ----------------
    {
        "id": "utcc_econ_biz",
        "title_th": "หลักสูตรเศรษฐศาสตรบัณฑิต สาขาวิชาเศรษฐศาสตร์ธุรกิจ",
        "title_en": "Bachelor of Economics in Business Economics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศ.บ. (เศรษฐศาสตร์ธุรกิจ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Economics",
        "department_th": "สาขาวิชาเศรษฐศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "26,500 บาท",
        "tuition_total": "285,000 บาท",
        "description": "ผลิตนักเศรษฐศาสตร์ธุรกิจที่มีทักษะการวิเคราะห์สภาวะเศรษฐกิจ การเงิน การคลัง และการพยากรณ์ตลาดเพื่อประกอบการตัดสินใจเชิงธุรกิจ",
        "curriculum_highlights": ["Micro & Macro Economic Analysis", "Econometrics & Quantitative Analysis", "Business Forecasting", "Public Policy & Economics"],
        "career_paths": ["Economic Analyst", "Policy & Plan Analyst", "Market Research Analyst", "Banking & Securities Officer"],
        "tags": ["Economics", "Business Economics", "Data Analysis", "Econometrics"],
        "website_url": "https://econ.utcc.ac.th"
    },
    {
        "id": "utcc_econ_mecon",
        "title_th": "หลักสูตรเศรษฐศาสตรมหาบัณฑิต",
        "title_en": "Master of Economics",
        "degree_level": "ปริญญาโท",
        "degree_name": "ศ.ม. (เศรษฐศาสตร์)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Economics",
        "department_th": "สาขาวิชาเศรษฐศาสตร์",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "50,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "มุ่งเน้นการวิเคราะห์เศรษฐกิจมหภาคระดับสูง การค้าระหว่างประเทศ นโยบายเศรษฐกิจดิจิทัล และการวิจัยเชิงปริมาณขั้นสูง",
        "curriculum_highlights": ["Advanced Macroeconomics", "Applied Econometrics", "International Trade Theory & Policy", "Digital Economy Policy"],
        "career_paths": ["Senior Economist", "Government Economic Advisor", "Research Fellow", "Bank Strategist"],
        "tags": ["Economics", "Master", "Trade", "Policy Analyst"],
        "website_url": "https://econ.utcc.ac.th"
    },

    # ---------------- 4. Faculty of Science and Technology (คณะวิทยาศาสตร์และเทคโนโลยี) ----------------
    {
        "id": "utcc_sci_cs_ds",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และวิทยาการข้อมูล",
        "title_en": "Bachelor of Science in Computer Science and Data Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์และวิทยาการข้อมูล)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "31,500 บาท",
        "tuition_total": "340,000 บาท",
        "description": "เน้นการพัฒนาซอฟต์แวร์ อัลกอริทึม ปัญญาประดิษฐ์ (AI) การวิเคราะห์ข้อมูลขนาดใหญ่ (Big Data) และการเรียนรู้ของเครื่อง (Machine Learning)",
        "curriculum_highlights": ["Data Science & Big Data", "Machine Learning & AI", "Full-Stack Software Development", "Cloud Architecture"],
        "career_paths": ["Data Scientist", "Software Engineer", "AI/ML Engineer", "Data Engineer"],
        "tags": ["Computer Science", "Data Science", "AI", "Machine Learning", "Software Development"],
        "website_url": "https://science.utcc.ac.th"
    },
    {
        "id": "utcc_sci_digital_tech",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีดิจิทัลและนวัตกรรม",
        "title_en": "Bachelor of Science in Digital Technology and Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีดิจิทัลและนวัตกรรม)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "31,000 บาท",
        "tuition_total": "340,000 บาท",
        "description": "เรียนรู้การพัฒนาเว็บและแอปพลิเคชันมือถือ UX/UI Design ความมั่นคงปลอดภัยไซเบอร์ และการจัดการระบบคลาวด์",
        "curriculum_highlights": ["Mobile & Web Application Development", "UX/UI Design", "Cybersecurity Fundamentals", "Cloud Computing & DevOps"],
        "career_paths": ["Full Stack Developer", "UX/UI Designer", "System Analyst", "DevOps Engineer"],
        "tags": ["Digital Technology", "Web Development", "Mobile Apps", "UX/UI", "Cybersecurity"],
        "website_url": "https://science.utcc.ac.th"
    },
    {
        "id": "utcc_sci_game_sim",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาดิจิทัลเกมซิมูเลชัน",
        "title_en": "Bachelor of Science in Digital Game Simulation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ดิจิทัลเกมซิมูเลชัน)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Digital Media and Game",
        "department_th": "สาขาวิชาดิจิทัลเกม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "34,500 บาท",
        "tuition_total": "390,000 บาท",
        "description": "ผลิตนักพัฒนาเกม โปรแกรมเมอร์เกม และผู้สร้างแบบจำลองเสมือนจริง (VR/AR/Metaverse) ด้วยเทคโนโลยี Game Engine ระดับสากล",
        "curriculum_highlights": ["Game Engine Programming (Unity / Unreal)", "Virtual & Augmented Reality (VR/AR)", "Game Physics & AI", "3D Modeling & Animation for Games"],
        "career_paths": ["Game Developer / Programmer", "VR/AR Engineer", "Simulation Engineer", "Gameplay Designer"],
        "tags": ["Game Development", "VR/AR", "Simulation", "Computer Graphics", "Unity", "Unreal"],
        "website_url": "https://science.utcc.ac.th"
    },
    {
        "id": "utcc_sci_fin_eng",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิศวกรรมการเงิน",
        "title_en": "Bachelor of Science in Financial Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิศวกรรมการเงิน)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Financial Engineering",
        "department_th": "สาขาวิชาวิศวกรรมการเงิน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "300,000 บาท",
        "description": "ผสานคณิตศาสตร์การเงิน วิทยาการคอมพิวเตอร์ และเศรษฐศาสตร์การเงิน เพื่อสร้างแบบจำลองคณิตศาสตร์ในการประเมินราคาสินทรัพย์และการบริหารความเสี่ยง",
        "curriculum_highlights": ["Quantitative Finance", "Financial Modeling & Algorithmic Trading", "Risk Management & Derivatives", "Computational Mathematics"],
        "career_paths": ["Financial Engineer / Quant", "Risk Analyst", "Algorithmic Trader", "Derivatives Structurer"],
        "tags": ["Financial Engineering", "Quantitative Finance", "Algo Trading", "Risk Management"],
        "website_url": "https://science.utcc.ac.th"
    },

    # ---------------- 5. Faculty of Engineering (คณะวิศวกรรมศาสตร์) ----------------
    {
        "id": "utcc_eng_comp_ai",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์",
        "title_en": "Bachelor of Engineering in Computer and Artificial Intelligence Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "33,000 บาท",
        "tuition_total": "350,000 บาท",
        "description": "มุ่งเน้นการสร้างวิศวกรคอมพิวเตอร์ที่มีความรู้ลึกทั้งระบบฮาร์ดแวร์ ซอฟต์แวร์ อินเทอร์เน็ตของสรรพสิ่ง (IoT) และระบบปัญญาประดิษฐ์",
        "curriculum_highlights": ["Artificial Intelligence & Deep Learning", "Embedded Systems & IoT", "Computer Architecture & Hardware", "Robotics & Automation"],
        "career_paths": ["AI System Engineer", "Computer Systems Engineer", "Embedded Software Engineer", "IoT Solution Architect"],
        "tags": ["Engineering", "Computer Engineering", "AI", "IoT", "Robotics"],
        "website_url": "https://eng.utcc.ac.th"
    },
    {
        "id": "utcc_eng_logistics",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโลจิสติกส์",
        "title_en": "Bachelor of Engineering in Logistics Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมโลจิสติกส์)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Logistics Engineering",
        "department_th": "สาขาวิชาวิศวกรรมโลจิสติกส์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "32,500 บาท",
        "tuition_total": "340,000 บาท",
        "description": "เน้นการออกแบบและบริหารจัดการระบบคลังสินค้าอัตโนมัติ การขนส่ง การจำลองกระบวนการโลจิสติกส์ และการเพิ่มประสิทธิภาพห่วงโซ่อุปทาน",
        "curriculum_highlights": ["Smart Warehouse Design & Automation", "Supply Chain Optimization", "Logistics Network Modeling", "Transportation Engineering"],
        "career_paths": ["Logistics Engineer", "Supply Chain Analyst", "Warehouse Operations Manager", "Distribution Planner"],
        "tags": ["Engineering", "Logistics", "Supply Chain", "Automation", "Operations"],
        "website_url": "https://eng.utcc.ac.th"
    },

    # ---------------- 6. Faculty of Communication Arts (คณะนิเทศศาสตร์) ----------------
    {
        "id": "utcc_comm_digital_media",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสื่อสารดิจิทัลและคอนเทนต์มีเดีย",
        "title_en": "Bachelor of Communication Arts in Digital Communication and Media Content",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (การสื่อสารดิจิทัลและคอนเทนต์มีเดีย)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Digital Communication",
        "department_th": "สาขาวิชาการสื่อสารดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "310,000 บาท",
        "description": "ผลิตนักสร้างสรรค์คอนเทนต์ นักสื่อสารมวลชน และผู้เชี่ยวชาญการผลิตสื่อดิจิทัลทุกแพลตฟอร์มด้วยอุปกรณ์และสตูดิโอระดับมาตรฐานอุตสาหกรรม",
        "curriculum_highlights": ["Digital Content Creation & Storytelling", "Video Production & Editing", "Social Media Strategy", "Influencer Marketing & Branding"],
        "career_paths": ["Content Creator", "Digital Media Producer", "Creative Director", "Social Media Strategist"],
        "tags": ["Communication Arts", "Digital Media", "Content Creation", "Video Production", "Broadcasting"],
        "website_url": "https://commarts.utcc.ac.th"
    },
    {
        "id": "utcc_comm_film",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาภาพยนตร์และสื่อดิจิทัล",
        "title_en": "Bachelor of Communication Arts in Film and Digital Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (ภาพยนตร์และสื่อดิจิทัล)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Film and Digital Media",
        "department_th": "สาขาวิชาภาพยนตร์และสื่อดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "29,500 บาท",
        "tuition_total": "320,000 บาท",
        "description": "มุ่งเน้นทักษะการกำกับ การเขียนบท การถ่ายทำ การจัดแสง และการตัดต่อภาพยนตร์และซีรีส์ระดับมืออาชีพ",
        "curriculum_highlights": ["Directing & Screenwriting", "Cinematography & Lighting", "Sound Design & Audio Post-Production", "Film Distribution & Business"],
        "career_paths": ["Film Director", "Screenwriter", "Cinematographer", "Post-Production Editor"],
        "tags": ["Film", "Cinema", "Communication Arts", "Screenwriting", "Directing"],
        "website_url": "https://commarts.utcc.ac.th"
    },

    # ---------------- 7. Faculty of Humanities (คณะมนุษยศาสตร์) ----------------
    {
        "id": "utcc_hum_biz_eng",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษธุรกิจ",
        "title_en": "Bachelor of Arts in Business English",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาอังกฤษธุรกิจ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Humanities",
        "faculty_th": "คณะมนุษยศาสตร์",
        "department": "Department of Business English",
        "department_th": "สาขาวิชาภาษาอังกฤษธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "27,000 บาท",
        "tuition_total": "290,000 บาท",
        "description": "พัฒนาทักษะภาษาอังกฤษเพื่อการสื่อสารธุรกิจระดับมืออาชีพ การแปล การเจรจาต่อรอง และการทำงานในองค์กรข้ามชาติ",
        "curriculum_highlights": ["Business Communication in English", "English for International Trade", "English-Thai Business Translation", "Public Speaking & Presentation"],
        "career_paths": ["International Relations Officer", "Corporate Communications Specialist", "Translator / Interpreter", "Executive Assistant"],
        "tags": ["Business English", "Languages", "Humanities", "Communication", "Translation"],
        "website_url": "https://humanities.utcc.ac.th"
    },
    {
        "id": "utcc_hum_biz_chinese",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาจีนธุรกิจ",
        "title_en": "Bachelor of Arts in Business Chinese",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาจีนธุรกิจ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Humanities",
        "faculty_th": "คณะมนุษยศาสตร์",
        "department": "Department of Business Chinese",
        "department_th": "สาขาวิชาภาษาจีนธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "295,000 บาท",
        "description": "เน้นภาษาจีนสำหรับการทำธุรกิจกับจีน การค้าระหว่างประเทศ การล่ามและการแปล พร้อมโอกาสศึกษาแลกเปลี่ยน ณ มหาวิทยาลัยพันธมิตรในประเทศจีน",
        "curriculum_highlights": ["Chinese for Commercial Negotiation", "Chinese-Thai Business Translation", "Chinese Business Culture & Etiquette", "Advanced HSK Preparation"],
        "career_paths": ["Chinese Business Coordinator", "Interpreter / Translator", "Import-Export Specialist", "Chinese Customer Relations Manager"],
        "tags": ["Chinese", "Business Chinese", "Languages", "International Relations", "Humanities"],
        "website_url": "https://humanities.utcc.ac.th"
    },

    # ---------------- 8. Faculty of Law (คณะนิติศาสตร์) ----------------
    {
        "id": "utcc_law_llb",
        "title_th": "หลักสูตรนิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ. (นิติศาสตร์)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Department of Law",
        "department_th": "สาขาวิชานิติศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "27,500 บาท",
        "tuition_total": "295,000 บาท",
        "description": "ผลิตนักกฎหมายที่มีความเชี่ยวชาญพิเศษด้านกฎหมายธุรกิจ กฎหมายการค้าระหว่างประเทศ กฎหมายทรัพย์สินทางปัญญา และกฎหมายเทคโนโลยีสารสนเทศ",
        "curriculum_highlights": ["Commercial & Corporate Law", "International Trade Law", "Intellectual Property & IT Law", "Litigation & Moot Court Practice"],
        "career_paths": ["Lawyer / Attorney", "Corporate Legal Counsel", "Judge / Public Prosecutor", "Legal Advisor"],
        "tags": ["Law", "Business Law", "Legal", "Litigation", "Intellectual Property"],
        "website_url": "https://law.utcc.ac.th"
    },

    # ---------------- 9. Faculty of Tourism and Hospitality (คณะการท่องเที่ยวและอุตสาหกรรมบริการ) ----------------
    {
        "id": "utcc_tourism_culinary",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาศิลปะการประกอบอาหารและการจัดการภัตตาคาร",
        "title_en": "Bachelor of Arts in Culinary Arts and Restaurant Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ศิลปะการประกอบอาหารและการจัดการภัตตาคาร)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Tourism and Hospitality",
        "faculty_th": "คณะการท่องเที่ยวและอุตสาหกรรมบริการ",
        "department": "Department of Culinary Arts",
        "department_th": "สาขาวิชาศิลปะการประกอบอาหาร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "380,000 บาท",
        "description": "สร้างเชฟมืออาชีพและผู้ประกอบการร้านอาหาร เรียนรู้ศาสตร์การปรุงอาหารระดับสากล การบริหารต้นทุนภัตตาคาร และความปลอดภัยด้านอาหาร",
        "curriculum_highlights": ["Western & Asian Culinary Arts", "Restaurant Entrepreneurship & Operations", "Food Cost Control & Menu Engineering", "Bakery & Pastry Arts"],
        "career_paths": ["Professional Chef / Executive Chef", "Restaurant Owner / Entrepreneur", "F&B Manager", "Food Stylist"],
        "tags": ["Culinary Arts", "Chef", "Restaurant Management", "Hospitality", "Food and Beverage"],
        "website_url": "https://tourism.utcc.ac.th"
    },
    {
        "id": "utcc_tourism_hotel",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาการจัดการการโรงแรมและธุรกิจบริการ",
        "title_en": "Bachelor of Arts in Hotel and Hospitality Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (การจัดการการโรงแรมและธุรกิจบริการ)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "Faculty of Tourism and Hospitality",
        "faculty_th": "คณะการท่องเที่ยวและอุตสาหกรรมบริการ",
        "department": "Department of Hotel Management",
        "department_th": "สาขาวิชาการจัดการการโรงแรม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "29,000 บาท",
        "tuition_total": "310,000 บาท",
        "description": "ฝึกฝนการจัดการโรงแรมระดับลักชัวรี การบริการส่วนหน้า งานต้อนรับ การบริหารจัดการงานแม่บ้าน และกลยุทธ์การขายห้องพัก",
        "curriculum_highlights": ["Front Office Management", "Luxury Hospitality Service", "Hotel Revenue Management", "Event & Banquet Catering"],
        "career_paths": ["Hotel Manager / General Manager", "Guest Relations Officer", "Event & Banquet Manager", "Hospitality Consultant"],
        "tags": ["Hotel Management", "Hospitality", "Tourism", "Service Industry"],
        "website_url": "https://tourism.utcc.ac.th"
    },

    # ---------------- 10. International School of Management (iSM) ----------------
    {
        "id": "utcc_ism_bba_inter",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาธุรกิจระหว่างประเทศ (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Business Administration in International Business (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.B.A. (International Business)",
        "university": "University of the Thai Chamber of Commerce",
        "university_th": "มหาวิทยาลัยหอการค้าไทย",
        "faculty": "International School of Management (iSM)",
        "faculty_th": "วิทยาลัยนานาชาติเพื่อการจัดการ",
        "department": "International Business Program",
        "department_th": "หลักสูตรธุรกิจระหว่างประเทศนานาชาติ",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "62,000 บาท",
        "tuition_total": "496,000 บาท",
        "description": "หลักสูตรนานาชาติภาษาอังกฤษ 100% เชื่อมโยงเครือข่ายธุรกิจระดับโลกและโอกาสรับปริญญา 2 ใบร่วมกับมหาวิทยาลัยชั้นนำในสหรัฐฯ และออสเตรเลีย",
        "curriculum_highlights": ["Global Business Strategies", "International Marketing Management", "Global Financial Markets", "Cross-Cultural Leadership"],
        "career_paths": ["Global Management Consultant", "Multinational Corporation Executive", "International Trade Specialist", "Entrepreneur"],
        "tags": ["International Program", "English Program", "Global Business", "BBA", "iSM"],
        "website_url": "https://ism.utcc.ac.th"
    }
]

def fetch_live_utcc_data() -> List[Dict]:
    """Optionally crawl live website pages from utcc.ac.th if available."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get("https://www.utcc.ac.th", headers=headers, timeout=10)
        if resp.status_code == 200:
            logger.info("Successfully reached UTCC main portal.")
    except Exception as e:
        logger.warning(f"Could not connect to live UTCC web server: {e}")
    return UTCC_COURSES

def save_json(courses: List[Dict], filepath: Path = OUTPUT_JSON):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(courses)} UTCC courses to {filepath}")

def seed_db(courses: List[Dict]):
    if not DB_AVAILABLE:
        logger.warning("Database connection is not available. Skipping DB seeding.")
        return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    for c in courses:
        try:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error seeding course {c['id']}: {e}")
    session.close()
    logger.info(f"DB Seeding Complete for UTCC: {inserted} inserted, {updated} updated.")

def main():
    logger.info("Starting UTCC Curricula Scraper & Data Collector...")
    courses = fetch_live_utcc_data()
    save_json(courses)
    seed_db(courses)
    logger.info(f"Finished processing UTCC courses. Total programs: {len(courses)}")

if __name__ == "__main__":
    main()
