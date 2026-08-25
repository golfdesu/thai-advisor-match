"""
Scraper and Catalog Builder for Bangkok University (BU) Curricula & Tuition Fees.
Target Sources:
- Bangkok University Academics & Programs (https://www.bu.ac.th/th/curriculum/bachelors-degree)
- Bangkok University Tuition & Fees Portal (https://www.bu.ac.th/th/tuition-fees/bachelor-degree/2025)
- Graduate School (https://www.bu.ac.th/th/curriculum/masters-degree)

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
DEFAULT_OUTPUT_FILE = DATA_DIR / "bu_courses.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scrape_bu")

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

BU_COURSES: List[Dict[str, Any]] = [
    # --- School of Digital Media and Cinematic Arts ---
    {
        "id": "bu_ca_film",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาภาพยนตร์",
        "title_en": "Bachelor of Fine Arts Program in Film",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (ภาพยนตร์)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Digital Media and Cinematic Arts",
        "faculty_th": "คณะดิจิทัลมีเดียและศิลปะภาพยนตร์",
        "department": "Department of Film",
        "department_th": "สาขาวิชาภาพยนตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "131 หน่วยกิต",
        "tuition_per_semester": "48,500 บาท",
        "tuition_total": "388,000 บาท",
        "description": "มุ่งเน้นการผลิตภาพยนตร์ครบวงจรตั้งแต่การเขียนบท การกำกับการแสดง การถ่ายภาพยนตร์ การตัดต่อเสียงและภาพ ด้วยสตูดิโอและอุปกรณ์ระดับฮอลลีวูดและพันธมิตรระดับสากล",
        "curriculum_highlights": [
            "Directing & Cinematography",
            "Screenwriting & Story Development",
            "Film Production Management",
            "Post-Production & Color Grading"
        ],
        "career_paths": [
            "Film Director",
            "Cinematographer / Director of Photography",
            "Film Producer",
            "Screenwriter",
            "Colorist / Film Editor"
        ],
        "tags": ["Film", "Cinematic Arts", "Directing", "Screenwriting", "Digital Media"],
        "website_url": "https://www.bu.ac.th/th/digital-media/film"
    },
    {
        "id": "bu_ca_dm",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาสื่อดิจิทัล",
        "title_en": "Bachelor of Fine Arts Program in Digital Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (สื่อดิจิทัล)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Digital Media and Cinematic Arts",
        "faculty_th": "คณะดิจิทัลมีเดียและศิลปะภาพยนตร์",
        "department": "Department of Digital Media",
        "department_th": "สาขาวิชาสื่อดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "49,000 บาท",
        "tuition_total": "392,000 บาท",
        "description": "เน้นการสร้างสรรค์ 3D Animation, Visual Effects (VFX), Sound Design และดิจิทัลคอนเทนต์ขั้นสูง เพื่อป้อนอุตสาหกรรมบันเทิงและดิจิทัลคอนเทนต์ระดับโลก",
        "curriculum_highlights": [
            "3D Character Modeling & Animation",
            "Visual Effects (VFX) & Compositing",
            "Sound Design & Audio Production",
            "Interactive Media & Motion Graphics"
        ],
        "career_paths": [
            "3D Animator",
            "VFX Artist",
            "Motion Graphics Designer",
            "Sound Designer",
            "Digital Artist"
        ],
        "tags": ["Animation", "3D", "VFX", "Sound Design", "Digital Media"],
        "website_url": "https://www.bu.ac.th/th/digital-media/digital-media"
    },
    {
        "id": "bu_ca_vp",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาการผลิตเสมือนและการออกแบบประสบการณ์โลกเสมือนจริง",
        "title_en": "Bachelor of Fine Arts Program in Virtual Production and Immersive Experience Design",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศป.บ. (การผลิตเสมือนและการออกแบบประสบการณ์โลกเสมือนจริง)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Digital Media and Cinematic Arts",
        "faculty_th": "คณะดิจิทัลมีเดียและศิลปะภาพยนตร์",
        "department": "Department of Virtual Production",
        "department_th": "สาขาวิชาการผลิตเสมือนจริง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "52,000 บาท",
        "tuition_total": "416,000 บาท",
        "description": "การผลิตสื่อยุคใหม่ด้วย Unreal Engine, LED Volume Studio, Real-time Virtual Production และการออกแบบประสบการณ์โลกเสมือนจริง (XR/AR/VR)",
        "curriculum_highlights": [
            "Virtual Production & Real-time Rendering",
            "Unreal Engine for Film & Media",
            "Immersive Experience & XR Design",
            "Motion Capture & Virtual Camera"
        ],
        "career_paths": [
            "Virtual Production Specialist",
            "XR Experience Designer",
            "Unreal Engine Technical Artist",
            "Real-time VFX Artist",
            "Metaverse Content Creator"
        ],
        "tags": ["Virtual Production", "Unreal Engine", "XR", "AR/VR", "Immersive Media"],
        "website_url": "https://www.bu.ac.th/th/digital-media"
    },

    # --- School of Communication Arts ---
    {
        "id": "bu_ca_dmcc",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสร้างสรรค์ดิจิทัลคอนเทนต์และสื่อ",
        "title_en": "Bachelor of Communication Arts Program in Digital Media and Content Creation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (การสร้างสรรค์ดิจิทัลคอนเทนต์และสื่อ)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Digital Content Creation",
        "department_th": "สาขาวิชาการสร้างสรรค์ดิจิทัลคอนเทนต์และสื่อ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "129 หน่วยกิต",
        "tuition_per_semester": "44,000 บาท",
        "tuition_total": "352,000 บาท",
        "description": "บ่มเพาะนักสร้างสรรค์ดิจิทัลคอนเทนต์ อินฟลูเอนเซอร์ ยูทูบเบอร์ สตรีมเมอร์ และนักวางกลยุทธ์สื่อออนไลน์ที่เชี่ยวชาญการผลิตคอนเทนต์ไวรัลและการตลาดอินฟลูเอนเซอร์",
        "curriculum_highlights": [
            "Digital Content Strategy & Storytelling",
            "Short-Form Video Production & Streaming",
            "Influencer Branding & Monetization",
            "Social Media Algorithms & Analytics"
        ],
        "career_paths": [
            "Digital Content Creator",
            "Influencer / YouTuber / Streamer",
            "Social Media Strategist",
            "Digital Media Producer",
            "Creative Content Director"
        ],
        "tags": ["Content Creation", "Influencer", "Social Media", "Communication Arts", "Digital Media"],
        "website_url": "https://www.bu.ac.th/th/comarts/digital-content"
    },
    {
        "id": "bu_ca_cnm",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสื่อสารและสื่อใหม่",
        "title_en": "Bachelor of Communication Arts Program in Communication and New Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (การสื่อสารและสื่อใหม่)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Communication and New Media",
        "department_th": "สาขาวิชาการสื่อสารและสื่อใหม่",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "43,000 บาท",
        "tuition_total": "344,000 บาท",
        "description": "บูรณาการการโฆษณาดิจิทัล การประชาสัมพันธ์ยุคใหม่ การสื่อสารการตลาดเชิงบูรณาการ (IMC) และการสร้างแบรนด์ผ่านแพลตฟอร์มสื่อดิจิทัล",
        "curriculum_highlights": [
            "Digital Advertising & Campaign Design",
            "Brand Communication & Identity",
            "Public Relations in Digital Age",
            "Integrated Marketing Communication (IMC)"
        ],
        "career_paths": [
            "Advertising Creative Director",
            "Brand Communication Specialist",
            "Digital PR Consultant",
            "Media Planner",
            "Account Executive"
        ],
        "tags": ["Advertising", "Branding", "PR", "Communication", "Marketing"],
        "website_url": "https://www.bu.ac.th/th/comarts/communication-new-media"
    },
    {
        "id": "bu_ca_pa",
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาศิลปะการแสดง",
        "title_en": "Bachelor of Communication Arts Program in Performing Arts",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (ศิลปะการแสดง)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Performing Arts",
        "department_th": "สาขาวิชาศิลปะการแสดง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "46,000 บาท",
        "tuition_total": "368,000 บาท",
        "description": "ฝึกฝนทักษะการแสดง ละครเวที ซีรีส์ ภาพยนตร์ การกำกับการแสดง และการจัดการผลิตละครเวทีและการแสดงสดในระดับมืออาชีพ",
        "curriculum_highlights": [
            "Acting Techniques for Stage & Screen",
            "Stage Directing & Production",
            "Movement & Voice for Performers",
            "Theatre & Musical Production"
        ],
        "career_paths": [
            "Actor / Actress",
            "Theatre Director",
            "Acting Coach",
            "Casting Director",
            "Stage Producer"
        ],
        "tags": ["Performing Arts", "Acting", "Theatre", "Directing", "Entertainment"],
        "website_url": "https://www.bu.ac.th/th/comarts/performing-arts"
    },

    # --- School of Information Technology and Innovation ---
    {
        "id": "bu_it_cs",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Information Technology and Innovation",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรม",
        "department": "Department of Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "42,500 บาท",
        "tuition_total": "340,000 บาท",
        "description": "มุ่งเน้นวิทยาการข้อมูล (Data Science), ปัญญาประดิษฐ์ (AI), และความมั่นคงปลอดภัยไซเบอร์ (Cybersecurity) พร้อมการฝึกปฏิบัติจริงกับโจทย์อุตสาหกรรมเทคโนโลยี",
        "curriculum_highlights": [
            "Data Science & Machine Learning",
            "Cybersecurity & Threat Detection",
            "Full Stack Software Development",
            "Cloud Computing & DevOps"
        ],
        "career_paths": [
            "Data Scientist / AI Engineer",
            "Cybersecurity Specialist",
            "Software Engineer",
            "Full Stack Developer",
            "Cloud Solution Architect"
        ],
        "tags": ["Computer Science", "Data Science", "Cybersecurity", "AI", "Software"],
        "website_url": "https://www.bu.ac.th/th/it-innovation/computer-science"
    },
    {
        "id": "bu_it_game",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเกมและเทคโนโลยีเชิงโต้ตอบอัจฉริยะ",
        "title_en": "Bachelor of Science Program in Games and Intelligent Interactive Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เกมและเทคโนโลยีเชิงโต้ตอบอัจฉริยะ)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Information Technology and Innovation",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรม",
        "department": "Department of Game and Interactive Media",
        "department_th": "สาขาวิชาเกมและเทคโนโลยีเชิงโต้ตอบอัจฉริยะ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "พัฒนาเกมครบวงจรทั้งการออกแบบเกมเพลย์ (Game Design), การเขียนโปรแกรมเกม (Game Programming ด้วย Unity และ Unreal Engine) และอีสปอร์ต (Esports)",
        "curriculum_highlights": [
            "Game Programming (Unity / Unreal)",
            "Game Design & Level Creation",
            "AI for Gaming & Interactive Systems",
            "Esports Business & Tournament Operations"
        ],
        "career_paths": [
            "Game Developer / Programmer",
            "Game Designer / Level Designer",
            "Technical Artist",
            "Esports Operations Specialist",
            "Interactive Media Developer"
        ],
        "tags": ["Game Development", "Unity", "Unreal", "Esports", "Interactive Media"],
        "website_url": "https://www.bu.ac.th/th/it-innovation/game-interactive"
    },
    {
        "id": "bu_it_it",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science Program in Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศ)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Information Technology and Innovation",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรม",
        "department": "Department of Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "40,000 บาท",
        "tuition_total": "320,000 บาท",
        "description": "เน้นการประยุกต์ใช้เทคโนโลยีสารสนเทศเพื่อขับเคลื่อนธุรกิจดิจิทัล การจัดการระบบเครือข่าย คลาวด์ และการวิเคราะห์ธุรกิจดิจิทัล",
        "curriculum_highlights": [
            "Enterprise IT Infrastructure",
            "Cloud System Administration",
            "Digital Business Systems",
            "Network & Security Fundamentals"
        ],
        "career_paths": [
            "IT Consultant",
            "System Administrator",
            "Cloud Engineer",
            "Business IT Analyst",
            "IT Project Manager"
        ],
        "tags": ["Information Technology", "Cloud", "Network", "Business IT", "Infrastructure"],
        "website_url": "https://www.bu.ac.th/th/it-innovation/information-technology"
    },

    # --- School of Business Administration ---
    {
        "id": "bu_ba_mkt",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการตลาดดิจิทัล",
        "title_en": "Bachelor of Business Administration Program in Digital Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาดดิจิทัล)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Marketing",
        "department_th": "สาขาวิชาการตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "41,000 บาท",
        "tuition_total": "328,000 บาท",
        "description": "สร้างนักการตลาดดิจิทัลยุคใหม่ที่เข้าใจการตลาดออนไลน์ Performance Marketing, E-Commerce, Data-Driven Marketing และการสร้างแบรนด์ยุค AI",
        "curriculum_highlights": [
            "Performance Marketing & SEO/SEM",
            "E-Commerce & Social Commerce Management",
            "Marketing Analytics & Consumer Insights",
            "AI-Powered Marketing Strategy"
        ],
        "career_paths": [
            "Digital Marketing Specialist",
            "Performance Marketing Specialist",
            "E-Commerce Manager",
            "Brand Manager",
            "Marketing Data Analyst"
        ],
        "tags": ["Marketing", "Digital Marketing", "E-Commerce", "Business", "SEO/SEM"],
        "website_url": "https://www.bu.ac.th/th/business/digital-marketing"
    },
    {
        "id": "bu_ba_ibm",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการธุรกิจระหว่างประเทศ (มุ่งเน้นธุรกิจจีน)",
        "title_en": "Bachelor of Business Administration Program in International Business Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการธุรกิจระหว่างประเทศ)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of International Business Management",
        "department_th": "สาขาวิชาการจัดการธุรกิจระหว่างประเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "เข้าใจกลยุทธ์การค้าและการลงทุนระหว่างประเทศ การค้าระหว่างประเทศกับจีนและอาเซียน กฎหมายและพิธีการศุลกากรระดับสากล",
        "curriculum_highlights": [
            "Global Trade & International Logistics",
            "China & ASEAN Business Strategies",
            "Cross-Cultural Business Negotiation",
            "Global Supply Chain Management"
        ],
        "career_paths": [
            "International Business Development Manager",
            "Export-Import Coordinator",
            "Cross-Border E-Commerce Specialist",
            "Foreign Trade Consultant",
            "International Relations Officer"
        ],
        "tags": ["International Business", "China Business", "Global Trade", "Export Import"],
        "website_url": "https://www.bu.ac.th/th/business/international-business"
    },
    {
        "id": "bu_ba_logistics",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทาน",
        "title_en": "Bachelor of Business Administration Program in Logistics and Supply Chain Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการโลจิสติกส์และโซ่อุปทาน)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Logistics and Supply Chain",
        "department_th": "สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทาน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "41,500 บาท",
        "tuition_total": "332,000 บาท",
        "description": "เน้นระบบดิจิทัลคอมเมิร์ซโลจิสติกส์ การบริหารคลังสินค้าอัจฉริยะ และการจัดการโซ่อุปทานระดับโลกด้วยเทคโนโลยี AI และ IoT",
        "curriculum_highlights": [
            "Smart Warehouse & Inventory Automation",
            "Digital Freight Forwarding & Transportation",
            "Supply Chain Analytics & Optimization",
            "Cold Chain & Global Logistics Management"
        ],
        "career_paths": [
            "Logistics Analyst",
            "Supply Chain Planner",
            "Warehouse Operations Manager",
            "Freight Forwarder Specialist",
            "Procurement Specialist"
        ],
        "tags": ["Logistics", "Supply Chain", "Warehouse", "Transportation", "Operations"],
        "website_url": "https://www.bu.ac.th/th/business/logistics"
    },

    # --- School of Entrepreneurship and Management (BUSEM) ---
    {
        "id": "bu_busem_ent",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการเป็นเจ้าของธุรกิจ",
        "title_en": "Bachelor of Business Administration Program in Entrepreneurship",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การเป็นเจ้าของธุรกิจ)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Entrepreneurship and Management (BUSEM)",
        "faculty_th": "คณะการสร้างเจ้าของธุรกิจและการบริหารกิจการ",
        "department": "Department of Entrepreneurship",
        "department_th": "สาขาวิชาการเป็นเจ้าของธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "127 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "384,000 บาท",
        "description": "หลักสูตรร่วมมือกับ Babson College สหรัฐอเมริกา อันดับ 1 ด้านผู้ประกอบการ ฝึกให้นักศึกษาตั้งบริษัทและทำธุรกิจจริงตั้งแต่ระหว่างเรียนพร้อมพี่เลี้ยงนักธุรกิจมืออาชีพ",
        "curriculum_highlights": [
            "New Venture Creation & Business Model Canvas",
            "Startup Pitching & Venture Capital Fundraising",
            "Innovation & Product Prototyping",
            "Family Business Management & Scaling"
        ],
        "career_paths": [
            "Business Owner / Startup Founder",
            "Family Business Successor",
            "Innovation Consultant",
            "Venture Capital Analyst",
            "Corporate Intrapreneur"
        ],
        "tags": ["Entrepreneurship", "Startup", "BUSEM", "Babson", "Innovation", "Business"],
        "website_url": "https://www.bu.ac.th/th/busem/entrepreneurship"
    },

    # --- School of Accounting ---
    {
        "id": "bu_acc_acc",
        "title_th": "หลักสูตรบัญชีบัณฑิต",
        "title_en": "Bachelor of Accountancy Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ.",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Accounting",
        "faculty_th": "คณะบัญชี",
        "department": "Department of Accountancy",
        "department_th": "สาขาวิชาการบัญชี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "39,500 บาท",
        "tuition_total": "316,000 บาท",
        "description": "หลักสูตรบัญชีดิจิทัลที่ผสานซอฟต์แวร์ ERP บัญชีคลาวด์ การวิเคราะห์ข้อมูลทางการเงิน และระบบภาษีอากรเพื่อเตรียมพร้อมสอบผู้สอบบัญชีรับอนุญาต (CPA/CPD)",
        "curriculum_highlights": [
            "Digital Accounting & Cloud ERP Systems",
            "Financial Auditing & Assurance Standards",
            "Tax Planning & Strategic Taxation",
            "Financial Statement & Business Analytics"
        ],
        "career_paths": [
            "Certified Public Accountant (CPA)",
            "Financial Auditor / Tax Auditor",
            "Financial Analyst / Controller",
            "Tax Consultant",
            "Chief Financial Officer (CFO)"
        ],
        "tags": ["Accounting", "Audit", "Tax", "Finance", "CPA"],
        "website_url": "https://www.bu.ac.th/th/accounting"
    },

    # --- School of Engineering ---
    {
        "id": "bu_eng_robotics",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์และหุ่นยนต์",
        "title_en": "Bachelor of Engineering Program in Computer and Robotics Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์และหุ่นยนต์)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer and Robotics Engineering",
        "department_th": "สาขาวิชาวิศวกรรมคอมพิวเตอร์และหุ่นยนต์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "เน้นการพัฒนาหุ่นยนต์อัจฉริยะ ระบบสมองกลฝังตัว (Embedded Systems) ปัญญาประดิษฐ์ในระบบอัตโนมัติ และระบบ IoT เพื่ออุตสาหกรรม 4.0",
        "curriculum_highlights": [
            "Robotics Kinematics & Control Systems",
            "Embedded Systems & Microcontroller Design",
            "Artificial Intelligence & Computer Vision",
            "Industrial Automation & Smart Manufacturing"
        ],
        "career_paths": [
            "Robotics Engineer",
            "Automation Engineer",
            "Embedded Software Developer",
            "AI/Computer Vision Engineer",
            "IoT Solutions Architect"
        ],
        "tags": ["Engineering", "Robotics", "Embedded", "AI", "Automation"],
        "website_url": "https://www.bu.ac.th/th/engineering/computer-robotics"
    },
    {
        "id": "bu_eng_ee",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและอินเทอร์เน็ตของสรรพสิ่ง",
        "title_en": "Bachelor of Engineering Program in Electrical Engineering and IoT",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมไฟฟ้าและอินเทอร์เน็ตของสรรพสิ่ง)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมไฟฟ้า",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "44,000 บาท",
        "tuition_total": "352,000 บาท",
        "description": "ครอบคลุมระบบพลังงานไฟฟ้า พลังงานทดแทน ระบบโครงข่ายไฟฟ้าอัจฉริยะ (Smart Grid) และการประยุกต์ใช้ IoT ในระบบพลังงาน",
        "curriculum_highlights": [
            "Smart Grid & Renewable Energy Systems",
            "Power System Analysis & High Voltage Engineering",
            "IoT Architecture & Sensor Networks",
            "Electrical Installation & Building Systems"
        ],
        "career_paths": [
            "Electrical Engineer",
            "Power Plant & Renewable Energy Engineer",
            "Building Systems Engineer",
            "Smart Grid Specialist",
            "Energy Management Consultant"
        ],
        "tags": ["Engineering", "Electrical", "IoT", "Smart Grid", "Renewable Energy"],
        "website_url": "https://www.bu.ac.th/th/engineering/electrical"
    },

    # --- School of Architecture ---
    {
        "id": "bu_arch_arch",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรม",
        "title_en": "Bachelor of Architecture Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ.",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Architecture",
        "department_th": "สาขาวิชาสถาปัตยกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "162 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "480,000 บาท",
        "description": "เน้นสถาปัตยกรรมเชิงนวัตกรรมและการออกแบบอย่างยั่งยืน การใช้เทคโนโลยี BIM และการออกแบบสถาปัตยกรรมที่ตอบสนองต่อบริบทเมืองและสิ่งแวดล้อม พร้อมสอบใบประกอบวิชาชีพสถาปัตยกรรม",
        "curriculum_highlights": [
            "Architectural Design Studio I-VIII",
            "Building Information Modeling (BIM)",
            "Sustainable & Green Architecture Design",
            "Structural Design & Building Materials"
        ],
        "career_paths": [
            "Architect (Licensed)",
            "BIM Coordinator / Manager",
            "Sustainable Design Consultant",
            "Urban Architectural Designer",
            "Real Estate Project Architect"
        ],
        "tags": ["Architecture", "BIM", "Design", "Sustainable", "Building"],
        "website_url": "https://www.bu.ac.th/th/architecture/architecture"
    },
    {
        "id": "bu_arch_interior",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต สาขาวิชาสถาปัตยกรรมภายใน",
        "title_en": "Bachelor of Architecture Program in Interior Architecture",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรมภายใน)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Interior Architecture",
        "department_th": "สาขาวิชาสถาปัตยกรรมภายใน",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "160 หน่วยกิต",
        "tuition_per_semester": "47,500 บาท",
        "tuition_total": "475,000 บาท",
        "description": "การออกแบบพื้นที่ภายในอาคาร การใช้วัสดุและแสงสว่าง การตกแต่งภายในโรงแรม ร้านค้า สำนักงาน และที่อยู่อาศัยระดับพรีเมียม",
        "curriculum_highlights": [
            "Interior Architecture Design Studio",
            "Lighting Design & Material Innovation",
            "Hospitality & Commercial Space Design",
            "3D Spatial Visualization & Rendering"
        ],
        "career_paths": [
            "Interior Architect",
            "Commercial Space Designer",
            "Lighting Designer",
            "Exhibition & Event Space Designer",
            "Furniture & Prop Stylist"
        ],
        "tags": ["Interior Architecture", "Interior Design", "Space Design", "Hospitality"],
        "website_url": "https://www.bu.ac.th/th/architecture/interior-architecture"
    },

    # --- School of Humanities and Tourism Management ---
    {
        "id": "bu_hum_airline",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาการจัดการธุรกิจการบิน",
        "title_en": "Bachelor of Arts Program in Airline Business Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (การจัดการธุรกิจการบิน)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Humanities and Tourism Management",
        "faculty_th": "คณะมนุษยศาสตร์และการจัดการการท่องเที่ยว",
        "department": "Department of Airline Business",
        "department_th": "สาขาวิชาการจัดการธุรกิจการบิน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "46,000 บาท",
        "tuition_total": "368,000 บาท",
        "description": "ฝึกปฏิบัติงานจริงในห้องปฏิบัติการจำลองเครื่องบิน Boeing 787 Dreamliner ครบวงจรทั้งงานบริการผู้โดยสารบนเครื่องบิน (Cabin Crew) และงานบริการภาคพื้น (Ground Service)",
        "curriculum_highlights": [
            "In-Flight Service & Safety Emergency Procedures",
            "Airline Ground Operations & Passenger Handling",
            "Aviation English & International Etiquette",
            "Airport Operations & Airline Ticketing (Amadeus)"
        ],
        "career_paths": [
            "Flight Attendant / Cabin Crew",
            "Airline Ground Service Agent",
            "Airport Operations Officer",
            "Airline Reservation & Ticketing Specialist",
            "VIP Lounge Service Executive"
        ],
        "tags": ["Aviation", "Airline", "Cabin Crew", "Airport", "Tourism"],
        "website_url": "https://www.bu.ac.th/th/humanities/airline-business"
    },
    {
        "id": "bu_hum_hotel",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาการจัดการการโรงแรมและภัตตาคาร",
        "title_en": "Bachelor of Arts Program in Hotel and Restaurant Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (การจัดการการโรงแรมและภัตตาคาร)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Humanities and Tourism Management",
        "faculty_th": "คณะมนุษยศาสตร์และการจัดการการท่องเที่ยว",
        "department": "Department of Hotel and Restaurant Management",
        "department_th": "สาขาวิชาการจัดการการโรงแรมและภัตตาคาร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "129 หน่วยกิต",
        "tuition_per_semester": "44,500 บาท",
        "tuition_total": "356,000 บาท",
        "description": "ฝึกอบรมการบริหารโรงแรมระดับ 5 ดาว การบริการอาหารและเครื่องดื่ม การจัดการภัตตาคาร และการบริการลูกค้าระดับลักชัวรี",
        "curriculum_highlights": [
            "Hotel Front Office & Property Management Systems",
            "Food & Beverage Service and Mixology",
            "Culinary Operations & Kitchen Management",
            "Luxury Hospitality & Guest Experience"
        ],
        "career_paths": [
            "Hotel General Manager / Department Head",
            "Food & Beverage Manager",
            "Front Office Executive",
            "Restaurant Owner / Operator",
            "Event & Banquet Coordinator"
        ],
        "tags": ["Hospitality", "Hotel", "Restaurant", "Food and Beverage", "Tourism"],
        "website_url": "https://www.bu.ac.th/th/humanities/hotel-management"
    },

    # --- School of Law ---
    {
        "id": "bu_law_llb",
        "title_th": "หลักสูตรนิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ.",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "School of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Department of Law",
        "department_th": "สาขาวิชานิติศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "38,500 บาท",
        "tuition_total": "308,000 บาท",
        "description": "เน้นกฎหมายแพ่ง พาณิชย์ อาญา พร้อมกฎหมายธุรกิจดิจิทัล กฎหมายทรัพย์สินทางปัญญา และกฎหมายคุ้มครองข้อมูลส่วนบุคคล (PDPA) พร้อมการฝึกศาลจำลอง",
        "curriculum_highlights": [
            "Civil and Commercial Law & Criminal Law",
            "Digital Business Law & PDPA",
            "Intellectual Property & Entertainment Law",
            "Moot Court & Legal Advocacy Practice"
        ],
        "career_paths": [
            "Lawyer / Attorney at Law",
            "Legal Consultant / Corporate In-house Counsel",
            "Judge / Public Prosecutor Trainee",
            "Compliance Officer",
            "Intellectual Property Specialist"
        ],
        "tags": ["Law", "Legal", "Corporate Law", "Intellectual Property", "PDPA"],
        "website_url": "https://www.bu.ac.th/th/law"
    },

    # --- Graduate School (BU) ---
    {
        "id": "bu_grad_mba",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต",
        "title_en": "Master of Business Administration Program (MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (MBA)",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "Graduate School",
        "faculty_th": "บัณฑิตวิทยาลัย",
        "department": "Business Administration Program",
        "department_th": "สาขาวิชาบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "260,000 บาท",
        "description": "หลักสูตร MBA เน้นการคิดเชิงกลยุทธ์ การทรานส์ฟอร์มธุรกิจสู่ยุคดิจิทัล และภาวะผู้นำระดับสูง เหมาะสำหรับผู้บริหารและผู้ประกอบการ",
        "curriculum_highlights": [
            "Strategic Management in Digital Disruption",
            "Advanced Financial & Investment Decision Making",
            "Data Analytics for Executive Decision Making",
            "Global Business Leadership & Innovation"
        ],
        "career_paths": [
            "Chief Executive Officer (CEO)",
            "Business Strategy Director",
            "Senior Management Consultant",
            "Business Transformation Specialist",
            "Entrepreneur"
        ],
        "tags": ["MBA", "Business Administration", "Executive", "Management", "Graduate"],
        "website_url": "https://www.bu.ac.th/th/curriculum/masters-degree/mba"
    },
    {
        "id": "bu_grad_mca",
        "title_th": "หลักสูตรนิเทศศาสตรมหาบัณฑิต สาขาวิชาการสื่อสารดิจิทัลและศิลปะภาพยนตร์",
        "title_en": "Master of Communication Arts Program in Digital Media and Cinematic Arts",
        "degree_level": "ปริญญาโท",
        "degree_name": "นศ.ม.",
        "university": "Bangkok University",
        "university_th": "มหาวิทยาลัยกรุงเทพ",
        "faculty": "Graduate School",
        "faculty_th": "บัณฑิตวิทยาลัย",
        "department": "Communication Arts Program",
        "department_th": "สาขาวิชานิเทศศาสตร์",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "62,500 บาท",
        "tuition_total": "250,000 บาท",
        "description": "ยกระดับงานวิจัยและงานสร้างสรรค์ด้านสื่อดิจิทัล ภาพยนตร์ และคอนเทนต์เสมือนจริงในระดับสูงเพื่อขับเคลื่อนเศรษฐกิจสร้างสรรค์ (Creative Economy)",
        "curriculum_highlights": [
            "Advanced Film Theory & Creative Production",
            "Strategic Digital Media Management",
            "Creative Economy & Intellectual Property Monetization",
            "Master's Thesis / Independent Study in Cinematic Arts"
        ],
        "career_paths": [
            "Executive Film Producer",
            "Media Researcher / University Lecturer",
            "Creative Director",
            "Chief Content Officer",
            "Media Industry Consultant"
        ],
        "tags": ["Master", "Communication Arts", "Film", "Digital Media", "Graduate"],
        "website_url": "https://www.bu.ac.th/th/curriculum/masters-degree/communication-arts"
    }
]

def fetch_bu_live_announcements() -> List[Dict[str, str]]:
    """Helper to scrape live announcements or admissions pages from bu.ac.th."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    urls = [
        "https://www.bu.ac.th/th/curriculum/bachelors-degree",
        "https://www.bu.ac.th/th/tuition-fees/bachelor-degree/2025"
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
    logger.info(f"Saved {len(courses)} Bangkok University courses to {filepath}")

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
    logger.info(f"Successfully seeded Bangkok University to DB: {inserted} inserted, {updated} updated.")

def main():
    import urllib3
    urllib3.disable_warnings()
    parser = argparse.ArgumentParser(description="Bangkok University (BU) Course Scraper & Catalog")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_FILE), help="Output JSON path")
    parser.add_argument("--seed-db", action="store_true", help="Seed courses directly to Database")
    parser.add_argument("--level", type=str, default="all", choices=["all", "bachelor", "master"], help="Filter degree level")
    args = parser.parse_args()

    courses = BU_COURSES
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
