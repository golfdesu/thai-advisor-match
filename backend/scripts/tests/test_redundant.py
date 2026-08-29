from app.core.database import SessionLocal
from app.models.db_models import CourseDB
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
session = SessionLocal()
mu_courses = session.query(CourseDB).filter(CourseDB.university == "Mahidol University").all()

# Group by normalized English title (if available) or Thai title
titles_en = defaultdict(list)
titles_th = defaultdict(list)

for c in mu_courses:
    en = c.title_en.lower().strip() if c.title_en and c.title_en != "ไม่ระบุ" else ""
    th = c.title_th.lower().strip() if c.title_th and c.title_th != "ไม่ระบุ" else ""
    
    # Remove common prefixes/suffixes for better matching
    en_norm = en.replace("master of science program in ", "").replace("master of science in ", "").replace("m.sc. in ", "").replace("m.sc. (", "").replace(")", "").strip()
    en_norm = en_norm.replace("program", "").strip()
    
    th_norm = th.replace("หลักสูตรวิทยาศาสตรมหาบัณฑิต", "").replace("วิทยาศาสตรมหาบัณฑิต", "").replace("สาขาวิชา", "").strip()
    
    if len(en_norm) > 5:
        titles_en[en_norm].append(c)
    if len(th_norm) > 5:
        titles_th[th_norm].append(c)

redundant_en = {k: v for k, v in titles_en.items() if len(v) > 1}
redundant_th = {k: v for k, v in titles_th.items() if len(v) > 1}

print(f"Potential English redundancies: {len(redundant_en)} groups")
count = 0
for k, v in redundant_en.items():
    print(f"\nGroup EN: '{k}'")
    for c in v:
        print(f"  - [{c.id}] {c.title_th} | {c.title_en} | {c.faculty_th}")
    count += 1
    if count > 5: break

print(f"\nPotential Thai redundancies: {len(redundant_th)} groups")
count = 0
for k, v in redundant_th.items():
    print(f"\nGroup TH: '{k}'")
    for c in v:
        print(f"  - [{c.id}] {c.title_th} | {c.title_en} | {c.faculty_th}")
    count += 1
    if count > 5: break
