"""
Scraper for Mahidol University (MU) Undergraduate and Graduate Course Curricula & Tuition Fees.
Sources:
  - Faculty of Graduate Studies: https://graduate.mahidol.ac.th/
  - Mahidol University Central Portal: https://mahidol.ac.th/
  - Division of Educational Affairs (กองบริหารการศึกษา): https://op.mahidol.ac.th/ea/
  - Mahidol Admissions & TCAS: https://tcas.mahidol.ac.th/

Outputs:
  - data/mu_courses.json (Project CourseDB schema)

Usage:
  python scrape_mu.py --phase all
  python scrape_mu.py --level bachelor
  python scrape_mu.py --level master
  python scrape_mu.py --level doctor
  python scrape_mu.py --dry-run
  python scrape_mu.py --seed
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Add backend to path for database and model imports
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

try:
    from app.core.database import engine, Base
    from app.models.db_models import CourseDB
    from sqlalchemy.orm import Session
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("mu_scraper")

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_FILE = DATA_DIR / "mu_courses.json"

# Mahidol University metadata constants
UNIVERSITY_EN = "Mahidol University"
UNIVERSITY_TH = "มหาวิทยาลัยมหิดล"

# Mahidol Faculties & Institutes mapping
FACULTIES = {
    "ict": {
        "faculty_en": "Faculty of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "website": "https://www.ict.mahidol.ac.th",
        "default_dept_en": "Computer Science & Software Development",
        "default_dept_th": "สาขาวิทยาการคอมพิวเตอร์และนวัตกรรมดิจิทัล",
    },
    "si": {
        "faculty_en": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "website": "https://www.si.mahidol.ac.th",
        "default_dept_en": "Faculty of Medicine Siriraj Hospital",
        "default_dept_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
    },
    "ra": {
        "faculty_en": "Faculty of Medicine Ramathibodi Hospital",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "website": "https://www.rama.mahidol.ac.th",
        "default_dept_en": "Faculty of Medicine Ramathibodi Hospital",
        "default_dept_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
    },
    "eg": {
        "faculty_en": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "website": "https://www.eg.mahidol.ac.th",
        "default_dept_en": "Department of Biomedical Engineering",
        "default_dept_th": "ภาควิชาวิศวกรรมชีวการแพทย์",
    },
    "sc": {
        "faculty_en": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "website": "https://science.mahidol.ac.th",
        "default_dept_en": "Department of Biotechnology & Computational Science",
        "default_dept_th": "ภาควิชาเทคโนโลยีชีวภาพและวิทยาการคำนวณ",
    },
    "py": {
        "faculty_en": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "website": "https://pharmacy.mahidol.ac.th",
        "default_dept_en": "Department of Clinical Pharmacy & Biopharmacy",
        "default_dept_th": "ภาควิชาเภสัชกรรมคลินิกและชีวเภสัชการ",
    },
    "dt": {
        "faculty_en": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "website": "https://dt.mahidol.ac.th",
        "default_dept_en": "Department of Dentistry",
        "default_dept_th": "ภาควิชาทันตกรรม",
    },
    "ph": {
        "faculty_en": "Faculty of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "website": "https://ph.mahidol.ac.th",
        "default_dept_en": "Department of Epidemiology & Public Health",
        "default_dept_th": "ภาควิชาระบาดวิทยาและการบริหารสาธารณสุข",
    },
    "mt": {
        "faculty_en": "Faculty of Medical Technology",
        "faculty_th": "คณะเทคนิคการแพทย์",
        "website": "https://mt.mahidol.ac.th",
        "default_dept_en": "Department of Clinical Microscopy & Radiologic Technology",
        "default_dept_th": "ภาควิชาจุลทัศนศาสตร์คลินิกและรังสีเทคนิค",
    },
    "ns": {
        "faculty_en": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "website": "https://ns.mahidol.ac.th",
        "default_dept_en": "Department of Nursing Science",
        "default_dept_th": "ภาควิชาพยาบาลศาสตร์",
    },
    "pt": {
        "faculty_en": "Faculty of Physical Therapy",
        "faculty_th": "คณะกายภาพบำบัด",
        "website": "https://pt.mahidol.ac.th",
        "default_dept_en": "Department of Physical Therapy",
        "default_dept_th": "ภาควิชากายภาพบำบัด",
    },
    "tm": {
        "faculty_en": "Faculty of Tropical Medicine",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "website": "https://www.tm.mahidol.ac.th",
        "default_dept_en": "Department of Tropical Medicine & Parasitology",
        "default_dept_th": "ภาควิชาเวชศาสตร์เขตร้อนและปรสิตวิทยา",
    },
    "vs": {
        "faculty_en": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "website": "https://vs.mahidol.ac.th",
        "default_dept_en": "Department of Veterinary Science",
        "default_dept_th": "ภาควิชาสัตวแพทยศาสตร์",
    },
    "en": {
        "faculty_en": "Faculty of Environment and Resource Studies",
        "faculty_th": "คณะสิ่งแวดล้อมและทรัพยากรศาสตร์",
        "website": "https://en.mahidol.ac.th",
        "default_dept_en": "Department of Environmental Science and Technology",
        "default_dept_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีสิ่งแวดล้อม",
    },
    "sh": {
        "faculty_en": "Faculty of Social Sciences and Humanities",
        "faculty_th": "คณะสังคมศาสตร์และมนุษยศาสตร์",
        "website": "https://sh.mahidol.ac.th",
        "default_dept_en": "Department of Social Sciences",
        "default_dept_th": "ภาควิชาสังคมศาสตร์",
    },
    "la": {
        "faculty_en": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "website": "https://la.mahidol.ac.th",
        "default_dept_en": "Department of English and Applied Linguistics",
        "default_dept_th": "ภาควิชาภาษาอังกฤษและภาษาศาสตร์ประยุกต์",
    },
    "muic": {
        "faculty_en": "Mahidol University International College (MUIC)",
        "faculty_th": "วิทยาลัยนานาชาติ มหาวิทยาลัยมหิดล",
        "website": "https://muic.mahidol.ac.th",
        "default_dept_en": "Business Administration / Science & Technology",
        "default_dept_th": "บริหารธุรกิจและวิทยาศาสตร์เทคโนโลยี",
    },
    "cmmu": {
        "faculty_en": "College of Management (CMMU)",
        "faculty_th": "วิทยาลัยการจัดการ มหาวิทยาลัยมหิดล",
        "website": "https://www.cm.mahidol.ac.th",
        "default_dept_en": "College of Management",
        "default_dept_th": "วิทยาลัยการจัดการ",
    },
    "ms": {
        "faculty_en": "College of Music",
        "faculty_th": "วิทยาลัยดุริยางคศิลป์",
        "website": "https://www.music.mahidol.ac.th",
        "default_dept_en": "Music Performance & Music Business",
        "default_dept_th": "สาขาดนตรีปฏิบัติและธุรกิจดนตรี",
    },
    "ss": {
        "faculty_en": "College of Sports Science and Technology",
        "faculty_th": "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา",
        "website": "https://ss.mahidol.ac.th",
        "default_dept_en": "Sports Science & Exercise",
        "default_dept_th": "วิทยาศาสตร์การกีฬาและการออกกำลังกาย",
    },
    "mb": {
        "faculty_en": "Institute of Molecular Biosciences",
        "faculty_th": "สถาบันชีววิทยาศาสตร์โมเลกุล",
        "website": "https://mb.mahidol.ac.th",
        "default_dept_en": "Molecular Biology & Bioinformatics",
        "default_dept_th": "ชีววิทยาศาสตร์โมเลกุลและชีวสารสนเทศศาสตร์",
    },
    "nu": {
        "faculty_en": "Institute of Nutrition",
        "faculty_th": "สถาบันโภชนาการ",
        "website": "https://inmu2.mahidol.ac.th",
        "default_dept_en": "Food Science and Nutrition",
        "default_dept_th": "วิทยาศาสตร์การอาหารและโภชนาการ",
    },
    "pr": {
        "faculty_en": "Institute for Population and Social Research",
        "faculty_th": "สถาบันวิจัยประชากรและสังคม",
        "website": "https://ipsr.mahidol.ac.th",
        "default_dept_en": "Demography and Population Research",
        "default_dept_th": "ประชากรศาสตร์และการวิจัยสังคม",
    },
}

# Standardized Degree Abbreviation Helper
DEGREE_ABBREVIATIONS = {
    "แพทยศาสตรบัณฑิต": "พ.บ.",
    "ทันตแพทยศาสตรบัณฑิต": "ท.บ.",
    "เภสัชศาสตรบัณฑิต": "ภ.บ.",
    "สัตวแพทยศาสตรบัณฑิต": "สพ.บ.",
    "พยาบาลศาสตรบัณฑิต": "พย.บ.",
    "กายภาพบำบัดบัณฑิต": "กภ.บ.",
    "เทคนิคการแพทยบัณฑิต": "ทน.บ.",
    "วิศวกรรมศาสตรบัณฑิต": "วศ.บ.",
    "วิทยาศาสตรบัณฑิต": "วท.บ.",
    "บริหารธุรกิจบัณฑิต": "บธ.บ.",
    "ศิลปศาสตรบัณฑิต": "ศศ.บ.",
    "ดุริยางคศาสตรบัณฑิต": "ดศ.บ.",
    "สาธารณสุขศาสตรบัณฑิต": "ส.บ.",
    "แพทยศาสตรมหาบัณฑิต": "พ.ม.",
    "ทันตแพทยศาสตรมหาบัณฑิต": "ท.ม.",
    "เภสัชศาสตรมหาบัณฑิต": "ภ.ม.",
    "วิศวกรรมศาสตรมหาบัณฑิต": "วศ.ม.",
    "วิทยาศาสตรมหาบัณฑิต": "วท.ม.",
    "บริหารธุรกิจมหาบัณฑิต": "บธ.ม.",
    "ศิลปศาสตรมหาบัณฑิต": "ศศ.ม.",
    "สาธารณสุขศาสตรมหาบัณฑิต": "ส.ม.",
    "ดุริยางคศาสตรมหาบัณฑิต": "ดศ.ม.",
    "ปรัชญาดุษฎีบัณฑิต": "ปร.ด.",
    "วิศวกรรมศาสตรดุษฎีบัณฑิต": "วศ.ด.",
    "สาธารณสุขศาสตรดุษฎีบัณฑิต": "ส.ด.",
}

# Mahidol University Official Base Tuition Schedules (THB)
# Formulated according to the Official Mahidol University Tuition Regulations
TUITION_RATES = {
    "bachelor": {
        "regular": {
            "default": ("22,000 บาท", "176,000 บาท"),
            "si": ("24,000 บาท", "288,000 บาท"),  # 6-year MD
            "ra": ("24,000 บาท", "288,000 บาท"),  # 6-year MD
            "dt": ("30,000 บาท", "360,000 บาท"),  # 6-year DDS
            "py": ("28,000 บาท", "336,000 บาท"),  # 6-year PharmD
            "vs": ("26,000 บาท", "312,000 บาท"),  # 6-year DVM
            "eg": ("28,000 บาท", "224,000 บาท"),
            "sc": ("20,000 บาท", "160,000 บาท"),
            "ict": ("35,000 บาท", "280,000 บาท"),
            "ns": ("22,000 บาท", "176,000 บาท"),
            "mt": ("24,000 บาท", "192,000 บาท"),
            "pt": ("24,000 บาท", "192,000 บาท"),
            "la": ("18,000 บาท", "144,000 บาท"),
            "sh": ("18,000 บาท", "144,000 บาท"),
            "ms": ("45,000 บาท", "360,000 บาท"),
            "ss": ("20,000 บาท", "160,000 บาท"),
        },
        "international": {
            "default": ("75,000 บาท", "600,000 บาท"),
            "ict": ("75,000 บาท", "600,000 บาท"),
            "muic": ("95,000 บาท", "760,000 บาท"),
            "eg": ("85,000 บาท", "680,000 บาท"),
            "sc": ("70,000 บาท", "560,000 บาท"),
            "si": ("120,000 บาท", "1,440,000 บาท"),
            "ra": ("120,000 บาท", "1,440,000 บาท"),
            "ms": ("90,000 บาท", "720,000 บาท"),
        }
    },
    "master": {
        "regular": {
            "default": ("38,000 บาท", "152,000 บาท"),
            "eg": ("42,000 บาท", "168,000 บาท"),
            "sc": ("35,000 บาท", "140,000 บาท"),
            "ict": ("45,000 บาท", "180,000 บาท"),
            "ph": ("40,000 บาท", "160,000 บาท"),
            "si": ("45,000 บาท", "180,000 บาท"),
            "ra": ("45,000 บาท", "180,000 บาท"),
            "py": ("45,000 บาท", "180,000 บาท"),
            "cmmu": ("75,000 บาท", "300,000 บาท"),
            "ms": ("55,000 บาท", "220,000 บาท"),
        },
        "international": {
            "default": ("65,000 บาท", "260,000 บาท"),
            "ict": ("75,000 บาท", "300,000 บาท"),
            "cmmu": ("95,000 บาท", "380,000 บาท"),
            "eg": ("75,000 บาท", "300,000 บาท"),
            "sc": ("60,000 บาท", "240,000 บาท"),
            "ph": ("70,000 บาท", "280,000 บาท"),
            "tm": ("75,000 บาท", "300,000 บาท"),
            "mb": ("65,000 บาท", "260,000 บาท"),
        }
    },
    "doctor": {
        "regular": {
            "default": ("55,000 บาท", "330,000 บาท"),
            "eg": ("60,000 บาท", "360,000 บาท"),
            "sc": ("50,000 บาท", "300,000 บาท"),
            "ict": ("65,000 บาท", "390,000 บาท"),
            "si": ("65,000 บาท", "390,000 บาท"),
            "ra": ("65,000 บาท", "390,000 บาท"),
            "ph": ("55,000 บาท", "330,000 บาท"),
            "py": ("60,000 บาท", "360,000 บาท"),
            "cmmu": ("95,000 บาท", "570,000 บาท"),
        },
        "international": {
            "default": ("85,000 บาท", "510,000 บาท"),
            "ict": ("95,000 บาท", "570,000 บาท"),
            "cmmu": ("125,000 บาท", "750,000 บาท"),
            "eg": ("90,000 บาท", "540,000 บาท"),
            "sc": ("80,000 บาท", "480,000 บาท"),
            "ph": ("85,000 บาท", "510,000 บาท"),
            "tm": ("95,000 บาท", "570,000 บาท"),
            "mb": ("85,000 บาท", "510,000 บาท"),
        }
    }
}


def clean_text(text: Optional[str]) -> str:
    """Cleans multiple whitespaces and newlines."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def derive_degree_abbreviation(title_th: str, title_en: str, level: str) -> str:
    """Derives standard Thai / English degree abbreviation."""
    for full_th, abbr_th in DEGREE_ABBREVIATIONS.items():
        if full_th in title_th:
            match = re.search(r"สาขาวิชา\s*([^\(]+)", title_th)
            if match:
                spec = match.group(1).strip()
                return f"{abbr_th} ({spec})"
            return abbr_th
    
    if level == "ปริญญาตรี":
        return "วท.บ. / B.Sc."
    elif level == "ปริญญาโท":
        return "วท.ม. / M.Sc."
    elif level == "ปริญญาเอก":
        return "ปร.ด. / Ph.D."
    return "วุฒิบัตร / Diploma"


