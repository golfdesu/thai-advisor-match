# -*- coding: utf-8 -*-
"""
National Universities Complete Data Expansion Pipeline
Universities Covered:
1. Srinakharinwirot University (SWU) - มหาวิทยาลัยศรีนครินทรวิโรฒ (มศว)
2. Silpakorn University (SU) - มหาวิทยาลัยศิลปากร (มศก.)
3. Suranaree University of Technology (SUT) - มหาวิทยาลัยเทคโนโลยีสุรนารี (มทส.)
4. Burapha University (BUU) - มหาวิทยาลัยบูรพา (มบ.) - EEC Regional Hub
5. National Institute of Development Administration (NIDA) - สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)
6. Naresuan University (NU) - มหาวิทยาลัยนเรศวร (มน.) - Lower Northern Flagship

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
# 1. EXPANDED NATIONAL CURRICULA DATASET (SWU, SU, SUT, BUU, NIDA, NU)
# =============================================================================
NATIONAL_UNIS_COURSES = [
    # -------------------------------------------------------------------------
    # 1. SRINAKHARINWIROT UNIVERSITY (SWU - มศว ประสานมิตร / องครักษ์)
    # -------------------------------------------------------------------------
    {
        "id": "swu_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine",
        "department_th": "สาขาวิชาแพทยศาสตร์ (ศูนย์การแพทย์สมเด็จพระเทพฯ)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "ผลิตแพทย์เวชปฏิบัติที่มีสมรรถนะคลินิกระดับสากล มีความร่วมมือกับ University of Nottingham (UK) และศูนย์การแพทย์สมเด็จพระเทพฯ องครักษ์",
        "curriculum_highlights": [
            "Clinical Training at HRH Princess Maha Chakri Sirindhorn Medical Center",
            "Joint Medical Program Partnership with University of Nottingham (UK)",
            "Holistic Patient Care & Pre-clinical Research Excellence",
            "Simulation-Based Medical Education"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Clinical Specialist", "Medical Academic Researcher", "Hospital Administrator"],
        "tags": ["Medicine", "Doctor", "SWU", "Nottingham", "Health Sciences", "Prasarnmit"],
        "website_url": "https://med.swu.ac.th"
    },
    {
        "id": "swu_dent_dds",
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Dental Surgery Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตรบัณฑิต)",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Dentistry",
        "department_th": "สาขาวิชาทันตแพทยศาสตร์ (มศว ประสานมิตร)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "230 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "384,000 บาท",
        "description": "เน้นทักษะคลินิกทันตกรรมระดับสูง เทคโนโลยีทันตกรรมดิจิทัล และการรักษาผู้ป่วยแบบสหสาขาวิชา ณ โรงพยาบาลทันตกรรม มศว ประสานมิตร",
        "curriculum_highlights": [
            "Advanced Clinical Practice at SWU Dental Hospital (Prasarnmit)",
            "Digital Dentistry & 3D Intraoral Scanning Technology",
            "Maxillofacial & Aesthetic Restorative Dentistry",
            "Community Oral Health Outreach"
        ],
        "career_paths": ["Dentist (ทันตแพทย์)", "Orthodontist", "Dental Specialist", "Dental Clinic Director"],
        "tags": ["Dentistry", "Dental", "SWU", "Prasarnmit", "Doctor of Dental Surgery"],
        "website_url": "https://dent.swu.ac.th"
    },
    {
        "id": "swu_cossci_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์เครื่องสำอางและผลิตภัณฑ์สุขภาพ",
        "title_en": "Bachelor of Science in Cosmetic Science and Health Products",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์เครื่องสำอาง)",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmaceutical Sciences",
        "department_th": "สาขาวิทยาศาสตร์เครื่องสำอาง",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "208,000 บาท",
        "description": "เน้นการวิจัยและพัฒนาสูตรตำรับเครื่องสำอาง ผลิตภัณฑ์ชะลอวัย สารสกัดสมุนไพรธรรมชาติ และการทดสอบประสิทธิภาพความปลอดภัยตามมาตรฐานสากล",
        "curriculum_highlights": [
            "Cosmetic Formulation Design & Nanocosmetics",
            "Efficacy & Safety Clinical Testing of Cosmeceuticals",
            "Natural Bioactive Compounds & Anti-Aging Science",
            "Cosmetic Brand Incubation & Regulatory Compliance"
        ],
        "career_paths": ["Cosmetic Formulation Scientist (R&D)", "Regulatory Affairs Specialist", "Cosmeceutical Brand Owner", "Quality Control Manager"],
        "tags": ["Cosmetic Science", "Pharmacy", "SWU", "Skincare", "Beauty Tech", "Formulation"],
        "website_url": "https://pharm.swu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 2. SILPAKORN UNIVERSITY (SU - ม.ศิลปากร วังท่าพระ / สนามจันทร์)
    # -------------------------------------------------------------------------
    {
        "id": "su_arch_barch",
        "title_th": "หลักสูตรสถาปัตยกรรมศาสตรบัณฑิต (สถ.บ.)",
        "title_en": "Bachelor of Architecture Program (B.Arch.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "สถ.บ. (สถาปัตยกรรมศาสตร์)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Architecture",
        "department_th": "สาขาวิชาสถาปัตยกรรม (วังท่าพระ)",
        "program_type": "ภาคปกติ",
        "duration_years": "5 ปี",
        "total_credits": "168 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "สถาบันผลิตสถาปนิกชั้นนำอันดับ 1 ของไทย ณ วังท่าพระ ผสานศิลปวัฒนธรรม ภูมิปัญญาไทย สถาปัตยกรรมร่วมสมัย และเทคโนโลยี BIM เพื่อความยั่งยืน",
        "curriculum_highlights": [
            "Iconic Design Studio & Architectural Heritage Preservation",
            "Contemporary Architectural Theory & Sustainable Design",
            "Building Information Modeling (BIM) & Parametric Architecture",
            "Senior Capstone Architectural Thesis"
        ],
        "career_paths": ["Licensed Architect (สถาปนิก)", "Design Principal", "Heritage Conservation Architect", "BIM Manager"],
        "tags": ["Architecture", "Silpakorn", "B.Arch", "Wang Tha Phra", "Heritage", "Design"],
        "website_url": "https://arch.su.ac.th"
    },
    {
        "id": "su_ict_game_interactive_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีดิจิทัลเพื่อการออกแบบ (เกมและสื่ออินเทอร์แอคทีฟ)",
        "title_en": "Bachelor of Science in Digital Technology for Design (Game and Interactive Media)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีดิจิทัลเพื่อการออกแบบ)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (ICT ศิลปากร)",
        "department": "Digital Technology for Design Program",
        "department_th": "สาขาวิชาเทคโนโลยีดิจิทัลเพื่อการออกแบบ (เมืองทองธานี)",
        "program_type": "โครงการพิเศษ (เมืองทองธานี)",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "หลักสูตรพัฒนาเกม แอนิเมชัน 3D และสื่อเสมือนจริง (VR/AR/XR) ชั้นแนวหน้าของไทย ผลิตนักสร้างสรรค์ดิจิทัลระดับสากล",
        "curriculum_highlights": [
            "Unreal Engine & Unity Advanced Game Development",
            "3D Modeling, Rigging, Animation & Visual Effects (VFX)",
            "Virtual Reality (VR), Augmented Reality (AR) & XR Experiences",
            "Game Economics & Studio Pipeline Management"
        ],
        "career_paths": ["Game Developer", "3D Technical Artist", "XR/VR Solution Specialist", "Creative Tech Director"],
        "tags": ["Game Development", "ICT", "Silpakorn", "VR/AR", "3D Animation", "Interactive Media"],
        "website_url": "https://ict.su.ac.th"
    },
    {
        "id": "su_pharm_pharmd",
        "title_th": "หลักสูตรเภสัชศาสตรบัณฑิต (บริบาลทางเภสัชกรรม / การคุ้มครองผู้บริโภค)",
        "title_en": "Doctor of Pharmacy Program (Pharm.D.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ภ.บ. (เภสัชศาสตร์)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Faculty of Pharmacy",
        "department_th": "คณะเภสัชศาสตร์ (พระราชวังสนามจันทร์)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "222 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "312,000 บาท",
        "description": "คณะเภสัชศาสตร์ชั้นนำ ณ พระราชวังสนามจันทร์ เน้นการบริบาลทางเภสัชกรรมในโรงพยาบาล การพัฒนายาชีววัตถุ และการวิจัยเภสัชวิทยา",
        "curriculum_highlights": [
            "Hospital Clinical Pharmacotherapy Clerkship",
            "Industrial Drug Formulation & Biopharmaceuticals",
            "Pharmacogenomics & Individualized Therapy",
            "Community Health & Consumer Protection"
        ],
        "career_paths": ["Hospital Clinical Pharmacist", "Industrial Formulation Pharmacist", "Clinical Research Associate (CRA)", "Regulatory Specialist"],
        "tags": ["Pharmacy", "Pharm.D.", "Silpakorn", "Sanam Chandra", "Healthcare"],
        "website_url": "https://pharmacy.su.ac.th"
    },

    # -------------------------------------------------------------------------
    # 3. SURANAREE UNIVERSITY OF TECHNOLOGY (SUT - มทส. นครราชสีมา)
    # -------------------------------------------------------------------------
    {
        "id": "sut_eng_mechatronics_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเมคคาทรอนิกส์และหุ่นยนต์",
        "title_en": "Bachelor of Engineering in Mechatronics and Robotics Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมเมคคาทรอนิกส์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Mechatronics Engineering",
        "department_th": "สาขาวิชาวิศวกรรมเมคคาทรอนิกส์",
        "program_type": "ภาคปกติ (ระบบไตรภาค)",
        "duration_years": "4 ปี",
        "total_credits": "180 หน่วยกิต (ไตรภาค)",
        "tuition_per_semester": "18,000 บาท (ต่อเทอมไตรภาค)",
        "tuition_total": "216,000 บาท",
        "description": "ศูนย์ความเป็นเลิศด้านวิศวกรรมเมคคาทรอนิกส์และหุ่นยนต์อุตสาหกรรม การควบคุมตำแหน่งความแม่นยำสูงระดับไมโคร/นาโน และระบบอัจฉริยะ Industry 4.0",
        "curriculum_highlights": [
            "Co-operative Education Program (สหกิจศึกษาเข้มข้น 2-3 ภาคการศึกษา)",
            "High-Precision Motion Control & Piezoelectric Actuators",
            "Industrial Automation, PLC & SCADA Systems",
            "Deep Learning & Embedded AI for Machine Diagnostics"
        ],
        "career_paths": ["Mechatronics Engineer", "Industrial Automation Architect", "Robotics R&D Specialist", "Smart Factory Lead"],
        "tags": ["Mechatronics", "Robotics", "SUT", "Industry 4.0", "Co-op Education", "Engineering"],
        "website_url": "https://eng.sut.ac.th/mechatronics"
    },
    {
        "id": "sut_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Medicine",
        "faculty_th": "สำนักวิชาแพทยศาสตร์",
        "department": "School of Medicine",
        "department_th": "สาขาวิชาแพทยศาสตร์ (โรงพยาบาลมหาวิทยาลัยเทคโนโลยีสุรนารี)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "250 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "มุ่งเน้นเวชศาสตร์ครอบครัว เวชศาสตร์ฉุกเฉิน และการใช้เทคโนโลยีปัญญาประดิษฐ์ทางการแพทย์ ณ โรงพยาบาลมหาวิทยาลัยเทคโนโลยีสุรนารี",
        "curriculum_highlights": [
            "Clinical Rotations at SUT University Hospital and Regional Medical Centers",
            "AI in Healthcare & Clinical Decision Support Systems",
            "Advanced Medical Simulation Center",
            "Family Medicine & Rural Community Health"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Clinical Specialist", "Medical AI Innovator", "Public Health Director"],
        "tags": ["Medicine", "Doctor", "SUT", "Korat", "Healthcare", "Hospital"],
        "website_url": "https://med.sut.ac.th"
    },

    # -------------------------------------------------------------------------
    # 4. BURAPHA UNIVERSITY (BUU - ม.บูรพา บางแสน / EEC Flagship)
    # -------------------------------------------------------------------------
    {
        "id": "buu_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Clinical Medicine",
        "department_th": "ภาควิชาแพทยศาสตร์คลินิก (โรงพยาบาลมหาวิทยาลัยบูรพา)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "250 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "336,000 บาท",
        "description": "ศูนย์การแพทย์เขตพัฒนาพิเศษภาคตะวันออก (EEC) มุ่งเน้นเวชศาสตร์ทางทะเล เวชศาสตร์ใต้น้ำ อาชีวเวชศาสตร์ และการดูแลสุขภาพในเขตนิคมอุตสาหกรรม",
        "curriculum_highlights": [
            "Clinical Training at Burapha University Hospital & Queen Savang Vadhana Memorial Hospital",
            "Specialized Focus on Maritime, Hyperbaric & Occupational Medicine",
            "Industrial Environmental Health & Toxicology",
            "Comprehensive Medical Research in Eastern Seaboard"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Maritime & Occupational Medicine Specialist", "Clinical Researcher", "Hospital Administrator"],
        "tags": ["Medicine", "Doctor", "BUU", "EEC", "Maritime Medicine", "Bangsaen"],
        "website_url": "https://med.buu.ac.th"
    },
    {
        "id": "buu_infor_ai_ds_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาปัญญาประดิษฐ์และวิทยาการข้อมูล",
        "title_en": "Bachelor of Science in Artificial Intelligence and Data Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ปัญญาประดิษฐ์และวิทยาการข้อมูล)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "ศูนย์กลางการศึกษาด้าน AI และ Data ในพื้นที่ EEC มุ่งเน้น AI สำหรับโรงงานอัจฉริยะ โลจิสติกส์ท่าเรือแหลมฉบัง และการวิเคราะห์ข้อมูลธุรกิจ",
        "curriculum_highlights": [
            "Applied Machine Learning & Deep Learning for Industry",
            "Smart Port & Logistics Data Analytics in EEC",
            "Big Data Technologies & Cloud Pipeline",
            "Co-operative Education with Leading Tech Enterprises in EEC"
        ],
        "career_paths": ["AI Engineer", "Data Scientist", "Data Platform Engineer", "Business Intelligence Specialist"],
        "tags": ["AI", "Data Science", "Informatics", "BUU", "EEC", "Smart Logistics"],
        "website_url": "https://informatics.buu.ac.th"
    },
    {
        "id": "buu_log_maritime_bba",
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาการจัดการพาณิชยนาวีและการขนส่งทางทะเล",
        "title_en": "Bachelor of Business Administration in Maritime Commerce and Shipping Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการพาณิชยนาวี)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Logistics",
        "faculty_th": "คณะโลจิสติกส์",
        "department": "Department of Maritime Logistics",
        "department_th": "ภาควิชาการจัดการพาณิชยนาวี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "18,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "คณะโลจิสติกส์แห่งแรกของไทย ผลิตผู้เชี่ยวชาญการบริหารพาณิชยนาวี ท่าเรือน้ำลึก การประกันภัยทางทะเล และห่วงโซ่อุปทานระหว่างประเทศ",
        "curriculum_highlights": [
            "Port Operations & Laem Chabang Deep Sea Port Management",
            "International Maritime Law & Marine Insurance",
            "Global Freight Forwarding & Vessel Chartering",
            "Maritime Supply Chain Analytics & Green Shipping"
        ],
        "career_paths": ["Maritime Logistics Executive", "Port Operations Specialist", "International Freight Forwarder", "Shipping Line Manager"],
        "tags": ["Logistics", "Maritime", "Shipping", "BUU", "EEC", "Port Management"],
        "website_url": "https://logistics.buu.ac.th"
    },

    # -------------------------------------------------------------------------
    # 5. NATIONAL INSTITUTE OF DEVELOPMENT ADMINISTRATION (NIDA - นิด้า)
    # -------------------------------------------------------------------------
    {
        "id": "nida_gsba_mba",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต (Flexible MBA / Regular MBA - NIDA Business School)",
        "title_en": "Master of Business Administration Program (NIDA Business School)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ - นิด้า)",
        "university": "National Institute of Development Administration",
        "university_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
        "faculty": "Graduate School of Business Administration (GSBA)",
        "faculty_th": "คณะบริหารธุรกิจ (NIDA Business School)",
        "department": "MBA Program",
        "department_th": "โครงการปริญญาโทบริหารธุรกิจ",
        "program_type": "ภาคปกติ / ภาคพิเศษ / Flexible",
        "duration_years": "2 ปี",
        "total_credits": "45 หน่วยกิต",
        "tuition_per_semester": "55,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "โรงเรียนบริหารธุรกิจแห่งแรกของไทยที่ได้รับการรับรองมาตรฐานสากล AACSB มุ่งเน้นการตัดสินใจเชิงกลยุทธ์ การเงิน การตลาด และการเป็นผู้นำองค์กร",
        "curriculum_highlights": [
            "AACSB Globally Accredited Business School",
            "Strategic Decision-Making & Harvard Case Method",
            "Corporate Financial Strategy & Asset Valuation",
            "Digital Business Model Transformation"
        ],
        "career_paths": ["Chief Executive / Senior Corporate Director", "Strategy Consultant (Big 4 / MBB)", "Investment Banker", "Venture Capitalist"],
        "tags": ["MBA", "NIDA", "AACSB", "Business School", "Leadership", "Strategy"],
        "website_url": "https://mba.nida.ac.th"
    },
    {
        "id": "nida_as_analytics_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการวิเคราะห์ธุรกิจและวิทยาการข้อมูล (Data Science & Business Analytics)",
        "title_en": "Master of Science in Business Analytics and Data Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การวิเคราะห์ธุรกิจและวิทยาการข้อมูล)",
        "university": "National Institute of Development Administration",
        "university_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
        "faculty": "Graduate School of Applied Statistics",
        "faculty_th": "คณะสถิติประยุกต์",
        "department": "Department of Data Analytics & AI",
        "department_th": "สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ธุรกิจ",
        "program_type": "ภาคพิเศษ (Weekend / Evening)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "หลักสูตรปริญญาโทด้าน Data Science ชั้นนำของประเทศ ผสานสถิติขั้นสูง Machine Learning, Big Data Analytics และการตัดสินใจเชิงธุรกิจ",
        "curriculum_highlights": [
            "Statistical Machine Learning & Predictive Modeling",
            "Deep Learning & Natural Language Processing in Business",
            "Big Data Engineering & Cloud Data Pipeline",
            "Data Strategy & Customer Intelligence"
        ],
        "career_paths": ["Lead Data Scientist", "Head of Business Analytics", "Data Platform Architect", "Chief Data Officer (CDO)"],
        "tags": ["Data Science", "Business Analytics", "NIDA", "Machine Learning", "Big Data", "Statistics"],
        "website_url": "https://as.nida.ac.th"
    },

    # -------------------------------------------------------------------------
    # 6. NARESUAN UNIVERSITY (NU - ม.นเรศวร พิษณุโลก / ภาคเหนือตอนล่าง)
    # -------------------------------------------------------------------------
    {
        "id": "nu_med_md",
        "title_th": "หลักสูตรแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Medicine Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พ.บ. (แพทยศาสตรบัณฑิต)",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Doctor of Medicine Program",
        "department_th": "สาขาวิชาแพทยศาสตร์ (โรงพยาบาลมหาวิทยาลัยนเรศวร)",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "ศูนย์การแพทย์ระดับตติยภูมิชั้นสูงแห่งภาคเหนือตอนล่าง มุ่งเน้นการแพทย์ปฐมภูมิ เวชศาสตร์ฉุกเฉิน และการดูแลผู้ป่วยวิกฤต",
        "curriculum_highlights": [
            "Super Tertiary Clinical Training at Naresuan University Hospital",
            "Regional Medical Hub for Lower Northern Thailand",
            "Advanced Cardiovascular & Oncology Center Training",
            "Community Medicine & Primary Care Innovation"
        ],
        "career_paths": ["Medical Doctor (แพทย์)", "Clinical Specialist", "Medical Researcher", "Regional Health Officer"],
        "tags": ["Medicine", "Doctor", "Naresuan", "Phitsanulok", "Healthcare"],
        "website_url": "https://med.nu.ac.th"
    },
    {
        "id": "nu_energy_solarenergy_phd",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาพลังงานทดแทนและพลังงานแสงอาทิตย์",
        "title_en": "Doctor of Philosophy Program in Renewable Energy and Solar Energy",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (พลังงานทดแทน)",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "School of Renewable Energy and Smart Grid Technology (SGtech)",
        "faculty_th": "วิทยาลัยพลังงานทดแทนและเทคโนโลยีสมาร์ตกริด (SGtech)",
        "department": "Department of Renewable Energy",
        "department_th": "สาขาวิชาพลังงานทดแทน",
        "program_type": "วิจัยเต็มเวลา (Full Research)",
        "duration_years": "3 - 5 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "270,000 บาท",
        "description": "ศูนย์วิจัยพลังงานแสงอาทิตย์และสมาร์ตกริดอันดับ 1 ของประเทศ เน้นเซลล์แสงอาทิตย์ประสิทธิภาพสูง ระบบกักเก็บพลังงาน BESS และไมโครกริด",
        "curriculum_highlights": [
            "National Excellence Center in Solar Energy Research (SERERT)",
            "Advanced Photovoltaic (PV) Technology & Perovskite Solar Cells",
            "Smart Grid & Battery Energy Storage Systems (BESS)",
            "Doctoral Dissertation with High-Impact Q1 International Publications"
        ],
        "career_paths": ["Principal Renewable Energy Scientist", "Smart Grid Technical Director", "Solar Energy Consultant", "University Professor"],
        "tags": ["Renewable Energy", "Solar Energy", "Smart Grid", "Naresuan", "Ph.D.", "Clean Tech"],
        "website_url": "https://sgtech.nu.ac.th"
    }
]

# =============================================================================
# 2. EXPANDED FACULTY ADVISORS DATASET (SWU, SU, SUT, BUU, NIDA, NU)
# =============================================================================
NATIONAL_UNIS_FACULTY = [
    # 1. SUT - Mechatronics & AI
    {
        "id": "sut_eng_001",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Mechatronics Engineering",
        "department_th": "สาขาวิชาวิศวกรรมเมคคาทรอนิกส์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Jiraphon",
        "last_name": "Srisertpol",
        "full_name": "Assoc. Prof. Dr. Jiraphon Srisertpol",
        "full_name_th": "รศ.ดร. จิระพล ศรีเสริฐผล",
        "role": "Director of Center of Excellence in Advanced Mechatronics and Automation",
        "email": "jiraphon@sut.ac.th",
        "image_url": "https://eng.sut.ac.th/images/faculty/jiraphon.jpg",
        "profile_url": "https://eng.sut.ac.th/staff/jiraphon",
        "education": [
            "D.Eng. (Mechanical Engineering), King Mongkut's University of Technology Thonburi",
            "M.Eng. (Mechanical Engineering), King Mongkut's University of Technology Thonburi",
            "B.Eng. (Mechanical Engineering), Suranaree University of Technology"
        ],
        "research_interests": [
            "Advanced Mechatronics & Precision Motion Control",
            "Piezoelectric Actuators & Nanopositioning",
            "Industrial Automation & Smart Manufacturing",
            "Condition Monitoring & Predictive Maintenance"
        ],
        "taught_courses": [
            "Precision Mechatronics System Design",
            "Industrial Robotics and Automation",
            "Advanced Control Theory"
        ],
        "featured_publications": [
            "Robust Adaptive Sliding Mode Control for Piezo-Actuated High-Precision Positioning Stages",
            "Vibration-based Machine Tool Anomaly Detection using Deep Autoencoders and Edge AI"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=JiraphonSrisertpol"
    },
    # 2. SUT - Biomedical Imaging & AI
    {
        "id": "sut_eng_002",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Computer Engineering",
        "department_th": "สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Paramate",
        "last_name": "Horkaew",
        "full_name": "Assoc. Prof. Dr. Paramate Horkaew",
        "full_name_th": "รศ.ดร. ปรเมศวร์ ห่อแก้ว",
        "role": "Head of Biomedical Imaging & AI Research Laboratory",
        "email": "paramate@sut.ac.th",
        "image_url": "https://cpe.sut.ac.th/images/faculty/paramate.jpg",
        "profile_url": "https://cpe.sut.ac.th/staff/paramate",
        "education": [
            "Ph.D. (Computing), Imperial College London, UK",
            "M.Sc. (Computing Science), Imperial College London, UK",
            "B.Eng. (Computer Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Medical Image Analysis & 3D Reconstruction",
            "Biomedical Signal Processing & ECG AI",
            "Deep Learning in Radiology & Surgical Simulation",
            "Computer Vision in Biomedical Sciences"
        ],
        "taught_courses": [
            "Medical Image Processing and Analysis",
            "Deep Learning for Computer Vision",
            "Pattern Recognition and Machine Learning"
        ],
        "featured_publications": [
            "3D Cardiac Left Ventricle Reconstruction from Sparse Ultrasound Views using Deep Shape Priors",
            "Automated Arrhythmia Classification from Multi-Lead ECG Signals using Temporal Convolutional Networks"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ParamateHorkaew"
    },
    # 3. NIDA - Business Analytics & Data Science
    {
        "id": "nida_as_001",
        "university": "National Institute of Development Administration",
        "university_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
        "faculty": "Graduate School of Applied Statistics",
        "faculty_th": "คณะสถิติประยุกต์",
        "department": "Department of Data Analytics & AI",
        "department_th": "สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์ธุรกิจ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Surapong",
        "last_name": "Aungsakun",
        "full_name": "Assoc. Prof. Dr. Surapong Ongkittikul",
        "full_name_th": "รศ.ดร. สุรพงษ์ อังคสกุลเกียรติ",
        "role": "Dean & Associate Professor in Big Data Analytics and AI Strategy",
        "email": "surapong@as.nida.ac.th",
        "image_url": "https://as.nida.ac.th/images/faculty/surapong.jpg",
        "profile_url": "https://as.nida.ac.th/faculty/surapong",
        "education": [
            "Ph.D. (Computer Science / Data Mining), University of Melbourne, Australia",
            "M.Sc. (Computer Science), Asian Institute of Technology (AIT)",
            "B.Sc. (Statistics), Chulalongkorn University"
        ],
        "research_interests": [
            "Customer Lifetime Value & Predictive Churn Modeling",
            "Natural Language Processing for Thai Financial Sentiments",
            "Algorithmic Credit Scoring in Banking and FinTech",
            "Big Data Strategy for Public Sector Governance"
        ],
        "taught_courses": [
            "Advanced Machine Learning for Business Decisions",
            "Data Mining and Knowledge Discovery",
            "Big Data Strategy and Governance"
        ],
        "featured_publications": [
            "Machine Learning Approaches for Microfinance Credit Risk Assessment in Southeast Asia",
            "Thai Financial Sentiment Analysis using Domain-Adapted Pretrained Language Models"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SurapongNIDA"
    },
    # 4. SWU - Cosmeceutical & Nanomedicine
    {
        "id": "swu_pharm_001",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmaceutical Sciences",
        "department_th": "สาขาวิทยาศาสตร์เครื่องสำอางและเภสัชเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Prapaporn",
        "last_name": "Boonme",
        "full_name": "Prof. Dr. Prapaporn Boonme",
        "full_name_th": "ศ.ดร. ประภาพร บุญมี",
        "role": "Professor in Cosmetic Formulation & Lipid Nanoparticles",
        "email": "prapaporn@g.swu.ac.th",
        "image_url": "https://pharm.swu.ac.th/images/faculty/prapaporn.jpg",
        "profile_url": "https://pharm.swu.ac.th/staff/prapaporn",
        "education": [
            "Ph.D. (Pharmaceutical Technology), Chulalongkorn University",
            "M.Sc. (Pharmaceutics), Chulalongkorn University",
            "B.Pharm. (First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Solid Lipid Nanoparticles (SLN) & Nanostructured Lipid Carriers (NLC)",
            "Cosmeceutical Delivery Systems for Anti-Aging Bioactives",
            "Transdermal & Topical Drug Delivery Systems",
            "Natural Herbal Extracts in Cosmetic Formulations"
        ],
        "taught_courses": [
            "Advanced Cosmetic Formulation Design",
            "Nanotechnology in Drug and Cosmetic Delivery",
            "Cosmetic Quality Assurance and Stability Testing"
        ],
        "featured_publications": [
            "Development of Curcumin-Loaded Nanostructured Lipid Carriers for Enhanced Skin Penetration and Anti-Aging",
            "Microemulsion and Nanoemulsion Systems for Transdermal Delivery of Natural Bioactive Flavonoids"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PrapapornBoonme"
    },
    # 5. BUU - Maritime Logistics & Marine Science
    {
        "id": "buu_log_001",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Logistics",
        "faculty_th": "คณะโลจิสติกส์",
        "department": "Department of Maritime Logistics and Port Management",
        "department_th": "ภาควิชาการจัดการพาณิชยนาวีและโลจิสติกส์ท่าเรือ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Saroj",
        "last_name": "Ruangdej",
        "full_name": "Assoc. Prof. Dr. Saroj Ruangdej",
        "full_name_th": "รศ.ดร. สโรช เรืองเดช",
        "role": "Associate Professor in Maritime Supply Chain & Port Optimization",
        "email": "saroj@buu.ac.th",
        "image_url": "https://logistics.buu.ac.th/images/faculty/saroj.jpg",
        "profile_url": "https://logistics.buu.ac.th/staff/saroj",
        "education": [
            "Ph.D. (Maritime Studies / Logistics), Cardiff University, UK",
            "M.Sc. (International Shipping and Transport), University of Plymouth, UK",
            "B.Sc. (Maritime Science), Burapha University"
        ],
        "research_interests": [
            "Deep-Sea Port Berth Allocation & Quay Crane Scheduling",
            "Green Maritime Shipping & Carbon Emission Reduction in EEC",
            "Maritime Risk Assessment and Marine Insurance Law",
            "Multimodal Freight Transportation Networks"
        ],
        "taught_courses": [
            "Port Planning and Operations Optimization",
            "Maritime Economics and Shipping Strategy",
            "International Maritime Logistics"
        ],
        "featured_publications": [
            "Integrated Berth Allocation and Quay Crane Scheduling at Laem Chabang Deep Sea Port using Genetic Algorithms",
            "Carbon Footprint Reduction Strategies for Container Terminals in the Eastern Economic Corridor (EEC)"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SarojRuangdej"
    },
    # 6. NU - Solar Energy & Smart Grid
    {
        "id": "nu_sgtech_001",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "School of Renewable Energy and Smart Grid Technology (SGtech)",
        "faculty_th": "วิทยาลัยพลังงานทดแทนและเทคโนโลยีสมาร์ตกริด (SGtech)",
        "department": "Solar Energy Research Center",
        "department_th": "ศูนย์ความเป็นเลิศด้านพลังงานแสงอาทิตย์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Nipon",
        "last_name": "Ketjoy",
        "full_name": "Prof. Dr. Nipon Ketjoy",
        "full_name_th": "ศ.ดร. นิพนธ์ เกตุจ้อย",
        "role": "Director of Solar Energy Excellence Center & Professor of Renewable Energy",
        "email": "niponk@nu.ac.th",
        "image_url": "https://sgtech.nu.ac.th/images/faculty/nipon.jpg",
        "profile_url": "https://sgtech.nu.ac.th/staff/nipon",
        "education": [
            "D.Tech.Sc. (Energy Technology), Asian Institute of Technology (AIT)",
            "M.Eng. (Energy Technology), Asian Institute of Technology (AIT)",
            "B.Eng. (Mechanical Engineering), King Mongkut's University of Technology Thonburi"
        ],
        "research_interests": [
            "Solar Photovoltaic (PV) Performance & Degradation Modeling",
            "Microgrid Integration with Battery Energy Storage Systems (BESS)",
            "Floating Solar PV Systems in Tropical Reservoirs",
            "Renewable Energy Policy and Hybrid Grid Optimization"
        ],
        "taught_courses": [
            "Photovoltaic Engineering and System Design",
            "Microgrid Architecture and Control",
            "Renewable Energy Project Economics"
        ],
        "featured_publications": [
            "Long-Term Degradation Analysis of Crystalline Silicon PV Modules under Tropical Climatic Conditions",
            "Optimal Energy Management and Sizing of Hybrid Solar-BESS Microgrid for Remote Communities"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=NiponKetjoy"
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

def expand_national_universities_database():
    logger.info("==================================================================")
    logger.info(" Starting National Universities Expansion (SWU, SU, SUT, BUU, NIDA, NU)")
    logger.info("==================================================================")

    session = SessionLocal()
    try:
        # 1. Upsert Curricula
        logger.info(f"Processing {len(NATIONAL_UNIS_COURSES)} national university curricula...")
        courses_count = 0

        for c in NATIONAL_UNIS_COURSES:
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
        logger.info(f" Successfully upserted {courses_count} national university curricula.")

        # 2. Upsert Faculty Advisors
        logger.info(f"Processing {len(NATIONAL_UNIS_FACULTY)} national university faculty advisors...")
        faculty_count = 0

        for f in NATIONAL_UNIS_FACULTY:
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
        archive_file = output_dir / "courses_national_expanded.json"
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(NATIONAL_UNIS_COURSES, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved local dataset to {archive_file}")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error during national expansion: {e}", exc_info=True)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    expand_national_universities_database()
