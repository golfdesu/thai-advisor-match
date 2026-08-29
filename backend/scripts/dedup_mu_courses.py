import sys
import os
import re
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal
from app.models.db_models import CourseDB

def normalize_th(text):
    if not text or text == "ไม่ระบุ": return ""
    t = text.lower()
    t = re.sub(r'\(.*?\)', '', t)
    for word in ["หลักสูตร", "วิทยาศาสตรบัณฑิต", "วิทยาศาสตรมหาบัณฑิต", "ปรัชญาดุษฎีบัณฑิต", "สาขาวิชา", "ศิลปศาสตรบัณฑิต", "ศิลปศาสตรมหาบัณฑิต", "วิศวกรรมศาสตรบัณฑิต", "วิศวกรรมศาสตรมหาบัณฑิต"]:
        t = t.replace(word, "")
    return t.strip().replace(" ", "")

def normalize_en(text):
    if not text or text == "ไม่ระบุ": return ""
    t = text.lower()
    t = re.sub(r'\(.*?\)', '', t)
    for word in ["program", "master of", "bachelor of", "doctor of", "science in", "arts in", "engineering in", "philosophy in", "ph.d.", "m.sc.", "b.sc.", "m.a.", "b.a.", "in "]:
        t = t.replace(word, "")
    return t.strip().replace(" ", "")

def run():
    session = SessionLocal()
    mu_courses = session.query(CourseDB).filter(CourseDB.university == "Mahidol University").all()
    
    # We will build groups based on TH name first, then EN name for those without TH name.
    groups = defaultdict(list)
    
    for c in mu_courses:
        th = normalize_th(c.title_th)
        en = normalize_en(c.title_en)
        key = th if len(th) > 3 else en
        if len(key) > 3:
            groups[key].append(c)
    
    deleted_count = 0
    merged_count = 0
    
    for key, courses in groups.items():
        if len(courses) > 1:
            # Sort courses to find the best one to keep
            # Best: faculty is NOT 'บัณฑิตวิทยาลัย' or 'ไม่ระบุ'
            def score(c):
                s = 0
                if c.faculty_th not in ["บัณฑิตวิทยาลัย", "ไม่ระบุ", "", None]:
                    s += 10
                if c.title_th not in ["ไม่ระบุ", "", None] and len(c.title_th) > 5:
                    s += 5
                if c.title_en not in ["ไม่ระบุ", "", None] and len(c.title_en) > 5:
                    s += 5
                # Prefer older manually created IDs (often uppercase or specific prefixes) over MD5 hashes
                if len(c.id) != 32:
                    s += 2
                return s
            
            courses.sort(key=score, reverse=True)
            kept = courses[0]
            duplicates = courses[1:]
            
            # Merge some useful info into kept if it's missing
            for d in duplicates:
                if kept.faculty_th in ["บัณฑิตวิทยาลัย", "ไม่ระบุ", "", None] and d.faculty_th not in ["บัณฑิตวิทยาลัย", "ไม่ระบุ", "", None]:
                    kept.faculty_th = d.faculty_th
                    kept.faculty = d.faculty
                if kept.title_th in ["ไม่ระบุ", "", None] and d.title_th not in ["ไม่ระบุ", "", None]:
                    kept.title_th = d.title_th
                if kept.title_en in ["ไม่ระบุ", "", None] and d.title_en not in ["ไม่ระบุ", "", None]:
                    kept.title_en = d.title_en
                
                session.delete(d)
                deleted_count += 1
            
            merged_count += 1
            
    session.commit()
    print(f"Deduplication complete. Merged {merged_count} groups, deleted {deleted_count} duplicate courses.")
    print("MU total now:", session.query(CourseDB).filter(CourseDB.university == "Mahidol University").count())

if __name__ == "__main__":
    run()
