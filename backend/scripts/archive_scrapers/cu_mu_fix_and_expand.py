# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, json, pathlib, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service
from sqlalchemy import text

def build_emb(c):
    if isinstance(c, dict):
        hl=", ".join(c.get("curriculum_highlights",[]) or [])
        cp=", ".join(c.get("career_paths",[]) or [])
        tags=", ".join(c.get("tags",[]) or [])
        return f"{c.get('title_th','')} {c.get('title_en','')}. University: {c.get('university','')} {c.get('university_th','')}. Faculty: {c.get('faculty','')} {c.get('faculty_th','')}. Description: {c.get('description','')}. Highlights: {hl}. Careers: {cp}. Tags: {tags}."
    else:
        hl=", ".join(c.curriculum_highlights or [])
        cp=", ".join(c.career_paths or [])
        tags=", ".join(c.tags or [])
        return f"{c.title_th} {c.title_en or ''}. University: {c.university} {c.university_th}. Faculty: {c.faculty} {c.faculty_th}. Description: {c.description or ''}. Highlights: {hl}. Careers: {cp}. Tags: {tags}."

session=SessionLocal()
print("=== Fix bad title_th 'ไม่ระบุ' for CU/MU ===")
# Map English title patterns to Thai
def translate_en_to_th(en_title, faculty_th=""):
    if not en_title or en_title=="ไม่ระบุ":
        return None
    en=en_title.strip()
    # Common patterns
    patterns = [
        (r"Bachelor of Science Program in (.+)", r"หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชา\1"),
        (r"Bachelor of Science in (.+)", r"หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชา\1"),
        (r"Bachelor of Arts Program in (.+)", r"หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชา\1"),
        (r"Bachelor of Engineering Program in (.+)", r"หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชา\1"),
        (r"Bachelor of (.+) Program in (.+)", r"หลักสูตร\1บัณฑิต สาขาวิชา\2"),
        (r"Master of Science Program in (.+)", r"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา\1"),
        (r"Master of (.+) Program in (.+)", r"หลักสูตร\1มหาบัณฑิต สาขาวิชา\2"),
        (r"Doctor of Philosophy Program in (.+)", r"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา\1"),
        (r"Ph\.D\. \((.+)\)", r"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา\1"),
        (r"Doctor of (.+) Program", r"หลักสูตร\1ดุษฎีบัณฑิต"),
    ]
    for pat, repl in patterns:
        m=re.match(pat, en, re.I)
        if m:
            th=re.sub(pat, repl, en, flags=re.I)
            # clean
            th=th.replace("()", "").strip()
            return th
    # fallback: just prefix
    if "Bachelor" in en:
        return f"หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชา{en}"
    if "Master" in en:
        return f"หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชา{en}"
    if "Doctor" in en or "Ph.D" in en:
        return f"หลักสูตรปรัชญาดุษฎีบัณฑิต สาขาวิชา{en}"
    return None

fixed_title=0
for uni in ["Chulalongkorn University","Mahidol University"]:
    bads=session.query(CourseDB).filter(CourseDB.university==uni, CourseDB.title_th=="ไม่ระบุ").all()
    print(f"{uni}: {len(bads)} bad titles")
    for c in bads:
        new_th=translate_en_to_th(c.title_en, c.faculty_th)
        if new_th and new_th!="ไม่ระบุ" and len(new_th)>5:
            # also handle faculty generic
            old=c.title_th
            c.title_th=new_th
            # also build thai faculty if missing
            fixed_title+=1
        else:
            # fallback use English as Thai with prefix
            if c.title_en and c.title_en!="ไม่ระบุ":
                c.title_th=f"หลักสูตร{c.title_en}"
                fixed_title+=1
    session.commit()
print(f"Fixed title_th: {fixed_title}")

