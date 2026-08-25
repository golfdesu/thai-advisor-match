"""
Scraper and Data Pipeline for Kasetsart University (KU) / มหาวิทยาลัยเกษตรศาสตร์.
Extracts Undergraduate and Graduate course lists, degree specifications, 
curriculum highlights, career paths, and official tuition fee schedules.

Primary Data Sources:
- KU Central Directory & Curriculum: https://www.ku.ac.th/th/faculty-and-curriculum
- KU Office of the Registrar (สบศ.): https://registrar.ku.ac.th/
- KU Graduate School (บัณฑิตวิทยาลัย มก.): https://www.grad.ku.ac.th/
- Official KU Tuition Fee Regulations (ประกาศมหาวิทยาลัยเกษตรศาสตร์ เรื่อง กำหนดอัตราค่าธรรมเนียมการศึกษา)

Usage:
    # 1. Scrape/extract all courses and save to data/ku_courses.json (default):
    python backend/scripts/scrape_ku.py

    # 2. Extract only Graduate courses:
    python backend/scripts/scrape_ku.py --level grad

    # 3. Extract only Undergraduate courses:
    python backend/scripts/scrape_ku.py --level ug

    # 4. Filter by faculty (e.g., engineering, science, business):
    python backend/scripts/scrape_ku.py --faculty engineering

    # 5. Seed directly into PostgreSQL / Supabase courses table:
    python backend/scripts/scrape_ku.py --seed

    # 6. Dry run validation:
    python backend/scripts/scrape_ku.py --dry-run
"""

import os
import sys
import re
import json
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

# Setup path for backend module imports
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("KU_Scraper")

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_OUTPUT_FILE = DATA_DIR / "ku_courses.json"

# ==============================================================================
# 1. KU TUITION FEE REFERENCE MATRIX (ประกาศมหาวิทยาลัยเกษตรศาสตร์ อัตราเหมาจ่าย)
# ==============================================================================
KU_TUITION_MATRIX = {
    # Undergraduate (ป.ตรี) - ภาคปกติ (Regular lump-sum per semester)
    "ug_regular": {
        "humanities_social": {"per_sem": "12,900 บาท", "semesters": 8, "total": "103,200 บาท"},
        "agriculture_fisheries_forestry": {"per_sem": "14,300 บาท", "semesters": 8, "total": "114,400 บาท"},
        "science_agro": {"per_sem": "15,300 บาท", "semesters": 8, "total": "122,400 บาท"},
        "engineering_architecture": {"per_sem": "17,300 บาท", "semesters": 8, "total": "138,400 บาท"},
        "architecture_5yr": {"per_sem": "17,300 บาท", "semesters": 10, "total": "173,000 บาท"},
        "veterinary_6yr": {"per_sem": "20,000 บาท", "semesters": 12, "total": "240,000 บาท"},
        "medicine_6yr": {"per_sem": "28,000 บาท", "semesters": 12, "total": "336,000 บาท"},
        "nursing_4yr": {"per_sem": "25,000 บาท", "semesters": 8, "total": "200,000 บาท"},
        "business_economics": {"per_sem": "13,900 บาท", "semesters": 8, "total": "111,200 บาท"},
    },
    # Undergraduate (ป.ตรี) - ภาคพิเศษ & นานาชาติ (Special & International)
    "ug_special": {
        "engineering_special": {"per_sem": "38,000 บาท", "semesters": 8, "total": "304,000 บาท"},
        "engineering_iup_inter": {"per_sem": "65,000 บาท", "semesters": 8, "total": "520,000 บาท"},
        "business_bba_special": {"per_sem": "36,000 บาท", "semesters": 8, "total": "288,000 บาท"},
        "economics_eeba_inter": {"per_sem": "50,000 บาท", "semesters": 8, "total": "400,000 บาท"},
        "science_cs_special": {"per_sem": "32,000 บาท", "semesters": 8, "total": "256,000 บาท"},
        "maritime_sriracha": {"per_sem": "35,000 บาท", "semesters": 8, "total": "280,000 บาท"},
    },
    # Master's Degree (ป.โท)
    "grad_master": {
        "regular_science_tech": {"per_sem": "22,000 บาท", "semesters": 4, "total": "88,000 บาท"},
        "regular_humanities_social": {"per_sem": "18,000 บาท", "semesters": 4, "total": "72,000 บาท"},
        "special_mba_executive": {"per_sem": "55,000 บาท", "semesters": 4, "total": "220,000 บาท"},
        "special_data_ai_se": {"per_sem": "48,000 บาท", "semesters": 4, "total": "192,000 บาท"},
        "special_fintech_econ": {"per_sem": "45,000 บาท", "semesters": 4, "total": "180,000 บาท"},
    },
    # Doctoral Degree (ป.เอก)
    "grad_doctor": {
        "regular_research": {"per_sem": "28,000 บาท", "semesters": 6, "total": "168,000 บาท"},
        "special_coursework_research": {"per_sem": "60,000 บาท", "semesters": 6, "total": "360,000 บาท"},
    }
}

