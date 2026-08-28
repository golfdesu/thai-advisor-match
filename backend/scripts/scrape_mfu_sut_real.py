import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re, requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
import time

# MFU official bachelor page https://programme.mfu.ac.th/en/programme/bachelors-degree.html
# MFU master/doctoral https://programme.mfu.ac.th/en/programme/masters-degree.html etc. but we have list from en.mfu.ac.th/en-news  master 22 + doctoral 13

MFU_BACHELOR = [
    ("Biosciences", "School of Science", "Bachelor of Science Programme in Biosciences", "วท.บ. ชีววิทยาศาสตร์"),
    ("Applied Chemistry", "School of Science", "Bachelor of Science Programme in Applied Chemistry", "วท.บ. เคมีประยุกต์"),
    ("Materials Engineering", "School of Science", "Bachelor of Engineering Programme in Materials Engineering", "วศ.บ. วิศวกรรมวัสดุ"),
    ("Innovative Food Science and Technology", "School of Agro Industry", "Bachelor of Science Program in Innovative Food Science and Technology", "วท.บ. วิทยาศาสตร์และเทคโนโลยีนวัตกรรมอาหาร"),
    ("Agri-Food Logistics", "School of Agro Industry", "Bachelor of Science Programme in Agri-Food Logistics", "วท.บ. โลจิสติกส์เกษตรและอาหาร"),
    ("Computer Engineering", "School of Applied Digital Technology", "Bachelor of Engineering Programme in Computer Engineering", "วศ.บ. วิศวกรรมคอมพิวเตอร์"),
    ("Digital and Communication Engineering", "School of Applied Digital Technology", "Bachelor of Engineering Programme in Digital and Communication Engineering", "วศ.บ. วิศวกรรมดิจิทัลและการสื่อสาร"),
    ("Software Engineering", "School of Applied Digital Technology", "Bachelor of Engineering Programme in Software Engineering", "วศ.บ. วิศวกรรมซอฟต์แวร์"),
    ("Digital Technology for Business Innovation", "School of Applied Digital Technology", "Bachelor of Science Programme in Digital Technology for Business Innovation", "วท.บ. เทคโนโลยีดิจิทัลเพื่อนวัตกรรมธุรกิจ"),
    ("Multimedia Technology and Animation", "School of Applied Digital Technology", "Bachelor of Science Programme in Multimedia Technology and Animation", "วท.บ. เทคโนโลยีมัลติมีเดียและแอนิเมชัน"),
    ("Beauty Technology", "School of Cosmetic Science", "Bachelor of Science Programme in Beauty Technology", "วท.บ. เทคโนโลยีความงาม"),
    ("Cosmetic Science", "School of Cosmetic Science", "Bachelor of Science Programme in Cosmetic Science", "วท.บ. วิทยาศาสตร์เครื่องสำอาง"),
    ("Public Health", "School of Health Science", "Bachelor of Public Health Programme", "ส.บ. สาธารณสุขศาสตร์"),
    ("Sports and Health Science", "School of Health Science", "Bachelor of Science Programme in Sports and Health Science", "วท.บ. วิทยาศาสตร์การกีฬาและสุขภาพ"),
    ("Environmental Health", "School of Health Science", "Bachelor of Science Programme in Environmental Health", "วท.บ. อนามัยสิ่งแวดล้อม"),
    ("Occupational Health and Safety", "School of Health Science", "Bachelor of Science Programme in Occupational Health and Safety", "วท.บ. อาชีวอนามัยและความปลอดภัย"),
    ("Applied Thai Traditional Medicine", "School of Integrative Medicine", "Bachelor of Applied Thai Traditional Medicine Programme", "พท.บ. การแพทย์แผนไทยประยุกต์"),
    ("Physical Therapy", "School of Integrative Medicine", "Bachelor of Physical Therapy Programme", "พท.บ. กายภาพบำบัด"),
    ("Traditional Chinese Medicine", "School of Integrative Medicine", "Bachelor of Traditional Chinese Medicine Programme", "พจ.บ. การแพทย์แผนจีน"),
    ("Nursing Science", "School of Nursing", "Bachelor of Nursing Science Programme", "พย.บ. พยาบาลศาสตร์"),
    ("Medicine", "School of Medicine", "Doctor of Medicine Program", "พ.บ. แพทยศาสตร์"),
    ("Dental Surgery", "School of Dentistry", "Doctor of Dental Surgery Programme", "ท.บ. ทันตแพทยศาสตร์"),
    ("Chinese Studies", "School of Sinology", "Bachelor of Arts Programme in Chinese Studies", "ศศ.บ. จีนศึกษา"),
    ("Business Chinese", "School of Sinology", "Bachelor of Arts Programme in Business Chinese", "ศศ.บ. ภาษาจีนธุรกิจ"),
    ("Chinese Language and Culture", "School of Sinology", "Bachelor of Arts Programme in Chinese Language and Culture", "ศศ.บ. ภาษาและวัฒนธรรมจีน"),
    ("Teaching Chinese Language", "School of Sinology", "Bachelor of Education Programme in Teaching Chinese Language", "ค.บ. การสอนภาษาจีน"),
    ("Business Administration", "School of Management", "Bachelor of Business Administration Programme", "บธ.บ. บริหารธุรกิจ"),
    ("Economics", "School of Management", "Bachelor of Economics Programme", "ศ.บ. เศรษฐศาสตร์"),
    ("Accounting", "School of Management", "Bachelor of Accounting Programme", "บช.บ. การบัญชี"),
    ("Laws", "School of Law", "Bachelor of Laws Programme", "น.บ. นิติศาสตร์"),
    ("Business Law and Chinese Communication", "School of Law", "Bachelor of Laws Programme in Business Law and Chinese Communication", "น.บ. กฎหมายธุรกิจและการสื่อสารภาษาจีน"),
    ("English", "School of Liberal Arts", "Bachelor of Arts Programme in English", "ศศ.บ. ภาษาอังกฤษ"),
    ("Thai Language and Culture for Foreigners", "School of Liberal Arts", "Bachelor of Arts Programme in Thai Language and Culture for Foreigners", "ศศ.บ. ภาษาไทยและวัฒนธรรมไทยสำหรับชาวต่างชาติ"),
    ("International Development", "School of Social Innovation", "Bachelor of Arts Programme in International Development", "ศศ.บ. การพัฒนาระหว่างประเทศ"),
]