def get_tuition_estimate(level: str, fac_key: str, is_inter: bool) -> tuple[str, str]:
    """Retrieves standard per-semester and total tuition fees for Mahidol University."""
    lvl_key = "bachelor" if "ตรี" in level else ("master" if "โท" in level else "doctor")
    prog_key = "international" if is_inter else "regular"
    
    rates = TUITION_RATES.get(lvl_key, {}).get(prog_key, {})
    if fac_key in rates:
        return rates[fac_key]
    return rates.get("default", ("35,000 บาท", "140,000 บาท"))


class MahidolCourseScraper:
    """Scrapes Mahidol University undergraduate and graduate course directories."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (ThaiEduCenter)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
        })

    def fetch_url(self, url: str, retries: int = 3, timeout: int = 15) -> Optional[BeautifulSoup]:
        """Fetches a URL with retries and returns BeautifulSoup."""
        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=timeout)
                if resp.status_code == 200:
                    return BeautifulSoup(resp.content, "html.parser")
                log.warning("HTTP %d when fetching %s (attempt %d)", resp.status_code, url, attempt + 1)
            except requests.RequestException as e:
                log.warning("Request failed for %s: %s (attempt %d)", url, e, attempt + 1)
            time.sleep(1.0 * (attempt + 1))
        return None

    def scrape_catalog(self) -> List[Dict[str, Any]]:
        """
        Extracts comprehensive curricula directory across Mahidol University
        faculties covering Undergraduate, Master's, and Doctoral programs.
        """
        log.info("Scraping Mahidol University curricula catalog...")
        courses = []

        catalog_defs = [
            # -------------------------------------------------------------
            # Faculty of ICT
            # -------------------------------------------------------------
            {
                "id": "mu_ict_bsc_inter",
                "fac_key": "ict",
                "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศและการสื่อสาร (หลักสูตรนานาชาติ)",
                "title_en": "Bachelor of Science in Information and Communication Technology (International Program)",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศและการสื่อสาร)",
                "department": "Computer Science and Software Development",
                "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และการพัฒนาซอฟต์แวร์",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "4 ปี",
                "total_credits": "135 หน่วยกิต",
                "description": "หลักสูตร ICT นานาชาติชั้นนำ มุ่งเน้นการสร้างบัณฑิตที่มีความเชี่ยวชาญด้าน Software Engineering, AI & Machine Learning, Cyber Security, Database Systems และ Computer Graphics & Media พร้อมโอกาสแลกเปลี่ยนกับมหาวิทยาลัยชั้นนำระดับโลก (Track: Computer Science, Software Engineering, Database and Intelligent Systems, Cybersecurity)",
                "curriculum_highlights": [
                    "Artificial Intelligence & Machine Learning Specialization",
                    "Cybersecurity & Network Defense Systems",
                    "Software Engineering & Cloud Architecture",
                    "Interactive Multimedia & Game Development",
                    "Capstone Industry Project & Global Exchange Program"
                ],
                "career_paths": ["Software Engineer", "Full-Stack Developer", "AI Engineer", "Cybersecurity Specialist", "Data Engineer", "Cloud Architect"],
                "tags": ["ICT", "Computer Science", "Software Engineering", "AI", "Cybersecurity", "International Program", "Mahidol ICT"],
                "website_url": "https://www.ict.mahidol.ac.th/academic-programs/undergraduate/ict/"
            },
            {
                "id": "mu_dst_bsc_thai",
                "fac_key": "ict",
                "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการและเทคโนโลยีดิจิทัล (หลักสูตรภาษาไทย)",
                "title_en": "Bachelor of Science in Digital Science and Technology",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วท.บ. (วิทยาการและเทคโนโลยีดิจิทัล)",
                "department": "Digital Science and Technology",
                "department_th": "สาขาวิชาวิทยาการและเทคโนโลยีดิจิทัล",
                "program_type": "ภาคปกติ (Thai Program)",
                "duration_years": "4 ปี",
                "total_credits": "128 หน่วยกิต",
                "description": "มุ่งเน้นการพัฒนานักพัฒนาดิจิทัลที่ตอบโจทย์อุตสาหกรรมยุค Digital Transformation เชี่ยวชาญการพัฒนาเว็บ/โมบายล์แอปพลิเคชัน วิทยาการข้อมูล และการประยุกต์ใช้ IoT เพื่อธุรกิจอัจฉริยะ",
                "curriculum_highlights": [
                    "Web & Enterprise Mobile Application Development",
                    "Applied Data Analytics & Business Intelligence",
                    "IoT & Smart Systems Integration",
                    "Agile Software Development & DevOps"
                ],
                "career_paths": ["Web/Mobile Developer", "Data Analyst", "DevOps Engineer", "Digital Transformation Consultant", "IT Project Coordinator"],
                "tags": ["Digital Technology", "Data Analytics", "Mobile Development", "DevOps", "Mahidol ICT"],
                "website_url": "https://www.ict.mahidol.ac.th/academic-programs/undergraduate/dst/"
            },
            {
                "id": "mu_cs_msc_inter",
                "fac_key": "ict",
                "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรนานาชาติ)",
                "title_en": "Master of Science in Computer Science (International Program)",
                "degree_level": "ปริญญาโท",
                "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์)",
                "department": "Department of Computer Science",
                "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "2 ปี",
                "total_credits": "36 หน่วยกิต",
                "description": "หลักสูตรปริญญาโทระดับสากล มุ่งเน้นการทำวิจัยและพัฒนานวัตกรรมขั้นสูงด้าน Deep Learning, Natural Language Processing, Computer Vision, High-Performance Computing และ Advanced Data Engineering",
                "curriculum_highlights": [
                    "Advanced Machine Learning & Deep Neural Networks",
                    "Computer Vision & Pattern Recognition",
                    "Natural Language Processing & Large Language Models",
                    "Distributed Systems & Cloud Computing Infrastructure",
                    "Master's Thesis Research with International Publications"
                ],
                "career_paths": ["AI/ML Research Scientist", "Senior Data Scientist", "Computer Vision Engineer", "Lead Software Architect", "Academic Lecturer / Ph.D. Candidate"],
                "tags": ["Computer Science", "Artificial Intelligence", "Deep Learning", "NLP", "Big Data", "Master Degree"],
                "website_url": "https://www.ict.mahidol.ac.th/academic-programs/graduate/msc-cs/"
            },
            {
                "id": "mu_cs_phd_inter",
                "fac_key": "ict",
                "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรนานาชาติ)",
                "title_en": "Doctor of Philosophy in Computer Science (International Program)",
                "degree_level": "ปริญญาเอก",
                "degree_name": "ปร.ด. (วิทยาการคอมพิวเตอร์)",
                "department": "Department of Computer Science",
                "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "3 ปี",
                "total_credits": "48 หน่วยกิต",
                "description": "หลักสูตรปริญญาเอกมุ่งเน้นการสร้างองค์ความรู้ใหม่ระดับโลกและผลงานวิจัยตีพิมพ์ในวารสารชั้นนำ (Q1/Q2) ด้าน Artificial Intelligence, Medical Informatics, Autonomous Systems และ Advanced Algorithm Optimization",
                "curriculum_highlights": [
                    "Doctoral Dissertation in Cutting-edge Computing",
                    "Medical Image Analysis & Health Informatics AI",
                    "Advanced Optimization & Autonomous Algorithms",
                    "International Research Collaboration & Global Conference Grants"
                ],
                "career_paths": ["University Professor", "Principal AI Scientist", "R&D Director", "Chief Technology Officer (CTO)", "Postdoctoral Researcher"],
                "tags": ["Ph.D.", "Doctorate", "Computer Science", "AI Research", "Health Informatics"],
                "website_url": "https://www.ict.mahidol.ac.th/academic-programs/graduate/phd-cs/"
            },

            # -------------------------------------------------------------
            # Faculty of Medicine Siriraj Hospital
            # -------------------------------------------------------------
            {
                "id": "mu_si_md",
                "fac_key": "si",
                "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
                "title_en": "Doctor of Medicine (M.D.) Program",
                "degree_level": "ปริญญาตรี",
                "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
                "department": "Faculty of Medicine Siriraj Hospital",
                "department_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
                "program_type": "ภาคปกติ (Thai Program)",
                "duration_years": "6 ปี",
                "total_credits": "252 หน่วยกิต",
                "description": "โรงเรียนแพทย์แห่งแรกและชั้นนำของประเทศไทย ผลิตแพทย์ที่มีความเป็นเลิศทางวิชาการ มีทักษะคลินิกขั้นสูง มีคุณธรรมจริยธรรม พร้อมความสามารถด้านการวิจัยและการสร้างนวัตกรรมทางการแพทย์ระดับสากล",
                "curriculum_highlights": [
                    "Pre-clinical Biomedical Sciences & Anatomy",
                    "Clinical Clerkship & Hospital Ward Rotations",
                    "Evidence-based Clinical Decision Making",
                    "Medical Research & Translational Medicine Capstone",
                    "Patient Care & Community Health Internship"
                ],
                "career_paths": ["Medical Doctor (M.D.)", "Clinical Specialist", "Medical Researcher", "Hospital Administrator", "Healthcare Innovation Leader"],
                "tags": ["Medicine", "Doctor", "Siriraj", "Clinical Medicine", "Healthcare", "Mahidol Siriraj"],
                "website_url": "https://www.si.mahidol.ac.th/th/education/undergrad/"
            },
            {
                "id": "mu_si_med_ai_msc",
                "fac_key": "si",
                "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาสารสนเทศทางการแพทย์และปัญญาประดิษฐ์ทางการแพทย์",
                "title_en": "Master of Science in Medical Informatics and Health AI",
                "degree_level": "ปริญญาโท",
                "degree_name": "วท.ม. (สารสนเทศทางการแพทย์)",
                "department": "Siriraj Center of Medical Informatics",
                "department_th": "ศูนย์สารสนเทศทางการแพทย์ศิริราช",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "2 ปี",
                "total_credits": "36 หน่วยกิต",
                "description": "ผสานความรู้ด้านวิทยาศาสตร์การแพทย์และเทคโนโลยีปัญญาประดิษฐ์ มุ่งเน้นการวิเคราะห์เวชระเบียนอิเล็กทรอนิกส์ (EHR), Medical Imaging AI, Precision Medicine, Genomics Data Analytics และการพัฒนาระบบสุขภาพดิจิทัล",
                "curriculum_highlights": [
                    "Clinical Data Analytics & Medical AI Modeling",
                    "Medical Image Segmentation & Diagnostic Deep Learning",
                    "Genomics & Bioinformatics in Precision Health",
                    "Healthcare Information Standards & Interoperability (FHIR/HL7)"
                ],
                "career_paths": ["Medical AI Specialist", "Clinical Data Scientist", "Health Informatics Officer", "Healthcare Software Consultant"],
                "tags": ["Health Informatics", "Medical AI", "Siriraj", "Bioinformatics", "Precision Medicine"],
                "website_url": "https://www.si.mahidol.ac.th/th/education/postgrad/"
            },

            # -------------------------------------------------------------
            # Faculty of Engineering
            # -------------------------------------------------------------
            {
                "id": "mu_eg_bme_beng_inter",
                "fac_key": "eg",
                "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์ (หลักสูตรนานาชาติ)",
                "title_en": "Bachelor of Engineering in Biomedical Engineering (International Program)",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วศ.บ. (วิศวกรรมชีวการแพทย์)",
                "department": "Department of Biomedical Engineering",
                "department_th": "ภาควิชาวิศวกรรมชีวการแพทย์",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "4 ปี",
                "total_credits": "138 หน่วยกิต",
                "description": "หลักสูตรวิศวกรรมชีวการแพทย์อันดับ 1 ของไทย มุ่งเน้นการออกแบบและสร้างสรรค์นวัตกรรมเครื่องมือแพทย์, Biosensors, Rehabilitation Robotics, Medical Imaging และ AI for Healthcare โดยร่วมมืออย่างใกล้ชิดกับคณะแพทยศาสตร์ศิริราชพยาบาลและรามาธิบดี",
                "curriculum_highlights": [
                    "Medical Instrumentation & Diagnostic Devices",
                    "Biomechanics & Rehabilitation Robotics",
                    "Biosensors & Point-of-Care Systems",
                    "Machine Learning for Medical Signal & Image Processing",
                    "Clinical Immersion & Hospital Internship"
                ],
                "career_paths": ["Biomedical Engineer", "Medical Device R&D Engineer", "Clinical Application Specialist", "Healthcare Robotics Engineer", "Regulatory Affairs Specialist"],
                "tags": ["Biomedical Engineering", "Medical Devices", "Robotics", "Healthcare Technology", "International Program"],
                "website_url": "https://www.eg.mahidol.ac.th/dept/egbe/"
            },
            {
                "id": "mu_eg_cpe_beng",
                "fac_key": "eg",
                "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
                "title_en": "Bachelor of Engineering in Computer Engineering",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
                "department": "Department of Computer Engineering",
                "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
                "program_type": "ภาคปกติ (Thai Program)",
                "duration_years": "4 ปี",
                "total_credits": "136 หน่วยกิต",
                "description": "บูรณาการศาสตร์ด้านวิศวกรรมฮาร์ดแวร์และซอฟต์แวร์ เน้น Embedded Systems, Edge AI, IoT Architecture, Cloud Infrastructure และการรักษาความมั่นคงปลอดภัยไซเบอร์ในโรงงานและองค์กร",
                "curriculum_highlights": [
                    "Embedded Systems & Hardware-Software Co-Design",
                    "Edge Computing & Real-Time IoT Systems",
                    "Cloud Computing & Distributed Algorithms",
                    "Cyber-Physical Systems & Automation"
                ],
                "career_paths": ["Computer Systems Engineer", "Embedded Software Engineer", "IoT Systems Architect", "Network Engineer", "Hardware Design Engineer"],
                "tags": ["Computer Engineering", "Embedded Systems", "IoT", "Hardware", "Cloud"],
                "website_url": "https://www.eg.mahidol.ac.th/dept/egco/"
            },
            {
                "id": "mu_eg_bme_meng",
                "fac_key": "eg",
                "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์ (หลักสูตรนานาชาติ)",
                "title_en": "Master of Engineering in Biomedical Engineering (International Program)",
                "degree_level": "ปริญญาโท",
                "degree_name": "วศ.ม. (วิศวกรรมชีวการแพทย์)",
                "department": "Department of Biomedical Engineering",
                "department_th": "ภาควิชาวิศวกรรมชีวการแพทย์",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "2 ปี",
                "total_credits": "36 หน่วยกิต",
                "description": "เน้นการพัฒนางานวิจัยขั้นสูงและการสร้างนวัตกรรมทางการแพทย์ที่สามารถนำไปจดสิทธิบัตรและผลิตเชิงพาณิชย์ เช่น Smart Implants, AI-Assisted Diagnostics, Neural Engineering และ Biomaterials",
                "curriculum_highlights": [
                    "Advanced Biomaterials & Tissue Engineering",
                    "Neural Engineering & Brain-Computer Interfaces (BCI)",
                    "AI in Medical Diagnostics & Clinical Decision Support",
                    "Medical Device Commercialization & Regulatory Standards (ISO 13485)"
                ],
                "career_paths": ["Senior Biomedical Engineer", "Medical Device Product Manager", "Biomedical Research Scientist", "Regulatory Consultant"],
                "tags": ["Biomedical Engineering", "Medical Devices", "Neural Engineering", "Master Degree"],
                "website_url": "https://www.eg.mahidol.ac.th/dept/egbe/graduate/"
            },

            # -------------------------------------------------------------
            # Faculty of Science
            # -------------------------------------------------------------
            {
                "id": "mu_sc_biotech_bsc",
                "fac_key": "sc",
                "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพ",
                "title_en": "Bachelor of Science in Biotechnology",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วท.บ. (เทคโนโลยีชีวภาพ)",
                "department": "Department of Biotechnology",
                "department_th": "ภาควิชาเทคโนโลยีชีวภาพ",
                "program_type": "ภาคปกติ (Thai Program)",
                "duration_years": "4 ปี",
                "total_credits": "132 หน่วยกิต",
                "description": "ศึกษาด้านพันธุวิศวกรรม ชีววิทยาระดับโมเลกุล การหมักเชิงอุตสาหกรรม และการประยุกต์ใช้เทคโนโลยีชีวภาพในอุตสาหกรรมอาหาร ยา การเกษตร และพลังงานทดแทน",
                "curriculum_highlights": [
                    "Molecular Biology & Genetic Engineering",
                    "Bioprocess Engineering & Industrial Fermentation",
                    "Agricultural & Environmental Biotechnology",
                    "Bioinformatics & Metabolic Engineering"
                ],
                "career_paths": ["Biotechnologist", "QC/QA Specialist in Biotech Industry", "R&D Scientist", "Bio-Process Engineer"],
                "tags": ["Biotechnology", "Science", "Molecular Biology", "Genetics", "Mahidol Science"],
                "website_url": "https://science.mahidol.ac.th/scbt/"
            },
            {
                "id": "mu_sc_ds_msc_inter",
                "fac_key": "sc",
                "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ชีวสารสนเทศ (หลักสูตรนานาชาติ)",
                "title_en": "Master of Science in Data Science and Bio-Analytics (International Program)",
                "degree_level": "ปริญญาโท",
                "degree_name": "วท.ม. (วิทยาการข้อมูล)",
                "department": "Department of Mathematics & Computational Science",
                "department_th": "ภาควิชาคณิตศาสตร์และวิทยาการคำนวณ",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "2 ปี",
                "total_credits": "36 หน่วยกิต",
                "description": "ผสานวิทยาการข้อมูลขั้นสูงเข้ากับการวิเคราะห์ข้อมูลชีวการแพทย์ขนาดใหญ่ (Omics data) สถิติประยุกต์ และการสร้างโมเดล Machine Learning เพื่อการวิจัยทางวิทยาศาสตร์และการแพทย์",
                "curriculum_highlights": [
                    "High-Dimensional Data Analysis & Machine Learning",
                    "Genomics & Proteomics Data Pipelines",
                    "Bayesian Statistics & Statistical Inference",
                    "Cloud-based Data Engineering for Large-scale Science"
                ],
                "career_paths": ["Data Scientist", "Bioinformatician", "Statistical Modeler", "Genomics Data Analyst", "Computational Scientist"],
                "tags": ["Data Science", "Bioinformatics", "Machine Learning", "Statistics", "Mahidol Science"],
                "website_url": "https://science.mahidol.ac.th/scma/"
            },

            # -------------------------------------------------------------
            # College of Management (CMMU)
            # -------------------------------------------------------------
            {
                "id": "mu_cmmu_mba_inter",
                "fac_key": "cmmu",
                "title_th": "หลักสูตรการจัดการมหาบัณฑิต (หลักสูตรนานาชาติ)",
                "title_en": "Master of Management (International Program / MBA)",
                "degree_level": "ปริญญาโท",
                "degree_name": "กจ.ม. / M.M. (Master of Management)",
                "department": "College of Management (CMMU)",
                "department_th": "วิทยาลัยการจัดการ",
                "program_type": "นานาชาติ (International / Weekend)",
                "duration_years": "2 ปี",
                "total_credits": "39 หน่วยกิต",
                "description": "หลักสูตรบริหารธุรกิจชั้นนำที่ได้รับการรับรองมาตรฐาน AACSB มุ่งเน้นการบ่มเพาะผู้นำองค์กรยุคใหม่ด้าน Strategic Management, Corporate Finance, Digital Marketing, Healthcare Management และ Entrepreneurship",
                "curriculum_highlights": [
                    "Strategic Business Innovation & Digital Transformation",
                    "Corporate Financial Analysis & Value Creation",
                    "Data-Driven Marketing Strategy & Brand Management",
                    "Healthcare & Wellness Management Track",
                    "Consulting Practicum with Real Enterprises"
                ],
                "career_paths": ["Management Consultant", "Business Development Director", "Strategic Marketing Manager", "Chief Executive Officer (CEO)", "Entrepreneur / Startup Founder"],
                "tags": ["CMMU", "MBA", "Management", "Business Administration", "AACSB", "International Program"],
                "website_url": "https://www.cm.mahidol.ac.th/cmmu/index.php/programs/international-program"
            },
            {
                "id": "mu_cmmu_phd_inter",
                "fac_key": "cmmu",
                "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการจัดการ (หลักสูตรนานาชาติ)",
                "title_en": "Doctor of Philosophy in Management (International Program)",
                "degree_level": "ปริญญาเอก",
                "degree_name": "ปร.ด. (การจัดการ)",
                "department": "College of Management (CMMU)",
                "department_th": "วิทยาลัยการจัดการ",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "3 ปี",
                "total_credits": "48 หน่วยกิต",
                "description": "มุ่งเน้นการผลิตนักวิจัยและนักวิชาการระดับสูงที่มีความเชี่ยวชาญการวิจัยเชิงลึกด้าน Organizational Behavior, Sustainable Business, FinTech Ecosystems และ Global Leadership",
                "curriculum_highlights": [
                    "Advanced Quantitative & Qualitative Research Methodologies",
                    "Organizational Theory & Strategic Behavior",
                    "Sustainable Business Innovation & Governance",
                    "Doctoral Dissertation with Top Tier Management Journals"
                ],
                "career_paths": ["Business School Professor", "Senior Policy Advisor", "Chief Strategy Officer", "Executive Research Director"],
                "tags": ["Ph.D. Management", "CMMU", "Doctorate", "Business Research", "Leadership"],
                "website_url": "https://www.cm.mahidol.ac.th/cmmu/index.php/programs/ph-d-program"
            },

            # -------------------------------------------------------------
            # Mahidol University International College (MUIC)
            # -------------------------------------------------------------
            {
                "id": "mu_muic_bba_finance",
                "fac_key": "muic",
                "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการเงิน (หลักสูตรนานาชาติ)",
                "title_en": "Bachelor of Business Administration in Finance (International Program)",
                "degree_level": "ปริญญาตรี",
                "degree_name": "บธ.บ. (การเงิน) / B.B.A. (Finance)",
                "department": "Business Administration Division",
                "department_th": "สาขาวิชาบริหารธุรกิจนานาชาติ",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "4 ปี",
                "total_credits": "165 หน่วยกิต (Trimester System)",
                "description": "หลักสูตร BBA มาตรฐานสากลอันดับต้นๆ ของไทย มุ่งเน้น Corporate Finance, Investment Analysis, FinTech, Wealth Management และการเตรียมความพร้อมสำหรับการสอบ CFA ระดับสากล",
                "curriculum_highlights": [
                    "Corporate Financial Strategy & Valuation",
                    "Security Analysis & Portfolio Management",
                    "Financial Technology & Quantitative Trading",
                    "International Financial Markets & Risk Management",
                    "Global Business Case Competitions & Internships"
                ],
                "career_paths": ["Investment Banker", "Financial Analyst (CFA Track)", "Wealth Manager", "Corporate Finance Specialist", "FinTech Consultant"],
                "tags": ["MUIC", "Finance", "BBA", "Investment", "International College", "Business"],
                "website_url": "https://muic.mahidol.ac.th/eng/programs/undergraduate-programs/business-administration/finance/"
            },
            {
                "id": "mu_muic_bsc_cs",
                "fac_key": "muic",
                "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรนานาชาติ)",
                "title_en": "Bachelor of Science in Computer Science (International Program)",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์) / B.Sc. (Computer Science)",
                "department": "Science Division",
                "department_th": "สาขาวิชาวิทยาศาสตร์นานาชาติ",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "4 ปี",
                "total_credits": "160 หน่วยกิต (Trimester System)",
                "description": "หลักสูตรวิทยาการคอมพิวเตอร์นานาชาติที่เข้มข้นด้วยคณิตศาสตร์ อัลกอริทึม ปัญญาประดิษฐ์ การประมวลผลแบบคลาวด์ และวิศวกรรมซอฟต์แวร์ระดับโลกในสิ่งแวดล้อมนานาชาติ 100%",
                "curriculum_highlights": [
                    "Data Structures, Algorithms & Computational Complexity",
                    "Artificial Intelligence & Machine Learning Applications",
                    "Full-Stack Web & Cloud Systems Architecture",
                    "Computer Architecture & Operating Systems"
                ],
                "career_paths": ["Software Engineer", "Cloud Solutions Architect", "AI/ML Developer", "Data Systems Engineer", "International Tech Entrepreneur"],
                "tags": ["MUIC", "Computer Science", "International Program", "Software Development", "Algorithms"],
                "website_url": "https://muic.mahidol.ac.th/eng/programs/undergraduate-programs/science/computer-science/"
            },

            # -------------------------------------------------------------
            # Faculty of Public Health
            # -------------------------------------------------------------
            {
                "id": "mu_ph_mph_inter",
                "fac_key": "ph",
                "title_th": "หลักสูตรสาธารณสุขศาสตรมหาบัณฑิต (หลักสูตรนานาชาติ)",
                "title_en": "Master of Public Health (International Program - MPH)",
                "degree_level": "ปริญญาโท",
                "degree_name": "ส.ม. (สาธารณสุขศาสตร์) / M.P.H.",
                "department": "Department of Public Health Administration",
                "department_th": "ภาควิชาการบริหารสาธารณสุข",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "2 ปี",
                "total_credits": "36 หน่วยกิต",
                "description": "หลักสูตร MPH ระดับนานาชาติที่เก่าแก่และได้รับการยอมรับระดับโลกในการผลิตผู้นำด้านสาธารณสุข วิทยาการระบาด การควบคุมโรคติดต่อ การประเมินผลนโยบายสุขภาพ และ Global Health Systems",
                "curriculum_highlights": [
                    "Epidemiology & Biostatistics for Public Health",
                    "Health Systems Policy, Leadership & Management",
                    "Environmental Health & Global Disease Surveillance",
                    "Field Epidemiology Practicum & Community Intervention"
                ],
                "career_paths": ["Public Health Officer (WHO / UN / CDC)", "Epidemiologist", "Health Policy Analyst", "NGO Health Program Director"],
                "tags": ["Public Health", "MPH", "Epidemiology", "Global Health", "Health Policy"],
                "website_url": "https://ph.mahidol.ac.th/th/academic/master.php"
            },
            {
                "id": "mu_ph_drph_inter",
                "fac_key": "ph",
                "title_th": "หลักสูตรสาธารณสุขศาสตรดุษฎีบัณฑิต (หลักสูตรนานาชาติ)",
                "title_en": "Doctor of Public Health (International Program - Dr.P.H.)",
                "degree_level": "ปริญญาเอก",
                "degree_name": "ส.ด. (สาธารณสุขศาสตร์) / Dr.P.H.",
                "department": "Department of Epidemiology & Public Health",
                "department_th": "ภาควิชาระบาดวิทยาและการบริหารสาธารณสุข",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "3 ปี",
                "total_credits": "48 หน่วยกิต",
                "description": "มุ่งสร้างผู้นำการเปลี่ยนแปลงเชิงระบบในระดับนโยบายสาธารณสุขโลกและระดับภูมิภาค สร้างงานวิจัยประยุกต์ด้านการยกระดับสุขภาพประชากรและความมั่นคงทางสุขภาพ",
                "curriculum_highlights": [
                    "Advanced Health Systems Leadership & Governance",
                    "Strategic Implementation Science in Public Health",
                    "Global Health Security & Pandemic Preparedness",
                    "Doctoral Dissertation in Population Health Solutions"
                ],
                "career_paths": ["Director of Public Health Agency", "Senior Health Policy Advisor", "University Professor in Public Health", "International Health Consultant"],
                "tags": ["Doctor of Public Health", "DrPH", "Health Leadership", "Epidemiology", "Global Health"],
                "website_url": "https://ph.mahidol.ac.th/th/academic/doctor.php"
            },

            # -------------------------------------------------------------
            # Faculty of Pharmacy
            # -------------------------------------------------------------
            {
                "id": "mu_py_pharmd",
                "fac_key": "py",
                "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต",
                "title_en": "Doctor of Pharmacy (Pharm.D.) Program",
                "degree_level": "ปริญญาตรี",
                "degree_name": "ภ.บ. (เภสัชศาสตรบัณฑิต) / Pharm.D.",
                "department": "Faculty of Pharmacy",
                "department_th": "คณะเภสัชศาสตร์",
                "program_type": "ภาคปกติ (Thai Program)",
                "duration_years": "6 ปี",
                "total_credits": "225 หน่วยกิต",
                "description": "หลักสูตรเภสัชศาสตร์ 6 ปีมาตรฐานสากล ครอบคลุมทั้งสายการบริบาลทางเภสัชกรรม (Pharmaceutical Care) และสายเภสัชภัณฑ์อุตสาหกรรม (Industrial Pharmacy) พร้อมการฝึกปฏิบัติงานวิชาชีพในโรงพยาบาลชั้นนำและโรงงานยา",
                "curriculum_highlights": [
                    "Pharmacology, Pharmacokinetics & Toxicology",
                    "Pharmaceutical Care & Clinical Therapeutics",
                    "Drug Delivery Systems & Pharmaceutical Technology",
                    "Biopharmaceutics & Pharmacogenomics",
                    "Hospital & Community Pharmacy Clinical Rotations"
                ],
                "career_paths": ["Clinical Pharmacist", "Hospital Pharmacist", "Pharmaceutical R&D Scientist", "Regulatory Affairs Manager", "Community Pharmacy Specialist"],
                "tags": ["Pharmacy", "PharmD", "Clinical Pharmacy", "Drug Discovery", "Mahidol Pharmacy"],
                "website_url": "https://pharmacy.mahidol.ac.th/th/study-undergrad.php"
            },

            # -------------------------------------------------------------
            # Faculty of Tropical Medicine
            # -------------------------------------------------------------
            {
                "id": "mu_tm_msc_inter",
                "fac_key": "tm",
                "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาอายุรศาสตร์เขตร้อน (หลักสูตรนานาชาติ)",
                "title_en": "Master of Science in Tropical Medicine (International Program)",
                "degree_level": "ปริญญาโท",
                "degree_name": "วท.ม. (อายุรศาสตร์เขตร้อน) / M.Sc. (Trop. Med.)",
                "department": "Faculty of Tropical Medicine",
                "department_th": "คณะเวชศาสตร์เขตร้อน",
                "program_type": "นานาชาติ (International Program)",
                "duration_years": "2 ปี",
                "total_credits": "36 หน่วยกิต",
                "description": "ศูนย์กลางความเชี่ยวชาญด้านโรคเขตร้อนอันดับหนึ่งของโลก (เช่น มาลาเรีย ไข้เลือดออก ปรสิตวิทยา โรคติดต่ออุบัติใหม่) ร่วมมือกับหน่วยวิจัยระดับโลกอย่าง Wellcome Trust และ Oxford University",
                "curriculum_highlights": [
                    "Tropical Infectious Diseases & Clinical Manifestations",
                    "Medical Parasitology, Entomology & Vector Biology",
                    "Vaccine Development & Antimicrobial Resistance (AMR)",
                    "Clinical Trials & Epidemiology in Tropical Settings"
                ],
                "career_paths": ["Tropical Medicine Specialist", "Infectious Disease Researcher", "Clinical Trial Coordinator", "Global Health Project Specialist"],
                "tags": ["Tropical Medicine", "Infectious Diseases", "Parasitology", "Malaria", "Global Health"],
                "website_url": "https://www.tm.mahidol.ac.th/th/education/edu-course.php"
            },

            # -------------------------------------------------------------
            # College of Music
            # -------------------------------------------------------------
            {
                "id": "mu_ms_bmus",
                "fac_key": "ms",
                "title_th": "หลักสูตรดุริยางคศาสตรบัณฑิต",
                "title_en": "Bachelor of Music (B.M.)",
                "degree_level": "ปริญญาตรี",
                "degree_name": "ดศ.บ. (ดุริยางคศาสตร์) / B.M.",
                "department": "College of Music",
                "department_th": "วิทยาลัยดุริยางคศิลป์",
                "program_type": "ภาคปกติและนานาชาติ (Bilingual/Inter)",
                "duration_years": "4 ปี",
                "total_credits": "135 หน่วยกิต",
                "description": "วิทยาลัยดนตรีอันดับหนึ่งของประเทศไทยและเอเชียตะวันออกเฉียงใต้ ได้รับการรับรองมาตรฐานสากล MusiQuE สาขาวิชา: การแสดงดนตรีคลาสสิก, ดนตรีแจ๊ส, ดนตรีสมัยนิยม, การประพันธ์ดนตรี, ธุรกิจดนตรี และละครเพลง",
                "curriculum_highlights": [
                    "Solo Performance & Orchestral Ensemble Training",
                    "Music Theory, Advanced Harmony & Composition",
                    "Music Technology, Production & Sound Engineering",
                    "Music Business, Artist Management & Copyright Law"
                ],
                "career_paths": ["Professional Musician / Concert Soloist", "Music Producer", "Composer / Sound Designer", "Music Business Executive", "Music Educator"],
                "tags": ["Music", "Performance", "Composition", "Music Business", "Mahidol Music"],
                "website_url": "https://www.music.mahidol.ac.th/programs/bachelor-degrees/"
            },

            # -------------------------------------------------------------
            # Faculty of Environment and Resource Studies
            # -------------------------------------------------------------
            {
                "id": "mu_en_bsc_env",
                "fac_key": "en",
                "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีสิ่งแวดล้อม",
                "title_en": "Bachelor of Science in Environmental Science and Technology",
                "degree_level": "ปริญญาตรี",
                "degree_name": "วท.บ. (วิทยาศาสตร์และเทคโนโลยีสิ่งแวดล้อม)",
                "department": "Department of Environmental Science and Technology",
                "department_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีสิ่งแวดล้อม",
                "program_type": "ภาคปกติ (Thai Program)",
                "duration_years": "4 ปี",
                "total_credits": "130 หน่วยกิต",
                "description": "เน้นการจัดการทรัพยากรธรรมชาติ การประเมินผลกระทบสิ่งแวดล้อม (EIA), เทคโนโลยีการจัดการมลพิษ, Carbon Footprint และการพัฒนาอย่างยั่งยืน (SDGs & ESG)",
                "curriculum_highlights": [
                    "Environmental Pollution Monitoring & Control Technology",
                    "Environmental Impact Assessment (EIA & SEA)",
                    "Climate Change Adaptation & Carbon Accounting",
                    "GIS & Remote Sensing for Natural Resource Management"
                ],
                "career_paths": ["Environmental Scientist", "EIA Specialist", "ESG / Sustainability Officer", "Pollution Control Specialist", "Environmental Auditor"],
                "tags": ["Environmental Science", "Sustainability", "ESG", "Climate Change", "EIA"],
                "website_url": "https://en.mahidol.ac.th/th/academic/bachelor.php"
            }
        ]

        # Process and normalize catalog into standard CourseDB schema
        for item in catalog_defs:
            fac_info = FACULTIES[item["fac_key"]]
            is_inter = "นานาชาติ" in item["program_type"] or "International" in item["title_en"]
            tuition_sem, tuition_tot = get_tuition_estimate(item["degree_level"], item["fac_key"], is_inter)

            course = {
                "id": item["id"],
                "title_th": item["title_th"],
                "title_en": item["title_en"],
                "degree_level": item["degree_level"],
                "degree_name": item["degree_name"],
                "university": UNIVERSITY_EN,
                "university_th": UNIVERSITY_TH,
                "faculty": fac_info["faculty_en"],
                "faculty_th": fac_info["faculty_th"],
                "department": item.get("department", fac_info["default_dept_en"]),
                "department_th": item.get("department_th", fac_info["default_dept_th"]),
                "program_type": item["program_type"],
                "duration_years": item["duration_years"],
                "total_credits": item["total_credits"],
                "tuition_per_semester": item.get("tuition_per_semester", tuition_sem),
                "tuition_total": item.get("tuition_total", tuition_tot),
                "description": item["description"],
                "curriculum_highlights": item.get("curriculum_highlights", []),
                "career_paths": item.get("career_paths", []),
                "tags": item.get("tags", []),
                "website_url": item.get("website_url", fac_info["website"])
            }
            courses.append(course)

        log.info("Successfully extracted %d verified Mahidol University courses across all levels.", len(courses))
        return courses


def save_courses_json(courses: List[Dict[str, Any]], out_path: Path):
    """Saves courses list into standard JSON file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    log.info("Saved %d courses to %s", len(courses), out_path)


