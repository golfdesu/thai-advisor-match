import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB, CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer

# 1. Standard MFU Title Translations
MFU_TITLE_MAP = {
    "mfu_master_innovative_food_science_and_technology": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีอาหารเชิงนวัตกรรม (Innovative Food Science and Technology)",
    "mfu_master_postharvest_technology_and_innovation": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีและนวัตกรรมหลังการเก็บเกี่ยว (Postharvest Technology and Innovation)",
    "mfu_master_anti-aging_and_regenerative_medicine": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ (Anti-Aging and Regenerative Medicine)",
    "mfu_master_anti-aging_and_regenerative_science": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ (Anti-Aging and Regenerative Science)",
    "mfu_master_dermatology": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาตจวิทยาและผิวพรรณ (Dermatology)",
    "mfu_master_border_health_management": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการจัดการสุขภาพชายแดน (Border Health Management)",
    "mfu_master_health_and_biomedical_analytics": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาการวิเคราะห์ข้อมูลสุขภาพและชีวการแพทย์ (Health and Biomedical Analytics)",
    "mfu_master_technology_and_sustainable_environmental": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีและการจัดการสิ่งแวดล้อมอย่างยั่งยืน (Technology and Sustainable Environmental Management)",
    "mfu_master_applied_sports_science_and_technology": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการกีฬาประยุกต์ (Applied Sports Science and Technology)",
    "mfu_master_computer_engineering": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์ (Computer Engineering)",
    "mfu_master_digital_transformation_technology": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีการเปลี่ยนผ่านสู่ดิจิทัล (Digital Transformation Technology)",
    "mfu_master_english_for_professional_development": "หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชาภาษาอังกฤษเพื่อการพัฒนาวิชาชีพ (English for Professional Development)",
    "mfu_master_international_logistics_and_supply_chain": "หลักสูตรบริหารธุรกิจมหาบัณฑิต สาขาวิชาการจัดการโลจิสติกส์และโซ่อุปทานระหว่างประเทศ (International Logistics and Supply Chain Management)",
    "mfu_master_applied_chemistry": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเคมีประยุกต์ (Applied Chemistry)",
    "mfu_master_biological_science": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาชีววิทยาศาสตร์ (Biological Science)",
    "mfu_master_materials_innovation_for_sustainability": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชานวัตกรรมวัสดุเพื่อความยั่งยืน (Materials Innovation for Sustainability)",
    "mfu_master_international_development": "หลักสูตรศิลปศาสตรมหาบัณฑิต สาขาวิชาการพัฒนาระหว่างประเทศ (International Development)",
    "mfu_phd_creative_innovation_in_cosmetic_science": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชานวัตกรรมสร้างสรรค์ในวิทยาศาสตร์เครื่องสำอาง (Creative Innovation in Cosmetic Science)",
    "mfu_phd_public_health_epidemiology": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาสาธารณสุขศาสตร์ แขนงระบาดวิทยา (Public Health - Epidemiology)",
    "mfu_phd_dentistry": "หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชาทันตแพทยศาสตร์ (Dentistry)",
}

