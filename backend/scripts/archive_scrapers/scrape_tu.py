import requests
from bs4 import BeautifulSoup
import urllib3
import sys
import os
import hashlib
urllib3.disable_warnings()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal, engine, Base
from app.models.db_models import CourseDB
from app.core.embedding_service import embedding_service

def run():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    groups = {
        "undergrad": "Bachelor",
        "master": "Graduate", # Master/Doctoral
        "doctoral": "Doctorate",
        "inter": "International",
        "online": "Online"
    }
    
    total_ins = 0
    total_upd = 0
    
    print("Scraping Thammasat University...")
    
    for group_id, level in groups.items():
        try:
            r = requests.get(f"https://tu.ac.th/academic/programs?group={group_id}", headers=headers, verify=False, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            triggers = soup.find_all("div", class_="ac-trigger")
            for t in triggers:
                h3 = t.find("h3")
                p = t.find("p")
                if h3 and p:
                    title_th = h3.text.strip()
                    faculty_th = p.text.strip()
                    
                    # Heuristics for degree level
                    deg_level = "Bachelor"
                    deg_name = "B.A./B.Sc."
                    if "มหาบัณฑิต" in title_th or "Master" in title_th:
                        deg_level = "Master"
                        deg_name = "M.A./M.Sc."
                    elif "ดุษฎีบัณฑิต" in title_th or "Doctor" in title_th or "Ph.D" in title_th:
                        deg_level = "Doctorate"
                        deg_name = "Ph.D."
                        
                    is_inter = "(นานาชาติ)" in title_th or "(หลักสูตรนานาชาติ)" in title_th or group_id == "inter"
                    
                    raw_id = f"tu-{title_th}-{faculty_th}"
                    course_id = hashlib.md5(raw_id.encode('utf-8')).hexdigest()
                    
                    c = {
                        "id": course_id,
                        "title_th": title_th,
                        "title_en": "Not specified",
                        "university": "Thammasat University",
                        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
                        "faculty": faculty_th,
                        "faculty_th": faculty_th,
                        "degree_level": deg_level,
                        "degree_name": deg_name,
                        "program_type": "International" if is_inter else "Thai",
                        "department": "ไม่ระบุ",
                        "department_th": "ไม่ระบุ",
                        "duration_years": "4" if deg_level == "Bachelor" else "2",
                        "tuition_per_semester": "ไม่ระบุ",
                        "tuition_total": "ไม่ระบุ",
                        "description": "Program at Thammasat University.",
                        "website_url": "https://tu.ac.th/academic/programs",
                        "curriculum_highlights": [],
                        "career_paths": [],
                        "tags": []
                    }
                    
                    emb_text = f"{c['title_th']} {c['faculty_th']} Thammasat University"
                    c["embedding_text"] = emb_text
                    
                    ex = session.query(CourseDB).filter_by(id=course_id).first()
                    if ex:
                        for k, v in c.items():
                            if k != 'embedding':
                                setattr(ex, k, v)
                        total_upd += 1
                    else:
                        vec = embedding_service.get_embedding(emb_text)
                        c["embedding"] = vec if vec and len(vec) == 768 else None
                        session.add(CourseDB(**c))
                        total_ins += 1
                        
                    session.commit()
        except Exception as e:
            print("Error:", e)

    print(f"\nDone! Inserted: {total_ins}, Updated: {total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        q = text("SELECT count(*) FROM courses WHERE university='Thammasat University'")
        print(f"TU total: {conn.execute(q).scalar()}")

if __name__ == "__main__":
    run()
