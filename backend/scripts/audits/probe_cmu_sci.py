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

url = 'https://www.chem.science.cmu.ac.th/personnel/2/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
chem_cards = []
for tag in soup.find_all(string=re.compile(r'@cmu\.ac\.th')):
    em = tag.strip().lower()
    if em == 'chem-sci@cmu.ac.th':
        continue
    card = tag.find_parent('div', class_='row') or tag.find_parent('div')
    lines = [l.strip() for l in card.get_text(separator='\n').splitlines() if l.strip()]
    name = lines[0] if lines else ''
    chem_cards.append({
        'name': name,
        'email': em,
        'full_text': ' '.join(lines)
    })

print(f'Total chem cards scraped: {len(chem_cards)}')

db = SessionLocal()
chem_nulls = (
    db.query(FacultyDB)
    .filter(
        FacultyDB.university_th == 'มหาวิทยาลัยเชียงใหม่',
        FacultyDB.faculty_th == 'คณะวิทยาศาสตร์',
        FacultyDB.department_th == 'ภาควิชาเคมี',
        FacultyDB.email.is_(None)
    )
    .all()
)
print(f'DB Chem NULLs: {len(chem_nulls)}')

matched = []
unmatched = []
for f in chem_nulls:
    m = None
    for c in chem_cards:
        c_parts = c['name'].split()
        if len(c_parts) >= 2:
            if c_parts[0] in f.full_name_th and c_parts[1] in f.full_name_th:
                m = c
                break
        elif c['name'] and c['name'] in f.full_name_th:
            m = c
            break
    if m:
        matched.append((f, m))
    else:
        unmatched.append(f)

print(f'Matched: {len(matched)}')
print(f'Unmatched: {len(unmatched)}')
for f, m in matched:
    print(f"  {f.id} | {f.full_name_th} -> {m['email']} ({m['name']})")

if unmatched:
    print('Unmatched DB chem:')
    for u in unmatched:
        print(f"  {u.id} | {u.full_name_th}")

db.close()
