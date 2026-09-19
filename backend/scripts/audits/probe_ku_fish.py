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

urls = [
    ('ภาควิชาการจัดการประมง', 'https://fish.ku.ac.th/th/node/338'),
    ('ภาควิชาชีววิทยาประมง', 'https://fish.ku.ac.th/th/%E0%B8%A0%E0%B8%B2%E0%B8%84%E0%B8%A7%E0%B8%B4%E0%B8%8A%E0%B8%B2%E0%B8%8A%E0%B8%B5%E0%B8%A7%E0%B8%A7%E0%B8%B4%E0%B8%97%E0%B8%A2%E0%B8%B2%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%A1%E0%B8%87'),
    ('ภาควิชาผลิตภัณฑ์ประมง', 'https://fish.ku.ac.th/th/node/340'),
    ('ภาควิชาเพาะเลี้ยงสัตว์น้ำ', 'https://fish.ku.ac.th/th/node/341'),
    ('ภาควิชาวิทยาศาสตร์ทางทะเล', 'https://fish.ku.ac.th/th/node/342'),
]

scraped = []
for dept_name, url in urls:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        soup = BeautifulSoup(resp.read(), 'html.parser')
        team_rows = soup.find_all('div', class_='teamdetail')
        for tr in team_rows:
            name_div = tr.find('div', class_='teamdetail-name')
            email_div = tr.find('div', class_='teamdetail-email')
            pos_div = tr.find('div', class_='teamdetail-position')
            name_raw = name_div.get_text(strip=True) if name_div else ''
            name_clean = ' '.join(name_raw.split())
            email_raw = email_div.get_text(strip=True) if email_div else ''
            em_match = re.search(r'[a-zA-Z0-9._%+-]+@ku\.(?:ac\.)?th', email_raw)
            email = em_match.group(0).lower() if em_match else None
            pos_raw = pos_div.get_text(strip=True) if pos_div else ''
            if name_clean and email:
                scraped.append({
                    'dept': dept_name,
                    'name': name_clean,
                    'email': email,
                    'position': pos_raw,
                    'url': url
                })

print(f'Total scraped faculty cards with valid email: {len(scraped)}')

db = SessionLocal()
ku_fish_nulls = (
    db.query(FacultyDB)
    .filter(
        FacultyDB.university_th == 'มหาวิทยาลัยเกษตรศาสตร์',
        FacultyDB.faculty_th == 'คณะประมง',
        FacultyDB.email.is_(None)
    )
    .all()
)
print(f'KU Fisheries records in DB with email IS NULL: {len(ku_fish_nulls)}')

matched = []
unmatched_db = []

for f in ku_fish_nulls:
    f_tokens = set(f.full_name_th.split())
    # find match in scraped
    match = None
    for s in scraped:
        s_tokens = set(s['name'].split())
        # check overlap
        if len(f_tokens.intersection(s_tokens)) >= 2 or (len(s_tokens) == 2 and any(t in f.full_name_th for t in s_tokens)):
            # verify both first and last name match or substring
            s_first = s['name'].split()[0]
            s_last = s['name'].split()[-1]
            if s_first in f.full_name_th and s_last in f.full_name_th:
                match = s
                break
    if match:
        matched.append((f, match))
    else:
        unmatched_db.append(f)

print(f'Matched: {len(matched)}')
print(f'Unmatched DB NULLs: {len(unmatched_db)}')

for f, m in matched[:10]:
    print(f'MATCH: {f.id} | {f.full_name_th} -> {m["email"]} ({m["name"]})')

if unmatched_db:
    print('Sample unmatched DB:')
    for f in unmatched_db[:5]:
        print(f'  {f.id} | {f.full_name_th}')

db.close()
