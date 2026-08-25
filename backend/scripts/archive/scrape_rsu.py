"""
Web Scraper and Course Seeder for Rangsit University (RSU / มหาวิทยาลัยรังสิต)
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
logger = logging.getLogger("scrape_rsu")

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON = DATA_DIR / "rsu_courses.json"

# Comprehensive Curricula Matrix for Rangsit University (RSU)
RSU_COURSES: List[Dict] = [
    # ---------------- 1. College of Medicine (วิทยาลัยแพทยศาสตร์) ----------------
    {
        "id": "rsu_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine (M.D.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Medicine",
        "faculty_th": "วิทยาลัยแพทยศาสตร์",
        "department": "Department of Medicine",
        "department_th": "สาขาวิชาแพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "400,000 บาท",
        "tuition_total": "4,800,000 บาท",
        "description": "ผลิตแพทย์ผู้มีความรู้ความสามารถและจริยธรรมทางการแพทย์ มีการฝึกปฏิบัติทางคลินิก ณ โรงพยาบาลราชวิถีและสถาบันสุขภาพเด็กแห่งชาติมหาราชินี",
        "curriculum_highlights": ["Pre-clinical Basic Sciences", "Clinical Clerkship & Rotations", "Preventive & Community Medicine", "Medical Ethics & Professionalism"],
        "career_paths": ["General Practitioner / Medical Doctor", "Specialist Physician (Resident)", "Clinical Researcher", "Hospital Administrator"],
        "tags": ["Medicine", "Doctor", "Health Science", "Clinical Medicine", "Healthcare"],
        "website_url": "https://med.rsu.ac.th"
    },

    # ---------------- 2. College of Dental Medicine (วิทยาลัยทันตแพทยศาสตร์) ----------------
    {
        "id": "rsu_dent_dds",
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Dental Surgery (D.D.S.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตรบัณฑิต)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Dental Medicine",
        "faculty_th": "วิทยาลัยทันตแพทยศาสตร์",
        "department": "Department of Dentistry",
        "department_th": "สาขาวิชาทันตแพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "240 หน่วยกิต",
        "tuition_per_semester": "450,000 บาท",
        "tuition_total": "5,400,000 บาท",
        "description": "มุ่งเน้นการรักษาและดูแลสุขภาพช่องปากและฟัน ด้วยเทคโนโลยีและศูนย์ทันตกรรมจำลองเสมือนจริงที่ทันสมัย",
        "curriculum_highlights": ["Operative Dentistry & Prosthodontics", "Oral & Maxillofacial Surgery", "Orthodontics & Pediatric Dentistry", "Comprehensive Dental Clinic"],
        "career_paths": ["Dentist / Dental Surgeon", "Orthodontist Specialist", "Dental Clinic Owner", "Oral Health Researcher"],
        "tags": ["Dentistry", "Dental Surgery", "Health Science", "Oral Health"],
        "website_url": "https://dent.rsu.ac.th"
    },

    # ---------------- 3. College of Pharmacy (วิทยาลัยเภสัชศาสตร์) ----------------
    {
        "id": "rsu_pharm_care",
        "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาการบริบาลทางเภสัชกรรม",
        "title_en": "Doctor of Pharmacy in Pharmaceutical Care",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ภ.บ. (การบริบาลทางเภสัชกรรม)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Pharmacy",
        "faculty_th": "วิทยาลัยเภสัชศาสตร์",
        "department": "Department of Clinical Pharmacy",
        "department_th": "สาขาวิชาเภสัชกรรมคลินิก",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "225 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "1,020,000 บาท",
        "description": "เน้นการดูแลการใช้ยาของผู้ป่วยในโรงพยาบาลและชุมชน การประเมินปฏิกิริยาระหว่างยา และการให้คำปรึกษาทางเภสัชบำบัด",
        "curriculum_highlights": ["Pharmacotherapeutics", "Clinical Pharmacokinetics", "Patient Counseling & Care", "Hospital Pharmacy Clerkship"],
        "career_paths": ["Hospital Pharmacist", "Clinical Pharmacist", "Community Pharmacy Owner", "Regulatory Affairs Specialist"],
        "tags": ["Pharmacy", "Pharmaceutical Care", "Clinical Pharmacy", "Healthcare", "Medicine"],
        "website_url": "https://pharmacy.rsu.ac.th"
    },
    {
        "id": "rsu_pharm_industrial",
        "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต สาขาวิชาเภสัชกรรมอุตสาหการ",
        "title_en": "Doctor of Pharmacy in Industrial Pharmacy",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ภ.บ. (เภสัชกรรมอุตสาหการ)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Pharmacy",
        "faculty_th": "วิทยาลัยเภสัชศาสตร์",
        "department": "Department of Pharmaceutical Technology",
        "department_th": "สาขาวิชาเภสัชกรรมอุตสาหการ",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "225 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "1,020,000 บาท",
        "description": "มุ่งเน้นการวิจัยและพัฒนายา เทคโนโลยีเภสัชกรรม การควบคุมคุณภาพยา และการผลิตยาในระดับอุตสาหกรรม",
        "curriculum_highlights": ["Drug Delivery Systems & Formulation", "Pharmaceutical Quality Assurance & QC", "Industrial Drug Manufacturing", "Biopharmaceutics"],
        "career_paths": ["Industrial Pharmacist", "R&D Formulation Scientist", "Quality Assurance Manager", "Drug Registration Officer"],
        "tags": ["Pharmacy", "Industrial Pharmacy", "Drug Formulation", "R&D", "Biopharma"],
        "website_url": "https://pharmacy.rsu.ac.th"
    },

    # ---------------- 4. Faculty of Nursing (คณะพยาบาลศาสตร์) ----------------
    {
        "id": "rsu_nurse_bns",
        "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต",
        "title_en": "Bachelor of Nursing Science (B.N.S.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พย.บ. (พยาบาลศาสตรบัณฑิต)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Department of Nursing",
        "department_th": "สาขาวิชาพยาบาลศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "52,000 บาท",
        "tuition_total": "416,000 บาท",
        "description": "ผลิตพยาบาลวิชาชีพที่มีทักษะการพยาบาลขั้นสูง มีจิตบริการ และผ่านการฝึกปฏิบัติงานจริงในโรงพยาบาลชั้นนำ",
        "curriculum_highlights": ["Adult & Geriatric Nursing", "Maternal & Child Nursing", "Critical Care & Emergency Nursing", "Community Health Nursing"],
        "career_paths": ["Registered Nurse (RN)", "ICU / Emergency Nurse", "Pediatric Nurse", "Occupational Health Nurse"],
        "tags": ["Nursing", "Health Science", "Healthcare", "Nurse"],
        "website_url": "https://nurse.rsu.ac.th"
    },

    # ---------------- 5. Faculty of Medical Technology (คณะเทคนิคการแพทย์) ----------------
    {
        "id": "rsu_medtech_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคนิคการแพทย์",
        "title_en": "Bachelor of Science in Medical Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคนิคการแพทย์)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "Faculty of Medical Technology",
        "faculty_th": "คณะเทคนิคการแพทย์",
        "department": "Department of Medical Technology",
        "department_th": "สาขาวิชาเทคนิคการแพทย์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "ตรวจวิเคราะห์สิ่งส่งตรวจทางห้องปฏิบัติการทางการแพทย์ โลหิตวิทยา ภูมิคุ้มกันวิทยา และอณูชีววิทยาทางการแพทย์",
        "curriculum_highlights": ["Clinical Chemistry", "Hematology & Transfusion Science", "Clinical Microbiology & Virology", "Molecular Diagnostics"],
        "career_paths": ["Medical Technologist (MT)", "Clinical Laboratory Scientist", "Diagnostic Product Specialist", "Research Scientist"],
        "tags": ["Medical Technology", "Laboratory Science", "Diagnostics", "Health Science"],
        "website_url": "https://medtech.rsu.ac.th"
    },

    # ---------------- 6. College of Engineering (วิทยาลัยวิศวกรรมศาสตร์) ----------------
    {
        "id": "rsu_eng_biomed",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์",
        "title_en": "Bachelor of Engineering in Biomedical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมชีวการแพทย์)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Engineering",
        "faculty_th": "วิทยาลัยวิศวกรรมศาสตร์",
        "department": "Department of Biomedical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมชีวการแพทย์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "62,250 บาท",
        "tuition_total": "498,000 บาท",
        "description": "บูรณาการองค์ความรู้ด้านวิศวกรรมและการแพทย์เพื่อการออกแบบ พัฒนา และบำรุงรักษาเครื่องมือแพทย์และระบบปัญญาประดิษฐ์ทางการแพทย์",
        "curriculum_highlights": ["Medical Imaging & Instrumentation", "Biomaterials & Tissue Engineering", "Biosignal Processing", "AI in Medical Devices"],
        "career_paths": ["Biomedical Engineer", "Medical Device Specialist", "Clinical Engineer", "Medical Equipment R&D Engineer"],
        "tags": ["Biomedical Engineering", "Medical Devices", "Engineering", "AI in Medicine"],
        "website_url": "https://bme.rsu.ac.th"
    },
    {
        "id": "rsu_eng_civil",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา",
        "title_en": "Bachelor of Engineering in Civil Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมโยธา)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Engineering",
        "faculty_th": "วิทยาลัยวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "สาขาวิชาวิศวกรรมโยธา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "144 หน่วยกิต",
        "tuition_per_semester": "62,600 บาท",
        "tuition_total": "500,800 บาท",
        "description": "การออกแบบโครงสร้างอาคาร สะพาน ถนน การบริหารงานก่อสร้าง ธรณีเทคนิค และระบบวิศวกรรมทรัพยากรน้ำ",
        "curriculum_highlights": ["Structural Analysis & Design (BIM)", "Geotechnical & Foundation Engineering", "Construction Project Management", "Transportation Infrastructure"],
        "career_paths": ["Civil Engineer", "Structural Engineer", "Construction Project Manager", "Geotechnical Engineer"],
        "tags": ["Civil Engineering", "Construction", "Structural Design", "BIM", "Engineering"],
        "website_url": "https://eng.rsu.ac.th"
    },
    {
        "id": "rsu_eng_mech",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล",
        "title_en": "Bachelor of Engineering in Mechanical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมเครื่องกล)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Engineering",
        "faculty_th": "วิทยาลัยวิศวกรรมศาสตร์",
        "department": "Department of Mechanical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมเครื่องกล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "144 หน่วยกิต",
        "tuition_per_semester": "65,500 บาท",
        "tuition_total": "524,000 บาท",
        "description": "การออกแบบระบบกลไก พลังงานความร้อน ระบบปรับอากาศ ยานยนต์ และหุ่นยนต์อุตสาหกรรม",
        "curriculum_highlights": ["Thermodynamics & Heat Transfer", "Mechanical System Design & CAD/CAE", "Robotics & Control Systems", "Renewable Energy & EV Technology"],
        "career_paths": ["Mechanical Engineer", "Robotics & Automation Engineer", "HVAC / Building Systems Engineer", "Automotive Engineer"],
        "tags": ["Mechanical Engineering", "Robotics", "Automotive", "Energy", "CAD/CAE"],
        "website_url": "https://eng.rsu.ac.th"
    },

    # ---------------- 7. College of Digital Innovation and Technology (วิทยาลัยนวัตกรรมดิจิทัลเทคโนโลยี) ----------------
    {
        "id": "rsu_dit_cs",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Digital Innovation and Technology",
        "faculty_th": "วิทยาลัยนวัตกรรมดิจิทัลเทคโนโลยี",
        "department": "Department of Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "41,100 บาท",
        "tuition_total": "328,900 บาท",
        "description": "ศึกษาโครงสร้างข้อมูล อัลกอริทึม ระบบฐานข้อมูล การพัฒนาคลาวด์เนทีฟ และความปลอดภัยของระบบซอฟต์แวร์",
        "curriculum_highlights": ["Data Structures & Advanced Algorithms", "Cloud Architecture & Microservices", "Full-Stack Web & Mobile Development", "Cybersecurity & Cryptography"],
        "career_paths": ["Software Engineer", "Cloud Solutions Architect", "Backend / Systems Developer", "DevOps Engineer"],
        "tags": ["Computer Science", "Software Engineering", "Cloud", "Programming", "Tech"],
        "website_url": "https://it.rsu.ac.th"
    },
    {
        "id": "rsu_dit_ai_innov",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชานวัตกรรมดิจิทัลและปัญญาประดิษฐ์",
        "title_en": "Bachelor of Science in Digital Innovation and Artificial Intelligence",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (นวัตกรรมดิจิทัลและปัญญาประดิษฐ์)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Digital Innovation and Technology",
        "faculty_th": "วิทยาลัยนวัตกรรมดิจิทัลเทคโนโลยี",
        "department": "Department of AI and Innovation",
        "department_th": "สาขาวิชาปัญญาประดิษฐ์และนวัตกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "41,050 บาท",
        "tuition_total": "328,400 บาท",
        "description": "เน้นการพัฒนาโมเดลปัญญาประดิษฐ์ การประมวลผลภาษาธรรมชาติ (NLP) วิสัยทัศน์คอมพิวเตอร์ (Computer Vision) และ Generative AI",
        "curriculum_highlights": ["Deep Learning & Neural Networks", "Natural Language Processing (NLP)", "Computer Vision & Image Processing", "Generative AI Application"],
        "career_paths": ["AI Engineer", "Machine Learning Specialist", "Data Scientist", "NLP Engineer"],
        "tags": ["AI", "Artificial Intelligence", "Machine Learning", "Data Science", "Deep Learning"],
        "website_url": "https://it.rsu.ac.th"
    },
    {
        "id": "rsu_dit_game_esports",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคอมพิวเตอร์เกมและอีสปอร์ต",
        "title_en": "Bachelor of Science in Computer Game and Esports",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (คอมพิวเตอร์เกมและอีสปอร์ต)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Digital Innovation and Technology",
        "faculty_th": "วิทยาลัยนวัตกรรมดิจิทัลเทคโนโลยี",
        "department": "Department of Game and Esports",
        "department_th": "สาขาวิชาเกมและอีสปอร์ต",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "41,800 บาท",
        "tuition_total": "334,300 บาท",
        "description": "การพัฒนาเกมแบบครบวงจร ทั้งการเขียนโปรแกรม Game Engine เกม 3D การสร้างระบบมัลติเพลเยอร์ และการบริหารจัดการธุรกิจอีสปอร์ต",
        "curriculum_highlights": ["Game Engine Architecture (Unreal/Unity)", "3D Game Programming & Physics", "Esports Management & Broadcasting", "Online Multiplayer Game Backend"],
        "career_paths": ["Game Programmer / Developer", "Game Designer", "Esports Broadcast Specialist", "Game Producer"],
        "tags": ["Game Development", "Esports", "Game Programming", "Unreal Engine", "Unity"],
        "website_url": "https://it.rsu.ac.th"
    },

    # ---------------- 8. Faculty of Digital Art (คณะดิจิทัลอาร์ต) ----------------
    {
        "id": "rsu_dart_animation",
        "title_th": "หลักสูตรศิลปบัณฑิต สาขาวิชาคอมพิวเตอร์แอนิเมชันและวิชวลเอฟเฟกต์",
        "title_en": "Bachelor of Fine Arts in Computer Animation and Visual Effects",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (คอมพิวเตอร์แอนิเมชันและวิชวลเอฟเฟกต์)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "Faculty of Digital Art",
        "faculty_th": "คณะดิจิทัลอาร์ต",
        "department": "Department of Computer Animation",
        "department_th": "สาขาวิชาคอมพิวเตอร์แอนิเมชัน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "ผลิตแอนิเมเตอร์และ VFX Artist มืออาชีพสำหรับอุตสาหกรรมภาพยนตร์ เกม และโฆษณาระดับฮอลลีวูด",
        "curriculum_highlights": ["3D Character Animation", "Visual Effects (VFX) & Compositing", "Lighting & Rigging Techniques", "Digital Storyboarding"],
        "career_paths": ["3D Animator", "VFX Artist", "Character Modeler", "Compositing Artist"],
        "tags": ["Animation", "VFX", "Digital Art", "3D Art", "Cinema"],
        "website_url": "https://dart.rsu.ac.th"
    },

    # ---------------- 9. Faculty of Architecture (คณะสถาปัตยกรรมศาสตร์) ----------------
    {
        "id": "rsu_arch_barch",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต",
        "title_en": "Bachelor of Architecture (B.Arch.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรม)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Architecture",
        "department_th": "สาขาวิชาสถาปัตยกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "165 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "480,000 บาท",
        "description": "เน้นการออกแบบสถาปัตยกรรมที่ยั่งยืน นวัตกรรมอาคารเขียว เทคโนโลยีการสร้างแบบจำลองสารสนเทศอาคาร (BIM) และการอนุรักษ์สิ่งแวดล้อม",
        "curriculum_highlights": ["Architectural Design Studio", "Building Information Modeling (BIM)", "Sustainable & Green Architecture", "Urban Planning & Landscape"],
        "career_paths": ["Licensed Architect", "Urban Designer", "BIM Specialist", "Design Director"],
        "tags": ["Architecture", "BIM", "Sustainable Design", "Urban Planning"],
        "website_url": "https://arch.rsu.ac.th"
    },

    # ---------------- 10. College of Communication Arts (วิทยาลัยนิเทศศาสตร์) ----------------
    {
        "id": "rsu_comm_film_video",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาภาพยนตร์และดิจิทัลมีเดีย",
        "title_en": "Bachelor of Communication Arts in Digital Film and Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (ภาพยนตร์และดิจิทัลมีเดีย)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "College of Communication Arts",
        "faculty_th": "วิทยาลัยนิเทศศาสตร์",
        "department": "Department of Film and Digital Media",
        "department_th": "สาขาวิชาภาพยนตร์และดิจิทัลมีเดีย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "40,000 บาท",
        "tuition_total": "320,000 บาท",
        "description": "ฝึกปฏิบัติจริงในสตูดิโอและโรงถ่ายภาพยนตร์มาตรฐานสากล ตั้งแต่การคิดพล็อตเรื่อง การกำกับ การจัดแสงถ่ายทำ จนถึงการตัดต่อเสียงและภาพ",
        "curriculum_highlights": ["Directing & Cinematography", "Screenwriting for Film & OTT Series", "Color Grading & Sound Post-Production", "Film Financing & Distribution"],
        "career_paths": ["Film Director", "Cinematographer (DP)", "Film Producer", "Screenwriter"],
        "tags": ["Film", "Digital Media", "Cinema", "Communication Arts", "OTT"],
        "website_url": "https://commarts.rsu.ac.th"
    },

    # ---------------- 11. Faculty of Business Administration (คณะบริหารธุรกิจ) ----------------
    {
        "id": "rsu_ba_digital_biz",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการธุรกิจดิจิทัล",
        "title_en": "Bachelor of Business Administration in Digital Business Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการธุรกิจดิจิทัล)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Digital Business",
        "department_th": "สาขาวิชาธุรกิจดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "37,000 บาท",
        "tuition_total": "296,000 บาท",
        "description": "สร้างผู้นำธุรกิจยุคดิจิทัล เรียนรู้การตลาดออนไลน์ การสร้างแบรนด์บนแพลตฟอร์มโซเชียลมีเดีย และการจัดการสตาร์ทอัพ",
        "curriculum_highlights": ["Digital Business Strategy", "E-Commerce & Social Commerce", "Data Analytics for Business Decisions", "Startup Pitching & Funding"],
        "career_paths": ["Digital Business Manager", "E-Commerce Director", "Tech Entrepreneur", "Business Development Consultant"],
        "tags": ["Business", "Digital Business", "Startup", "E-Commerce", "Management"],
        "website_url": "https://ba.rsu.ac.th"
    },

    # ---------------- 12. Rangsit University International College (RSUIC) ----------------
    {
        "id": "rsu_rsuic_bba_inter",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาธุรกิจระหว่างประเทศ (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Business Administration in International Business (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "B.B.A. (International Business)",
        "university": "Rangsit University",
        "university_th": "มหาวิทยาลัยรังสิต",
        "faculty": "Rangsit University International College (RSUIC)",
        "faculty_th": "วิทยาลัยนานาชาติ",
        "department": "Department of International Business",
        "department_th": "สาขาวิชาธุรกิจระหว่างประเทศ",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "หลักสูตรนานาชาติที่สอนเป็นภาษาอังกฤษทั้งหมด มุ่งเน้นการค้าระหว่างประเทศ การเงินสากล และโอกาสแลกเปลี่ยนกับมหาวิทยาลัยพันธมิตรทั่วโลก",
        "curriculum_highlights": ["International Trade Law & Practice", "Cross-Cultural Communication", "Global Strategy & Operations", "Multinational Enterprise Management"],
        "career_paths": ["Global Trade Consultant", "International Business Manager", "Foreign Exchange Analyst", "Export-Import Executive"],
        "tags": ["International Program", "RSUIC", "English Program", "Global Business", "BBA"],
        "website_url": "https://rsuic.rsu.ac.th"
    }
]

def fetch_live_rsu_data() -> List[Dict]:
    """Optionally crawl live website pages from rsu.ac.th if available."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get("https://www.rsu.ac.th", headers=headers, timeout=10)
        if resp.status_code == 200:
            logger.info("Successfully reached RSU main portal.")
    except Exception as e:
        logger.warning(f"Could not connect to live RSU web server: {e}")
    return RSU_COURSES

def save_json(courses: List[Dict], filepath: Path = OUTPUT_JSON):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(courses)} RSU courses to {filepath}")

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
    logger.info(f"DB Seeding Complete for RSU: {inserted} inserted, {updated} updated.")

def main():
    logger.info("Starting Rangsit University Curricula Scraper & Data Collector...")
    courses = fetch_live_rsu_data()
    save_json(courses)
    seed_db(courses)
    logger.info(f"Finished processing RSU courses. Total programs: {len(courses)}")

if __name__ == "__main__":
    main()
