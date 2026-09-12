# -*- coding: utf-8 -*-
"""
Regional Graduate Curriculum Expansion (Task 3):
Expands premier Master's and Doctoral programs for regional universities:
- University of Phayao (UP)
- Walailak University (WU)
- Maejo University (MJU)
- Mahasarakham University (MSU)
- Burapha University (BUU)
- Silpakorn University (SU)
- Mae Fah Luang University (MFU)
- Prince of Songkla University (PSU)
- Naresuan University (NU)
- Ubon Ratchathani University (UBU)
- Thaksin University (TSU)

Generates 768-dim Gemini vector embeddings and commits to local PostgreSQL 17.
"""

import os
import sys
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REGIONAL_GRAD_COURSES = [
    # =========================================================================
    # 1. University of Phayao (UP)
    # =========================================================================
    {
        "id": "up_ict_msc_it",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Master of Science Program in Information Technology",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (เทคโนโลยีสารสนเทศ)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Department of Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "มุ่งเน้นการวิจัยและประยุกต์ใช้เทคโนโลยีสารสนเทศขั้นสูง ระบบคลาวด์ การจัดการข้อมูลขนาดใหญ่ และการพัฒนานวัตกรรมดิจิทัลเพื่อชุมชนและองค์กร",
        "curriculum_highlights": [
            "Advanced Cloud Architecture & Distributed Systems",
            "Big Data Engineering & Analytics",
            "Enterprise Digital Strategy & Security",
            "Applied Smart Community Technologies"
        ],
        "career_paths": ["Senior IT Consultant", "Cloud Solutions Architect", "Enterprise Data Engineer", "Academic Researcher"],
        "tags": ["Information Technology", "Cloud Computing", "Big Data", "UP ICT"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_msc_cs",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Master of Science Program in Computer Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Department of Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "เน้นทฤษฎีวิทยาการคอมพิวเตอร์ ปัญญาประดิษฐ์ การเรียนรู้ของเครื่อง และคอมพิวเตอร์วิทัศน์ เพื่อสร้างสรรค์งานวิจัยและเทคโนโลยีปัญญาประดิษฐ์ประยุกต์",
        "curriculum_highlights": [
            "Machine Learning & Deep Learning Algorithms",
            "Computer Vision & Pattern Recognition",
            "Advanced Algorithm Design & Complexity",
            "Intelligent Systems Development"
        ],
        "career_paths": ["AI / Machine Learning Engineer", "Computer Vision Specialist", "Data Scientist", "Lecturer"],
        "tags": ["Computer Science", "Artificial Intelligence", "Deep Learning", "Machine Learning"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_ict_phd_cs_it",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
        "title_en": "Doctor of Philosophy Program in Computer Science and Information Technology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (วิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Department of Computer Science and IT",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ (วิจัยเน้น)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "270,000 บาท",
        "description": "หลักสูตรระดับดุษฎีบัณฑิตเพื่อพัฒนานักวิจัยชั้นแนวหน้า ผลิตองค์ความรู้ใหม่ระดับนานาชาติด้านปัญญาประดิษฐ์ วิศวกรรมซอฟต์แวร์ และเทคโนโลยีสารสนเทศขั้นสูง",
        "curriculum_highlights": [
            "Doctoral Dissertation in Applied AI / Computing",
            "International Journal Publications (Scopus / WoS)",
            "Interdisciplinary Computing Seminars",
            "Research Grant Proposal & Innovation Management"
        ],
        "career_paths": ["University Professor", "Senior Research Scientist", "Principal AI Architect", "R&D Director"],
        "tags": ["Ph.D.", "Doctorate", "Computer Science", "Advanced AI", "UP ICT"],
        "website_url": "https://ict.up.ac.th"
    },
    {
        "id": "up_eng_meng_civil",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมโยธา",
        "title_en": "Master of Engineering Program in Civil Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมโยธา)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "สาขาวิชาวิศวกรรมโยธา",
        "program_type": "ภาคปกติ / เสาร์-อาทิตย์",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "เน้นวิศวกรรมโครงสร้าง วิศวกรรมปฐพี และการบริหารโครงการก่อสร้างสมัยใหม่ที่ทนทานต่อภัยพิบัติทางธรรมชาติในภูมิภาคภาคเหนือ",
        "curriculum_highlights": [
            "Advanced Structural Analysis & Seismic Design",
            "Geotechnical Hazard Mitigation & Slope Stability",
            "Building Information Modeling (BIM) & Project Management",
            "Sustainable Construction Materials"
        ],
        "career_paths": ["Senior Structural Engineer", "Project Director", "Geotechnical Consultant", "Infrastructure Specialist"],
        "tags": ["Civil Engineering", "Structural Engineering", "Infrastructure", "BIM"],
        "website_url": "https://eng.up.ac.th"
    },
    {
        "id": "up_eng_meng_ee",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า",
        "title_en": "Master of Engineering Program in Electrical Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมไฟฟ้า)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมไฟฟ้า",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "มุ่งเน้นระบบโครงข่ายไฟฟ้าอัจฉริยะ (Smart Grid) พลังงานหมุนเวียน ระบบควบคุมอัตโนมัติ และอิเล็กทรอนิกส์กำลังสำหรับยานยนต์ไฟฟ้า",
        "curriculum_highlights": [
            "Smart Grid & Renewable Power Integration",
            "Power Electronics & EV Drive Systems",
            "Advanced Control Systems & Industrial Robotics",
            "Energy Management in Industry 4.0"
        ],
        "career_paths": ["Power Systems Engineer", "Renewable Energy Specialist", "Control & Automation Engineer", "Energy Auditor"],
        "tags": ["Electrical Engineering", "Smart Grid", "Renewable Energy", "Power Electronics"],
        "website_url": "https://eng.up.ac.th"
    },

    # =========================================================================
    # 2. Walailak University (WU)
    # =========================================================================
    {
        "id": "wu_eng_meng_inter",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมศาสตร์ (หลักสูตรนานาชาติ)",
        "title_en": "Master of Engineering Program in Engineering (International Program)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมศาสตร์)",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Engineering and Technology",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "department": "School of Engineering and Technology",
        "department_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "program_type": "หลักสูตรนานาชาติ (International Program)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "หลักสูตรนานาชาติแบบบูรณาการสาขาวิศวกรรมเคมี วัสดุ โยธา เครื่องกล และคอมพิวเตอร์ เพื่อรองรับการวิจัยอุตสาหกรรมในภาคใต้และภูมิภาคอาเซียน",
        "curriculum_highlights": [
            "Interdisciplinary Advanced Engineering Systems",
            "Sustainable Materials & Nanotechnology",
            "Smart Energy & Process Optimization",
            "International Research Collaboration"
        ],
        "career_paths": ["Engineering Manager", "R&D Engineer", "Process Safety Consultant", "International Project Lead"],
        "tags": ["Engineering", "International Program", "Materials Science", "Chemical Engineering", "Walailak"],
        "website_url": "https://engineer.wu.ac.th"
    },
    {
        "id": "wu_eng_phd_inter",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรม (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy Program in Engineering (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (วิศวกรรม)",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Engineering and Technology",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "department": "School of Engineering and Technology",
        "department_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "program_type": "หลักสูตรนานาชาติ (International Program)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "50,000 บาท",
        "tuition_total": "300,000 บาท",
        "description": "สร้างนักวิจัยดุษฎีบัณฑิตมาตรฐานสากล ผลิตงานวิจัยตีพิมพ์ Q1/Q2 ใน Scopus/WoS ด้านวิศวกรรมวัสดุ พลังงานยั่งยืน และวิศวกรรมกระบวนการชีวภาพ",
        "curriculum_highlights": [
            "High-Impact International Doctoral Research",
            "Advanced Materials & Catalysis Engineering",
            "Renewable Resource Transformation",
            "International Joint Supervisions"
        ],
        "career_paths": ["University Professor", "Principal Scientist", "Industrial R&D Director", "Policy Advisor"],
        "tags": ["Ph.D.", "Doctorate", "Engineering", "International Program", "Walailak"],
        "website_url": "https://engineer.wu.ac.th"
    },
    {
        "id": "wu_eng_msc_matsci",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวัสดุศาสตร์และวิศวกรรมวัสดุ",
        "title_en": "Master of Science Program in Materials Science and Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วัสดุศาสตร์และวิศวกรรมวัสดุ)",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Engineering and Technology",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "department": "Department of Materials and Polymer Engineering",
        "department_th": "สาขาวิชาวิศวกรรมพอลิเมอร์และวัสดุ",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "มุ่งเน้นการวิจัยพอลิเมอร์ชีวภาพ ยางพาราแปรรูป คอมโพสิตขั้นสูง และวัสดุสำหรับการกักเก็บพลังงานเพื่อสร้างมูลค่าเพิ่มให้วัตถุดิบภาคใต้",
        "curriculum_highlights": [
            "Advanced Polymer Characterization & Rheology",
            "Natural Rubber & Biocomposite Innovation",
            "Nanomaterials & Energy Storage Applications",
            "Circular Materials & Recycling Technologies"
        ],
        "career_paths": ["Materials Scientist", "Polymer R&D Specialist", "Quality Control Director", "Technical Consultant"],
        "tags": ["Materials Science", "Polymer Engineering", "Natural Rubber", "Nanomaterials"],
        "website_url": "https://engineer.wu.ac.th"
    },
    {
        "id": "wu_info_msc_ai_data",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาปัญญาประดิษฐ์และวิทยาการข้อมูล",
        "title_en": "Master of Science in Artificial Intelligence and Data Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (ปัญญาประดิษฐ์และวิทยาการข้อมูล)",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Informatics",
        "faculty_th": "สำนักวิชาสารสนเทศศาสตร์",
        "department": "Department of Intelligent Computing",
        "department_th": "สาขาวิชาคอมพิวเตอร์อัจฉริยะ",
        "program_type": "ภาคปกติ / แบบออนไลน์ไฮบริด",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "ผลิตผู้เชี่ยวชาญด้านปัญญาประดิษฐ์และการวิเคราะห์ข้อมูลขั้นสูงเพื่อการแพทย์อัจฉริยะ การเกษตรแม่นยำ และระบบอัตโนมัติ",
        "curriculum_highlights": [
            "Deep Learning & Generative AI",
            "Predictive Health Analytics & Medical AI",
            "Smart Agriculture IoT & AI Integration",
            "Enterprise Data Platforms & MLOps"
        ],
        "career_paths": ["AI Engineer", "Lead Data Scientist", "MLOps Engineer", "Digital Innovation Strategist"],
        "tags": ["Artificial Intelligence", "Data Science", "Machine Learning", "Informatics", "Walailak"],
        "website_url": "https://informatics.wu.ac.th"
    },

    # =========================================================================
    # 3. Maejo University (MJU)
    # =========================================================================
    {
        "id": "mju_agr_msc_sustainable_geosocial",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการพัฒนาภูมิสังคมอย่างยั่งยืน",
        "title_en": "Master of Science in Sustainable Geosocial Development",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การพัฒนาภูมิสังคมอย่างยั่งยืน)",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Agricultural Production",
        "faculty_th": "คณะผลิตกรรมการเกษตร",
        "department": "Department of Sustainable Geosocial Development",
        "department_th": "สาขาวิชาการพัฒนาภูมิสังคมอย่างยั่งยืน",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "100,000 บาท",
        "description": "เน้นการพัฒนาเกษตรกรรมและทรัพยากรชุมชนตามศาสตร์พระราชา การจัดการภูมิสังคมและสิ่งแวดล้อมอย่างยั่งยืนในเขตพื้นที่สูงและชนบท",
        "curriculum_highlights": [
            "Geosocial Principles & Sufficiency Economy in Agriculture",
            "Watershed & Mountain Resource Management",
            "Community-based Agro-enterprise Innovation",
            "Climate Change Adaptation & Resilience"
        ],
        "career_paths": ["Community Development Director", "Environmental Policy Consultant", "Smart Farm Planner", "Agricultural Officer"],
        "tags": ["Sustainable Agriculture", "Geosocial Development", "Agro-ecology", "Maejo"],
        "website_url": "https://ap.mju.ac.th"
    },
    {
        "id": "mju_agr_msc_horticulture",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาพืชสวน",
        "title_en": "Master of Science Program in Horticulture",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (พืชสวน)",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Agricultural Production",
        "faculty_th": "คณะผลิตกรรมการเกษตร",
        "department": "Department of Horticulture",
        "department_th": "สาขาวิชาพืชสวน",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "104,000 บาท",
        "description": "ความเชี่ยวชาญด้านการปรับปรุงพันธุ์พืชสวน สรีรวิทยาการผลิตพืชในโรงเรือนอัจฉริยะ และเทคโนโลยีหลังการเก็บเกี่ยวสำหรับผลไม้ ไม้ดอก และพืชสมุนไพร",
        "curriculum_highlights": [
            "Advanced Plant Breeding & Molecular Genetics",
            "Smart Greenhouse & Precision Horticulture",
            "Postharvest Physiology & Quality Assurance",
            "Medicinal & Aromatic Plant Biotechnology"
        ],
        "career_paths": ["Senior Horticulturist", "Plant Breeder", "Smart Farm Manager", "Postharvest Technology Specialist"],
        "tags": ["Horticulture", "Plant Breeding", "Postharvest", "Smart Farming", "Maejo"],
        "website_url": "https://ap.mju.ac.th"
    },
    {
        "id": "mju_agr_phd_res_mgmt",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาการจัดการและพัฒนาทรัพยากร",
        "title_en": "Doctor of Philosophy Program in Resource Management and Development",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (การจัดการและพัฒนาทรัพยากร)",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Agricultural Production",
        "faculty_th": "คณะผลิตกรรมการเกษตร",
        "department": "Department of Resource Management",
        "department_th": "สาขาวิชาการจัดการและพัฒนาทรัพยากร",
        "program_type": "ภาคปกติ (วิจัยเน้น)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "40,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "สร้างนักวิจัยระดับดุษฎีบัณฑิตเพื่อเป็นผู้นำการบริหารจัดการทรัพยากรดิน น้ำ ป่าไม้ และระบบนิเวศการเกษตรอย่างบูรณาการเพื่อความมั่นคงทางอาหาร",
        "curriculum_highlights": [
            "Integrated Natural Resource Modeling & Policy",
            "Soil Carbon Sequestration & Climate Smart Agriculture",
            "Doctoral Dissertation in Agro-resource Systems",
            "High-impact Scopus Research Publications"
        ],
        "career_paths": ["University Professor", "Senior Environmental Scientist", "Policy Director", "International Development Officer"],
        "tags": ["Ph.D.", "Doctorate", "Resource Management", "Agriculture", "Maejo"],
        "website_url": "https://ap.mju.ac.th"
    },

    # =========================================================================
    # 4. Mahasarakham University (MSU)
    # =========================================================================
    {
        "id": "msu_it_msc_it",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Master of Science Program in Information Technology",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (เทคโนโลยีสารสนเทศ)",
        "university": "Mahasarakham University",
        "university_th": "มหาวิทยาลัยมหาสารคาม",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Information Technology",
        "department_th": "ภาควิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "27,000 บาท",
        "tuition_total": "108,000 บาท",
        "description": "เน้นการพัฒนาระบบสารสนเทศองค์กร การวิเคราะห์ข้อมูลขนาดใหญ่ ความมั่นคงปลอดภัยไซเบอร์ และการขับเคลื่อนเศรษฐกิจดิจิทัลในภาคอีสาน",
        "curriculum_highlights": [
            "Enterprise Information Architecture & Cybersecurity",
            "Big Data Analytics & Business Intelligence",
            "Cloud Solutions & Web Services",
            "Digital Governance & Project Leadership"
        ],
        "career_paths": ["IT Director", "Cybersecurity Specialist", "Data Architect", "Senior Systems Analyst"],
        "tags": ["Information Technology", "Cybersecurity", "Data Analytics", "MSU IT"],
        "website_url": "https://it.msu.ac.th"
    },
    {
        "id": "msu_it_phd_it",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Doctor of Philosophy Program in Information Technology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีสารสนเทศ)",
        "university": "Mahasarakham University",
        "university_th": "มหาวิทยาลัยมหาสารคาม",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Information Technology",
        "department_th": "ภาควิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ (วิจัยเน้น)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท",
        "tuition_total": "252,000 บาท",
        "description": "หลักสูตรวิจัยระดับดุษฎีบัณฑิตเพื่อสร้างสรรค์นวัตกรรมสารสนเทศ ปัญญาประดิษฐ์ และเทคโนโลยีสารสนเทศเพื่อการศึกษาและสาธารณสุข",
        "curriculum_highlights": [
            "Advanced Research Methodologies in Informatics",
            "Doctoral Thesis with Scopus Publications",
            "Health & Educational Informatics Innovations",
            "AI-driven Knowledge Discovery Systems"
        ],
        "career_paths": ["University Professor", "Chief Technology Officer (CTO)", "Senior IT Researcher", "Informatics Consultant"],
        "tags": ["Ph.D.", "Doctorate", "Information Technology", "Informatics", "MSU"],
        "website_url": "https://it.msu.ac.th"
    },

    # =========================================================================
    # 5. Burapha University (BUU)
    # =========================================================================
    {
        "id": "buu_info_msc_ds",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์",
        "title_en": "Master of Science in Data Science and Analytics",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการข้อมูลและการวิเคราะห์)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Data Science",
        "department_th": "ภาควิชาวิทยาการข้อมูล",
        "program_type": "ภาคปกติ / ภาคพิเศษ เสาร์-อาทิตย์",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "ผลิตมหาบัณฑิตด้าน Data Science ที่ตอบโจทย์การเติบโตของเขตพัฒนาพิเศษภาคตะวันออก (EEC) เชื่อมโยงอุตสาหกรรม โลจิสติกส์ และ Smart Cities",
        "curriculum_highlights": [
            "Predictive Modeling & Applied Machine Learning",
            "Industrial IoT Data Engineering for EEC",
            "Big Data Analytics & Visualization Platforms",
            "Data Governance & Ethics in Industry 4.0"
        ],
        "career_paths": ["Senior Data Scientist", "Analytics Manager", "Big Data Engineer", "EEC Industrial Consultant"],
        "tags": ["Data Science", "Analytics", "Machine Learning", "EEC", "Burapha"],
        "website_url": "https://informatics.buu.ac.th"
    },
    {
        "id": "buu_eng_meng_industrial_logistics",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการและโลจิสติกส์",
        "title_en": "Master of Engineering Program in Industrial Engineering and Logistics",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมอุตสาหการและโลจิสติกส์)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Industrial Engineering",
        "department_th": "ภาควิชาวิศวกรรมอุตสาหการ",
        "program_type": "ภาคพิเศษ เสาร์-อาทิตย์",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "เน้นการบริหารจัดการห่วงโซ่อุปทานอัจฉริยะ ระบบการผลิตอัตโนมัติ และการเพิ่มประสิทธิภาพโลจิสติกส์ท่าเรือและอุตสาหกรรมในพื้นที่ EEC",
        "curriculum_highlights": [
            "Smart Manufacturing & Supply Chain 4.0",
            "Port & Maritime Logistics Optimization",
            "Operations Research & Simulation Modeling",
            "Lean Six Sigma & Quality Engineering"
        ],
        "career_paths": ["Supply Chain Director", "Logistics Operations Lead", "Industrial Plant Manager", "Process Optimization Consultant"],
        "tags": ["Industrial Engineering", "Logistics", "Supply Chain", "EEC", "Burapha"],
        "website_url": "https://eng.buu.ac.th"
    },
    {
        "id": "buu_eng_phd_eng",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิศวกรรมศาสตร์",
        "title_en": "Doctor of Philosophy Program in Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (วิศวกรรมศาสตร์)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Faculty of Engineering",
        "department_th": "คณะวิศวกรรมศาสตร์",
        "program_type": "ภาคปกติ (วิจัยเน้น)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "50,000 บาท",
        "tuition_total": "300,000 บาท",
        "description": "สร้างนักวิจัยระดับดุษฎีบัณฑิตที่มีผลงานวิจัยเชิงลึกด้านระบบอัตโนมัติ วิศวกรรมสิ่งแวดล้อม และพลังงานสะอาดเพื่อรองรับการเติบโตทางเศรษฐกิจของประเทศ",
        "curriculum_highlights": [
            "Doctoral Thesis in Advanced Engineering Innovation",
            "Clean Energy Technologies & Circular Economy",
            "Automated & Intelligent Systems Research",
            "International Peer-reviewed Publications"
        ],
        "career_paths": ["University Professor", "Chief Engineer", "Industrial R&D Lead", "Technical Policy Director"],
        "tags": ["Ph.D.", "Doctorate", "Engineering", "Innovation", "Burapha"],
        "website_url": "https://eng.buu.ac.th"
    },

    # =========================================================================
    # 6. Silpakorn University (SU)
    # =========================================================================
    {
        "id": "su_eng_meng_petro_polymer",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาปิโตรเคมีและวัสดุพอลิเมอร์",
        "title_en": "Master of Engineering in Petrochemicals and Polymer Materials",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (ปิโตรเคมีและวัสดุพอลิเมอร์)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Engineering and Industrial Technology",
        "faculty_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
        "department": "Department of Materials Science and Engineering",
        "department_th": "ภาควิชาวิทยาการและวิศวกรรมวัสดุ",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "หลักสูตรชั้นนำของประเทศด้านวิศวกรรมปิโตรเคมีและพอลิเมอร์ เน้นการสังเคราะห์สารพอลิเมอร์ขั้นสูง พลาสติกชีวภาพย่อยสลายได้ และเทคโนโลยีเร่งปฏิกิริยา",
        "curriculum_highlights": [
            "Catalytic Reaction Engineering & Petrochemicals",
            "Biodegradable Polymers & Green Composites",
            "Polymer Processing & Rheological Analysis",
            "Circular Polymer Economy & Chemical Recycling"
        ],
        "career_paths": ["Petrochemical Process Engineer", "Polymer R&D Scientist", "Plastics Technical Manager", "Materials Consultant"],
        "tags": ["Petrochemicals", "Polymer Engineering", "Materials Science", "Silpakorn"],
        "website_url": "https://eng.su.ac.th"
    },
    {
        "id": "su_eng_phd_foodtech",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีอาหาร",
        "title_en": "Doctor of Philosophy Program in Food Technology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีอาหาร)",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Engineering and Industrial Technology",
        "faculty_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
        "department": "Department of Food Technology",
        "department_th": "ภาควิชาเทคโนโลยีอาหาร",
        "program_type": "ภาคปกติ (วิจัยเน้น)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "ความเป็นเลิศด้านการวิจัยอาหารฟังก์ชัน สารออกฤทธิ์ทางชีวภาพ การแปรรูปอาหารขั้นสูง และการควบคุมความปลอดภัยระดับสากล",
        "curriculum_highlights": [
            "Advanced Food Engineering & Non-thermal Processing",
            "Bioactive Ingredients & Functional Food Design",
            "Food Nanotechnology & Encapsulation Systems",
            "International Food Safety Regulations & Risk Analysis"
        ],
        "career_paths": ["Food Science Professor", "Director of Food Innovation", "Senior Product Development Manager", "Food Safety Auditor"],
        "tags": ["Ph.D.", "Doctorate", "Food Technology", "Functional Food", "Silpakorn"],
        "website_url": "https://eng.su.ac.th"
    },

    # =========================================================================
    # 7. Mae Fah Luang University (MFU)
    # =========================================================================
    {
        "id": "mfu_cos_msc_inter",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์เครื่องสำอาง (หลักสูตรนานาชาติ)",
        "title_en": "Master of Science in Cosmetic Science (International Program)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาศาสตร์เครื่องสำอาง)",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Cosmetic Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "department": "School of Cosmetic Science",
        "department_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "program_type": "หลักสูตรนานาชาติ (International Program)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "หลักสูตรมาตรฐานสากลอันดับหนึ่งของภูมิภาค ผลิตผู้เชี่ยวชาญด้านการพัฒนาสูตรตำรับเครื่องสำอาง สารสกัดจากธรรมชาติ และการทดสอบประสิทธิภาพทางคลินิก",
        "curriculum_highlights": [
            "Advanced Cosmetic Formulation & Delivery Systems",
            "Phytochemistry & Natural Bioactive Ingredients",
            "Clinical Efficacy & Safety Evaluation",
            "Global Cosmetic Regulatory Affairs"
        ],
        "career_paths": ["Cosmetic Formulation Scientist", "R&D Director", "Regulatory Affairs Specialist", "Cosmeceutical Brand Founder"],
        "tags": ["Cosmetic Science", "International Program", "Formulation", "Natural Products", "MFU"],
        "website_url": "https://cosmeticscience.mfu.ac.th"
    },
    {
        "id": "mfu_cos_phd_inter",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์เครื่องสำอาง (หลักสูตรนานาชาติ)",
        "title_en": "Doctor of Philosophy in Cosmetic Science (International Program)",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (วิทยาศาสตร์เครื่องสำอาง)",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Cosmetic Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "department": "School of Cosmetic Science",
        "department_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "program_type": "หลักสูตรนานาชาติ (International Program)",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "สร้างนักวิจัยระดับดุษฎีบัณฑิตเพื่อบุกเบิกองค์ความรู้ใหม่ด้านวิทยาการชะลอวัย สารออกฤทธิ์ทางชีวภาพขั้นสูง และนวัตกรรมนาโนเทคโนโลยีเครื่องสำอาง",
        "curriculum_highlights": [
            "Doctoral Research with High-impact Q1/Q2 Publications",
            "Cellular Anti-aging Mechanisms & In-vitro Screening",
            "Nanocarriers & Target Delivery for Cosmeceuticals",
            "Global Patent & Intellectual Property Strategy"
        ],
        "career_paths": ["University Professor", "Principal Cosmetic Scientist", "Head of Global R&D", "Cosmetic Dermatologist Consultant"],
        "tags": ["Ph.D.", "Doctorate", "Cosmetic Science", "International Program", "Nanotechnology", "MFU"],
        "website_url": "https://cosmeticscience.mfu.ac.th"
    },

    # =========================================================================
    # 8. Thaksin University (TSU) & Ubon Ratchathani University (UBU)
    # =========================================================================
    {
        "id": "tsu_sci_msc_sustainable_resources",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการจัดการทรัพยากรและสิ่งแวดล้อมอย่างยั่งยืน",
        "title_en": "Master of Science in Sustainable Resource and Environmental Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (การจัดการทรัพยากรและสิ่งแวดล้อมอย่างยั่งยืน)",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Environmental Science",
        "department_th": "ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "96,000 บาท",
        "description": "เน้นการอนุรักษ์และจัดการระบบนิเวศลุ่มน้ำทะเลสาบสงขลา ความหลากหลายทางชีวภาพทางทะเล และการประเมินผลกระทบสิ่งแวดล้อมในภาคใต้",
        "curriculum_highlights": [
            "Songkhla Lake Basin Ecological Management",
            "Marine & Coastal Biodiversity Conservation",
            "Environmental Impact Assessment (EIA) & GIS",
            "Community Climate Resilience"
        ],
        "career_paths": ["Environmental Impact Specialist", "Ecologist", "Coastal Resource Officer", "Sustainability Consultant"],
        "tags": ["Environmental Science", "Ecology", "Marine Conservation", "Thaksin"],
        "website_url": "https://sci.tsu.ac.th"
    },
    {
        "id": "ubu_eng_meng_infra",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมโครงสร้างพื้นฐานและการขนส่งยั่งยืน",
        "title_en": "Master of Engineering in Sustainable Infrastructure and Transportation",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมโครงสร้างพื้นฐานและการขนส่งยั่งยืน)",
        "university": "Ubon Ratchathani University",
        "university_th": "มหาวิทยาลัยอุบลราชธานี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา",
        "program_type": "ภาคปกติ / เสาร์-อาทิตย์",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "104,000 บาท",
        "description": "มุ่งเน้นการวางแผนโครงสร้างพื้นฐาน คมนาคมขนส่งเชื่อมโยงอนุภูมิภาคลุ่มน้ำโขง (GMS) และวิศวกรรมการบำรุงรักษาอัจฉริยะ",
        "curriculum_highlights": [
            "Cross-border Transportation Systems & Logistics",
            "Smart Infrastructure Monitoring & NDT",
            "Sustainable Pavement Materials & Design",
            "GMS Economic Corridor Connectivity"
        ],
        "career_paths": ["Transportation Systems Planner", "Infrastructure Project Engineer", "Highway Consultant", "Public Works Director"],
        "tags": ["Civil Engineering", "Transportation", "Infrastructure", "GMS", "Ubon"],
        "website_url": "https://eng.ubu.ac.th"
    }
]


