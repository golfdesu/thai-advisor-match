import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

def add_curated():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    uni = "Mahidol University"
    uni_th = "มหาวิทยาลัยมหิดล"
    
    curated_courses = [
        # Dentistry
        {
            "title_en": "Doctor of Dental Surgery (International Program)",
            "title_th": "ทันตแพทยศาสตรบัณฑิต (หลักสูตรนานาชาติ)",
            "faculty": "Faculty of Dentistry",
            "faculty_th": "คณะทันตแพทยศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "D.D.S.",
            "duration_years": "6",
            "program_type": "International",
            "tuition_per_semester": "670,000 THB (Thai) / 750,000 THB (Non-Thai)",
            "description": "Focuses on critical thinking, integrative and holistic dental health skills, and clinical practice in state-of-the-art facilities at Mahidol International Dental School (MIDS).",
            "website_url": "https://dt.mahidol.ac.th/en/mahidol-international-dental-school"
        },
        {
            "title_en": "Ph.D. in Oral Biology and Integrative Biomedical Science",
            "title_th": "ปรัชญาดุษฎีบัณฑิต สาขาวิชาชีววิทยาช่องปากและวิทยาศาสตร์ชีวการแพทย์เชิงบูรณาการ",
            "faculty": "Faculty of Dentistry",
            "faculty_th": "คณะทันตแพทยศาสตร์",
            "degree_level": "Doctorate",
            "degree_name": "Ph.D.",
            "program_type": "International",
            "website_url": "https://dt.mahidol.ac.th"
        },
        {
            "title_en": "Ph.D. in Dental Biomaterials Science",
            "title_th": "ปรัชญาดุษฎีบัณฑิต สาขาวิชาวิทยาศาสตร์วัสดุชีวภาพทางทันตกรรม",
            "faculty": "Faculty of Dentistry",
            "faculty_th": "คณะทันตแพทยศาสตร์",
            "degree_level": "Doctorate",
            "degree_name": "Ph.D.",
            "program_type": "International",
            "website_url": "https://dt.mahidol.ac.th"
        },
        {
            "title_en": "M.Sc. in Orthodontics",
            "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชาทันตกรรมจัดฟัน",
            "faculty": "Faculty of Dentistry",
            "faculty_th": "คณะทันตแพทยศาสตร์",
            "degree_level": "Master",
            "degree_name": "M.Sc.",
            "program_type": "International",
            "website_url": "https://dt.mahidol.ac.th"
        },
        {
            "title_en": "M.Sc. in Oral Biology and Integrative Biomedical Science",
            "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชาชีววิทยาช่องปากและวิทยาศาสตร์ชีวการแพทย์เชิงบูรณาการ",
            "faculty": "Faculty of Dentistry",
            "faculty_th": "คณะทันตแพทยศาสตร์",
            "degree_level": "Master",
            "degree_name": "M.Sc.",
            "program_type": "International",
            "website_url": "https://dt.mahidol.ac.th"
        },
        {
            "title_en": "M.Sc. in Implant Dentistry",
            "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการรากเทียม",
            "faculty": "Faculty of Dentistry",
            "faculty_th": "คณะทันตแพทยศาสตร์",
            "degree_level": "Master",
            "degree_name": "M.Sc.",
            "program_type": "International (Double Degree)",
            "description": "Double-degree program: M.Sc. in Implant Dentistry (Mahidol University) and M.Sc. in Implantology and Dental Surgery (International Medical College, Germany).",
            "website_url": "https://dt.mahidol.ac.th"
        },
        # Engineering
        {
            "title_en": "B.Eng. in Biomedical Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular / International",
            "department": "Department of Biomedical Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        {
            "title_en": "B.Eng. in Chemical Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเคมี",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular",
            "department": "Department of Chemical Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        {
            "title_en": "B.Eng. in Civil and Environmental Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโยธาและสิ่งแวดล้อม",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular",
            "department": "Department of Civil and Environmental Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        {
            "title_en": "B.Eng. in Computer Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular / International",
            "department": "Department of Computer Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        {
            "title_en": "B.Eng. in Electrical Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้า",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular",
            "department": "Department of Electrical Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        {
            "title_en": "B.Eng. in Industrial Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมอุตสาหการ",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular",
            "department": "Department of Industrial Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        {
            "title_en": "B.Eng. in Mechanical Engineering",
            "title_th": "วิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมเครื่องกล",
            "faculty": "Faculty of Engineering",
            "faculty_th": "คณะวิศวกรรมศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "B.Eng.",
            "program_type": "Regular",
            "department": "Department of Mechanical Engineering",
            "website_url": "https://www.eg.mahidol.ac.th"
        },
        # Pharmacy
        {
            "title_en": "Doctor of Pharmacy (International Program)",
            "title_th": "เภสัชศาสตรบัณฑิต (หลักสูตรนานาชาติ)",
            "faculty": "Faculty of Pharmacy",
            "faculty_th": "คณะเภสัชศาสตร์",
            "degree_level": "Bachelor",
            "degree_name": "Pharm.D.",
            "duration_years": "6",
            "program_type": "International",
            "description": "A 6-year full-time professional program. The curriculum is structured with foundational sciences at the Mahidol University International College for the first year, followed by core medical and pharmaceutical courses at the Phayathai Campus.",
            "website_url": "https://pharmacy.mahidol.ac.th"
        },
        {
            "title_en": "Master of Science in Interdisciplinary Pharmaceutical Sciences for Health Products and Drug Discovery and Development",
            "title_th": "วิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์เภสัชกรรมสหวิทยาการเพื่อผลิตภัณฑ์สุขภาพและการค้นพบและพัฒนายา",
            "faculty": "Faculty of Pharmacy",
            "faculty_th": "คณะเภสัชศาสตร์",
            "degree_level": "Master",
            "degree_name": "M.Sc.",
            "program_type": "International",
            "website_url": "https://pharmacy.mahidol.ac.th"
        }
    ]
    
    ins = 0
    upd = 0
    
    for c in curated_courses:
        c["university"] = uni
        c["university_th"] = uni_th
        import uuid
        c["id"] = f"{uni}-{c['faculty']}-{c['title_en']}".lower().replace(" ","-").replace(".","").replace("(","").replace(")","")[:50]
        
        # Ensure required fields
        for field in ["department", "department_th", "duration_years", "total_credits", "tuition_per_semester", "tuition_total", "description"]:
            if field not in c:
                c[field] = "ไม่ระบุ"
                
        c["curriculum_highlights"] = []
        c["career_paths"] = []
        c["tags"] = []
        
        emb_text = f"{c.get('title_th','')} {c.get('title_en','')} {c.get('faculty_th','')}"
        c["embedding_text"] = emb_text
        vec = embedding_service.get_embedding(emb_text)
        c["embedding"] = vec if vec and len(vec) == 768 else None
        
        ex = session.query(CourseDB).filter_by(id=c["id"]).first()
        if ex:
            for k, v in c.items():
                setattr(ex, k, v)
            upd += 1
        else:
            session.add(CourseDB(**c))
            ins += 1
            
        session.commit()
        
    print(f"Curated courses added: {ins} inserted, {upd} updated.")
    
    from sqlalchemy import text
    with engine.connect() as conn:
        q1 = text("SELECT count(*) FROM courses WHERE university='Mahidol University'")
        q2 = text("SELECT count(*) FROM courses")
        print(f"MU total: {conn.execute(q1).scalar()}")
        print(f"DB total: {conn.execute(q2).scalar()}")

if __name__ == "__main__":
    add_curated()
