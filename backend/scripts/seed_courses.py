import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base
from app.models.db_models import CourseDB
from sqlalchemy.orm import Session
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_COURSES = [
    {
        "id": "cmu_ds_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการข้อมูล",
        "title_en": "Master of Science Program in Data Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการข้อมูล)",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "เน้นการผลิตบัณฑิตที่มีความรู้ความเชี่ยวชาญด้าน Big Data Analytics, Machine Learning, Deep Learning และการประยุกต์ใช้โมเดลข้อมูลเพื่อการตัดสินใจในองค์กรชั้นนำ",
        "curriculum_highlights": [
            "Advanced Machine Learning & AI",
            "Big Data Infrastructure & Cloud Computing",
            "Deep Learning & Natural Language Processing",
            "Business Intelligence & Data Visualization"
        ],
        "career_paths": ["Data Scientist", "Machine Learning Engineer", "AI Researcher", "Data Architect"],
        "tags": ["Data Science", "AI & Machine Learning", "Big Data", "Cloud Computing"],
        "website_url": "https://cs.science.cmu.ac.th"
    },
    {
        "id": "chula_ai_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิศวกรรมปัญญาประดิษฐ์",
        "title_en": "Master of Engineering in Artificial Intelligence Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมปัญญาประดิษฐ์)",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "นานาชาติ (International Program)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "85,000 บาท",
        "tuition_total": "340,000 บาท",
        "description": "หลักสูตรมาตรฐานสากล มุ่งเน้นการสร้างนวัตกรรม AI สำหรับอุตสาหกรรม การแพทย์ และหุ่นยนต์อัจฉริยะ พร้อมเครือข่ายวิจัยระดับนานาชาติ",
        "curriculum_highlights": [
            "Computer Vision & Pattern Recognition",
            "Robotics & Autonomous Systems",
            "Large Language Models & Generative AI",
            "Edge AI & IoT"
        ],
        "career_paths": ["AI Engineer", "Computer Vision Specialist", "Robotics Engineer", "AI Product Lead"],
        "tags": ["Artificial Intelligence", "Robotics", "Deep Learning", "Generative AI"],
        "website_url": "https://www.cp.eng.chula.ac.th"
    },
    {
        "id": "tu_mba_fintech",
        "title_th": "หลักสูตรบริหารธุรกิจมหาบัณฑิต นวัตกรรมการเงินและการลงทุน",
        "title_en": "Master of Business Administration in FinTech & Investment Innovation",
        "degree_level": "ปริญญาโท",
        "degree_name": "บธ.ม. (นวัตกรรมการเงิน)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Thammasat Business School",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี",
        "department": "Department of Finance",
        "department_th": "ภาควิชาการเงิน",
        "program_type": "โครงการพิเศษ (Executive / Weekend)",
        "duration_years": "2 ปี",
        "total_credits": "42 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "ผสานศาสตร์ด้านการเงินระดับสูง เทคโนโลยีบล็อกเชน และการวิเคราะห์การลงทุนเชิงปริมาณ (Quantitative Finance) ตอบโจทย์โลกการเงินยุคใหม่",
        "curriculum_highlights": [
            "Algorithmic & Quantitative Trading",
            "Blockchain & Decentralized Finance (DeFi)",
            "Financial Data Modeling with Python",
            "Venture Capital & Tech Valuation"
        ],
        "career_paths": ["FinTech Consultant", "Quantitative Analyst (Quant)", "Investment Banker", "Fund Manager"],
        "tags": ["FinTech", "Quantitative Finance", "Investment", "Blockchain", "MBA"],
        "website_url": "https://www.tbs.tu.ac.th"
    },
    {
        "id": "mu_biomed_phd",
        "title_th": "หลักสูตรวิทยาศาสตรดุษฎีบัณฑิต สาขาวิชาชีวการแพทย์และเวชศาสตร์ฟื้นฟู",
        "title_en": "Doctor of Philosophy Program in Biomedical Sciences & Regenerative Medicine",
        "degree_level": "ปริญญาเอก",
        "degree_name": "ปร.ด. (ชีวการแพทย์)",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Immunology & Molecular Biology",
        "department_th": "ภาควิชาภูมิคุ้มกันวิทยา",
        "program_type": "วิจัยเต็มเวลา (Full Research)",
        "duration_years": "3 - 5 ปี",
        "total_credits": "48 หน่วยกิต",
        "tuition_per_semester": "มีทุนสนับสนุนเต็มจำนวน",
        "tuition_total": "ทุนวิจัยจากคณะ",
        "description": "เน้นงานวิจัยระดับแนวหน้าด้านสเต็มเซลล์ พันธุวิศวกรรม การรักษาโรคมะเร็ง และการบำบัดรักษาแม่นยำ (Precision Medicine)",
        "curriculum_highlights": [
            "Stem Cell Biology & Tissue Engineering",
            "Genomics & Precision Medicine",
            "Translational Immunology",
            "Advanced Clinical Research Methodologies"
        ],
        "career_paths": ["Medical Research Scientist", "Clinical AI Researcher", "Biotech Entrepreneur", "University Professor"],
        "tags": ["Biomedical Science", "Regenerative Medicine", "Immunology", "Ph.D."],
        "website_url": "https://www.si.mahidol.ac.th"
    },
    {
        "id": "cmu_cpe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ / นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "20,000 - 35,000 บาท",
        "tuition_total": "160,000 - 280,000 บาท",
        "description": "สร้างวิศวกรคอมพิวเตอร์ที่มีความรู้ทั้งด้าน Software Systems, Computer Hardware Architecture, Cyber Security และ Embedded Systems",
        "curriculum_highlights": [
            "Full-Stack Software Development",
            "Cybersecurity & Network Systems",
            "Computer Architecture & Microprocessors",
            "Applied AI & Internet of Things"
        ],
        "career_paths": ["Software Engineer", "DevOps Engineer", "Cybersecurity Specialist", "Systems Architect"],
        "tags": ["Computer Engineering", "Software", "Hardware", "Bachelor"],
        "website_url": "https://cpe.eng.cmu.ac.th"
    }
]

