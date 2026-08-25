"""
Comprehensive Course Scraper & DB Seeder for Ramkhamhaeng University (RU)
มหาวิทยาลัยรามคำแหง
Schema: CourseDB(id, title_th, title_en, degree_level, degree_name, university, university_th, faculty, faculty_th, department, department_th, program_type, duration_years, total_credits, tuition_per_semester, tuition_total, description, curriculum_highlights, career_paths, tags, website_url)
"""
import os
import sys
import json
import logging
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ScraperRU")

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

RU_COURSES = [
    # --- Faculty of Law ---
    {
        "id": "ru_law_llb",
        "title_th": "นิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ. (นิติศาสตร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Department of Law",
        "department_th": "ภาควิชานิติศาสตร์",
        "program_type": "ภาคปกติ (ตลาดวิชา / Pre-degree)",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "หนึ่งในคณะนิติศาสตร์ชั้นนำของประเทศไทย ผลิตนักกฎหมาย ผู้พิพากษา อัยการ และทนายความจำนวนมากที่สุดในประเทศ",
        "curriculum_highlights": ["Civil and Commercial Code", "Criminal Law & Procedure", "Constitutional and Administrative Law"],
        "career_paths": ["ผู้พิพากษา", "พนักงานอัยการ", "ทนายความ", "นิติกรภาครัฐและเอกชน", "ที่ปรึกษากฎหมาย"],
        "tags": ["Law", "Legal Studies", "Judiciary", "Pre-degree", "RU", "Ramkhamhaeng"],
        "website_url": "https://www.law.ru.ac.th"
    },
    {
        "id": "ru_law_llm",
        "title_th": "นิติศาสตรมหาบัณฑิต",
        "title_en": "Master of Laws Program (LL.M.)",
        "degree_level": "ปริญญาโท",
        "degree_name": "น.ม. (นิติศาสตร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Graduate Program in Law",
        "department_th": "บัณฑิตศึกษานิติศาสตร์",
        "program_type": "ภาคพิเศษ / เสาร์-อาทิตย์",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "120,000 บาท",
        "description": "หลักสูตรระดับบัณฑิตศึกษาเฉพาะทางด้านกฎหมายมหาชน กฎหมายอาญา กฎหมายธุรกิจระหว่างประเทศ และกฎหมายการค้าภาษีอากร",
        "curriculum_highlights": ["International Trade Law", "Comparative Public Law", "Advanced Criminal Law Jurisprudence"],
        "career_paths": ["ผู้พิพากษาศาลชั้นอุทธรณ์/ฎีกา", "อัยการพิเศษ", "อาจารย์สอนกฎหมาย", "ที่ปรึกษากฎหมายธุรกิจข้ามชาติ"],
        "tags": ["Master Degree", "Law", "LLM", "RU"],
        "website_url": "https://www.law.ru.ac.th"
    },

    # --- Faculty of Business Administration ---
    {
        "id": "ru_bus_acc",
        "title_th": "บัญชีบัณฑิต สาขาวิชาการบัญชี",
        "title_en": "Bachelor of Accountancy Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ. (การบัญชี)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Accounting",
        "department_th": "ภาควิชาการบัญชี",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "มาตรฐานวิชาชีพบัญชี การสอบบัญชี ระบบสารสนเทศทางการบัญชี และการตรวจสอบภาษีอากร",
        "curriculum_highlights": ["Financial Accounting & Reporting", "Auditing & Assurance", "Tax Accounting & Planning"],
        "career_paths": ["ผู้สอบบัญชีรับอนุญาต (CPA)", "ผู้ตรวจสอบภายใน (CIA)", "สมุห์บัญชี", "ที่ปรึกษาภาษีอากร"],
        "tags": ["Accounting", "Finance", "Business", "CPA", "RU"],
        "website_url": "https://ba.ru.ac.th"
    },
    {
        "id": "ru_bus_fin",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการเงินและการธนาคาร",
        "title_en": "Bachelor of Business Administration in Finance and Banking",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การเงินและการธนาคาร)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Finance and Banking",
        "department_th": "ภาควิชาการเงินและการธนาคาร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "การจัดการการเงินองค์กร ตลาดการเงินและตราสารอนุพันธ์ การวิเคราะห์หลักทรัพย์และการจัดการพอร์ตการลงทุน",
        "curriculum_highlights": ["Corporate Finance", "Investment Analysis & Portfolio Management", "Financial Markets & Fintech"],
        "career_paths": ["นักวิเคราะห์หลักทรัพย์", "ผู้จัดการกองทุน", "เจ้าหน้าที่สินเชื่อสถาบันการเงิน", "นักวางแผนการเงิน (CFP)"],
        "tags": ["Finance", "Banking", "Investment", "Business", "RU"],
        "website_url": "https://ba.ru.ac.th"
    },
    {
        "id": "ru_bus_mkt",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการตลาด",
        "title_en": "Bachelor of Business Administration in Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาด)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Marketing",
        "department_th": "ภาควิชาการตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "กลยุทธ์การตลาดสมัยใหม่ การบริหารตราสินค้า พฤติกรรมผู้บริโภค และการตลาดดิจิทัล",
        "curriculum_highlights": ["Strategic Marketing Management", "Brand Building & Integrated Marketing", "Digital Consumer Behavior"],
        "career_paths": ["ผู้จัดการฝ่ายการตลาด", "นักวางแผนกลยุทธ์แบรนด์", "ผู้จัดการผลิตภัณฑ์ (Product Manager)", "นักสื่อสารการตลาด"],
        "tags": ["Marketing", "Branding", "Digital Marketing", "Business", "RU"],
        "website_url": "https://ba.ru.ac.th"
    },
    {
        "id": "ru_bus_mgmt",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการจัดการทั่วไป",
        "title_en": "Bachelor of Business Administration in General Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการทั่วไป)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Management",
        "department_th": "ภาควิชาการจัดการ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "การบริหารเชิงกลยุทธ์ การพัฒนาภาวะผู้นำ การจัดการการเปลี่ยนแปลง และการบริหารธุรกิจขนาดย่อม (SMEs)",
        "curriculum_highlights": ["Strategic Organization Management", "Leadership & Team Management", "SMEs Entrepreneurship"],
        "career_paths": ["ผู้จัดการทั่วไป", "ผู้บริหารฝ่ายปฏิบัติการ", "ผู้ประกอบการธุรกิจ", "เจ้าหน้าที่ฝ่ายพัฒนาธุรกิจ"],
        "tags": ["Management", "Leadership", "Business", "SMEs", "RU"],
        "website_url": "https://ba.ru.ac.th"
    },
    {
        "id": "ru_bus_logistics",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และซัพพลายเชน",
        "title_en": "Bachelor of Business Administration in Logistics and Supply Chain Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการโลจิสติกส์และซัพพลายเชน)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Logistics and Supply Chain",
        "department_th": "ภาควิชาการจัดการโลจิสติกส์และโซ่อุปทาน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "การขนส่ง การบริหารคลังสินค้า การจัดซื้อจัดหา และการบูรณาการระบบโซ่อุปทานระดับโลก",
        "curriculum_highlights": ["Warehouse & Inventory Management", "Transportation & Distribution Network", "Global Supply Chain Strategy"],
        "career_paths": ["นักวิเคราะห์โลจิสติกส์", "ผู้จัดการฝ่ายคลังสินค้าและการจัดส่ง", "เจ้าหน้าที่จัดซื้อระหว่างประเทศ", "ผู้ประสานงาน Freight Forwarder"],
        "tags": ["Logistics", "Supply Chain", "Business", "Transportation", "RU"],
        "website_url": "https://ba.ru.ac.th"
    },
    {
        "id": "ru_bus_mba",
        "title_th": "บริหารธุรกิจมหาบัณฑิต",
        "title_en": "Master of Business Administration Program (MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Business Administration",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Graduate School of Business",
        "department_th": "บัณฑิตศึกษาบริหารธุรกิจ",
        "program_type": "ภาคพิเศษ / ออนไลน์ / เสาร์-อาทิตย์",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "32,500 บาท",
        "tuition_total": "130,000 บาท",
        "description": "โครงการ MBA สำหรับผู้บริหารและนักศึกษาทั่วไป พัฒนาทักษะการตัดสินใจเชิงกลยุทธ์ การเงิน การตลาด และความเป็นผู้นำ",
        "curriculum_highlights": ["Executive Strategic Decision Making", "Corporate Financial Strategy", "Global Business Leadership"],
        "career_paths": ["ผู้บริหารระดับสูง (CEO, MD)", "ที่ปรึกษาธุรกิจ", "ผู้จัดการฝ่ายกลยุทธ์องค์กร"],
        "tags": ["Master Degree", "MBA", "Executive", "Business", "RU"],
        "website_url": "https://ba.ru.ac.th"
    },

    # --- Faculty of Political Science ---
    {
        "id": "ru_pol_gov",
        "title_th": "รัฐศาสตรบัณฑิต สาขาวิชาการปกครอง",
        "title_en": "Bachelor of Political Science in Politics and Government",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (การปกครอง)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Politics and Government",
        "department_th": "ภาควิชาการปกครอง",
        "program_type": "ภาคปกติ (ตลาดวิชา)",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "ทฤษฎีการเมือง การเมืองเปรียบเทียบ ระบบรัฐสภา และพรรคการเมืองและการเลือกตั้ง",
        "curriculum_highlights": ["Thai Politics & Constitutional History", "Comparative Political Systems", "Political Philosophy and Ideology"],
        "career_paths": ["นักการเมือง / ผู้ช่วย ส.ส.", "ปลัดอำเภอ", "นักวิชาการด้านรัฐศาสตร์", "เจ้าหน้าที่ฝ่ายความมั่นคง"],
        "tags": ["Political Science", "Government", "Politics", "RU"],
        "website_url": "https://www.pol.ru.ac.th"
    },
    {
        "id": "ru_pol_pa",
        "title_th": "รัฐศาสตรบัณฑิต สาขาวิชารัฐประศาสนศาสตร์",
        "title_en": "Bachelor of Political Science in Public Administration",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (รัฐประศาสนศาสตร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Public Administration",
        "department_th": "ภาควิชารัฐประศาสนศาสตร์",
        "program_type": "ภาคปกติ (ตลาดวิชา)",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "การบริหารงานภาครัฐ การจัดทำนโยบายสาธารณะ การบริหารงบประมาณ และการบริหารทรัพยากรบุคคลภาครัฐ",
        "curriculum_highlights": ["Public Policy Formulation & Analysis", "Public Personnel Administration", "Local Administration Management"],
        "career_paths": ["ปลัดอำเภอ", "เจ้าพนักงานปกครอง", "นักวิเคราะห์นโยบายและแผน", "ข้าราชการ ก.พ."],
        "tags": ["Political Science", "Public Administration", "Civil Service", "RU"],
        "website_url": "https://www.pol.ru.ac.th"
    },
    {
        "id": "ru_pol_ir",
        "title_th": "รัฐศาสตรบัณฑิต สาขาวิชาความสัมพันธ์ระหว่างประเทศ",
        "title_en": "Bachelor of Political Science in International Relations",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (ความสัมพันธ์ระหว่างประเทศ)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of International Relations",
        "department_th": "ภาควิชาความสัมพันธ์ระหว่างประเทศ",
        "program_type": "ภาคปกติ (ตลาดวิชา)",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "การเมืองระหว่างประเทศ กฎหมายระหว่างประเทศ องค์การระหว่างประเทศ และนโยบายต่างประเทศของมหาอำนาจ",
        "curriculum_highlights": ["International Relations Theory", "Foreign Policy of Major Powers", "International Organizations (UN, ASEAN)"],
        "career_paths": ["นักการทูต (กระทรวงการต่างประเทศ)", "เจ้าหน้าที่องค์กรระหว่างประเทศ", "นักวิเคราะห์ข่าวต่างประเทศ"],
        "tags": ["Political Science", "International Relations", "Diplomacy", "RU"],
        "website_url": "https://www.pol.ru.ac.th"
    },

    # --- Faculty of Humanities ---
    {
        "id": "ru_human_eng",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาภาษาอังกฤษ",
        "title_en": "Bachelor of Arts Program in English",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาอังกฤษ)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Humanities",
        "faculty_th": "คณะมนุษยศาสตร์",
        "department": "Department of Western Languages",
        "department_th": "ภาควิชาภาษาตะวันตก",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "ทักษะภาษาอังกฤษเพื่อการสื่อสารระดับสูง การแปล การเขียนเชิงวิชาการ และวรรณคดีอังกฤษ-อเมริกัน",
        "curriculum_highlights": ["Advanced English Composition", "English-Thai Translation Techniques", "English for International Business"],
        "career_paths": ["นักแปลและล่าม", "พนักงานต้อนรับบนเครื่องบิน", "เจ้าหน้าที่วิเทศสัมพันธ์", "นักวิชาการด้านภาษา"],
        "tags": ["Humanities", "English", "Translation", "Language", "RU"],
        "website_url": "https://www.human.ru.ac.th"
    },
    {
        "id": "ru_human_psych",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาจิตวิทยา",
        "title_en": "Bachelor of Science Program in Psychology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (จิตวิทยา)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Humanities",
        "faculty_th": "คณะมนุษยศาสตร์",
        "department": "Department of Psychology",
        "department_th": "ภาควิชาจิตวิทยา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "1,600 บาท",
        "tuition_total": "12,800 บาท",
        "description": "จิตวิทยาคลินิก จิตวิทยาการปรึกษา และจิตวิทยาอุตสาหกรรมและองค์การเพื่อพัฒนาศักยภาพมนุษย์",
        "curriculum_highlights": ["Clinical Psychology & Assessment", "Counseling Techniques & Therapy", "Industrial & Organizational Psychology"],
        "career_paths": ["นักจิตวิทยาคลินิก", "นักจิตวิทยาการปรึกษา", "เจ้าหน้าที่ฝ่ายทรัพยากรบุคคล (HRD)", "ผู้เชี่ยวชาญด้านพฤติกรรมองค์กร"],
        "tags": ["Humanities", "Psychology", "Clinical", "Counseling", "RU"],
        "website_url": "https://www.human.ru.ac.th"
    },
    {
        "id": "ru_human_chinese",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาภาษาจีน",
        "title_en": "Bachelor of Arts Program in Chinese",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาจีน)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Humanities",
        "faculty_th": "คณะมนุษยศาสตร์",
        "department": "Department of Eastern Languages",
        "department_th": "ภาควิชาภาษาตะวันออก",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,500 บาท",
        "tuition_total": "12,000 บาท",
        "description": "ภาษาจีนมาตรฐาน (Mandarin) ไวยากรณ์ การแปล และภาษาจีนเชิงธุรกิจสำหรับการค้าไทย-จีน",
        "curriculum_highlights": ["Advanced Chinese Grammar & Syntax", "Business Chinese for Import-Export", "Chinese-Thai Translation & Interpretation"],
        "career_paths": ["ล่ามภาษาจีน", "เจ้าหน้าที่ประสานงานธุรกิจไทย-จีน", "มัคคุเทศก์", "พนักงานบริษัทข้ามชาติจีน"],
        "tags": ["Humanities", "Chinese", "Mandarin", "Language", "RU"],
        "website_url": "https://www.human.ru.ac.th"
    },

    # --- Faculty of Science ---
    {
        "id": "ru_sci_cs",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "1,800 บาท",
        "tuition_total": "14,400 บาท",
        "description": "โครงสร้างข้อมูล อัลกอริทึม ระบบฐานข้อมูล ปัญญาประดิษฐ์ และการพัฒนาซอฟต์แวร์ระดับองค์กร",
        "curriculum_highlights": ["Data Structures & Algorithms", "Database Systems Design", "Artificial Intelligence & Software Engineering"],
        "career_paths": ["Software Developer", "Backend/Frontend Developer", "Database Administrator", "System Analyst"],
        "tags": ["Science", "Computer Science", "Software", "Programming", "RU"],
        "website_url": "https://www.sci.ru.ac.th"
    },
    {
        "id": "ru_sci_ds",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาสถิติศาสตร์และวิทยาการข้อมูล",
        "title_en": "Bachelor of Science in Statistics and Data Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (สถิติศาสตร์และวิทยาการข้อมูล)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Statistics",
        "department_th": "ภาควิชาสถิติ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "1,800 บาท",
        "tuition_total": "14,400 บาท",
        "description": "การวิเคราะห์สถิติประยุกต์ การสร้างแบบจำลองพยากรณ์ การเรียนรู้ของเครื่อง (Machine Learning) และการวิเคราะห์ข้อมูลขนาดใหญ่",
        "curriculum_highlights": ["Applied Statistical Modeling", "Machine Learning with Python/R", "Big Data Analytics & BI"],
        "career_paths": ["Data Analyst", "Data Scientist", "Statistician", "Business Intelligence Analyst"],
        "tags": ["Science", "Data Science", "Statistics", "Machine Learning", "RU"],
        "website_url": "https://www.sci.ru.ac.th"
    },

    # --- Faculty of Mass Communication Technology ---
    {
        "id": "ru_mass_comm",
        "title_th": "นิเทศศาสตรบัณฑิต สาขาวิชานิเทศศาสตร์และสื่อดิจิทัล",
        "title_en": "Bachelor of Communication Arts in Digital Media and Communication",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (นิเทศศาสตร์และสื่อดิจิทัล)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Mass Communication Technology",
        "faculty_th": "คณะสื่อสารมวลชน",
        "department": "Department of Mass Communication",
        "department_th": "ภาควิชาการสื่อสารมวลชน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "1,600 บาท",
        "tuition_total": "12,800 บาท",
        "description": "การผลิตสื่อดิจิทัล วารสารศาสตร์ออนไลน์ การผลิตรายการวิทยุโทรทัศน์ และการประชาสัมพันธ์เชิงกลยุทธ์",
        "curriculum_highlights": ["Digital Video Production & Editing", "Online Journalism & Storytelling", "Strategic PR and Corporate Communication"],
        "career_paths": ["Content Creator", "นักข่าวและผู้ประกาศ", "ผู้กำกับรายการและตัดต่อสื่อดิจิทัล", "นักประชาสัมพันธ์ (PR)"],
        "tags": ["Mass Communication", "Digital Media", "Journalism", "Content Creator", "RU"],
        "website_url": "https://mac.ru.ac.th"
    },

    # --- Faculty of Engineering ---
    {
        "id": "ru_eng_civil",
        "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธา",
        "title_en": "Bachelor of Engineering Program in Civil Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมโยธา)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "144 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "การออกแบบโครงสร้าง คอนกรีตเสริมเหล็ก การสำรวจ วิศวกรรมปฐพี และการบริหารงานก่อสร้าง",
        "curriculum_highlights": ["Structural Analysis & Reinforced Concrete", "Geotechnical & Soil Mechanics", "Construction Project Management"],
        "career_paths": ["วิศวกรโยธา", "วิศวกรโครงสร้าง", "ผู้จัดการโครงการก่อสร้าง", "วิศวกรควบคุมงาน"],
        "tags": ["Engineering", "Civil Engineering", "Construction", "RU"],
        "website_url": "https://eng.ru.ac.th"
    },
    {
        "id": "ru_eng_comp",
        "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "สถาปัตยกรรมคอมพิวเตอร์ ระบบสมองกลฝังตัว (Embedded Systems) เครือข่ายคอมพิวเตอร์ และอินเทอร์เน็ตของสรรพสิ่ง (IoT)",
        "curriculum_highlights": ["Embedded Systems & Microcontrollers", "Computer Network & Cybersecurity", "IoT Architecture & Cloud Integration"],
        "career_paths": ["Computer Engineer", "Embedded Systems Engineer", "Network Engineer", "IoT Solutions Architect"],
        "tags": ["Engineering", "Computer Engineering", "IoT", "Hardware", "RU"],
        "website_url": "https://eng.ru.ac.th"
    },

    # --- Faculty of Optometry ---
    {
        "id": "ru_opto_od",
        "title_th": "ทัศนมาตรศาสตรบัณฑิต",
        "title_en": "Doctor of Optometry Program (O.D.)",
        "degree_level": "ปริญญาตรี (หลักสูตรวิชาชีพ 6 ปี)",
        "degree_name": "ทศ.บ. (ทัศนมาตรศาสตร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Optometry",
        "faculty_th": "คณะทัศนมาตรศาสตร์",
        "department": "Department of Optometry",
        "department_th": "ภาควิชาทัศนมาตรศาสตร์",
        "program_type": "ภาคปกติ (หลักสูตร 6 ปี)",
        "duration_years": "6 ปี",
        "total_credits": "218 หน่วยกิต",
        "tuition_per_semester": "50,000 บาท",
        "tuition_total": "600,000 บาท",
        "description": "คณะทัศนมาตรศาสตร์แห่งแรกของประเทศไทย ตรวจวินิจฉัยและแก้ไขปัญหาสายตา เลนส์สัมผัส และฟื้นฟูระบบการมองเห็น",
        "curriculum_highlights": ["Ocular Anatomy & Pathology", "Clinical Refraction & Contact Lens", "Pediatric & Geriatric Optometry Clinical Practicum"],
        "career_paths": ["นักทัศนมาตรวิชาชีพ (Optometrist)", "ผู้เชี่ยวชาญด้านเลนส์และสายตา", "เจ้าของศูนย์ทัศนมาตรและคลินิกสายตา"],
        "tags": ["Optometry", "Eye Care", "Health Science", "Medical", "RU"],
        "website_url": "https://optometry.ru.ac.th"
    },

    # --- Faculty of Public Health ---
    {
        "id": "ru_pub_health",
        "title_th": "สาธารณสุขศาสตรบัณฑิต สาขาวิชาสาธารณสุขศาสตร์",
        "title_en": "Bachelor of Public Health Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ส.บ. (สาธารณสุขศาสตร์)",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Department of Public Health",
        "department_th": "ภาควิชาสาธารณสุขศาสตร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "12,000 บาท",
        "tuition_total": "96,000 บาท",
        "description": "การส่งเสริมสุขภาพ การป้องกันโรค อาชีวอนามัยและความปลอดภัย และการบริหารระบบสุขภาพชุมชน",
        "curriculum_highlights": ["Community Health Assessment", "Occupational Health and Safety", "Health Economics & Policy"],
        "career_paths": ["นักวิชาการสาธารณสุข", "เจ้าหน้าที่ความปลอดภัยในการทำงาน (จป.วิชาชีพ)", "นักเวชสถิติ"],
        "tags": ["Public Health", "Health", "Occupational Safety", "RU"],
        "website_url": "https://publichealth.ru.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE:
        logger.error("Database connection not available. Skipping DB commit.")
        return 0

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    try:
        for c in RU_COURSES:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
        session.commit()
        logger.info(f"=== Successfully seeded Ramkhamhaeng University: {inserted} inserted, {updated} updated ===")
        return inserted + updated
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding Ramkhamhaeng University DB: {e}")
        return 0
    finally:
        session.close()

if __name__ == "__main__":
    count = seed_db()
    print(f"RU courses processed: {count}")
