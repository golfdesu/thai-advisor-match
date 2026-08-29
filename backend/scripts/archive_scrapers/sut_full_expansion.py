import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

# 1. Existing SUT Courses Clean-up Map (Fixing English title_th)
SUT_EXISTING_FIXES = {
    "sut_bachelor_electrical_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า",
        "title_en": "Bachelor of Engineering Program in Electrical Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมไฟฟ้า)"
    },
    "sut_bachelor_polymer_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมพอลิเมอร์",
        "title_en": "Bachelor of Engineering Program in Polymer Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมพอลิเมอร์)"
    },
    "sut_bachelor_aeronautical_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการบินและอวกาศ",
        "title_en": "Bachelor of Engineering Program in Aeronautical Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมการบินและอวกาศ)"
    },
    "sut_bachelor_agricultural_and_food_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเกษตรและอาหาร",
        "title_en": "Bachelor of Engineering Program in Agricultural and Food Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมเกษตรและอาหาร)",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์"
    },
    "sut_bachelor_animal_production_technology": {
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีและนวัตกรรมทางสัตว์",
        "title_en": "Bachelor of Science Program in Animal Production Technology",
        "degree_name": "วท.บ. (เทคโนโลยีและนวัตกรรมทางสัตว์)",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร"
    },
    "sut_bachelor_automotive_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมยานยนต์",
        "title_en": "Bachelor of Engineering Program in Automotive Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมยานยนต์)"
    },
    "sut_bachelor_ceramic_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเซรามิก",
        "title_en": "Bachelor of Engineering Program in Ceramic Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมเซรามิก)"
    },
    "sut_bachelor_chemical_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี",
        "title_en": "Bachelor of Engineering Program in Chemical Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมเคมี)"
    },
    "sut_bachelor_civil_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา",
        "title_en": "Bachelor of Engineering Program in Civil Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมโยธา)"
    },
    "sut_bachelor_communication": {
        "title_th": "หลักสูตรนิเทศศาสตรบัณฑิต สาขาวิชาการสื่อสารดิจิทัลและสื่อนฤมิต",
        "title_en": "Bachelor of Communication Arts Program in Digital Communication",
        "degree_name": "นศ.บ. (การสื่อสารดิจิทัล)",
        "faculty_th": "สำนักวิชาศาสตร์และศิลป์ดิจิทัล"
    },
    "sut_bachelor_computer_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)"
    },
    "sut_bachelor_crop_production_technology": {
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีการผลิตพืช",
        "title_en": "Bachelor of Science Program in Crop Production Technology",
        "degree_name": "วท.บ. (เทคโนโลยีการผลิตพืช)",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร"
    },
    "sut_bachelor_environmental_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมสิ่งแวดล้อม",
        "title_en": "Bachelor of Engineering Program in Environmental Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมสิ่งแวดล้อม)"
    },
    "sut_bachelor_food_technology": {
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีอาหาร",
        "title_en": "Bachelor of Science Program in Food Technology",
        "degree_name": "วท.บ. (เทคโนโลยีอาหาร)",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร"
    },
    "sut_bachelor_geological_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมธรณี",
        "title_en": "Bachelor of Engineering Program in Geological Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมธรณี)"
    },
    "sut_bachelor_industrial_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการ",
        "title_en": "Bachelor of Engineering Program in Industrial Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมอุตสาหการ)"
    },
    "sut_bachelor_information_technology": {
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีดิจิทัลและสารสนเทศ",
        "title_en": "Bachelor of Science Program in Digital Technology and Information",
        "degree_name": "วท.บ. (เทคโนโลยีดิจิทัลและสารสนเทศ)",
        "faculty_th": "สำนักวิชาศาสตร์และศิลป์ดิจิทัล"
    },
    "sut_bachelor_management_technology": {
        "title_th": "หลักสูตรบริหารธุรกิจบัณฑิต สาขาวิชาเทคโนโลยีการจัดการ",
        "title_en": "Bachelor of Business Administration Program in Management Technology",
        "degree_name": "บธ.บ. (เทคโนโลยีการจัดการ)"
    },
    "sut_bachelor_mechanical_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล",
        "title_en": "Bachelor of Engineering Program in Mechanical Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมเครื่องกล)"
    },
    "sut_bachelor_mechatronics": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเมคคาทรอนิกส์",
        "title_en": "Bachelor of Engineering Program in Mechatronics Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมเมคคาทรอนิกส์)"
    },
    "sut_bachelor_metallurgical_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโลหการ",
        "title_en": "Bachelor of Engineering Program in Metallurgical Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมโลหการ)"
    },
    "sut_bachelor_occupational_health_and_safety": {
        "title_th": "หลักสูตรสาธารณสุขศาสตรบัณฑิต สาขาวิชาอาชีวอนามัยและความปลอดภัย",
        "title_en": "Bachelor of Public Health Program in Occupational Health and Safety",
        "degree_name": "ส.บ. (อาชีวอนามัยและความปลอดภัย)"
    },
    "sut_bachelor_environmental_health": {
        "title_th": "หลักสูตรสาธารณสุขศาสตรบัณฑิต สาขาวิชาอนามัยสิ่งแวดล้อม",
        "title_en": "Bachelor of Public Health Program in Environmental Health",
        "degree_name": "ส.บ. (อนามัยสิ่งแวดล้อม)"
    },
    "sut_bachelor_telecommunication_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโทรคมนาคม",
        "title_en": "Bachelor of Engineering Program in Telecommunication Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมโทรคมนาคม)"
    },
    "sut_bachelor_transportation_engineering": {
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมขนส่งและโลจิสติกส์",
        "title_en": "Bachelor of Engineering Program in Transportation and Logistics Engineering",
        "degree_name": "วศ.บ. (วิศวกรรมขนส่งและโลจิสติกส์)"
    },
    # Fix Master courses with English titles
    "sut-ms-02": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์", "title_en": "Master of Science Program in Applied Mathematics", "degree_name": "วท.ม. (คณิตศาสตร์ประยุกต์)"},
    "sut-ms-03": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาฟิสิกส์ประยุกต์และเลเซอร์", "title_en": "Master of Science Program in Applied Physics and Laser Technology", "degree_name": "วท.ม. (ฟิสิกส์ประยุกต์)"},
    "sut-ms-04": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาชีวเคมีและเทคโนโลยีชีวเคมี", "title_en": "Master of Science Program in Biochemistry and Biochemical Technology", "degree_name": "วท.ม. (ชีวเคมี)"},
    "sut-ms-05": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาชีวเวชศาสตร์", "title_en": "Master of Science Program in Biomedical Sciences", "degree_name": "วท.ม. (ชีวเวชศาสตร์)"},
    "sut-ms-06": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาชีววิทยา", "title_en": "Master of Science Program in Biology", "degree_name": "วท.ม. (ชีววิทยา)"},
    "sut-ms-07": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพการเกษตร", "title_en": "Master of Science Program in Agricultural Biotechnology", "degree_name": "วท.ม. (เทคโนโลยีชีวภาพ)"},
    "sut-ms-08": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์ระดับเซลล์และโมเลกุลสำหรับชีวการแพทย์", "title_en": "Master of Science Program in Cellular and Molecular Science for Biomedical Applications", "degree_name": "วท.ม. (วิทยาศาสตร์เซลล์และโมเลกุล)"},
    "sut-ms-09": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเคมี", "title_en": "Master of Science Program in Chemistry", "degree_name": "วท.ม. (เคมี)"},
    "sut-ms-10": {"title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมโยธา ขนส่ง และทรัพยากรธรณี", "title_en": "Master of Engineering Program in Civil, Transportation and Geo-resources Engineering", "degree_name": "วศ.ม. (วิศวกรรมโยธาและทรัพยากรธรณี)"},
    "sut-ms-11": {"title_th": "หลักสูตรศึกษาศาสตรมหาบัณฑิต สาขาวิชาสหกิจศึกษาและการจัดการเรียนรู้เชิงประสบการณ์", "title_en": "Master of Education Program in Cooperative Education", "degree_name": "ศษ.ม. (สหกิจศึกษา)"},
    "sut-ms-12": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีการผลิตพืช", "title_en": "Master of Science Program in Crop Production Technology", "degree_name": "วท.ม. (เทคโนโลยีการผลิตพืช)"},
    "sut-ms-14": {"title_th": "หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชาภาษาอังกฤษศึกษา (ELS)", "title_en": "Master of Arts Program in English Language Studies", "degree_name": "ศศ.ม. (ภาษาอังกฤษศึกษา)"},
    "sut-ms-16": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาภูมิสารสนเทศ", "title_en": "Master of Science Program in Geoinformatics", "degree_name": "วท.ม. (ภูมิสารสนเทศ)"},
    "sut-ms-17": {"title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาระบบวิศวกรรมอุตสาหการและสิ่งแวดล้อม", "title_en": "Master of Engineering Program in Industrial Systems and Environmental Engineering", "degree_name": "วศ.ม. (วิศวกรรมอุตสาหการและสิ่งแวดล้อม)"},
    "sut-ms-18": {"title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมวัสดุ (เซรามิก/โลหการ/พอลิเมอร์)", "title_en": "Master of Engineering Program in Materials Engineering", "degree_name": "วศ.ม. (วิศวกรรมวัสดุ)"},
    "sut-ms-19": {"title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมเครื่องกลและระบบกระบวนการ", "title_en": "Master of Engineering Program in Mechanical and Process System Engineering", "degree_name": "วศ.ม. (วิศวกรรมเครื่องกล)"},
    "sut-ms-20": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาจุลชีววิทยา", "title_en": "Master of Science Program in Microbiology", "degree_name": "วท.ม. (จุลชีววิทยา)"},
    "sut-ms-21": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาฟิสิกส์", "title_en": "Master of Science Program in Physics", "degree_name": "วท.ม. (ฟิสิกส์)"},
    "sut-ms-22": {"title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมโทรคมนาคมและคอมพิวเตอร์", "title_en": "Master of Engineering Program in Telecommunication and Computer Engineering", "degree_name": "วศ.ม. (วิศวกรรมโทรคมนาคมและคอมพิวเตอร์)"},
    "sut-ms-23": {"title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการแพทย์ปริวรรตและการวิจัยทางคลินิก", "title_en": "Master of Science Program in Translational Medicine", "degree_name": "วท.ม. (การแพทย์ปริวรรต)"},
    "sut-phd-15": {"title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาชีววิทยาสิ่งแวดล้อม", "title_en": "Doctor of Philosophy Program in Environmental Biology", "degree_name": "ปร.ด. (ชีววิทยาสิ่งแวดล้อม)"},
}