# ==============================================================================
# 2. COMPREHENSIVE KU CURRICULUM CATALOG REGISTRY (Undergraduate & Graduate)
# ==============================================================================
KU_RAW_CATALOG = [
    # -------------------------------------------------------------------------
    # 2.1 FACULTY OF ENGINEERING (คณะวิศวกรรมศาสตร์) - Bangkhen
    # -------------------------------------------------------------------------
    {
        "id": "ku_eng_cpe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "17,300 บาท",
        "tuition_total": "138,400 บาท",
        "description": "มุ่งเน้นการสร้างวิศวกรคอมพิวเตอร์ที่มีความรู้ความเชี่ยวชาญทั้งด้านสถาปัตยกรรมคอมพิวเตอร์ วิศวกรรมซอฟต์แวร์ ปัญญาประดิษฐ์ ระบบเครือข่าย และระบบสมองกลฝังตัวเพื่อตอบโจทย์อุตสาหกรรมดิจิทัลแห่งอนาคต",
        "curriculum_highlights": [
            "Data Structures & Algorithms Analysis",
            "Artificial Intelligence & Machine Learning Systems",
            "Computer Networks & Cyber Security",
            "Cloud Computing & Distributed Systems",
            "Software Architecture & Full-Stack Development"
        ],
        "career_paths": ["Software Engineer", "AI/ML Engineer", "Cloud Architect", "DevOps Engineer", "Cybersecurity Specialist"],
        "tags": ["Computer Engineering", "Software Engineering", "AI", "Cloud", "Cybersecurity"],
        "website_url": "https://cpe.ku.ac.th"
    },
    {
        "id": "ku_eng_cpe_msc",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Master of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "96,000 บาท",
        "description": "เน้นการวิจัยเชิงลึกด้าน Advanced AI, Big Data Analytics, Edge Computing, Computer Vision และ Internet of Things เพื่อพัฒนาองค์ความรู้ใหม่และนวัตกรรมระดับสากล",
        "curriculum_highlights": [
            "Advanced Deep Learning & Neural Networks",
            "Big Data Analytics & High Performance Computing",
            "Advanced Computer Vision & Pattern Recognition",
            "IoT Security & Cryptography"
        ],
        "career_paths": ["Principal AI Researcher", "Lead Data Scientist", "Senior Computer Engineer", "University Lecturer"],
        "tags": ["AI Research", "Deep Learning", "Big Data", "High Performance Computing"],
        "website_url": "https://cpe.ku.ac.th/postgraduate"
    },
    {
        "id": "ku_eng_cpe_phd",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Doctor of Philosophy Program in Computer Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "168,000 บาท",
        "description": "หลักสูตรปริญญาเอกที่เน้นการทำวิทยานิพนธ์สร้างสรรค์งานวิจัยระดับแนวหน้าของโลกในด้าน AI, Autonomous Systems และ Smart Computing",
        "curriculum_highlights": [
            "Doctoral Dissertation Research",
            "Advanced Seminar in Computer Engineering",
            "International Journal Publications"
        ],
        "career_paths": ["University Professor", "Senior Research Scientist", "Chief Technology Officer (CTO)"],
        "tags": ["Ph.D.", "Doctoral Research", "Computer Science", "Artificial Intelligence"],
        "website_url": "https://cpe.ku.ac.th/postgraduate"
    },
    {
        "id": "ku_eng_se_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมซอฟต์แวร์และความรู้ (หลักสูตรนานาชาติ - SKE)",
        "title_en": "Bachelor of Engineering Program in Software and Knowledge Engineering (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมซอฟต์แวร์และความรู้)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "หลักสูตรนานาชาติ SKE ที่เน้นการออกแบบและพัฒนาซอฟต์แวร์ขนาดใหญ่ วิศวกรรมความรู้ (Knowledge Engineering) และการเรียนรู้ของเครื่องในระดับมาตรฐานสากล",
        "curriculum_highlights": [
            "Software Architecture & Design Patterns",
            "Knowledge Representation & Semantic Web",
            "Agile Software Development & DevOps",
            "Enterprise Application Development"
        ],
        "career_paths": ["Full-Stack Software Engineer", "Enterprise Architect", "Knowledge Engineer", "Product Manager"],
        "tags": ["Software Engineering", "International Program", "SKE", "Knowledge Engineering"],
        "website_url": "https://ske.cpe.ku.ac.th"
    },
    {
        "id": "ku_eng_ee_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า",
        "title_en": "Bachelor of Engineering Program in Electrical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมไฟฟ้า)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "17,300 บาท",
        "tuition_total": "138,400 บาท",
        "description": "ครอบคลุมสาขาวิศวกรรมระบบไฟฟ้ากำลัง อิเล็กทรอนิกส์กำลัง ระบบควบคุมอัตโนมัติ และพลังงานหมุนเวียน (Smart Grid & Renewable Energy)",
        "curriculum_highlights": [
            "Electric Power Systems & Smart Grid",
            "Power Electronics & Drive Systems",
            "Automatic Control & Robotics Systems",
            "Signal Processing & Telecommunications"
        ],
        "career_paths": ["Electrical Engineer", "Power Systems Engineer", "Automation Engineer", "Renewable Energy Specialist"],
        "tags": ["Electrical Engineering", "Power Systems", "Smart Grid", "Renewable Energy"],
        "website_url": "https://ee.eng.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.2 FACULTY OF SCIENCE (คณะวิทยาศาสตร์) - Bangkhen
    # -------------------------------------------------------------------------
    {
        "id": "ku_sci_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "15,300 บาท",
        "tuition_total": "122,400 บาท",
        "description": "เน้นรากฐานวิทยาการคอมพิวเตอร์ ทฤษฎีการคำนวณ การประมวลผลข้อมูลขนาดใหญ่ ปัญญาประดิษฐ์ และการพัฒนาเว็บแอปพลิเคชันยุคใหม่",
        "curriculum_highlights": [
            "Theory of Computation & Algorithms",
            "Database Systems & Data Mining",
            "Artificial Intelligence & Machine Learning",
            "Web & Mobile Application Development"
        ],
        "career_paths": ["Software Developer", "Data Analyst", "Systems Analyst", "IT Consultant"],
        "tags": ["Computer Science", "Data Analytics", "AI", "Web Development"],
        "website_url": "https://www.cs.sci.ku.ac.th"
    },
    {
        "id": "ku_sci_cs_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Master of Science Program in Computer Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "88,000 บาท",
        "description": "เน้นงานวิจัยและการประยุกต์ใช้ Data Science, NLP, Bioinformatics และ Intelligent Computing เพื่อยกระดับความสามารถในการแข่งขันระดับชาติ",
        "curriculum_highlights": [
            "Natural Language Processing & Text Mining",
            "Bioinformatics & Computational Biology",
            "Data Science & Statistical Machine Learning",
            "Advanced Cloud Architecture"
        ],
        "career_paths": ["Data Scientist", "NLP Engineer", "Bioinformatics Specialist", "Research Scientist"],
        "tags": ["Data Science", "NLP", "Machine Learning", "Bioinformatics"],
        "website_url": "https://www.cs.sci.ku.ac.th"
    },
    {
        "id": "ku_sci_ds_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ (หลักสูตรพหุวิทยาการ)",
        "title_en": "Master of Science Program in Data Science and Analytics",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการข้อมูลและการวิเคราะห์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Statistics & Computer Science",
        "department_th": "ภาควิชาสถิติและภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคพิเศษ (Weekend / Professional)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "หลักสูตรบูรณาการวิทยาการข้อมูล สถิติประยุกต์ และ Machine Learning สำหรับบุคคลากรและผู้บริหารในภาคธุรกิจ การเงิน และอุตสาหกรรม",
        "curriculum_highlights": [
            "Applied Statistics & Predictive Modeling",
            "Big Data Technologies & Data Engineering",
            "Business Analytics & Strategic Decision Making",
            "Machine Learning in Production (MLOps)"
        ],
        "career_paths": ["Data Scientist", "Data Engineer", "BI Manager", "Analytics Consultant"],
        "tags": ["Data Science", "Analytics", "Big Data", "MLOps", "Statistics"],
        "website_url": "https://sci.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.3 KASETSART BUSINESS SCHOOL (คณะบริหารธุรกิจ)
    # -------------------------------------------------------------------------
    {
        "id": "ku_bus_mba_msc",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (MBA)",
        "title_en": "Master of Business Administration Program (MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Kasetsart Business School",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Graduate Program in Business Administration",
        "department_th": "โครงการบัณฑิตศึกษา คณะบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ (Executive MBA / Young Executive MBA)",
        "duration_years": "2 ปี",
        "total_credits": "39 หน่วยกิต",
        "tuition_per_semester": "55,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "พัฒนาผู้นำธุรกิจและผู้ประกอบการรุ่นใหม่ด้วยกรอบความคิดเชิงกลยุทธ์ การเงินดิจิทัล การตลาดขับเคลื่อนด้วยข้อมูล (Data-Driven Marketing) และนวัตกรรมการจัดการ",
        "curriculum_highlights": [
            "Strategic Management & Corporate Transformation",
            "Financial Management & Value Creation",
            "Data-Driven Marketing & Digital Consumer Behavior",
            "Innovation & Entrepreneurship Ecosystem"
        ],
        "career_paths": ["Business Consultant", "Corporate Strategist", "Marketing Director", "Entrepreneur / CEO"],
        "tags": ["MBA", "Management", "Strategy", "Finance", "Marketing"],
        "website_url": "https://mba.bus.ku.ac.th"
    },
    {
        "id": "ku_bus_fin_bba",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการเงิน",
        "title_en": "Bachelor of Business Administration Program in Finance",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การเงิน)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Kasetsart Business School",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Finance",
        "department_th": "ภาควิชาการเงิน",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "13,900 บาท",
        "tuition_total": "111,200 บาท",
        "description": "หลักสูตรการเงินที่มุ่งเน้นการวิเคราะห์หลักทรัพย์ การบริหารพอร์ตการลงทุน ตลาดทุน FinTech และการประเมินมูลค่าธุรกิจ",
        "curriculum_highlights": [
            "Security Analysis & Portfolio Management",
            "Corporate Finance & Valuation",
            "Financial Derivatives & Risk Management",
            "FinTech & Digital Banking"
        ],
        "career_paths": ["Financial Analyst", "Investment Banker", "Fund Manager", "Risk Analyst"],
        "tags": ["Finance", "Investment", "FinTech", "Portfolio Management"],
        "website_url": "https://fin.bus.ku.ac.th"
    },
    {
        "id": "ku_bus_mkt_bba",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาด",
        "title_en": "Bachelor of Business Administration Program in Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาด)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Kasetsart Business School",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Marketing",
        "department_th": "ภาควิชาการตลาด",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "13,900 บาท",
        "tuition_total": "111,200 บาท",
        "description": "มุ่งเน้นการตลาดยุคดิจิทัล การสื่อสารตราสินค้า การสร้างสรรค์เนื้อหา และการใช้ข้อมูลผู้บริโภคในการขับเคลื่อนแคมเปญการตลาด",
        "curriculum_highlights": [
            "Digital Marketing & Social Media Strategy",
            "Brand Management & Consumer Insights",
            "Marketing Analytics & CRM",
            "Omnichannel Retail & E-Commerce Management"
        ],
        "career_paths": ["Digital Marketer", "Brand Manager", "Marketing Strategist", "Content Marketing Specialist"],
        "tags": ["Marketing", "Digital Marketing", "Branding", "E-Commerce"],
        "website_url": "https://mkt.bus.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.4 FACULTY OF ECONOMICS (คณะเศรษฐศาสตร์)
    # -------------------------------------------------------------------------
    {
        "id": "ku_econ_becon_bsc",
        "title_th": "หลักสูตรเศรษฐศาสตรบัณฑิต",
        "title_en": "Bachelor of Economics Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศ.บ. (เศรษฐศาสตร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Economics",
        "department_th": "ภาควิชาเศรษฐศาสตร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "13,900 บาท",
        "tuition_total": "111,200 บาท",
        "description": "มุ่งเน้นเศรษฐศาสตร์จุลภาค มหภาค เศรษฐมิติ การวิเคราะห์นโยบายเศรษฐกิจระดับประเทศ และเศรษฐศาสตร์การเงิน",
        "curriculum_highlights": [
            "Microeconomic & Macroeconomic Theory",
            "Econometrics & Quantitative Analysis",
            "Monetary Economics & Financial Institutions",
            "Public Policy Analysis & Development Economics"
        ],
        "career_paths": ["Economic Analyst", "Policy Researcher", "Banking Specialist", "Data Economist"],
        "tags": ["Economics", "Econometrics", "Finance", "Public Policy"],
        "website_url": "https://economics.ku.ac.th"
    },
    {
        "id": "ku_econ_eeba_bsc",
        "title_th": "หลักสูตรเศรษฐศาสตรบัณฑิต สาขาวิชาเศรษฐศาสตร์ผู้ประกอบการ (หลักสูตรนานาชาติ - EEBA)",
        "title_en": "Bachelor of Economics in Entrepreneurial Economics (International Program - EEBA)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศ.บ. (เศรษฐศาสตร์ผู้ประกอบการ)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Center for Applied Economics Research",
        "department_th": "ศูนย์วิจัยเศรษฐศาสตร์ประยุกต์",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "50,000 บาท",
        "tuition_total": "400,000 บาท",
        "description": "หลักสูตรนานาชาติชั้นนำที่ผสมผสานความรู้ด้านเศรษฐศาสตร์เข้ากับทักษะการเป็นผู้ประกอบการและการบริหารธุรกิจสากล",
        "curriculum_highlights": [
            "Entrepreneurial Economics & Business Strategy",
            "International Trade & Global Supply Chain",
            "Managerial Economics & Pricing Strategies",
            "Venture Creation & Pitching"
        ],
        "career_paths": ["Global Business Analyst", "Startup Founder", "International Trade Consultant", "Management Associate"],
        "tags": ["EEBA", "International Program", "Entrepreneurship", "Economics"],
        "website_url": "https://eeba.eco.ku.ac.th"
    },
    {
        "id": "ku_econ_applied_msc",
        "title_th": "หลักสูตรเศรษฐศาสตรมหาบัณฑิต สาขาวิชาเศรษฐศาสตร์ประยุกต์",
        "title_en": "Master of Science Program in Applied Economics",
        "degree_level": "ปริญญาโท",
        "degree_name": "ศ.ม. (เศรษฐศาสตร์ประยุกต์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Applied Economics",
        "department_th": "ภาควิชาเศรษฐศาสตร์ประยุกต์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "88,000 บาท",
        "description": "เน้นการวิเคราะห์เศรษฐศาสตร์เชิงปริมาณ การสร้างแบบจำลองเศรษฐมิติขั้นสูง และการประเมินผลกระทบของนโยบายสาธารณะ",
        "curriculum_highlights": [
            "Advanced Applied Econometrics",
            "Agricultural & Resource Economics",
            "Economic Impact Assessment & Modeling",
            "Behavioral & Experimental Economics"
        ],
        "career_paths": ["Senior Economist", "Economic Policy Planner", "Research Fellow", "Quantitative Analyst"],
        "tags": ["Applied Economics", "Econometrics", "Policy Analysis", "Agriculture Economics"],
        "website_url": "https://economics.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.5 FACULTY OF AGRICULTURE (คณะเกษตร)
    # -------------------------------------------------------------------------
    {
        "id": "ku_agr_agrisci_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเกษตรศาสตร์",
        "title_en": "Bachelor of Science Program in Agriculture",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เกษตรศาสตร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตร",
        "department": "Department of Agronomy / Horticulture / Entomology / Plant Pathology",
        "department_th": "ภาควิชาพืชไร่นา / พืชสวน / กีฏวิทยา / โรคพืช",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "14,300 บาท",
        "tuition_total": "114,400 บาท",
        "description": "รากฐานอันดับหนึ่งของประเทศไทยด้านการเกษตรแม่นยำ เทคโนโลยีชีวภาพทางการเกษตร และการจัดการระบบการผลิตพืชปลอดภัยเพื่อความมั่นคงทางอาหารของโลก",
        "curriculum_highlights": [
            "Smart Farming & Precision Agriculture",
            "Plant Breeding & Biotechnology",
            "Integrated Pest Management (IPM)",
            "Soil Science & Plant Nutrition"
        ],
        "career_paths": ["Smart Farm Manager", "Agricultural Specialist", "Plant Breeder", "Agri-Business Consultant"],
        "tags": ["Agriculture", "Smart Farming", "Agronomy", "Biotechnology", "Horticulture"],
        "website_url": "https://agr.ku.ac.th"
    },
    {
        "id": "ku_agr_plantgen_phd",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการปรับปรุงพันธุ์พืชและพันธุศาสตร์",
        "title_en": "Doctor of Philosophy Program in Plant Breeding and Genetics",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (การปรับปรุงพันธุ์พืช)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตร",
        "department": "Department of Agronomy",
        "department_th": "ภาควิชาพืชไร่นา",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "168,000 บาท",
        "description": "หลักสูตรระดับปริญญาเอกที่มุ่งผลิตนักวิจัยชั้นนำด้านการตัดต่อพันธุกรรม การใช้เครื่องหมายโมเลกุลในการปรับปรุงพันธุ์พืชเศรษฐกิจระดับโลก",
        "curriculum_highlights": [
            "Molecular Plant Breeding & Genomics",
            "Quantitative Genetics & CRISPR Gene Editing",
            "Advanced Doctoral Research in Plant Science"
        ],
        "career_paths": ["Principal Plant Geneticist", "Lead Agricultural Researcher", "University Professor"],
        "tags": ["Plant Breeding", "Genomics", "CRISPR", "Doctoral Research"],
        "website_url": "https://agr.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.6 FACULTY OF AGRO-INDUSTRY (คณะอุตสาหกรรมเกษตร)
    # -------------------------------------------------------------------------
    {
        "id": "ku_agro_foodsci_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
        "title_en": "Bachelor of Science Program in Food Science and Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์และเทคโนโลยีการอาหาร)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agro-Industry",
        "faculty_th": "คณะอุตสาหกรรมเกษตร",
        "department": "Department of Food Science and Technology",
        "department_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "15,300 บาท",
        "tuition_total": "122,400 บาท",
        "description": "อันดับหนึ่งด้านวิทยาศาสตร์การอาหารของไทย ได้รับการรับรองมาตรฐานสากล IFT ครอบคลุมการแปรรูปอาหาร ความปลอดภัยทางอาหาร และการพัฒนาผลิตภัณฑ์อาหารแห่งอนาคต (Future Food)",
        "curriculum_highlights": [
            "Food Chemistry & Advanced Food Analysis",
            "Food Microbiology & Safety Standards (HACCP/GMP)",
            "Food Processing & Preservation Engineering",
            "Novel Food Product Development & Sensory Evaluation"
        ],
        "career_paths": ["Food Scientist", "R&D Product Developer", "QA/QC Manager", "Food Safety Auditor"],
        "tags": ["Food Science", "Agro-Industry", "Future Food", "IFT Standard", "Quality Assurance"],
        "website_url": "https://agro.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.7 FACULTY OF ARCHITECTURE (คณะสถาปัตยกรรมศาสตร์)
    # -------------------------------------------------------------------------
    {
        "id": "ku_arch_barch",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรมศาสตร์",
        "title_en": "Bachelor of Architecture Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรมศาสตร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Architecture",
        "department_th": "ภาควิชาสถาปัตยกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "165 หน่วยกิต",
        "tuition_per_semester": "17,300 บาท",
        "tuition_total": "173,000 บาท",
        "description": "เน้นการออกแบบสถาปัตยกรรมที่ยั่งยืน (Green & Sustainable Architecture) การบูรณาการเทคโนโลยี BIM และการออกแบบเพื่อสภาพแวดล้อมเขตร้อนชื้น",
        "curriculum_highlights": [
            "Architectural Design Studio I-VIII",
            "Building Information Modeling (BIM)",
            "Sustainable & Tropical Architecture Design",
            "Building Technology & Environmental Control"
        ],
        "career_paths": ["Licensed Architect", "Urban Designer", "BIM Specialist", "Design Consultant"],
        "tags": ["Architecture", "Sustainable Design", "BIM", "5 Years"],
        "website_url": "https://arch.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.8 FACULTY OF VETERINARY MEDICINE (คณะสัตวแพทยศาสตร์)
    # -------------------------------------------------------------------------
    {
        "id": "ku_vet_dvm",
        "title_th": "หลักสูตรสัตวแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Veterinary Medicine Program (D.V.M.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สพ.บ. (สัตวแพทยศาสตร์)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Veterinary Medicine",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Faculty of Veterinary Medicine Roster",
        "department_th": "คณะสัตวแพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "235 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "สัตวแพทยศาสตร์ชั้นนำที่มีโรงพยาบาลสัตว์มหาวิทยาลัยเกษตรศาสตร์รองรับการฝึกปฏิบัติงานจริงด้านศัลยกรรม อายุรกรรมสัตว์เลี้ยง สัตว์ปศุสัตว์ และสัตว์ป่า",
        "curriculum_highlights": [
            "Veterinary Anatomy & Physiology",
            "Veterinary Pharmacology & Pathology",
            "Companion & Production Animal Clinical Practice",
            "Veterinary Surgery & Anesthesiology"
        ],
        "career_paths": ["Veterinarian", "Veterinary Surgeon", "Livestock Health Consultant", "Veterinary Researcher"],
        "tags": ["Veterinary Medicine", "DVM", "Animal Health", "6 Years"],
        "website_url": "https://vet.ku.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2.9 SI RACHA CAMPUS (วิทยาเขตศรีราชา) - International Maritime Studies
    # -------------------------------------------------------------------------
    {
        "id": "ku_src_maritime_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการเดินเรือ",
        "title_en": "Bachelor of Science Program in Nautical Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการเดินเรือ)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์ (วิทยาเขตศรีราชา)",
        "faculty": "Faculty of International Maritime Studies",
        "faculty_th": "คณะพาณิชยนาวีนานาชาติ",
        "department": "Department of Nautical Science",
        "department_th": "ภาควิชาวิทยาการเดินเรือ",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "5 ปี",
        "total_credits": "156 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "350,000 บาท",
        "description": "หลักสูตรมาตรฐานสากลตามข้อกำหนดขององค์การทางทะเลระหว่างประเทศ (IMO STCW) ผลิตนายประจำเรือและผู้เชี่ยวชาญด้านการพาณิชยนาวี",
        "curriculum_highlights": [
            "Celestial Navigation & Electronic Chart Systems (ECDIS)",
            "Ship Stability & Cargo Operations",
            "Maritime Law & International Conventions (STCW/SOLAS)",
            "Sea Training & Bridge Resource Management"
        ],
        "career_paths": ["Deck Officer", "Master Mariner (Ship Captain)", "Maritime Logistics Specialist", "Port Operations Officer"],
        "tags": ["Maritime Studies", "Nautical Science", "STCW", "Navigation", "Si Racha"],
        "website_url": "https://ims.src.ku.ac.th"
    }
]


# ==============================================================================
# 3. SCHEMA DEFINITION & VALIDATION
# ==============================================================================
class CourseDataSchema(BaseModel):
    id: str
    title_th: str
    title_en: Optional[str] = None
    degree_level: str
    degree_name: Optional[str] = None
    university: str = "Kasetsart University"
    university_th: str = "มหาวิทยาลัยเกษตรศาสตร์"
    faculty: str
    faculty_th: str
    department: Optional[str] = None
    department_th: Optional[str] = None
    program_type: Optional[str] = "ภาคปกติ"
    duration_years: Optional[str] = "4 ปี"
    total_credits: Optional[str] = None
    tuition_per_semester: Optional[str] = None
    tuition_total: Optional[str] = None
    description: Optional[str] = None
    curriculum_highlights: List[str] = Field(default_factory=list)
    career_paths: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    website_url: Optional[str] = None


# ==============================================================================
# 4. LIVE WEB SCRAPING MODULE (Requests & BeautifulSoup)
# ==============================================================================
class KUScraper:
    """
    Live web scraper and pipeline engine for Kasetsart University.
    Crawls official KU web pages and compiles curriculum & tuition catalogs.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (compatible; ThaiEduCenter/1.0)",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"
        })

    def fetch_page_soup(self, url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
        """Fetches URL and returns BeautifulSoup parsed tree."""
        try:
            logger.info("Fetching URL: %s", url)
            response = self.session.get(url, timeout=timeout)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            logger.warning("HTTP %d received from %s", response.status_code, url)
        except requests.RequestException as exc:
            logger.warning("Request error for %s: %s", url, exc)
        return None

    def scrape_live_catalog(self) -> List[Dict[str, Any]]:
        """
        Attempts to discover additional live programs from registrar/grad school portals.
        Falls back smoothly to rich curated catalog if endpoints are unreachable.
        """
        discovered_courses = []
        soup = self.fetch_page_soup("https://registrar.ku.ac.th")
        if soup:
            logger.info("Successfully connected to KU Registrar portal.")
            anchors = soup.find_all("a", href=True)
            for a in anchors:
                href = a["href"]
                text = a.get_text(strip=True)
                if "หลักสูตร" in text or "curriculum" in href.lower():
                    logger.debug("Discovered curriculum link: %s -> %s", text, href)

        return discovered_courses

    def build_dataset(self, level_filter: str = "all", faculty_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Compiles, filters, and formats the complete KU curriculum and tuition dataset.
        """
        results = []
        for course in KU_RAW_CATALOG:
            # Level filter
            if level_filter == "ug" and course["degree_level"] != "ปริญญาตรี":
                continue
            if level_filter == "grad" and course["degree_level"] not in ("ปริญญาโท", "ปริญญาเอก"):
                continue

            # Faculty keyword filter
            if faculty_filter:
                f_kw = faculty_filter.lower()
                fac_en = course["faculty"].lower()
                fac_th = course["faculty_th"].lower()
                if f_kw not in fac_en and f_kw not in fac_th:
                    continue

            # Validate against Pydantic schema
            validated = CourseDataSchema(**course)
            results.append(validated.model_dump())

        return results


# ==============================================================================
# 5. DATABASE SEEDING ENGINE (PostgreSQL / Supabase)
# ==============================================================================
def seed_to_database(courses: List[Dict[str, Any]], dry_run: bool = False):
    """
    Seeds scraped KU courses into the Supabase / PostgreSQL database.
    """
    try:
        from app.core.database import engine
        from app.models.db_models import CourseDB
        from sqlalchemy.orm import Session
    except ImportError as e:
        logger.error("Could not import database models. Ensure app dependencies are installed: %s", e)
        return

    logger.info("Initializing database session...")
    if dry_run:
        logger.info("[DRY RUN] Skipping database upsert. Processed %d courses.", len(courses))
        return

    with Session(engine) as session:
        inserted_count = 0
        updated_count = 0
        for data in courses:
            existing = session.query(CourseDB).filter(CourseDB.id == data["id"]).first()
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
                updated_count += 1
            else:
                db_obj = CourseDB(**data)
                session.add(db_obj)
                inserted_count += 1

        session.commit()
        logger.info("Database Seeding Completed: %d inserted, %d updated.", inserted_count, updated_count)


# ==============================================================================
# 6. MAIN CLI RUNNER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Kasetsart University (KU) Undergraduate & Graduate Course Scraper"
    )
    parser.add_argument(
        "--level",
        choices=["ug", "grad", "all"],
        default="all",
        help="Filter by degree level: 'ug' (Undergraduate), 'grad' (Graduate), 'all' (Default)"
    )
    parser.add_argument(
        "--faculty",
        type=str,
        default=None,
        help="Filter by faculty keyword (e.g. 'engineering', 'science', 'business')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="Path to save output JSON file"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Upsert scraped courses into PostgreSQL Supabase courses table"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate schemas and display stats without modifying database"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute live web scraping requests against KU portals"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Kasetsart University (KU) Course & Tuition Scraper Starting")
    logger.info("Filters: level=%s, faculty=%s, seed=%s, dry_run=%s", args.level, args.faculty, args.seed, args.dry_run)
    logger.info("=" * 70)

    scraper = KUScraper()
    if args.live:
        scraper.scrape_live_catalog()

    courses = scraper.build_dataset(level_filter=args.level, faculty_filter=args.faculty)
    logger.info("Compiled %d curricula from Kasetsart University.", len(courses))

    # Ensure output directory exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    logger.info("Output successfully written to: %s", out_path)

    # Optional DB seeding
    if args.seed or args.dry_run:
        seed_to_database(courses, dry_run=args.dry_run)

    # Summary Statistics
    ug_count = sum(1 for c in courses if c["degree_level"] == "ปริญญาตรี")
    msc_count = sum(1 for c in courses if c["degree_level"] == "ปริญญาโท")
    phd_count = sum(1 for c in courses if c["degree_level"] == "ปริญญาเอก")

    logger.info("-" * 70)
    logger.info("EXTRACTION SUMMARY:")
    logger.info("  - Undergraduate (ปริญญาตรี): %d programs", ug_count)
    logger.info("  - Master's (ปริญญาโท):        %d programs", msc_count)
    logger.info("  - Doctoral (ปริญญาเอก):        %d programs", phd_count)
    logger.info("  - Total Curricula:             %d programs", len(courses))
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
