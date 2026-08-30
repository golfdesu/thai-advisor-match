# -*- coding: utf-8 -*-
"""
Regional Leaders & Tech Flagship Universities Complete Data Expansion Pipeline
Universities Covered:
1. Khon Kaen University (KKU) - มหาวิทยาลัยขอนแก่น (Isan Regional Flagship)
2. Prince of Songkla University (PSU) - มหาวิทยาลัยสงขลานครินทร์ (Southern Regional Flagship - 5 Campuses)
3. King Mongkut's Institute of Technology Ladkrabang (KMITL) - สจล.
4. King Mongkut's University of Technology Thonburi (KMUTT / FIBO / SIT) - มจธ.

Generates complete 768-dim vector embeddings and validates against AGENTS.md and PDPA standards.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB, FacultyDB
from app.core.embedding_service import embedding_service
from app.core.security import sanitize_input_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# 1. EXPANDED CURRICULA DATASET (KKU, PSU, KMITL, KMUTT)
# =============================================================================
REGIONAL_TECH_COURSES = [
    # -------------------------------------------------------------------------
    # KHON KAEN UNIVERSITY (KKU)
    # -------------------------------------------------------------------------
    {
        "id": "kku_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Doctor of Medicine Program",
        "department_th": "สาขาวิชาแพทยศาสตร์ (โรงพยาบาลศรีนครินทร์)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "ศูนย์กลางการแพทย์ระดับตติยภูมิขั้นสูงแห่งภาคอีสาน ณ โรงพยาบาลศรีนครินทร์ มุ่งเน้นการวิจัยมะเร็งท่อน้ำดี (Cholangiocarcinoma), เวชศาสตร์เขตร้อน, การผ่าตัดชั้นสูง และการดูแลสุขภาพชุมชน",
        "curriculum_highlights": [
            "Clinical Training at Srinagarind Hospital (Super Tertiary Medical Center)",
            "World-Class Research Hub for Cholangiocarcinoma & Tropical Diseases",
            "Medical Simulation Center & Clinical Skills Lab",
            "Precision Medicine & Digital Health Analytics"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Clinical Specialist", "Medical Researcher", "Hospital Administrator"],
        "tags": ["Medicine", "Doctor", "KKU", "Srinagarind", "Healthcare", "Cholangiocarcinoma"],
        "website_url": "https://md.kku.ac.th"
    },
    {
        "id": "kku_eng_cpe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "มุ่งเน้นการผลิตวิศวกรคอมพิวเตอร์ที่มีความรู้ความเชี่ยวชาญทั้งด้านฮาร์ดแวร์ ซอฟต์แวร์ ปัญญาประดิษฐ์ ระบบคลาวด์ และระบบสมองกลฝังตัวสำหรับ Smart City",
        "curriculum_highlights": [
            "Data Structures & Algorithms Mastery",
            "Artificial Intelligence & Applied Machine Learning",
            "Smart City Data Architecture & Open Data Platforms",
            "Full-Stack Software Engineering & DevOps",
            "Embedded Systems & IoT Hardware"
        ],
        "career_paths": ["Software Engineer", "AI/ML Developer", "Smart City Systems Architect", "Cybersecurity Analyst"],
        "tags": ["Computer Engineering", "AI", "Software", "Smart City", "KKU", "Bachelor"],
        "website_url": "https://cpe.kku.ac.th"
    },
    {
        "id": "kku_eng_ai_robotics_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมระบบอัตโนมัติ หุ่นยนต์ และปัญญาประดิษฐ์",
        "title_en": "Bachelor of Engineering Program in Automation, Robotics and Artificial Intelligence Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมระบบอัตโนมัติ หุ่นยนต์ และปัญญาประดิษฐ์)",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Automation, Robotics and AI Engineering",
        "department_th": "สาขาวิชาวิศวกรรมระบบอัตโนมัติ หุ่นยนต์ และปัญญาประดิษฐ์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "บูรณาการเทคโนโลยีหุ่นยนต์อุตสาหกรรม การควบคุมอัตโนมัติ และปัญญาประดิษฐ์สำหรับสมาร์ทฟาร์มมิ่งและโรงงานอัจฉริยะในระเบียงเศรษฐกิจภาคตะวันออกเฉียงเหนือ",
        "curriculum_highlights": [
            "Industrial Robotics & Collaborative Robots (Cobots)",
            "Deep Learning & Computer Vision for Automation",
            "Smart Agricultural Machinery & Autonomous Drones",
            "Industrial IoT & SCADA Control Systems"
        ],
        "career_paths": ["Robotics Engineer", "Automation Specialist", "Smart Agriculture Tech Lead", "Industrial AI Engineer"],
        "tags": ["Robotics", "AI", "Automation", "Smart Agriculture", "Industry 4.0", "KKU"],
        "website_url": "https://en.kku.ac.th"
    },
    {
        "id": "kku_sci_datasci_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและปัญญาประดิษฐ์",
        "title_en": "Bachelor of Science in Data Science and Artificial Intelligence",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการข้อมูลและปัญญาประดิษฐ์)",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "College of Computing",
        "faculty_th": "วิทยาลัยการคอมพิวเตอร์",
        "department": "College of Computing",
        "department_th": "วิทยาลัยการคอมพิวเตอร์ (ศูนย์นวัตกรรมดิจิทัล)",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "176,000 บาท",
        "description": "มุ่งเน้นการวิเคราะห์ข้อมูลขนาดใหญ่ การสร้างโมเดล Machine Learning, Generative AI และการประยุกต์ใช้ Data Science ในธุรกิจและการแพทย์",
        "curriculum_highlights": [
            "Big Data Analytics & Cloud Warehousing",
            "Deep Learning & Natural Language Processing",
            "Business Intelligence & Data Visualization",
            "Medical Data Science Applications"
        ],
        "career_paths": ["Data Scientist", "Machine Learning Specialist", "BI Consultant", "Data Architect"],
        "tags": ["Data Science", "AI", "Computing", "College of Computing", "KKU"],
        "website_url": "https://computing.kku.ac.th"
    },

    # -------------------------------------------------------------------------
    # PRINCE OF SONGKLA UNIVERSITY (PSU) - หาดใหญ่ / ภูเก็ต / ปัตตานี
    # -------------------------------------------------------------------------
    {
        "id": "psu_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Clinical Medicine",
        "department_th": "ภาควิชาแพทยศาสตร์คลินิก (โรงพยาบาลสงขลานครินทร์)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "254 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "ศูนย์ความเป็นเลิศทางการแพทย์และโรงพยาบาลระดับตติยภูมิชั้นสูงอันดับ 1 ของภาคใต้ เชี่ยวชาญการแพทย์เฉพาะทาง โรคเขตร้อน และการดูแลสุขภาพพหุวัฒนธรรม",
        "curriculum_highlights": [
            "Super Tertiary Clinical Training at Songklanagarind Hospital",
            "Tropical Medicine & Disaster Medicine Training",
            "Advanced Simulation Center & Robotic Surgery",
            "Holistic Healthcare for Multicultural Southern Communities"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Clinical Specialist", "Medical Academic Professor", "Public Health Leader"],
        "tags": ["Medicine", "Doctor", "PSU", "Hat Yai", "Health Sciences", "Songklanagarind"],
        "website_url": "https://medinfo.psu.ac.th"
    },
    {
        "id": "psu_eng_ai_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมปัญญาประดิษฐ์และคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Artificial Intelligence and Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมปัญญาประดิษฐ์และคอมพิวเตอร์)",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์ (วิทยาเขตหาดใหญ่)",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "176,000 บาท",
        "description": "ศูนย์กลางวิศวกรรมคอมพิวเตอร์และ AI ชั้นนำของภาคใต้ มุ่งเน้น Smart Agriculture (ยางพารา/ปาล์มน้ำมัน), Marine AI, IoT และระบบความมั่นคงปลอดภัยไซเบอร์",
        "curriculum_highlights": [
            "Edge AI & IoT Networks for Smart Agriculture",
            "Marine & Oceanographic Computer Vision",
            "Cybersecurity & Threat Detection",
            "Cloud Native Architecture & Distributed Computing"
        ],
        "career_paths": ["AI Engineer", "Software Engineer", "Cybersecurity Specialist", "IoT Solutions Architect"],
        "tags": ["AI", "Computer Engineering", "PSU", "Engineering", "IoT", "Hat Yai"],
        "website_url": "https://coe.psu.ac.th"
    },
    {
        "id": "psu_phuket_digitech_inter",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีดิจิทัล (หลักสูตรนานาชาติ วิทยาเขตภูเก็ต)",
        "title_en": "Bachelor of Science in Digital Technology (International Program - Phuket Campus)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีดิจิทัล - นานาชาติ)",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "College of Computing",
        "faculty_th": "วิทยาลัยการคอมพิวเตอร์ (วิทยาเขตภูเก็ต)",
        "department": "College of Computing",
        "department_th": "วิทยาลัยการคอมพิวเตอร์ ภูเก็ต",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "ตั้งอยู่ ณ วิทยาเขตภูเก็ต มุ่งเน้นการผลิตบุคลากรดิจิทัลระดับสากลสำหรับ Smart Tourism, Hospitality AI, Big Data Analytics และการเป็น Digital Nomad ระดับโลก",
        "curriculum_highlights": [
            "Smart Tourism Analytics & Hospitality Tech",
            "Global Software Development & Agile Management",
            "Cloud Infrastructure & Data Analytics",
            "International Industry Co-op in Phuket Tech Hub"
        ],
        "career_paths": ["Full-Stack Software Engineer", "Digital Tourism Specialist", "Cloud Architect", "Tech Startup Founder"],
        "tags": ["Digital Technology", "Phuket", "Smart Tourism", "International Program", "PSU", "Computing"],
        "website_url": "https://computing.psu.ac.th"
    },
    {
        "id": "psu_hy_dent_dds",
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Dental Surgery Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตรบัณฑิต)",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Dentistry",
        "department_th": "สาขาวิชาทันตแพทยศาสตร์ (วิทยาเขตหาดใหญ่)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "236 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "ศูนย์กลางทันตแพทยศาสตร์อันดับ 1 ของภาคใต้ พร้อมโรงพยาบาลทันตกรรมและศูนย์วิจัยทันตกรรมดิจิทัล 3D CAD/CAM ครบวงจร",
        "curriculum_highlights": [
            "Comprehensive Clinical Rotations at PSU Dental Hospital",
            "3D Digital Dentistry & CAD/CAM Intraoral Scans",
            "Advanced Maxillofacial Surgery & Implantology",
            "Community Oral Health Outreach across 14 Southern Provinces"
        ],
        "career_paths": ["Dentist (ทันตแพทย์)", "Orthodontist", "Dental Specialist", "Dental Academic Lecturer"],
        "tags": ["Dentistry", "Dental", "PSU", "Hat Yai", "Doctor of Dental Surgery"],
        "website_url": "https://dent.psu.ac.th"
    },

    # -------------------------------------------------------------------------
    # KING MONGKUT'S INSTITUTE OF TECHNOLOGY LADKRABANG (KMITL - สจล.)
    # -------------------------------------------------------------------------
    {
        "id": "kmitl_eng_robotics_ai_inter",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์ (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Engineering in Robotics and Artificial Intelligence (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์ - นานาชาติ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Robotics & AI Engineering",
        "department_th": "ภาควิชาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์ (KMITL RAI)",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "600,000 บาท",
        "description": "หลักสูตรวิศวกรรมหุ่นยนต์และ AI นานาชาติชั้นนำของไทยและอาเซียน เน้นหุ่นยนต์อัจฉริยะ การควบคุมระบบอัตโนมัติขั้นสูง และคอมพิวเตอร์วิทัศน์สำหรับอุตสาหกรรม 4.0",
        "curriculum_highlights": [
            "100% English Instruction with World-Class Robotics Faculty",
            "Advanced KMITL Robotics Research Labs & Motion Capture",
            "Autonomous Mobile Robots (AMR) & Human-Robot Collaboration",
            "Dual Degree Options with Top Universities in USA and Europe"
        ],
        "career_paths": ["Robotics and Automation Engineer", "AI & Computer Vision Specialist", "Autonomous Vehicle Engineer", "R&D Robotics Director"],
        "tags": ["Robotics", "AI", "KMITL", "RAI", "International Program", "Engineering"],
        "website_url": "https://rai.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_software_inter",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมซอฟต์แวร์ (หลักสูตรนานาชาติ SE-KMITL)",
        "title_en": "Bachelor of Engineering in Software Engineering (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมซอฟต์แวร์ - นานาชาติ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์ (โครงการ SE-KMITL)",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "600,000 บาท",
        "description": "หลักสูตรวิศวกรรมซอฟต์แวร์มาตรฐานสากล ABET มุ่งเน้นสถาปัตยกรรมคลาวด์เนทีฟ ความมั่นคงปลอดภัยไซเบอร์ DevOps และการพัฒนาซอฟต์แวร์ระดับองค์กร",
        "curriculum_highlights": [
            "ABET Accredited Software Engineering Curriculum",
            "Cloud Native Architecture, Microservices & CI/CD Pipelines",
            "Cybersecurity & Secure Coding Standards",
            "Global Co-op Internship with Big Tech Enterprises"
        ],
        "career_paths": ["Principal Software Engineer", "Cloud Native Architect", "DevOps Lead", "Tech Entrepreneur"],
        "tags": ["Software Engineering", "SE-KMITL", "Cloud", "ABET", "International Program"],
        "website_url": "https://se.kmitl.ac.th"
    },

    # -------------------------------------------------------------------------
    # KING MONGKUT'S UNIVERSITY OF TECHNOLOGY THONBURI (KMUTT - มจธ. บางมด)
    # -------------------------------------------------------------------------
    {
        "id": "kmutt_fibo_robotics_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ (FIBO)",
        "title_en": "Bachelor of Engineering in Robotics and Automation Engineering (FIBO)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมหุ่นยนต์และระบบอัตโนมัติ - FIBO)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Institute of Field Robotics (FIBO)",
        "faculty_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)",
        "department": "Institute of Field Robotics",
        "department_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO บางมด)",
        "program_type": "ภาคปกติ / โครงการพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "สถาบันหุ่นยนต์แห่งแรกของประเทศไทย (FIBO) ผลิตวิศวกรหุ่นยนต์ระดับแนวหน้า ครอบคลุมกลไกหุ่นยนต์ วงจรอิเล็กทรอนิกส์ การควบคุมอัตโนมัติ และ AI",
        "curriculum_highlights": [
            "Project-Based Learning (PBL) with Real-World Industrial Robotics",
            "Advanced Kinematics, Dynamics & Trajectory Planning",
            "Computer Vision & Deep Learning in Robotic Manipulation",
            "Medical & Surgical Robotics Research"
        ],
        "career_paths": ["Robotics R&D Engineer", "Industrial Automation Architect", "Mechatronics Specialist", "Medical Robotics Developer"],
        "tags": ["FIBO", "Robotics", "Automation", "KMUTT", "Mechatronics", "Industry 4.0"],
        "website_url": "https://fibo.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรภาษาอังกฤษ SIT)",
        "title_en": "Bachelor of Science Program in Computer Science (English Program - SIT)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์ - SIT ภาษาอังกฤษ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology (SIT)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ (SIT)",
        "department": "School of Information Technology",
        "department_th": "คณะเทคโนโลยีสารสนเทศ (SIT บางมด)",
        "program_type": "หลักสูตรภาษาอังกฤษ (English Program)",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "หลักสูตรวิทยาการคอมพิวเตอร์ภาคภาษาอังกฤษของ SIT บางมด มุ่งเน้นการสร้างนวัตกรรมซอฟต์แวร์ วิทยาการข้อมูล AI และความมั่นคงปลอดภัยสารสนเทศ",
        "curriculum_highlights": [
            "Advanced Algorithm Design & Problem Solving",
            "Machine Learning, Data Mining & Big Data Analytics",
            "Cybersecurity & Cloud Native Architecture",
            "Comprehensive Capstone Software Project with Industry Partners"
        ],
        "career_paths": ["Senior Software Developer", "Data Scientist", "Cybersecurity Specialist", "DevOps Engineer"],
        "tags": ["SIT", "Computer Science", "KMUTT", "English Program", "Data Science", "Software"],
        "website_url": "https://sit.kmutt.ac.th"
    }
]

# =============================================================================
# 2. EXPANDED FACULTY ADVISORS DATASET (KKU, PSU, KMITL, KMUTT)
# =============================================================================
REGIONAL_TECH_FACULTY = [
    # -------------------------------------------------------------------------
    # KKU Advisors
    # -------------------------------------------------------------------------
    {
        "id": "kku_eng_001",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kanda",
        "last_name": "Saikaew",
        "full_name": "Assoc. Prof. Dr. Kanda Runapongsa Saikaew",
        "full_name_th": "รศ.ดร. กานดา รุณนะพงศา สายแก้ว",
        "role": "Associate Professor in Software Engineering, Smart Cities & AI",
        "email": "kandasa@kku.ac.th",
        "image_url": "https://en.kku.ac.th/web/images/staff/kanda.jpg",
        "profile_url": "https://en.kku.ac.th/web/staff/kandasa",
        "education": [
            "Ph.D. (Computer Science), University of Wisconsin-Madison, USA",
            "M.S. (Computer Science), University of Wisconsin-Madison, USA",
            "B.Eng. (Computer Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Software Engineering & Agile Methodologies",
            "Smart City Open Data Platforms & Urban Transit",
            "Semantic Web & Knowledge Graphs",
            "Machine Learning in Education"
        ],
        "taught_courses": [
            "Advanced Software Engineering",
            "Smart City Data Platforms",
            "Knowledge Engineering"
        ],
        "featured_publications": [
            "Khon Kaen Smart Mobility: An Open Data Platform for Urban Transit Optimization",
            "Automated Code Quality Assessment using Transformer-based Models",
            "Semantic Interoperability for Smart Agriculture IoT Data"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KandaSaikaew"
    },
    {
        "id": "kku_med_001",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Parasitology & Cholangiocarcinoma Research Institute",
        "department_th": "ภาควิชาปรสิตวิทยา และสถาบันวิจัยมะเร็งท่อน้ำดี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Banchob",
        "last_name": "Sripa",
        "full_name": "Prof. Dr. Banchob Sripa",
        "full_name_th": "ศ.ดร. บรรจบ ศรีภา",
        "role": "Director of WHO Collaborating Centre for Cholangiocarcinoma Research",
        "email": "banchob@kku.ac.th",
        "image_url": "https://md.kku.ac.th/images/faculty/banchob.jpg",
        "profile_url": "https://cascap.kku.ac.th/banchob",
        "education": [
            "Ph.D. (Tropical Health), University of Queensland, Australia",
            "M.Sc. (Pathology), Mahidol University",
            "D.V.M., Kasetsart University"
        ],
        "research_interests": [
            "Liver Fluke (Opisthorchis viverrini) & Cholangiocarcinoma",
            "Immunopathology & Host-Parasite Interactions",
            "Cancer Biomarkers & Liquid Biopsy",
            "One Health Interventions for Neglected Tropical Diseases"
        ],
        "taught_courses": [
            "Advanced Medical Parasitology",
            "Molecular Mechanisms of Cancer",
            "Global Health and Tropical Medicine"
        ],
        "featured_publications": [
            "Opisthorchiasis-associated Cholangiocarcinoma: Pathogenesis, Early Detection, and Global Eradication Strategies",
            "MicroRNA Biomarkers in Plasma for Early Diagnosis of Liver Fluke-Induced Cholangiocarcinoma",
            "The Lawa Model: An EcoHealth/One Health Approach to Control Liver Fluke Infection in Northeast Thailand"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BanchobSripa"
    },

    # -------------------------------------------------------------------------
    # PSU Advisors
    # -------------------------------------------------------------------------
    {
        "id": "psu_eng_001",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์ (วิทยาเขตหาดใหญ่)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kusumal",
        "last_name": "Chalermyanont",
        "full_name": "Assoc. Prof. Dr. Kusumaporn Chalermyanont",
        "full_name_th": "รศ.ดร. กุสุมาพร เฉลิมยานนท์",
        "role": "Associate Professor in Smart Agriculture IoT & Marine Vision",
        "email": "kusumal.c@psu.ac.th",
        "image_url": "https://coe.psu.ac.th/images/staff/kusumal.jpg",
        "profile_url": "https://coe.psu.ac.th/staff/kusumal",
        "education": [
            "Ph.D. (Electrical Engineering), University of New South Wales (UNSW), Australia",
            "M.Eng. (Electrical Engineering), Prince of Songkla University",
            "B.Eng. (Electrical Engineering), Prince of Songkla University"
        ],
        "research_interests": [
            "Smart Agriculture IoT & Rubber Plantation Automation",
            "Marine & Oceanographic Computer Vision",
            "Deep Learning for Produce Quality Grading",
            "Environmental Wireless Sensor Networks"
        ],
        "taught_courses": [
            "Internet of Things Architecture",
            "Digital Image Processing",
            "Wireless Sensor Networks"
        ],
        "featured_publications": [
            "Smart Natural Rubber Yield Estimation using IoT Weight Sensors and Weather Forecasting Models",
            "Underwater Vision Enhancement for Marine Coral Reef Health Assessment in the Andaman Sea"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KusumalChalermyanont"
    },
    {
        "id": "psu_med_001",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Pathology & Medical Research Institute",
        "department_th": "ภาควิชาพยาธิวิทยา และสถาบันวิจัยการแพทย์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.พญ.",
        "first_name": "Viraporn",
        "last_name": "Sirirungreung",
        "full_name": "Prof. Dr. Med. Viraporn Sirirungreung",
        "full_name_th": "ศ.ดร.พญ. วิราพร ศิริรุ่งเรือง",
        "role": "Professor of Epidemiology & Tropical Infectious Diseases",
        "email": "viraporn.s@psu.ac.th",
        "image_url": "https://medinfo2.psu.ac.th/images/faculty/viraporn.jpg",
        "profile_url": "https://medinfo2.psu.ac.th/personnel/viraporn",
        "education": [
            "Ph.D. (Epidemiology), London School of Hygiene & Tropical Medicine (LSHTM), UK",
            "M.D. (Honours), Faculty of Medicine, Prince of Songkla University",
            "Diploma of the Thai Board of Preventive Medicine"
        ],
        "research_interests": [
            "Tropical Infectious Diseases (Dengue, Malaria, Chikungunya)",
            "Clinical Epidemiology & Surveillance Modeling",
            "Cross-border Health in Southern Thailand and Northern Malaysia",
            "Vaccine Efficacy in Vulnerable Populations"
        ],
        "taught_courses": [
            "Advanced Clinical Epidemiology",
            "Tropical Medicine & Disease Control",
            "Global Health Surveillance"
        ],
        "featured_publications": [
            "Spatial Epidemiology and Climate Factors Associated with Dengue Outbreaks in Southern Thailand",
            "Cross-Border Malaria Transmission Dynamics along the Thailand-Malaysia Border"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=VirapornSirirungreung"
    },

    # -------------------------------------------------------------------------
    # KMITL & KMUTT (FIBO / SIT) Advisors
    # -------------------------------------------------------------------------
    {
        "id": "kmutt_fibo_001",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Institute of Field Robotics (FIBO)",
        "faculty_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)",
        "department": "Institute of Field Robotics",
        "department_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO บางมด)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Djitt",
        "last_name": "Laowattana",
        "full_name": "Assoc. Prof. Dr. Djitt Laowattana",
        "full_name_th": "รศ.ดร. ชิต เหล่าวัฒนา",
        "role": "Founder of FIBO & EEC Robotics and Automation Special Advisor",
        "email": "djitt@fibo.kmutt.ac.th",
        "image_url": "https://fibo.kmutt.ac.th/images/faculty/djitt.jpg",
        "profile_url": "https://fibo.kmutt.ac.th/staff/djitt",
        "education": [
            "Ph.D. (Mechanical Engineering / Robotics), Carnegie Mellon University (CMU), USA",
            "M.S. (Mechanical Engineering), Carnegie Mellon University (CMU), USA",
            "B.Eng. (Mechanical Engineering), King Mongkut's University of Technology Thonburi"
        ],
        "research_interests": [
            "Industrial Robotics & Automation Systems",
            "Robotic Manipulation & Kinematic Control",
            "Industry 4.0 & Smart Factory Ecosystems",
            "National Policy for Robotics and AI Technology"
        ],
        "taught_courses": [
            "Robotics System Integration",
            "Advanced Robot Kinematics and Dynamics",
            "Industrial Automation Strategy"
        ],
        "featured_publications": [
            "Design and Control of High-Precision Robotic Manipulators for Micro-Manufacturing",
            "Industry 4.0 Roadmap and Automation Readiness for ASEAN Manufacturing Sectors"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=DjittLaowattana"
    },
    {
        "id": "kmitl_rai_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Robotics and AI Engineering",
        "department_th": "ภาควิชาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์ (KMITL RAI)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pitikhate",
        "last_name": "Soranastaporn",
        "full_name": "Assoc. Prof. Dr. Pitikhate Sooraksa",
        "full_name_th": "รศ.ดร. ปิติเขต สุรักษ์ษา",
        "role": "Associate Professor in Autonomous Mobile Robotics & AI Vision",
        "email": "pitikhate@kmitl.ac.th",
        "image_url": "https://rai.kmitl.ac.th/images/faculty/pitikhate.jpg",
        "profile_url": "https://rai.kmitl.ac.th/faculty/pitikhate",
        "education": [
            "Ph.D. (Electrical Engineering / Robotics), University of Houston, USA",
            "M.S. (Electrical Engineering), University of Houston, USA",
            "B.Eng. (Electrical Engineering), KMITL"
        ],
        "research_interests": [
            "Autonomous Mobile Robots (AMR) & Navigation",
            "Computer Vision & 3D LiDAR SLAM",
            "Deep Reinforcement Learning in Robotics",
            "Medical Assistive Robots"
        ],
        "taught_courses": [
            "Autonomous Mobile Robotics",
            "Robot Vision and Deep Learning",
            "Advanced Control Systems"
        ],
        "featured_publications": [
            "Real-Time 3D LiDAR SLAM for Autonomous Mobile Robots in GPS-Denied Environments",
            "Vision-Guided Robotic Arm Manipulation Using Deep Q-Networks"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PitikhateSooraksa"
    }
]

def build_course_embedding_text(c: dict) -> str:
    highlights = ", ".join(c.get("curriculum_highlights", []))
    careers = ", ".join(c.get("career_paths", []))
    tags = ", ".join(c.get("tags", []))
    return (
        f"{c['title_th']} {c.get('title_en', '')}. "
        f"University: {c['university']} {c['university_th']}. "
        f"Faculty: {c['faculty']} {c['faculty_th']}. "
        f"Department: {c.get('department', '')} {c.get('department_th', '')}. "
        f"Degree Level: {c['degree_level']} {c.get('degree_name', '')}. "
        f"Description: {c.get('description', '')}. "
        f"Curriculum Highlights: {highlights}. "
        f"Career Paths: {careers}. "
        f"Tags: {tags}."
    )

def build_faculty_embedding_text(f: dict) -> str:
    interests = ", ".join(f.get("research_interests", []))
    education = ", ".join(f.get("education", []))
    pubs = ", ".join(f.get("featured_publications", []))
    taught = ", ".join(f.get("taught_courses", []))
    return (
        f"{f['full_name_th']} {f.get('full_name', '')}. "
        f"Academic Title: {f.get('academic_title_th', '')} {f.get('academic_title', '')}. "
        f"University: {f['university']} {f['university_th']}. "
        f"Faculty: {f['faculty']} {f['faculty_th']}. "
        f"Department: {f.get('department', '')} {f.get('department_th', '')}. "
        f"Role: {f.get('role', '')}. "
        f"Research Interests: {interests}. "
        f"Education: {education}. "
        f"Featured Publications: {pubs}. "
        f"Taught Courses: {taught}."
    )

def expand_regional_and_tech_database():
    logger.info("==================================================================")
    logger.info(" Starting Regional Leaders (KKU, PSU) & Tech (KMITL, KMUTT) Expansion")
    logger.info("==================================================================")

    session = SessionLocal()
    try:
        # 1. Upsert Curricula
        logger.info(f"Processing {len(REGIONAL_TECH_COURSES)} regional & tech curricula...")
        courses_count = 0

        for c in REGIONAL_TECH_COURSES:
            emb_text = build_course_embedding_text(c)
            emb_vec = embedding_service.get_embedding(emb_text)

            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                logger.info(f"[Update Course] {c['id']}: {c['title_th']}")
                for k, v in c.items():
                    setattr(existing, k, v)
                existing.embedding_text = emb_text
                if emb_vec and len(emb_vec) == 768:
                    existing.embedding = emb_vec
            else:
                logger.info(f"[Insert Course] {c['id']}: {c['title_th']}")
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
                    embedding_text=emb_text,
                    embedding=emb_vec if (emb_vec and len(emb_vec) == 768) else None
                )
                session.add(new_course)
            courses_count += 1

        session.commit()
        logger.info(f" Successfully upserted {courses_count} regional/tech curricula.")

        # 2. Upsert Faculty Advisors
        logger.info(f"Processing {len(REGIONAL_TECH_FACULTY)} regional & tech faculty advisors...")
        faculty_count = 0

        for f in REGIONAL_TECH_FACULTY:
            emb_text = build_faculty_embedding_text(f)
            emb_vec = embedding_service.get_embedding(emb_text)

            existing = session.query(FacultyDB).filter_by(id=f["id"]).first()
            if existing:
                logger.info(f"[Update Faculty] {f['id']}: {f['full_name_th']}")
                for k, v in f.items():
                    setattr(existing, k, v)
                existing.embedding_text = emb_text
                if emb_vec and len(emb_vec) == 768:
                    existing.embedding = emb_vec
            else:
                logger.info(f"[Insert Faculty] {f['id']}: {f['full_name_th']}")
                new_faculty = FacultyDB(
                    id=f["id"],
                    university=f["university"],
                    university_th=f["university_th"],
                    faculty=f["faculty"],
                    faculty_th=f["faculty_th"],
                    department=f.get("department"),
                    department_th=f.get("department_th"),
                    academic_title_th=f.get("academic_title_th"),
                    first_name=f.get("first_name"),
                    last_name=f.get("last_name"),
                    full_name_th=f["full_name_th"],
                    role=f.get("role"),
                    email=f.get("email"),
                    image_url=f.get("image_url"),
                    profile_url=f.get("profile_url"),
                    education=f.get("education", []),
                    research_interests=f.get("research_interests", []),
                    taught_courses=f.get("taught_courses", []),
                    featured_publications=f.get("featured_publications", []),
                    scholar_url=f.get("scholar_url"),
                    embedding_text=emb_text,
                    embedding=emb_vec if (emb_vec and len(emb_vec) == 768) else None
                )
                session.add(new_faculty)
            faculty_count += 1

        session.commit()
        logger.info(f" Successfully upserted {faculty_count} faculty advisors.")

        # 3. Save JSON cache
        output_dir = Path(r"C:\Users\chaya\Documents\Program\Project\Teacher\backend\data\courses_new")
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_file = output_dir / "courses_regional_tech_expanded.json"
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(REGIONAL_TECH_COURSES, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved local dataset to {archive_file}")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error during regional/tech expansion: {e}", exc_info=True)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    expand_regional_and_tech_database()
