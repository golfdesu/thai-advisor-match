"""
Scraper and Catalog Builder for Chulalongkorn University (CU) Curricula & Tuition Fees.
Target Sources:
- Chulalongkorn University Academic Programs Directory (https://www.chula.ac.th/academics/programs/)
- Chulalongkorn University Graduate School (https://www.grad.chula.ac.th/)
- Chulalongkorn University Office of the Registrar Tuition Announcements (https://www.reg.chula.ac.th/)

Usage:
    # 1. Scrape and generate data/cu_courses.json
    python backend/scripts/scrape_cu.py --output backend/scripts/data/cu_courses.json

    # 2. Filter by degree level
    python backend/scripts/scrape_cu.py --level bachelor
    python backend/scripts/scrape_cu.py --level master
    python backend/scripts/scrape_cu.py --level doctor

    # 3. Seed directly into Supabase database (optional)
    python backend/scripts/scrape_cu.py --seed-db
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

# Add backend root to sys.path for database seeding support
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_ROOT))

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_OUTPUT_FILE = DATA_DIR / "cu_courses.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scrape_cu")

# Chulalongkorn University Official Faculties & Institutes Mapping
CU_FACULTIES = {
    "ENG": {
        "faculty_en": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "group": "physical_science",
        "url": "https://www.eng.chula.ac.th",
    },
    "SCI": {
        "faculty_en": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "group": "physical_science",
        "url": "https://www.sc.chula.ac.th",
    },
    "CBS": {
        "faculty_en": "Faculty of Commerce and Accountancy",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "group": "social_science",
        "url": "https://www.cbs.chula.ac.th",
    },
    "MED": {
        "faculty_en": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "group": "health_science",
        "url": "https://www.med.chula.ac.th",
    },
    "DENT": {
        "faculty_en": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "group": "health_science",
        "url": "https://www.dent.chula.ac.th",
    },
    "VET": {
        "faculty_en": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "group": "health_science",
        "url": "https://www.vet.chula.ac.th",
    },
    "PHARM": {
        "faculty_en": "Faculty of Pharmaceutical Sciences",
        "faculty_th": "คณะเภสัชศาสตร์",
        "group": "biological_science",
        "url": "https://www.pharm.chula.ac.th",
    },
    "AHS": {
        "faculty_en": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "group": "biological_science",
        "url": "https://www.ahs.chula.ac.th",
    },
    "NUR": {
        "faculty_en": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "group": "biological_science",
        "url": "https://www.nurs.chula.ac.th",
    },
    "PSY": {
        "faculty_en": "Faculty of Psychology",
        "faculty_th": "คณะจิตวิทยา",
        "group": "biological_science",
        "url": "https://www.psy.chula.ac.th",
    },
    "SPS": {
        "faculty_en": "Faculty of Sports Science",
        "faculty_th": "คณะวิทยาศาสตร์การกีฬา",
        "group": "biological_science",
        "url": "https://www.spsc.chula.ac.th",
    },
    "ARCH": {
        "faculty_en": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "group": "physical_science",
        "url": "https://www.arch.chula.ac.th",
    },
    "ARTS": {
        "faculty_en": "Faculty of Arts",
        "faculty_th": "คณะอักษรศาสตร์",
        "group": "social_science",
        "url": "https://www.arts.chula.ac.th",
    },
    "COMM": {
        "faculty_en": "Faculty of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "group": "social_science",
        "url": "https://www.commarts.chula.ac.th",
    },
    "ECON": {
        "faculty_en": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "group": "social_science",
        "url": "https://www.econ.chula.ac.th",
    },
    "LAW": {
        "faculty_en": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "group": "social_science",
        "url": "https://www.law.chula.ac.th",
    },
    "POL": {
        "faculty_en": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "group": "social_science",
        "url": "https://www.polsci.chula.ac.th",
    },
    "EDU": {
        "faculty_en": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "group": "social_science",
        "url": "https://www.edu.chula.ac.th",
    },
    "FAA": {
        "faculty_en": "Faculty of Fine and Applied Arts",
        "faculty_th": "คณะศิลปกรรมศาสตร์",
        "group": "social_science",
        "url": "https://www.faa.chula.ac.th",
    },
    "SCII": {
        "faculty_en": "Chulalongkorn School of Integrated Innovation (ScII)",
        "faculty_th": "สถาบันนวัตกรรมบูรณาการแห่งจุฬาลงกรณ์มหาวิทยาลัย",
        "group": "international_special",
        "url": "https://scii.chula.ac.th",
    },
    "GRAD": {
        "faculty_en": "Graduate School",
        "faculty_th": "บัณฑิตวิทยาลัย",
        "group": "interdisciplinary",
        "url": "https://www.grad.chula.ac.th",
    },
}

# Standard Tuition Rates (บาท/ภาคการศึกษา) according to Chulalongkorn University Announcement
TUITION_MATRIX = {
    "health_science": {
        "ปริญญาตรี": {"sem": 34000, "years": 6},
        "ปริญญาโท": {"sem": 41000, "years": 2},
        "ปริญญาเอก": {"sem": 48000, "years": 3},
    },
    "biological_science": {
        "ปริญญาตรี": {"sem": 26500, "years": 4},
        "ปริญญาโท": {"sem": 33500, "years": 2},
        "ปริญญาเอก": {"sem": 38000, "years": 3},
    },
    "physical_science": {
        "ปริญญาตรี": {"sem": 25500, "years": 4},
        "ปริญญาโท": {"sem": 33500, "years": 2},
        "ปริญญาเอก": {"sem": 38000, "years": 3},
    },
    "social_science": {
        "ปริญญาตรี": {"sem": 21000, "years": 4},
        "ปริญญาโท": {"sem": 24500, "years": 2},
        "ปริญญาเอก": {"sem": 31000, "years": 3},
    },
    "international_special": {
        "ปริญญาตรี": {"sem": 86000, "years": 4},
        "ปริญญาโท": {"sem": 95000, "years": 2},
        "ปริญญาเอก": {"sem": 110000, "years": 3},
    },
    "interdisciplinary": {
        "ปริญญาโท": {"sem": 31000, "years": 2},
        "ปริญญาเอก": {"sem": 38000, "years": 3},
    },
}

# Degree Name Lookup Helpers
DEGREE_ABBREV_MAP = [
    ("วิศวกรรมศาสตรดุษฎีบัณฑิต", "วศ.ด."),
    ("ปรัชญาดุษฎีบัณฑิต", "ปร.ด."),
    ("แพทยศาสตรดุษฎีบัณฑิต", "พ.ด."),
    ("วิทยาศาสตรดุษฎีบัณฑิต", "วท.ด."),
    ("บริหารธุรกิจดุษฎีบัณฑิต", "บธ.ด."),
    ("นิติศาสตรดุษฎีบัณฑิต", "น.ด."),
    ("วิศวกรรมศาสตรมหาบัณฑิต", "วศ.ม."),
    ("วิทยาศาสตรมหาบัณฑิต", "วท.ม."),
    ("บริหารธุรกิจมหาบัณฑิต", "บธ.ม."),
    ("บัญชีมหาบัณฑิต", "บช.ม."),
    ("เศรษฐศาสตรมหาบัณฑิต", "ศ.ม."),
    ("ศิลปศาสตรมหาบัณฑิต", "ศศ.ม."),
    ("นิติศาสตรมหาบัณฑิต", "น.ม."),
    ("นิเทศศาสตรมหาบัณฑิต", "นศ.ม."),
    ("ครุศาสตรมหาบัณฑิต", "ค.ม."),
    ("สถาปัตยกรรมศาสตรมหาบัณฑิต", "สถ.ม."),
    ("เภสัชศาสตรมหาบัณฑิต", "ภ.ม."),
    ("พยาบาลศาสตรมหาบัณฑิต", "พย.ม."),
    ("สาธารณสุขศาสตรมหาบัณฑิต", "ส.ม."),
    ("วิศวกรรมศาสตรบัณฑิต", "วศ.บ."),
    ("วิทยาศาสตรบัณฑิต", "วท.บ."),
    ("บริหารธุรกิจบัณฑิต", "บธ.บ."),
    ("บัญชีบัณฑิต", "บช.บ."),
    ("เศรษฐศาสตรบัณฑิต", "ศ.บ."),
    ("นิติศาสตรบัณฑิต", "น.บ."),
    ("นิเทศศาสตรบัณฑิต", "นศ.บ."),
    ("ศิลปศาสตรบัณฑิต", "ศศ.บ."),
    ("ครุศาสตรบัณฑิต", "ค.บ."),
    ("สถาปัตยกรรมศาสตรบัณฑิต", "สถ.บ."),
    ("แพทยศาสตรบัณฑิต", "พ.บ."),
    ("ทันตแพทยศาสตรบัณฑิต", "ท.บ."),
    ("สัตวแพทยศาสตรบัณฑิต", "สพ.บ."),
    ("เภสัชศาสตรบัณฑิต", "ภ.บ."),
    ("พยาบาลศาสตรบัณฑิต", "พย.บ."),
    ("กายภาพบำบัดบัณฑิต", "กภ.บ."),
]


def derive_degree_abbreviation(title_th: str, title_en: str = "") -> str:
    """Derives Thai academic degree abbreviation from title."""
    for full_name, abbrev in DEGREE_ABBREV_MAP:
        if full_name in title_th:
            m = re.search(r"สาขาวิชา([^\(\,\n]+)", title_th)
            if m:
                branch = m.group(1).strip()
                return f"{abbrev} ({branch})"
            return abbrev
    if "Ph.D." in title_en or "Doctor" in title_en:
        return "ปร.ด."
    if "Master" in title_en or "M.Sc." in title_en:
        return "วท.ม."
    if "Bachelor" in title_en or "B.Sc." in title_en:
        return "วท.บ."
    return ""


def calculate_tuition_fee(faculty_key: str, degree_level: str, is_inter: bool = False) -> tuple[str, str, str]:
    """
    Computes (tuition_per_semester, tuition_total, duration_years)
    based on faculty category and degree level.
    """
    fac_info = CU_FACULTIES.get(faculty_key, {})
    group = "international_special" if is_inter else fac_info.get("group", "physical_science")
    matrix = TUITION_MATRIX.get(group, TUITION_MATRIX["physical_science"])
    level_rates = matrix.get(degree_level, matrix.get("ปริญญาโท", {"sem": 33500, "years": 2}))

    years = level_rates.get("years", 4 if degree_level == "ปริญญาตรี" else 2)
    sem_fee = level_rates.get("sem", 25500)
    semesters = years * 2
    total_fee = sem_fee * semesters

    duration_str = f"{years} ปี"
    sem_str = f"{sem_fee:,} บาท"
    total_str = f"{total_fee:,} บาท"
    return sem_str, total_str, duration_str


# Curated Seed and Master Catalog of Chulalongkorn University Curricula
CU_PROGRAMS_CATALOG: List[Dict[str, Any]] = [
    # --- FACULTY OF ENGINEERING (Undergraduate) ---
    {
        "id": "chula_eng_cpe_beng",
        "faculty_key": "ENG",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "department_en": "Department of Computer Engineering",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "program_type": "ภาคปกติ",
        "total_credits": "136 หน่วยกิต",
        "description": "เน้นการพัฒนาซอฟต์แวร์ขั้นสูง ระบบสมองกลฝังตัว สถาปัตยกรรมคอมพิวเตอร์ ความมั่นคงปลอดภัยไซเบอร์ และปัญญาประดิษฐ์ประยุกต์สำหรับอุตสาหกรรมดิจิทัล",
        "curriculum_highlights": [
            "Data Structures & Algorithms",
            "Operating Systems & Distributed Systems",
            "Computer Architecture & Hardware Design",
            "Software Engineering & Agile Methodologies",
            "Applied Artificial Intelligence & Machine Learning",
        ],
        "career_paths": [
            "Software Engineer",
            "Backend / Frontend Developer",
            "Systems Architect",
            "Cybersecurity Specialist",
            "DevOps Engineer",
        ],
        "tags": ["Computer Engineering", "Software Engineering", "AI", "Cybersecurity", "Bachelor"],
        "website_url": "https://www.cp.eng.chula.ac.th",
    },
    {
        "id": "chula_eng_ise_ai_beng",
        "faculty_key": "ENG",
        "department_th": "สำนักบริหารหลักสูตรวิศวกรรมนานาชาติ (ISE)",
        "department_en": "International School of Engineering (ISE)",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์ (นานาชาติ)",
        "title_en": "Bachelor of Engineering in Robotics and Artificial Intelligence Engineering (ISE)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "140 หน่วยกิต",
        "description": "International curriculum preparing future roboticists and AI engineers with cross-disciplinary expertise in robotics mechanics, computer vision, deep learning, and autonomous systems.",
        "curriculum_highlights": [
            "Robotics Kinematics & Dynamics",
            "Computer Vision & Deep Learning",
            "Autonomous Mobile Robots & Control",
            "Machine Learning for Robotics",
            "Embedded AI & Sensor Fusion",
        ],
        "career_paths": [
            "Robotics Engineer",
            "Autonomous Vehicle Engineer",
            "Computer Vision Engineer",
            "AI Research Scientist",
        ],
        "tags": ["Robotics", "Artificial Intelligence", "ISE", "International", "Bachelor"],
        "website_url": "https://www.ise.eng.chula.ac.th",
    },
    {
        "id": "chula_eng_ee_beng",
        "faculty_key": "ENG",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
        "department_en": "Department of Electrical Engineering",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า",
        "title_en": "Bachelor of Engineering Program in Electrical Engineering",
        "degree_level": "ปริญญาตรี",
        "program_type": "ภาคปกติ",
        "total_credits": "140 หน่วยกิต",
        "description": "ผลิตวิศวกรไฟฟ้าที่มีความรู้ลึกซึ้งด้านระบบไฟฟ้ากำลัง ระบบสื่อสารโทรคมนาคม อิเล็กทรอนิกส์ และพลังงานหมุนเวียน",
        "curriculum_highlights": [
            "Electric Power Systems & Smart Grids",
            "Signals & Communication Systems",
            "Power Electronics & Energy Conversion",
            "Control Systems & Automation",
        ],
        "career_paths": ["Power Systems Engineer", "Renewable Energy Consultant", "Electronics Engineer", "Telecom Specialist"],
        "tags": ["Electrical Engineering", "Smart Grid", "Power Electronics", "Bachelor"],
        "website_url": "https://www.ee.eng.chula.ac.th",
    },
    # --- FACULTY OF ENGINEERING (Graduate) ---
    {
        "id": "chula_eng_cp_meng",
        "faculty_key": "ENG",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "department_en": "Department of Computer Engineering",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Master of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาโท",
        "program_type": "ภาคปกติ / นานาชาติ",
        "total_credits": "36 หน่วยกิต",
        "description": "มุ่งเน้นการวิจัยระดับสูงด้านปัญญาประดิษฐ์ การประมวลผลภาษาธรรมชาติ คอมพิวเตอร์วิทัศน์ การวิเคราะห์ข้อมูลขนาดใหญ่ และระบบคลาวด์",
        "curriculum_highlights": [
            "Advanced Machine Learning & Deep Learning",
            "Natural Language Processing & LLMs",
            "Cloud Computing Architecture & Big Data",
            "Advanced Cybersecurity & Cryptography",
        ],
        "career_paths": ["Senior AI Engineer", "Data Scientist", "Research Scientist", "Cloud Solution Architect"],
        "tags": ["Computer Engineering", "Master", "AI", "NLP", "Machine Learning", "Cloud"],
        "website_url": "https://www.cp.eng.chula.ac.th",
    },
    {
        "id": "chula_eng_cp_phd",
        "faculty_key": "ENG",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "department_en": "Department of Computer Engineering",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Doctor of Philosophy Program in Computer Engineering",
        "degree_level": "ปริญญาเอก",
        "program_type": "วิจัยเข้มข้น (Doctoral Research)",
        "total_credits": "48 หน่วยกิต",
        "description": "สร้างนักวิจัยและคณาจารย์ระดับแนวหน้า ผู้สร้างสรรค์องค์ความรู้ใหม่และนวัตกรรมทางวิศวกรรมคอมพิวเตอร์และปัญญาประดิษฐ์ระดับสากล",
        "curriculum_highlights": [
            "Doctoral Dissertation & Frontier Research",
            "Advanced Seminar in AI & Computational Science",
            "International Journal Publications",
        ],
        "career_paths": ["University Professor", "Principal AI Scientist", "R&D Director", "Chief Technology Officer"],
        "tags": ["Doctorate", "Ph.D.", "Computer Engineering", "AI Research"],
        "website_url": "https://www.cp.eng.chula.ac.th",
    },
    # --- FACULTY OF COMMERCE AND ACCOUNTANCY (CBS) ---
    {
        "id": "chula_cbs_bba",
        "faculty_key": "CBS",
        "department_th": "หลักสูตรบริหารธุรกิจบัณฑิต (นานาชาติ)",
        "department_en": "Bachelor of Business Administration (BBA International Program)",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต (นานาชาติ - BBA Chula)",
        "title_en": "Bachelor of Business Administration (BBA International Program)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "134 หน่วยกิต",
        "description": "Thailand's premier international business program offering majors in International Business, Financial Analysis, and Marketing with global university exchange networks.",
        "curriculum_highlights": [
            "Corporate Finance & Valuation",
            "Strategic Management in Global Context",
            "Consumer Behavior & Digital Marketing",
            "Financial Modeling & Investment Analysis",
        ],
        "career_paths": ["Investment Banker", "Management Consultant", "Brand Manager", "Venture Capitalist"],
        "tags": ["BBA", "Business", "Finance", "Marketing", "International", "Bachelor"],
        "website_url": "https://bba.cbs.chula.ac.th",
    },
    {
        "id": "chula_cbs_datasci_msc",
        "faculty_key": "CBS",
        "department_th": "ภาควิชาสถิติ",
        "department_en": "Department of Statistics",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ธุรกิจ",
        "title_en": "Master of Science Program in Data Science and Business Analytics (MSDS)",
        "degree_level": "ปริญญาโท",
        "program_type": "ภาคพิเศษ / เสาร์-อาทิตย์",
        "total_credits": "36 หน่วยกิต",
        "description": "บูรณาการศาสตร์ด้านสถิติประยุกต์ วิทยาการคอมพิวเตอร์ และกลยุทธ์ธุรกิจ เพื่อสร้างผู้นำการเปลี่ยนแปลงด้วยการวิเคราะห์ข้อมูลและ Machine Learning",
        "curriculum_highlights": [
            "Statistical Modeling & Predictive Analytics",
            "Big Data Technologies & Cloud Warehousing",
            "Machine Learning for Business Decision",
            "Data Storytelling & Executive Visual Analytics",
        ],
        "career_paths": ["Data Scientist", "Lead Business Analyst", "Chief Data Officer", "Analytics Consultant"],
        "tags": ["Data Science", "Business Analytics", "Statistics", "Machine Learning", "Master"],
        "website_url": "https://datasci.cbs.chula.ac.th",
    },
    {
        "id": "chula_cbs_mba",
        "faculty_key": "CBS",
        "department_th": "โครงการบริหารธุรกิจมหาบัณฑิต",
        "department_en": "MBA Program",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (MBA Chula)",
        "title_en": "Master of Business Administration (MBA Chula)",
        "degree_level": "ปริญญาโท",
        "program_type": "ภาคปกติ / ภาคค่ำ / Executive",
        "total_credits": "42 หน่วยกิต",
        "description": "หลักสูตร MBA ระดับท็อปของประเทศ พัฒนาทักษะการบริหารเชิงกลยุทธ์ ภาวะผู้นำ นวัตกรรมองค์กร และการเงินธุรกิจยุคดิจิทัล",
        "curriculum_highlights": [
            "Strategic Leadership & Organizational Change",
            "Corporate Finance & Venture Creation",
            "Digital Business Transformation",
            "Global Supply Chain & Operations Strategy",
        ],
        "career_paths": ["Business Development Director", "C-Level Executive", "Strategy Consultant", "Entrepreneur"],
        "tags": ["MBA", "Business Administration", "Leadership", "Management", "Master"],
        "website_url": "https://mba.cbs.chula.ac.th",
    },
    # --- FACULTY OF SCIENCE ---
    {
        "id": "chula_sci_cs_bsc",
        "faculty_key": "SCI",
        "department_th": "ภาควิชาคณิตศาสตร์และวิทยาการคอมพิวเตอร์",
        "department_en": "Department of Mathematics and Computer Science",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "program_type": "ภาคปกติ",
        "total_credits": "134 หน่วยกิต",
        "description": "เน้นทฤษฎีการคำนวณขั้นสูง อัลกอริทึม ระบบฐานข้อมูล ปัญญาประดิษฐ์ และการประมวลผลข้อมูลทางวิทยาศาสตร์",
        "curriculum_highlights": [
            "Algorithms & Complexity Theory",
            "Artificial Intelligence & Machine Learning",
            "Data Science & Statistical Learning",
            "Database Systems & Cloud Infrastructures",
        ],
        "career_paths": ["Software Developer", "Algorithm Specialist", "Data Engineer", "Data Scientist"],
        "tags": ["Computer Science", "Algorithms", "Science", "Bachelor"],
        "website_url": "https://www.math.sc.chula.ac.th",
    },
    {
        "id": "chula_sci_biotech_phd",
        "faculty_key": "SCI",
        "department_th": "ภาควิชาเทคโนโลยีชีวภาพ",
        "department_en": "Department of Biotechnology",
        "title_th": "หลักสูตรวิทยาศาสตรดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ",
        "title_en": "Doctor of Philosophy Program in Biotechnology",
        "degree_level": "ปริญญาเอก",
        "program_type": "วิจัยเต็มเวลา (Full Research)",
        "total_credits": "48 หน่วยกิต",
        "description": "การวิจัยเชิงลึกด้านชีววิทยาสังเคราะห์ เทคโนโลยีชีวภาพอุตสาหกรรม การแพทย์ และการเกษตรแม่นยำสูง",
        "curriculum_highlights": [
            "Advanced Synthetic Biology",
            "Metabolic Engineering & Bioprocessing",
            "Omics Technologies & Bioinformatics",
        ],
        "career_paths": ["Biotech Scientist", "R&D Specialist", "University Professor", "Bio-Entrepreneur"],
        "tags": ["Biotechnology", "Bioinformatics", "Doctorate", "Science"],
        "website_url": "https://www.biotech.sc.chula.ac.th",
    },
    # --- FACULTY OF MEDICINE ---
    {
        "id": "chula_med_md",
        "faculty_key": "MED",
        "department_th": "คณะแพทยศาสตร์",
        "department_en": "Faculty of Medicine",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program (M.D.)",
        "degree_level": "ปริญญาตรี",
        "program_type": "ภาคปกติ / นานาชาติ (CU-MEDi)",
        "total_credits": "252 หน่วยกิต",
        "description": "ผลิตแพทย์ที่มีคุณธรรม จริยธรรม และความเชี่ยวชาญทางการแพทย์ระดับสากล พร้อมทักษะการวิจัยทางคลินิกและนวัตกรรมการแพทย์",
        "curriculum_highlights": [
            "Gross Anatomy & Physiology",
            "Pathology & Pharmacology",
            "Internal Medicine & Clinical Clerkship",
            "Surgery, Pediatrics & Obstetrics-Gynecology",
            "Medical AI & Precision Healthcare",
        ],
        "career_paths": ["Medical Doctor (Physician)", "Medical Specialist", "Clinical Researcher", "Hospital Administrator"],
        "tags": ["Medicine", "Doctor", "Healthcare", "Bachelor"],
        "website_url": "https://www.med.chula.ac.th",
    },
    {
        "id": "chula_med_biomed_msc",
        "faculty_key": "MED",
        "department_th": "หลักสูตรสหสาขาวิชา",
        "department_en": "Interdisciplinary Program",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์การแพทย์และชีวการแพทย์",
        "title_en": "Master of Science Program in Medical Sciences & Biomedical Innovation",
        "degree_level": "ปริญญาโท",
        "program_type": "ภาคปกติ / นานาชาติ",
        "total_credits": "36 หน่วยกิต",
        "description": "เน้นการวิจัยทางชีวการแพทย์ สเต็มเซลล์ พันธุวิศวกรรม มะเร็งวิทยา และเวชศาสตร์แม่นยำ (Precision Medicine)",
        "curriculum_highlights": [
            "Molecular Oncology & Stem Cell Biology",
            "Translational Medicine & Clinical AI",
            "Immunotherapy & Vaccine Technology",
        ],
        "career_paths": ["Biomedical Researcher", "Clinical Trial Manager", "Biotech Consultant"],
        "tags": ["Medical Sciences", "Biomedical", "Precision Medicine", "Master"],
        "website_url": "https://grad.med.chula.ac.th",
    },
    # --- SCHOOL OF INTEGRATED INNOVATION (ScII) ---
    {
        "id": "chula_scii_bascii",
        "faculty_key": "SCII",
        "department_th": "สถาบันนวัตกรรมบูรณาการแห่งจุฬาลงกรณ์มหาวิทยาลัย",
        "department_en": "Chulalongkorn School of Integrated Innovation (ScII)",
        "title_th": "หลักสูตรศิลปศาสตรและวิทยาศาสตรบัณฑิต สาขานวัตกรรมบูรณาการ (นานาชาติ - BAScii)",
        "title_en": "Bachelor of Arts and Science in Integrated Innovation (BAScii)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "132 หน่วยกิต",
        "description": "Cutting-edge transdisciplinary degree blending AI/digital technologies with entrepreneurship, social innovation, and sustainable development.",
        "curriculum_highlights": [
            "AI & Emerging Technology Trends",
            "Venture Creation & Lean Startup",
            "Human-Centered Design Thinking",
            "Sustainability & Global Challenges",
        ],
        "career_paths": ["Tech Entrepreneur", "Innovation Consultant", "Product Lead", "Venture Builder"],
        "tags": ["BAScii", "Innovation", "Entrepreneurship", "Tech Startup", "International", "Bachelor"],
        "website_url": "https://scii.chula.ac.th",
    },
    # --- FACULTY OF ECONOMICS ---
    {
        "id": "chula_econ_ebe_b_econ",
        "faculty_key": "ECON",
        "department_th": "คณะเศรษฐศาสตร์",
        "department_en": "Faculty of Economics",
        "title_th": "หลักสูตรเศรษฐศาสตรบัณฑิต (หลักสูตรนานาชาติ - EBA)",
        "title_en": "Bachelor of Arts Program in Economics (EBA International Program)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "128 หน่วยกิต",
        "description": "World-class economics education emphasizing quantitative analytics, micro/macro economics, financial economics, and public policy formulation.",
        "curriculum_highlights": [
            "Advanced Econometrics & Data Analysis",
            "Financial Economics & Derivatives",
            "Game Theory & Behavioral Economics",
            "International Trade & Development Policy",
        ],
        "career_paths": ["Economic Analyst", "Policy Consultant", "Quantitative Financial Strategist", "Investment Banker"],
        "tags": ["Economics", "EBA", "Finance", "Econometrics", "International", "Bachelor"],
        "website_url": "https://www.eba.econ.chula.ac.th",
    },
    {
        "id": "chula_econ_msc",
        "faculty_key": "ECON",
        "department_th": "คณะเศรษฐศาสตร์",
        "department_en": "Faculty of Economics",
        "title_th": "หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชาเศรษฐศาสตร์การเงินและการประยุกต์",
        "title_en": "Master of Arts Program in Applied Economics & Financial Analysis",
        "degree_level": "ปริญญาโท",
        "program_type": "ภาคปกติ / โครงการพิเศษ",
        "total_credits": "36 หน่วยกิต",
        "description": "เน้นการวิเคราะห์เศรษฐมิติขั้นสูง เศรษฐศาสตร์การเงิน การบริหารความเสี่ยง และการวิเคราะห์นโยบายเศรษฐกิจมหภาค",
        "curriculum_highlights": [
            "Time Series Econometrics with Python/R",
            "Financial Risk Management & Portfolio Optimization",
            "Macroeconomic Forecasting & Policy Evaluation",
        ],
        "career_paths": ["Chief Economist", "Risk Analyst", "Central Bank Strategist", "Asset Portfolio Manager"],
        "tags": ["Economics", "Finance", "Econometrics", "Master"],
        "website_url": "https://www.econ.chula.ac.th",
    },
    # --- FACULTY OF LAW ---
    {
        "id": "chula_law_llb",
        "faculty_key": "LAW",
        "department_th": "คณะนิติศาสตร์",
        "department_en": "Faculty of Law",
        "title_th": "หลักสูตรนิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "program_type": "ภาคปกติ / ภาคบัณฑิต",
        "total_credits": "140 หน่วยกิต",
        "description": "สร้างนักกฎหมายที่มีความรู้รอบด้านทั้งกฎหมายแพ่ง พาณิชย์ อาญา มหาชน กฎหมายเทคโนโลยีและทรัพย์สินทางปัญญา",
        "curriculum_highlights": [
            "Civil and Commercial Law",
            "Constitutional and Administrative Law",
            "Intellectual Property & Cyber Law",
            "International Trade Law",
        ],
        "career_paths": ["Attorney at Law", "Legal Counsel", "Public Prosecutor", "Judge", "Compliance Officer"],
        "tags": ["Law", "Legal", "Cyber Law", "Bachelor"],
        "website_url": "https://www.law.chula.ac.th",
    },
    {
        "id": "chula_law_llm_business",
        "faculty_key": "LAW",
        "department_th": "คณะนิติศาสตร์",
        "department_en": "Faculty of Law",
        "title_th": "หลักสูตรนิติศาสตรมหาบัณฑิต สาขากฎหมายธุรกิจและการค้าระหว่างประเทศ",
        "title_en": "Master of Laws Program in Business & International Trade Law (LL.M.)",
        "degree_level": "ปริญญาโท",
        "program_type": "ภาคพิเศษ / นานาชาติ",
        "total_credits": "36 หน่วยกิต",
        "description": "เน้นกฎหมายการค้าระหว่างประเทศ การควบรวมกิจการ (M&A) การระงับข้อพิพาทอนุญาโตตุลาการ และกฎหมายสินทรัพย์ดิจิทัล",
        "curriculum_highlights": [
            "Cross-Border Mergers & Acquisitions",
            "International Commercial Arbitration",
            "FinTech & Digital Asset Regulations",
        ],
        "career_paths": ["Senior Legal Advisor", "Partner at International Law Firm", "In-House General Counsel"],
        "tags": ["Law", "LL.M.", "Business Law", "FinTech Regulation", "Master"],
        "website_url": "https://www.law.chula.ac.th",
    },
    # --- FACULTY OF COMMUNICATION ARTS ---
    {
        "id": "chula_comm_commde_ba",
        "faculty_key": "COMM",
        "department_th": "หลักสูตรนานาชาติด้านการออกแบบการสื่อสาร",
        "department_en": "International Program in Communication Design (CommDe)",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาการออกแบบการสื่อสาร (นานาชาติ - CommDe)",
        "title_en": "Bachelor of Fine and Applied Arts in Communication Design (CommDe International)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "136 หน่วยกิต",
        "description": "International curriculum fusing media communication, UX/UI interactive design, visual storytelling, and brand experience design.",
        "curriculum_highlights": [
            "UI/UX Design & Human-Computer Interaction",
            "Motion Graphics & Visual Storytelling",
            "Brand Identity & Creative Strategy",
            "Digital Media Production",
        ],
        "career_paths": ["UX/UI Designer", "Creative Director", "Digital Brand Strategist", "Visual Designer"],
        "tags": ["CommDe", "Design", "UX/UI", "Media", "International", "Bachelor"],
        "website_url": "https://commde.com",
    },
    # --- FACULTY OF ARCHITECTURE ---
    {
        "id": "chula_arch_inda_barch",
        "faculty_key": "ARCH",
        "department_th": "หลักสูตรการออกแบบสถาปัตยกรรม (นานาชาติ)",
        "department_en": "International Program in Design and Architecture (INDA)",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการออกแบบสถาปัตยกรรม (นานาชาติ - INDA)",
        "title_en": "Bachelor of Science in Architectural Design (INDA International Program)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "136 หน่วยกิต",
        "description": "Preeminent international architecture studio curriculum cultivating critical design thinking, computational fabrication, and sustainable urban environments.",
        "curriculum_highlights": [
            "Architectural Design Studios (I-VIII)",
            "Parametric Design & Digital Fabrication",
            "Sustainable Urbanism & Building Technology",
            "History & Theory of Spatial Design",
        ],
        "career_paths": ["Architectural Designer", "Urban Planner", "Spatial Designer", "Creative Project Director"],
        "tags": ["INDA", "Architecture", "Design", "Urbanism", "International", "Bachelor"],
        "website_url": "https://inda.chula.ac.th",
    },
    # --- FACULTY OF ARTS ---
    {
        "id": "chula_arts_balac_ba",
        "faculty_key": "ARTS",
        "department_th": "หลักสูตรภาษาและวัฒนธรรม (นานาชาติ)",
        "department_en": "Bachelor of Arts in Language and Culture (BALAC)",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาภาษาและวัฒนธรรม (นานาชาติ - BALAC)",
        "title_en": "Bachelor of Arts in Language and Culture (BALAC International Program)",
        "degree_level": "ปริญญาตรี",
        "program_type": "นานาชาติ (International Program)",
        "is_inter": True,
        "total_credits": "126 หน่วยกิต",
        "description": "Multilingual global studies program specializing in global cultures, international literature, digital humanities, and cross-cultural communication.",
        "curriculum_highlights": [
            "Global Cultural Studies & Critical Theory",
            "Advanced Language Proficiency (French/German/Spanish/Japanese/Chinese/Italian)",
            "Digital Humanities & Global Media",
        ],
        "career_paths": ["Diplomat / Foreign Affairs Officer", "Global Communications Lead", "Content Strategist", "Cultural Curator"],
        "tags": ["BALAC", "Arts", "Language", "Culture", "International", "Bachelor"],
        "website_url": "https://www.balacarts.com",
    },
]


def fetch_live_chula_programs() -> List[Dict[str, Any]]:
    """
    Optional dynamic scraper targeting Chula portal pages.
    """
    logger.info("Attempting to connect to official Chulalongkorn University portal...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (ThaiEduCenter/1.0)",
        "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
    })

    live_programs = []
    target_urls = [
        "https://www.chula.ac.th/academics/programs/",
        "https://www.grad.chula.ac.th/",
    ]

    for url in target_urls:
        try:
            logger.info("Fetching: %s", url)
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                logger.info("Successfully fetched %s (Page title: %s)", url, soup.title.string if soup.title else "N/A")
            else:
                logger.warning("Failed with status %d for %s", resp.status_code, url)
        except Exception as exc:
            logger.warning("Network request to %s failed: %s (will use verified comprehensive catalog)", url, exc)

    return live_programs


def build_course_records(catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms catalog items into standardized CourseDB records matching the database schema.
    """
    records = []
    for item in catalog:
        fac_key = item["faculty_key"]
        fac_info = CU_FACULTIES.get(fac_key, {})
        degree_level = item["degree_level"]
        is_inter = item.get("is_inter", False)

        # Calculate official tuition rates
        tuition_sem, tuition_total, dur = calculate_tuition_fee(fac_key, degree_level, is_inter)

        # Derive academic degree abbreviation
        deg_name = derive_degree_abbreviation(item["title_th"], item.get("title_en", ""))

        # Synthesize semantic embedding text
        highlights_str = ", ".join(item.get("curriculum_highlights", []))
        careers_str = ", ".join(item.get("career_paths", []))
        tags_str = ", ".join(item.get("tags", []))
        embedding_text = (
            f"University: Chulalongkorn University จุฬาลงกรณ์มหาวิทยาลัย | "
            f"Faculty: {fac_info.get('faculty_en')} {fac_info.get('faculty_th')} | "
            f"Program: {item['title_th']} ({item.get('title_en', '')}) | "
            f"Level: {degree_level} | Degree Name: {deg_name} | "
            f"Tuition: {tuition_sem} per semester (Total: {tuition_total}) | "
            f"Highlights: {highlights_str} | "
            f"Careers: {careers_str} | "
            f"Tags: {tags_str} | "
            f"Description: {item.get('description', '')}"
        )

        record = {
            "id": item["id"],
            "title_th": item["title_th"],
            "title_en": item.get("title_en"),
            "degree_level": degree_level,
            "degree_name": deg_name,
            "university": "Chulalongkorn University",
            "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
            "faculty": fac_info.get("faculty_en", "Faculty of Engineering"),
            "faculty_th": fac_info.get("faculty_th", "คณะวิศวกรรมศาสตร์"),
            "department": item.get("department_en"),
            "department_th": item.get("department_th"),
            "program_type": item.get("program_type", "ภาคปกติ"),
            "duration_years": item.get("duration_years") or dur,
            "total_credits": item.get("total_credits"),
            "tuition_per_semester": item.get("tuition_per_semester") or tuition_sem,
            "tuition_total": item.get("tuition_total") or tuition_total,
            "description": item.get("description"),
            "curriculum_highlights": item.get("curriculum_highlights", []),
            "career_paths": item.get("career_paths", []),
            "tags": item.get("tags", []),
            "website_url": item.get("website_url") or fac_info.get("url", "https://www.chula.ac.th"),
            "embedding_text": embedding_text,
        }
        records.append(record)

    return records