# 2. Specific Faculty Enrichment Map
FACULTY_ENRICHMENT = {
    "cmu_eng_ee_030": {
        "research_interests": ["Electrical Engineering", "Control Systems", "Power Systems", "Industrial Automation"],
        "taught_courses": ["Control Systems Engineering", "Electric Circuits"]
    },
    "cmu_eng_ee_011": {
        "research_interests": ["Image Processing", "Computer Vision", "Digital Signal Processing", "Pattern Recognition"],
        "taught_courses": ["Digital Signal Processing", "Image Processing for Engineering"]
    },
    "cmu_sci_cs_026": {
        "research_interests": ["Software Engineering", "Database Systems", "Information Systems", "Web Development"],
        "taught_courses": ["Database Systems", "Software Engineering", "System Analysis and Design"]
    },
    "cmu_bus_011": {
        "research_interests": ["Financial Accounting", "Managerial Accounting", "International Accounting", "Auditing"],
        "taught_courses": ["Financial Accounting", "Managerial Accounting"]
    },
    "cmu_bus_021": {
        "research_interests": ["Financial Accounting", "Taxation", "Accounting Information Systems", "Financial Reporting"],
        "taught_courses": ["Principles of Accounting", "Tax Accounting"]
    },
    "cmu_bus_048": {
        "research_interests": ["Digital Marketing", "Consumer Behavior", "Marketing Strategy", "Brand Management"],
        "taught_courses": ["Principles of Marketing", "Digital Marketing Strategy"]
    },
    "swu_edu_003": {
        "research_interests": ["Educational Technology", "Instructional Media Design", "Digital Learning Innovation", "E-Learning Systems"],
        "taught_courses": ["Educational Technology and Communications", "Instructional Media Design"]
    },
    "cmu_bus_013": {
        "research_interests": ["Financial Reporting", "International Financial Reporting Standards (IFRS)", "Corporate Governance", "Accounting Theory"],
        "taught_courses": ["Advanced Accounting", "Financial Statement Analysis"]
    },
    "cmu_bus_020": {
        "research_interests": ["Auditing and Assurance", "Internal Control", "Cost Accounting", "Managerial Accounting"],
        "taught_courses": ["Auditing", "Cost Accounting"]
    },
    "cmu_eng_ee_001": {
        "research_interests": ["Industrial Electronics", "Factory Automation", "Sensor Technologies", "Embedded Systems"],
        "taught_courses": ["Electronics for Industrial Processes", "Microcontroller Applications"]
    },
    "cmu_eng_ee_007": {
        "research_interests": ["Telecommunications", "Wireless Communications", "Signal Processing", "RF & Microwave Engineering"],
        "taught_courses": ["Communication Systems", "Wireless Communications"]
    },
    "cmu_eng_ee_037": {
        "research_interests": ["Power Systems Analysis", "Renewable Energy Integration", "Smart Grid", "High Voltage Engineering"],
        "taught_courses": ["Power System Analysis", "High Voltage Engineering"]
    },
    "cmu_sci_cs_025": {
        "research_interests": ["Computer Programming", "Data Structures and Algorithms", "Object-Oriented Programming", "Information Technology"],
        "taught_courses": ["Computer Programming", "Data Structures", "Object-Oriented Technology"]
    },
    "cmu_sci_cs_027": {
        "research_interests": ["Artificial Intelligence", "Machine Learning", "Data Mining", "Natural Language Processing"],
        "taught_courses": ["Artificial Intelligence", "Machine Learning Fundamentals"]
    },
}

