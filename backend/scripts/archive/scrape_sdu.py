"""
Comprehensive Scraper and Course Data Pipeline for Suan Dusit University (SDU)
มหาวิทยาลัยสวนดุสิต
"""
import sys
import os
import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.db_models import CourseDB
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SDU_Scraper")

SDU_COURSES = [
    # โรงเรียนการเรือน (School of Culinary Arts & Culinary Technology)
    {
        "id": "sdu_culinary_tech",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีการประกอบอาหารและการบริการ",
        "title_en": "Bachelor of Science in Culinary Arts and Service Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีการประกอบอาหารและการบริการ)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "School of Culinary Arts",
        "faculty_th": "โรงเรียนการเรือน",
        "department": "Culinary Arts and Service Technology",
        "department_th": "สาขาวิชาเทคโนโลยีการประกอบอาหารและการบริการ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "208,000 บาท",
        "description": "หลักสูตรระดับแนวหน้าของประเทศด้านศิลปะการประกอบอาหารไทยและสากล วิทยาศาสตร์อาหาร การจัดการครัวมาตรฐานสากล และการบริการอาหารและเครื่องดื่ม",
        "curriculum_highlights": ["Thai & Western Culinary Arts", "Bakery & Pastry Masterclass", "Kitchen & Food Service Management", "Food Safety & Sanitation (HACCP)", "Menu Planning & Cost Control"],
        "career_paths": ["Chef / Executive Chef", "Food & Beverage Manager", "ผู้ประกอบการธุรกิจอาหารและเบเกอรี่", "Food Stylist", "นักพัฒนาผลิตภัณฑ์อาหาร"],
        "tags": ["Culinary Arts", "Chef", "Food Science", "Hospitality", "สวนดุสิต"],
        "website_url": "https://culinary.dusit.ac.th"
    },
    {
        "id": "sdu_culinary_nutrition",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาโภชนาการและการประกอบอาหาร",
        "title_en": "Bachelor of Science in Nutrition and Culinary Arts",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (โภชนาการและการประกอบอาหาร)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "School of Culinary Arts",
        "faculty_th": "โรงเรียนการเรือน",
        "department": "Nutrition and Culinary Arts",
        "department_th": "สาขาวิชาโภชนาการและการประกอบอาหาร",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "บูรณาการศาสตร์ด้านโภชนาการ การกำหนดอาหารเพื่อสุขภาพ และทักษะการประกอบอาหารบำบัดโรคสำหรับโรงพยาบาลและศูนย์เวลเนส",
        "curriculum_highlights": ["Clinical Nutrition & Dietetics", "Nutritional Assessment", "Medical & Wellness Food Preparation", "Food Chemistry & Microbiology"],
        "career_paths": ["นักกำหนดอาหาร (Dietitian)", "นักโภชนาการโรงพยาบาล", "ที่ปรึกษาโภชนาการศูนย์เวลเนส", "ผู้พัฒนาสูตรอาหารสุขภาพ"],
        "tags": ["Nutrition", "Dietetics", "Healthcare", "Culinary", "Wellness"],
        "website_url": "https://culinary.dusit.ac.th"
    },

    # โรงเรียนการท่องเที่ยวและการบริการ (School of Tourism and Hospitality Management)
    {
        "id": "sdu_aviation_biz",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาธุรกิจการบิน",
        "title_en": "Bachelor of Arts in Aviation Business",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ธุรกิจการบิน)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "School of Tourism and Hospitality Management",
        "faculty_th": "โรงเรียนการท่องเที่ยวและการบริการ",
        "department": "Aviation Business",
        "department_th": "สาขาวิชาธุรกิจการบิน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "224,000 บาท",
        "description": "ฝึกอบรมทักษะงานบริการการบินระดับมืออาชีพ ทั้งงานบริการบนเครื่องบิน (Cabin Crew) และงานบริการภาคพื้นดิน (Ground Services) พร้อมห้องปฏิบัติการจำลองเครื่องบินมาตรฐาน",
        "curriculum_highlights": ["In-Flight Passenger Services & Safety", "Airport Ground Handling Operations", "Airline Passenger Reservation Systems (Amadeus/Sabre)", "Aviation English & Grooming"],
        "career_paths": ["พนักงานต้อนรับบนเครื่องบิน (Flight Attendant)", "เจ้าหน้าที่บริการภาคพื้นดิน (Ground Staff)", "เจ้าหน้าที่สำรองที่นั่งสายการบิน", "เจ้าหน้าที่อำนวยการบิน (Flight Dispatcher)"],
        "tags": ["Aviation", "Cabin Crew", "Airline Business", "Hospitality", "Tourism"],
        "website_url": "https://tourism.dusit.ac.th"
    },
    {
        "id": "sdu_hotel_biz",
        "title_th": "ศิลปศาสตรบัณฑิต สาขาวิชาธุรกิจโรงแรม",
        "title_en": "Bachelor of Arts in Hotel Business",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (ธุรกิจโรงแรม)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "School of Tourism and Hospitality Management",
        "faculty_th": "โรงเรียนการท่องเที่ยวและการบริการ",
        "department": "Hotel Business",
        "department_th": "สาขาวิชาธุรกิจโรงแรม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "176,000 บาท",
        "description": "เรียนรู้การบริหารงานโรงแรม รีสอร์ท งานบริการส่วนหน้า งานแม่บ้าน และการจัดการงานจัดเลี้ยงมาตรฐานระดับสากล",
        "curriculum_highlights": ["Front Office Operations & Property Management Systems", "Housekeeping Management", "Food & Beverage Service Excellence", "Hotel Revenue Management"],
        "career_paths": ["ผู้จัดการแผนกต้อนรับส่วนหน้า", "ผู้จัดการแผนกอาหารและเครื่องดื่ม", "ผู้บริหารงานโรงแรมและรีสอร์ท", "ผู้ประสานงานการจัดเลี้ยงและอีเวนต์"],
        "tags": ["Hotel Business", "Hospitality Management", "Tourism"],
        "website_url": "https://tourism.dusit.ac.th"
    },

    # คณะครุศาสตร์ (Faculty of Education)
    {
        "id": "sdu_edu_earlychildhood",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาการศึกษาปฐมวัย",
        "title_en": "Bachelor of Education Program in Early Childhood Education",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (การศึกษาปฐมวัย)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Early Childhood Education",
        "department_th": "สาขาวิชาการศึกษาปฐมวัย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "ศูนย์กลางความเชี่ยวชาญด้านการศึกษาปฐมวัยของประเทศไทย เน้นการพัฒนานวัตกรรมการสอนเด็กเล็ก การจัดกระบวนการเรียนรู้ตามแนวคิด High/Scope, Montessori และนวัตกรรมปฐมวัยสวนดุสิต",
        "curriculum_highlights": ["Suan Dusit Early Childhood Pedagogy", "Brain-Based Learning for Young Children", "Play-Based Curriculum Design", "Child Development Assessment"],
        "career_paths": ["ครูปฐมวัย/อนุบาล", "นักวิชาการศึกษาปฐมวัย", "ผู้เชี่ยวชาญด้านสื่อการเรียนรู้สำหรับเด็ก", "ผู้บริหารศูนย์พัฒนาเด็กเล็ก"],
        "tags": ["การศึกษาปฐมวัย", "ครูปฐมวัย", "Early Childhood", "สวนดุสิต", "Education"],
        "website_url": "https://edu.dusit.ac.th"
    },
    {
        "id": "sdu_edu_primary",
        "title_th": "ครุศาสตรบัณฑิต สาขาวิชาการประถมศึกษา",
        "title_en": "Bachelor of Education Program in Elementary Education",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ค.บ. (การประถมศึกษา)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Elementary Education",
        "department_th": "สาขาวิชาการประถมศึกษา",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "135 หน่วยกิต",
        "tuition_per_semester": "15,500 บาท",
        "tuition_total": "124,000 บาท",
        "description": "ผลิตครูระดับประถมศึกษาที่มีความเชี่ยวชาญการจัดการเรียนการสอนแบบบูรณาการ การพัฒนาทักษะการคิดวิเคราะห์ และการดูแลผู้เรียนรายบุคคล",
        "curriculum_highlights": ["Integrated Primary Curriculum", "Classroom Action Research", "STEAM Education for Primary Schools", "Digital Learning Media Development"],
        "career_paths": ["ครูประจำชั้นประถมศึกษา", "นักวิชาการศึกษา", "นักพัฒนาหลักสูตรประถมศึกษา"],
        "tags": ["ประถมศึกษา", "ครูประถม", "Elementary Education", "Education"],
        "website_url": "https://edu.dusit.ac.th"
    },

    # โรงเรียนกฎหมายและการเมือง (School of Law and Politics)
    {
        "id": "sdu_law_llb",
        "title_th": "นิติศาสตรบัณฑิต",
        "title_en": "Bachelor of Laws Program (LL.B.)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "น.บ.",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "School of Law and Politics",
        "faculty_th": "โรงเรียนกฎหมายและการเมือง",
        "department": "Law",
        "department_th": "สาขาวิชานิติศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "16,500 บาท",
        "tuition_total": "132,000 บาท",
        "description": "มุ่งเน้นความรู้กฎหมายแพ่ง พาณิชย์ อาญา มหาชน กฎหมายปกครอง และกฎหมายธุรกิจดิจิทัล พร้อมฝึกทักษะการว่าความและการศาลจำลอง",
        "curriculum_highlights": ["Civil & Commercial Code", "Criminal Law & Procedure", "Administrative Law & Judicial Process", "Cyber Law & Intellectual Property", "Moot Court Practice"],
        "career_paths": ["ทนายความ", "นิติกรประจำหน่วยงานรัฐและเอกชน", "ผู้ช่วยผู้พิพากษา/อัยการ", "ที่ปรึกษากฎหมายธุรกิจ"],
        "tags": ["Law", "นิติศาสตร์", "Legal Studies", "Advocate"],
        "website_url": "https://lap.dusit.ac.th"
    },

    # คณะพยาบาลศาสตร์ (Faculty of Nursing)
    {
        "id": "sdu_nurse_bns",
        "title_th": "พยาบาลศาสตรบัณฑิต",
        "title_en": "Bachelor of Nursing Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "พย.บ.",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Nursing Science",
        "department_th": "พยาบาลศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "304,000 บาท",
        "description": "สร้างพยาบาลวิชาชีพที่มีทักษะการพยาบาลขั้นสูง ความรู้ทางการแพทย์ และความพร้อมดูแลสุขภาพผู้สูงอายุและผู้ป่วยวิกฤต",
        "curriculum_highlights": ["Adult & Critical Care Nursing", "Pediatric Nursing", "Maternal-Newborn Nursing", "Community Health & Gerontology"],
        "career_paths": ["พยาบาลวิชาชีพ", "พยาบาลวิกฤต/ฉุกเฉิน", "พยาบาลผู้เชี่ยวชาญด้านผู้สูงอายุ", "นักวิจัยด้านการพยาบาล"],
        "tags": ["Nursing", "พยาบาลศาสตร์", "Healthcare", "Medical"],
        "website_url": "https://nurse.dusit.ac.th"
    },

    # คณะวิทยาการจัดการ (Faculty of Management Science)
    {
        "id": "sdu_fms_brand_marketing",
        "title_th": "บริหารธุรกิจบัณฑิต สาขาวิชาการตลาดและการสร้างแบรนด์บุคคล",
        "title_en": "Bachelor of Business Administration in Marketing and Personal Branding",
        "degree_level": "ปริญญาตรี",
        "degree_name": "บธ.บ. (การตลาดและการสร้างแบรนด์บุคคล)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "Faculty of Management Science",
        "faculty_th": "คณะวิทยาการจัดการ",
        "department": "Marketing",
        "department_th": "สาขาวิชาการตลาด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "16,000 บาท",
        "tuition_total": "128,000 บาท",
        "description": "หลักสูตรทันสมัยที่ผสานกลยุทธ์การตลาด การสร้างแบรนด์บุคคล (Personal Branding) อินฟลูเอนเซอร์มาร์เก็ตติง และการสื่อสารการตลาดดิจิทัล",
        "curriculum_highlights": ["Personal Branding & Image Consulting", "Influencer Marketing Strategy", "Digital Content Creation", "Consumer Insights & Brand Analytics"],
        "career_paths": ["Personal Brand Consultant", "Digital Marketing Specialist", "Influencer & Content Creator", "Brand Manager"],
        "tags": ["Marketing", "Personal Branding", "Digital Media", "Influencer"],
        "website_url": "https://ms.dusit.ac.th"
    },

    # คณะวิทยาศาสตร์และเทคโนโลยี (Faculty of Science and Technology)
    {
        "id": "sdu_sci_it",
        "title_th": "วิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science in Computer Science and Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Computer Science and Information Technology",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "17,000 บาท",
        "tuition_total": "136,000 บาท",
        "description": "มุ่งเน้นการพัฒนาโปรแกรม ซอฟต์แวร์ประยุกต์ ปัญญาประดิษฐ์ คลาวด์ และการวิเคราะห์ข้อมูลเพื่อธุรกิจการบริการและอาหาร",
        "curriculum_highlights": ["Full-Stack Software Development", "Applied AI & Data Analytics", "Cloud Services & Database Systems", "Smart IoT & Mobile App Development"],
        "career_paths": ["Software Developer", "IT Consultant", "Data Analyst", "System Analyst"],
        "tags": ["Computer Science", "Information Technology", "AI", "Software Development"],
        "website_url": "https://sci.dusit.ac.th"
    },

    # บัณฑิตวิทยาลัย (ระดับปริญญาโท)
    {
        "id": "sdu_grad_medu",
        "title_th": "ศึกษาศาสตรมหาบัณฑิต สาขาวิชาการจัดการการศึกษาปฐมวัยและประถมศึกษา",
        "title_en": "Master of Education in Early Childhood and Elementary Education Management",
        "degree_level": "ปริญญาโท",
        "degree_name": "ศษ.ม. (การจัดการการศึกษาปฐมวัยและประถมศึกษา)",
        "university": "Suan Dusit University",
        "university_th": "มหาวิทยาลัยสวนดุสิต",
        "faculty": "Graduate School",
        "faculty_th": "บัณฑิตวิทยาลัย",
        "department": "Education",
        "department_th": "สาขาวิชาศึกษาศาสตร์",
        "program_type": "ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท",
        "tuition_total": "144,000 บาท",
        "description": "พัฒนาผู้บริหารสถานศึกษาและผู้นำทางวิชาการด้านการศึกษาปฐมวัยและประถมศึกษา เน้นนวัตกรรมการจัดการเรียนรู้และการวิจัยขั้นสูง",
        "curriculum_highlights": ["Educational Leadership & Policy", "Advanced Early Childhood Pedagogy", "Curriculum Development & Evaluation", "Thesis / Master Research"],
        "career_paths": ["ผู้บริหารสถานศึกษา", "ศึกษานิเทศก์", "อาจารย์สถาบันอุดมศึกษา", "นักวิจัยด้านการศึกษา"],
        "tags": ["Master of Education", "Early Childhood", "Education Leadership", "บัณฑิตศึกษา"],
        "website_url": "https://grad.dusit.ac.th"
    }
]

def seed_db():
    if not DB_AVAILABLE:
        logger.warning("Database module not available. Writing courses to JSON data file instead.")
        data_path = Path(__file__).resolve().parent / "data" / "sdu_courses.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(SDU_COURSES, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(SDU_COURSES)} SDU courses to {data_path}")
        return

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    try:
        for c in SDU_COURSES:
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                for k, v in c.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(CourseDB(**c))
                inserted += 1
        session.commit()
        logger.info(f"SDU Seeding completed: {inserted} inserted, {updated} updated.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding SDU: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_db()
