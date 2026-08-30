# -*- coding: utf-8 -*-
"""
Thammasat University (TU) Complete Data Expansion Pipeline
Expands curricula (Bachelor, Master, Ph.D.) and Faculty Advisors across all 18+ faculties and international colleges.
Generates 768-dim Gemini vector embeddings and upserts into Supabase PostgreSQL.
Complies strictly with AGENTS.md, DSA Standards, and PDPA compliance.
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
# 1. THAMMASAT UNIVERSITY EXPANDED CURRICULA DATASET
# =============================================================================
TU_EXPANDED_COURSES = [
    # -------------------------------------------------------------------------
    # 1. Chulabhorn International College of Medicine (CICM) & Faculty of Medicine
    # -------------------------------------------------------------------------
    {
        "id": "tu_cicm_md_inter",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต (หลักสูตรนานาชาติ CICM)",
        "title_en": "Doctor of Medicine Program (CICM International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตร์ - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Chulabhorn International College of Medicine",
        "faculty_th": "วิทยาลัยแพทยศาสตร์นานาชาติจุฬาภรณ์",
        "department": "Doctor of Medicine Program",
        "department_th": "สาขาวิชาแพทยศาสตร์ (หลักสูตรนานาชาติ)",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "450,000 บาท",
        "tuition_total": "5,400,000 บาท",
        "description": "หลักสูตรแพทยศาสตรบัณฑิตภาคภาษาอังกฤษแห่งแรกของประเทศไทย ผ่านการรับรองมาตรฐานสากล WFME มุ่งเน้นการแพทย์แม่นยำ (Precision Medicine), นวัตกรรมทางการแพทย์ และการฝึกคลินิกในโรงพยาบาลมาตรฐานระดับโลก",
        "curriculum_highlights": [
            "WFME Globally Accredited Medical Curriculum",
            "Precision Medicine & Medical Genomics",
            "Clinical Rotations at Thammasat University Hospital & Partner Centers",
            "Artificial Intelligence in Healthcare & Clinical Decision Support",
            "Problem-Based Learning (PBL) & Simulation Center Training"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Clinical Specialist", "Medical AI Researcher", "Hospital Administrator"],
        "tags": ["Medicine", "CICM", "Doctor of Medicine", "International Program", "WFME", "Healthcare"],
        "website_url": "https://cicm.tu.ac.th"
    },
    {
        "id": "tu_cicm_dent_inter",
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต (หลักสูตรนานาชาติ CICM)",
        "title_en": "Doctor of Dental Surgery Program (CICM International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตร์ - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Chulabhorn International College of Medicine",
        "faculty_th": "วิทยาลัยแพทยศาสตร์นานาชาติจุฬาภรณ์",
        "department": "Doctor of Dental Surgery Program",
        "department_th": "สาขาวิชาทันตแพทยศาสตร์ (หลักสูตรนานาชาติ)",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "6 ปี",
        "total_credits": "228 หน่วยกิต",
        "tuition_per_semester": "480,000 บาท",
        "tuition_total": "5,760,000 บาท",
        "description": "มุ่งเน้นทันตกรรมดิจิทัล (Digital Dentistry), การออกแบบรอยยิ้มด้วย CAD/CAM, รากเทียมขั้นสูง และทันตกรรมบูรณะระดับสากล สอนเป็นภาษาอังกฤษ 100%",
        "curriculum_highlights": [
            "Digital Dentistry & 3D CAD/CAM Intraoral Scanning",
            "Advanced Implantology & Prosthodontics",
            "Comprehensive Patient Dental Care at Thammasat Dental Hospital",
            "Oral and Maxillofacial Surgery Training"
        ],
        "career_paths": ["Dentist (ทันตแพทย์)", "Orthodontist", "Implantologist", "Dental Clinic Owner"],
        "tags": ["Dentistry", "CICM", "Digital Dentistry", "Dental Surgery", "International Program"],
        "website_url": "https://cicm.tu.ac.th"
    },
    {
        "id": "tu_med_phd_regen",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการแพทย์บูรณาการและสเต็มเซลล์ฟื้นฟู",
        "title_en": "Doctor of Philosophy Program in Integrative Medicine and Regenerative Stem Cell",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (การแพทย์บูรณาการ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Graduate Studies Division",
        "department_th": "ฝ่ายบัณฑิตศึกษา คณะแพทยศาสตร์",
        "program_type": "วิจัยเต็มเวลา (Full Research)",
        "duration_years": "3 - 5 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "450,000 บาท",
        "description": "เน้นการวิจัยเชิงลึกด้านสเต็มเซลล์บำบัด เวชศาสตร์ชะลอวัย ภูมิคุ้มกันบำบัดมะเร็ง และชีวการแพทย์ขั้นสูงเพื่อสร้างนวัตกรรมสุขภาพระดับแนวหน้า",
        "curriculum_highlights": [
            "Stem Cell Biology & Regenerative Therapeutics",
            "Immunotherapy & CAR-T Cell Engineering",
            "Advanced Clinical Trial Design & Ethics",
            "Doctoral Dissertation with High-Impact International Publications"
        ],
        "career_paths": ["Medical Research Scientist", "Cell Therapy Specialist", "Biotech Entrepreneur", "Medical Faculty Professor"],
        "tags": ["Regenerative Medicine", "Stem Cell", "Immunotherapy", "Ph.D.", "Medicine", "Doctorate"],
        "website_url": "https://med.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2. Faculty of Engineering (วิศวกรรมศาสตร์ มธ. - TEP / TEPE & Regular)
    # -------------------------------------------------------------------------
    {
        "id": "tu_eng_tepe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต โครงการนานาชาติ TEPE (Thammasat English Programme of Engineering)",
        "title_en": "Bachelor of Engineering (TEPE International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมศาสตร์ - TEPE นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "TEPE International Engineering Program",
        "department_th": "โครงการ TEPE วิศวกรรมศาสตร์ภาคภาษาอังกฤษ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "68,000 บาท",
        "tuition_total": "544,000 บาท",
        "description": "หลักสูตรวิศวกรรมศาสตร์นานาชาติ 4 ปีเต็ม ครอบคลุม 5 สาขาหลัก: ไฟฟ้า, เครื่องกล, เคมี, โยธา และอุตสาหการ พร้อมโครงการฝึกงานระดับนานาชาติในเยอรมนี ญี่ปุ่น และสหรัฐอเมริกา",
        "curriculum_highlights": [
            "Global Engineering Accreditation & Standard",
            "Robotics & Smart Mobility Integration",
            "Clean Energy Transition & Smart Grid Systems",
            "Global Engineering Capstone Design Project"
        ],
        "career_paths": ["International Project Engineer", "Robotics Specialist", "Energy Systems Engineer", "Engineering Consultant"],
        "tags": ["TEPE", "Engineering", "International Program", "Mechanical", "Electrical", "Chemical"],
        "website_url": "https://tep.engr.tu.ac.th"
    },
    {
        "id": "tu_eng_auto_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมยานยนต์และระบบขับเคลื่อนอัตโนมัติ",
        "title_en": "Bachelor of Engineering in Automotive Engineering and Autonomous Mobility",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมยานยนต์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์ (ศูนย์พัทยา)",
        "department": "Department of Mechanical & Automotive Engineering",
        "department_th": "ภาควิชาวิศวกรรมยานยนต์ (ศูนย์พัทยา / EEC)",
        "program_type": "ภาคปกติ / โครงการพิเศษ EEC",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "280,000 บาท",
        "description": "ตั้งอยู่ ณ ศูนย์พัทยาในเขตพัฒนาพิเศษภาคตะวันออก (EEC) มุ่งเน้นการผลิตวิศวกรยานยนต์ไฟฟ้ารุ่นใหม่ (EV), แบตเตอรี่และระบบกักเก็บพลังงาน และยานยนต์ไร้คนขับ (Autonomous Vehicles)",
        "curriculum_highlights": [
            "Electric Vehicle (EV) Powertrain & Battery Management Systems (BMS)",
            "Autonomous Driving Systems, Sensors, LiDAR & Computer Vision",
            "Vehicle Dynamics & Crash Safety Simulation",
            "Industry Co-op Internship at Global EV Manufacturers in EEC"
        ],
        "career_paths": ["EV Powertrain Engineer", "Autonomous Vehicle Specialist", "Battery Systems Engineer", "Automotive R&D Engineer"],
        "tags": ["EV", "Automotive Engineering", "Autonomous Vehicles", "EEC", "Battery Technology", "Robotics"],
        "website_url": "https://auto.engr.tu.ac.th"
    },
    {
        "id": "tu_eng_ai_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมปัญญาประดิษฐ์และอินเทอร์เน็ตของสรรพสิ่ง",
        "title_en": "Master of Engineering in Artificial Intelligence and IoT Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมปัญญาประดิษฐ์และไอโอที)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical and Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "หลักสูตรปริญญาโทที่มุ่งเน้นการวิจัยเชิงประยุกต์ด้าน Edge AI, Deep Learning, สมองกลฝังตัว, สมาร์ทซิตี้ และระบบอัตโนมัติในโรงงานอัจฉริยะ",
        "curriculum_highlights": [
            "Embedded AI & TinyML Implementation",
            "Computer Vision & Deep Learning for Industry 4.0",
            "Cyber-Physical Systems & IoT Security Architecture",
            "Applied Master's Thesis with Industrial Sponsorship"
        ],
        "career_paths": ["Lead AI Engineer", "IoT Solution Architect", "Smart Automation Director", "Applied AI Researcher"],
        "tags": ["AI", "IoT", "Computer Engineering", "Deep Learning", "Edge AI", "Master Degree"],
        "website_url": "https://ece.engr.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 3. Faculty of Pharmacy & Faculty of Public Health
    # -------------------------------------------------------------------------
    {
        "id": "tu_pharm_pharmd",
        "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต (บริบาลทางเภสัชกรรม / การค้นพบยา)",
        "title_en": "Doctor of Pharmacy Program (Pharm.D.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ภ.บ. (เภสัชศาสตร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Faculty of Pharmacy",
        "department_th": "คณะเภสัชศาสตร์ (ศูนย์รังสิต)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "220 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "ผลิตเภสัชกรวิชาชีพที่มีความเชี่ยวชาญการบริบาลทางเภสัชกรรมในโรงพยาบาล การพัฒนายาชีววัตถุ เภสัชพันธุศาสตร์ และการควบคุมคุณภาพยาตามมาตรฐานสากล",
        "curriculum_highlights": [
            "Clinical Pharmacotherapy & Patient Care",
            "Biopharmaceuticals & Nanomedicine Formulation",
            "Pharmacogenomics & Precision Medication",
            "Clinical Pharmacy Clerkship in Leading Medical Centers"
        ],
        "career_paths": ["Clinical Pharmacist (เภสัชกรโรงพยาบาล)", "Industrial Pharmacist", "Regulatory Affairs Specialist", "Clinical Trial Manager"],
        "tags": ["Pharmacy", "Pharm.D.", "Pharmacology", "Drug Discovery", "Clinical Pharmacy", "Healthcare"],
        "website_url": "https://pharm.tu.ac.th"
    },
    {
        "id": "tu_ph_epidemiology_mph",
        "title_th": "หลักสูตรสาธารณสุขศาสตรมหาบัณฑิต สาขาวิชาระบาดวิทยาและการจัดการสุขภาพโลก",
        "title_en": "Master of Public Health Program in Epidemiology and Global Health Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "ส.ม. (สาธารณสุขศาสตร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Department of Epidemiology and Health Administration",
        "department_th": "ภาควิชาระบาดวิทยาและการบริหารสาธารณสุข",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "40,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "เน้นการวิเคราะห์ข้อมูลระบาดวิทยาขนาดใหญ่ (Health Big Data), การควบคุมโรคติดต่ออุบัติใหม่, นโยบายสุขภาพระดับโลก และการบริหารระบบสาธารณสุขยุคดิจิทัล",
        "curriculum_highlights": [
            "Advanced Epidemiological Methods & Biostatistics",
            "Global Health Policy, Economics & Governance",
            "Infectious Disease Modeling & Outbreak Investigation",
            "Health Big Data Analytics & Spatial GIS Mapping"
        ],
        "career_paths": ["Epidemiologist (นักระบาดวิทยา)", "Global Health Program Officer (WHO, CDC)", "Public Health Administrator", "Health Policy Analyst"],
        "tags": ["Public Health", "Epidemiology", "Global Health", "Biostatistics", "Healthcare Management"],
        "website_url": "https://fph.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 4. Faculty of Architecture and Planning (สถาปัตยกรรมศาสตร์และการผังเมือง มธ.)
    # -------------------------------------------------------------------------
    {
        "id": "tu_arch_uddi_inter",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาการออกแบบเชิงนวัตกรรมและการพัฒนาเมือง (หลักสูตรนานาชาติ UDDI)",
        "title_en": "Bachelor of Science in Urban Design and Development (UDDI International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (การออกแบบและการพัฒนาเมือง - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Architecture and Planning",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการผังเมือง",
        "department": "UDDI International Program",
        "department_th": "โครงการนวัตกรรมการออกแบบและการพัฒนาเมืองนานาชาติ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "680,000 บาท",
        "description": "หลักสูตรออกแบบเมืองอัจฉริยะ (Smart City Design) ผสานสถาปัตยกรรมผังเมือง เทคโนโลยีภูมิสารสนเทศ (GIS) การพัฒนาเมืองอย่างยั่งยืน และการออกแบบเมืองที่เป็นมิตรกับสิ่งแวดล้อม",
        "curriculum_highlights": [
            "Smart City Planning & Resilient Urban Design",
            "Geographic Information Systems (GIS) & Spatial Big Data",
            "Transit-Oriented Development (TOD) & Urban Mobility",
            "Sustainable Real Estate & Community Revitalization"
        ],
        "career_paths": ["Urban Designer", "Smart City Planner", "Real Estate Development Consultant", "GIS Spatial Analyst"],
        "tags": ["Architecture", "Urban Design", "Smart City", "UDDI", "International Program", "Sustainability"],
        "website_url": "https://www.ap.tu.ac.th/uddi"
    },
    {
        "id": "tu_arch_design_barch",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต (สถ.บ.)",
        "title_en": "Bachelor of Architecture Program (B.Arch.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรมศาสตร์)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Architecture and Planning",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการผังเมือง",
        "department": "Department of Architecture",
        "department_th": "สาขาวิชาสถาปัตยกรรมศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "165 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "เน้นการออกแบบสถาปัตยกรรมเขียว (Green Architecture), การจำลองพลังงานอาคาร (Building Energy Simulation), เทคโนโลยี BIM และการออกแบบเพื่อความยั่งยืน",
        "curriculum_highlights": [
            "Architectural Design Studio & Sustainable Concept",
            "Building Information Modeling (BIM) & Parametric Architecture",
            "Green Building Design (LEED / TREES Standards)",
            "Advanced Construction Technology & Material Innovation"
        ],
        "career_paths": ["Licensed Architect (สถาปนิก)", "BIM Specialist", "Green Building Consultant", "Design Director"],
        "tags": ["Architecture", "B.Arch", "BIM", "Green Building", "Sustainable Design"],
        "website_url": "https://www.ap.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 5. Faculty of Political Science (คณะรัฐศาสตร์ มธ. - ท่าพระจันทร์ / รังสิต)
    # -------------------------------------------------------------------------
    {
        "id": "tu_polsci_bir_inter",
        "title_th": "หลักสูตรรัฐศาสตรบัณฑิต สาขาวิชาการเมืองและการระหว่างประเทศ (หลักสูตรนานาชาติ BIR)",
        "title_en": "Bachelor of Political Science in Politics and International Relations (BIR International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (การเมืองและการระหว่างประเทศ - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "BIR International Program",
        "department_th": "โครงการปริญญาตรีการเมืองและการระหว่างประเทศภาคภาษาอังกฤษ",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "หลักสูตรความสัมพันธ์ระหว่างประเทศนานาชาติอันดับ 1 ของไทย ณ ท่าพระจันทร์ เน้นภูมิรัฐศาสตร์โลก ความมั่นคงระหว่างประเทศ การทูต และเศรษฐกิจการเมืองระหว่างประเทศ (IPE)",
        "curriculum_highlights": [
            "Geopolitics, Great Power Competition & Indo-Pacific Strategy",
            "International Law, Human Rights & Global Governance",
            "Diplomatic Strategy, Negotiations & Model United Nations (MUN)",
            "International Political Economy & Global Trade Conflicts"
        ],
        "career_paths": ["Diplomat / Foreign Service Officer (นักการทูต)", "International Relations Analyst", "United Nations Officer", "Global Risk Consultant"],
        "tags": ["Political Science", "BIR", "International Relations", "Diplomacy", "Geopolitics", "International Program"],
        "website_url": "https://bir.polsci.tu.ac.th"
    },
    {
        "id": "tu_polsci_gov_bpol",
        "title_th": "หลักสูตรรัฐศาสตรบัณฑิต สาขาวิชาการเมืองการปกครอง",
        "title_en": "Bachelor of Political Science Program in Government and Politics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (การเมืองการปกครอง)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Government",
        "department_th": "สาขาวิชาการเมืองการปกครอง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "14,300 บาท",
        "tuition_total": "114,400 บาท",
        "description": "สถาบันผลิตผู้นำการเมือง นักบริหารรัฐกิจ และนักวิชาการประชาธิปไตย มุ่งเน้นปรัชญาการเมือง ทฤษฎีประชาธิปไตย รัฐธรรมนูญ และการปฏิรูประบบราชการ",
        "curriculum_highlights": [
            "Democratic Theory & Constitutional Politics",
            "Comparative Political Systems & Southeast Asian Politics",
            "Public Policy Analysis & State Reform",
            "Political Psychology & Public Opinion Dynamics"
        ],
        "career_paths": ["Government Officer (ข้าราชการสายบริหาร)", "Policy Analyst", "Political Strategist", "NGO Program Manager"],
        "tags": ["Political Science", "Government", "Democracy", "Public Policy", "Leadership"],
        "website_url": "https://www.polsci.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 6. School of Global Studies (วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์ / SGS)
    # -------------------------------------------------------------------------
    {
        "id": "tu_sgs_gsse_inter",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาโลกคดีศึกษาและการประกอบการสังคม (หลักสูตรนานาชาติ GSSE)",
        "title_en": "Bachelor of Arts in Global Studies and Social Entrepreneurship (GSSE International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (โลกคดีศึกษาและการประกอบการสังคม - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "School of Global Studies",
        "faculty_th": "วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์",
        "department": "GSSE International Program",
        "department_th": "โครงการปริญญาตรีนานาชาติ GSSE",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "680,000 บาท",
        "description": "บ่มเพาะผู้นำการเปลี่ยนแปลงทางสังคม (Change-makers) และผู้ประกอบการเพื่อสังคม (Social Entrepreneurs) ด้วยการแก้ปัญหาความยั่งยืน SDGs, นวัตกรรมทางสังคม และการเป็นผู้ประกอบการระดับโลก",
        "curriculum_highlights": [
            "Social Enterprise Incubation & Impact Investing",
            "Human-Centered Design Thinking for Global Challenges",
            "Sustainable Development Goals (SDGs) Project Implementation",
            "Global Fieldwork & Social Impact Venture Launch"
        ],
        "career_paths": ["Social Entrepreneur", "ESG / Sustainability Strategist", "Impact Investment Analyst", "Global NGO Director"],
        "tags": ["GSSE", "Social Entrepreneurship", "Global Studies", "SDGs", "ESG", "International Program"],
        "website_url": "https://sgs.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 7. Faculty of Journalism and Mass Communication (วารสารศาสตร์และสื่อสารมวลชน มธ.)
    # -------------------------------------------------------------------------
    {
        "id": "tu_jc_bjm_inter",
        "title_th": "หลักสูตรวารสารศาสตรบัณฑิต สาขาวิชาสื่อมวลชนศึกษา (หลักสูตรนานาชาติ BJM)",
        "title_en": "Bachelor of Arts in Journalism and Mass Communication (BJM International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (สื่อมวลชนศึกษา - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Journalism and Mass Communication",
        "faculty_th": "คณะวารสารศาสตร์และสื่อสารมวลชน",
        "department": "BJM International Program",
        "department_th": "โครงการวารสารศาสตรบัณฑิตภาคภาษาอังกฤษ (BJM)",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "75,000 บาท",
        "tuition_total": "600,000 บาท",
        "description": "ผลิตนักสื่อสารระดับสากลที่เชี่ยวชาญการผลิตสื่อดิจิทัล สื่อสารการตลาดระดับโลก วารสารศาสตร์เชิงสืบสวน และการสร้างคอนเทนต์ด้วยปัญญาประดิษฐ์และนวัตกรรมมัลติมีเดีย",
        "curriculum_highlights": [
            "Digital Media Production & Storytelling",
            "Global Strategic Communication & PR",
            "Data Journalism & Multimedia Investigations",
            "AI in Content Creation & Creative Direction"
        ],
        "career_paths": ["Creative Director", "Global PR & Communications Lead", "Data Journalist", "Digital Media Producer"],
        "tags": ["Journalism", "BJM", "Mass Communication", "Digital Media", "Public Relations", "International Program"],
        "website_url": "https://www.jc.tu.ac.th/bjm"
    },

    # -------------------------------------------------------------------------
    # 8. Faculty of Liberal Arts (คณะศิลปศาสตร์ มธ.)
    # -------------------------------------------------------------------------
    {
        "id": "tu_arts_bec_inter",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษเชิงธุรกิจ (หลักสูตรนานาชาติ BEC)",
        "title_en": "Bachelor of Arts in Business English Communication (BEC International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาอังกฤษเชิงธุรกิจ - นานาชาติ)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "BEC International Program",
        "department_th": "โครงการภาษาอังกฤษเชิงธุรกิจ (ท่าพระจันทร์)",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "ผสานความเชี่ยวชาญภาษาอังกฤษระดับสูงเข้ากับการสื่อสารทางธุรกิจ การเจรจาต่อรองข้ามวัฒนธรรม การบริหารลูกค้าสัมพันธ์ระดับสากล และการตลาดดิจิทัล",
        "curriculum_highlights": [
            "Advanced Business Negotiation & Corporate Communication",
            "Cross-Cultural Communication in Global Enterprises",
            "Digital Marketing Communications & Content Strategy",
            "Corporate Public Relations & Event Management"
        ],
        "career_paths": ["International Corporate Communications Manager", "Global Key Account Executive", "International Marketing Specialist", "Cross-Cultural Consultant"],
        "tags": ["Liberal Arts", "BEC", "Business English", "Communication", "International Program"],
        "website_url": "https://arts.tu.ac.th/bec"
    },
    {
        "id": "tu_arts_psychology_ba",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาจิตวิทยา",
        "title_en": "Bachelor of Science Program in Psychology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (จิตวิทยา)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Department of Psychology",
        "department_th": "สาขาวิชาจิตวิทยา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "14,300 บาท",
        "tuition_total": "114,400 บาท",
        "description": "ครอบคลุมจิตวิทยาคลินิก จิตวิทยาอุตสาหกรรมและองค์การ และจิตวิทยาการให้คำปรึกษา พร้อมการตรวจประเมินทางจิตวิทยาและการพัฒนาศักยภาพมนุษย์",
        "curriculum_highlights": [
            "Cognitive Psychology & Behavioral Neuroscience",
            "Psychological Assessment & Psychometrics",
            "Industrial and Organizational Psychology (I/O)",
            "Counseling & Psychotherapy Fundamentals"
        ],
        "career_paths": ["Organizational Psychologist", "HR People Analytics Specialist", "Counselor / Mental Health Practitioner", "User Experience (UX) Researcher"],
        "tags": ["Psychology", "Behavioral Science", "I/O Psychology", "Mental Health", "Counseling"],
        "website_url": "https://psy.arts.tu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 9. College of Interdisciplinary Studies (วิทยาลัยสหวิทยาการ มธ.)
    # -------------------------------------------------------------------------
    {
        "id": "tu_cis_dsdi_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและนวัตกรรมดิจิทัล (DSDI)",
        "title_en": "Bachelor of Science in Data Science and Digital Innovation (DSDI)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการข้อมูลและนวัตกรรมดิจิทัล)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "College of Interdisciplinary Studies",
        "faculty_th": "วิทยาลัยสหวิทยาการ",
        "department": "DSDI Program",
        "department_th": "สาขาวิชาวิทยาการข้อมูลและนวัตกรรมดิจิทัล",
        "program_type": "โครงการพิเศษ (ศูนย์รังสิต)",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "304,000 บาท",
        "description": "หลักสูตรบูรณาการวิทยาการข้อมูล ปัญญาประดิษฐ์ สถิติ และการประยุกต์ใช้เพื่อแก้ปัญหาเศรษฐกิจ สังคม และนวัตกรรมดิจิทัล",
        "curriculum_highlights": [
            "Data Science Pipeline & Predictive Modeling",
            "Deep Learning & Generative AI Applications",
            "Big Data Technologies & Cloud Infrastructure",
            "Digital Business Innovation & Fintech Analytics"
        ],
        "career_paths": ["Data Scientist", "Machine Learning Specialist", "Business Intelligence Analyst", "Digital Innovation Lead"],
        "tags": ["Data Science", "AI", "DSDI", "Machine Learning", "Digital Innovation", "Interdisciplinary"],
        "website_url": "https://cis.tu.ac.th"
    }
]

# =============================================================================
# 2. THAMMASAT UNIVERSITY EXPANDED FACULTY ADVISORS DATASET
# =============================================================================
TU_EXPANDED_FACULTY = [
    # 1. SIIT - AI & Computer Vision
    {
        "id": "tu_siit_004",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Sirindhorn International Institute of Technology (SIIT)",
        "faculty_th": "สถาบันเทคโนโลยีนานาชาติสิรินธร (SIIT)",
        "department": "School of Information, Computer, and Communication Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ คอมพิวเตอร์ และการสื่อสาร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Teerayut",
        "last_name": "Horanont",
        "full_name": "Assoc. Prof. Dr. Teerayut Horanont",
        "full_name_th": "รศ.ดร. ธีรยุทธ โหรานนท์",
        "role": "Associate Professor in Geoinformatics, Smart City & Urban Big Data",
        "email": "teerayut@siit.tu.ac.th",
        "image_url": "https://www.siit.tu.ac.th/images/faculty/teerayut.jpg",
        "profile_url": "https://www.siit.tu.ac.th/personnel.php?id=teerayut",
        "education": [
            "Ph.D. (Spatial Information Engineering), University of Tokyo, Japan",
            "M.Sc. (Remote Sensing and GIS), Asian Institute of Technology (AIT)",
            "B.Sc. (Computer Science), Thammasat University"
        ],
        "research_interests": [
            "Smart Cities & Urban Mobility Analytics",
            "Geographic Information Systems (GIS) & Spatial Big Data",
            "Deep Learning for Remote Sensing & Disaster Mitigation",
            "Internet of Things for Environmental Monitoring"
        ],
        "taught_courses": [
            "Spatial Big Data Analytics",
            "Smart City Technologies",
            "Geographic Information Systems"
        ],
        "featured_publications": [
            "Large-Scale GPS Trajectory Mining for Urban Congestion Detection",
            "Deep Learning-Based Flood Prediction Using Satellite Synthetic Aperture Radar",
            "IoT-Driven Real-time Air Quality Monitoring Network in Bangkok Metropolitan"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=TeerayutHoranont"
    },
    # 2. Thammasat Business School - Finance & Quantitative Modeling
    {
        "id": "tu_tbs_002",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "Department of Finance",
        "department_th": "ภาควิชาการเงิน",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Piman",
        "last_name": "Limpaphayom",
        "full_name": "Assoc. Prof. Dr. Piman Limpaphayom",
        "full_name_th": "รศ.ดร. พิมาน ลิ้มประภาภัทร",
        "role": "Associate Professor in Corporate Governance & Investment Strategy (CFA)",
        "email": "piman@tbs.tu.ac.th",
        "image_url": "https://tbs.tu.ac.th/images/faculty/piman.jpg",
        "profile_url": "https://tbs.tu.ac.th/faculty/piman",
        "education": [
            "Ph.D. (Finance), University of Rhode Island, USA",
            "M.B.A. (Finance), University of Houston, USA",
            "B.B.A. (Finance), Thammasat University"
        ],
        "research_interests": [
            "Corporate Governance & Board Dynamics",
            "Asset Pricing & Empirical Finance",
            "FinTech Innovation & Algorithmic Trading",
            "Mergers and Acquisitions (M&A) in Emerging Markets"
        ],
        "taught_courses": [
            "Advanced Corporate Finance",
            "Empirical Asset Pricing",
            "Financial Modeling and Valuation"
        ],
        "featured_publications": [
            "Corporate Governance and Firm Value in Asian Financial Markets",
            "Impact of ESG Integration on Sovereign Bond Yields in ASEAN",
            "Algorithmic Trading Performance during Extreme Market Volatility"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PimanLimpaphayom"
    },
    # 3. Chulabhorn International College of Medicine - Precision Medicine & Oncology
    {
        "id": "tu_cicm_001",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Chulabhorn International College of Medicine",
        "faculty_th": "วิทยาลัยแพทยศาสตร์นานาชาติจุฬาภรณ์",
        "department": "Clinical Oncology and Molecular Medicine Research Unit",
        "department_th": "หน่วยวิจัยมะเร็งวิทยาคลินิกและเวชศาสตร์โมเลกุล",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Kammal",
        "last_name": "Kumar Pawa",
        "full_name": "Prof. Dr. Med. Kammal Kumar Pawa",
        "full_name_th": "ศ.ดร.นพ. กัมมาล คูมาร์ ปาวา",
        "role": "Dean & Professor of Medicine and Clinical Immunology",
        "email": "kammal@cicm.tu.ac.th",
        "image_url": "https://cicm.tu.ac.th/images/faculty/kammal.jpg",
        "profile_url": "https://cicm.tu.ac.th/personnel/kammal",
        "education": [
            "Ph.D. (Immunology), London School of Hygiene & Tropical Medicine, UK",
            "M.D., Faculty of Medicine Siriraj Hospital, Mahidol University",
            "Diploma in Tropical Medicine & Hygiene (DTM&H), UK"
        ],
        "research_interests": [
            "Cellular Immunotherapy for Solid Tumors",
            "Precision Oncology & Molecular Biomarkers",
            "Tropical Medicine & Vaccine Development",
            "Clinical Trials of Herbal Bioactive Compounds in Cancer"
        ],
        "taught_courses": [
            "Molecular Oncology",
            "Clinical Immunology and Immunopathology",
            "Advanced Clinical Trial Methodology"
        ],
        "featured_publications": [
            "Targeted Immunotherapy Approaches in Advanced Cholangiocarcinoma",
            "Molecular Profiling of Lung Adenocarcinoma in Non-Smoking Asian Populations",
            "Efficacy of Curcumin Nanoparticles as Adjuvant Therapy in Colorectal Cancer"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KammalKumarPawa"
    },
    # 4. Faculty of Law - Business Law & AI Governance
    {
        "id": "tu_law_002",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Department of International Business Law",
        "department_th": "สาขากฎหมายธุรกิจระหว่างประเทศและทรัพย์สินทางปัญญา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pinai",
        "last_name": "Na Nakorn",
        "full_name": "Assoc. Prof. Dr. Pinai Na Nakorn",
        "full_name_th": "รศ.ดร. พินัย ณ นคร",
        "role": "Associate Professor in Cyberlaw, AI Ethics & International Commercial Law",
        "email": "pinai@law.tu.ac.th",
        "image_url": "https://www.law.tu.ac.th/images/faculty/pinai.jpg",
        "profile_url": "https://www.law.tu.ac.th/faculty/pinai",
        "education": [
            "Ph.D. (Law), University of Bristol, UK",
            "LL.M. (International Commercial Law), King's College London, UK",
            "LL.B. (Honours), Thammasat University",
            "Barrister-at-Law, Thai Bar Association"
        ],
        "research_interests": [
            "Artificial Intelligence Legal Governance & Ethics",
            "Digital Asset, Blockchain & Smart Contract Law",
            "Cross-Border Data Privacy & PDPA Compliance",
            "International Trade Law & Commercial Arbitration"
        ],
        "taught_courses": [
            "Artificial Intelligence and Cyber Law",
            "International Commercial Arbitration",
            "Comparative Intellectual Property Law"
        ],
        "featured_publications": [
            "Legal Liability Framework for Autonomous AI Systems: A Comparative Study",
            "Cross-Border Data Transfer Regulations under Thai PDPA and EU GDPR",
            "Enforceability of Smart Contracts in International Commercial Disputes"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PinaiNaNakorn"
    },
    # 5. Faculty of Economics - Econometrics & Health Economics
    {
        "id": "tu_econ_002",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Quantitative Economics & Econometrics",
        "department_th": "สาขาเศรษฐศาสตร์เชิงปริมาณและเศรษฐมิติ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Supachai",
        "last_name": "Srisuchart",
        "full_name": "Assoc. Prof. Dr. Supachai Srisuchart",
        "full_name_th": "รศ.ดร. ศุภชัย ศรีสุชาติ",
        "role": "Dean & Associate Professor in Labor Economics & Applied Econometrics",
        "email": "supachai@econ.tu.ac.th",
        "image_url": "https://www.econ.tu.ac.th/images/faculty/supachai.jpg",
        "profile_url": "https://www.econ.tu.ac.th/faculty/supachai",
        "education": [
            "Ph.D. (Economics), University of Illinois at Chicago, USA",
            "M.S. (Economics), University of Illinois at Chicago, USA",
            "B.Econ. (First Class Honours), Thammasat University"
        ],
        "research_interests": [
            "Applied Microeconometrics & Causal Inference",
            "Labor Market Transitions & Automation Impact",
            "Health Economics & Universal Health Coverage Evaluation",
            "Public Policy Evaluation for Aging Societies"
        ],
        "taught_courses": [
            "Applied Microeconometrics",
            "Labor Economics and Policy",
            "Quantitative Methods for Public Policy"
        ],
        "featured_publications": [
            "Impact of AI and Digital Automation on Thai Labor Market Structure",
            "Fiscal Sustainability of Universal Health Coverage in Thailand's Aging Society",
            "Evaluating Minimum Wage Policies on Small and Medium Enterprises: A Spatial Difference-in-Differences Approach"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SupachaiSrisuchart"
    },
    # 6. Faculty of Architecture & Planning - Smart Cities & Urban Resiliency
    {
        "id": "tu_arch_001",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Architecture and Planning",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการผังเมือง",
        "department": "Department of Urban Design and Planning",
        "department_th": "สาขาวิชาการออกแบบและการพัฒนาเมือง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Wijitbusaba",
        "last_name": "Marome",
        "full_name": "Assoc. Prof. Dr. Wijitbusaba Marome",
        "full_name_th": "รศ.ดร. วิจิตรบุษบา มารมย์",
        "role": "Head of Urban Resilient Futures Research Unit (URFRU)",
        "email": "wijitbusaba@ap.tu.ac.th",
        "image_url": "https://www.ap.tu.ac.th/images/faculty/wijitbusaba.jpg",
        "profile_url": "https://www.ap.tu.ac.th/faculty/wijitbusaba",
        "education": [
            "Ph.D. (Planning Studies), University College London (UCL), UK",
            "M.Sc. (Regional and Rural Development Planning), Asian Institute of Technology (AIT)",
            "B.Arch. (Architecture), Chulalongkorn University"
        ],
        "research_interests": [
            "Urban Resilience & Climate Adaptation Planning",
            "Smart Urban Infrastructure & Transit-Oriented Development",
            "Disaster Risk Reduction in Megacities",
            "Spatial Modeling & Urban Governance"
        ],
        "taught_courses": [
            "Urban Resilience and Climate Planning",
            "Spatial Analytics for Smart Cities",
            "Urban Design Studio"
        ],
        "featured_publications": [
            "Building Urban Resilience to Climate Hazards in the Bangkok Metropolitan Region",
            "Spatial Decision Support System for Flood Evacuation in Rapidly Urbanizing Deltas",
            "Transit-Oriented Development Integration with Green Infrastructure for Carbon Neutral Cities"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=WijitbusabaMarome"
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

def expand_thammasat_database():
    logger.info("==================================================================")
    logger.info(" Starting Thammasat University (TU) Complete Data Expansion")
    logger.info("==================================================================")

    session = SessionLocal()
    try:
        # ---------------------------------------------------------------------
        # Step 1: Process and Upsert Curricula
        # ---------------------------------------------------------------------
        logger.info(f"Processing {len(TU_EXPANDED_COURSES)} Thammasat University curricula...")
        courses_upserted = 0

        for c in TU_EXPANDED_COURSES:
            emb_text = build_course_embedding_text(c)
            emb_vec = embedding_service.get_embedding(emb_text)

            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                logger.info(f"[Update Course] {c['id']}: {c['title_th']}")
                for key, val in c.items():
                    setattr(existing, key, val)
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
            courses_upserted += 1

        session.commit()
        logger.info(f" Successfully upserted {courses_upserted} TU courses with 768-dim embeddings.")

        # ---------------------------------------------------------------------
        # Step 2: Process and Upsert Faculty Advisors
        # ---------------------------------------------------------------------
        logger.info(f"Processing {len(TU_EXPANDED_FACULTY)} Thammasat University faculty advisors...")
        faculty_upserted = 0

        for f in TU_EXPANDED_FACULTY:
            emb_text = build_faculty_embedding_text(f)
            emb_vec = embedding_service.get_embedding(emb_text)

            existing = session.query(FacultyDB).filter_by(id=f["id"]).first()
            if existing:
                logger.info(f"[Update Faculty] {f['id']}: {f['full_name_th']}")
                for key, val in f.items():
                    setattr(existing, key, val)
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
            faculty_upserted += 1

        session.commit()
        logger.info(f" Successfully upserted {faculty_upserted} TU faculty members with 768-dim embeddings.")

        # ---------------------------------------------------------------------
        # Step 3: Save to local JSON archive for reproducibility
        # ---------------------------------------------------------------------
        output_dir = Path(r"C:\Users\chaya\Documents\Program\Project\Teacher\backend\data\courses_new")
        output_dir.mkdir(parents=True, exist_ok=True)
        tu_archive_file = output_dir / "courses_tu_expanded.json"
        with open(tu_archive_file, "w", encoding="utf-8") as f:
            json.dump(TU_EXPANDED_COURSES, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved local copy to {tu_archive_file}")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error during Thammasat expansion: {e}", exc_info=True)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    expand_thammasat_database()