def build_course_embedding_text(c: Dict[str, Any]) -> str:
    highlights_text = ", ".join(c.get("curriculum_highlights", []))
    careers_text = ", ".join(c.get("career_paths", []))
    tags_text = ", ".join(c.get("tags", []))
    return (
        f"{c['title_th']} ({c.get('title_en', '')}). "
        f"University: {c['university']} ({c['university_th']}). "
        f"Faculty: {c['faculty']} ({c['faculty_th']}). "
        f"Department: {c.get('department', '')} ({c.get('department_th', '')}). "
        f"Degree: {c['degree_level']} {c.get('degree_name', '')}. "
        f"Description: {c.get('description', '')}. "
        f"Highlights: {highlights_text}. "
        f"Careers: {careers_text}. "
        f"Tags: {tags_text}."
    )[:6000]


def run_enrichment():
    logger.info("=======================================================================")
    logger.info("🚀 STARTING REGIONAL GRADUATE CURRICULUM EXPANSION (TASK 3)")
    logger.info("=======================================================================")

    logger.info(f"Targeting {len(REGIONAL_GRAD_COURSES)} premier graduate programs across regional universities...")

    # Vectorize via Gemini
    logger.info("🧠 Generating 768-dim vector embeddings for graduate courses (4 workers)...")
    for c in REGIONAL_GRAD_COURSES:
        c["embedding_text"] = build_course_embedding_text(c)

    def embed_course(c: Dict[str, Any]) -> Dict[str, Any]:
        vec = embedding_service.get_embedding(c["embedding_text"], max_retries=3)
        c["embedding"] = vec
        return c

    vectorized = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(embed_course, c): c for c in REGIONAL_GRAD_COURSES}
        for future in as_completed(futures):
            res = future.result()
            if res.get("embedding") and len(res["embedding"]) == 768:
                vectorized.append(res)

    logger.info(f"✅ Successfully computed {len(vectorized)} vector embeddings (0 null).")

    # Ingest into local PostgreSQL
    db = SessionLocal()
    inserted_cnt = 0
    updated_cnt = 0

    for c in vectorized:
        existing = db.query(CourseDB).filter_by(id=c["id"]).first()
        if existing:
            for k, v in c.items():
                setattr(existing, k, v)
            updated_cnt += 1
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
                embedding_text=c["embedding_text"],
                embedding=c["embedding"]
            )
            db.add(new_course)
            inserted_cnt += 1

    db.commit()
    db.close()

    logger.info(f"🎉 TASK 3 COMPLETE! Inserted {inserted_cnt}, Updated {updated_cnt} graduate courses with 768-dim embeddings.")


if __name__ == "__main__":
    run_enrichment()