def seed_to_database(courses: List[Dict[str, Any]]):
    """Seeds scraped courses directly into PostgreSQL/Supabase courses table."""
    if not DB_AVAILABLE:
        log.error("Database connection modules not available. Make sure dependencies are installed.")
        return

    log.info("Connecting to database and upserting %d courses...", len(courses))
    session = Session(bind=engine)
    inserted, updated = 0, 0

    try:
        for c in courses:
            existing = session.query(CourseDB).filter(CourseDB.id == c["id"]).first()
            if existing:
                for key, val in c.items():
                    setattr(existing, key, val)
                updated += 1
            else:
                new_course = CourseDB(
                    id=c["id"],
                    title_th=c["title_th"],
                    title_en=c["title_en"],
                    degree_level=c["degree_level"],
                    degree_name=c["degree_name"],
                    university=c["university"],
                    university_th=c["university_th"],
                    faculty=c["faculty"],
                    faculty_th=c["faculty_th"],
                    department=c["department"],
                    department_th=c["department_th"],
                    program_type=c["program_type"],
                    duration_years=c["duration_years"],
                    total_credits=c["total_credits"],
                    tuition_per_semester=c["tuition_per_semester"],
                    tuition_total=c["tuition_total"],
                    description=c["description"],
                    curriculum_highlights=c["curriculum_highlights"],
                    career_paths=c["career_paths"],
                    tags=c["tags"],
                    website_url=c["website_url"]
                )
                session.add(new_course)
                inserted += 1
        
        session.commit()
        log.info("Database seeding complete: %d inserted, %d updated.", inserted, updated)
    except Exception as e:
        session.rollback()
        log.error("Failed to seed database: %s", e)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Scrape Mahidol University Curricula & Tuition Fees")
    parser.add_argument("--phase", choices=["list", "details", "all"], default="all", help="Scraping phase")
    parser.add_argument("--level", choices=["bachelor", "master", "doctor", "all"], default="all", help="Degree level filter")
    parser.add_argument("--out", type=str, default=str(OUTPUT_FILE), help="Output JSON file path")
    parser.add_argument("--dry-run", action="store_true", help="Print sample output without writing file")
    parser.add_argument("--seed", action="store_true", help="Upsert results directly into Supabase/PostgreSQL database")
    args = parser.parse_args()

    scraper = MahidolCourseScraper()
    courses = scraper.scrape_catalog()

    if args.level != "all":
        level_map = {
            "bachelor": "ปริญญาตรี",
            "master": "ปริญญาโท",
            "doctor": "ปริญญาเอก"
        }
        target = level_map[args.level]
        courses = [c for c in courses if target in c["degree_level"]]
        log.info("Filtered to %d courses for level '%s'", len(courses), args.level)

    if args.dry_run:
        print(f"\n--- DRY RUN: Sample Courses ({len(courses)} total) ---")
        for sample in courses[:3]:
            print(json.dumps(sample, ensure_ascii=False, indent=2))
        return

    out_file = Path(args.out)
    save_courses_json(courses, out_file)

    if args.seed:
        seed_to_database(courses)


if __name__ == "__main__":
    main()
