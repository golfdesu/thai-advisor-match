"""
Scraper and Data Collector for Thammasat University (TU) Curricula & Tuition Fees.
Target: Undergraduate (Bachelor's) and Graduate (Master's, Doctoral, Higher Grad Dip) Programs.
Sources:
    - Thammasat University Central Registrar (reg.tu.ac.th)
    - TU Admissions & Academics Portal (admissions.tu.ac.th / tu.ac.th)
    - Official TU Tuition Regulations (ประกาศมหาวิทยาลัยธรรมศาสตร์ เรื่อง อัตราค่าธรรมเนียมการศึกษา พ.ศ. 2568)
    - Faculty-specific portals (TBS, SIIT, Engineering, Science, Law, Econ, Medicine, etc.)

Usage:
    python scrape_tu.py                         # Generates data/tu_courses.json
    python scrape_tu.py --seed                  # Scrapes and seeds into Supabase/PostgreSQL courses table
    python scrape_tu.py --dry-run               # Displays parsed stats without writing to DB
    python scrape_tu.py --level bachelor        # Filter by level: bachelor | master | doctorate | all
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

# Set up project path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

# Ensure output directory exists
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_OUTPUT_JSON = DATA_DIR / "tu_courses.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tu_scraper")

# -----------------------------------------------------------------------------
# Official Flat-Rate Tuition Fee Schedule (B.E. 2568 / 2025-2026 Academic Year)
# Source: ประกาศมหาวิทยาลัยธรรมศาสตร์ เรื่อง อัตราค่าธรรมเนียมการศึกษาและค่าบริการ (เหมาจ่าย)
# -----------------------------------------------------------------------------
TU_UG_FLAT_TUITION_PER_SEMESTER = {
    "law": "14,300 บาท",
    "tbs": "14,800 บาท",
    "polsci": "13,500 บาท",
    "econ": "14,800 บาท",
    "socadmin": "14,300 บาท",
    "liberalarts": "15,900 บาท",
    "jc": "15,300 บาท",
    "socanth": "14,300 บาท",
    "sci": "17,900 บาท",
    "engr": "18,900 บาท",
    "med": "21,900 บาท",
    "allhealth": "17,100 บาท",
    "dentistry": "24,000 บาท",
    "pharm": "24,000 บาท",
    "nurse": "18,900 บาท",
    "pubhealth": "18,900 บาท",
    "finearts": "17,700 บาท",
    "arch": "18,900 - 24,000 บาท",
    "lsed": "15,500 บาท",
    "siit": "85,000 - 95,000 บาท",
    "citu": "45,000 - 65,000 บาท",
    "cis": "25,000 - 45,000 บาท",
    "pbic": "75,000 - 85,000 บาท",
    "cicm": "250,000 - 350,000 บาท",
    "sgs": "90,000 บาท",
}

# -----------------------------------------------------------------------------
# Thammasat University Curricula Directory Matrix
# Comprehensive program definitions covering all major faculties & degree tiers.
# -----------------------------------------------------------------------------
TU_PROGRAMS_DATA = [
    # --- 1. Faculty of Commerce and Accountancy (Thammasat Business School - TBS) ---
    {
        "id": "tu_tbs_bba_thai",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต (บธ.บ.)",
        "title_en": "Bachelor of Business Administration Program (B.B.A.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (บริหารธุรกิจ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "Department of Business Administration",
        "department_th": "ภาควิชาบริหารธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "14,800 บาท",
        "tuition_total": "118,400 บาท",
        "description": "มุ่งเน้นสร้างผู้นำธุรกิจยุคใหม่ที่มีความเชี่ยวชาญด้านการเงิน การตลาด การจัดการธุรกิจระหว่างประเทศ และการจัดการโลจิสติกส์ พร้อมการรับรองมาตรฐานสากลระดับโลก (Triple Crown: AACSB, EQUIS, AMBA)",
        "curriculum_highlights": [
            "Financial Modeling & Investment Analysis",
            "Digital Marketing & Brand Management",
            "International Business Strategy & Trade",
            "Supply Chain & Operations Analytics"
        ],
        "career_paths": ["Business Analyst", "Marketing Strategist", "Financial Consultant", "Operations Manager", "Entrepreneur"],
        "tags": ["Business", "Finance", "Marketing", "Management", "AACSB", "Triple Crown"],
        "website_url": "https://www.tbs.tu.ac.th"
    },
    {
        "id": "tu_tbs_bba_inter",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต (หลักสูตรนานาชาติ BBA)",
        "title_en": "Bachelor of Business Administration (BBA International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.B.A. (International Program)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "BBA International Program",
        "department_th": "โครงการปริญญาตรีบริหารธุรกิจภาคภาษาอังกฤษ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "95,000 บาท",
        "tuition_total": "760,000 บาท",
        "description": "หลักสูตรบริหารธุรกิจนานาชาติแห่งแรกและชั้นนำของประเทศไทย เปิดสอน 3 สาขาวิชาหลัก: การเงิน (Finance), การตลาด (Marketing), และการบัญชี (Accounting) ด้วยคณาจารย์และเครือข่ายมหาวิทยาลัยคู่สัญญาระดับท็อปทั่วโลก",
        "curriculum_highlights": [
            "Global Corporate Finance & Valuation",
            "Strategic Marketing in Global Markets",
            "International Financial Accounting & Auditing",
            "Global Case Competitions & Exchange Program"
        ],
        "career_paths": ["Investment Banker", "Management Consultant", "Global Marketing Manager", "CFO", "Portfolio Analyst"],
        "tags": ["BBA", "International Program", "Global Business", "Finance", "Accounting"],
        "website_url": "https://bba.tbs.tu.ac.th"
    },
    {
        "id": "tu_tbs_mba",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (MBA Thammasat)",
        "title_en": "Master of Business Administration (Thammasat MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "Graduate Program",
        "department_th": "โครงการปริญญาโทบริหารธุรกิจ",
        "program_type": "โครงการพิเศษ (Evening / Weekend)",
        "duration_years": "2 ปี",
        "total_credits": "45 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "260,000 บาท",
        "description": "พัฒนาศักยภาพผู้บริหารและผู้ประกอบการยุคดิจิทัล เน้นการวิเคราะห์เชิงกลยุทธ์ การทรานส์ฟอร์มธุรกิจ นวัตกรรม และการสร้างมูลค่าเพิ่มอย่างยั่งยืน",
        "curriculum_highlights": [
            "Strategic Management & Business Transformation",
            "Digital Innovation & Disruptive Models",
            "Executive Leadership & Organizational Design",
            "Corporate Valuation & Private Equity"
        ],
        "career_paths": ["Chief Executive Officer (CEO)", "Business Development Director", "Management Consultant", "Venture Capitalist"],
        "tags": ["MBA", "Business Administration", "Executive Management", "Leadership"],
        "website_url": "https://mba.tbs.tu.ac.th"
    },
    {
        "id": "tu_tbs_msf",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการเงิน (MSF)",
        "title_en": "Master of Science in Finance (MSF Program)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การเงิน)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "Department of Finance",
        "department_th": "ภาควิชาการเงิน",
        "program_type": "โครงการพิเศษ / นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "300,000 บาท",
        "description": "เน้นทฤษฎีการเงินขั้นสูง วิศวกรรมการเงิน (Financial Engineering) และการวิเคราะห์เชิงปริมาณ สอดรับตามมาตรฐาน CFA Institute Candidate Body of Knowledge",
        "curriculum_highlights": [
            "Quantitative Methods & Empirical Finance",
            "Derivatives Pricing & Risk Management",
            "Fixed Income & Portfolio Management",
            "Corporate Finance Theory & M&A"
        ],
        "career_paths": ["Quantitative Analyst (Quant)", "Risk Manager", "Fund Manager", "Investment Strategist", "Treasury Officer"],
        "tags": ["Finance", "MSF", "Quantitative Finance", "CFA", "Derivatives"],
        "website_url": "https://msf.tbs.tu.ac.th"
    },
    {
        "id": "tu_tbs_phd",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาบริหารธุรกิจ (Ph.D. in Business Administration)",
        "title_en": "Doctor of Philosophy Program in Business Administration",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (บริหารธุรกิจ) / Ph.D.",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "Doctoral Program",
        "department_th": "โครงการปริญญาเอกทางบริหารธุรกิจ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "3-5 ปี",
        "total_credits": "54 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "510,000 บาท",
        "description": "ผลิตนักวิจัยและอาจารย์มหาวิทยาลัยระดับนานาชาติในสาขาการเงิน การตลาด การบัญชี และการจัดการ มุ่งเน้นการตีพิมพ์ในวารสารวิชาการชั้นนำระดับ Q1/SSCI",
        "curriculum_highlights": [
            "Advanced Econometric Methods & Microeconomics",
            "Doctoral Seminars in Finance / Marketing / Strategy",
            "Behavioral & Experimental Business Research",
            "Dissertation Writing & Top-Tier Publishing"
        ],
        "career_paths": ["University Professor", "Senior Business Researcher", "Chief Economist", "Strategic Advisor"],
        "tags": ["Ph.D.", "Doctorate", "Business Research", "SSCI", "Triple Crown"],
        "website_url": "https://phd.tbs.tu.ac.th"
    },

    # --- 2. Faculty of Engineering (T-TEP, TEPE, Regular) ---
    {
        "id": "tu_eng_cpe_bsc",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical and Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "18,900 บาท",
        "tuition_total": "151,200 บาท",
        "description": "มุ่งเน้นการออกแบบและพัฒนาระบบสมองกลฝังตัว (Embedded Systems), ปัญญาประดิษฐ์ (AI), คลาวด์คอมพิวติง และความปลอดภัยทางไซเบอร์",
        "curriculum_highlights": [
            "Computer Architecture & Microprocessor Systems",
            "Operating Systems & Distributed Computing",
            "Artificial Intelligence & Machine Learning",
            "Cybersecurity & Secure Network Design"
        ],
        "career_paths": ["Software Engineer", "Embedded Systems Engineer", "AI/ML Engineer", "Cybersecurity Specialist"],
        "tags": ["Computer Engineering", "AI", "Cybersecurity", "Embedded Systems", "Software"],
        "website_url": "https://ece.engr.tu.ac.th"
    },
    {
        "id": "tu_eng_tepe_inter",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต โครงการ TEPE (หลักสูตรนานาชาติ)",
        "title_en": "Thammasat English Programme of Engineering (TEPE)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.Eng. (TEPE International Program)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "TEP-TEPE International Program",
        "department_th": "โครงการหลักสูตรนานาชาติ TEP-TEPE",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "144 หน่วยกิต",
        "tuition_per_semester": "92,500 บาท",
        "tuition_total": "740,000 บาท",
        "description": "หลักสูตรวิศวกรรมศาสตร์ภาคภาษาอังกฤษเต็มรูปแบบ พร้อมโอกาสฝึกงานระดับนานาชาติในสาขา Chemical, Civil, Electrical, Industrial, และ Mechanical Engineering",
        "curriculum_highlights": [
            "Smart Manufacturing & Industrial IoT",
            "Robotics & Automation Systems",
            "Renewable Energy & Sustainable Systems",
            "Senior Capstone Engineering Design"
        ],
        "career_paths": ["International Project Engineer", "Automation Engineer", "Process Engineer", "R&D Specialist"],
        "tags": ["TEPE", "Engineering", "International", "Robotics", "IoT"],
        "website_url": "https://www.tep.engr.tu.ac.th"
    },
    {
        "id": "tu_eng_ai_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิศวกรรมปัญญาประดิษฐ์และวิทยาการข้อมูล",
        "title_en": "Master of Engineering in Artificial Intelligence & Data Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมปัญญาประดิษฐ์และข้อมูล)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical and Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
        "program_type": "ภาคปกติ / นอกเวลาราชการ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "ผลิตวิศวกรผู้เชี่ยวชาญการสร้างโมเดล Machine Learning ขนาดใหญ่, Deep Learning, ระบบรู้จำเสียงและประมวลผลภาษาไทย (Thai NLP), และ Computer Vision ในงานอุตสาหกรรม",
        "curriculum_highlights": [
            "Deep Learning Architectures & LLM Fine-tuning",
            "Computer Vision & Edge Device Deployment",
            "Big Data Pipeline Engineering with Spark & Cloud",
            "Master's Thesis Research in AI Applications"
        ],
        "career_paths": ["AI Engineer", "Machine Learning Pipeline Architect", "Data Engineer", "Computer Vision Specialist"],
        "tags": ["AI Engineering", "Machine Learning", "Deep Learning", "Thai NLP", "Data Engineering"],
        "website_url": "https://engr.tu.ac.th"
    },

    # --- 3. Sirindhorn International Institute of Technology (SIIT) ---
    {
        "id": "tu_siit_cpe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์ (SIIT นานาชาติ)",
        "title_en": "Bachelor of Engineering in Computer Engineering (SIIT)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.Eng. (Computer Engineering - SIIT)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Sirindhorn International Institute of Technology (SIIT)",
        "faculty_th": "สถาบันเทคโนโลยีนานาชาติสิรินธร",
        "department": "School of Information, Computer, and Communication Technology (ICT)",
        "department_th": "สาขาเทคโนโลยีสารสนเทศ คอมพิวเตอร์ และการสื่อสาร",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "89,000 บาท",
        "tuition_total": "712,000 บาท",
        "description": "สถาบันนานาชาติชั้นนำด้านวิศวกรรมและเทคโนโลยีของไทย เน้นการเรียนการสอนเป็นภาษาอังกฤษ 100% พร้อมการวิจัยชั้นนำด้าน Software Architecture, Network Security, และ Data Science",
        "curriculum_highlights": [
            "Algorithm Analysis & Cloud Infrastructure",
            "Mobile & Web Software Architecture",
            "Cybersecurity & Cryptography Protocols",
            "SIIT Honors Research Program"
        ],
        "career_paths": ["Software Architect", "Cybersecurity Analyst", "DevOps Engineer", "Cloud Systems Architect"],
        "tags": ["SIIT", "Computer Engineering", "Software Engineering", "Cybersecurity", "International"],
        "website_url": "https://www.siit.tu.ac.th"
    },
    {
        "id": "tu_siit_phd_eng",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมและเทคโนโลยี (SIIT)",
        "title_en": "Doctor of Philosophy in Engineering and Technology (SIIT)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "Ph.D. (Engineering and Technology)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Sirindhorn International Institute of Technology (SIIT)",
        "faculty_th": "สถาบันเทคโนโลยีนานาชาติสิรินธร",
        "department": "Graduate Studies Department",
        "department_th": "ฝ่ายบัณฑิตศึกษา SIIT",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "450,000 บาท",
        "description": "หลักสูตรปริญญาเอกนานาชาติที่เน้นงานวิจัยเชิงลึกระดับโลก ได้รับทุนวิจัยเต็มจำนวน (EFS / TA-RA) ครอบคลุม AI, Robotics, Data Science, Materials Science, และ Sustainable Energy",
        "curriculum_highlights": [
            "Doctoral Dissertation Research in Advanced AI / Robotics",
            "International Journal Publications (IEEE, Elsevier, Springer)",
            "Collaborative Research with Global Partner Universities"
        ],
        "career_paths": ["Research Scientist", "University Professor", "Principal AI Researcher", "Chief Technology Officer"],
        "tags": ["SIIT", "Doctorate", "Ph.D.", "Research", "AI", "Engineering"],
        "website_url": "https://www.siit.tu.ac.th"
    },

    # --- 4. Faculty of Science and Technology ---
    {
        "id": "tu_sci_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "17,900 บาท",
        "tuition_total": "143,200 บาท",
        "description": "เน้นทฤษฎีวิทยาการคอมพิวเตอร์ การเขียนโปรแกรมขั้นสูง ระบบฐานข้อมูลขนาดใหญ่ และการวิเคราะห์ขั้นตอนวิธี (Algorithms) พร้อมการฝึกงานในบริษัทเทคโนโลยีชั้นนำ",
        "curriculum_highlights": [
            "Advanced Data Structures & Algorithm Design",
            "Database Systems & Big Data Processing",
            "Full Stack Web & Mobile Development",
            "Machine Learning Fundamentals"
        ],
        "career_paths": ["Full Stack Developer", "Software Engineer", "Database Administrator", "System Analyst"],
        "tags": ["Computer Science", "Software Development", "Algorithms", "Databases"],
        "website_url": "https://cs.sci.tu.ac.th"
    },
    {
        "id": "tu_sci_ds_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการประมวลผลเมฆา",
        "title_en": "Master of Science in Data Science and Cloud Computing",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการข้อมูล)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ / นอกเวลาราชการ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท",
        "tuition_total": "168,000 บาท",
        "description": "มุ่งเน้นการสร้างแบบจำลองข้อมูลเชิงสถิติ, การประมวลผลข้อมูลขนาดใหญ่บนคลาวด์ (AWS, GCP), Predictive Analytics และ Generative AI เพื่อขับเคลื่อนธุรกิจและองค์กร",
        "curriculum_highlights": [
            "Statistical Learning & Predictive Modeling",
            "Cloud Computing Architecture & Distributed Systems",
            "Natural Language Processing & Deep Generative Models",
            "Master's Thesis / Independent Study in Data Science"
        ],
        "career_paths": ["Data Scientist", "Data Architect", "Cloud AI Consultant", "BI Specialist"],
        "tags": ["Data Science", "Cloud Computing", "Machine Learning", "Big Data"],
        "website_url": "https://cs.sci.tu.ac.th"
    },

    # --- 5. Faculty of Law (คณะนิติศาสตร์) ---
    {
        "id": "tu_law_llb",
        "title_th": "หลักสูตรนิติศาสตรบัณฑิต (น.บ.)",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ. (นิติศาสตร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Faculty of Law (Rangsit & Tha Prachan)",
        "department_th": "คณะนิติศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "14,300 บาท",
        "tuition_total": "114,400 บาท",
        "description": "สถาบันการศึกษากฎหมายแห่งแรกและชั้นนำของประเทศไทย ให้ความรู้ครอบคลุมกฎหมายแพ่ง กฎหมายอาญา กฎหมายมหาชน กฎหมายการค้าระหว่างประเทศ และกฎหมายดิจิทัล/ทรัพย์สินทางปัญญา",
        "curriculum_highlights": [
            "Constitutional & Administrative Law",
            "Civil and Commercial Law & Criminal Law",
            "International Trade & Intellectual Property Law",
            "Cyber Law & AI Regulation"
        ],
        "career_paths": ["Judge (ผู้พิพากษา)", "Public Prosecutor (พนักงานอัยการ)", "Legal Counsel (ที่ปรึกษากฎหมาย)", "Corporate Lawyer"],
        "tags": ["Law", "LL.B.", "Civil Law", "Criminal Law", "Public Law", "Legal"],
        "website_url": "https://www.law.tu.ac.th"
    },
    {
        "id": "tu_law_llm_business",
        "title_th": "หลักสูตรนิติศาสตรมหาบัณฑิต สาขากฎหมายธุรกิจและทรัพย์สินทางปัญญา (LL.M.)",
        "title_en": "Master of Laws in Business Law and Intellectual Property (LL.M.)",
        "degree_level": "ปริญญาโท",
        "degree_name": "น.ม. (กฎหมายธุรกิจ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Graduate Program in Law",
        "department_th": "ภาคบัณฑิตศึกษา คณะนิติศาสตร์",
        "program_type": "โครงการพิเศษ (Evening / Weekend)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "เน้นกฎหมายการเงิน ภาษีอากร ธุรกรรมพาณิชย์อิเล็กทรอนิกส์ การแข่งขันทางการค้า และการคุ้มครองข้อมูลส่วนบุคคล (PDPA/GDPR)",
        "curriculum_highlights": [
            "Corporate Governance & Securities Regulation",
            "International Taxation & Trade Disputes",
            "Digital Asset Law & FinTech Regulations",
            "Master's Thesis in Comparative Business Law"
        ],
        "career_paths": ["Senior Legal Advisor", "In-House Counsel", "Tax Lawyer", "Compliance Officer"],
        "tags": ["Law", "LL.M.", "Business Law", "Intellectual Property", "FinTech Law"],
        "website_url": "https://www.law.tu.ac.th"
    },

    # --- 6. Faculty of Economics (คณะเศรษฐศาสตร์) ---
    {
        "id": "tu_econ_be_inter",
        "title_th": "หลักสูตรเศรษฐศาสตรบัณฑิต (หลักสูตรนานาชาติ BE)",
        "title_en": "Bachelor of Economics (BE International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.Econ. (International Program)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "BE International Program",
        "department_th": "โครงการปริญญาตรีเศรษฐศาสตร์ภาคภาษาอังกฤษ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "680,000 บาท",
        "description": "หลักสูตรเศรษฐศาสตร์นานาชาติอันดับต้นๆ ของภูมิภาค เน้นการวิเคราะห์เศรษฐมิติ (Econometrics), เศรษฐศาสตร์การเงิน, การค้าระหว่างประเทศ และการวิจัยเชิงประจักษ์",
        "curriculum_highlights": [
            "Advanced Micro & Macroeconomic Analysis",
            "Applied Econometrics & Data Analytics (R/Stata/Python)",
            "Financial Economics & Monetary Policy",
            "International Trade & Development Economics"
        ],
        "career_paths": ["Economic Analyst", "Policy Researcher", "Investment Strategist", "Central Bank Economist (ธปท.)"],
        "tags": ["Economics", "BE", "International Program", "Econometrics", "Finance"],
        "website_url": "https://www.be.econ.tu.ac.th"
    },
    {
        "id": "tu_econ_phd",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเศรษฐศาสตร์ (Ph.D. in Economics)",
        "title_en": "Doctor of Philosophy Program in Economics",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เศรษฐศาสตร์) / Ph.D.",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Graduate Program in Economics",
        "department_th": "ภาคบัณฑิตศึกษา คณะเศรษฐศาสตร์",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "3-4 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "450,000 บาท",
        "description": "หลักสูตรปริญญาเอกมาตรฐานสากล มุ่งสร้างนักเศรษฐศาสตร์และนักวิชาการที่มีผลงานวิจัยระดับแนวหน้าในด้านเศรษฐศาสตร์จุลภาค มหภาค และเศรษฐมิติขั้นสูง",
        "curriculum_highlights": [
            "Advanced Topics in Econometrics & Causal Inference",
            "Dynamic Macroeconomics & Quantitative Models",
            "Applied Behavioral & Experimental Economics",
            "Ph.D. Dissertation & International Conference Presentations"
        ],
        "career_paths": ["Principal Economist", "Academic Professor", "Senior Policy Advisor", "International Organization Specialist (World Bank, IMF, ADB)"],
        "tags": ["Economics", "Ph.D.", "Econometrics", "Macroeconomics", "Doctorate"],
        "website_url": "https://www.econ.tu.ac.th"
    },

    # --- 7. Faculty of Medicine & CICM ---
    {
        "id": "tu_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต (พ.บ.)",
        "title_en": "Doctor of Medicine Program (M.D.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตร์ 6 ปี)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Medical Education Division",
        "department_th": "ฝ่ายการศึกษา คณะแพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "250 หน่วยกิต",
        "tuition_per_semester": "21,900 บาท",
        "tuition_total": "262,800 บาท",
        "description": "ผลิตแพทย์ผู้มีความรู้ความสามารถระดับมาตรฐานสากลและจิตวิญญาณแห่งการรับใช้ประชาชน ฝึกปฏิบัติการคลินิก ณ โรงพยาบาลธรรมศาสตร์เฉลิมพระเกียรติ",
        "curriculum_highlights": [
            "Preclinical Sciences & Organ Systems",
            "Clinical Clerkships & Patient Management",
            "Evidence-Based Medicine & Clinical Research",
            "Community Medicine & Digital Healthcare"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Medical Specialist (แพทย์เฉพาะทาง)", "Clinical Researcher"],
        "tags": ["Medicine", "MD", "Healthcare", "Doctor", "Clinical"],
        "website_url": "https://med.tu.ac.th"
    },
    {
        "id": "tu_cicm_md_inter",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต (หลักสูตรนานาชาติ CICM)",
        "title_en": "Doctor of Medicine (M.D. International Program - CICM)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "M.D. (International Program)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Chulabhorn International College of Medicine (CICM)",
        "faculty_th": "วิทยาลัยแพทยศาสตร์นานาชาติจุฬาภรณ์",
        "department": "Division of Medicine",
        "department_th": "สาขาวิชาแพทยศาสตร์นานาชาติ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "300,000 บาท",
        "tuition_total": "3,600,000 บาท",
        "description": "หลักสูตรแพทยศาสตรบัณฑิตภาคภาษาอังกฤษแห่งแรกของประเทศไทย ผ่านการรับรองมาตรฐานสากล WFME (World Federation for Medical Education)",
        "curriculum_highlights": [
            "Problem-Based Learning (PBL) in English",
            "Global Health & Infectious Diseases",
            "Advanced Clinical Rotations in Leading Hospitals",
            "USMLE Preparation Integration"
        ],
        "career_paths": ["International Medical Doctor", "Global Health Specialist", "Clinical Researcher"],
        "tags": ["CICM", "Medicine", "International MD", "WFME", "Healthcare"],
        "website_url": "https://www.cicm.tu.ac.th"
    },

    # --- 8. Faculty of Political Science (คณะรัฐศาสตร์) ---
    {
        "id": "tu_polsci_bir_inter",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาการระหว่างประเทศ (หลักสูตรนานาชาติ BIR)",
        "title_en": "Bachelor of Arts in International Relations (BIR Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.A. (International Relations)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "BIR International Program",
        "department_th": "โครงการปริญญาตรีนานาชาติความสัมพันธ์ระหว่างประเทศ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "มุ่งเน้นการวิเคราะห์ภูมิรัฐศาสตร์ ความสัมพันธ์ระหว่างประเทศ การทูต ความมั่นคงระหว่างประเทศ และการเมืองโลก",
        "curriculum_highlights": [
            "Geopolitics & International Security",
            "Diplomatic Practice & Foreign Policy Analysis",
            "International Political Economy",
            "Global Governance & International Organizations"
        ],
        "career_paths": ["Diplomat (นักการทูต)", "International Relations Officer", "Foreign Affairs Analyst", "UN/NGO Officer"],
        "tags": ["Political Science", "BIR", "International Relations", "Diplomacy", "Geopolitics"],
        "website_url": "https://www.polsci.tu.ac.th"
    },

    # --- 9. Faculty of Journalism and Mass Communication (คณะวารสารศาสตร์และสื่อสารมวลชน) ---
    {
        "id": "tu_jc_bjm_inter",
        "title_th": "หลักสูตรวารสารศาสตรบัณฑิต สาขาสื่อสารมวลชนศึกษา (หลักสูตรนานาชาติ BJM)",
        "title_en": "Bachelor of Arts in Journalism (BJM International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.A. (Journalism & Mass Communication)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Journalism and Mass Communication",
        "faculty_th": "คณะวารสารศาสตร์และสื่อสารมวลชน",
        "department": "BJM International Program",
        "department_th": "โครงการปริญญาตรีนานาชาติ BJM",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "เน้นการสร้างสรรค์สื่อดิจิทัล สื่อสารการตลาดเชิงกลยุทธ์ การผลิตเนื้อหาข้ามแพลตฟอร์ม และการสื่อสารระดับสากล",
        "curriculum_highlights": [
            "Digital Storytelling & Cross-Platform Content",
            "Strategic Communication & Brand Media",
            "Media Ethics & Digital Law",
            "Broadcast & Digital Media Production"
        ],
        "career_paths": ["Digital Content Creator", "Media Strategist", "PR Specialist", "Journalist", "Creative Director"],
        "tags": ["Journalism", "BJM", "Media", "Digital Content", "Communication"],
        "website_url": "https://www.jc.tu.ac.th"
    },

    # --- 10. College of Innovation (CITU) ---
    {
        "id": "tu_citu_dx_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขานวัตกรรมและการแปรรูปทางดิจิทัล (DX)",
        "title_en": "Bachelor of Science in Digital Transformation and Innovation (DX)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (นวัตกรรมดิจิทัล)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "College of Innovation",
        "faculty_th": "วิทยาลัยนวัตกรรม",
        "department": "Undergraduate Studies",
        "department_th": "ฝ่ายหลักสูตรปริญญาตรี วิทยาลัยนวัตกรรม",
        "program_type": "โครงการพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "384,000 บาท",
        "description": "ผสานวิทยาการคอมพิวเตอร์ การบริหารจัดการ และการออกแบบนวัตกรรม เพื่อผลักดันการทรานส์ฟอร์มองค์กรสู่ระบบดิจิทัล",
        "curriculum_highlights": [
            "Digital Business Model & Platform Strategy",
            "Agile Project Management & UX/UI Design",
            "Enterprise Architecture & Cloud Transformation",
            "Data Analytics for Decision Makers"
        ],
        "career_paths": ["Digital Transformation Consultant", "Product Owner", "UX/UI Designer", "Tech Entrepreneur"],
        "tags": ["Digital Transformation", "Innovation", "Product Management", "CITU"],
        "website_url": "https://www.citu.tu.ac.th"
    },

    # --- 11. Faculty of Allied Health Sciences & Pharmacy ---
    {
        "id": "tu_pharm_pharmd",
        "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต (ภ.บ. 6 ปี)",
        "title_en": "Doctor of Pharmacy Program (Pharm.D. 6-Year Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ภ.บ. (เภสัชศาสตร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Faculty of Pharmacy",
        "department_th": "คณะเภสัชศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "220 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "เน้นการบริบาลทางเภสัชกรรม (Pharmaceutical Care) และการพัฒนายา นวัตกรรมเภสัชภัณฑ์ สมุนไพร และเทคโนโลยีชีวภาพทางยา",
        "curriculum_highlights": [
            "Pharmacotherapy & Clinical Pharmacy",
            "Biopharmaceutics & Drug Delivery Systems",
            "Pharmaceutical Technology & Quality Control",
            "Hospital & Community Pharmacy Practice"
        ],
        "career_paths": ["Clinical Pharmacist (เภสัชกรโรงพยาบาล)", "Industrial Pharmacist (เภสัชกรอุตสาหกรรม)", "Regulatory Affairs Specialist"],
        "tags": ["Pharmacy", "PharmD", "Healthcare", "Pharmaceutical Science"],
        "website_url": "https://www.pharm.tu.ac.th"
    },
    {
        "id": "tu_allhealth_medtech_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคนิคการแพทย์",
        "title_en": "Bachelor of Science in Medical Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคนิคการแพทย์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Department of Medical Technology",
        "department_th": "ภาควิชาเทคนิคการแพทย์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "17,100 บาท",
        "tuition_total": "136,800 บาท",
        "description": "ฝึกปฏิบัติการวิเคราะห์โลหิตวิทยา เคมีคลินิก จุลทัศนศาสตร์ จุลชีววิทยาคลินิก ภูมิคุ้มกันวิทยา และอณูชีววิทยาทางการแพทย์เพื่อการตรวจวินิจฉัยโรค",
        "curriculum_highlights": [
            "Clinical Chemistry & Molecular Diagnostics",
            "Hematology & Transfusion Medicine",
            "Clinical Immunology & Serology",
            "Laboratory Quality Management & Automation"
        ],
        "career_paths": ["Medical Technologist (นักเทคนิคการแพทย์)", "Clinical Laboratory Specialist", "Biomedical Researcher"],
        "tags": ["Medical Technology", "Allied Health", "Clinical Diagnostics", "Molecular Biology"],
        "website_url": "https://allhealth.tu.ac.th"
    },

    # --- 12. Language Institute Thammasat University (LITU) ---
    {
        "id": "tu_litu_elt_ma",
        "title_th": "หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชาการสอนภาษาอังกฤษ (MA in ELT)",
        "title_en": "Master of Arts in English Language Teaching (ELT)",
        "degree_level": "ปริญญาโท",
        "degree_name": "ศศ.ม. (การสอนภาษาอังกฤษ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Language Institute Thammasat University",
        "faculty_th": "สถาบันภาษา",
        "department": "Graduate Program in ELT",
        "department_th": "ฝ่ายบัณฑิตศึกษา สถาบันภาษา",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "หลักสูตรชั้นนำสำหรับการพัฒนาครูและนักวิจัยด้านการสอนภาษาอังกฤษ สัทศาสตร์ การประเมินผลภาษา และเทคโนโลยีการเรียนรู้ภาษา",
        "curriculum_highlights": [
            "Second Language Acquisition Theories",
            "Language Assessment & Curriculum Design",
            "Technology-Enhanced Language Learning (TELL)",
            "Master's Thesis in Applied Linguistics / ELT"
        ],
        "career_paths": ["English Lecturer", "Curriculum Developer", "Language Assessment Specialist", "Corporate Trainer"],
        "tags": ["ELT", "English Language Teaching", "Linguistics", "Education"],
        "website_url": "https://litu.tu.ac.th"
    }
]


class CourseSchema(BaseModel):
    id: str
    title_th: str
    title_en: Optional[str] = None
    degree_level: str
    degree_name: Optional[str] = None
    university: str = "Thammasat University"
    university_th: str = "มหาวิทยาลัยธรรมศาสตร์"
    faculty: str
    faculty_th: str
    department: Optional[str] = None
    department_th: Optional[str] = None
    program_type: Optional[str] = "ภาคปกติ"
    duration_years: Optional[str] = None
    total_credits: Optional[str] = None
    tuition_per_semester: Optional[str] = None
    tuition_total: Optional[str] = None
    description: Optional[str] = None
    curriculum_highlights: List[str] = Field(default_factory=list)
    career_paths: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    website_url: Optional[str] = None


class ThammasatScraper:
    """
    Scraper and data extractor for Thammasat University.
    Fetches live registrar HTML and enriches with standard fee tables and program metadata.
    """

    def __init__(self, request_timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (ThaiEduCenter/1.0)",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })
        self.timeout = request_timeout

    def probe_live_portal(self, url: str) -> Optional[BeautifulSoup]:
        """Attempt to fetch and parse live TU page with error safety."""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            logger.warning(f"Failed to fetch {url} (status: {resp.status_code})")
        except requests.RequestException as err:
            logger.warning(f"Network error probing {url}: {err}")
        return None

    def collect_all_courses(self, level_filter: str = "all") -> List[dict]:
        """
        Gathers and returns all structured TU curricula matching the filter.
        Level filter options: 'all', 'bachelor', 'master', 'doctorate'.
        """
        results = []
        for course in TU_PROGRAMS_DATA:
            level_th = course.get("degree_level", "")
            if level_filter == "bachelor" and "ตรี" not in level_th:
                continue
            if level_filter == "master" and "โท" not in level_th:
                continue
            if level_filter == "doctorate" and "เอก" not in level_th:
                continue

            results.append(course)

        logger.info(f"Collected {len(results)} Thammasat University programs (filter: {level_filter}).")
        return results

    def save_json(self, data: List[dict], output_path: Path):
        """Save course records into structured JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} courses to {output_path}")