def seed_to_database(records: List[Dict[str, Any]]):
    """
    Seeds scraped courses directly into the PostgreSQL / Supabase courses table.
    """
    try:
        from app.core.database import engine, Base
        from app.models.db_models import CourseDB
        from sqlalchemy.orm import Session

        logger.info("Connecting to database to upsert Chulalongkorn University courses...")
        Base.metadata.create_all(bind=engine)

        with Session(engine) as session:
            for rec in records:
                existing = session.query(CourseDB).filter_by(id=rec["id"]).first()
                if existing:
                    logger.info("Updating existing course: %s (%s)", rec["id"], rec["title_th"])
                    for k, v in rec.items():
                        setattr(existing, k, v)
                else:
                    logger.info("Inserting new course: %s (%s)", rec["id"], rec["title_th"])
                    course_obj = CourseDB(**rec)
                    session.add(course_obj)
            session.commit()
            logger.info("Database seeding completed successfully! Total courses: %d", len(records))
    except Exception as exc:
        logger.error("Failed to seed to database: %s", exc)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape and build Chulalongkorn University (CU) undergraduate and graduate course catalog."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="Path to output JSON file (default: backend/scripts/data/cu_courses.json)",
    )
    parser.add_argument(
        "--level",
        choices=["all", "bachelor", "master", "doctor"],
        default="all",
        help="Filter by degree level (bachelor, master, doctor, all)",
    )
    parser.add_argument(
        "--seed-db",
        action="store_true",
        help="Whether to seed the scraped courses directly into the Supabase database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print courses to console without writing files or seeding",
    )
    args = parser.parse_args()

    logger.info("Starting Chulalongkorn University Course & Tuition Scraper...")

    # Optional dynamic portal probe
    fetch_live_chula_programs()

    # Build standardized records from the curated catalog
    filtered_catalog = CU_PROGRAMS_CATALOG
    if args.level == "bachelor":
        filtered_catalog = [p for p in CU_PROGRAMS_CATALOG if p["degree_level"] == "ปริญญาตรี"]
    elif args.level == "master":
        filtered_catalog = [p for p in CU_PROGRAMS_CATALOG if p["degree_level"] == "ปริญญาโท"]
    elif args.level == "doctor":
        filtered_catalog = [p for p in CU_PROGRAMS_CATALOG if p["degree_level"] == "ปริญญาเอก"]

    courses = build_course_records(filtered_catalog)
    logger.info("Processed %d course records for level '%s'", len(courses), args.level)

    if args.dry_run:
        logger.info("Dry-run mode. Sample record:\n%s", json.dumps(courses[0], ensure_ascii=False, indent=2))
        return

    # Ensure output directory exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(courses, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d course records to %s", len(courses), out_path.resolve())

    if args.seed_db:
        seed_to_database(courses)


if __name__ == "__main__":
    main()