# Fix generic faculty
print("\n=== Fix generic faculty ===")
faculty_fixes = {
    "Chulalongkorn University": {
        "ไม่ระบุ": "คณะวิทยาศาสตร์", # most CU bad are Science
    },
    "Mahidol University": {
        "บัณฑิตวิทยาลัย": None, # infer from title
        "ไม่ระบุ": "คณะวิทยาศาสตร์",
    }
}
# For MU, try to infer faculty from title_en keywords
def infer_mu_faculty(title_en, title_th):
    t=(title_en or "")+" "+(title_th or "")
    t=t.lower()
    if any(k in t for k in ["nursing","พยาบาล"]):
        return ("Faculty of Nursing","คณะพยาบาลศาสตร์")
    if any(k in t for k in ["public health","สาธารณสุข"]):
        return ("Faculty of Public Health","คณะสาธารณสุขศาสตร์")
    if any(k in t for k in ["dent","ทันต"]):
        return ("Faculty of Dentistry","คณะทันตแพทยศาสตร์")
    if any(k in t for k in ["pharm","เภสัช"]):
        return ("Faculty of Pharmacy","คณะเภสัชศาสตร์")
    if any(k in t for k in ["med","แพทย์","clinical"]):
        return ("Faculty of Medicine Siriraj Hospital","คณะแพทยศาสตร์ศิริราชพยาบาล")
    if any(k in t for k in ["sci","วิทยาศาสตร์","physics","chem","bio","math"]):
        return ("Faculty of Science","คณะวิทยาศาสตร์")
    if any(k in t for k in ["engineer","วิศว"]):
        return ("Faculty of Engineering","คณะวิศวกรรมศาสตร์")
    if any(k in t for k in ["environment","สิ่งแวดล้อม"]):
        return ("Faculty of Environment and Resource Studies","คณะสิ่งแวดล้อมและทรัพยากรศาสตร์")
    if any(k in t for k in ["ict","computer","สารสนเทศ","เทคโน"]):
        return ("Faculty of Information and Communication Technology","คณะเทคโนโลยีสารสนเทศและการสื่อสาร")
    if any(k in t for k in ["manage","บริหาร","business"]):
        return ("College of Management","วิทยาลัยการจัดการ")
    if any(k in t for k in ["tropical","เขตร้อน"]):
        return ("Faculty of Tropical Medicine","คณะเวชศาสตร์เขตร้อน")
    return ("Faculty of Graduate Studies","บัณฑิตวิทยาลัย")

fixed_fac=0
for uni in ["Chulalongkorn University","Mahidol University"]:
    generics=session.query(CourseDB).filter(CourseDB.university==uni, CourseDB.faculty_th.in_(["ไม่ระบุ","บัณฑิตวิทยาลัย"])).all()
    print(f"{uni} generic faculty: {len(generics)}")
    for c in generics:
        if uni=="Chulalongkorn University":
            # most are Science per earlier check
            if "Computer Science" in (c.title_en or "") or "Physics" in (c.title_en or "") or "Microbiology" in (c.title_en or ""):
                c.faculty="Faculty of Science"
                c.faculty_th="คณะวิทยาศาสตร์"
                fixed_fac+=1
            else:
                # keep as Science as default
                c.faculty="Faculty of Science"
                c.faculty_th="คณะวิทยาศาสตร์"
                fixed_fac+=1
        elif uni=="Mahidol University":
            fac_en, fac_th = infer_mu_faculty(c.title_en, c.title_th)
            c.faculty=fac_en
            c.faculty_th=fac_th
            fixed_fac+=1
session.commit()
print(f"Fixed faculty: {fixed_fac}")

# Also update embedding_text for fixed ones
print("\n=== Update embedding for fixed rows ===")
# We'll update embedding_text for all fixed titles/faculties (142+ ~180)
# Fetch all CU/MU and rebuild embedding_text if needed
for uni in ["Chulalongkorn University","Mahidol University"]:
    courses=session.query(CourseDB).filter(CourseDB.university==uni).all()
    updated=0
    for c in courses:
        new_emb=build_emb(c)
        if c.embedding_text != new_emb:
            c.embedding_text=new_emb
            try:
                vec=embedding_service.get_embedding(new_emb)
                if vec and len(vec)==768:
                    c.embedding=vec
            except: pass
            updated+=1
            if updated%30==0:
                session.commit()
                print(f"  {uni} updated {updated}/{len(courses)}")
    session.commit()
    print(f"{uni} embedding updated: {updated}")

print("\n=== Done fixing ===")
with engine.connect() as conn:
    for uni in ["Chulalongkorn University","Mahidol University"]:
        bad=conn.execute(text("SELECT COUNT(*) FROM courses WHERE university=:u AND title_th='ไม่ระบุ'"), {"u":uni}).scalar()
        gen_fac=conn.execute(text("SELECT COUNT(*) FROM courses WHERE university=:u AND faculty_th IN ('ไม่ระบุ','บัณฑิตวิทยาลัย')"), {"u":uni}).scalar()
        total=conn.execute(text("SELECT COUNT(*) FROM courses WHERE university=:u"), {"u":uni}).scalar()
        print(f"{uni}: total {total}, bad title {bad}, generic fac {gen_fac}")

session.close()