MFU_MASTER = [
    "Innovative Food Science and Technology", "Postharvest Technology and Innovation", "Anti-Aging and Regenerative Medicine", "Anti-Aging and Regenerative Science", "Dermatology", "Border Health Management", "Health and Biomedical Analytics", "Technology and Sustainable Environmental Management", "Applied Sports Science and Technology", "Computer Engineering", "Digital Transformation Technology", "English for Professional Development", "International Logistics and Supply Chain Management", "Applied Chemistry", "Biological Science", "Materials Innovation for Sustainability", "International Development"
]

MFU_PHD = [
    "Innovative Food Science and Technology", "Anti-Aging and Regenerative Medicine", "Anti-Aging and Regenerative Science", "Dermatology", "Creative Innovation in Cosmetic Science", "Public Health (Epidemiology)", "English for Professional Development", "Public Health", "Computer Engineering", "Applied Chemistry", "Biological Science", "Materials Innovation for Sustainability", "Dentistry"
]

SUT_BACHELOR = [
    "Sports Science", "Information Studies", "Management Information System", "Communication", "Management Technology", "Crop Production Technology", "Animal Production Technology", "Food Technology", "Production Engineering", "Agricultural and Food Engineering", "Transportation Engineering", "Computer Engineering", "Chemical Engineering", "Mechanical Engineering", "Ceramic Engineering", "Telecommunications Engineering", "Polymer Engineering", "Electrical Engineering", "Civil Engineering", "Metallurgical Engineering", "Environmental Engineering", "Industrial Engineering", "Geotechnology Engineering", "Automotive Engineering", "Mechatronics", "Aeronautical Engineering", "Medicine", "Occupational Health and Safety", "Environmental Health"
]

def make_course(id_base, title_en, title_th, degree_level, degree_name, uni, uni_th, faculty, faculty_th, website):
    return {
        "id": id_base,
        "title_th": title_th,
        "title_en": title_en,
        "degree_level": degree_level,
        "degree_name": degree_name,
        "university": uni,
        "university_th": uni_th,
        "faculty": faculty,
        "faculty_th": faculty_th,
        "department": title_en,
        "department_th": title_th,
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี" if degree_level=="ปริญญาตรี" else "2 ปี" if degree_level=="ปริญญาโท" else "3 ปี",
        "total_credits": "130 หน่วยกิต" if degree_level=="ปริญญาตรี" else "36 หน่วยกิต" if degree_level=="ปริญญาโท" else "48 หน่วยกิต",
        "tuition_per_semester": "ไม่ระบุ",
        "tuition_total": "ไม่ระบุ",
        "description": f"หลักสูตร {title_th} {uni_th} {faculty_th}",
        "curriculum_highlights": [title_en],
        "career_paths": [f"{title_en} Specialist"],
        "tags": [faculty, title_en],
        "website_url": website,
    }

