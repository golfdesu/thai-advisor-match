import requests
import json
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
    
    url = "https://graduate.mahidol.ac.th/Admission/announce/cur_open_list_table.php"
    
    levels = {"M": "Master", "D": "Doctorate"}
    total_ins = 0
    total_upd = 0
    
    print("Scraping Mahidol Graduate Studies (Fixing ID collisions)...")
    
    for level_code, level_name in levels.items():
        for fac_id in range(1, 100):
            data = {
                "fac_id": str(fac_id),
                "cur_open_year": "2569",
                "act_open": "2569/08/29",
                "Level": level_code,
                "search": "",
                "lang": "th",
                "status": "",
                "selected_faculty": ""
            }
            try:
                r = requests.post(url, data=data, verify=False, timeout=10)
                if not r.text.strip():
                    continue
                    
                soup = BeautifulSoup(r.text, 'html.parser')
                links = soup.find_all("a", class_="mugr-program-detail-link")
                
                if not links:
                    continue
                
                courses = []
                for i in range(0, len(links), 2):
                    title_th = links[i].text.strip()
                    title_en = ""
                    if i + 1 < len(links):
                        title_en = links[i+1].text.strip()
                    
                    # Generate a truly unique ID using MD5
                    raw_id = f"mu-grad-{level_code}-{title_en}-{title_th}"
                    course_id = hashlib.md5(raw_id.encode('utf-8')).hexdigest()
                    
                    c = {
                        "id": course_id,
                        "title_th": title_th,
                        "title_en": title_en,
                        "university": "Mahidol University",
                        "university_th": "มหาวิทยาลัยมหิดล",
                        "faculty": "Faculty of Graduate Studies",
                        "faculty_th": "บัณฑิตวิทยาลัย",
                        "degree_level": level_name,
                        "degree_name": level_code + ".Sc." if level_code == "M" else "Ph.D.",
                        "program_type": "Graduate",
                        "department": "ไม่ระบุ",
                        "department_th": "ไม่ระบุ",
                        "duration_years": "2" if level_code == "M" else "3",
                        "tuition_per_semester": "ไม่ระบุ",
                        "tuition_total": "ไม่ระบุ",
                        "description": "Graduate program at Mahidol University.",
                        "website_url": "https://graduate.mahidol.ac.th/Admission/announce/cur_open_list.php?Level=" + level_code,
                        "curriculum_highlights": [],
                        "career_paths": [],
                        "tags": []
                    }
                    
                    emb_text = f"{c['title_th']} {c['title_en']} {c['faculty_th']}"
                    c["embedding_text"] = emb_text
                    
                    ex = session.query(CourseDB).filter_by(id=c["id"]).first()
                    if ex:
                        for k, v in c.items():
                            if k != 'embedding': # dont overwrite embedding if already exists
                                setattr(ex, k, v)
                        total_upd += 1
                    else:
                        vec = embedding_service.get_embedding(emb_text)
                        c["embedding"] = vec if vec and len(vec) == 768 else None
                        session.add(CourseDB(**c))
                        total_ins += 1
                        
                    session.commit()
            except Exception as e:
                pass

    print(f"\nDone! Inserted: {total_ins}, Updated: {total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        q1 = text("SELECT count(*) FROM courses WHERE university='Mahidol University'")
        q2 = text("SELECT count(*) FROM courses")
        print(f"MU total: {conn.execute(q1).scalar()}")
        print(f"DB total: {conn.execute(q2).scalar()}")

if __name__ == "__main__":
    run()