from app.core.embedding_service import embedding_service

def build_course_embedding_text(c: dict) -> str:
    highlights_text = ", ".join(c.get("curriculum_highlights", []))
    careers_text = ", ".join(c.get("career_paths", []))
    tags_text = ", ".join(c.get("tags", []))
    return (
        f"{c['title_th']} {c.get('title_en', '')}. "
        f"University: {c['university']} {c['university_th']}. "
        f"Faculty: {c['faculty']} {c['faculty_th']}. "
        f"Department: {c.get('department', '')} {c.get('department_th', '')}. "
        f"Degree: {c['degree_level']} {c.get('degree_name', '')}. "
        f"Description: {c.get('description', '')}. "
        f"Highlights: {highlights_text}. "
        f"Careers: {careers_text}. "
        f"Tags: {tags_text}."
    )

def seed_courses():
    logger.info("Initializing courses table...")
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as session:
        for c in INITIAL_COURSES:
            emb_text = build_course_embedding_text(c)
            emb_vector = embedding_service.get_embedding(emb_text)
            
            existing = session.query(CourseDB).filter_by(id=c["id"]).first()
            if existing:
                logger.info(f"Course {c['id']} already exists. Updating...")
                for key, value in c.items():
                    setattr(existing, key, value)
                existing.embedding_text = emb_text
                if emb_vector and len(emb_vector) == 768:
                    existing.embedding = emb_vector
            else:
                logger.info(f"Inserting new course with vector embedding: {c['title_th']}")
                course_db = CourseDB(
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
                    embedding=emb_vector if (emb_vector and len(emb_vector) == 768) else None
                )
                session.add(course_db)
        session.commit()
        logger.info("Course seeding completed successfully with vector embeddings! 🎉")

if __name__ == "__main__":
    seed_courses()