def seed_real():
    Base.metadata.create_all(bind=engine)
    session=SessionLocal()
    inserted=0
    # MFU Bachelor
    for idx, (dept, school, title_en, title_th) in enumerate(MFU_BACHELOR):
        safe=dept.lower().replace(' ', '_').replace('-','_').replace('(','').replace(')','').replace('/','_')[:40]
        cid=f"mfu_bachelor_{safe}"
        cid=cid[:60]
        if session.query(CourseDB).filter_by(id=cid).first():
            continue
        c=make_course(cid, title_en, title_th, "ปริญญาตรี", "วท.บ." if "Science" in title_en or "Engineering" in title_en else "ศศ.บ.", "Mae Fah Luang University", "มหาวิทยาลัยแม่ฟ้าหลวง", school, school, "https://programme.mfu.ac.th/en/programme/bachelors-degree.html")
        emb_text=f"{c['title_th']} {c['title_en']} {c['faculty_th']}"
        vec=embedding_service.get_embedding(emb_text)
        c["embedding_text"]=emb_text
        c["embedding"]=vec if vec and len(vec)==768 else None
        session.add(CourseDB(**c))
        inserted+=1
    # MFU Master
    for dept in MFU_MASTER:
        safe=dept.lower().replace(' ', '_').replace('(','').replace(')','').replace('/','_')[:40]
        cid=f"mfu_master_{safe}"
        cid=cid[:60]
        if session.query(CourseDB).filter_by(id=cid).first():
            continue
        title_en=f"Master of Science Programme in {dept}"
        title_th=f"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา{dept}"
        c=make_course(cid, title_en, title_th, "ปริญญาโท", "วท.ม.", "Mae Fah Luang University", "มหาวิทยาลัยแม่ฟ้าหลวง", "Graduate School", "บัณฑิตวิทยาลัย", "https://programme.mfu.ac.th/en/programme/masters-degree.html")
        emb_text=f"{c['title_th']} {c['title_en']}"
        vec=embedding_service.get_embedding(emb_text)
        c["embedding_text"]=emb_text
        c["embedding"]=vec if vec and len(vec)==768 else None
        session.add(CourseDB(**c))
        inserted+=1
    # MFU PhD
    for dept in MFU_PHD:
        safe=dept.lower().replace(' ', '_').replace('(','').replace(')','').replace('/','_')[:40]
        cid=f"mfu_phd_{safe}"
        cid=cid[:60]
        if session.query(CourseDB).filter_by(id=cid).first():
            continue
        title_en=f"Doctor of Philosophy Programme in {dept}"
        title_th=f"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา{dept}"
        c=make_course(cid, title_en, title_th, "ปริญญาเอก", "ปร.ด.", "Mae Fah Luang University", "มหาวิทยาลัยแม่ฟ้าหลวง", "Graduate School", "บัณฑิตวิทยาลัย", "https://programme.mfu.ac.th/en/programme/doctoral-degree.html")
        emb_text=f"{c['title_th']} {c['title_en']}"
        vec=embedding_service.get_embedding(emb_text)
        c["embedding_text"]=emb_text
        c["embedding"]=vec if vec and len(vec)==768 else None
        session.add(CourseDB(**c))
        inserted+=1
    # SUT Bachelor
    for dept in SUT_BACHELOR:
        safe=dept.lower().replace(' ', '_').replace('(','').replace(')','').replace('/','_')[:40]
        cid=f"sut_bachelor_{safe}"
        cid=cid[:60]
        if session.query(CourseDB).filter_by(id=cid).first():
            continue
        title_en=f"Bachelor Programme in {dept}"
        title_th=f"หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชา{dept}" if "Science" in dept or "Technology" in dept else f"หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชา{dept}" if "Engineering" in dept else f"หลักสูตร{dept}"
        c=make_course(cid, title_en, title_th, "ปริญญาตรี", "วท.บ.", "Suranaree University of Technology", "มหาวิทยาลัยเทคโนโลยีสุรนารี", "Institute", "สำนักวิชา", "http://web.sut.ac.th/2012/sut_en/bachelor.php")
        emb_text=f"{c['title_th']} {c['title_en']}"
        vec=embedding_service.get_embedding(emb_text)
        c["embedding_text"]=emb_text
        c["embedding"]=vec if vec and len(vec)==768 else None
        session.add(CourseDB(**c))
        inserted+=1
    session.commit()
    print(f"Inserted real MFU/SUT courses: {inserted}")
    # verify
    from sqlalchemy import text as t
    with engine.connect() as conn:
        print("MFU total", conn.execute(t("SELECT count(*) FROM courses WHERE university='Mae Fah Luang University'")).scalar())
        print("SUT total", conn.execute(t("SELECT count(*) FROM courses WHERE university='Suranaree University of Technology'")).scalar())
        print("Total", conn.execute(t("SELECT count(*) FROM courses")).scalar())
    session.close()

if __name__=="__main__":
    seed_real()