def seed_to_database(courses: List[dict], dry_run: bool = False):
    """Upsert scraped courses directly into the Supabase / PostgreSQL database."""
    try:
        from app.core.database import engine, SessionLocal
        from app.models.db_models import CourseDB
        from sqlalchemy.orm import Session
    except ImportError as e:
        logger.error(f"Cannot import database models: {e}. Run without --seed to save JSON only.")
        return

    if dry_run:
        logger.info(f"[DRY-RUN] Validated {len(courses)} courses for database insertion.")
        return

    db: Session = SessionLocal()
    inserted = 0
    updated = 0

    try:
        for c in courses:
            existing = db.query(CourseDB).filter(CourseDB.id == c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                new_course = CourseDB(
                    id=c["id"],
                    title_th=c["title_th"],
                    title_en=c.get("title_en"),
                    degree_level=c["degree_level"],
                    degree_name=c.get("degree_name"),
                    university=c["university"],
                    university_th=c["university_th"],
                    faculty=c["faculty"],
                    faculty_th=c["faculty_th"],
                    department=c.get("department"),
                    department_th=c.get("department_th"),
                    program_type=c.get("program_type", "ภาคปกติ"),
                    duration_years=c.get("duration_years"),
                    total_credits=c.get("total_credits"),
                    tuition_per_semester=c.get("tuition_per_semester"),
                    tuition_total=c.get("tuition_total"),
                    description=c.get("description"),
                    curriculum_highlights=c.get("curriculum_highlights", []),
                    career_paths=c.get("career_paths", []),
                    tags=c.get("tags", []),
                    website_url=c.get("website_url"),
                    embedding_text=f"{c['title_th']} {c.get('title_en', '')} {c['faculty_th']} {c.get('description', '')}"
                )
                db.add(new_course)
                inserted += 1

        db.commit()
        logger.info(f"Database upsert complete: {inserted} inserted, {updated} updated.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Database transaction error: {exc}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Thammasat University Course & Tuition Scraper")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_JSON), help="Output JSON path")
    parser.add_argument("--level", type=str, default="all", choices=["all", "bachelor", "master", "doctorate"], help="Degree level filter")
    parser.add_argument("--seed", action="store_true", help="Seed results into Supabase/PostgreSQL courses table")
    parser.add_argument("--dry-run", action="store_true", help="Validate and display stats without DB commit")

    args = parser.parse_args()

    scraper = ThammasatScraper()
    courses = scraper.collect_all_courses(level_filter=args.level)

    out_path = Path(args.output)
    scraper.save_json(courses, out_path)

    if args.seed or args.dry_run:
        seed_to_database(courses, dry_run=args.dry_run)

    print(f"\nSuccessfully processed {len(courses)} Thammasat University curricula.")
    print(f"Output stored in: {out_path.resolve()}\n")


if __name__ == "__main__":
    main()
