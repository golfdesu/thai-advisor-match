"""
Comprehensive Course Scraper & DB Seeder for Sukhothai Thammathirat Open University (STOU)
มหาวิทยาลัยสุโขทัยธรรมาธิราช (มสธ.)
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
logger = logging.getLogger("ScraperSTOU")

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

STOU_COURSES = [
    # --- School of Law ---
    {
        "id": "stou_law_llb",
        "title_th": "นิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ. (นิติศาสตร์)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Law",
        "faculty_th": "สาขาวิชานิติศาสตร์",
        "department": "Department of Law",
        "department_th": "แขนงวิชานิติศาสตร์",
        "program_type": "ระบบการศึกษาทางไกล (Online / Distance Learning)",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต (23 ชุดวิชา)",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "หลักสูตรนิติศาสตร์ระบบการศึกษาทางไกลอันดับหนึ่งของไทย เรียนรู้ด้วยตนเองผ่านชุดวิชาและสื่อผสมออนไลน์",
        "curriculum_highlights": ["Civil and Commercial Law Modules", "Criminal Law & Criminal Procedure Modules", "Administrative and Public Law Modules"],
        "career_paths": ["ทนายความ", "นิติกร", "ผู้พิพากษา", "พนักงานอัยการ", "ที่ปรึกษากฎหมาย"],
        "tags": ["Law", "Distance Learning", "E-learning", "STOU", "มสธ."],
        "website_url": "https://law.stou.ac.th"
    },
    {
        "id": "stou_law_llm",
        "title_th": "นิติศาสตรมหาบัณฑิต",
        "title_en": "Master of Laws Program (LL.M.)",
        "degree_level": "ปริญญาโท",
        "degree_name": "น.ม. (นิติศาสตร์)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Law",
        "faculty_th": "สาขาวิชานิติศาสตร์",
        "department": "Graduate Law Program",
        "department_th": "บัณฑิตศึกษานิติศาสตร์",
        "program_type": "ระบบทางไกล / บัณฑิตศึกษา",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "96,000 บาท",
        "description": "การศึกษากฎหมายขั้นสูงและการทำวิทยานิพนธ์/การค้นคว้าอิสระทางด้านกฎหมายมหาชน กฎหมายอาญา และกฎหมายธุรกิจ",
        "curriculum_highlights": ["Comparative Legal Systems", "Advanced Criminal Jurisprudence", "Public Governance Law"],
        "career_paths": ["ผู้เชี่ยวชาญด้านกฎหมายระดับสูง", "อาจารย์สอนกฎหมาย", "ผู้บริหารฝ่ายกฎหมาย"],
        "tags": ["Master Degree", "Law", "LLM", "Distance Learning", "STOU"],
        "website_url": "https://law.stou.ac.th"
    },

    # --- School of Management Science ---
    {
        "id": "stou_mgmt_acc",
        "title_th": "บัญชีบัณฑิต สาขาวิชาวิทยาการจัดการ",
        "title_en": "Bachelor of Accountancy Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บช.บ. (การบัญชี)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Management Science",
        "faculty_th": "สาขาวิชาวิทยาการจัดการ",
        "department": "Department of Accounting",
        "department_th": "แขนงวิชาการบัญชี",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "มาตรฐานวิชาชีพบัญชี การรายงานทางการเงิน การตรวจสอบบัญชี และระบบภาษีอากรตามเกณฑ์สภาวิชาชีพบัญชี",
        "curriculum_highlights": ["Financial & Cost Accounting Modules", "Auditing and Internal Control", "Taxation Law and Practice"],
        "career_paths": ["นักบัญชี", "ผู้ตรวจสอบบัญชี (CPA)", "ผู้ทำบัญชีอิสระ", "นักวิเคราะห์การเงิน"],
        "tags": ["Management", "Accounting", "Finance", "STOU"],
        "website_url": "https://managementsci.stou.ac.th"
    },
    {
        "id": "stou_mgmt_bba_general",
        "title_th": "บริหารธุรกิจบัณฑิต แขนงวิชาการจัดการ",
        "title_en": "Bachelor of Business Administration in Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การจัดการ)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Management Science",
        "faculty_th": "สาขาวิชาวิทยาการจัดการ",
        "department": "Department of Business Administration",
        "department_th": "แขนงวิชาบริหารธุรกิจ",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "การจัดการองค์การ การบริหารเชิงกลยุทธ์ การจัดการนวัตกรรม และการประกอบการธุรกิจขนาดย่อมและขนาดย่อม (SMEs)",
        "curriculum_highlights": ["Strategic Business Planning", "Operations and Project Management", "Leadership in Modern Organizations"],
        "career_paths": ["ผู้จัดการทั่วไป", "ผู้ประกอบการธุรกิจ", "เจ้าหน้าที่ฝ่ายบริหาร", "นักวิเคราะห์ธุรกิจ"],
        "tags": ["Management", "Business", "Entrepreneurship", "STOU"],
        "website_url": "https://managementsci.stou.ac.th"
    },
    {
        "id": "stou_mgmt_bba_marketing",
        "title_th": "บริหารธุรกิจบัณฑิต แขนงวิชาการตลาด",
        "title_en": "Bachelor of Business Administration in Marketing",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาด)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Management Science",
        "faculty_th": "สาขาวิชาวิทยาการจัดการ",
        "department": "Department of Business Administration",
        "department_th": "แขนงวิชาบริหารธุรกิจ",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "กลยุทธ์การตลาด การตลาดดิจิทัล การวิจัยตลาด และพฤติกรรมผู้บริโภคยุคดิจิทัล",
        "curriculum_highlights": ["Digital Marketing & E-Commerce", "Market Research & Analysis", "Consumer Behavior & CRM"],
        "career_paths": ["นักการตลาดดิจิทัล", "ผู้จัดการฝ่ายขายและการตลาด", "นักวางแผนโฆษณา", "นักวิจัยตลาด"],
        "tags": ["Marketing", "Digital Marketing", "Business", "STOU"],
        "website_url": "https://managementsci.stou.ac.th"
    },
    {
        "id": "stou_mgmt_pa",
        "title_th": "รัฐประศาสนศาสตรบัณฑิต",
        "title_en": "Bachelor of Public Administration Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "รป.บ. (รัฐประศาสนศาสตร์)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Management Science",
        "faculty_th": "สาขาวิชาวิทยาการจัดการ",
        "department": "Department of Public Administration",
        "department_th": "แขนงวิชารัฐประศาสนศาสตร์",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "การบริหารงานภาครัฐ นโยบายสาธารณะ การบริหารงานคลังและงบประมาณ และการบริหารทรัพยากรบุคคลภาครัฐ",
        "curriculum_highlights": ["Public Policy & Implementation", "Public Sector Human Capital Management", "Local Governance Administration"],
        "career_paths": ["ข้าราชการพลเรือน", "ปลัด อบต. / เทศบาล", "นักวิเคราะห์นโยบายและแผน", "เจ้าหน้าที่ฝ่ายทรัพยากรบุคคลภาครัฐ"],
        "tags": ["Public Administration", "Management", "Civil Service", "STOU"],
        "website_url": "https://managementsci.stou.ac.th"
    },
    {
        "id": "stou_mgmt_mba",
        "title_th": "บริหารธุรกิจมหาบัณฑิต",
        "title_en": "Master of Business Administration Program (MBA)",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (บริหารธุรกิจ)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Management Science",
        "faculty_th": "สาขาวิชาวิทยาการจัดการ",
        "department": "Graduate Business Program",
        "department_th": "บัณฑิตศึกษาบริหารธุรกิจ",
        "program_type": "ระบบการศึกษาทางไกล / บัณฑิตศึกษา",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "100,000 บาท",
        "description": "พัฒนาศักยภาพผู้บริหารระดับสูง การวางแผนกลยุทธ์เชิงแข่งขัน การเงินธุรกิจ และนวัตกรรมองค์กร",
        "curriculum_highlights": ["Strategic Management Seminar", "Corporate Financial Strategy", "Global Business Leadership"],
        "career_paths": ["ผู้บริหารระดับสูง", "ที่ปรึกษาธุรกิจ", "ผู้จัดการทั่วไป", "เจ้าของธุรกิจ"],
        "tags": ["Master Degree", "MBA", "Business", "Leadership", "STOU"],
        "website_url": "https://managementsci.stou.ac.th"
    },

    # --- School of Political Science ---
    {
        "id": "stou_pol_gov",
        "title_th": "รัฐศาสตรบัณฑิต แขนงวิชาการเมืองการปกครอง",
        "title_en": "Bachelor of Political Science in Politics and Governance",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (การเมืองการปกครอง)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Political Science",
        "faculty_th": "สาขาวิชารัฐศาสตร์",
        "department": "Department of Politics and Government",
        "department_th": "แขนงวิชาการเมืองการปกครอง",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "ทฤษฎีการเมือง การปกครองเปรียบเทียบ สถาบันการเมือง และกระบวนการทางการเมืองของไทยและสากล",
        "curriculum_highlights": ["Comparative Political Institutions", "Thai Politics and Democratic Transition", "Political Theory and Governance"],
        "career_paths": ["นักวิชาการรัฐศาสตร์", "นักการเมือง / ผู้ช่วย ส.ส.", "เจ้าหน้าที่ปกครอง", "นักวิเคราะห์สถานการณ์การเมือง"],
        "tags": ["Political Science", "Politics", "Government", "STOU"],
        "website_url": "https://polsci.stou.ac.th"
    },
    {
        "id": "stou_pol_ir",
        "title_th": "รัฐศาสตรบัณฑิต แขนงวิชาความสัมพันธ์ระหว่างประเทศและการเมืองการปกครองเปรียบเทียบ",
        "title_en": "Bachelor of Political Science in International Relations and Comparative Politics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ร.บ. (ความสัมพันธ์ระหว่างประเทศฯ)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Political Science",
        "faculty_th": "สาขาวิชารัฐศาสตร์",
        "department": "Department of International Relations",
        "department_th": "แขนงวิชาความสัมพันธ์ระหว่างประเทศ",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "การทูต การเมืองระหว่างประเทศ องค์การระหว่างประเทศ และความมั่นคงร่วมสมัยในบริบทอาเซียนและโลก",
        "curriculum_highlights": ["Diplomacy & International Law", "ASEAN Studies & Regional Integration", "Global Security & Conflict Management"],
        "career_paths": ["นักการทูต", "เจ้าหน้าที่วิเทศสัมพันธ์", "นักวิเคราะห์ข่าวต่างประเทศ", "เจ้าหน้าที่องค์กรพัฒนาเอกชนระหว่างประเทศ"],
        "tags": ["Political Science", "International Relations", "Diplomacy", "STOU"],
        "website_url": "https://polsci.stou.ac.th"
    },

    # --- School of Communication Arts ---
    {
        "id": "stou_comm_arts",
        "title_th": "นิเทศศาสตรบัณฑิต",
        "title_en": "Bachelor of Communication Arts Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "นศ.บ. (นิเทศศาสตร์)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Communication Arts",
        "faculty_th": "สาขาวิชานิเทศศาสตร์",
        "department": "Department of Communication Arts",
        "department_th": "แขนงวิชานิเทศศาสตร์",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "การผลิตสื่อดิจิทัล การสื่อสารองค์กร การประชาสัมพันธ์ การโฆษณา และการสื่อสารการตลาดแบบบูรณาการ",
        "curriculum_highlights": ["Digital Media Production", "Strategic Public Relations & Advertising", "Corporate Communication in Digital Era"],
        "career_paths": ["นักประชาสัมพันธ์ (PR)", "นักสร้างสรรค์เนื้อหา (Content Creator)", "เจ้าหน้าที่สื่อสารองค์กร", "นักวางแผนกลยุทธ์สื่อ"],
        "tags": ["Communication Arts", "Digital Media", "PR", "Advertising", "STOU"],
        "website_url": "https://commarts.stou.ac.th"
    },

    # --- School of Liberal Arts ---
    {
        "id": "stou_arts_eng",
        "title_th": "ศิลปศาสตรบัณฑิต แขนงวิชาภาษาอังกฤษเพื่ออาชีพ",
        "title_en": "Bachelor of Arts in English for Careers",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ภาษาอังกฤษเพื่ออาชีพ)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Liberal Arts",
        "faculty_th": "สาขาวิชาศิลปศาสตร์",
        "department": "Department of English",
        "department_th": "แขนงวิชาภาษาอังกฤษ",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "ภาษาอังกฤษเชิงวิชาชีพ การสื่อสารในที่ทำงาน การแปลเอกสารธุรกิจ และการเจรจาต่อรองข้ามวัฒนธรรม",
        "curriculum_highlights": ["English for Business Communication", "Professional Translation Techniques", "Intercultural Communication at Work"],
        "career_paths": ["นักแปลภาษา", "เจ้าหน้าที่ติดต่อประสานงานต่างประเทศ", "พนักงานต้อนรับและการโรงแรม", "เลขาผู้บริหาร"],
        "tags": ["Liberal Arts", "English", "Translation", "Career", "STOU"],
        "website_url": "https://libarts.stou.ac.th"
    },
    {
        "id": "stou_arts_info",
        "title_th": "ศิลปศาสตรบัณฑิต แขนงวิชาสารสนเทศศาสตร์",
        "title_en": "Bachelor of Arts in Information Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (สารสนเทศศาสตร์)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Liberal Arts",
        "faculty_th": "สาขาวิชาศิลปศาสตร์",
        "department": "Department of Information Science",
        "department_th": "แขนงวิชาสารสนเทศศาสตร์",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "การจัดการสารสนเทศดิจิทัล การจัดการความรู้ (Knowledge Management) ระบบห้องสมุดดิจิทัล และคลังข้อมูลสารสนเทศ",
        "curriculum_highlights": ["Digital Information & Knowledge Management", "Information Architecture & Metadata", "Database and Digital Archiving"],
        "career_paths": ["นักสารสนเทศ", "ผู้จัดการความรู้ (KM Officer)", "บรรณารักษ์ดิจิทัล", "เจ้าหน้าที่จัดการเอกสารและข้อมูลอิเล็กทรอนิกส์"],
        "tags": ["Information Science", "Knowledge Management", "Digital Library", "STOU"],
        "website_url": "https://libarts.stou.ac.th"
    },

    # --- School of Educational Studies ---
    {
        "id": "stou_edu_m_admin",
        "title_th": "ศึกษาศาสตรมหาบัณฑิต แขนงวิชาการบริหารการศึกษา",
        "title_en": "Master of Education in Educational Administration",
        "degree_level": "ปริญญาโท",
        "degree_name": "ศษ.ม. (การบริหารการศึกษา)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Educational Studies",
        "faculty_th": "สาขาวิชาศึกษาศาสตร์",
        "department": "Department of Educational Administration",
        "department_th": "แขนงวิชาการบริหารการศึกษา",
        "program_type": "ระบบการศึกษาทางไกล / บัณฑิตศึกษา",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "96,000 บาท",
        "description": "หลักสูตรยอดนิยมสำหรับผู้บริหารสถานศึกษา พัฒนาภาวะผู้นำทางวิชาการ การบริหารการศึกษาเชิงยุทธศาสตร์ และการประกันคุณภาพ",
        "curriculum_highlights": ["Strategic Educational Leadership", "School Law and Policy Analysis", "Educational Quality Assurance"],
        "career_paths": ["ผู้อำนวยการโรงเรียน", "รองผู้อำนวยการโรงเรียน", "ศึกษานิเทศก์", "ผู้บริหารการศึกษาในระดับเขตพื้นที่"],
        "tags": ["Master Degree", "Education", "Educational Administration", "Leadership", "STOU"],
        "website_url": "https://edstudies.stou.ac.th"
    },
    {
        "id": "stou_edu_m_curriculum",
        "title_th": "ศึกษาศาสตรมหาบัณฑิต แขนงวิชาหลักสูตรและการสอน",
        "title_en": "Master of Education in Curriculum and Instruction",
        "degree_level": "ปริญญาโท",
        "degree_name": "ศษ.ม. (หลักสูตรและการสอน)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Educational Studies",
        "faculty_th": "สาขาวิชาศึกษาศาสตร์",
        "department": "Department of Curriculum and Instruction",
        "department_th": "แขนงวิชาหลักสูตรและการสอน",
        "program_type": "ระบบการศึกษาทางไกล / บัณฑิตศึกษา",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "96,000 บาท",
        "description": "การพัฒนาหลักสูตรสมัยใหม่ นวัตกรรมการจัดการเรียนรู้ การวิจัยในชั้นเรียน และการประเมินผลการเรียนรู้เชิงสมรรถนะ",
        "curriculum_highlights": ["Curriculum Development & Evaluation", "Instructional Innovation & Learning Technologies", "Classroom Action Research"],
        "career_paths": ["ครูชำนาญการพิเศษ/เชี่ยวชาญ", "นักพัฒนาหลักสูตร", "ศึกษานิเทศก์", "นักวิชาการศึกษา"],
        "tags": ["Master Degree", "Education", "Curriculum", "Pedagogy", "STOU"],
        "website_url": "https://edstudies.stou.ac.th"
    },

    # --- School of Science and Technology ---
    {
        "id": "stou_sci_ict",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศและการสื่อสาร",
        "title_en": "Bachelor of Science in Information and Communication Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศและการสื่อสาร)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Science and Technology",
        "faculty_th": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Computer and Information Technology",
        "department_th": "แขนงวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,800 บาท",
        "tuition_total": "38,400 บาท",
        "description": "ระบบเครือข่ายและความมั่นคงปลอดภัยไซเบอร์ การพัฒนาเว็บและโมบายล์แอปพลิเคชัน และระบบคลาวด์",
        "curriculum_highlights": ["Network Engineering & Cybersecurity", "Web & Mobile Application Development", "Cloud Computing & Database Administration"],
        "career_paths": ["IT Support & Network Engineer", "Web Developer", "System Administrator", "Cybersecurity Analyst"],
        "tags": ["Science", "ICT", "Technology", "Cybersecurity", "STOU"],
        "website_url": "https://scitech.stou.ac.th"
    },
    {
        "id": "stou_sci_ind_tech",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีอุตสาหกรรม",
        "title_en": "Bachelor of Science Program in Industrial Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีอุตสาหกรรม)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Science and Technology",
        "faculty_th": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Industrial Technology",
        "department_th": "แขนงวิชาเทคโนโลยีอุตสาหกรรม",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,800 บาท",
        "tuition_total": "38,400 บาท",
        "description": "การจัดการการผลิตและการดำเนินงาน ระบบควบคุมอัตโนมัติในโรงงาน การควบคุมคุณภาพ และการจัดการพลังงาน",
        "curriculum_highlights": ["Production Planning & Control", "Industrial Automation & Robotics Basics", "Total Quality Management (TQM) & Six Sigma"],
        "career_paths": ["นักเทคโนโลยีอุตสาหกรรม", "ผู้ควบคุมกระบวนการผลิต", "เจ้าหน้าที่ควบคุมคุณภาพ (QC/QA)", "ผู้จัดการโรงงาน"],
        "tags": ["Science", "Industrial Technology", "Manufacturing", "Quality", "STOU"],
        "website_url": "https://scitech.stou.ac.th"
    },

    # --- School of Health Sciences ---
    {
        "id": "stou_health_pub",
        "title_th": "สาธารณสุขศาสตรบัณฑิต",
        "title_en": "Bachelor of Public Health Program",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ส.บ. (สาธารณสุขศาสตร์)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Health Sciences",
        "faculty_th": "สาขาวิชาวิทยาศาสตร์สุขภาพ",
        "department": "Department of Public Health",
        "department_th": "แขนงวิชาสาธารณสุขศาสตร์",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,800 บาท",
        "tuition_total": "38,400 บาท",
        "description": "การส่งเสริมสุขภาพ การป้องกันโรค ระบาดวิทยา การบริหารงานสาธารณสุข และการจัดการอนามัยสิ่งแวดล้อม",
        "curriculum_highlights": ["Community Health Management", "Epidemiology & Disease Surveillance", "Environmental & Occupational Health"],
        "career_paths": ["นักวิชาการสาธารณสุข", "เจ้าหน้าที่โรงพยาบาลส่งเสริมสุขภาพตำบล (รพ.สต.)", "นักระบาดวิทยาชุมชน"],
        "tags": ["Health Sciences", "Public Health", "Community Health", "STOU"],
        "website_url": "https://healthsci.stou.ac.th"
    },
    {
        "id": "stou_health_occhealth",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาอาชีวอนามัยและความปลอดภัย",
        "title_en": "Bachelor of Science in Occupational Health and Safety",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (อาชีวอนามัยและความปลอดภัย)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Health Sciences",
        "faculty_th": "สาขาวิชาวิทยาศาสตร์สุขภาพ",
        "department": "Department of Occupational Health",
        "department_th": "แขนงวิชาอาชีวอนามัยและความปลอดภัย",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "4,800 บาท",
        "tuition_total": "38,400 บาท",
        "description": "มาตรฐาน จป.วิชาชีพ: กฎหมายความปลอดภัย การประเมินความเสี่ยง สุขศาสตร์อุตสาหกรรม และการยศาสตร์ในโรงงาน",
        "curriculum_highlights": ["Industrial Hygiene & Risk Assessment", "Safety Law and Management Systems (ISO 45001)", "Ergonomics and Accident Prevention"],
        "career_paths": ["เจ้าหน้าที่ความปลอดภัยในการทำงานระดับวิชาชีพ (จป.วิชาชีพ)", "ผู้ตรวจประเมินระบบ ISO 45001", "ที่ปรึกษาด้านความปลอดภัย"],
        "tags": ["Health Sciences", "Occupational Health", "Safety", "จป.วิชาชีพ", "STOU"],
        "website_url": "https://healthsci.stou.ac.th"
    },

    # --- School of Agricultural Extension and Cooperatives ---
    {
        "id": "stou_agri_ext",
        "title_th": "เกษตรศาสตรบัณฑิต สาขาวิชาส่งเสริมการเกษตรและการจัดการนวัตกรรมเกษตร",
        "title_en": "Bachelor of Agriculture in Agricultural Extension and Agri-Innovation Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "กษ.บ. (ส่งเสริมการเกษตรฯ)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Agricultural Extension and Cooperatives",
        "faculty_th": "สาขาวิชาเกษตรศาสตร์และสหกรณ์",
        "department": "Department of Agricultural Extension",
        "department_th": "แขนงวิชาส่งเสริมการเกษตร",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,500 บาท",
        "tuition_total": "36,000 บาท",
        "description": "การส่งเสริมการเกษตรยุคใหม่ สมาร์ตฟาร์มมิ่ง การจัดการห่วงโซ่คุณค่าสินค้าเกษตร และธุรกิจเกษตรกรรม",
        "curriculum_highlights": ["Smart Farming & Agri-Tech", "Agricultural Value Chain & Marketing", "Extension Methodology & Community Engagement"],
        "career_paths": ["นักวิชาการส่งเสริมการเกษตร (เกษตรตำบล/อำเภอ)", "ผู้จัดการฟาร์มเกษตรอัจฉริยะ", "ผู้ประกอบการธุรกิจเกษตร"],
        "tags": ["Agriculture", "Smart Farm", "Agri-Tech", "Extension", "STOU"],
        "website_url": "https://agri.stou.ac.th"
    },

    # --- School of Human Ecology ---
    {
        "id": "stou_human_eco_food",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาโภชนาการและการจัดการอาหาร",
        "title_en": "Bachelor of Science in Food Nutrition and Management",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (โภชนาการและการจัดการอาหาร)",
        "university": "Sukhothai Thammathirat Open University",
        "university_th": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
        "faculty": "School of Human Ecology",
        "faculty_th": "สาขาวิชามนุษยนิเวศศาสตร์",
        "department": "Department of Food Nutrition",
        "department_th": "แขนงวิชาโภชนาการและการจัดการอาหาร",
        "program_type": "ระบบการศึกษาทางไกล",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "4,800 บาท",
        "tuition_total": "38,400 บาท",
        "description": "โภชนาการบำบัด การจัดบริการอาหารในโรงพยาบาลและสถาบัน การสุขาภิบาลอาหาร และการพัฒนาผลิตภัณฑ์อาหารเพื่อสุขภาพ",
        "curriculum_highlights": ["Clinical Nutrition & Diet Therapy", "Institutional Food Service Management", "Food Sanitation & Quality Systems (HACCP/GMP)"],
        "career_paths": ["นักโภชนาการ", "ผู้จัดการบริการอาหารในโรงพยาบาล/โรงแรม", "นักพัฒนาผลิตภัณฑ์อาหารเพื่อสุขภาพ"],
        "tags": ["Human Ecology", "Nutrition", "Food Management", "Diet", "STOU"],
        "website_url": "https://hec.stou.ac.th"
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
        for c in STOU_COURSES:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
        session.commit()
        logger.info(f"=== Successfully seeded Sukhothai Thammathirat Open University: {inserted} inserted, {updated} updated ===")
        return inserted + updated
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding STOU DB: {e}")
        return 0
    finally:
        session.close()

if __name__ == "__main__":
    count = seed_db()
    print(f"STOU courses processed: {count}")