# 2. NEW SUT CURRICULA TO EXPAND (~35+ official programs across all schools)
NEW_SUT_COURSES = [
    # --- สำนักวิชาแพทยศาสตร์ / ทันตแพทยศาสตร์ / พยาบาลศาสตร์ ---
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
        "department": "Department of Clinical Medicine",
        "department_th": "สาขาวิชาแพทยศาสตร์คลินิก",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "252 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท (ระบบไตรภาค)",
        "tuition_total": "810,000 บาท",
        "description": "มุ่งเน้นการผลิตแพทย์ที่มีความรู้ความสามารถทางคลินิกระดับสูง มีคุณธรรม จริยธรรม และทักษะการวิจัยทางการแพทย์เพื่อพัฒนาสุขภาวะของชุมชนและประเทศ",
        "curriculum_highlights": ["การเรียนรู้โดยใช้ปัญหาเป็นฐาน (PBL) ร่วมกับเทคโนโลยีการแพทย์สมัยใหม่", "การฝึกปฏิบัติการทางคลินิก ณ โรงพยาบาลมหาวิทยาลัยเทคโนโลยีสุรนารีและเครือข่าย", "การบูรณาการเวชศาสตร์ครอบครัว ชุมชน และนวัตกรรมการแพทย์"],
        "career_paths": ["แพทย์เวชปฏิบัติทั่วไป", "แพทย์เฉพาะทางสาขาต่างๆ", "อาจารย์แพทย์และนักวิจัยทางการแพทย์", "ผู้บริหารงานสาธารณสุขและโรงพยาบาล"],
        "tags": ["Medicine", "Doctor", "Health Science", "SUT Medicine"],
        "website_url": "https://med.sut.ac.th"
    },
    {
        "id": "sut_dent_dds",
        "title_th": "หลักสูตรทันตแพทยศาสตรบัณฑิต",
        "title_en": "Doctor of Dental Surgery Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ท.บ. (ทันตแพทยศาสตรบัณฑิต)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Dentistry",
        "faculty_th": "สำนักวิชาทันตแพทยศาสตร์",
        "department": "Department of Dentistry",
        "department_th": "สาขาวิชาทันตแพทยศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "6 ปี",
        "total_credits": "228 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท (ระบบไตรภาค)",
        "tuition_total": "1,080,000 บาท",
        "description": "มุ่งเน้นการสร้างทันตแพทย์ที่มีทักษะหัตถการคลินิกที่แม่นยำ เชี่ยวชาญการดูแลสุขภาพช่องปากแบบองค์รวม และการประยุกต์ใช้นวัตกรรมทันตกรรมดิจิทัล",
        "curriculum_highlights": ["การฝึกปฏิบัติการคลินิกทันตกรรมด้วยเครื่องมือและระบบดิจิทัลทันสมัย", "การบริการทันตกรรมชุมชนและทันตกรรมป้องกัน", "การเรียนการสอนบูรณาการวิทยาศาสตร์การแพทย์และทันตกรรม"],
        "career_paths": ["ทันตแพทย์ทั่วไปในโรงพยาบาลรัฐและเอกชน", "ทันตแพทย์เฉพาะทาง", "เจ้าของคลินิกทันตกรรม", "อาจารย์และนักวิจัยทันตแพทยศาสตร์"],
        "tags": ["Dentistry", "Dental", "Doctor of Dental Surgery", "SUT Dentistry"],
        "website_url": "https://dent.sut.ac.th"
    },
    {
        "id": "sut_nurs_bns",
        "title_th": "หลักสูตรพยาบาลศาสตรบัณฑิต",
        "title_en": "Bachelor of Nursing Science Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พย.บ. (พยาบาลศาสตรบัณฑิต)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Nursing",
        "faculty_th": "สำนักวิชาพยาบาลศาสตร์",
        "department": "Department of Nursing",
        "department_th": "สาขาวิชาพยาบาลศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท (ระบบไตรภาค)",
        "tuition_total": "336,000 บาท",
        "description": "ผลิตพยาบาลวิชาชีพที่มีสมรรถนะตามมาตรฐานสากล มีทักษะการพยาบาลแบบองค์รวม การใช้เทคโนโลยีสุขภาพ และจิตบริการในการดูแลผู้ป่วยทุกช่วงวัย",
        "curriculum_highlights": ["การฝึกปฏิบัติการพยาบาลในห้องจำลองสถานการณ์เสมือนจริง (Simulated Lab)", "การฝึกประสบการณ์วิชาชีพ ณ โรงพยาบาล มทส. และโรงพยาบาลศูนย์ชั้นนำ", "การพยาบาลผู้สูงอายุและการพยาบาลเวชปฏิบัติฉุกเฉิน"],
        "career_paths": ["พยาบาลวิชาชีพในโรงพยาบาลรัฐและเอกชน", "พยาบาลเฉพาะทาง", "พยาบาลประจำสถานประกอบการ", "อาจารย์และนักวิชาการพยาบาล"],
        "tags": ["Nursing", "Health Science", "Nurse", "SUT Nursing"],
        "website_url": "https://nurse.sut.ac.th"
    },
    {
        "id": "sut_nurs_mns_adult",
        "title_th": "หลักสูตรพยาบาลศาสตรมหาบัณฑิต สาขาวิชาการพยาบาลผู้ใหญ่และผู้สูงอายุ",
        "title_en": "Master of Nursing Science Program in Adult and Gerontological Nursing",
        "degree_level": "ปริญญาโท",
        "degree_name": "พย.ม. (การพยาบาลผู้ใหญ่และผู้สูงอายุ)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Nursing",
        "faculty_th": "สำนักวิชาพยาบาลศาสตร์",
        "department": "Department of Nursing",
        "department_th": "สาขาวิชาพยาบาลศาสตร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท (ระบบไตรภาค)",
        "tuition_total": "210,000 บาท",
        "description": "เน้นการพัฒนาพยาบาลผู้เชี่ยวชาญระดับสูงในการดูแลผู้ป่วยผู้ใหญ่และผู้สูงอายุที่มีภาวะซับซ้อนและการวิจัยทางคลินิกเพื่อพัฒนาคุณภาพการพยาบาล",
        "curriculum_highlights": ["การพยาบาลขั้นสูงสำหรับผู้ป่วยวิกฤตและโรคเรื้อรังซับซ้อน", "การบูรณาการเทคโนโลยีสุขภาพและระบบสารสนเทศทางการพยาบาล", "การวิจัยและสร้างนวัตกรรมการพยาบาลผู้สูงอายุ"],
        "career_paths": ["พยาบาลผู้เชี่ยวชาญทางคลินิก (APN)", "ผู้บริหารและหัวหน้าฝ่ายการพยาบาล", "อาจารย์พยาบาลและนักวิจัย"],
        "tags": ["Nursing", "Gerontology", "Adult Nursing", "Master of Nursing"],
        "website_url": "https://nurse.sut.ac.th"
    },
    # --- สำนักวิชาสาธารณสุขศาสตร์ (Graduate) ---
    {
        "id": "sut_ph_mph",
        "title_th": "หลักสูตรสาธารณสุขศาสตรมหาบัณฑิต",
        "title_en": "Master of Public Health Program",
        "degree_level": "ปริญญาโท",
        "degree_name": "ส.ม. (สาธารณสุขศาสตร์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Public Health",
        "faculty_th": "สำนักวิชาสาธารณสุขศาสตร์",
        "department": "Department of Public Health",
        "department_th": "สาขาวิชาสาธารณสุขศาสตร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท (ระบบไตรภาค)",
        "tuition_total": "192,000 บาท",
        "description": "มุ่งเน้นการพัฒนานักวิชาการและผู้บริหารด้านสาธารณสุขที่มีความเชี่ยวชาญด้านระบาดวิทยา การบริหารจัดการระบบสุขภาพ และการจัดการอนามัยสิ่งแวดล้อม",
        "curriculum_highlights": ["การบริหารจัดการระบบสุขภาพและนโยบายสาธารณสุขเชิงยุทธศาสตร์", "การวิเคราะห์ระบาดวิทยาและการประเมินความเสี่ยงสุขภาพ", "การจัดการสุขศาสตร์อุตสาหกรรมและความปลอดภัย"],
        "career_paths": ["นักวิชาการสาธารณสุขระดับชำนาญการ", "ผู้บริหารหน่วยงานสุขภาพและโรงพยาบาล", "นักวิจัยด้านระบาดวิทยาและสิ่งแวดล้อม"],
        "tags": ["Public Health", "MPH", "Health Policy", "Epidemiology"],
        "website_url": "https://iph.sut.ac.th"
    },
    {
        "id": "sut_ph_phd",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสาธารณสุขศาสตร์",
        "title_en": "Doctor of Philosophy Program in Public Health",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (สาธารณสุขศาสตร์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Public Health",
        "faculty_th": "สำนักวิชาสาธารณสุขศาสตร์",
        "department": "Department of Public Health",
        "department_th": "สาขาวิชาสาธารณสุขศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "40,000 บาท (ระบบไตรภาค)",
        "tuition_total": "360,000 บาท",
        "description": "เน้นการผลิตดุษฎีบัณฑิตและนักวิจัยชั้นนำที่สามารถสร้างองค์ความรู้ใหม่ นวัตกรรมสุขภาพ และข้อเสนอนโยบายสาธารณสุขระดับประเทศและสากล",
        "curriculum_highlights": ["การวิจัยขั้นสูงด้านระบาดวิทยาและชีวสถิติ", "การสร้างนวัตกรรมสุขศาสตร์อุตสาหกรรมและอนามัยสิ่งแวดล้อม", "การพัฒนานโยบายสุขภาพระดับประชากร"],
        "career_paths": ["อาจารย์และนักวิจัยสาธารณสุขศาสตร์", "ผู้เชี่ยวชาญนโยบายสุขภาพในองค์กรระดับประเทศและนานาชาติ (WHO, ฯลฯ)"],
        "tags": ["Public Health", "Ph.D.", "Doctorate", "Health Research"],
        "website_url": "https://iph.sut.ac.th"
    },
    # --- สำนักวิชาวิศวกรรมศาสตร์ (Ph.D. & Master's Programs) ---
    {
        "id": "sut_eng_phd_chemical",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมเคมี",
        "title_en": "Doctor of Philosophy Program in Chemical Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมเคมี)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Chemical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมเคมี",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "สร้างนักวิจัยระดับปริญญาเอกที่มีความเชี่ยวชาญด้านกระบวนการทางวิศวกรรมเคมี พลังงานสะอาด ตัวเร่งปฏิกิริยา และการออกแบบกระบวนการคาร์บอนต่ำ",
        "curriculum_highlights": ["การวิจัยตัวเร่งปฏิกิริยาและการสังเคราะห์สารเคมีขั้นสูง", "การดักจับและกักเก็บคาร์บอน (CCUS) และพลังงานไฮโดรเจน", "การจำลองและการเพิ่มประสิทธิภาพกระบวนการเคมีเชิงคำนวณ"],
        "career_paths": ["นักวิจัยอาวุโสด้านพลังงานและปิโตรเคมี", "อาจารย์มหาวิทยาลัย", "ที่ปรึกษาเทคโนโลยีวิศวกรรมเคมี"],
        "tags": ["Chemical Engineering", "Ph.D.", "Catalysis", "Clean Energy"],
        "website_url": "https://che.sut.ac.th"
    },
    {
        "id": "sut_eng_phd_materials",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมวัสดุ",
        "title_en": "Doctor of Philosophy Program in Materials Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมวัสดุ)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Materials Engineering",
        "department_th": "สาขาวิชาวิศวกรรมวัสดุ (เซรามิก/โลหการ/พอลิเมอร์)",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "หลักสูตรบูรณาการด้านวิศวกรรมวัสดุขั้นสูง ครอบคลุมเซรามิก โลหการ และพอลิเมอร์ เพื่อตอบโจทย์อุตสาหกรรมเซมิคอนดักเตอร์ ยานยนต์ และชีวการแพทย์",
        "curriculum_highlights": ["การวิจัยวัสดุสำหรับกักเก็บพลังงานและแบตเตอรี่", "การพัฒนาวัสดุเซรามิกและพอลิเมอร์ชีวภาพ", "การวิเคราะห์โครงสร้างจุลภาคด้วยแสงซินโครตรอน"],
        "career_paths": ["นักวิจัยวัสดุศาสตร์และนาโนเทคโนโลยี", "วิศวกรวิจัยและพัฒนาวัสดุขั้นสูง (R&D)", "อาจารย์และนักวิชาการ"],
        "tags": ["Materials Engineering", "Ceramic", "Polymer", "Metallurgy", "Ph.D."],
        "website_url": "https://mat.sut.ac.th"
    },
    {
        "id": "sut_eng_phd_environmental",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมสิ่งแวดล้อม",
        "title_en": "Doctor of Philosophy Program in Environmental Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมสิ่งแวดล้อม)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Environmental Engineering",
        "department_th": "สาขาวิชาวิศวกรรมสิ่งแวดล้อม",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "มุ่งเน้นการวิจัยเทคโนโลยีการบำบัดมลพิษขั้นสูง การฟื้นฟูสิ่งแวดล้อม และการจัดการน้ำและของเสียตามแนวทางเศรษฐกิจหมุนเวียน (Circular Economy)",
        "curriculum_highlights": ["เทคโนโลยีการบำบัดน้ำเสียขั้นสูงและการนำน้ำกลับมาใช้ใหม่", "การจัดการขยะมูลฝอยและของเสียอันตรายเพื่อผลิตพลังงาน", "แบบจำลองมลพิษทางอากาศและการเปลี่ยนแปลงสภาพภูมิอากาศ"],
        "career_paths": ["ผู้เชี่ยวชาญและที่ปรึกษาด้านวิศวกรรมสิ่งแวดล้อม", "อาจารย์และนักวิจัย", "ผู้บริหารนโยบายสิ่งแวดล้อม"],
        "tags": ["Environmental Engineering", "Ph.D.", "Water Treatment", "Sustainability"],
        "website_url": "https://env.sut.ac.th"
    },
    {
        "id": "sut_eng_phd_industrial",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการและการผลิต",
        "title_en": "Doctor of Philosophy Program in Industrial and Manufacturing Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมอุตสาหการและการผลิต)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Industrial Engineering",
        "department_th": "สาขาวิชาวิศวกรรมอุตสาหการ",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "เน้นการวิจัยขั้นสูงด้านอุตสาหกรรม 4.0 การเพิ่มประสิทธิภาพระบบโซ่อุปทาน การผลิตอัจฉริยะ (Smart Manufacturing) และการประยุกต์ใช้ AI ในอุตสาหกรรม",
        "curriculum_highlights": ["การจำลองและเพิ่มประสิทธิภาพระบบการผลิตด้วยดิจิทัลทวิน (Digital Twin)", "การวิจัยระบบโลจิสติกส์และซัพพลายเชนระดับโลก", "การจัดการคุณภาพและการยกระดับผลิตภาพด้วยปัญญาประดิษฐ์"],
        "career_paths": ["ที่ปรึกษาระบบอุตสาหกรรมและการผลิตขั้นสูง", "นักวิจัยอุตสาหการ", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Industrial Engineering", "Manufacturing", "Ph.D.", "Industry 4.0"],
        "website_url": "https://ie.sut.ac.th"
    },
    {
        "id": "sut_eng_phd_mechatronics",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมเมคคาทรอนิกส์",
        "title_en": "Doctor of Philosophy Program in Mechatronics Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมเมคคาทรอนิกส์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Mechatronics Engineering",
        "department_th": "สาขาวิชาวิศวกรรมเมคคาทรอนิกส์",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "วิจัยเชิงลึกด้านระบบหุ่นยนต์อัตโนมัติ การควบคุมอัจฉริยะ ปัญญาประดิษฐ์สำหรับระบบไซเบอร์-กายภาพ และระบบอัตโนมัติในโรงงาน",
        "curriculum_highlights": ["การพัฒนาหุ่นยนต์บริการและหุ่นยนต์อุตสาหกรรมขั้นสูง", "ระบบควบคุมอัจฉริยะและการประมวลผลเซนเซอร์หลายมิติ", "การออกแบบยานยนต์อัตโนมัติและโดรน"],
        "career_paths": ["นักวิจัยระบบหุ่นยนต์และ AI", "วิศวกรเมคคาทรอนิกส์ระดับสถาปนิก", "อาจารย์และนักวิชาการ"],
        "tags": ["Mechatronics", "Robotics", "Automation", "Ph.D."],
        "website_url": "https://mechatronics.sut.ac.th"
    },
    {
        "id": "sut_eng_phd_geological",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมธรณีและทรัพยากรธรณี",
        "title_en": "Doctor of Philosophy Program in Geological and Geo-resources Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมธรณี)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Geotechnology",
        "department_th": "สาขาวิชาเทคโนโลยีธรณี",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "เน้นการวิจัยธรณีวิศวกรรม กลศาสตร์ของหินและดิน การสำรวจและขุดเจาะทรัพยากรใต้ดิน รวมถึงการประเมินความเสี่ยงภัยพิบัติทางธรณี",
        "curriculum_highlights": ["กลศาสตร์ของหินขั้นสูงและการขุดเจาะอุโมงค์ใต้ดิน", "การสำรวจทางธรณีฟิสิกส์และแหล่งพลังงานใต้พิภพ", "การวิเคราะห์เสถียรภาพลาดชันและฐานรากโครงสร้างขนาดใหญ่"],
        "career_paths": ["วิศวกรธรณีอาวุโส", "ผู้เชี่ยวชาญการขุดเจาะอุโมงค์และเหมืองแร่", "อาจารย์และนักวิจัยธรณีเทคโนโลยี"],
        "tags": ["Geological Engineering", "Geotechnology", "Rock Mechanics", "Ph.D."],
        "website_url": "https://geo.sut.ac.th"
    },
    {
        "id": "sut_eng_phd_telecom_comp",
        "title_th": "หลักสูตรวิศวกรรมศาสตรดุษฎีบัณฑิต สาขาวิชาวิศวกรรมโทรคมนาคมและคอมพิวเตอร์",
        "title_en": "Doctor of Philosophy Program in Telecommunication and Computer Engineering",
        "degree_level": "ปริญญาเอก",
        "degree_name": "วศ.ด. (วิศวกรรมโทรคมนาคมและคอมพิวเตอร์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Telecommunication Engineering",
        "department_th": "สาขาวิชาวิศวกรรมโทรคมนาคม",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "การวิจัยขั้นสูงด้านระบบสื่อสารไร้สาย 5G/6G เครือข่ายคอมพิวเตอร์ ความมั่นคงปลอดภัยไซเบอร์ และการประมวลผลข้อมูลขนาดใหญ่",
        "curriculum_highlights": ["ระบบสื่อสารไร้สายความเร็วสูงและโครงข่ายเซนเซอร์ไร้สาย", "ปัญญาประดิษฐ์สำหรับโครงข่ายสื่อสารและ Edge Computing", "การออกแบบสายอากาศและอุปกรณ์ไมโครเวฟขั้นสูง"],
        "career_paths": ["นักวิจัยระบบสื่อสารและเครือข่าย", "สถาปนิกโครงสร้างพื้นฐานดิจิทัล", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Telecommunication", "Computer Engineering", "Wireless", "5G/6G", "Ph.D."],
        "website_url": "https://telecom.sut.ac.th"
    },
    # --- สำนักวิชาวิทยาศาสตร์ (Ph.D. Programs) ---
    {
        "id": "sut_sci_phd_chemistry",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเคมี",
        "title_en": "Doctor of Philosophy Program in Chemistry",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เคมี)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Chemistry",
        "department_th": "สาขาวิชาเคมี",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "มุ่งเน้นการวิจัยเคมีขั้นสูง เคมีอินทรีย์ เคมีอนินทรีย์ เคมีเชิงฟิสิกส์ และเคมีคำนวณ โดยเน้นการใช้ประโยชน์ร่วมกับสถาบันวิจัยแสงซินโครตรอนแห่งชาติ",
        "curriculum_highlights": ["การวิเคราะห์โครงสร้างสารด้วยเทคนิคซินโครตรอน", "การสังเคราะห์สารอินทรีย์และสารชีวภาพสำหรับยา", "เคมีคำนวณและการออกแบบโมเลกุล"],
        "career_paths": ["นักวิจัยเคมีในสถาบันวิจัยระดับชาติและนานาชาติ", "นักวิทยาศาสตร์ R&D ภาคอุตสาหกรรม", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Chemistry", "Ph.D.", "Synchrotron", "Computational Chemistry"],
        "website_url": "https://chem.sut.ac.th"
    },
    {
        "id": "sut_sci_phd_physics",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาฟิสิกส์",
        "title_en": "Doctor of Philosophy Program in Physics",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (ฟิสิกส์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Physics",
        "department_th": "สาขาวิชาฟิสิกส์",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "ศูนย์กลางการวิจัยฟิสิกส์พลังงานสูง ฟิสิกส์ทฤษฎี ฟิสิกส์สารควบแน่น และฟิสิกส์ดาราศาสตร์ ร่วมกับห้องปฏิบัติการระดับโลก (CERN, SLRI)",
        "curriculum_highlights": ["การวิจัยฟิสิกส์พลังงานสูงและอนุภาคพื้นฐาน (ร่วมกับ CERN)", "ฟิสิกส์สารควบแน่นและควอนตัมเทคโนโลยี", "การประยุกต์ใช้แสงซินโครตรอนในฟิสิกส์ของแข็ง"],
        "career_paths": ["นักฟิสิกส์วิจัยประจำสถาบันชั้นนำ", "นักวิทยาศาสตร์ข้อมูลและควอนตัม", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Physics", "Ph.D.", "Quantum", "High Energy Physics", "CERN"],
        "website_url": "https://phys.sut.ac.th"
    },
    {
        "id": "sut_sci_phd_applied_math",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์",
        "title_en": "Doctor of Philosophy Program in Applied Mathematics",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (คณิตศาสตร์ประยุกต์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Mathematics",
        "department_th": "สาขาวิชาคณิตศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "สร้างนักวิจัยด้านคณิตศาสตร์เชิงคำนวณ แบบจำลองคณิตศาสตร์สำหรับการเงินและชีววิทยา และการวิเคราะห์ข้อมูลขั้นสูง",
        "curriculum_highlights": ["แบบจำลองคณิตศาสตร์สำหรับระบบพลวัตและชีวการแพทย์", "ระเบียบวิธีเชิงตัวเลขและการคำนวณสมรรถนะสูง (HPC)", "คณิตศาสตร์ประกันภัยและการวิเคราะห์เชิงปริมาณ"],
        "career_paths": ["นักคณิตศาสตร์ประกันภัยและนักวิเคราะห์เชิงปริมาณ (Quant)", "นักวิทยาศาสตร์ข้อมูล (Data Scientist)", "อาจารย์และนักวิจัย"],
        "tags": ["Applied Mathematics", "Mathematics", "Data Science", "Ph.D."],
        "website_url": "https://math.sut.ac.th"
    },
    {
        "id": "sut_sci_phd_geoinformatics",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาภูมิสารสนเทศ",
        "title_en": "Doctor of Philosophy Program in Geoinformatics",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (ภูมิสารสนเทศ)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Remote Sensing and Geoinformatics",
        "department_th": "สาขาวิชาภูมิสารสนเทศและการสำรวจระยะไกล",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "การวิจัยเชิงลึกด้านการสำรวจระยะไกล (Remote Sensing) ระบบสารสนเทศภูมิศาสตร์ (GIS) และการประยุกต์ใช้ AI ในการวิเคราะห์ข้อมูลเชิงพื้นที่และภูมิอากาศ",
        "curriculum_highlights": ["การประมวลผลภาพถ่ายดาวเทียมขั้นสูงด้วย Deep Learning", "การสร้างแบบจำลองการเปลี่ยนแปลงการใช้ที่ดินและภูมิอากาศ", "ภูมิสารสนเทศสำหรับเกษตรแม่นยำและการจัดการภัยพิบัติ"],
        "career_paths": ["ผู้เชี่ยวชาญด้าน GIS และ Remote Sensing", "นักวิจัยเทคโนโลยีอวกาศและภูมิสารสนเทศ (GISTDA ฯลฯ)", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Geoinformatics", "GIS", "Remote Sensing", "Satellite Imagery", "Ph.D."],
        "website_url": "https://gis.sut.ac.th"
    },
    {
        "id": "sut_sci_phd_biomedical",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาชีวเวชศาสตร์",
        "title_en": "Doctor of Philosophy Program in Biomedical Sciences",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (ชีวเวชศาสตร์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Preclinical Sciences",
        "department_th": "สาขาวิชาชีวเวชศาสตร์และวิทยาศาสตร์ปรีคลินิก",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "342,000 บาท",
        "description": "เน้นการวิจัยระดับโมเลกุล พยาธิสรีรวิทยา กลไกการเกิดโรค การพัฒนายาและชีวเภสัชภัณฑ์ เพื่อตอบสนองงานวิจัยทางการแพทย์ขั้นสูง",
        "curriculum_highlights": ["ชีววิทยาโมเลกุลและพันธุศาสตร์ทางการแพทย์", "การค้นพบและพัฒนายาจากสารธรรมชาติและชีวสังเคราะห์", "การวิจัยโรคมะเร็งและภูมิคุ้มกันวิทยาบำบัด"],
        "career_paths": ["นักวิจัยชีวเวชศาสตร์และพัฒนายา", "นักวิทยาศาสตร์การแพทย์ประจำโรงพยาบาลและสถาบันวิจัย", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Biomedical Sciences", "Molecular Biology", "Ph.D.", "Drug Discovery"],
        "website_url": "https://sc.sut.ac.th"
    },
    # --- สำนักวิชาเทคโนโลยีการเกษตร (Ph.D. & Master's Programs) ---
    {
        "id": "sut_agr_phd_crop_production",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีการผลิตพืช",
        "title_en": "Doctor of Philosophy Program in Crop Production Technology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีการผลิตพืช)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Agricultural Technology",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร",
        "department": "School of Crop Production Technology",
        "department_th": "สาขาวิชาเทคโนโลยีการผลิตพืช",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "วิจัยขั้นสูงด้านการปรับปรุงพันธุ์พืช สรีรวิทยาพืช เกษตรแม่นยำ และการเพิ่มผลผลิตพืชเศรษฐกิจภายใต้สภาพภูมิอากาศเปลี่ยนแปลง",
        "curriculum_highlights": ["การปรับปรุงพันธุ์พืชระดับโมเลกุล (Molecular Breeding)", "เทคโนโลยีการผลิตพืชแม่นยำและโรงเรือนอัจฉริยะ (Smart Greenhouse)", "สรีรวิทยาและความต้านทานความเครียดของพืช"],
        "career_paths": ["นักวิจัยปรับปรุงพันธุ์พืชอาวุโส", "ผู้เชี่ยวชาญการผลิตพืชในบริษัทเกษตรชั้นนำ", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Crop Science", "Plant Breeding", "Agriculture", "Ph.D."],
        "website_url": "https://iat.sut.ac.th"
    },
    {
        "id": "sut_agr_phd_animal_production",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีและนวัตกรรมทางสัตว์",
        "title_en": "Doctor of Philosophy Program in Animal Production Technology and Innovation",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีและนวัตกรรมทางสัตว์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Agricultural Technology",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร",
        "department": "School of Animal Technology and Innovation",
        "department_th": "สาขาวิชาเทคโนโลยีและนวัตกรรมทางสัตว์",
        "program_type": "ภาคปกติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "เน้นการวิจัยโภชนศาสตร์สัตว์ พันธุศาสตร์และการปรับปรุงพันธุ์สัตว์ สรีรวิทยาการสืบพันธุ์ และระบบฟาร์มปศุสัตว์อัจฉริยะ",
        "curriculum_highlights": ["โภชนศาสตร์สัตว์ขั้นสูงและสารเสริมชีวภาพ", "พันธุศาสตร์ระดับโมเลกุลและการคัดเลือกจีโนมิกส์ในปศุสัตว์", "สวัสดิภาพสัตว์และการจัดการฟาร์มลดการปล่อยคาร์บอน"],
        "career_paths": ["นักวิชาการสัตวบาลและโภชนาการสัตว์อาวุโส", "ผู้เชี่ยวชาญด้านเทคโนโลยีฟาร์มปศุสัตว์", "อาจารย์และนักวิจัย"],
        "tags": ["Animal Science", "Animal Production", "Genomics", "Ph.D."],
        "website_url": "https://iat.sut.ac.th"
    },
    {
        "id": "sut_agr_phd_biotechnology",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีชีวภาพการเกษตร",
        "title_en": "Doctor of Philosophy Program in Agricultural Biotechnology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีชีวภาพ)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Agricultural Technology",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร",
        "department": "School of Biotechnology",
        "department_th": "สาขาวิชาเทคโนโลยีชีวภาพ",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "การประยุกต์ใช้พันธุวิศวกรรม เทคโนโลยีการหมักขั้นสูง เอนไซม์วิทยา และชีววิทยาเชิงระบบเพื่อสร้างมูลค่าเพิ่มในภาคเกษตรและอุตสาหกรรมชีวภาพ",
        "curriculum_highlights": ["พันธุวิศวกรรมจุลินทรีย์และการสังเคราะห์ชีวภาพ (Synthetic Biology)", "เทคโนโลยีชีวภาพจุลินทรีย์สำหรับเกษตรและสิ่งแวดล้อม", "การผลิตโปรตีนทางเลือกและสารชีวภัณฑ์มูลค่าสูง"],
        "career_paths": ["นักวิจัยเทคโนโลยีชีวภาพและอุตสาหกรรมชีวภาพ", "ผู้เชี่ยวชาญด้านพันธุวิศวกรรม", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Biotechnology", "Agricultural Biotech", "Fermentation", "Ph.D."],
        "website_url": "https://iat.sut.ac.th"
    },
    {
        "id": "sut_agr_phd_food_tech",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีอาหาร",
        "title_en": "Doctor of Philosophy Program in Food Technology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีอาหาร)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Agricultural Technology",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร",
        "department": "School of Food Technology",
        "department_th": "สาขาวิชาเทคโนโลยีอาหาร",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท (ระบบไตรภาค)",
        "tuition_total": "324,000 บาท",
        "description": "มุ่งเน้นการวิจัยกระบวนการแปรรูปอาหารขั้นสูง เคมีและความปลอดภัยทางอาหาร สารอาหารเชิงหน้าที่ (Functional Food) และบรรจุภัณฑ์อัจฉริยะ",
        "curriculum_highlights": ["การพัฒนานวัตกรรมอาหารแห่งอนาคตและอาหารเพื่อสุขภาพ (Future Food)", "กระบวนการแปรรูปอาหารแบบไม่ใช้ความร้อนและเทคโนโลยีไมโครเอนแคปซูเลชัน", "การวิเคราะห์โครงสร้างอาหารระดับโมเลกุล"],
        "career_paths": ["นักวิจัยและพัฒนานวัตกรรมอาหาร (R&D Food Scientist)", "ผู้เชี่ยวชาญควบคุมคุณภาพและความปลอดภัยทางอาหาร", "อาจารย์มหาวิทยาลัย"],
        "tags": ["Food Technology", "Future Food", "Functional Food", "Ph.D."],
        "website_url": "https://iat.sut.ac.th"
    },
    # --- สำนักวิชาเทคโนโลยีสังคม & ศาสตร์และศิลป์ดิจิทัล ---
    {
        "id": "sut_soc_phd_management_tech",
        "title_th": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาเทคโนโลยีการจัดการ",
        "title_en": "Doctor of Philosophy Program in Management Technology",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (เทคโนโลยีการจัดการ)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Social Technology",
        "faculty_th": "สำนักวิชาเทคโนโลยีสังคม",
        "department": "School of Management Technology",
        "department_th": "สาขาวิชาเทคโนโลยีการจัดการ",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "3 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท (ระบบไตรภาค)",
        "tuition_total": "378,000 บาท",
        "description": "เน้นการวิจัยกลยุทธ์การจัดการนวัตกรรม โลจิสติกส์และโซ่อุปทานดิจิทัล การเปลี่ยนผ่านธุรกิจสู่ความยั่งยืน และการจัดการเทคโนโลยีสารสนเทศ",
        "curriculum_highlights": ["การจัดการนวัตกรรมและเทคโนโลยีเชิงกลยุทธ์", "การวิเคราะห์และออกแบบระบบโซ่อุปทานอัจฉริยะ (Smart Logistics)", "การสร้างโมเดลธุรกิจดิจิทัลและความยั่งยืน (ESG Business)"],
        "career_paths": ["ผู้บริหารระดับสูงด้านกลยุทธ์และนวัตกรรม", "ที่ปรึกษาธุรกิจและโลจิสติกส์", "อาจารย์และนักวิจัยด้านการจัดการ"],
        "tags": ["Management Technology", "Innovation Management", "Logistics", "Ph.D."],
        "website_url": "https://soctech.sut.ac.th"
    },
    {
        "id": "sut_soc_mba",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชาการจัดการเทคโนโลยีและนวัตกรรมธุรกิจ (MBA)",
        "title_en": "Master of Business Administration Program in Technology Management and Business Innovation",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Social Technology",
        "faculty_th": "สำนักวิชาเทคโนโลยีสังคม",
        "department": "School of Management Technology",
        "department_th": "สาขาวิชาเทคโนโลยีการจัดการ",
        "program_type": "ภาคปกติ / ภาคพิเศษ (วันเสาร์-อาทิตย์)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท (ระบบไตรภาค)",
        "tuition_total": "228,000 บาท",
        "description": "หลักสูตร MBA ยุคใหม่ที่ผสานความรู้ด้านการบริหารธุรกิจ การตลาดดิจิทัล การเงิน และการประยุกต์ใช้เทคโนโลยีเพื่อสร้างผู้ประกอบการและผู้นำองค์กร",
        "curriculum_highlights": ["การวางแผนกลยุทธ์ธุรกิจที่ขับเคลื่อนด้วยข้อมูล (Data-Driven Business Strategy)", "การเป็นผู้ประกอบการสตาร์ทอัพและการระดมทุน", "การจัดการโซ่อุปทานและการตลาดดิจิทัล"],
        "career_paths": ["ผู้บริหารฝ่ายพัฒนาธุรกิจและนวัตกรรม", "นักวิเคราะห์ธุรกิจและการเงิน", "ผู้ประกอบการสตาร์ทอัพ / เจ้าของธุรกิจส่วนตัว"],
        "tags": ["MBA", "Business Administration", "Innovation", "Management"],
        "website_url": "https://soctech.sut.ac.th"
    },
    {
        "id": "sut_das_bsc_applied_cs_ai",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และปัญญาประดิษฐ์ประยุกต์",
        "title_en": "Bachelor of Science Program in Applied Computer Science and Artificial Intelligence",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์และปัญญาประดิษฐ์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Digital Arts and Science",
        "faculty_th": "สำนักวิชาศาสตร์และศิลป์ดิจิทัล",
        "department": "Department of Computer Science and AI",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และ AI",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท (ระบบไตรภาค)",
        "tuition_total": "264,000 บาท",
        "description": "เน้นการสร้างนักพัฒนาระบบซอฟต์แวร์ วิศวกร AI และนักวิทยาศาสตร์ข้อมูลที่มีทักษะการเรียนรู้ของเครื่อง (Machine Learning), Deep Learning และ Generative AI",
        "curriculum_highlights": ["การพัฒนาแบบจำลอง AI, Machine Learning และ Deep Learning", "การพัฒนาซอฟต์แวร์ฟูลสแตกและระบบคลาวด์เนทีฟ (Cloud Native)", "โครงงานบูรณาการร่วมกับภาคอุตสาหกรรมและสหกิจศึกษา"],
        "career_paths": ["AI / Machine Learning Engineer", "Software Engineer / Full-Stack Developer", "Data Scientist", "System Architect"],
        "tags": ["Computer Science", "Artificial Intelligence", "AI", "Machine Learning", "Software Engineer"],
        "website_url": "https://das.sut.ac.th"
    },
    {
        "id": "sut_das_msc_applied_cs_ai",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และปัญญาประดิษฐ์",
        "title_en": "Master of Science Program in Computer Science and Artificial Intelligence",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์และปัญญาประดิษฐ์)",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Digital Arts and Science",
        "faculty_th": "สำนักวิชาศาสตร์และศิลป์ดิจิทัล",
        "department": "Department of Computer Science and AI",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และ AI",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "34,000 บาท (ระบบไตรภาค)",
        "tuition_total": "204,000 บาท",
        "description": "การศึกษาวิจัยขั้นสูงด้านอัลกอริทึมปัญญาประดิษฐ์ การประมวลผลภาษาธรรมชาติ (NLP) การมองเห็นของคอมพิวเตอร์ (Computer Vision) และระบบคลาวด์อัจฉริยะ",
        "curriculum_highlights": ["การวิจัยขั้นสูงด้าน Deep Learning, NLP และ Generative Models", "ความมั่นคงปลอดภัยไซเบอร์และความเป็นส่วนตัวของข้อมูล", "การประยุกต์ใช้ AI ในภาคอุตสาหกรรมการผลิตและการแพทย์"],
        "career_paths": ["นักวิจัยและวิศวกร AI ขั้นสูง", "หัวหน้าทีมพัฒนาเทคโนโลยี (Tech Lead)", "อาจารย์และนักวิชาการคอมพิวเตอร์"],
        "tags": ["Computer Science", "Artificial Intelligence", "AI", "NLP", "Computer Vision"],
        "website_url": "https://das.sut.ac.th"
    },
]

def build_course_embedding_text(c: CourseDB) -> str:
    parts = [
        c.title_th or "",
        c.title_en or "",
        c.degree_level or "",
        c.degree_name or "",
        c.faculty_th or "",
        c.department_th or "",
        c.university_th or "",
        c.university or "",
        c.description or "",
        " ".join(c.curriculum_highlights) if c.curriculum_highlights else "",
        " ".join(c.career_paths) if c.career_paths else "",
        " ".join(c.tags) if c.tags else ""
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

def expand_and_standardize_sut():
    print("=========================================================")
    print("🚀 SUT FULL EXPANSION & STANDARDIZATION PIPELINE")
    print("=========================================================")
    
    db = SessionLocal()
    
    # ---------------------------------------------------------
    # STEP 1: CLEAN EXISTING SUT COURSES
    # ---------------------------------------------------------
    print("\n[1/3] ปรับปรุงข้อมูลหลักสูตรเดิมของ มทส. ให้เป็นภาษาไทยมาตรฐาน...")
    updated_existing_ids = set()
    for cid, fixes in SUT_EXISTING_FIXES.items():
        c = db.query(CourseDB).filter(CourseDB.id == cid).first()
        if c:
            for k, v in fixes.items():
                setattr(c, k, v)
            c.university_th = "มหาวิทยาลัยเทคโนโลยีสุรนารี"
            c.embedding_text = build_course_embedding_text(c)
            updated_existing_ids.add(c.id)
            
    db.commit()
    print(f"  -> ปรับปรุงหลักสูตรเดิมเสร็จสิ้น: {len(updated_existing_ids)} รายการ")
    
    # ---------------------------------------------------------
    # STEP 2: INSERT NEW SUT CURRICULA
    # ---------------------------------------------------------
    print("\n[2/3] เพิ่มหลักสูตรทางการใหม่ของ มทส. ครบทุกสำนักวิชา...")
    new_course_ids = set()
    for item in NEW_SUT_COURSES:
        existing = db.query(CourseDB).filter(CourseDB.id == item["id"]).first()
        if not existing:
            new_c = CourseDB(
                id=item["id"],
                title_th=item["title_th"],
                title_en=item["title_en"],
                degree_level=item["degree_level"],
                degree_name=item["degree_name"],
                university=item["university"],
                university_th=item["university_th"],
                faculty=item["faculty"],
                faculty_th=item["faculty_th"],
                department=item["department"],
                department_th=item["department_th"],
                program_type=item["program_type"],
                duration_years=item["duration_years"],
                total_credits=item["total_credits"],
                tuition_per_semester=item["tuition_per_semester"],
                tuition_total=item["tuition_total"],
                description=item["description"],
                curriculum_highlights=item["curriculum_highlights"],
                career_paths=item["career_paths"],
                tags=item["tags"],
                website_url=item["website_url"],
                embedding_text=""
            )
            new_c.embedding_text = build_course_embedding_text(new_c)
            db.add(new_c)
            new_course_ids.add(new_c.id)
            print(f"  -> Added: [{new_c.id}] {new_c.title_th} ({new_c.degree_level})")
        else:
            # Update existing
            for k, v in item.items():
                setattr(existing, k, v)
            existing.embedding_text = build_course_embedding_text(existing)
            new_course_ids.add(existing.id)
            
    db.commit()
    print(f"  -> เพิ่มและปรับปรุงหลักสูตรใหม่เสร็จสิ้น: {len(new_course_ids)} รายการ")
    
    # ---------------------------------------------------------
    # STEP 3: RECOMPUTE AI VECTOR EMBEDDINGS (768-DIM)
    # ---------------------------------------------------------
    all_sut_to_embed = list(updated_existing_ids.union(new_course_ids))
    print(f"\n[3/3] คำนวณและอัปเดต AI Vector Embeddings ({len(all_sut_to_embed)} รายการ)...")
    
    def fetch_sut_vec(cid):
        with SessionLocal() as s:
            obj = s.query(CourseDB).filter(CourseDB.id == cid).first()
            if obj and obj.embedding_text:
                vec = embedding_service.get_embedding(obj.embedding_text)
                return cid, vec
        return cid, None

    CHUNK = 20
    for i in range(0, len(all_sut_to_embed), CHUNK):
        batch = all_sut_to_embed[i:i+CHUNK]
        v_map = {}
        with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
            futs = {executor.submit(fetch_sut_vec, cid): cid for cid in batch}
            for fut in as_completed(futs):
                cid, vec = fut.result()
                if vec:
                    v_map[cid] = vec
        if v_map:
            with SessionLocal() as s:
                for cid, vec in v_map.items():
                    c_obj = s.query(CourseDB).filter(CourseDB.id == cid).first()
                    if c_obj:
                        c_obj.embedding = vec
                s.commit()
        print(f"     ความคืบหน้า: {min(i+CHUNK, len(all_sut_to_embed))}/{len(all_sut_to_embed)}")

    db.close()
    print("\n=========================================================")
    print("✅ การขยายและปรับปรุงข้อมูลหลักสูตร มทส. เสร็จสมบูรณ์เรียบร้อย 100%!")
    print("=========================================================")

if __name__ == "__main__":
    expand_and_standardize_sut()