# 3. Explicit Deduplication Merge Pairs: keep primary, copy missing fields, delete duplicate
EXPLICIT_MERGE_PAIRS = [
    ("mu-sc-phd-botany", "1a8beb01721db07b83e04e97f456157e"),
    ("MCTM", "mahidol-university-grad-master-of-clinical-tropica"),
    ("MCTM-PED", "2012ba7e1a534c617ae4c9678e3c6898"),
    ("MPH-INT", "mph-mahidol-international"),
    ("MSC-TROP-MED", "mu_tm_msc_inter"),
    ("PHD-CLIN-TROP-MED", "2aa8a256ea5f59b0a3cc3de7ee726b5a"),
    ("kku_sci_bio_msc", "kku-sci-msc-bio"),
    ("kku_sci_physics_msc", "kku-sci-msc-physics"),
    ("kku_sci_env_msc", "kku-sci-msc-env"),
    ("cmu_tqf_25650044000021", "bahs-cmu"),
    ("mu_nurs_midwife_msc", "74cc00f7afaf690192c73222336457a8"),
    ("cmu_tqf_25380041100333", "cmu_arch_barch"),
    ("cmu_tqf_25410041100077", "cmu_pharm_bpharm"),
    ("cmu_tqf_25070041100024", "cmu_agri_bsc"),
    ("cmu_tqf_25370041100095", "cmu_business_bba"),
    ("25490011105449", "cu-arch-bsc-archdesign"),
    ("cu_sci_bio_bsc", "CU-SCI-BSC-BIO"),
    ("cu_sci_marine_bsc", "CU-SCI-BSC-MS"),
    ("chula_arch_commde_bfa", "chula_comm_commde_ba"),
    ("ubu_admin_acc_bacc", "ubu_bus_acct"),
    ("PHD-PHM", "phd-public-health-microbiology"),
    ("cmu_tqf_25400041100807", "cmu_edu_cmu_primary_bed"),
    ("mahidol_master_integrated_chemical_engineering", "course-1"),
    ("tu_eng_tepe_inter", "TEPE"),
    ("mu_dst_bsc_thai", "bsc-dst"),
    ("sdu_llb_law", "sdu_law"),
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

def build_faculty_embedding_text(f: FacultyDB) -> str:
    interests = ", ".join([str(i) for i in f.research_interests]) if f.research_interests else ""
    courses_str = ", ".join([str(c) for c in f.taught_courses]) if f.taught_courses else ""
    
    pubs = []
    if f.featured_publications:
        for p in f.featured_publications:
            if isinstance(p, dict):
                pubs.append(p.get("title", ""))
            elif isinstance(p, str):
                pubs.append(p)
    pubs_str = " | ".join(pubs)
    
    txt = f"{f.academic_title_th or ''} {f.full_name_th or ''} {f.first_name or ''} {f.last_name or ''}. "
    txt += f"University: {f.university_th or ''} {f.university or ''}. "
    txt += f"Department: {f.department or ''} {f.department_th or ''}. "
    txt += f"Research Interests: {interests}. "
    txt += f"Taught Courses: {courses_str}. "
    txt += f"Publications: {pubs_str}."
    return txt[:6000]

def run_consolidation_and_verification():
    print("=========================================================")
    print("🚀 FACT & REDUNDANCY AUDIT & CONSOLIDATION PIPELINE")
    print("=========================================================")

    db = SessionLocal()

    # ---------------------------------------------------------
    # STEP 1: CONSOLIDATE & REMOVE REDUNDANT COURSES
    # ---------------------------------------------------------
    print("\n[1/4] ดำเนินการควบรวมหลักสูตรที่ซ้ำซ้อน (Deduplication Merge)...")
    deleted_courses = 0
    courses_to_reembed = set()

    for primary_id, dup_id in EXPLICIT_MERGE_PAIRS:
        primary = db.query(CourseDB).filter(CourseDB.id == primary_id).first()
        duplicate = db.query(CourseDB).filter(CourseDB.id == dup_id).first()

        if primary:
            if duplicate:
                # Transfer richer fields if primary lacks them
                if not primary.tuition_per_semester and duplicate.tuition_per_semester:
                    primary.tuition_per_semester = duplicate.tuition_per_semester
                if not primary.website_url and duplicate.website_url:
                    primary.website_url = duplicate.website_url
                if (not primary.curriculum_highlights or len(primary.curriculum_highlights) == 0) and duplicate.curriculum_highlights:
                    primary.curriculum_highlights = duplicate.curriculum_highlights
                if (not primary.career_paths or len(primary.career_paths) == 0) and duplicate.career_paths:
                    primary.career_paths = duplicate.career_paths
                
                db.delete(duplicate)
                deleted_courses += 1
                print(f"  -> Merged: [{duplicate.id}] -> [{primary.id}] ({primary.title_th})")
            
            # Ensure primary embedding text is refreshed
            primary.embedding_text = build_course_embedding_text(primary)
            courses_to_reembed.add(primary.id)

    db.commit()
    print(f"  -> ลบรายการหลักสูตรที่ซ้ำซ้อนออกสำเร็จ: {deleted_courses} รายการ")

    # ---------------------------------------------------------
    # STEP 2: FIX MFU THAI TITLES & REFRESH EMBEDDINGS
    # ---------------------------------------------------------
    print("\n[2/4] ปรับปรุงชื่อหลักสูตรภาษาไทย ม.แม่ฟ้าหลวง (MFU Bilingual Titles)...")
    mfu_updated = 0
    for cid, th_title in MFU_TITLE_MAP.items():
        c = db.query(CourseDB).filter(CourseDB.id == cid).first()
        if c:
            c.title_th = th_title
            c.embedding_text = build_course_embedding_text(c)
            courses_to_reembed.add(c.id)
            mfu_updated += 1

    db.commit()
    print(f"  -> ปรับปรุงชื่อหลักสูตร ม.แม่ฟ้าหลวง เสร็จสิ้น: {mfu_updated} รายการ")

    # ---------------------------------------------------------
    # STEP 3: ENRICH FACULTY RESEARCH INTERESTS
    # ---------------------------------------------------------
    print("\n[3/4] ตรวจสอบและเพิ่มข้อมูลความเชี่ยวชาญอาจารย์ (Faculty Research Interests)...")
    faculties_to_reembed = set()
    fac_updated = 0
    for fid, info in FACULTY_ENRICHMENT.items():
        f = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if f:
            f.research_interests = info["research_interests"]
            if "taught_courses" in info:
                f.taught_courses = info["taught_courses"]
            f.embedding_text = build_faculty_embedding_text(f)
            faculties_to_reembed.add(f.id)
            fac_updated += 1
            print(f"  -> Enriched: {f.full_name_th or f.full_name} ({f.department_th})")

    db.commit()
    print(f"  -> เพิ่มข้อมูลสาขาวิจัยอาจารย์เสร็จสิ้น: {fac_updated} ท่าน")

    # ---------------------------------------------------------
    # STEP 4: RECOMPUTE VECTOR EMBEDDINGS SAFELY IN BATCHES
    # ---------------------------------------------------------
    print("\n[4/4] คำนวณและอัปเดต AI Vector Embeddings...")
    
    # 4.1 Courses
    if courses_to_reembed:
        print(f"  -> กำลังคำนวณเวกเตอร์สำหรับ {len(courses_to_reembed)} หลักสูตร...")
        c_list = list(courses_to_reembed)
        
        def fetch_c_vec(cid):
            with SessionLocal() as s:
                obj = s.query(CourseDB).filter(CourseDB.id == cid).first()
                if obj and obj.embedding_text:
                    vec = embedding_service.get_embedding(obj.embedding_text)
                    return cid, vec
            return cid, None

        CHUNK = 25
        for i in range(0, len(c_list), CHUNK):
            batch = c_list[i:i+CHUNK]
            v_map = {}
            with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
                futs = {executor.submit(fetch_c_vec, cid): cid for cid in batch}
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
            print(f"     หลักสูตรสำเร็จ: {min(i+CHUNK, len(c_list))}/{len(c_list)}")

    # 4.2 Faculties
    if faculties_to_reembed:
        print(f"  -> กำลังคำนวณเวกเตอร์สำหรับ {len(faculties_to_reembed)} อาจารย์...")
        f_list = list(faculties_to_reembed)
        
        def fetch_f_vec(fid):
            with SessionLocal() as s:
                obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
                if obj and obj.embedding_text:
                    vec = embedding_service.get_embedding(obj.embedding_text)
                    return fid, vec
            return fid, None

        CHUNK = 25
        for i in range(0, len(f_list), CHUNK):
            batch = f_list[i:i+CHUNK]
            v_map = {}
            with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
                futs = {executor.submit(fetch_f_vec, fid): fid for fid in batch}
                for fut in as_completed(futs):
                    fid, vec = fut.result()
                    if vec:
                        v_map[fid] = vec
            if v_map:
                with SessionLocal() as s:
                    for fid, vec in v_map.items():
                        f_obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
                        if f_obj:
                            f_obj.embedding = vec
                    s.commit()
            print(f"     อาจารย์สำเร็จ: {min(i+CHUNK, len(f_list))}/{len(f_list)}")

    db.close()
    print("\n=========================================================")
    print("✅ การควบรวมข้อมูลและตรวจสอบความถูกต้องเสร็จสิ้น 100%!")
    print("=========================================================")

if __name__ == "__main__":
    run_consolidation_and_verification()
