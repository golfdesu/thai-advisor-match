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

db = SessionLocal()
facs = (
    db.query(FacultyDB)
    .filter(
        FacultyDB.university_th == 'จุฬาลงกรณ์มหาวิทยาลัย',
        FacultyDB.faculty_th == 'คณะแพทยศาสตร์',
        FacultyDB.email.is_(None)
    )
    .all()
)
print(f'Total Chula Medicine NULLs in DB: {len(facs)}')

results = []
for f in facs:
    url = f.profile_url
    if not url:
        results.append((f, None, 'no_url'))
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            # filter prmdcu
            cleaned = [e.lower() for e in set(emails) if e.lower() != 'prmdcu@gmail.com']
            results.append((f, cleaned, 'ok'))
    except Exception as e:
        results.append((f, None, str(e)))

print('--- RESULTS SUMMARY ---')
official_emails = []
freemails = []
empty_emails = []

for f, emails, status in results:
    if not emails:
        empty_emails.append(f)
    else:
        # check if any official
        off = [e for e in emails if e.endswith('chula.md') or e.endswith('chula.ac.th') or e.endswith('.ac.th') or e.endswith('.edu')]
        free = [e for e in emails if any(e.endswith(d) for d in ['@gmail.com', '@hotmail.com', '@yahoo.com', '@yahoo.co.th'])]
        if off:
            official_emails.append((f, off[0]))
        elif free:
            freemails.append((f, free[0]))
        else:
            empty_emails.append(f)

print(f'Official institutional emails found: {len(official_emails)}')
for f, em in official_emails:
    print(f'  OFFICIAL: {f.id} | {f.full_name_th} -> {em}')

print(f'Personal freemails found (must remain NULL): {len(freemails)}')
for f, em in freemails[:5]:
    print(f'  FREEMAIL: {f.id} | {f.full_name_th} -> {em}')

print(f'Empty emails (no email published): {len(empty_emails)}')
db.close()
