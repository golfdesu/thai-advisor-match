import json
from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

extra_faculty = [
    # --- MAHIDOL MEDICINE ---
    {
        "id": "mu_med_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Surgery",
        "department_th": "ภาควิชาศัลยศาสตร์",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Prasit",
        "last_name": "Watanapa",
        "full_name_th": "ศ.ดร.นพ. ประสิทธิ์ วัฒนาภา",
        "role": "คณาจารย์ประจำคณะ",
        "email": "prasit.wat@mahidol.ac.th",
        "image_url": "https://www.si.mahidol.ac.th/th/department/surgery/images/staff/prasit.jpg",
        "profile_url": "https://www.si.mahidol.ac.th/th/department/surgery/",
        "education": ["Ph.D. (Surgery), University of London", "M.D., Mahidol University"],
        "research_interests": ["Surgery", "Medical Education", "Healthcare Management", "Oncology"],
        "taught_courses": ["Clinical Surgery", "Medical Ethics", "Health Systems"],
        "scholar_url": ""
    },
    {
        "id": "mu_med_002",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Pediatrics",
        "department_th": "ภาควิชากุมารเวชศาสตร์",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Vip",
        "last_name": "Viprakasit",
        "full_name_th": "ศ.ดร.นพ. วิป วิประกษิต",
        "role": "คณาจารย์ประจำคณะ",
        "email": "vip.vip@mahidol.ac.th",
        "image_url": "https://www.si.mahidol.ac.th/th/department/pediatrics/images/staff/vip.jpg",
        "profile_url": "https://www.si.mahidol.ac.th/th/department/pediatrics/",
        "education": ["D.Phil. (Molecular Medicine), University of Oxford", "M.D., Mahidol University"],
        "research_interests": ["Hematology", "Genetics", "Thalassemia", "Molecular Biology"],
        "taught_courses": ["Pediatric Hematology", "Human Genetics"],
        "scholar_url": ""
    },
    
    # --- CMU BUSINESS SCHOOL ---
    {
        "id": "cmu_bus_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "CMU Business School",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Finance",
        "department_th": "ภาควิชาการเงินและการธนาคาร",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Ravi",
        "last_name": "Lonkani",
        "full_name_th": "รศ.ดร. รวิ ลงกานี",
        "role": "คณาจารย์ประจำภาควิชา",
        "email": "ravi.l@cmu.ac.th",
        "image_url": "https://www.ba.cmu.ac.th/wp-content/uploads/2019/08/ravi.jpg",
        "profile_url": "https://www.ba.cmu.ac.th/",
        "education": ["Ph.D. (Finance), NIDA", "MBA, Chiang Mai University"],
        "research_interests": ["Corporate Finance", "FinTech", "Investment Analysis", "Financial Markets"],
        "taught_courses": ["Financial Management", "Investment Theory", "Financial Technology"],
        "scholar_url": ""
    },
    {
        "id": "cmu_bus_002",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "CMU Business School",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Marketing",
        "department_th": "ภาควิชาการตลาด",
        "academic_title_th": "ผศ.ดร.",
        "first_name": "Nittaya",
        "last_name": "Jariangprasert",
        "full_name_th": "ผศ.ดร. นิตยา เจรียงประเสริฐ",
        "role": "คณาจารย์ประจำภาควิชา",
        "email": "nittaya.j@cmu.ac.th",
        "image_url": "https://www.ba.cmu.ac.th/wp-content/uploads/2019/08/nittaya.jpg",
        "profile_url": "https://www.ba.cmu.ac.th/",
        "education": ["Ph.D. (Marketing), University of Melbourne", "MBA, Chulalongkorn University"],
        "research_interests": ["Consumer Behavior", "Digital Marketing", "Brand Management", "Social Media Analytics"],
        "taught_courses": ["Marketing Management", "Digital Marketing Strategy", "Consumer Psychology"],
        "scholar_url": ""
    },
    {
        "id": "cmu_bus_003",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "CMU Business School",
        "faculty_th": "คณะบริหารธุรกิจ",
        "department": "Department of Management",
        "department_th": "ภาควิชาการจัดการ",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Siriwut",
        "last_name": "Buranapin",
        "full_name_th": "รศ.ดร. สิริวุฒิ บูรณพิร",
        "role": "อดีตคณบดีคณะบริหารธุรกิจ",
        "email": "siriwut.b@cmu.ac.th",
        "image_url": "https://www.ba.cmu.ac.th/wp-content/uploads/2019/08/siriwut.jpg",
        "profile_url": "https://www.ba.cmu.ac.th/",
        "education": ["Ph.D. (Management), Asian Institute of Technology", "MBA, Chiang Mai University"],
        "research_interests": ["Human Resource Management", "Organizational Behavior", "Strategic Management", "Leadership"],
        "taught_courses": ["Strategic Management", "Organizational Behavior", "HR Analytics"],
        "scholar_url": ""
    }
]

def seed_extra():
    db = SessionLocal()
    for item in extra_faculty:
        existing = db.query(FacultyDB).filter_by(id=item["id"]).first()
        if existing:
            continue
            
        fac = FacultyDB(
            id=item["id"],
            university=item["university"],
            university_th=item["university_th"],
            faculty=item["faculty"],
            faculty_th=item["faculty_th"],
            department=item["department"],
            department_th=item["department_th"],
            academic_title_th=item["academic_title_th"],
            first_name=item["first_name"],
            last_name=item["last_name"],
            full_name_th=item["full_name_th"],
            role=item["role"],
            email=item["email"],
            image_url=item["image_url"],
            profile_url=item["profile_url"],
            education=item["education"],
            research_interests=item["research_interests"],
            taught_courses=item["taught_courses"],
            scholar_url=item["scholar_url"]
        )
        db.add(fac)
    db.commit()
    db.close()
    print("Extra faculty (Medicine & Business) imported successfully.")

if __name__ == "__main__":
    seed_extra()
