import urllib.request
import ssl
from bs4 import BeautifulSoup
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://biology.science.cmu.ac.th/teacher.php', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
cards = soup.find_all('div', class_='col-md-6')
print(f'Total col-md-6 found: {len(cards)}')

bio_faculty = []
for c in cards:
    text = c.get_text(separator=' | ', strip=True)
    if 'ชื่อ - สกุล' in text:
        name_match = re.search(r'ชื่อ - สกุล\s*\|\s*:\s*\|\s*([^|]+)', text)
        name = name_match.group(1).strip() if name_match else ''
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@cmu\.ac\.th', text)
        email = email_match.group(0).lower() if email_match else None
        # look for any email (including gmail/hotmail to know)
        any_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        link = c.find('a', href=re.compile(r'personal-detail\.php\?id='))
        prof_url = f"https://biology.science.cmu.ac.th/{link['href']}" if link else None
        bio_faculty.append({
            'name': name,
            'email': email,
            'any_email': any_email,
            'prof_url': prof_url,
            'text': text[:150]
        })

print(f'Total bio faculty found: {len(bio_faculty)}')

db = SessionLocal()
bio_nulls = (
    db.query(FacultyDB)
    .filter(
        FacultyDB.university_th == 'มหาวิทยาลัยเชียงใหม่',
        FacultyDB.faculty_th == 'คณะวิทยาศาสตร์',
        FacultyDB.department_th == 'ภาควิชาชีววิทยา',
        FacultyDB.email.is_(None)
    )
    .all()
)
print(f'DB Bio NULLs: {len(bio_nulls)}')

matched = []
unmatched = []
for f in bio_nulls:
    m = None
    for b in bio_faculty:
        # match tokens
        b_clean = re.sub(r'^(ผศ\.|รศ\.|ศ\.|อ\.|ดร\.|อาจารย์|ผู้ช่วยศาสตราจารย์|รองศาสตราจารย์)\s*', '', b['name'])
        parts = b_clean.split()
        if len(parts) >= 2 and parts[0] in f.full_name_th and parts[1] in f.full_name_th:
            m = b
            break
        elif b_clean in f.full_name_th:
            m = b
            break
    if m:
        matched.append((f, m))
    else:
        unmatched.append(f)

print(f'Matched: {len(matched)}')
print(f'Unmatched: {len(unmatched)}')

for f, m in matched:
    print(f"  {f.id} | {f.full_name_th} -> {m['email']} (Any: {m['any_email']})")

if unmatched:
    print('Unmatched DB Bio:')
    for u in unmatched:
        print(f"  {u.id} | {u.full_name_th}")

db.close()
