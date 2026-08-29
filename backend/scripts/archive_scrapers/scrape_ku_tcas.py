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
    base_url = "https://admission.ku.ac.th"
    
    r = requests.get(base_url, headers=headers, verify=False, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    project_links = list(set([a['href'] for a in soup.find_all("a", href=True) if "/majors/project/" in a['href']]))
    
    total_ins = 0
    total_upd = 0
    unique_titles = set()
    
    print(f"Scraping KU TCAS Undergraduate Programs... (Found {len(project_links)} projects)")
    
    for link in project_links:
        try:
            r2 = requests.get(base_url + link, headers=headers, verify=False, timeout=10)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            trs = soup2.find_all("tr")
            
            current_faculty = "ไม่ระบุ"
            
            for tr in trs:
                ths = tr.find_all("th")
                tds = tr.find_all("td")
                
                # Check for faculty header
                if ths and len(ths) == 1:
                    header_text = ths[0].text.strip()
                    if "คณะ" in header_text or "วิทยาลัย" in header_text or "วิทยาเขต" in header_text:
                        current_faculty = header_text
                        continue
                
                if tds and len(tds) >= 1:
                    raw_title = tds[0].text.strip()
                    if not raw_title or "โครงการ" in raw_title:
                        continue
                        
                    norm_title = raw_title.replace(" ", "")
                    # to prevent duplicates across rounds, we only add unique courses per faculty
                    unique_key = f"{current_faculty}-{norm_title}"
                    
                    if unique_key in unique_titles:
                        continue
                    unique_titles.add(unique_key)
                    
                    is_inter = "(นานาชาติ" in raw_title or "ภาษาอังกฤษ" in raw_title
                    title_th = raw_title
                    title_en = "Not specified"
                    
                    deg_name = "B.Sc." if "วท.บ." in raw_title else ("B.A." if "ศศ.บ." in raw_title else ("B.Eng." if "วศ.บ." in raw_title else "B.B.A." if "บธ.บ." in raw_title else "Bachelor"))
                    
                    raw_id = f"ku-tcas-{unique_key}"
                    course_id = hashlib.md5(raw_id.encode('utf-8')).hexdigest()
                    
                    c = {
                        "id": course_id,
                        "title_th": title_th,
                        "title_en": title_en,
                        "university": "Kasetsart University",
                        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
                        "faculty": current_faculty, 
                        "faculty_th": current_faculty,
                        "degree_level": "Bachelor",
                        "degree_name": deg_name,
                        "program_type": "International" if is_inter else "Thai",
                        "department": "ไม่ระบุ",
                        "department_th": "ไม่ระบุ",
                        "duration_years": "4",
                        "tuition_per_semester": "ไม่ระบุ",
                        "tuition_total": "ไม่ระบุ",
                        "description": "Undergraduate program at Kasetsart University.",
                        "website_url": "https://admission.ku.ac.th",
                        "curriculum_highlights": [],
                        "career_paths": [],
                        "tags": []
                    }
                    
                    emb_text = f"{c['title_th']} {c['faculty_th']} Kasetsart University"
                    c["embedding_text"] = emb_text
                    
                    ex = session.query(CourseDB).filter_by(id=course_id).first()
                    if ex:
                        total_upd += 1
                    else:
                        vec = embedding_service.get_embedding(emb_text)
                        c["embedding"] = vec if vec and len(vec) == 768 else None
                        session.add(CourseDB(**c))
                        total_ins += 1
            session.commit()
        except Exception as e:
            print("Error on", link, e)

    print(f"\nTCAS Done! Inserted: {total_ins}, Updated: {total_upd}")
    from sqlalchemy import text
    with engine.connect() as conn:
        q = text("SELECT count(*) FROM courses WHERE university='Kasetsart University'")
        print(f"KU total: {conn.execute(q).scalar()}")

if __name__ == "__main__":
    run()
