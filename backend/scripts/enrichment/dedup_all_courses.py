import sys
import os
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import SessionLocal
from app.models.db_models import CourseDB

def normalize_th(text):
    if not text or text == "ไม่ระบุ": return ""
    t = text.lower()
    t = re.sub(r'\(.*?\)', '', t)
    for word in ["หลักสูตร", "วิทยาศาสตรบัณฑิต", "วิทยาศาสตรมหาบัณฑิต", "ปรัชญาดุษฎีบัณฑิต", "สาขาวิชา", "ศิลปศาสตรบัณฑิต", "ศิลปศาสตรมหาบัณฑิต", "วิศวกรรมศาสตรบัณฑิต", "วิศวกรรมศาสตรมหาบัณฑิต", "บัญชีบัณฑิต", "บริหารธุรกิจบัณฑิต", "นิติศาสตรบัณฑิต", "พยาบาลศาสตรบัณฑิต", "การจัดการมหาบัณฑิต", "วท.บ.", "ศศ.บ.", "วศ.บ.", "บธ.บ."]:
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
    all_courses = session.query(CourseDB).all()
    
    # Group by: university -> normalized_title
    # We will build groups based on TH name first, then EN name for those without TH name.
    uni_groups = defaultdict(lambda: defaultdict(list))
    
    for c in all_courses:
        uni = c.university
        th = normalize_th(c.title_th)
        en = normalize_en(c.title_en)
        key = th if len(th) > 3 else en
        
        # fallback to raw title if normalizer stripped everything
        if len(key) <= 3:
            key = c.title_th.strip() if c.title_th and c.title_th != "ไม่ระบุ" else c.title_en.strip()
            
        uni_groups[uni][key].append(c)
    
    total_deleted = 0
    total_merged = 0
    
    print("Starting Global Deduplication...")
    
    for uni, groups in uni_groups.items():
        uni_deleted = 0
        uni_merged = 0
        for key, courses in groups.items():
            if len(courses) > 1:
                # Sort courses to find the best one to keep
                def score(c):
                    s = 0
                    if c.faculty_th not in ["บัณฑิตวิทยาลัย", "ไม่ระบุ", "", None]:
                        s += 10
                    if c.title_th not in ["ไม่ระบุ", "", None] and len(c.title_th) > 5:
                        s += 5
                    if c.title_en not in ["ไม่ระบุ", "", None] and len(c.title_en) > 5:
                        s += 5
                    if c.website_url and len(c.website_url) > 10:
                        s += 3
                    return s
                
                courses.sort(key=score, reverse=True)
                kept = courses[0]
                duplicates = courses[1:]
                
                # Merge info
                for d in duplicates:
                    if kept.faculty_th in ["บัณฑิตวิทยาลัย", "ไม่ระบุ", "", None] and d.faculty_th not in ["บัณฑิตวิทยาลัย", "ไม่ระบุ", "", None]:
                        kept.faculty_th = d.faculty_th
                        kept.faculty = d.faculty
                    if kept.title_th in ["ไม่ระบุ", "", None] and d.title_th not in ["ไม่ระบุ", "", None]:
                        kept.title_th = d.title_th
                    if kept.title_en in ["ไม่ระบุ", "", None] and d.title_en not in ["ไม่ระบุ", "", None]:
                        kept.title_en = d.title_en
                    if kept.website_url in ["", None] and d.website_url:
                        kept.website_url = d.website_url
                    
                    session.delete(d)
                    uni_deleted += 1
                uni_merged += 1
                
        if uni_merged > 0:
            print(f"[{uni}] Merged {uni_merged} groups, deleted {uni_deleted} duplicates.")
        total_deleted += uni_deleted
        total_merged += uni_merged
            
    session.commit()
    print(f"\nGlobal Deduplication Complete!")
    print(f"Total Merged Groups: {total_merged}")
    print(f"Total Deleted Courses: {total_deleted}")
    print("Total Database Courses Now:", session.query(CourseDB).count())

if __name__ == "__main__":
    run()
