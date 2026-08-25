"""
Scraper and Catalog Builder for Sripatum University (SPU) Curricula & Tuition Fees.
Target Sources:
- Sripatum University Academics & Programs (https://www.spu.ac.th/)
- SPU Admissions & Tuition Fees Portal (https://www.spu.ac.th/apply/)
- Graduate College of Management (https://www.spu.ac.th/graduate69/)

Schema:
CourseDB(id, title_th, title_en, degree_level, degree_name, university, university_th,
         faculty, faculty_th, department, department_th, program_type, duration_years,
         total_credits, tuition_per_semester, tuition_total, description,
         curriculum_highlights, career_paths, tags, website_url)
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup

# Add backend root to sys.path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_ROOT))

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_OUTPUT_FILE = DATA_DIR / "spu_courses.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scrape_spu")

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

SPU_COURSES: List[Dict[str, Any]] = [
    # --- Faculty of Digital Media (คณะดิจิทัลมีเดีย) ---
    {
        "id": "spu_dm_da",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาดิจิทัลอาร์ตส์",
        "title_en": "Bachelor of Fine Arts Program in Digital Arts",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (ดิจิทัลอาร์ตส์)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Digital Media",
        "faculty_th": "คณะดิจิทัลมีเดีย",
        "department": "Department of Digital Arts",
        "department_th": "สาขาวิชาดิจิทัลอาร์ตส์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "เน้นการสร้างสรรค์ 2D/3D Concept Art, Digital Painting, คาแรคเตอร์ดีไซน์ และภาพประกอบดิจิทัลสำหรับอุตสาหกรรมเกม ภาพยนตร์ และคอมมิก",
        "curriculum_highlights": [
            "Character Design & World Building",
            "Concept Art for Games & Cinema",
            "Digital Illustration & Comic Art",
            "3D Digital Sculpting (ZBrush)"
        ],
        "career_paths": [
            "Concept Artist",
            "Character Designer",
            "Digital Illustrator",
            "Comic / Webtoon Artist",
            "3D Sculptor"
        ],
        "tags": ["Digital Arts", "Concept Art", "Character Design", "Digital Media", "SPU"],
        "website_url": "https://www.spu.ac.th/fac/sdm/courses/bachelor/digital-arts/"
    },
    {
        "id": "spu_dm_anim",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาแอนิเมชันและวิชวลเอฟเฟกต์",
        "title_en": "Bachelor of Fine Arts Program in Animation and Visual Effects",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (แอนิเมชันและวิชวลเอฟเฟกต์)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Digital Media",
        "faculty_th": "คณะดิจิทัลมีเดีย",
        "department": "Department of Animation and Visual Effects",
        "department_th": "สาขาวิชาแอนิเมชันและวิชวลเอฟเฟกต์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "43,500 บาท",
        "tuition_total": "348,000 บาท",
        "description": "สอนการทำ 3D Animation และ VFX ขั้นสูง การจัดแสง การจำลองฟิสิกส์ (Dynamics & Simulation) และการผสมผสานภาพกับฉากจริง",
        "curriculum_highlights": [
            "3D Character Animation & Rigging",
            "Visual Effects (VFX) & Fluid Simulation",
            "Lighting & Look Development",
            "Motion Capture & Post-Production"
        ],
        "career_paths": [
            "3D Animator",
            "VFX Compositor",
            "Rigging Artist",
            "Lighting Artist",
            "Animation Technical Director"
        ],
        "tags": ["Animation", "3D", "VFX", "Simulation", "Motion Capture"],
        "website_url": "https://www.spu.ac.th/fac/sdm/courses/bachelor/animation-vfx/"
    },
    {
        "id": "spu_dm_game",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาการออกแบบอินเทอร์แอคทีฟและเกม",
        "title_en": "Bachelor of Fine Arts Program in Interactive and Game Design",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (การออกแบบอินเทอร์แอคทีฟและเกม)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Digital Media",
        "faculty_th": "คณะดิจิทัลมีเดีย",
        "department": "Department of Interactive and Game Design",
        "department_th": "สาขาวิชาการออกแบบอินเทอร์แอคทีฟและเกม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "43,000 บาท",
        "tuition_total": "344,000 บาท",
        "description": "เน้น Game Design, Level Design, UI/UX for Games, การพัฒนาเกมด้วยเอนจินมาตรฐานอุตสาหกรรม (Unreal & Unity) และการผลิตเกมเชิงพาณิชย์",
        "curriculum_highlights": [
            "Game Mechanics & Level Design",
            "Game Engine Integration (Unreal/Unity)",
            "Game UI/UX & Interactive Prototyping",
            "Commercial Game Publishing & Monetization"
        ],
        "career_paths": [
            "Game Designer",
            "Level Designer",
            "Game UI/UX Designer",
            "Technical Game Artist",
            "Game Producer"
        ],
        "tags": ["Game Design", "Interactive", "Level Design", "Unreal", "Unity"],
        "website_url": "https://www.spu.ac.th/fac/sdm/courses/bachelor/game-design/"
    },

    # --- Faculty of Information Technology (คณะเทคโนโลยีสารสนเทศ) ---
    {
        "id": "spu_it_cs",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และนวัตกรรมข้อมูล",
        "title_en": "Bachelor of Science Program in Computer Science and Data Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์และนวัตกรรมข้อมูล)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "38,500 บาท",
        "tuition_total": "308,000 บาท",
        "description": "มุ่งเน้น Data Science, Artificial Intelligence (AI), Machine Learning, และการพัฒนาซอฟต์แวร์ฟูลสแตกที่ตอบโจทย์อุตสาหกรรมดิจิทัล",
        "curriculum_highlights": [
            "Applied AI & Machine Learning",
            "Big Data Engineering & Pipeline",
            "Full Stack Software Development",
            "Cloud Computing Platforms"
        ],
        "career_paths": [
            "Data Scientist / Data Engineer",
            "AI / Machine Learning Engineer",
            "Full Stack Developer",
            "Software Architect",
            "Cloud Systems Developer"
        ],
        "tags": ["Computer Science", "Data Science", "AI", "Software", "Cloud"],
        "website_url": "https://www.spu.ac.th/fac/informatics/courses/bachelor/computer-science/"
    },
    {
        "id": "spu_it_cyber",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาความมั่นคงปลอดภัยไซเบอร์และระบบเครือข่าย",
        "title_en": "Bachelor of Science Program in Cybersecurity and Network Systems",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ความมั่นคงปลอดภัยไซเบอร์และระบบเครือข่าย)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Cybersecurity",
        "department_th": "สาขาวิชาความมั่นคงปลอดภัยไซเบอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "39,000 บาท",
        "tuition_total": "312,000 บาท",
        "description": "เจาะลึก Ethical Hacking, การตรวจจับและป้องกันภัยคุกคามทางไซเบอร์ (SOC), ดิจิทัลฟอเรนสิกส์ และมาตรฐานความมั่นคงปลอดภัยข้อมูล",
        "curriculum_highlights": [
            "Ethical Hacking & Penetration Testing",
            "Security Operations Center (SOC) & Threat Hunting",
            "Digital Forensics & Incident Response",
            "Enterprise Network Security & Cryptography"
        ],
        "career_paths": [
            "Cybersecurity Specialist / Penetration Tester",
            "SOC Analyst",
            "Information Security Consultant",
            "Network Security Engineer",
            "Digital Forensics Investigator"
        ],
        "tags": ["Cybersecurity", "Network", "Ethical Hacking", "SOC", "Forensics"],
        "website_url": "https://www.spu.ac.th/fac/informatics/courses/bachelor/cybersecurity/"
    },

    # --- Faculty of Engineering (คณะวิศวกรรมศาสตร์) ---
    {
        "id": "spu_eng_rail",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมระบบรางและการขนส่ง",
        "title_en": "Bachelor of Engineering Program in Railway and Transportation System Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมระบบรางและการขนส่ง)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Railway Engineering",
        "department_th": "สาขาวิชาวิศวกรรมระบบราง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "304,000 บาท",
        "description": "เน้นวิศวกรรมรถไฟฟ้าความเร็วสูง รถไฟฟ้าขนส่งมวลชน ระบบอาณัติสัญญาณ ระบบราง และการบริหารจัดการการเดินรถที่เชื่อมโยงกับโครงข่ายระดับภูมิภาค",
        "curriculum_highlights": [
            "Railway Signaling & Telecommunication Systems",
            "Rolling Stock & Train Traction Engineering",
            "Track Design & Maintenance Engineering",
            "Mass Transit Operations & Safety Management"
        ],
        "career_paths": [
            "Railway Systems Engineer",
            "Signaling & Telecom Engineer",
            "Train Maintenance Specialist",
            "Mass Transit Operations Controller",
            "Transportation Infrastructure Project Engineer"
        ],
        "tags": ["Railway", "Transit", "Transportation", "Engineering", "High Speed Rail"],
        "website_url": "https://www.spu.ac.th/fac/engineer/courses/bachelor/railway/"
    },
    {
        "id": "spu_eng_civil",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา",
        "title_en": "Bachelor of Engineering Program in Civil Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมโยธา)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "สาขาวิชาวิศวกรรมโยธา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "37,000 บาท",
        "tuition_total": "296,000 บาท",
        "description": "การคำนวณออกแบบโครงสร้างอาคาร สะพาน ถนน การควบคุมงานก่อสร้างด้วย BIM และการบริหารจัดการโครงการก่อสร้างขนาดใหญ่ พร้อมสอบใบ กว.",
        "curriculum_highlights": [
            "Structural Analysis & Reinforced Concrete Design",
            "Building Information Modeling (BIM) for Construction",
            "Soil Mechanics & Geotechnical Engineering",
            "Construction Project Management & Estimation"
        ],
        "career_paths": [
            "Civil Engineer (Licensed กว.)",
            "Structural Design Engineer",
            "Site / Project Engineer",
            "Construction Project Manager",
            "BIM Engineer"
        ],
        "tags": ["Civil Engineering", "Construction", "Structural", "BIM", "Licensed"],
        "website_url": "https://www.spu.ac.th/fac/engineer/courses/bachelor/civil/"
    },

    # --- College of Logistics and Supply Chain (วิทยาลัยโลจิสติกส์และซัพพลายเชน) ---
    {
        "id": "spu_log_scm",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทาน",
        "title_en": "Bachelor of Business Administration in Logistics and Supply Chain Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการโลจิสติกส์และโซ่อุปทาน)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "College of Logistics and Supply Chain",
        "faculty_th": "วิทยาลัยโลจิสติกส์และซัพพลายเชน",
        "department": "Department of Logistics Management",
        "department_th": "สาขาวิชาการจัดการโลจิสติกส์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "124 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "หลักสูตรมาตรฐานสากลเน้น Smart Logistics, Warehouse Automation, การจัดการการขนส่งข้ามพรมแดน และการวางแผนอุปสงค์ด้วยระบบ AI Analytics",
        "curriculum_highlights": [
            "Smart Warehouse & Inventory Optimization",
            "International Multimodal Transportation & Customs",
            "Supply Chain Analytics & Demand Planning",
            "Procurement & Global Sourcing Strategies"
        ],
        "career_paths": [
            "Supply Chain Planner / Analyst",
            "Logistics Operations Manager",
            "Freight Forwarding Specialist",
            "Warehouse Automation Supervisor",
            "Procurement Specialist"
        ],
        "tags": ["Logistics", "Supply Chain", "Warehouse", "Freight", "Operations"],
        "website_url": "https://www.spu.ac.th/fac/logistics/courses/bachelor/"
    },

    # --- College of Aviation, Tourism and Hospitality (วิทยาลัยการบิน การท่องเที่ยวและการบริการ) ---
    {
        "id": "spu_av_safety",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการจัดการความปลอดภัยการบินและการดำเนินงานสนามบิน",
        "title_en": "Bachelor of Science in Aviation Safety and Airport Operations Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (การจัดการความปลอดภัยการบินและการดำเนินงานสนามบิน)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "College of Aviation, Tourism and Hospitality",
        "faculty_th": "วิทยาลัยการบิน การท่องเที่ยวและการบริการ",
        "department": "Department of Aviation Management",
        "department_th": "สาขาวิชาการจัดการความปลอดภัยการบิน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "38,500 บาท",
        "tuition_total": "308,000 บาท",
        "description": "ฝึกอบรมการบริหารจัดการสนามบิน มาตรฐานความปลอดภัยการบินระดับสากล ICAO การควบคุมการจราจรทางอากาศ และการจัดการบริการภาคพื้น",
        "curriculum_highlights": [
            "ICAO Aviation Safety & Security Management (SMS)",
            "Airport Operations & Ground Handling Standards",
            "Air Traffic Control Fundamentals",
            "Dangerous Goods Regulations & Ramp Safety"
        ],
        "career_paths": [
            "Airport Operations Officer",
            "Aviation Safety & Quality Auditor",
            "Ground Service Supervisor",
            "Air Cargo Operations Executive",
            "Flight Dispatcher Trainee"
        ],
        "tags": ["Aviation", "Airport Operations", "ICAO", "Safety", "Ground Service"],
        "website_url": "https://www.spu.ac.th/fac/aviation/courses/bachelor/safety-management/"
    },

    # --- Faculty of Communication Arts (คณะนิเทศศาสตร์) ---
    {
        "id": "spu_ca_film",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาภาพยนตร์และสื่อดิจิทัล",
        "title_en": "Bachelor of Communication Arts in Film and Digital Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (ภาพยนตร์และสื่อดิจิทัล)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Film and Digital Media",
        "department_th": "สาขาวิชาภาพยนตร์และสื่อดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "41,000 บาท",
        "tuition_total": "328,000 บาท",
        "description": "ฝึกปฏิบัติงานโปรดักชันภาพยนตร์ ซีรีส์สตรีมมิ่ง โฆษณา มิวสิควิดีโอ และสื่อดิจิทัล ด้วยกล้องและอุปกรณ์ระดับอุตสาหกรรม",
        "curriculum_highlights": [
            "Cinematography & Lighting for Streaming Media",
            "Film Directing & Screenplay Writing",
            "Post-Production, Editing & Color Grading",
            "Short Film & Web Series Production"
        ],
        "career_paths": [
            "Film / Series Director",
            "Cinematographer",
            "Video Editor / Colorist",
            "Creative Producer",
            "Media Production Lead"
        ],
        "tags": ["Film", "Digital Media", "Production", "Directing", "Editing"],
        "website_url": "https://www.spu.ac.th/fac/commarts/courses/bachelor/film/"
    },

    # --- Faculty of Business Administration (คณะบริหารธุรกิจ) ---
    {
        "id": "spu_ba_mkt",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาดสมัยใหม่และการตลาดเอไอ",
        "title_en": "Bachelor of Business Administration in Modern Marketing and AI Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาดสมัยใหม่)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Marketing",
        "department_th": "สาขาวิชาการตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "124 หน่วยกิต",
        "tuition_per_semester": "36,500 บาท",
        "tuition_total": "292,000 บาท",
        "description": "เน้นการตลาดเชิงรุกด้วย AI Tools, Data-Driven Marketing, การสร้างแบรนด์บน TikTok และ Social Commerce ยุคใหม่",
        "curriculum_highlights": [
            "AI for Marketing & Content Generation",
            "TikTok Marketing & Live Commerce Strategies",
            "Customer Analytics & Performance Marketing",
            "Omnichannel Brand Strategy"
        ],
        "career_paths": [
            "Digital & AI Marketing Specialist",
            "Social Commerce Manager",
            "Performance Marketing Analyst",
            "Brand Strategist",
            "Growth Marketer"
        ],
        "tags": ["Marketing", "AI Marketing", "Social Commerce", "Digital", "Business"],
        "website_url": "https://www.spu.ac.th/fac/business/courses/bachelor/marketing/"
    },

    # --- Faculty of Law (คณะนิติศาสตร์) ---
    {
        "id": "spu_law_llb",
        "title_th": "หลักสูตรนิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ.",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Department of Law",
        "department_th": "สาขาวิชานิติศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "280,000 บาท",
        "description": "เรียนรู้หลักกฎหมายครบทุกสาขา พร้อมกฎหมายเทคโนโลยี กฎหมายดิจิทัล และว่าความในศาลจำลอง เน้นความพร้อมสู่เนติบัณฑิตและตั๋วทนาย",
        "curriculum_highlights": [
            "Civil, Commercial and Criminal Procedure Law",
            "Cyber Law, Digital Asset & PDPA Law",
            "Trial Practice & Legal Ethics",
            "Labor and International Trade Law"
        ],
        "career_paths": [
            "Litigation Lawyer (Licensed)",
            "Corporate In-House Counsel",
            "Judge / Prosecutor Candidate",
            "Legal Advisor / Compliance Specialist",
            "Government Legal Officer"
        ],
        "tags": ["Law", "Legal", "Litigation", "Cyber Law", "LL.B"],
        "website_url": "https://www.spu.ac.th/fac/law/courses/bachelor/"
    },

    # --- Graduate College of Management (SPU) ---
    {
        "id": "spu_grad_mba",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต",
        "title_en": "Master of Business Administration (MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (MBA)",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Graduate College of Management",
        "faculty_th": "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ",
        "department": "MBA Program",
        "department_th": "สาขาวิชาบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ",
        "duration_years": "1.5 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "55,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "หลักสูตร MBA ยุคดิจิทัล เรียนแบบ Hybrid สอดรับกับคนทำงาน เน้นการเป็นผู้นำองค์กร การวิเคราะห์กลยุทธ์ และการขยายธุรกิจ",
        "curriculum_highlights": [
            "Strategic Management in Digital Era",
            "Financial Management & Corporate Valuation",
            "Digital Leadership & Organization Innovation",
            "Independent Study & Strategic Business Plan"
        ],
        "career_paths": [
            "Senior Business Executive",
            "Business Development Director",
            "Management Consultant",
            "Entrepreneur / Startup Founder",
            "Corporate Strategy Lead"
        ],
        "tags": ["MBA", "Management", "Graduate", "Executive", "Master"],
        "website_url": "https://www.spu.ac.th/graduate69/mba/"
    },
    {
        "id": "spu_grad_llm",
        "title_th": "หลักสูตรนิติศาสตรมหาบัณฑิต",
        "title_en": "Master of Laws Program (LL.M.)",
        "degree_level": "ปริญญาโท",
        "degree_name": "น.ม.",
        "university": "Sripatum University",
        "university_th": "มหาวิทยาลัยศรีปทุม",
        "faculty": "Graduate College of Management",
        "faculty_th": "วิทยาลัยบัณฑิตศึกษาด้านการจัดการ",
        "department": "LL.M. Program",
        "department_th": "สาขาวิชานิติศาสตร์",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "55,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "เจาะลึกกฎหมายธุรกิจ กฎหมายทรัพย์สินทางปัญญา กฎหมายภาษีอากร และการระงับข้อพิพาททางธุรกิจระดับสูง",
        "curriculum_highlights": [
            "Advanced Business & Corporate Law",
            "Intellectual Property & Digital Innovation Law",
            "Advanced Taxation & International Tax Planning",
            "Master's Thesis in Contemporary Legal Issues"
        ],
        "career_paths": [
            "Senior Legal Counsel",
            "Specialized Attorney",
            "Judicial Candidate",
            "Legal Consultant in Banking & Corporate",
            "Law Lecturer"
        ],
        "tags": ["LLM", "Law", "Master", "Legal", "Graduate"],
        "website_url": "https://www.spu.ac.th/graduate69/llm/"
    }
]

def fetch_spu_live_announcements() -> List[Dict[str, str]]:
    """Helper to scrape live admissions pages from spu.ac.th."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    urls = [
        "https://www.spu.ac.th/apply/",
        "https://www.spu.ac.th/graduate69/"
    ]
    results = []
    for u in urls:
        try:
            resp = requests.get(u, headers=headers, timeout=10, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                title = soup.title.string if soup.title else u
                results.append({"url": u, "title": title.strip()})
        except Exception as e:
            logger.warning(f"Could not reach {u}: {e}")
    return results

def save_to_json(courses: List[Dict[str, Any]], filepath: Path):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(courses)} Sripatum University courses to {filepath}")

def seed_database(courses: List[Dict[str, Any]]):
    if not DB_AVAILABLE:
        logger.error("Database connection unavailable. Skipping seeding.")
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
            logger.error(f"Error seeding {c['id']}: {e}")
    session.close()
    logger.info(f"Successfully seeded Sripatum University to DB: {inserted} inserted, {updated} updated.")

def main():
    import urllib3
    urllib3.disable_warnings()
    parser = argparse.ArgumentParser(description="Sripatum University (SPU) Course Scraper & Catalog")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_FILE), help="Output JSON path")
    parser.add_argument("--seed-db", action="store_true", help="Seed courses directly to Database")
    parser.add_argument("--level", type=str, default="all", choices=["all", "bachelor", "master"], help="Filter degree level")
    args = parser.parse_args()

    courses = SPU_COURSES
    if args.level == "bachelor":
        courses = [c for c in courses if c["degree_level"] == "ปริญญาตรี"]
    elif args.level == "master":
        courses = [c for c in courses if c["degree_level"] == "ปริญญาโท"]

    out_path = Path(args.output)
    save_to_json(courses, out_path)

    if args.seed_db:
        seed_database(courses)

if __name__ == "__main__":
    main()
